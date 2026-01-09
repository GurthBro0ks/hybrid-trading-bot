# Phase 2.3 — SMA Strategy (Replay-Proved)

## Baseline
$ date -Iseconds && hostname && uname -a
2026-01-09T17:23:27+00:00
slimy-nuc1
Linux slimy-nuc1 6.8.0-90-generic #91-Ubuntu SMP PREEMPT_DYNAMIC Tue Nov 18 14:14:30 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux

$ git log -1 --oneline
554ddce docs(spec): lock exit-code protocol + sampling invariant

$ git status -sb
## main...origin/main [ahead 15]
?? docs/buglog/BUG_2026-01-09_phase2_2_4_contract_lock_phase2_3_sma.md

## Strategy code map
$ rg -n "strategy" engine-rust/src
engine-rust/src/main.rs:3://! Pipeline: ingest → strategy → execute(shadow) → persist
engine-rust/src/main.rs:17:mod strategy;
engine-rust/src/main.rs:209:    let persist_tx_strategy = persist_tx.clone();
engine-rust/src/main.rs:211:    let metrics_strategy = metrics.clone();
engine-rust/src/main.rs:240:    // Spawn strategy task
engine-rust/src/main.rs:241:    let strategy_handle = tokio::spawn(async move {
engine-rust/src/main.rs:242:        strategy::run_strategy_task(
engine-rust/src/main.rs:246:            persist_tx_strategy,
engine-rust/src/main.rs:247:            metrics_strategy,
engine-rust/src/main.rs:317:            let _ = strategy_handle.await;
engine-rust/src/lib.rs:10:pub mod strategy;
engine-rust/src/strategy.rs:12:/// Run the strategy task with deterministic signal generation
engine-rust/src/strategy.rs:20:pub async fn run_strategy_task(
engine-rust/src/strategy.rs:32:        "strategy task started (deterministic stub)"
engine-rust/src/strategy.rs:90:        "strategy task ended (tick channel closed)"
engine-rust/src/strategy.rs:106:        // Spawn strategy task
engine-rust/src/strategy.rs:109:            run_strategy_task(5, tick_rx, signal_tx, persist_tx, metrics_clone).await;
engine-rust/src/strategy.rs:160:            run_strategy_task(3, tick_rx1, signal_tx1, persist_tx1, m1).await;
engine-rust/src/strategy.rs:163:            run_strategy_task(3, tick_rx2, signal_tx2, persist_tx2, m2).await;
engine-rust/src/execution.rs:166:/// * `signal_rx` - Channel to receive signals from strategy

## strategy.rs
$ sed -n '1,240p' engine-rust/src/strategy.rs
//! Strategy task - Deterministic signal generator
//!
//! Emits a signal every N ticks with reason codes (G4)
//! Implements S6 (backpressure) and S8 (determinism)

use crate::types::{EventId, Metrics, PersistEvent, ReasonCode, Side, Signal, Tick};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{info, warn};

/// Run the strategy task with deterministic signal generation
///
/// # Arguments
/// * `signal_every_n_ticks` - Emit signal every N ticks
/// * `tick_rx` - Channel to receive ticks from ingestion
/// * `signal_tx` - Channel to send signals to execution
/// * `persist_tx` - Channel to send signals to persistence
/// * `metrics` - Shared metrics for heartbeat
pub async fn run_strategy_task(
    signal_every_n_ticks: u64,
    mut tick_rx: mpsc::Receiver<Tick>,
    signal_tx: mpsc::Sender<Signal>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
) {
    let mut tick_count: u64 = 0;
    let mut last_side = Side::Buy;

    info!(
        signal_every_n = signal_every_n_ticks,
        "strategy task started (deterministic stub)"
    );

    while let Some(tick) = tick_rx.recv().await {
        tick_count += 1;

        // Deterministic signal emission every N ticks (S8)
        if tick_count % signal_every_n_ticks == 0 {
            // Alternate buy/sell for determinism
            let side = if last_side == Side::Buy {
                Side::Sell
            } else {
                Side::Buy
            };
            last_side = side;

            let signal = Signal {
                event_id: EventId::new(),
                symbol: tick.symbol.clone(),
                side,
                confidence: 0.75, // Fixed confidence for determinism
                reason: ReasonCode::PeriodicTrigger,
                desired_size: 0.1, // Fixed size for shadow mode
                ts: tick.ts,
            };

            metrics.signal_count.fetch_add(1, Ordering::Relaxed);

            info!(
                event_id = %signal.event_id,
                symbol = %signal.symbol,
                side = %signal.side,
                reason_code = %signal.reason,
                confidence = signal.confidence,
                desired_size = signal.desired_size,
                tick_count = tick_count,
                "signal generated"
            );

            // Send to execution (with backpressure tracking - S6)
            if signal_tx.try_send(signal.clone()).is_err() {
                metrics
                    .backpressure_drops_signal
                    .fetch_add(1, Ordering::Relaxed);
                warn!(
                    reason_code = "BP_DROP_SIGNAL",
                    channel = "signal",
                    "backpressure: dropped signal (channel full)"
                );
            }

            // Send to persist (non-blocking - I6)
            let _ = persist_tx.try_send(PersistEvent::Signal(signal));
        }
    }

    info!(
        total_signals = metrics.signal_count.load(Ordering::Relaxed),
        "strategy task ended (tick channel closed)"
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::now_ts_millis;

    #[tokio::test]
    async fn test_signal_generation_every_n_ticks() {
        let metrics = Arc::new(Metrics::new());
        let (tick_tx, tick_rx) = mpsc::channel(10);
        let (signal_tx, mut signal_rx) = mpsc::channel(10);
        let (persist_tx, _persist_rx) = mpsc::channel(10);

        // Spawn strategy task
        let metrics_clone = metrics.clone();
        let handle = tokio::spawn(async move {
            run_strategy_task(5, tick_rx, signal_tx, persist_tx, metrics_clone).await;
        });

        // Send 10 ticks
        for i in 0..10 {
            let tick = Tick {
                event_id: EventId::new(),
                symbol: "TEST/USD".to_string(),
                price: 100.0 + i as f64,
                volume: 1.0,
                ts: now_ts_millis(),
            };
            tick_tx.send(tick).await.unwrap();
        }

        // Drop sender to close channel
        drop(tick_tx);

        // Wait for task to complete
        handle.await.unwrap();

        // Should have 2 signals (at tick 5 and 10)
        let mut signals = vec![];
        while let Ok(s) = signal_rx.try_recv() {
            signals.push(s);
        }
        assert_eq!(signals.len(), 2);

        // First signal should be Sell (alternates from initial Buy)
        assert_eq!(signals[0].side, Side::Sell);
        // Second should be Buy
        assert_eq!(signals[1].side, Side::Buy);
    }

    #[tokio::test]
    async fn test_signal_determinism() {
        // Same input should produce same signals
        let metrics1 = Arc::new(Metrics::new());
        let metrics2 = Arc::new(Metrics::new());

        let (tick_tx1, tick_rx1) = mpsc::channel(10);
        let (tick_tx2, tick_rx2) = mpsc::channel(10);
        let (signal_tx1, mut signal_rx1) = mpsc::channel(10);
        let (signal_tx2, mut signal_rx2) = mpsc::channel(10);
        let (persist_tx1, _) = mpsc::channel(10);
        let (persist_tx2, _) = mpsc::channel(10);

        let m1 = metrics1.clone();
        let m2 = metrics2.clone();

        let h1 = tokio::spawn(async move {
            run_strategy_task(3, tick_rx1, signal_tx1, persist_tx1, m1).await;
        });
        let h2 = tokio::spawn(async move {
            run_strategy_task(3, tick_rx2, signal_tx2, persist_tx2, m2).await;
        });

        // Send identical tick sequences
        for i in 0..6 {
            let tick1 = Tick {
                event_id: EventId::new(),
                symbol: "TEST/USD".to_string(),
                price: 100.0 + i as f64,
                volume: 1.0,
                ts: 1000000 + i,
            };
            let tick2 = Tick {
                event_id: EventId::new(),
                symbol: "TEST/USD".to_string(),
                price: 100.0 + i as f64,
                volume: 1.0,
                ts: 1000000 + i,
            };
            tick_tx1.send(tick1).await.unwrap();
            tick_tx2.send(tick2).await.unwrap();
        }

        drop(tick_tx1);
        drop(tick_tx2);

        h1.await.unwrap();
        h2.await.unwrap();

        // Collect signals
        let mut signals1 = vec![];
        let mut signals2 = vec![];
        while let Ok(s) = signal_rx1.try_recv() {
            signals1.push(s);
        }
        while let Ok(s) = signal_rx2.try_recv() {
            signals2.push(s);
        }

        // Same number of signals
        assert_eq!(signals1.len(), signals2.len());

        // Same sides (S8: determinism)
        for (s1, s2) in signals1.iter().zip(signals2.iter()) {
            assert_eq!(s1.side, s2.side);
            assert_eq!(s1.confidence, s2.confidence);
            assert_eq!(s1.desired_size, s2.desired_size);
        }
    }
}

## Ingest modules
$ ls -la engine-rust/src/ingest
total 36
drwxrwxr-x 2 slimy slimy  4096 Jan  9 12:56 .
drwxrwxr-x 4 slimy slimy  4096 Jan  9 12:56 ..
-rw-rw-r-- 1 slimy slimy 10272 Jan  9 14:54 mod.rs
-rw-rw-r-- 1 slimy slimy  8628 Jan  9 16:16 realws.rs
-rw-rw-r-- 1 slimy slimy   540 Jan  9 12:54 ws_sources.rs

## ingest/mod.rs
$ sed -n '1,260p' engine-rust/src/ingest/mod.rs
//! Ingestion task - Deterministic tick generator, Replay, MockWS, and RealWS
//!
//! Implements S6 (backpressure) via try_send with counter
//! Implements Replay (from DB) and MockWS (with reconnect)

pub mod realws;
pub mod ws_sources;

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
                config.sample_every,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            )
            .await
        }
        IngestMode::Replay => {
            run_replay(symbol, config.sample_every, pool, tick_tx, persist_tx, metrics, shutdown).await
        }
        IngestMode::MockWs => {
            let url = config.ws_url.unwrap_or_else(|| "ws://localhost:9001".to_string());
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
            realws::run_real_ws(
                symbol,
                config,
                tick_tx,
                persist_tx,
                metrics,
                shutdown,
            ).await
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

async fn run_replay(
    symbol: String,
    sample_every: u64,
    pool: SqlitePool,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    info!(mode = "REPLAY", sample_every = sample_every, "ingest task started");

    let mut offset = 0;
    let limit = 1000;
    let mut sequence = 0u64;
    
    loop {
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

## ingest/mod.rs (continued)
$ sed -n '260,520p' engine-rust/src/ingest/mod.rs
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
        metrics.backpressure_drops_tick.fetch_add(1, Ordering::Relaxed);
        error!(reason = "OVERLOAD", "tick channel full, exiting 13");
        // G5: Deterministic overload handling -> Exit 13
        std::process::exit(13);
    }
    if persist_tx.try_send(PersistEvent::Tick(tick)).is_err() {
        metrics.backpressure_drops_persist.fetch_add(1, Ordering::Relaxed);
        // Persist channel full is bad but maybe not fatal? 
        // Prompt says "Backpressure (channel full ... saturated) -> exit 13"
        // Let's being strict.
        error!(reason = "OVERLOAD", "persist channel full, exiting 13");
        std::process::exit(13);
    }
}

## config.rs
$ sed -n '1,260p' engine-rust/src/config.rs
//! Configuration module for engine-rust
//!
//! Implements G0 (SHADOW_MODE default) and G1 (LIVE mode fail-closed)

use anyhow::{bail, Result};
use serde::Deserialize;
use std::path::Path;

/// Execution mode enum (G0: Shadow is default)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Default)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ExecutionMode {
    #[default]
    Shadow, // Default - records shadow orders only (S9, I1)
    Paper, // Simulated fills, no real network
    Live,  // BLOCKED unless gate G1 satisfied
}

impl std::fmt::Display for ExecutionMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExecutionMode::Shadow => write!(f, "SHADOW"),
            ExecutionMode::Paper => write!(f, "PAPER"),
            ExecutionMode::Live => write!(f, "LIVE"),
        }
    }
}

