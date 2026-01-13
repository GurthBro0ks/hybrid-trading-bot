//! Ingestion task - Deterministic tick generator, Replay, MockWS, and RealWS
//!
//! Implements S6 (backpressure) via try_send with counter
//! Implements Replay (from DB) and MockWS (with reconnect)

pub mod realws;
pub mod venuebook;
pub mod ws_sources;

use crate::config::{EngineConfig, IngestMode};
use crate::types::{EventId, Metrics, PersistEvent, Tick};
use futures::{SinkExt, StreamExt};
use serde::Deserialize;
use sqlx::SqlitePool;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::sync::{mpsc, oneshot};
use tokio::time::{interval, Duration};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use tracing::{error, info, warn};

/// Run the ingestion task
pub async fn run_ingest_task(
    symbol: String,
    config: EngineConfig,
    pool: SqlitePool,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    shutdown: tokio::sync::broadcast::Receiver<()>,
    replay_done: Option<oneshot::Sender<()>>,
) {
    match config.ingest_mode {
        IngestMode::Synthetic => {
            run_synthetic(
                symbol,
                config.tick_interval_ms,
                config.sample_every,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            )
            .await
        }
        IngestMode::Replay => {
            if let Some(replay_file) = config.replay_file.clone() {
                run_replay_file(
                    replay_file,
                    config.sample_every,
                    tick_tx,
                    persist_tx,
                    metrics,
                    shutdown,
                    replay_done,
                )
                .await;
            } else {
                run_replay_db(
                    symbol,
                    config.sample_every,
                    pool,
                    tick_tx,
                    persist_tx,
                    metrics,
                    shutdown,
                    replay_done,
                )
                .await;
            }
        }
        IngestMode::MockWs => {
            let url = config
                .ws_url
                .unwrap_or_else(|| "ws://localhost:9001".to_string());
            run_mock_ws(
                symbol,
                url,
                config.sample_every,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            )
            .await
        }
        IngestMode::RealWs => {
            realws::run_real_ws(symbol, config, tick_tx, persist_tx, metrics, shutdown).await
        }
    }
}

async fn run_synthetic(
    symbol: String,
    tick_interval_ms: u64,
    sample_every: u64,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    let mut timer = interval(Duration::from_millis(tick_interval_ms));
    let mut price = 100.0;
    let price_step = 0.05;
    let mut sequence = 0u64;

    info!(
        symbol = %symbol,
        interval_ms = tick_interval_ms,
        sample_every = sample_every,
        mode = "SYNTHETIC",
        "ingest task started"
    );

    loop {
        tokio::select! {
            _ = timer.tick() => {
                sequence += 1;
                if sequence % sample_every != 0 {
                    continue;
                }

                let count = metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                let direction = match count % 5 {
                    0 | 2 | 3 => 1.0,
                    _ => -0.5,
                };
                price += price_step * direction;
                if price < 1.0 { price = 1.0; }

                let tick = Tick {
                    event_id: EventId::new(),
                    symbol: symbol.clone(),
                    price,
                    volume: 1.0,
                    ts: crate::types::now_ts_millis(),
                };

                send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
            }
            _ = shutdown.recv() => {
                info!("ingest task received shutdown signal");
                break;
            }
        }
    }
}

#[derive(Debug, Deserialize)]
struct ReplayTick {
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub ts: i64,
    #[serde(default)]
    pub event_id: Option<EventId>,
}

async fn run_replay_file(
    replay_file: String,
    sample_every: u64,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
    replay_done: Option<oneshot::Sender<()>>,
) {
    info!(
        mode = "REPLAY",
        replay_file = %replay_file,
        sample_every = sample_every,
        "ingest task started"
    );

    let file = match tokio::fs::File::open(&replay_file).await {
        Ok(file) => file,
        Err(err) => {
            error!(error = %err, replay_file = %replay_file, "replay file open failed");
            return;
        }
    };

    let reader = BufReader::new(file);
    let mut lines = reader.lines();
    let mut sequence = 0u64;
    let mut ticks_read = 0u64;

    loop {
        if shutdown.try_recv().is_ok() {
            info!("replay received shutdown");
            break;
        }

        match lines.next_line().await {
            Ok(Some(line)) => {
                let line = line.trim();
                if line.is_empty() {
                    continue;
                }

                ticks_read += 1;
                metrics.ingest_received.fetch_add(1, Ordering::Relaxed);

                let parsed: ReplayTick = match serde_json::from_str(line) {
                    Ok(value) => value,
                    Err(err) => {
                        warn!(error = %err, "replay line parse failed");
                        continue;
                    }
                };

                sequence += 1;
                if sequence % sample_every != 0 {
                    continue;
                }

                let tick = Tick {
                    event_id: parsed.event_id.unwrap_or_else(EventId::new),
                    symbol: parsed.symbol,
                    price: parsed.price,
                    volume: parsed.volume,
                    ts: parsed.ts,
                };

                send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
                metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                metrics.ingest_processed.fetch_add(1, Ordering::Relaxed);
            }
            Ok(None) => {
                info!(ticks_read = ticks_read, "replay finished (file)");
                break;
            }
            Err(err) => {
                error!(error = %err, "replay read failed");
                break;
            }
        }
    }

    if let Some(done) = replay_done {
        let _ = done.send(());
    }
}

