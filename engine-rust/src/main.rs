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
use tokio::sync::{broadcast, mpsc, oneshot};
use tokio::time::{interval, Duration};
use tracing::{error, info, warn};

use config::{Config, ExecutionMode, IngestMode};
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

    /// Replay file (JSONL) for ingest=replay
    #[arg(long)]
    replay_file: Option<String>,

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

    // Override replay file for ingest=replay
    if let Some(replay_file) = args.replay_file {
        config.engine.replay_file = Some(replay_file);
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
        ingest_mode = %config.engine.ingest_mode,
        replay_file = ?config.engine.replay_file,
        sample_every = config.engine.sample_every,
        tick_interval_ms = config.engine.tick_interval_ms,
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

    let mode = config.mode;
    let risk_caps = config.risk_caps.clone();
    let heartbeat_interval = config.engine.heartbeat_interval_secs;
    let run_seconds = config.engine.run_seconds;
    let replay_mode = config.engine.ingest_mode == IngestMode::Replay;

    // Spawn ingest task
    let shutdown_rx_ingest = shutdown_tx.subscribe();
    let engine_config = config.engine.clone();
    let db_pool = pool.clone(); // Needed for replay

    let (replay_done_tx, mut replay_done_rx) = if replay_mode {
        let (tx, rx) = oneshot::channel();
        (Some(tx), Some(rx))
    } else {
        (None, None)
    };

    let ingest_handle = tokio::spawn(async move {
        ingest::run_ingest_task(
            config.app.symbol,
            engine_config,
            db_pool,
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
        strategy::run_strategy_task(tick_rx, signal_tx, persist_tx_strategy, metrics_strategy)
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
    } else if replay_done_rx.is_some() {
        info!("waiting for replay completion or shutdown signal");
        tokio::select! {
            _ = tokio::signal::ctrl_c() => {
                warn!("shutdown signal received (S13: graceful shutdown)");
            }
            _ = &mut replay_done_rx.as_mut().expect("replay rx") => {
                warn!("replay completed, initiating shutdown");
            }
        }
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

    if config.engine.ingest_mode == IngestMode::Replay {
        let replay_file = config
            .engine
            .replay_file
            .clone()
            .unwrap_or_else(|| "NONE".to_string());
        info!(
            ingest = "replay",
            replay_file = %replay_file,
            db = %config.app.db_path,
            ticks_read = metrics.ingest_received.load(Ordering::Relaxed),
            signals_emitted = metrics.signal_count.load(Ordering::Relaxed),
            "replay summary"
        );
    }

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
