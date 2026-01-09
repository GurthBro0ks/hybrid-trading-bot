use crate::config::EngineConfig;
use crate::types::{EventId, Metrics, PersistEvent, Tick};
use futures::{SinkExt, StreamExt};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::time::{interval, sleep, Duration, Instant};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use tracing::{error, info, warn};
use url::Url;
use super::ws_sources::{WsSourceConfig, WsSourcesConfig};

pub async fn run_real_ws(
    symbol: String,
    config: EngineConfig,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    info!(mode = "REAL_WS", "ingest task started");

    let config_path = "/opt/hybrid-trading-bot/config/ws_sources.toml";
    
    // If config doesn't exist, we might be in a test env or need to fallback to example for dev convenience?
    // STRICT MODE: Fail if missing.
    let sources_config = match WsSourcesConfig::load(config_path) {
        Ok(c) => c,
        Err(e) => {
             // Check if example exists and suggestion?
             error!("Failed to load ws_sources.toml: {}. (Did you cp config/ws_sources.example.toml config/ws_sources.toml?)", e);
             std::process::exit(12);
        }
    };
    
    let mut sources = sources_config.source.clone();
    sources.sort_by_key(|s| s.priority);
    
    if sources.is_empty() {
        error!("No sources defined in ws_sources.toml");
        std::process::exit(12);
    }

    loop {
         if shutdown.try_recv().is_ok() { break; }
         
         for source in &sources {
             // Pass config.sample_every
             if run_source_session(source, &symbol, config.sample_every, &tick_tx, &persist_tx, &metrics, &mut shutdown).await {
                 // graceful shutdown
                 return; 
             }
             // Connection failed or lost, try next source
             warn!(source=%source.name, "source disconnected or failed, switching...");
         }
         
         // If we cycled through all sources, wait a bit before retrying from top
         warn!("All sources failed, sleeping 5s...");
         tokio::select! {
             _ = sleep(Duration::from_secs(5)) => {},
             _ = shutdown.recv() => { return; }
         }
    }
}

// Returns true if shutdown requested, false if connection lost/failed
async fn run_source_session(
    source: &WsSourceConfig,
    symbol: &str,
    sample_every: u64,
    tick_tx: &mpsc::Sender<Tick>,
    persist_tx: &mpsc::Sender<PersistEvent>,
    metrics: &Arc<Metrics>,
    shutdown: &mut tokio::sync::broadcast::Receiver<()>,
) -> bool {
    let url = match Url::parse(&source.url) {
        Ok(u) => u,
        Err(e) => {
            error!(source = %source.name, error = %e, "Invalid URL");
            return false;
        }
    };

    info!(source = %source.name, url = %source.url, sample_every = sample_every, "connecting...");
    
    match connect_async(url).await {
        Ok((ws_stream, _)) => {
            info!(source = %source.name, "connected");
            let (mut write, mut read) = ws_stream.split();
            let mut last_activity = Instant::now();
            let mut ping_timer = interval(Duration::from_secs(10));
            let mut sequence = 0u64;

            loop {
                tokio::select! {
                    _ = shutdown.recv() => {
                        info!("shutdown requested");
                        return true;
                    }
                     _ = ping_timer.tick() => {
                        // Keepalive
                        if last_activity.elapsed() > Duration::from_secs(20) {
                             // Send pings if idle
                            if let Err(_) = write.send(Message::Ping(vec![])).await {
                                return false; 
                            }
                        }
                    }
                    msg = read.next() => {
                        match msg {
                            Some(Ok(Message::Text(text))) => {
                                last_activity = Instant::now();
                                
                                // Parser Logic
                                if text.contains("\"type\":\"update\"") {
                                    // Gemini
                                    if let Ok(ticks) = parse_gemini_update(&text, symbol) {
                                        for tick in ticks {
                                            sequence += 1;
                                            if sequence % sample_every == 0 {
                                                crate::ingest::send_tick(tick, tick_tx, persist_tx, metrics).await;
                                                metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                            }
                                        }
                                    }
                                } else if text.contains("\"e\":\"trade\"") || text.contains("\"e\":\"aggTrade\"") {
                                    // Binance
                                    if let Ok(tick) = parse_binance_trade(&text, symbol) {
                                        sequence += 1;
                                        if sequence % sample_every == 0 {
                                            crate::ingest::send_tick(tick, tick_tx, persist_tx, metrics).await;
                                            metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                        }
                                    }
                                }
                            }
                            Some(Ok(Message::Pong(_))) => {
                                last_activity = Instant::now();
                            }
                            Some(Ok(Message::Close(_))) => return false,
                            Some(Err(e)) => {
                                warn!("ws error: {}", e);
                                return false;
                            }
                            None => return false,
                            _ => {}
                        }
                    }
                }
            }
        }
        Err(e) => {
            warn!(source = %source.name, error = %e, "connection failed");
            return false;
        }
    }
}

fn parse_binance_trade(text: &str, symbol: &str) -> anyhow::Result<Tick> {
    #[derive(serde::Deserialize)]
    struct BTrade {
        p: String,
        q: String,
        T: i64,
    }
    let t: BTrade = serde_json::from_str(text)?;
    Ok(Tick {
        event_id: EventId::new(),
        symbol: symbol.to_string(),
        price: t.p.parse()?,
        volume: t.q.parse()?,
        ts: t.T,
    })
}

fn parse_gemini_update(text: &str, symbol: &str) -> anyhow::Result<Vec<Tick>> {
    #[derive(serde::Deserialize)]
    struct GEvent {
        #[serde(rename = "type")]
        type_: String,
        price: Option<String>,
        amount: Option<String>,
        makerSide: Option<String>,
    }
    #[derive(serde::Deserialize)]
    struct GUpdate {
        timestampms: i64,
        events: Vec<GEvent>,
    }
    
    let u: GUpdate = serde_json::from_str(text)?;
    let mut ticks = Vec::new();
    
    for event in u.events {
        if event.type_ == "trade" {
            if let (Some(price), Some(amount)) = (event.price, event.amount) {
                ticks.push(Tick {
                    event_id: EventId::new(),
                    symbol: symbol.to_string(),
                    price: price.parse()?,
                    volume: amount.parse()?,
                    ts: u.timestampms,
                });
            }
        }
    }
    Ok(ticks)
}