/// Risk caps configuration (I2)
#[derive(Debug, Clone, Deserialize)]
pub struct RiskCaps {
    #[serde(default = "default_max_exposure")]
    pub max_exposure_usd: f64,
    #[serde(default = "default_max_symbol_exposure")]
    pub max_symbol_exposure_usd: f64,
    #[serde(default = "default_max_open_orders")]
    pub max_open_orders: usize,
}

fn default_max_exposure() -> f64 {
    10_000.0
}
fn default_max_symbol_exposure() -> f64 {
    5_000.0
}
fn default_max_open_orders() -> usize {
    10
}

impl Default for RiskCaps {
    fn default() -> Self {
        Self {
            max_exposure_usd: default_max_exposure(),
            max_symbol_exposure_usd: default_max_symbol_exposure(),
            max_open_orders: default_max_open_orders(),
        }
    }
}

/// Channel configuration (S6: bounded channels)
#[derive(Debug, Clone, Deserialize)]
pub struct ChannelConfig {
    #[serde(default = "default_tick_channel")]
    pub tick_channel_size: usize,
    #[serde(default = "default_signal_channel")]
    pub signal_channel_size: usize,
    #[serde(default = "default_persist_channel")]
    pub persist_channel_size: usize,
}

fn default_tick_channel() -> usize {
    256
}
fn default_signal_channel() -> usize {
    64
}
fn default_persist_channel() -> usize {
    512
}

impl Default for ChannelConfig {
    fn default() -> Self {
        Self {
            tick_channel_size: default_tick_channel(),
            signal_channel_size: default_signal_channel(),
            persist_channel_size: default_persist_channel(),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Default)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum IngestMode {
    #[default]
    Synthetic, // Deterministic generator
    Replay,    // From DB (ticks table)
    MockWs,    // WebSocket (ws://localhost...)
    RealWs,    // Real WebSocket ingestion (Option A)
}

impl std::fmt::Display for IngestMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            IngestMode::Synthetic => write!(f, "SYNTHETIC"),
            IngestMode::Replay => write!(f, "REPLAY"),
            IngestMode::MockWs => write!(f, "MOCK_WS"),
            IngestMode::RealWs => write!(f, "REAL_WS"),
        }
    }
}

/// Engine configuration
#[derive(Debug, Clone, Deserialize)]
pub struct EngineConfig {
    #[serde(default)]
    pub ingest_mode: IngestMode,
    #[serde(default = "default_tick_interval")]
    pub tick_interval_ms: u64,
    #[serde(default = "default_signal_every_n")]
    pub signal_every_n_ticks: u64,
    #[serde(default = "default_heartbeat_interval")]
    pub heartbeat_interval_secs: u64,
    #[serde(default = "default_run_seconds")]
    pub run_seconds: Option<u64>,
    #[serde(default)]
    pub ws_url: Option<String>,
    #[serde(default = "default_sample_every")]
    pub sample_every: u64,
}

fn default_tick_interval() -> u64 {
    500
}
fn default_signal_every_n() -> u64 {
    10
}
fn default_heartbeat_interval() -> u64 {
    10
}
fn default_run_seconds() -> Option<u64> {
    None
}
fn default_sample_every() -> u64 {
    1
}

impl Default for EngineConfig {
    fn default() -> Self {
        Self {
            ingest_mode: IngestMode::default(),
            tick_interval_ms: default_tick_interval(),
            signal_every_n_ticks: default_signal_every_n(),
            heartbeat_interval_secs: default_heartbeat_interval(),
            run_seconds: default_run_seconds(),
            ws_url: None,
            sample_every: default_sample_every(),
        }
    }
}

/// App configuration
#[derive(Debug, Clone, Deserialize)]
pub struct AppConfig {
    pub symbol: String,
    pub db_path: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            symbol: "SOL/USDC".to_string(),
            db_path: "/opt/hybrid-trading-bot/data/bot.db".to_string(),
        }
    }
}

/// Main configuration struct
#[derive(Debug, Clone, Deserialize)]
pub struct Config {
    #[serde(default)]
    pub mode: ExecutionMode,
    #[serde(default)]
    pub live_armed: bool,
    #[serde(default)]
    pub app: AppConfig,
    #[serde(default)]
    pub engine: EngineConfig,
    #[serde(default)]
    pub risk_caps: RiskCaps,
    #[serde(default)]
    pub channels: ChannelConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            mode: ExecutionMode::default(),
            live_armed: false,
            app: AppConfig::default(),
            engine: EngineConfig::default(),
            risk_caps: RiskCaps::default(),
            channels: ChannelConfig::default(),
        }
    }
}

impl Config {
    /// Load configuration from TOML file
    pub fn load(path: &str) -> Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }

    /// Validate configuration (G0, G1: fail-closed for LIVE mode)
    pub fn validate(&self) -> Result<()> {
        if self.mode == ExecutionMode::Live {
            // G1: LIVE_MODE requires explicit arming
            if !self.live_armed {
                bail!(
                    "LIVE_MODE requires live_armed=true in config (G1 fail-closed). \
                     This is a safety gate to prevent accidental live trading."
                );
            }

            // G1: Check for proof bundle existence
            let proof_path = Path::new("/opt/hybrid-trading-bot/data/proof_bundle.json");
            if !proof_path.exists() {
                bail!(
                    "LIVE_MODE requires proof bundle at {:?} (G1 fail-closed). \
                     Run shadow/paper tests first to generate proof.",
                    proof_path
                );
            }

            tracing::warn!(
                "LIVE_MODE activated - this will place REAL orders! \
                 Ensure you have reviewed all safety checks."
            );
        }

        // Validate risk caps
        if self.risk_caps.max_exposure_usd <= 0.0 {
            bail!("max_exposure_usd must be positive");
        }
        if self.risk_caps.max_symbol_exposure_usd <= 0.0 {
            bail!("max_symbol_exposure_usd must be positive");
        }
        if self.risk_caps.max_open_orders == 0 {
            bail!("max_open_orders must be at least 1");
        }

        // Validate channel sizes
        if self.channels.tick_channel_size == 0 {
            bail!("tick_channel_size must be at least 1");
        }

        Ok(())
    }
}

## main.rs
$ sed -n '1,260p' engine-rust/src/main.rs
//! Engine-Rust: Phase 2 Tokio Pipeline Skeleton
//!
//! Pipeline: ingest → strategy → execute(shadow) → persist
//!
//! Guardrails:
//! - G0: SHADOW_MODE default, LIVE fails closed
//! - G1: healthcheck.sh must PASS
//! - G3: PRAGMAs verified at startup
//! - G4: Heartbeat every 10s with structured logs
//! - G5: Behavior maps to spec

mod config;
mod db;
mod execution;
mod ingest;
mod persist;
mod strategy;
mod types;

use anyhow::Result;
use clap::Parser;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc};
use tokio::time::{interval, Duration};
use tracing::{error, info, warn};

use config::{Config, ExecutionMode};
use types::Metrics;

/// Exit codes for deterministic control
pub const EXIT_COMPLETE: i32 = 0;
pub const EXIT_NETWORK: i32 = 10;
pub const EXIT_PARSE: i32 = 11;
pub const EXIT_CONFIG: i32 = 12;
pub const EXIT_OVERLOAD: i32 = 13;

/// Command line arguments
#[derive(Parser, Debug)]
#[command(name = "engine-rust")]
#[command(about = "Phase 2 Rust Pipeline Skeleton - Shadow Mode Trading Engine")]
struct Args {
    /// Execution mode (shadow, paper, live)
    #[arg(long, default_value = "shadow")]
    mode: String,

    /// Path to config file
    #[arg(long, default_value = "/opt/hybrid-trading-bot/config/config.toml")]
    config: String,

    /// Run for N seconds then exit (for testing)
    #[arg(long)]
    seconds: Option<u64>,

    /// Path to database
    #[arg(long)]
    db: Option<String>,

    /// Ingestion mode (synthetic, replay, mockws)
    #[arg(long)]
    ingest: Option<String>,

    /// WebSocket URL for mockws mode
    #[arg(long)]
    ws_url: Option<String>,

    /// Sample every N ticks (1 = all, 10 = 10% ingestion)
    #[arg(long)]
    sample_every: Option<u64>,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing with JSON for structured logs (G4)
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .json()
        .init();

    info!(
        version = env!("CARGO_PKG_VERSION"),
        "engine-rust starting (Phase 2 skeleton)"
    );

    // Parse command line arguments
    let args = Args::parse();

    // Load configuration
    let mut config = if std::path::Path::new(&args.config).exists() {
        match Config::load(&args.config) {
            Ok(config) => config,
            Err(err) => {
                if is_toml_parse_error(&err) {
                    error!(
                        config_path = %args.config,
                        error = %err,
                        "config TOML parse failed"
                    );
                    std::process::exit(EXIT_CONFIG);
                }
                return Err(err);
            }
        }
    } else {
        info!(
            config_path = %args.config,
            "config file not found, using defaults"
        );
        Config::default()
    };

    // Override mode from CLI
    config.mode = match args.mode.to_lowercase().as_str() {
        "shadow" => ExecutionMode::Shadow,
        "paper" => ExecutionMode::Paper,
        "live" => ExecutionMode::Live,
        _ => {
            warn!(mode = %args.mode, "unknown mode, defaulting to SHADOW");
            ExecutionMode::Shadow
        }
    };

    // Override run duration from CLI
    if let Some(secs) = args.seconds {
        config.engine.run_seconds = Some(secs);
    }

    // Override db path from CLI
    if let Some(db_path) = args.db {
        config.app.db_path = db_path;
    }

    // Override ingest mode
    if let Some(ingest) = args.ingest {
        config.engine.ingest_mode = match ingest.to_lowercase().as_str() {
            "synthetic" => config::IngestMode::Synthetic,
            "replay" => config::IngestMode::Replay,
            "mockws" => config::IngestMode::MockWs,
            "realws" => config::IngestMode::RealWs,
            _ => {
                warn!(ingest = %ingest, "unknown ingest mode, defaulting to SYNTHETIC");
                config::IngestMode::Synthetic
            }
        };
    }

    // Override ws_url
    if let Some(url) = args.ws_url {
        config.engine.ws_url = Some(url);
    }

    // Override sample_every
    if let Some(sample) = args.sample_every {
        config.engine.sample_every = sample;
    }

    // Validate configuration (G0, G1: fail-closed for LIVE mode)
    config.validate()?;

