//! Ingestion task - Deterministic tick generator, Replay, and MockWS
//!
//! Implements S6 (backpressure) via try_send with counter
//! Implements Replay (from DB) and MockWS (with reconnect)

use crate::config::{EngineConfig, IngestMode};
use crate::types::{EventId, Metrics, PersistEvent, Tick};
use futures::{SinkExt, StreamExt};
use sqlx::SqlitePool;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
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
) {
    match config.ingest_mode {
        IngestMode::Synthetic => {
            run_synthetic(
                symbol,
                config.tick_interval_ms,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            )
            .await
        }
        IngestMode::Replay => {
            run_replay(symbol, pool, tick_tx, persist_tx, metrics, shutdown).await
        }
        IngestMode::MockWs => {
            let url = config.ws_url.unwrap_or_else(|| "ws://localhost:9001".to_string());
            run_mock_ws(
                symbol,
                url,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            )
            .await
        }
    }
}

async fn run_synthetic(
    symbol: String,
    tick_interval_ms: u64,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    let mut timer = interval(Duration::from_millis(tick_interval_ms));
    let mut price = 100.0;
    let price_step = 0.05;

    info!(
        symbol = %symbol,
        interval_ms = tick_interval_ms,
        mode = "SYNTHETIC",
        "ingest task started"
    );

    loop {
        tokio::select! {
            _ = timer.tick() => {
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

async fn run_replay(
    symbol: String,
    pool: SqlitePool,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    info!(mode = "REPLAY", "ingest task started");

    // Fetch all ticks (for now, simplistic) - TODO: stream cursor
    // In a real replay, we'd probably want to stream from DB effectively.
    // For Phase 2, reading all ticks into memory or small pages is fine if dataset is small.
    // Let's assume small dataset for now or use a simple loop offset/limit.
    
    let mut offset = 0;
    let limit = 1000;
    
    loop {
        // checkpoint for shutdown
        if shutdown.try_recv().is_ok() {
             info!("replay received shutdown");
             break;
        }

        let rows = sqlx::query_as::<_, (i64, String, f64, f64, i64)>(
            "SELECT id, symbol, price, volume, ts FROM ticks ORDER BY ts ASC LIMIT ? OFFSET ?"
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
                     
                     // If we want to simulate time, we could sleep delta.
                     // For now, full speed replay (or we could add a speed factor knob).
                     // Let's just pump them.
                     
                     let tick = Tick {
                         event_id: EventId::new(),
                         symbol: sym, // Use stored symbol? or override? Stored is better for replay.
                         price,
                         volume: vol,
                         ts, // Use historical TS? Yes.
                     };
                     
                     // In replay mode, we might NOT want to persist back to DB (duplicates)?
                     // BUT, the pipeline mandates persistence.
                     // Ideally, replay is for Strategy testing, so we persist Signals, but maybe not Ticks again.
                     // However, to keep pipeline uniform, we send to persist_tx.
                     // The persist task will insert. ID collision? 
                     // Ticks table has auto-inc ID. EventId is not in Ticks table currently (it is in Types but not Schema in db.rs? Check db.rs).
                     // db.rs schema: ticks(id, symbol, price, volume, ts). No event_id.
                     // Types::Tick has event_id.
                     // So we generate new EventId for the "Replayed Tick" event in the system.
                     
                     send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
                     metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                     
                     // Small yield to avoid hogging CPU completely
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
}

async fn run_mock_ws(
    symbol: String,
    url: String,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    info!(mode = "MOCKWS", url = %url, "ingest task started");

    loop {
        // Reconnect loop (S3)
        // Check shutdown first
        if shutdown.try_recv().is_ok() {
            break;
        }

        info!("connecting to {}", url);
        match connect_async(&url).await {
            Ok((ws_stream, _)) => {
                info!("connected to mock ws");
                let (mut write, mut read) = ws_stream.split();
                
                // Ping interval
                let mut ping_timer = interval(Duration::from_secs(5));
                let mut last_activity = tokio::time::Instant::now();

                loop {
                    tokio::select! {
                         _ = shutdown.recv() => {
                             info!("shutdown requested");
                             return; 
                         }
                         _ = ping_timer.tick() => {
                             // S4: Keepalive
                             if last_activity.elapsed() > Duration::from_secs(5) {
                                 // Send ping
                                 if let Err(e) = write.send(Message::Ping(vec![])).await {
                                     warn!("failed to send ping: {}", e);
                                     break; // Reconnect
                                 }
                             }
                         }
                         msg = read.next() => {
                             match msg {
                                 Some(Ok(Message::Text(text))) => {
                                     last_activity = tokio::time::Instant::now();
                                     match serde_json::from_str::<Tick>(&text) {
                                         Ok(tick) => {
                                             metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                             send_tick(tick, &tick_tx, &persist_tx, &metrics).await;
                                         }
                                         Err(e) => {
                                              // S5: Malformed handling
                                              warn!(error = %e, "malformed json");
                                         }
                                     }
                                 }
                                 Some(Ok(Message::Pong(_))) => {
                                     last_activity = tokio::time::Instant::now();
                                     // S4: Pong received
                                 }
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
                warn!(error = %e, "connect failed, retrying in 3s (Exponential backoff todo)");
                // S3 says exponential backoff. For now constant 3s is better than tight loop.
                tokio::select! {
                    _ = tokio::time::sleep(Duration::from_secs(3)) => {}
                    _ = shutdown.recv() => { return; }
                }
            }
        }
    }
}

async fn send_tick(
    tick: Tick,
    tick_tx: &mpsc::Sender<Tick>,
    persist_tx: &mpsc::Sender<PersistEvent>,
    metrics: &Arc<Metrics>,
) {
    if tick_tx.try_send(tick.clone()).is_err() {
        metrics.backpressure_drops_tick.fetch_add(1, Ordering::Relaxed);
        warn!(reason = "BP_DROP_TICK", "dropped tick");
    }
    if persist_tx.try_send(PersistEvent::Tick(tick)).is_err() {
        metrics.backpressure_drops_persist.fetch_add(1, Ordering::Relaxed);
    }
}