async fn run_replay_db(
    _symbol: String,
    sample_every: u64,
    pool: SqlitePool,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
    replay_done: Option<oneshot::Sender<()>>,
) {
    info!(
        mode = "REPLAY",
        sample_every = sample_every,
        "ingest task started"
    );

    let mut offset = 0;
    let limit = 1000;
    let mut sequence = 0u64;

    loop {
        if shutdown.try_recv().is_ok() {
            info!("replay received shutdown");
            break;
        }

        let rows = sqlx::query_as::<_, (i64, String, f64, f64, i64)>(
            "SELECT id, symbol, price, volume, ts FROM ticks ORDER BY ts ASC LIMIT ? OFFSET ?",
        )
        .bind(limit)
        .bind(offset)
        .fetch_all(&pool)
        .await;

        match rows {
            Ok(ticks) => {
                if ticks.is_empty() {
                    info!("replay finished (no more ticks)");
                    break;
                }

                for (_id, sym, price, vol, ts) in ticks {
                    if shutdown.try_recv().is_ok() {
                        break;
                    }

                    metrics.ingest_received.fetch_add(1, Ordering::Relaxed);
                    sequence += 1;
                    if sequence % sample_every != 0 {
                        continue;
                    }

                    let tick = Tick {
                        event_id: EventId::new(),
                        symbol: sym,
                        price,
                        volume: vol,
                        ts,
                    };

                    send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
                    metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                    metrics.ingest_processed.fetch_add(1, Ordering::Relaxed);

                    tokio::task::yield_now().await;
                }
                offset += limit;
            }
            Err(e) => {
                error!(error = %e, "replay fetch failed");
                break;
            }
        }
    }

    if let Some(done) = replay_done {
        let _ = done.send(());
    }
}

async fn run_mock_ws(
    symbol: String,
    url: String,
    sample_every: u64,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    info!(mode = "MOCKWS", url = %url, sample_every = sample_every, "ingest task started");
    let mut sequence = 0u64;

    loop {
        if shutdown.try_recv().is_ok() {
            break;
        }

        info!("connecting to {}", url);
        match connect_async(&url).await {
            Ok((ws_stream, _)) => {
                info!("connected to mock ws");
                let (mut write, mut read) = ws_stream.split();

                let mut ping_timer = interval(Duration::from_secs(5));
                let mut last_activity = tokio::time::Instant::now();

                loop {
                    tokio::select! {
                         _ = shutdown.recv() => {
                             info!("shutdown requested");
                             return;
                         }
                         _ = ping_timer.tick() => {
                             if last_activity.elapsed() > Duration::from_secs(5) {
                                 if let Err(e) = write.send(Message::Ping(vec![])).await {
                                     warn!("failed to send ping: {}", e);
                                     break;
                                 }
                             }
                         }
                         msg = read.next() => {
                             match msg {
                                 Some(Ok(Message::Text(text))) => {
                                     last_activity = tokio::time::Instant::now();
                                     match serde_json::from_str::<Tick>(&text) {
                                         Ok(tick) => {
                                             sequence += 1;
                                             if sequence % sample_every == 0 {
                                                 metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                                 send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
                                             }
                                         }
                                         Err(e) => {
                                              warn!(error = %e, "malformed json");
                                         }
                                     }
                                 }
                                 Some(Ok(Message::Pong(_))) => {}
                                 Some(Ok(Message::Close(_))) => {
                                     warn!("server closed connection");
                                     break;
                                 }
                                 Some(Err(e)) => {
                                     warn!("ws error: {}", e);
                                     break;
                                 }
                                 None => {
                                     warn!("ws stream ended");
                                     break;
                                 }
                                 _ => {}
                             }
                         }
                    }
                }
            }
            Err(e) => {
                warn!(error = %e, "connect failed, retrying in 3s");
                tokio::select! {
                    _ = tokio::time::sleep(Duration::from_secs(3)) => {}
                    _ = shutdown.recv() => { return; }
                }
            }
        }
    }
}

pub(crate) async fn send_tick(
    tick: Tick,
    tick_tx: &mpsc::Sender<Tick>,
    persist_tx: &mpsc::Sender<PersistEvent>,
    metrics: &Arc<Metrics>,
) {
    if tick_tx.try_send(tick.clone()).is_err() {
        metrics
            .backpressure_drops_tick
            .fetch_add(1, Ordering::Relaxed);
        error!(reason = "OVERLOAD", "tick channel full, exiting 13");
        // G5: Deterministic overload handling -> Exit 13
        std::process::exit(13);
    }
    if persist_tx.try_send(PersistEvent::Tick(tick)).is_err() {
        metrics
            .backpressure_drops_persist
            .fetch_add(1, Ordering::Relaxed);
        // Persist channel full is bad but maybe not fatal?
        // Prompt says "Backpressure (channel full ... saturated) -> exit 13"
        // Let's being strict.
        error!(reason = "OVERLOAD", "persist channel full, exiting 13");
        std::process::exit(13);
    }
}