    info!(
        mode = %config.mode,
        symbol = %config.app.symbol,
        db_path = %config.app.db_path,
        tick_interval_ms = config.engine.tick_interval_ms,
        signal_every_n = config.engine.signal_every_n_ticks,
        heartbeat_secs = config.engine.heartbeat_interval_secs,
        run_seconds = ?config.engine.run_seconds,
        "configuration loaded (G0: shadow mode default enforced)"
    );

    // Create DB pool and verify PRAGMAs (S1, G3)
    let pool = db::create_pool(&config.app.db_path).await?;
    db::verify_pragmas(&pool, &db::PragmaRequirements::default()).await?;
    db::ensure_schema(&pool).await?;

    // Log initial row counts
    let (ticks, signals, orders, trades) = db::get_row_counts(&pool).await?;
    info!(
        ticks = ticks,
        signals = signals,
        orders = orders,
        trades = trades,
        "initial database state"
    );

    // Create shared metrics (G4)
    let metrics = Arc::new(Metrics::new());

    // Create channels (S6: bounded with documented sizes)
    let (tick_tx, tick_rx) = mpsc::channel(config.channels.tick_channel_size);
    let (signal_tx, signal_rx) = mpsc::channel(config.channels.signal_channel_size);
    let (persist_tx, persist_rx) = mpsc::channel(config.channels.persist_channel_size);

    info!(
        tick_channel = config.channels.tick_channel_size,
        signal_channel = config.channels.signal_channel_size,
        persist_channel = config.channels.persist_channel_size,
        "channels created (S6: bounded, backpressure policy: DROP_OLDEST with metrics)"
    );

    // Create shutdown broadcast channel
    let (shutdown_tx, _) = broadcast::channel::<()>(1);

    // Clone for tasks
    let persist_tx_ingest = persist_tx.clone();
    let persist_tx_strategy = persist_tx.clone();
    let metrics_ingest = metrics.clone();
    let metrics_strategy = metrics.clone();
    let metrics_execution = metrics.clone();
    let metrics_persist = metrics.clone();
    let metrics_heartbeat = metrics.clone();

    let signal_every_n = config.engine.signal_every_n_ticks;
    let mode = config.mode;
    let risk_caps = config.risk_caps.clone();
    let heartbeat_interval = config.engine.heartbeat_interval_secs;
    let run_seconds = config.engine.run_seconds;

    // Spawn ingest task
    let shutdown_rx_ingest = shutdown_tx.subscribe();
    let engine_config = config.engine.clone();
    let db_pool = pool.clone(); // Needed for replay
    
    let ingest_handle = tokio::spawn(async move {
        ingest::run_ingest_task(
            config.app.symbol,
            engine_config,
            db_pool,
            tick_tx,
            persist_tx_ingest,
            metrics_ingest,
            shutdown_rx_ingest,
        )
        .await;
    });

    // Spawn strategy task
    let strategy_handle = tokio::spawn(async move {
        strategy::run_strategy_task(
            signal_every_n,
            tick_rx,
            signal_tx,
            persist_tx_strategy,
            metrics_strategy,
        )
        .await;
    });

    // Spawn execution task
    let execution_handle = tokio::spawn(async move {
        execution::run_execution_task(mode, risk_caps, signal_rx, persist_tx, metrics_execution)
            .await;
    });

    // Spawn persist task
    let persist_handle = tokio::spawn(async move {
        persist::run_persist_task(pool, persist_rx, metrics_persist).await;

## main.rs (continued)
$ sed -n '260,640p' engine-rust/src/main.rs
        persist::run_persist_task(pool, persist_rx, metrics_persist).await;
    });

    // Spawn heartbeat task (G4: every N seconds)
    let heartbeat_handle = tokio::spawn(async move {
        let mut timer = interval(Duration::from_secs(heartbeat_interval));
        loop {
            timer.tick().await;
            info!(
                tick_count = metrics_heartbeat.tick_count.load(Ordering::Relaxed),
                signal_count = metrics_heartbeat.signal_count.load(Ordering::Relaxed),
                shadow_orders = metrics_heartbeat.shadow_order_count.load(Ordering::Relaxed),
                trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                bp_drops_tick = metrics_heartbeat
                    .backpressure_drops_tick
                    .load(Ordering::Relaxed),
                bp_drops_signal = metrics_heartbeat
                    .backpressure_drops_signal
                    .load(Ordering::Relaxed),
                bp_drops_persist = metrics_heartbeat
                    .backpressure_drops_persist
                    .load(Ordering::Relaxed),
                risk_vetoes = metrics_heartbeat.risk_vetoes.load(Ordering::Relaxed),
                "HEARTBEAT (G4)"
            );
        }
    });

    info!("all tasks spawned, pipeline running");

    // Wait for shutdown signal or timeout
    if let Some(secs) = run_seconds {
        info!(seconds = secs, "running for fixed duration");
        tokio::time::sleep(Duration::from_secs(secs)).await;
        warn!("fixed duration elapsed, initiating shutdown");
    } else {
        // Wait for SIGINT/CTRL-C (S13: graceful shutdown)
        info!("waiting for shutdown signal (CTRL-C)");
        tokio::signal::ctrl_c().await?;
        warn!("shutdown signal received (S13: graceful shutdown)");
    }

    // Signal shutdown
    let _ = shutdown_tx.send(());

    // Abort heartbeat (it runs forever)
    heartbeat_handle.abort();

    // Wait for tasks to complete (with timeout)
    let shutdown_timeout = Duration::from_secs(5);
    tokio::select! {
        _ = async {
            let _ = ingest_handle.await;
            let _ = strategy_handle.await;
            let _ = execution_handle.await;
            let _ = persist_handle.await;
        } => {
            info!("all tasks completed gracefully");
        }
        _ = tokio::time::sleep(shutdown_timeout) => {
            warn!("shutdown timeout, some tasks may not have completed");
        }
    }

    // Log final metrics
    info!(
        tick_count = metrics.tick_count.load(Ordering::Relaxed),
        signal_count = metrics.signal_count.load(Ordering::Relaxed),
        shadow_orders = metrics.shadow_order_count.load(Ordering::Relaxed),
        trade_count = metrics.trade_count.load(Ordering::Relaxed),
        persist_count = metrics.persist_count.load(Ordering::Relaxed),
        persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
        bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
        bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
        risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
        "FINAL METRICS"
    );

    info!("engine-rust shutdown complete");
    Ok(())
}

fn is_toml_parse_error(err: &anyhow::Error) -> bool {
    err.downcast_ref::<toml::de::Error>().is_some()
}

#[cfg(test)]
mod tests {
    use super::is_toml_parse_error;
    use crate::config::Config;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn invalid_toml_is_classified_as_config_error() {
        let mut path = std::env::temp_dir();
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time ok")
            .as_nanos();
        path.push(format!("engine_config_invalid_{unique}.toml"));

        fs::write(&path, "invalid = [toml").expect("write invalid toml");
        let err = Config::load(path.to_str().expect("path utf-8")).unwrap_err();
        assert!(is_toml_parse_error(&err));
        let _ = fs::remove_file(&path);
    }
}

## types.rs
$ sed -n '1,220p' engine-rust/src/types.rs
//! Core domain types for the trading pipeline
//!
//! Implements event_id for idempotency (I3) and reason codes (G4)

use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Unique event identifier for idempotency (I3)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct EventId(pub Uuid);

impl EventId {
    pub fn new() -> Self {
        Self(Uuid::new_v4())
    }
}

impl Default for EventId {
    fn default() -> Self {
        Self::new()
    }
}

impl std::fmt::Display for EventId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Reason codes for signals and order actions (G4: structured logging)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ReasonCode {
    // Signal generation reasons
    PeriodicTrigger,  // Deterministic N-tick trigger
    ThresholdCrossed, // Price threshold crossed (future)

    // Veto reasons
    RiskCap,   // I2: exposure exceeded
    StaleData, // S7: timestamp drift exceeded

    // Order lifecycle
    Submitted,
    Acknowledged,
    PartialFill,
    Filled,
    Canceled,
    Rejected,

    // Shadow-specific
    ShadowRecorded, // S9: shadow order logged
}

impl std::fmt::Display for ReasonCode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ReasonCode::PeriodicTrigger => write!(f, "PERIODIC_TRIGGER"),
            ReasonCode::ThresholdCrossed => write!(f, "THRESHOLD_CROSSED"),
            ReasonCode::RiskCap => write!(f, "RISK_CAP"),
            ReasonCode::StaleData => write!(f, "STALE_DATA"),
            ReasonCode::Submitted => write!(f, "SUBMITTED"),
            ReasonCode::Acknowledged => write!(f, "ACKNOWLEDGED"),
            ReasonCode::PartialFill => write!(f, "PARTIAL_FILL"),
            ReasonCode::Filled => write!(f, "FILLED"),
            ReasonCode::Canceled => write!(f, "CANCELED"),
            ReasonCode::Rejected => write!(f, "REJECTED"),
            ReasonCode::ShadowRecorded => write!(f, "SHADOW_RECORDED"),
        }
    }
}

/// Market data tick
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tick {
    pub event_id: EventId,
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub ts: i64, // Unix timestamp in milliseconds
}

/// Order side
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Side {
    Buy,
    Sell,
}

impl std::fmt::Display for Side {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Side::Buy => write!(f, "BUY"),
            Side::Sell => write!(f, "SELL"),
        }
    }
}

/// Strategy signal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Signal {
    pub event_id: EventId,
    pub symbol: String,
    pub side: Side,
    pub confidence: f64, // 0.0 - 1.0
    pub reason: ReasonCode,
    pub desired_size: f64,
    pub ts: i64,
}

/// Order status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OrderStatus {
    Submitted,
    Acknowledged,
    PartialFill,
    Filled,
    Canceled,
    Rejected,
}

impl std::fmt::Display for OrderStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            OrderStatus::Submitted => write!(f, "SUBMITTED"),
            OrderStatus::Acknowledged => write!(f, "ACKNOWLEDGED"),
            OrderStatus::PartialFill => write!(f, "PARTIAL_FILL"),
            OrderStatus::Filled => write!(f, "FILLED"),
            OrderStatus::Canceled => write!(f, "CANCELED"),
            OrderStatus::Rejected => write!(f, "REJECTED"),
        }
    }
}

/// Order record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    pub event_id: EventId,
    pub signal_id: EventId, // Links back to originating signal
    pub symbol: String,
    pub side: Side,
    pub qty: f64,
    pub price: Option<f64>, // None for market orders
    pub status: OrderStatus,
    pub reason: ReasonCode,
    pub ts: i64,
    pub is_shadow: bool, // S9: true in SHADOW_MODE
}

/// Trade (fill) record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub event_id: EventId,
    pub order_id: EventId,
    pub symbol: String,
    pub side: Side,
    pub fill_qty: f64,
    pub fill_price: f64,
    pub fees: f64,
    pub ts: i64,
    pub is_shadow: bool,
}

/// Wrapper for all persistable events
#[derive(Debug, Clone)]
pub enum PersistEvent {
    Tick(Tick),
    Signal(Signal),
    Order(Order),
    Trade(Trade),
}

/// Metrics counters for heartbeat (G4)
#[derive(Debug, Default)]
pub struct Metrics {
    pub tick_count: std::sync::atomic::AtomicU64,
    pub signal_count: std::sync::atomic::AtomicU64,
    pub shadow_order_count: std::sync::atomic::AtomicU64,
    pub trade_count: std::sync::atomic::AtomicU64,
    pub persist_count: std::sync::atomic::AtomicU64,
    pub persist_errors: std::sync::atomic::AtomicU64,
    pub ingest_received: std::sync::atomic::AtomicU64,
    pub ingest_processed: std::sync::atomic::AtomicU64,
    pub backpressure_drops_tick: std::sync::atomic::AtomicU64,
    pub backpressure_drops_signal: std::sync::atomic::AtomicU64,
    pub backpressure_drops_persist: std::sync::atomic::AtomicU64,
    pub risk_vetoes: std::sync::atomic::AtomicU64,
}

impl Metrics {
    pub fn new() -> Self {
        Self::default()
    }
}

/// Get current timestamp in milliseconds
pub fn now_ts_millis() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .expect("Time went backwards")
        .as_millis() as i64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_id_unique() {
        let id1 = EventId::new();
        let id2 = EventId::new();
        assert_ne!(id1, id2);
    }

    #[test]
    fn test_reason_code_display() {
        assert_eq!(format!("{}", ReasonCode::ShadowRecorded), "SHADOW_RECORDED");
        assert_eq!(format!("{}", ReasonCode::RiskCap), "RISK_CAP");
    }

## engine-rust/tests tree
$ ls -la engine-rust/tests
total 32
drwxrwxr-x 3 slimy slimy  4096 Jan  9 12:56 .
drwxrwxr-x 5 slimy slimy  4096 Jan  9 12:32 ..
drwxrwxr-x 2 slimy slimy  4096 Jan  9 12:56 fixtures
-rw-rw-r-- 1 slimy slimy  5599 Jan  9 12:03 pragma_verification.rs
-rw-rw-r-- 1 slimy slimy 11121 Jan  9 12:03 property_tests.rs

## main.rs (top for patch)
$ sed -n '1,120p' engine-rust/src/main.rs
//! Engine-Rust: Phase 2 Tokio Pipeline Skeleton
//!
//! Pipeline: ingest → strategy → execute(shadow) → persist
//!
//! Guardrails:
//! - G0: SHADOW_MODE default, LIVE fails closed
//! - G1: healthcheck.sh must PASS
//! - G3: PRAGMAs verified at startup
//! - G4: Heartbeat every 10s with structured logs
//! - G5: Behavior maps to spec

mod config;
mod db;
mod execution;
mod ingest;
mod persist;
mod strategy;
mod types;

use anyhow::Result;
use clap::Parser;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc};
use tokio::time::{interval, Duration};
use tracing::{error, info, warn};

use config::{Config, ExecutionMode};
use types::Metrics;

/// Exit codes for deterministic control
pub const EXIT_COMPLETE: i32 = 0;
pub const EXIT_NETWORK: i32 = 10;
pub const EXIT_PARSE: i32 = 11;
pub const EXIT_CONFIG: i32 = 12;
pub const EXIT_OVERLOAD: i32 = 13;

/// Command line arguments
#[derive(Parser, Debug)]
#[command(name = "engine-rust")]
#[command(about = "Phase 2 Rust Pipeline Skeleton - Shadow Mode Trading Engine")]
struct Args {
    /// Execution mode (shadow, paper, live)
    #[arg(long, default_value = "shadow")]
    mode: String,

    /// Path to config file
    #[arg(long, default_value = "/opt/hybrid-trading-bot/config/config.toml")]
    config: String,

    /// Run for N seconds then exit (for testing)
    #[arg(long)]
    seconds: Option<u64>,

    /// Path to database
    #[arg(long)]
    db: Option<String>,

    /// Ingestion mode (synthetic, replay, mockws)
    #[arg(long)]
    ingest: Option<String>,

    /// WebSocket URL for mockws mode
    #[arg(long)]
    ws_url: Option<String>,

    /// Sample every N ticks (1 = all, 10 = 10% ingestion)
    #[arg(long)]
    sample_every: Option<u64>,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing with JSON for structured logs (G4)
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .json()
        .init();

    info!(
        version = env!("CARGO_PKG_VERSION"),
        "engine-rust starting (Phase 2 skeleton)"
    );

    // Parse command line arguments
    let args = Args::parse();

    // Load configuration
    let mut config = if std::path::Path::new(&args.config).exists() {
        match Config::load(&args.config) {
            Ok(config) => config,
            Err(err) => {
                if is_toml_parse_error(&err) {
                    error!(
                        config_path = %args.config,
                        error = %err,
                        "config TOML parse failed"
                    );
                    std::process::exit(EXIT_CONFIG);
                }
                return Err(err);
            }
        }
    } else {
        info!(
            config_path = %args.config,
            "config file not found, using defaults"
        );
        Config::default()
    };

    // Override mode from CLI
    config.mode = match args.mode.to_lowercase().as_str() {
        "shadow" => ExecutionMode::Shadow,
        "paper" => ExecutionMode::Paper,
        "live" => ExecutionMode::Live,
        _ => {

## main.rs (config overrides)
$ rg -n "Override ingest mode" -C 4 engine-rust/src/main.rs
136-    if let Some(db_path) = args.db {
137-        config.app.db_path = db_path;
138-    }
139-
140:    // Override ingest mode
141-    if let Some(ingest) = args.ingest {
142-        config.engine.ingest_mode = match ingest.to_lowercase().as_str() {
143-            "synthetic" => config::IngestMode::Synthetic,
144-            "replay" => config::IngestMode::Replay,

## main.rs (config log)
$ rg -n "configuration loaded" -n engine-rust/src/main.rs
180:        "configuration loaded (G0: shadow mode default enforced)"

## main.rs (config log block)
$ sed -n '160,210p' engine-rust/src/main.rs
    if let Some(url) = args.ws_url {
        config.engine.ws_url = Some(url);
    }

    // Override sample_every
    if let Some(sample) = args.sample_every {
        config.engine.sample_every = sample;
    }

    // Validate configuration (G0, G1: fail-closed for LIVE mode)
    config.validate()?;

    info!(
        mode = %config.mode,
        symbol = %config.app.symbol,
        db_path = %config.app.db_path,
        tick_interval_ms = config.engine.tick_interval_ms,
        signal_every_n = config.engine.signal_every_n_ticks,
        heartbeat_secs = config.engine.heartbeat_interval_secs,
        run_seconds = ?config.engine.run_seconds,
        "configuration loaded (G0: shadow mode default enforced)"
    );

    // Create DB pool and verify PRAGMAs (S1, G3)
    let pool = db::create_pool(&config.app.db_path).await?;
    db::verify_pragmas(&pool, &db::PragmaRequirements::default()).await?;
    db::ensure_schema(&pool).await?;

    // Log initial row counts
    let (ticks, signals, orders, trades) = db::get_row_counts(&pool).await?;
    info!(
        ticks = ticks,
        signals = signals,
        orders = orders,
        trades = trades,
        "initial database state"
    );

    // Create shared metrics (G4)
    let metrics = Arc::new(Metrics::new());

    // Create channels (S6: bounded with documented sizes)
    let (tick_tx, tick_rx) = mpsc::channel(config.channels.tick_channel_size);
    let (signal_tx, signal_rx) = mpsc::channel(config.channels.signal_channel_size);
    let (persist_tx, persist_rx) = mpsc::channel(config.channels.persist_channel_size);

    info!(
        tick_channel = config.channels.tick_channel_size,
        signal_channel = config.channels.signal_channel_size,
        persist_channel = config.channels.persist_channel_size,
        "channels created (S6: bounded, backpressure policy: DROP_OLDEST with metrics)"

## main.rs (signal_every_n block)
$ rg -n "signal_every_n" -n engine-rust/src/main.rs
227:    let signal_every_n = config.engine.signal_every_n_ticks;
254:            signal_every_n,

## main.rs (task spawn block)
$ sed -n '220,290p' engine-rust/src/main.rs
    let persist_tx_strategy = persist_tx.clone();
    let metrics_ingest = metrics.clone();
    let metrics_strategy = metrics.clone();
    let metrics_execution = metrics.clone();
    let metrics_persist = metrics.clone();
    let metrics_heartbeat = metrics.clone();

    let signal_every_n = config.engine.signal_every_n_ticks;
    let mode = config.mode;
    let risk_caps = config.risk_caps.clone();
    let heartbeat_interval = config.engine.heartbeat_interval_secs;
    let run_seconds = config.engine.run_seconds;

    // Spawn ingest task
    let shutdown_rx_ingest = shutdown_tx.subscribe();
    let engine_config = config.engine.clone();
    let db_pool = pool.clone(); // Needed for replay
    
    let ingest_handle = tokio::spawn(async move {
        ingest::run_ingest_task(
            config.app.symbol,
            engine_config,
            db_pool,
            tick_tx,
            persist_tx_ingest,
            metrics_ingest,
            shutdown_rx_ingest,
        )
        .await;
    });

    // Spawn strategy task
    let strategy_handle = tokio::spawn(async move {
        strategy::run_strategy_task(
            signal_every_n,
            tick_rx,
            signal_tx,
            persist_tx_strategy,
            metrics_strategy,
        )
        .await;
    });

    // Spawn execution task
    let execution_handle = tokio::spawn(async move {
        execution::run_execution_task(mode, risk_caps, signal_rx, persist_tx, metrics_execution)
            .await;
    });

    // Spawn persist task
    let persist_handle = tokio::spawn(async move {
        persist::run_persist_task(pool, persist_rx, metrics_persist).await;
    });

    // Spawn heartbeat task (G4: every N seconds)
    let heartbeat_handle = tokio::spawn(async move {
        let mut timer = interval(Duration::from_secs(heartbeat_interval));
        loop {
            timer.tick().await;
            info!(
                tick_count = metrics_heartbeat.tick_count.load(Ordering::Relaxed),
                signal_count = metrics_heartbeat.signal_count.load(Ordering::Relaxed),
                shadow_orders = metrics_heartbeat.shadow_order_count.load(Ordering::Relaxed),
                trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                bp_drops_tick = metrics_heartbeat
                    .backpressure_drops_tick
                    .load(Ordering::Relaxed),

## main.rs (wait block)
$ sed -n '320,400p' engine-rust/src/main.rs
        tokio::signal::ctrl_c().await?;
        warn!("shutdown signal received (S13: graceful shutdown)");
    }

    // Signal shutdown
    let _ = shutdown_tx.send(());

    // Abort heartbeat (it runs forever)
    heartbeat_handle.abort();

    // Wait for tasks to complete (with timeout)
    let shutdown_timeout = Duration::from_secs(5);
    tokio::select! {
        _ = async {
            let _ = ingest_handle.await;
            let _ = strategy_handle.await;
            let _ = execution_handle.await;
            let _ = persist_handle.await;
        } => {
            info!("all tasks completed gracefully");
        }
        _ = tokio::time::sleep(shutdown_timeout) => {
            warn!("shutdown timeout, some tasks may not have completed");
        }
    }

    // Log final metrics
    info!(
        tick_count = metrics.tick_count.load(Ordering::Relaxed),
        signal_count = metrics.signal_count.load(Ordering::Relaxed),
        shadow_orders = metrics.shadow_order_count.load(Ordering::Relaxed),
        trade_count = metrics.trade_count.load(Ordering::Relaxed),
        persist_count = metrics.persist_count.load(Ordering::Relaxed),
        persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
        bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
        bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
        risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
        "FINAL METRICS"
    );

    info!("engine-rust shutdown complete");
    Ok(())
}

fn is_toml_parse_error(err: &anyhow::Error) -> bool {
    err.downcast_ref::<toml::de::Error>().is_some()
}

#[cfg(test)]
mod tests {
    use super::is_toml_parse_error;
    use crate::config::Config;
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn invalid_toml_is_classified_as_config_error() {
        let mut path = std::env::temp_dir();
        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("time ok")
            .as_nanos();
        path.push(format!("engine_config_invalid_{unique}.toml"));

        fs::write(&path, "invalid = [toml").expect("write invalid toml");
        let err = Config::load(path.to_str().expect("path utf-8")).unwrap_err();
        assert!(is_toml_parse_error(&err));
        let _ = fs::remove_file(&path);
    }
}

## main.rs (wait logic context)
$ sed -n '280,340p' engine-rust/src/main.rs

    // Spawn heartbeat task (G4: every N seconds)
    let heartbeat_handle = tokio::spawn(async move {
        let mut timer = interval(Duration::from_secs(heartbeat_interval));
        loop {
            timer.tick().await;
            info!(
                tick_count = metrics_heartbeat.tick_count.load(Ordering::Relaxed),
                signal_count = metrics_heartbeat.signal_count.load(Ordering::Relaxed),
                shadow_orders = metrics_heartbeat.shadow_order_count.load(Ordering::Relaxed),
                trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                bp_drops_tick = metrics_heartbeat
                    .backpressure_drops_tick
                    .load(Ordering::Relaxed),
                bp_drops_signal = metrics_heartbeat
                    .backpressure_drops_signal
                    .load(Ordering::Relaxed),
                bp_drops_persist = metrics_heartbeat
                    .backpressure_drops_persist
                    .load(Ordering::Relaxed),
                risk_vetoes = metrics_heartbeat.risk_vetoes.load(Ordering::Relaxed),
                "HEARTBEAT (G4)"
            );
        }
    });

    info!("all tasks spawned, pipeline running");

    // Wait for shutdown signal or timeout
    if let Some(secs) = run_seconds {
        info!(seconds = secs, "running for fixed duration");
        tokio::time::sleep(Duration::from_secs(secs)).await;
        warn!("fixed duration elapsed, initiating shutdown");
    } else {
        // Wait for SIGINT/CTRL-C (S13: graceful shutdown)
        info!("waiting for shutdown signal (CTRL-C)");
        tokio::signal::ctrl_c().await?;
        warn!("shutdown signal received (S13: graceful shutdown)");
    }

    // Signal shutdown
    let _ = shutdown_tx.send(());

    // Abort heartbeat (it runs forever)
    heartbeat_handle.abort();

    // Wait for tasks to complete (with timeout)
    let shutdown_timeout = Duration::from_secs(5);
    tokio::select! {
        _ = async {
            let _ = ingest_handle.await;
            let _ = strategy_handle.await;
            let _ = execution_handle.await;
            let _ = persist_handle.await;
        } => {
            info!("all tasks completed gracefully");
        }

## strategy.rs (tests section)
$ rg -n "mod tests" -A 120 engine-rust/src/strategy.rs
158:mod tests {
159-    use super::*;
160-    use crate::types::now_ts_millis;
161-
162-    #[tokio::test]
163-    async fn test_sma_crossover_emits_buy_and_sell() {
164-        let metrics = Arc::new(Metrics::new());
165-        let (tick_tx, tick_rx) = mpsc::channel(64);
166-        let (signal_tx, mut signal_rx) = mpsc::channel(64);
167-        let (persist_tx, _persist_rx) = mpsc::channel(64);
168-
169-        let metrics_clone = metrics.clone();
170-        let handle = tokio::spawn(async move {
171-            run_strategy_task(tick_rx, signal_tx, persist_tx, metrics_clone).await;
172-        });
173-
174-        let mut ts = 1_000_000i64;
175-        for i in 0..50 {
176-            let price = if i < 20 {
177-                100.0
178-            } else if i < 30 {
179-                100.0 + (i as f64 - 19.0)
180-            } else {
181-                110.0 - (i as f64 - 29.0)
182-            };
183-            let tick = Tick {
184-                event_id: EventId::new(),
185-                symbol: "TEST/USD".to_string(),
186-                price,
187-                volume: 1.0,
188-                ts,
189-            };
190-            ts += 1;
191-            tick_tx.send(tick).await.unwrap();
192-        }
193-
194-        drop(tick_tx);
195-        handle.await.unwrap();
196-
197-        let mut signals = vec![];
198-        while let Ok(s) = signal_rx.try_recv() {
199-            signals.push(s);
200-        }
201-
202-        assert_eq!(signals.len(), 2);
203-        assert_eq!(signals[0].side, Side::Buy);
204-        assert_eq!(signals[1].side, Side::Sell);
205-        assert_eq!(signals[0].reason, ReasonCode::SmaCrossover);
206-    }
207-}

## ReasonCode usage
$ rg -n "SmaCrossover|SMA_CROSSOVER" engine-rust/src
engine-rust/src/types.rs:37:    SmaCrossover,     // SMA crossover (Phase 2.3)
engine-rust/src/types.rs:60:            ReasonCode::SmaCrossover => write!(f, "SMA_CROSSOVER"),
engine-rust/src/types.rs:222:        assert_eq!(format!("{}", ReasonCode::SmaCrossover), "SMA_CROSSOVER");
engine-rust/src/strategy.rs:116:                reason: ReasonCode::SmaCrossover,
engine-rust/src/strategy.rs:130:                event = "SMA_CROSSOVER",
engine-rust/src/strategy.rs:204:        assert_eq!(signals[0].reason, ReasonCode::SmaCrossover);

## run_strategy_task references
$ rg -n "run_strategy_task" -g'*.rs' engine-rust/src
engine-rust/src/main.rs:261:        strategy::run_strategy_task(
engine-rust/src/strategy.rs:26:pub async fn run_strategy_task(
engine-rust/src/strategy.rs:170:            run_strategy_task(tick_rx, signal_tx, persist_tx, metrics_clone).await;

## main.rs (strategy call)
$ sed -n '250,275p' engine-rust/src/main.rs
            tick_tx,
            persist_tx_ingest,
            metrics_ingest,
            shutdown_rx_ingest,
            replay_done_tx,
        )
        .await;
    });

    // Spawn strategy task
    let strategy_handle = tokio::spawn(async move {
        strategy::run_strategy_task(
            tick_rx,
            signal_tx,
            persist_tx_strategy,
            metrics_strategy,
        )
        .await;
    });

    // Spawn execution task
    let execution_handle = tokio::spawn(async move {
        execution::run_execution_task(mode, risk_caps, signal_rx, persist_tx, metrics_execution)
            .await;
    });


## Fixture generate
$ python3 - <<'PY'

## Remaining signal_every_n references
$ rg -n "signal_every_n" engine-rust/src
engine-rust/src/config.rs:119:    #[serde(default = "default_signal_every_n")]
engine-rust/src/config.rs:120:    pub signal_every_n_ticks: u64,
engine-rust/src/config.rs:136:fn default_signal_every_n() -> u64 {
engine-rust/src/config.rs:154:            signal_every_n_ticks: default_signal_every_n(),

## Git diff --stat
$ git diff --stat
 engine-rust/src/config.rs     |   3 +
 engine-rust/src/ingest/mod.rs | 137 +++++++++++++++++++++++++-
 engine-rust/src/main.rs       |  56 +++++++++--
 engine-rust/src/strategy.rs   | 218 ++++++++++++++++++++----------------------
 engine-rust/src/types.rs      |   3 +
 5 files changed, 295 insertions(+), 122 deletions(-)

## strategy.rs (SMA logic)
$ sed -n '1,170p' engine-rust/src/strategy.rs
//! Strategy task - SMA crossover
//!
//! Implements S6 (backpressure) and S8 (determinism)

use crate::types::{EventId, Metrics, PersistEvent, ReasonCode, Side, Signal, Tick};
use std::collections::VecDeque;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{debug, info, warn};

const SMA_SHORT_WINDOW: usize = 5;
const SMA_LONG_WINDOW: usize = 20;

fn sma_iter(values: impl Iterator<Item = f64>, count: usize) -> f64 {
    values.sum::<f64>() / count as f64
}

/// Run the strategy task with SMA crossover signal generation
///
/// # Arguments
/// * `tick_rx` - Channel to receive ticks from ingestion
/// * `signal_tx` - Channel to send signals to execution
/// * `persist_tx` - Channel to send signals to persistence
/// * `metrics` - Shared metrics for heartbeat
pub async fn run_strategy_task(
    mut tick_rx: mpsc::Receiver<Tick>,
    signal_tx: mpsc::Sender<Signal>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
) {
    let mut prices: VecDeque<f64> = VecDeque::with_capacity(SMA_LONG_WINDOW);
    let mut prev_diff: Option<f64> = None;

    info!(
        short_window = SMA_SHORT_WINDOW,
        long_window = SMA_LONG_WINDOW,
        "strategy task started (sma crossover)"
    );

    while let Some(tick) = tick_rx.recv().await {
        prices.push_back(tick.price);
        if prices.len() > SMA_LONG_WINDOW {
            prices.pop_front();
        }

        let short_len = prices.len().min(SMA_SHORT_WINDOW);
        let short_sma = sma_iter(
            prices.iter().skip(prices.len() - short_len).copied(),
            short_len,
        );
        let long_sma = sma_iter(prices.iter().copied(), prices.len());
        let curr_diff = short_sma - long_sma;

        if prices.len() < SMA_LONG_WINDOW {
            debug!(
                event = "SMA_CALC",
                short = short_sma,
                long = long_sma,
                prev_diff = prev_diff.unwrap_or(0.0),
                curr_diff = curr_diff,
                emit = false,
                action = "WARMUP",
                "sma calc"
            );
            continue;
        }

        if prev_diff.is_none() {
            debug!(
                event = "SMA_CALC",
                short = short_sma,
                long = long_sma,
                prev_diff = 0.0,
                curr_diff = curr_diff,
                emit = false,
                action = "NONE",
                "sma calc"
            );
            prev_diff = Some(curr_diff);
            continue;
        }

        let prev = prev_diff.unwrap_or(0.0);
        let mut emit = false;
        let mut action = "NONE";

        if prev <= 0.0 && curr_diff > 0.0 {
            emit = true;
            action = "BUY";
        } else if prev >= 0.0 && curr_diff < 0.0 {
            emit = true;
            action = "SELL";
        }

        debug!(
            event = "SMA_CALC",
            short = short_sma,
            long = long_sma,
            prev_diff = prev,
            curr_diff = curr_diff,
            emit = emit,
            action = action,
            "sma calc"
        );

        prev_diff = Some(curr_diff);

        if emit {
            let side = if action == "BUY" { Side::Buy } else { Side::Sell };
            let signal = Signal {
                event_id: EventId::new(),
                symbol: tick.symbol.clone(),
                side,
                confidence: 0.75, // Fixed confidence for determinism
                reason: ReasonCode::SmaCrossover,
                desired_size: 0.1, // Fixed size for shadow mode
                ts: tick.ts,
            };

            metrics.signal_count.fetch_add(1, Ordering::Relaxed);

            info!(
                event_id = %signal.event_id,
                symbol = %signal.symbol,
                side = %signal.side,
                reason_code = %signal.reason,
                confidence = signal.confidence,
                desired_size = signal.desired_size,
                event = "SMA_CROSSOVER",
                "signal generated"
            );

            // Send to execution (with backpressure tracking - S6)
            if signal_tx.try_send(signal.clone()).is_err() {
                metrics
                    .backpressure_drops_signal
                    .fetch_add(1, Ordering::Relaxed);
                warn!(
                    reason_code = "BP_DROP_SIGNAL",
                    channel = "signal",
                    "backpressure: dropped signal (channel full)"
                );
            }

            // Send to persist (non-blocking - I6)
            let _ = persist_tx.try_send(PersistEvent::Signal(signal));
        }
    }

    info!(
        total_signals = metrics.signal_count.load(Ordering::Relaxed),
        "strategy task ended (tick channel closed)"
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_sma_crossover_emits_buy_and_sell() {
        let metrics = Arc::new(Metrics::new());
        let (tick_tx, tick_rx) = mpsc::channel(64);
        let (signal_tx, mut signal_rx) = mpsc::channel(64);
        let (persist_tx, _persist_rx) = mpsc::channel(64);

        let metrics_clone = metrics.clone();
        let handle = tokio::spawn(async move {
            run_strategy_task(tick_rx, signal_tx, persist_tx, metrics_clone).await;

## ingest/mod.rs (replay functions)
$ rg -n "run_replay_file|run_replay_db" -n -C 3 engine-rust/src/ingest/mod.rs
45-        }
46-        IngestMode::Replay => {
47-            if let Some(replay_file) = config.replay_file.clone() {
48:                run_replay_file(
49-                    replay_file,
50-                    config.sample_every,
51-                    tick_tx,
--
56-                )
57-                .await;
58-            } else {
59:                run_replay_db(
60-                    symbol,
61-                    config.sample_every,
62-                    pool,
--
161-    pub event_id: Option<EventId>,
162-}
163-
164:async fn run_replay_file(
165-    replay_file: String,
166-    sample_every: u64,
167-    tick_tx: mpsc::Sender<Tick>,
--
247-    }
248-}
249-
250:async fn run_replay_db(
251-    _symbol: String,
252-    sample_every: u64,
253-    pool: SqlitePool,

## ingest/mod.rs (replay file)
$ sed -n '140,240p' engine-rust/src/ingest/mod.rs
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

## ingest/mod.rs (replay db)
$ sed -n '240,340p' engine-rust/src/ingest/mod.rs
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
    info!(mode = "REPLAY", sample_every = sample_every, "ingest task started");

    let mut offset = 0;
    let limit = 1000;
    let mut sequence = 0u64;
    
    loop {
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

## Build release
$ cd engine-rust && cargo build --release

## Proof run (SMA replay)
$ REPLAY_DB="/tmp/bot_replay_sma.db"
$ rm -f "/tmp/bot_replay_sma.db" "/tmp/bot_replay_sma.db-wal" "/tmp/bot_replay_sma.db-shm"

$ RUST_LOG=debug ./engine-rust/target/release/engine-rust --ingest replay --replay-file engine-rust/tests/fixtures/crossover_scenario.jsonl --db "/tmp/bot_replay_sma.db"
{"timestamp":"2026-01-09T17:42:06.207404Z","level":"INFO","fields":{"message":"engine-rust starting (Phase 2 skeleton)","version":"0.1.0"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.209878Z","level":"INFO","fields":{"message":"configuration loaded (G0: shadow mode default enforced)","mode":"SHADOW","symbol":"SOL/USDC","db_path":"/tmp/bot_replay_sma.db","ingest_mode":"REPLAY","replay_file":"Some(\"engine-rust/tests/fixtures/crossover_scenario.jsonl\")","sample_every":1,"tick_interval_ms":500,"heartbeat_secs":10,"run_seconds":"None"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.233876Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode = WAL; …","db.statement":"\n\nPRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY; \n","rows_affected":0,"rows_returned":1,"elapsed":"22.980107ms","elapsed_secs":0.022980107},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.234025Z","level":"INFO","fields":{"message":"database pool created with WAL mode","db_path":"/tmp/bot_replay_sma.db"},"target":"engine_rust::db"}
{"timestamp":"2026-01-09T17:42:06.234231Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode;","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"24.436µs","elapsed_secs":0.000024436},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.238077Z","level":"DEBUG","fields":{"summary":"PRAGMA synchronous;","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"19.928µs","elapsed_secs":0.000019928},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.239284Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode = WAL; …","db.statement":"\n\nPRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY; \n","rows_affected":0,"rows_returned":1,"elapsed":"402.735µs","elapsed_secs":0.000402735},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.239478Z","level":"DEBUG","fields":{"summary":"PRAGMA busy_timeout;","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"17.534µs","elapsed_secs":0.000017534},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.239935Z","level":"DEBUG","fields":{"summary":"PRAGMA temp_store;","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"23.086µs","elapsed_secs":0.000023086},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.240000Z","level":"INFO","fields":{"message":"PRAGMA verification","journal_mode":"wal","synchronous":1,"busy_timeout":5000,"temp_store":2},"target":"engine_rust::db"}
{"timestamp":"2026-01-09T17:42:06.240016Z","level":"INFO","fields":{"message":"all PRAGMAs verified successfully (S1 PASS)"},"target":"engine_rust::db"}
{"timestamp":"2026-01-09T17:42:06.241035Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode = WAL; …","db.statement":"\n\nPRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY; \n","rows_affected":0,"rows_returned":1,"elapsed":"302.985µs","elapsed_secs":0.000302985},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.258327Z","level":"DEBUG","fields":{"summary":"CREATE TABLE IF NOT …","db.statement":"\n\n\n        CREATE TABLE IF NOT EXISTS ticks (\n            id INTEGER PRIMARY KEY,\n            symbol TEXT NOT NULL,\n            price REAL NOT NULL,\n            volume REAL NOT NULL,\n            ts INTEGER NOT NULL\n        );\n        \n","rows_affected":0,"rows_returned":0,"elapsed":"16.881926ms","elapsed_secs":0.016881926},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.259069Z","level":"DEBUG","fields":{"summary":"CREATE INDEX IF NOT …","db.statement":"\n\nCREATE INDEX IF NOT EXISTS idx_ticks_ts ON ticks(ts);\n","rows_affected":0,"rows_returned":0,"elapsed":"368.326µs","elapsed_secs":0.000368326},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.259541Z","level":"DEBUG","fields":{"summary":"CREATE TABLE IF NOT …","db.statement":"\n\n\n        CREATE TABLE IF NOT EXISTS signals (\n            id INTEGER PRIMARY KEY,\n            symbol TEXT NOT NULL,\n            kind TEXT NOT NULL,\n            value REAL NOT NULL,\n            ts INTEGER NOT NULL\n        );\n        \n","rows_affected":0,"rows_returned":0,"elapsed":"359.809µs","elapsed_secs":0.000359809},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.260300Z","level":"DEBUG","fields":{"summary":"CREATE INDEX IF NOT …","db.statement":"\n\nCREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(ts);\n","rows_affected":0,"rows_returned":0,"elapsed":"311.566µs","elapsed_secs":0.000311566},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.261805Z","level":"DEBUG","fields":{"summary":"CREATE TABLE IF NOT …","db.statement":"\n\n\n        CREATE TABLE IF NOT EXISTS orders (\n            id INTEGER PRIMARY KEY,\n            symbol TEXT NOT NULL,\n            side TEXT NOT NULL,\n            qty REAL NOT NULL,\n            price REAL,\n            status TEXT NOT NULL,\n            ts INTEGER NOT NULL\n        );\n        \n","rows_affected":0,"rows_returned":0,"elapsed":"624.322µs","elapsed_secs":0.000624322},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.262283Z","level":"DEBUG","fields":{"summary":"CREATE INDEX IF NOT …","db.statement":"\n\nCREATE INDEX IF NOT EXISTS idx_orders_ts ON orders(ts);\n","rows_affected":0,"rows_returned":0,"elapsed":"304.82µs","elapsed_secs":0.00030482},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.263414Z","level":"DEBUG","fields":{"summary":"CREATE TABLE IF NOT …","db.statement":"\n\n\n        CREATE TABLE IF NOT EXISTS trades (\n            id INTEGER PRIMARY KEY,\n            event_id TEXT NOT NULL UNIQUE,\n            order_id TEXT NOT NULL,\n            symbol TEXT NOT NULL,\n            side TEXT NOT NULL,\n            fill_qty REAL NOT NULL,\n            fill_price REAL NOT NULL,\n            fees REAL NOT NULL,\n            ts INTEGER NOT NULL,\n            is_shadow INTEGER NOT NULL DEFAULT 1\n        );\n        \n","rows_affected":0,"rows_returned":0,"elapsed":"418.769µs","elapsed_secs":0.000418769},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.264196Z","level":"DEBUG","fields":{"summary":"CREATE INDEX IF NOT …","db.statement":"\n\nCREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(ts);\n","rows_affected":0,"rows_returned":0,"elapsed":"566.604µs","elapsed_secs":0.000566604},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.264790Z","level":"DEBUG","fields":{"summary":"CREATE INDEX IF NOT …","db.statement":"\n\nCREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id);\n","rows_affected":0,"rows_returned":0,"elapsed":"343.883µs","elapsed_secs":0.000343883},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.265030Z","level":"INFO","fields":{"message":"schema ensured (ticks, signals, orders, trades tables ready)"},"target":"engine_rust::db"}
{"timestamp":"2026-01-09T17:42:06.265327Z","level":"DEBUG","fields":{"summary":"SELECT COUNT(*) FROM ticks","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"248.042µs","elapsed_secs":0.000248042},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.266016Z","level":"DEBUG","fields":{"summary":"SELECT COUNT(*) FROM signals","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"206.06µs","elapsed_secs":0.00020606},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.266206Z","level":"DEBUG","fields":{"summary":"SELECT COUNT(*) FROM orders","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"34.041µs","elapsed_secs":0.000034041},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.266480Z","level":"DEBUG","fields":{"summary":"SELECT COUNT(*) FROM trades","db.statement":"","rows_affected":0,"rows_returned":1,"elapsed":"36.332µs","elapsed_secs":0.000036332},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.266744Z","level":"INFO","fields":{"message":"initial database state","ticks":0,"signals":0,"orders":0,"trades":0},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.266769Z","level":"INFO","fields":{"message":"channels created (S6: bounded, backpressure policy: DROP_OLDEST with metrics)","tick_channel":256,"signal_channel":64,"persist_channel":512},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.266880Z","level":"INFO","fields":{"message":"ingest task started","mode":"REPLAY","replay_file":"engine-rust/tests/fixtures/crossover_scenario.jsonl","sample_every":1},"target":"engine_rust::ingest"}
{"timestamp":"2026-01-09T17:42:06.267786Z","level":"INFO","fields":{"message":"replay finished (file)","ticks_read":50},"target":"engine_rust::ingest"}
{"timestamp":"2026-01-09T17:42:06.267820Z","level":"INFO","fields":{"message":"all tasks spawned, pipeline running"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.267832Z","level":"INFO","fields":{"message":"waiting for replay completion or shutdown signal"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.267838Z","level":"WARN","fields":{"message":"replay completed, initiating shutdown"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.267960Z","level":"INFO","fields":{"message":"strategy task started (sma crossover)","short_window":5,"long_window":20},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.267975Z","level":"INFO","fields":{"message":"persist task started (dedicated, non-blocking - I6)","batch_size":100,"flush_interval_ms":1000},"target":"engine_rust::persist"}
{"timestamp":"2026-01-09T17:42:06.267976Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.267986Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.267996Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268002Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268004Z","level":"INFO","fields":{"message":"execution task started (shadow adapter, NO NETWORK)","mode":"SHADOW","max_exposure":10000.0,"max_symbol_exposure":5000.0,"max_open_orders":10},"target":"engine_rust::execution"}
{"timestamp":"2026-01-09T17:42:06.268008Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268015Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268026Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268037Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268047Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268060Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268068Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268076Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268085Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268094Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268106Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268113Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268123Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268135Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268145Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268158Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268171Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.2,"long":100.05,"prev_diff":0.0,"curr_diff":0.15000000000000568,"emit":true,"action":"BUY"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268182Z","level":"INFO","fields":{"message":"signal generated","event_id":"32116555-cace-4d10-8e67-499e68fd54c2","symbol":"TEST/USD","side":"BUY","reason_code":"SMA_CROSSOVER","confidence":0.75,"desired_size":0.1,"event":"SMA_CROSSOVER"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268198Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.6,"long":100.15,"prev_diff":0.15000000000000568,"curr_diff":0.44999999999998863,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268208Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":101.2,"long":100.3,"prev_diff":0.44999999999998863,"curr_diff":0.9000000000000057,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268220Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":102.0,"long":100.5,"prev_diff":0.9000000000000057,"curr_diff":1.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268229Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":103.0,"long":100.75,"prev_diff":1.5,"curr_diff":2.25,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268238Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":104.0,"long":101.05,"prev_diff":2.25,"curr_diff":2.950000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268250Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":105.0,"long":101.4,"prev_diff":2.950000000000003,"curr_diff":3.5999999999999943,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268258Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":106.0,"long":101.8,"prev_diff":3.5999999999999943,"curr_diff":4.200000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268263Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":107.0,"long":102.25,"prev_diff":4.200000000000003,"curr_diff":4.75,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268271Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.0,"long":102.75,"prev_diff":4.75,"curr_diff":5.25,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268282Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.6,"long":103.2,"prev_diff":5.25,"curr_diff":5.3999999999999915,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268291Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.8,"long":103.6,"prev_diff":5.3999999999999915,"curr_diff":5.200000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268302Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.6,"long":103.95,"prev_diff":5.200000000000003,"curr_diff":4.6499999999999915,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268309Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.0,"long":104.25,"prev_diff":4.6499999999999915,"curr_diff":3.75,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268320Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":107.0,"long":104.5,"prev_diff":3.75,"curr_diff":2.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268330Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":106.0,"long":104.7,"prev_diff":2.5,"curr_diff":1.2999999999999972,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268342Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":105.0,"long":104.85,"prev_diff":1.2999999999999972,"curr_diff":0.15000000000000568,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268350Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":104.0,"long":104.95,"prev_diff":0.15000000000000568,"curr_diff":-0.9500000000000028,"emit":true,"action":"SELL"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268360Z","level":"INFO","fields":{"message":"signal generated","event_id":"d326b7e8-dcaa-439e-ae75-13f3b118be36","symbol":"TEST/USD","side":"SELL","reason_code":"SMA_CROSSOVER","confidence":0.75,"desired_size":0.1,"event":"SMA_CROSSOVER"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268369Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":103.0,"long":105.0,"prev_diff":-0.9500000000000028,"curr_diff":-2.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268377Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":102.0,"long":105.0,"prev_diff":-2.0,"curr_diff":-3.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268387Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":101.0,"long":104.9,"prev_diff":-3.0,"curr_diff":-3.9000000000000057,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268398Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":104.7,"prev_diff":-3.9000000000000057,"curr_diff":-4.700000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268408Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":99.0,"long":104.4,"prev_diff":-4.700000000000003,"curr_diff":-5.400000000000006,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268418Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":98.0,"long":104.0,"prev_diff":-5.400000000000006,"curr_diff":-6.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268431Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":97.0,"long":103.5,"prev_diff":-6.0,"curr_diff":-6.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268437Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":96.0,"long":102.9,"prev_diff":-6.5,"curr_diff":-6.900000000000006,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268443Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":95.0,"long":102.2,"prev_diff":-6.900000000000006,"curr_diff":-7.200000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268449Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":94.0,"long":101.4,"prev_diff":-7.200000000000003,"curr_diff":-7.400000000000006,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268454Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":93.0,"long":100.5,"prev_diff":-7.400000000000006,"curr_diff":-7.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268460Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":92.0,"long":99.5,"prev_diff":-7.5,"curr_diff":-7.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268466Z","level":"INFO","fields":{"message":"strategy task ended (tick channel closed)","total_signals":2},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268485Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"a09eafa9-3123-4d5d-9be8-b7ca22a946c0","signal_id":"32116555-cace-4d10-8e67-499e68fd54c2","symbol":"TEST/USD","side":"BUY","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
{"timestamp":"2026-01-09T17:42:06.268505Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"467f5829-165f-431c-9b83-876cd59ef320","signal_id":"d326b7e8-dcaa-439e-ae75-13f3b118be36","symbol":"TEST/USD","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
{"timestamp":"2026-01-09T17:42:06.268520Z","level":"INFO","fields":{"message":"execution task ended (signal channel closed)","total_shadow_orders":2,"total_trades":2,"risk_vetoes":0},"target":"engine_rust::execution"}
{"timestamp":"2026-01-09T17:42:06.268580Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"142.645µs","elapsed_secs":0.000142645},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.270492Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"112.949µs","elapsed_secs":0.000112949},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.270527Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
{"timestamp":"2026-01-09T17:42:06.270554Z","level":"INFO","fields":{"message":"final flush on shutdown","remaining":54},"target":"engine_rust::persist"}
{"timestamp":"2026-01-09T17:42:06.271054Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"129.68µs","elapsed_secs":0.00012968},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.271269Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"66.642µs","elapsed_secs":0.000066642},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.271607Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"64.575µs","elapsed_secs":0.000064575},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.271791Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"64.837µs","elapsed_secs":0.000064837},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.271984Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"78.155µs","elapsed_secs":0.000078155},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.272989Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode = WAL; …","db.statement":"\n\nPRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY; \n","rows_affected":0,"rows_returned":1,"elapsed":"272.742µs","elapsed_secs":0.000272742},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.273524Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"115.554µs","elapsed_secs":0.000115554},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.273665Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"54.061µs","elapsed_secs":0.000054061},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.273876Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"62.097µs","elapsed_secs":0.000062097},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.274328Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"71.306µs","elapsed_secs":0.000071306},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.274509Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"56.659µs","elapsed_secs":0.000056659},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.274797Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"62.965µs","elapsed_secs":0.000062965},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.275151Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"65.91µs","elapsed_secs":0.00006591},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.275627Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"61.042µs","elapsed_secs":0.000061042},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.275967Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"78.007µs","elapsed_secs":0.000078007},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.276437Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"68.557µs","elapsed_secs":0.000068557},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.276535Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"50.809µs","elapsed_secs":0.000050809},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.276702Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"55.285µs","elapsed_secs":0.000055285},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.284259Z","level":"DEBUG","fields":{"summary":"PRAGMA journal_mode = WAL; …","db.statement":"\n\nPRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON; PRAGMA synchronous = NORMAL; PRAGMA temp_store = MEMORY; \n","rows_affected":0,"rows_returned":1,"elapsed":"263.662µs","elapsed_secs":0.000263662},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.286540Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"461.96µs","elapsed_secs":0.00046196},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.287236Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"82.016µs","elapsed_secs":0.000082016},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.287681Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"70.749µs","elapsed_secs":0.000070749},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.288343Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"78.191µs","elapsed_secs":0.000078191},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.289380Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"145.201µs","elapsed_secs":0.000145201},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.294292Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"96.277µs","elapsed_secs":0.000096277},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.295151Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"71.566µs","elapsed_secs":0.000071566},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.295414Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"181.033µs","elapsed_secs":0.000181033},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.295753Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"64.649µs","elapsed_secs":0.000064649},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.295886Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"57.018µs","elapsed_secs":0.000057018},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.296063Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"75.941µs","elapsed_secs":0.000075941},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.296280Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"64.397µs","elapsed_secs":0.000064397},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.297092Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"594.045µs","elapsed_secs":0.000594045},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.297249Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"71.982µs","elapsed_secs":0.000071982},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.297454Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"57.9µs","elapsed_secs":0.0000579},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.302977Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"3.741133ms","elapsed_secs":0.003741133},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.303224Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"93.521µs","elapsed_secs":0.000093521},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.303605Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"62.866µs","elapsed_secs":0.000062866},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.303792Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"92.132µs","elapsed_secs":0.000092132},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.304110Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"69.901µs","elapsed_secs":0.000069901},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.304395Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"177.145µs","elapsed_secs":0.000177145},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.304743Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"68.668µs","elapsed_secs":0.000068668},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.309111Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"104.453µs","elapsed_secs":0.000104453},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.309311Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"77.586µs","elapsed_secs":0.000077586},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.309632Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"69.875µs","elapsed_secs":0.000069875},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.310046Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"71.582µs","elapsed_secs":0.000071582},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.310214Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"69.602µs","elapsed_secs":0.000069602},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.312111Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"93.314µs","elapsed_secs":0.000093314},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.312549Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"73.693µs","elapsed_secs":0.000073693},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.312667Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"58.567µs","elapsed_secs":0.000058567},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.312886Z","level":"DEBUG","fields":{"summary":"INSERT INTO ticks(symbol, price, …","db.statement":"\n\nINSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"61.593µs","elapsed_secs":0.000061593},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.313319Z","level":"DEBUG","fields":{"summary":"INSERT INTO signals(symbol, kind, …","db.statement":"\n\nINSERT INTO signals(symbol, kind, value, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"103.768µs","elapsed_secs":0.000103768},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.313632Z","level":"DEBUG","fields":{"summary":"INSERT INTO signals(symbol, kind, …","db.statement":"\n\nINSERT INTO signals(symbol, kind, value, ts) VALUES(?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"106.864µs","elapsed_secs":0.000106864},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.313808Z","level":"DEBUG","fields":{"summary":"INSERT INTO orders(symbol, side, …","db.statement":"\n\nINSERT INTO orders(symbol, side, qty, price, status, ts) VALUES(?, ?, ?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"104.318µs","elapsed_secs":0.000104318},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.314100Z","level":"DEBUG","fields":{"summary":"INSERT INTO trades(event_id, order_id, …","db.statement":"\n\nINSERT INTO trades(event_id, order_id, symbol, side, fill_qty, fill_price, fees, ts, is_shadow) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"147.812µs","elapsed_secs":0.000147812},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.317134Z","level":"DEBUG","fields":{"summary":"INSERT INTO orders(symbol, side, …","db.statement":"\n\nINSERT INTO orders(symbol, side, qty, price, status, ts) VALUES(?, ?, ?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"135.005µs","elapsed_secs":0.000135005},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.317419Z","level":"DEBUG","fields":{"summary":"INSERT INTO trades(event_id, order_id, …","db.statement":"\n\nINSERT INTO trades(event_id, order_id, symbol, side, fill_qty, fill_price, fees, ts, is_shadow) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)\n","rows_affected":1,"rows_returned":0,"elapsed":"155.175µs","elapsed_secs":0.000155175},"target":"sqlx::query"}
{"timestamp":"2026-01-09T17:42:06.317454Z","level":"INFO","fields":{"message":"batch flushed","persisted":54,"errors":0},"target":"engine_rust::persist"}
{"timestamp":"2026-01-09T17:42:06.317465Z","level":"INFO","fields":{"message":"persist task ended (channel closed, final flush complete)","total_persisted":56,"total_errors":0},"target":"engine_rust::persist"}
{"timestamp":"2026-01-09T17:42:06.317538Z","level":"INFO","fields":{"message":"all tasks completed gracefully"},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.317551Z","level":"INFO","fields":{"message":"FINAL METRICS","tick_count":50,"signal_count":2,"shadow_orders":2,"trade_count":2,"persist_count":56,"persist_errors":0,"ingest_received":50,"ingest_processed":50,"bp_drops_tick":0,"bp_drops_signal":0,"risk_vetoes":0},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.317565Z","level":"INFO","fields":{"message":"replay summary","ingest":"replay","replay_file":"engine-rust/tests/fixtures/crossover_scenario.jsonl","db":"/tmp/bot_replay_sma.db","ticks_read":50,"signals_emitted":2},"target":"engine_rust"}
{"timestamp":"2026-01-09T17:42:06.317577Z","level":"INFO","fields":{"message":"engine-rust shutdown complete"},"target":"engine_rust"}

## Replay evidence excerpts
$ rg "SMA_CALC" /tmp/phase2_3_sma_replay.log | head -40
{"timestamp":"2026-01-09T17:42:06.267976Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.267986Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.267996Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268002Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268008Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268015Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268026Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268037Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268047Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268060Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268068Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268076Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268085Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268094Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268106Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268113Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268123Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268135Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268145Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"WARMUP"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268158Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.0,"long":100.0,"prev_diff":0.0,"curr_diff":0.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268171Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.2,"long":100.05,"prev_diff":0.0,"curr_diff":0.15000000000000568,"emit":true,"action":"BUY"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268198Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":100.6,"long":100.15,"prev_diff":0.15000000000000568,"curr_diff":0.44999999999998863,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268208Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":101.2,"long":100.3,"prev_diff":0.44999999999998863,"curr_diff":0.9000000000000057,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268220Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":102.0,"long":100.5,"prev_diff":0.9000000000000057,"curr_diff":1.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268229Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":103.0,"long":100.75,"prev_diff":1.5,"curr_diff":2.25,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268238Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":104.0,"long":101.05,"prev_diff":2.25,"curr_diff":2.950000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268250Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":105.0,"long":101.4,"prev_diff":2.950000000000003,"curr_diff":3.5999999999999943,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268258Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":106.0,"long":101.8,"prev_diff":3.5999999999999943,"curr_diff":4.200000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268263Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":107.0,"long":102.25,"prev_diff":4.200000000000003,"curr_diff":4.75,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268271Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.0,"long":102.75,"prev_diff":4.75,"curr_diff":5.25,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268282Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.6,"long":103.2,"prev_diff":5.25,"curr_diff":5.3999999999999915,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268291Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.8,"long":103.6,"prev_diff":5.3999999999999915,"curr_diff":5.200000000000003,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268302Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.6,"long":103.95,"prev_diff":5.200000000000003,"curr_diff":4.6499999999999915,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268309Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":108.0,"long":104.25,"prev_diff":4.6499999999999915,"curr_diff":3.75,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268320Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":107.0,"long":104.5,"prev_diff":3.75,"curr_diff":2.5,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268330Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":106.0,"long":104.7,"prev_diff":2.5,"curr_diff":1.2999999999999972,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268342Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":105.0,"long":104.85,"prev_diff":1.2999999999999972,"curr_diff":0.15000000000000568,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268350Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":104.0,"long":104.95,"prev_diff":0.15000000000000568,"curr_diff":-0.9500000000000028,"emit":true,"action":"SELL"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268369Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":103.0,"long":105.0,"prev_diff":-0.9500000000000028,"curr_diff":-2.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268377Z","level":"DEBUG","fields":{"message":"sma calc","event":"SMA_CALC","short":102.0,"long":105.0,"prev_diff":-2.0,"curr_diff":-3.0,"emit":false,"action":"NONE"},"target":"engine_rust::strategy"}

$ rg "SMA_CROSSOVER|SIGNAL" /tmp/phase2_3_sma_replay.log
{"timestamp":"2026-01-09T17:42:06.268182Z","level":"INFO","fields":{"message":"signal generated","event_id":"32116555-cace-4d10-8e67-499e68fd54c2","symbol":"TEST/USD","side":"BUY","reason_code":"SMA_CROSSOVER","confidence":0.75,"desired_size":0.1,"event":"SMA_CROSSOVER"},"target":"engine_rust::strategy"}
{"timestamp":"2026-01-09T17:42:06.268360Z","level":"INFO","fields":{"message":"signal generated","event_id":"d326b7e8-dcaa-439e-ae75-13f3b118be36","symbol":"TEST/USD","side":"SELL","reason_code":"SMA_CROSSOVER","confidence":0.75,"desired_size":0.1,"event":"SMA_CROSSOVER"},"target":"engine_rust::strategy"}

$ wc -l engine-rust/tests/fixtures/crossover_scenario.jsonl
50 engine-rust/tests/fixtures/crossover_scenario.jsonl

$ sqlite3 "/tmp/bot_replay_sma.db" "SELECT side, reason_code, ts FROM signals ORDER BY ts;"

## Signals table shape + contents
$ sqlite3 "/tmp/bot_replay_sma.db" "PRAGMA table_info(signals);"
0|id|INTEGER|0||1
1|symbol|TEXT|1||0
2|kind|TEXT|1||0
3|value|REAL|1||0
4|ts|INTEGER|1||0

$ sqlite3 "/tmp/bot_replay_sma.db" "SELECT symbol, kind, value, ts FROM signals ORDER BY ts;"
TEST/USD|BUY:SMA_CROSSOVER|0.75|1700000020
TEST/USD|SELL:SMA_CROSSOVER|0.75|1700000037

## cargo test
$ cd engine-rust && cargo test

running 17 tests
test config::tests::test_default_mode_is_shadow ... ok
test config::tests::test_shadow_mode_validates ... ok
test config::tests::test_live_mode_fails_without_armed ... ok
test config::tests::test_default_risk_caps ... ok
test execution::tests::test_exposure_tracker_per_symbol_cap ... ok
test execution::tests::test_exposure_tracker_respects_caps ... ok
test execution::tests::test_shadow_execution_has_no_network_fields ... ok
test db::tests::test_pragma_values_correct ... ok
test db::tests::test_pragma_verification_passes ... ok
test db::tests::test_schema_creation ... ok
test strategy::tests::test_sma_crossover_emits_buy_and_sell ... ok
test types::tests::test_event_id_unique ... ok
test types::tests::test_reason_code_display ... ok
test types::tests::test_side_display ... ok
test persist::tests::test_persist_signal ... ok
test persist::tests::test_persist_tick ... ok
test persist::tests::test_batch_flush ... ok

test result: ok. 17 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.63s


running 18 tests
test config::tests::test_default_mode_is_shadow ... ok
test config::tests::test_default_risk_caps ... ok
test config::tests::test_live_mode_fails_without_armed ... ok
test config::tests::test_shadow_mode_validates ... ok
test execution::tests::test_exposure_tracker_per_symbol_cap ... ok
test execution::tests::test_exposure_tracker_respects_caps ... ok
test execution::tests::test_shadow_execution_has_no_network_fields ... ok
test db::tests::test_pragma_verification_passes ... ok
test db::tests::test_pragma_values_correct ... ok
test db::tests::test_schema_creation ... ok
test strategy::tests::test_sma_crossover_emits_buy_and_sell ... ok
test tests::invalid_toml_is_classified_as_config_error ... ok
test types::tests::test_event_id_unique ... ok
test types::tests::test_reason_code_display ... ok
test types::tests::test_side_display ... ok
test persist::tests::test_persist_signal ... ok
test persist::tests::test_persist_tick ... ok
test persist::tests::test_batch_flush ... ok

test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.61s


running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


running 5 tests
test test_pragma_verification_passes ... ok
test test_pragma_values_are_correct ... ok
test test_pragma_verification_fails_on_mismatch ... ok
test test_schema_creation ... ok
test test_wal_allows_concurrent_access ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.14s


running 7 tests
test order_trade_correctly_linked ... ok
test per_symbol_exposure_respects_caps ... ok
test unit_tests::test_exposure_tracker_release ... ok
test unit_tests::test_shadow_execution_struct_has_no_network_fields ... ok
test shadow_orders_always_marked ... ok
test shadow_execution_makes_zero_network_calls ... ok
test risk_caps_never_exceeded ... ok

test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 2.46s


running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


## Git status
$ git status -sb
## main...origin/main [ahead 15]
 M engine-rust/src/config.rs
 M engine-rust/src/ingest/mod.rs
 M engine-rust/src/main.rs
 M engine-rust/src/strategy.rs
 M engine-rust/src/types.rs
?? docs/buglog/BUG_2026-01-09_phase2_2_4_contract_lock_phase2_3_sma.md
?? docs/buglog/BUG_2026-01-09_phase2_3_strategy_sma.md
?? engine-rust/tests/fixtures/

## Commit Phase 2.2.4 buglog
$ git add docs/buglog/BUG_2026-01-09_phase2_2_4_contract_lock_phase2_3_sma.md

$ git commit -m "docs(buglog): phase 2.2.4 contract lock"
[main e7ed77a] docs(buglog): phase 2.2.4 contract lock
 1 file changed, 481 insertions(+)
 create mode 100644 docs/buglog/BUG_2026-01-09_phase2_2_4_contract_lock_phase2_3_sma.md

## Final checks pre-freeze
$ git status -sb
## main...origin/main [ahead 16]
 M engine-rust/src/config.rs
 M engine-rust/src/ingest/mod.rs
 M engine-rust/src/main.rs
 M engine-rust/src/strategy.rs
 M engine-rust/src/types.rs
?? docs/buglog/BUG_2026-01-09_phase2_3_strategy_sma.md
?? engine-rust/tests/fixtures/

$ git log -5 --oneline
e7ed77a docs(buglog): phase 2.2.4 contract lock
554ddce docs(spec): lock exit-code protocol + sampling invariant
a573bcf docs(buglog): Phase 2.2.3 proof closure evidence
1151fff soak(proofs): add psi-actions flag + rerun proofs 2/3/5 with evidence
97a3413 engine(exitcodes): map TOML parse errors to CONFIG=12 + tests

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecStart
Restart=on-failure
RestartPreventExitStatus=12
ExecStart={ path=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; argv[]=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; ignore_errors=no ; start_time=[Fri 2026-01-09 16:54:44 UTC] ; stop_time=[n/a] ; pid=1881587 ; code=(null) ; status=0/0 }

## Post-freeze commands (output suppressed)
$ git add engine-rust/src/config.rs engine-rust/src/ingest/mod.rs engine-rust/src/main.rs engine-rust/src/strategy.rs engine-rust/src/types.rs engine-rust/tests/fixtures/crossover_scenario.jsonl docs/buglog/BUG_2026-01-09_phase2_3_strategy_sma.md
$ git commit -m "feat(strategy): SMA crossover + replay ingest proof"
$ git push origin main

---
## BUGLOG FREEZE (Pre-push)
Freeze Timestamp: 2026-01-09T17:47:27+00:00
Git HEAD: e7ed77a4e48cfcc5201ee81a1c76a9ddcb04712c
Buglog SHA256: b9b6eb36896831be4ead3259f39649b2b8e26ab26315cbd91a61f377f75ebabb
---
