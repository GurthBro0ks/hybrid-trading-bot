# BUG 2026-01-09 Phase 2.2.3 Proof Closure

Notes:
- Flight recorder: all shell commands + outputs are appended below.
- File created via apply_patch (no shell command output to record).

## Command Log

$ systemctl cat hybrid-engine.service
# /etc/systemd/system/hybrid-engine.service
[Unit]
Description=Hybrid Trading Bot Engine
After=network.target

[Service]
Type=simple
User=slimy
WorkingDirectory=/opt/hybrid-trading-bot
Environment=RUST_LOG=info
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/debug/engine-rust
Restart=always
RestartSec=2
Nice=10

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/hybrid-engine.service.d/override.conf
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecStart
Restart=on-failure
RestartPreventExitStatus=
ExecStart={ path=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; argv[]=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; ignore_errors=no ; start_time=[Fri 2026-01-09 15:51:33 UTC] ; stop_time=[n/a] ; pid=1733966 ; code=(null) ; status=0/0 }

$ systemctl show hybrid-engine.service -p FragmentPath,DropInPaths
FragmentPath=/etc/systemd/system/hybrid-engine.service
DropInPaths=/etc/systemd/system/hybrid-engine.service.d/override.conf

$ python3 scripts/soak_2h.py --help
usage: soak_2h.py [-h] [--seconds SECONDS] [--mode MODE] [--db DB]

options:
  -h, --help         show this help message and exit
  --seconds SECONDS  Soak duration seconds
  --mode MODE        Initial ingest mode
  --db DB

$ rg -n decisions scripts/soak_2h.py
18:DECISION_LOG_PATH = "/opt/hybrid-trading-bot/data/ops/soak_decisions.jsonl"

$ sed -n 1,160p /etc/systemd/system/hybrid-engine.service.d/override.conf
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure

$ sudo tee /etc/systemd/system/hybrid-engine.service.d/override.conf >/dev/null <<"EOF"
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure
RestartPreventExitStatus=12
# Optional: treat 12 as clean for status dashboards
# SuccessExitStatus=12
EOF

$ tail -n 80 docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

NOTE: sudo command output (captured manually, not tee'd):
sudo: 1 incorrect password attempt
# BUG 2026-01-09 Phase 2.2.3 Proof Closure

Notes:
- Flight recorder: all shell commands + outputs are appended below.
- File created via apply_patch (no shell command output to record).

## Command Log

$ systemctl cat hybrid-engine.service
# /etc/systemd/system/hybrid-engine.service
[Unit]
Description=Hybrid Trading Bot Engine
After=network.target

[Service]
Type=simple
User=slimy
WorkingDirectory=/opt/hybrid-trading-bot
Environment=RUST_LOG=info
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/debug/engine-rust
Restart=always
RestartSec=2
Nice=10

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/hybrid-engine.service.d/override.conf
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecStart
Restart=on-failure
RestartPreventExitStatus=
ExecStart={ path=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; argv[]=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; ignore_errors=no ; start_time=[Fri 2026-01-09 15:51:33 UTC] ; stop_time=[n/a] ; pid=1733966 ; code=(null) ; status=0/0 }

$ systemctl show hybrid-engine.service -p FragmentPath,DropInPaths
FragmentPath=/etc/systemd/system/hybrid-engine.service
DropInPaths=/etc/systemd/system/hybrid-engine.service.d/override.conf

$ python3 scripts/soak_2h.py --help
usage: soak_2h.py [-h] [--seconds SECONDS] [--mode MODE] [--db DB]

options:
  -h, --help         show this help message and exit
  --seconds SECONDS  Soak duration seconds
  --mode MODE        Initial ingest mode
  --db DB

$ rg -n decisions scripts/soak_2h.py
18:DECISION_LOG_PATH = "/opt/hybrid-trading-bot/data/ops/soak_decisions.jsonl"

$ sed -n 1,160p /etc/systemd/system/hybrid-engine.service.d/override.conf
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure

$ sudo tee /etc/systemd/system/hybrid-engine.service.d/override.conf >/dev/null <<"EOF"
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure
RestartPreventExitStatus=12
# Optional: treat 12 as clean for status dashboards
# SuccessExitStatus=12
EOF

$ tail -n 80 docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ rg -n toml|config engine-rust/src
engine-rust/src/lib.rs:5:pub mod config;
engine-rust/src/ingest/ws_sources.rs:20:        let config: WsSourcesConfig = toml::from_str(&content)?;
engine-rust/src/ingest/ws_sources.rs:21:        Ok(config)
engine-rust/src/ingest/realws.rs:1:use crate::config::EngineConfig;
engine-rust/src/ingest/realws.rs:15:    config: EngineConfig,
engine-rust/src/ingest/realws.rs:23:    let config_path = "/opt/hybrid-trading-bot/config/ws_sources.toml";
engine-rust/src/ingest/realws.rs:25:    // If config doesn't exist, we might be in a test env or need to fallback to example for dev convenience?
engine-rust/src/ingest/realws.rs:27:    let sources_config = match WsSourcesConfig::load(config_path) {
engine-rust/src/ingest/realws.rs:31:             error!("Failed to load ws_sources.toml: {}. (Did you cp config/ws_sources.example.toml config/ws_sources.toml?)", e);
engine-rust/src/ingest/realws.rs:36:    let mut sources = sources_config.source.clone();
engine-rust/src/ingest/realws.rs:40:        error!("No sources defined in ws_sources.toml");
engine-rust/src/ingest/realws.rs:48:             // Pass config.sample_every
engine-rust/src/ingest/realws.rs:49:             if run_source_session(source, &symbol, config.sample_every, &tick_tx, &persist_tx, &metrics, &mut shutdown).await {
engine-rust/src/ingest/mod.rs:9:use crate::config::{EngineConfig, IngestMode};
engine-rust/src/ingest/mod.rs:23:    config: EngineConfig,
engine-rust/src/ingest/mod.rs:30:    match config.ingest_mode {
engine-rust/src/ingest/mod.rs:34:                config.tick_interval_ms,
engine-rust/src/ingest/mod.rs:35:                config.sample_every,
engine-rust/src/ingest/mod.rs:44:            run_replay(symbol, config.sample_every, pool, tick_tx, persist_tx, metrics, shutdown).await
engine-rust/src/ingest/mod.rs:47:            let url = config.ws_url.unwrap_or_else(|| "ws://localhost:9001".to_string());
engine-rust/src/ingest/mod.rs:51:                config.sample_every,
engine-rust/src/ingest/mod.rs:62:                config,
engine-rust/src/execution.rs:6:use crate::config::{ExecutionMode, RiskCaps};
engine-rust/src/execution.rs:165:/// * `risk_caps` - Risk caps configuration for I2
engine-rust/src/main.rs:12:mod config;
engine-rust/src/main.rs:28:use config::{Config, ExecutionMode};
engine-rust/src/main.rs:47:    /// Path to config file
engine-rust/src/main.rs:48:    #[arg(long, default_value = "/opt/hybrid-trading-bot/config/config.toml")]
engine-rust/src/main.rs:49:    config: String,
engine-rust/src/main.rs:91:    // Load configuration
engine-rust/src/main.rs:92:    let mut config = if std::path::Path::new(&args.config).exists() {
engine-rust/src/main.rs:93:        Config::load(&args.config)?
engine-rust/src/main.rs:96:            config_path = %args.config,
engine-rust/src/main.rs:97:            "config file not found, using defaults"
engine-rust/src/main.rs:103:    config.mode = match args.mode.to_lowercase().as_str() {
engine-rust/src/main.rs:115:        config.engine.run_seconds = Some(secs);
engine-rust/src/main.rs:120:        config.app.db_path = db_path;
engine-rust/src/main.rs:125:        config.engine.ingest_mode = match ingest.to_lowercase().as_str() {
engine-rust/src/main.rs:126:            "synthetic" => config::IngestMode::Synthetic,
engine-rust/src/main.rs:127:            "replay" => config::IngestMode::Replay,
engine-rust/src/main.rs:128:            "mockws" => config::IngestMode::MockWs,
engine-rust/src/main.rs:129:            "realws" => config::IngestMode::RealWs,
engine-rust/src/main.rs:132:                config::IngestMode::Synthetic
engine-rust/src/main.rs:139:        config.engine.ws_url = Some(url);
engine-rust/src/main.rs:144:        config.engine.sample_every = sample;
engine-rust/src/main.rs:147:    // Validate configuration (G0, G1: fail-closed for LIVE mode)
engine-rust/src/main.rs:148:    config.validate()?;
engine-rust/src/main.rs:151:        mode = %config.mode,
engine-rust/src/main.rs:152:        symbol = %config.app.symbol,
engine-rust/src/main.rs:153:        db_path = %config.app.db_path,
engine-rust/src/main.rs:154:        tick_interval_ms = config.engine.tick_interval_ms,
engine-rust/src/main.rs:155:        signal_every_n = config.engine.signal_every_n_ticks,
engine-rust/src/main.rs:156:        heartbeat_secs = config.engine.heartbeat_interval_secs,
engine-rust/src/main.rs:157:        run_seconds = ?config.engine.run_seconds,
engine-rust/src/main.rs:158:        "configuration loaded (G0: shadow mode default enforced)"
engine-rust/src/main.rs:162:    let pool = db::create_pool(&config.app.db_path).await?;
engine-rust/src/main.rs:180:    let (tick_tx, tick_rx) = mpsc::channel(config.channels.tick_channel_size);
engine-rust/src/main.rs:181:    let (signal_tx, signal_rx) = mpsc::channel(config.channels.signal_channel_size);
engine-rust/src/main.rs:182:    let (persist_tx, persist_rx) = mpsc::channel(config.channels.persist_channel_size);
engine-rust/src/main.rs:185:        tick_channel = config.channels.tick_channel_size,
engine-rust/src/main.rs:186:        signal_channel = config.channels.signal_channel_size,
engine-rust/src/main.rs:187:        persist_channel = config.channels.persist_channel_size,
engine-rust/src/main.rs:203:    let signal_every_n = config.engine.signal_every_n_ticks;
engine-rust/src/main.rs:204:    let mode = config.mode;
engine-rust/src/main.rs:205:    let risk_caps = config.risk_caps.clone();
engine-rust/src/main.rs:206:    let heartbeat_interval = config.engine.heartbeat_interval_secs;
engine-rust/src/main.rs:207:    let run_seconds = config.engine.run_seconds;
engine-rust/src/main.rs:211:    let engine_config = config.engine.clone();
engine-rust/src/main.rs:216:            config.app.symbol,
engine-rust/src/main.rs:217:            engine_config,
engine-rust/src/config.rs:29:/// Risk caps configuration (I2)
engine-rust/src/config.rs:60:/// Channel configuration (S6: bounded channels)
engine-rust/src/config.rs:112:/// Engine configuration
engine-rust/src/config.rs:161:/// App configuration
engine-rust/src/config.rs:177:/// Main configuration struct
engine-rust/src/config.rs:208:    /// Load configuration from TOML file
engine-rust/src/config.rs:211:        let config: Config = toml::from_str(&content)?;
engine-rust/src/config.rs:212:        Ok(config)
engine-rust/src/config.rs:215:    /// Validate configuration (G0, G1: fail-closed for LIVE mode)
engine-rust/src/config.rs:221:                    "LIVE_MODE requires live_armed=true in config (G1 fail-closed). \
engine-rust/src/config.rs:268:        let config = Config::default();
engine-rust/src/config.rs:269:        assert_eq!(config.mode, ExecutionMode::Shadow);
engine-rust/src/config.rs:274:        let config = Config {
engine-rust/src/config.rs:279:        assert!(config.validate().is_err());
engine-rust/src/config.rs:284:        let config = Config::default();
engine-rust/src/config.rs:285:        assert!(config.validate().is_ok());

$ sed -n 1,220p engine-rust/src/main.rs
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
use tracing::{info, warn};

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
        Config::load(&args.config)?
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

$ sed -n 1,260p engine-rust/src/config.rs
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

$ rg -n EXIT_CONFIG|exit engine-rust/src
engine-rust/src/main.rs:35:pub const EXIT_CONFIG: i32 = 12;
engine-rust/src/main.rs:51:    /// Run for N seconds then exit (for testing)
engine-rust/src/ingest/realws.rs:32:             std::process::exit(12);
engine-rust/src/ingest/realws.rs:41:        std::process::exit(12);
engine-rust/src/ingest/mod.rs:292:        error!(reason = "OVERLOAD", "tick channel full, exiting 13");
engine-rust/src/ingest/mod.rs:294:        std::process::exit(13);
engine-rust/src/ingest/mod.rs:299:        // Prompt says "Backpressure (channel full ... saturated) -> exit 13"
engine-rust/src/ingest/mod.rs:301:        error!(reason = "OVERLOAD", "persist channel full, exiting 13");
engine-rust/src/ingest/mod.rs:302:        std::process::exit(13);

$ rg -n Config::load engine-rust
engine-rust/src/main.rs:93:        Config::load(&args.config)?
engine-rust/src/ingest/realws.rs:27:    let sources_config = match WsSourcesConfig::load(config_path) {

$ sed -n 1,240p scripts/soak_2h.py
#!/usr/bin/env python3
import sys
import os
import time
import subprocess
import argparse
import json
import uuid
import signal
import datetime
import re
import sqlite3
from pathlib import Path
from typing import Dict, Tuple

# --- Configuration & Constants ---
PSI_PATH = "/proc/pressure"
DECISION_LOG_PATH = "/opt/hybrid-trading-bot/data/ops/soak_decisions.jsonl"
ENGINE_SERVICE = "hybrid-engine.service"
HEALTHCHECK_SCRIPT = "/opt/hybrid-trading-bot/scripts/healthcheck.sh"
ABORT_FILE = "/opt/hybrid-trading-bot/data/ops/ABORT"
CONFIG_PATH = "/opt/hybrid-trading-bot/config/config.toml"

# Throttle Ladder: (State Name, sample_every value)
THROTTLE_LADDER = [
    ("NORMAL", 1),
    ("THROTTLE1", 5),
    ("THROTTLE2", 10),
    ("THROTTLE3", 20),
]

# Exit Codes from Engine
EXIT_ACTIONS = {
    0:  ("COMPLETE", "stop"),
    10: ("NETWORK", "restart_backoff"),
    11: ("PARSE", "retry_then_mock"),
    12: ("CONFIG", "abort"),
    13: ("OVERLOAD", "throttle_up"),
}

# Thresholds (avg10)
CPU_LIMIT = 20.0
MEM_LIMIT = 10.0
IO_LIMIT = 15.0

PSI_RE = re.compile(r'avg10=(\d+(\.\d+)?)')

def _parse_avg10(line: str) -> float:
    m = PSI_RE.search(line)
    return float(m.group(1)) if m else 0.0

def get_psi() -> Dict[str, object]:
    """
    PSI is stall time (percentage of wall time tasks are waiting), expressed as floats in the kernel output.
    DO NOT label as CPU utilization.
    """
    out: Dict[str, object] = {}
    for metric in ("cpu", "memory", "io"):
        path = f"/proc/pressure/{metric}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f.read().strip().splitlines() if ln.strip()]
            # Expected: lines[0] starts with "some", lines[1] starts with "full" (cpu usually has both)
            some = next((ln for ln in lines if ln.startswith("some ")), "")
            full = next((ln for ln in lines if ln.startswith("full ")), "")
            out[f"{metric}_some_raw"] = some
            out[f"{metric}_some_avg10"] = _parse_avg10(some) if some else 0.0
            out[f"{metric}_full_raw"] = full
            out[f"{metric}_full_avg10"] = _parse_avg10(full) if full else 0.0
        except Exception as e:
            out[f"{metric}_some_raw"] = f"ERROR: {e}"
            out[f"{metric}_some_avg10"] = -1.0
            out[f"{metric}_full_raw"] = f"ERROR: {e}"
            out[f"{metric}_full_avg10"] = -1.0
    return out

class StallDetector:
    def __init__(self, db_path: str, stall_threshold_sec: int = 60):
        self.db_path = db_path
        self.stall_threshold = stall_threshold_sec
        self.last_count = None
        self.last_progress_wall = None
        self.stall_streak = 0

    def check(self):
        try:
            # Use file URIs for read-only if possible, but basic path is safer for compatibility
            # Using read-only mode to prevent locking
            uri = f"file:{self.db_path}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=1.0)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*), MAX(ts) FROM ticks")
            row = cur.fetchone()
            conn.close()
            
            if not row:
                return (False, {"error": "No data returned from ticks table"})

            count, max_ts = row
            now = time.time()

            if self.last_count is None:
                # first observation seeds baselines
                self.last_count = count
                self.last_progress_wall = now
                return (False, {
                    "ticks_count": count,
                    "last_tick_ts": max_ts,
                    "note": "seed_baseline"
                })

            progressed = (count != self.last_count)
            if progressed:
                self.last_count = count
                self.last_progress_wall = now
                self.stall_streak = 0
                return (False, {"ticks_count": count, "last_tick_ts": max_ts, "progress": True})

            stalled = (now - (self.last_progress_wall or now)) > self.stall_threshold
            if stalled:
                self.stall_streak += 1

            return (stalled, {
                "ticks_count": count,
                "last_tick_ts": max_ts,
                "progress": False,
                "stall_streak": self.stall_streak,
                "seconds_since_progress": round(now - (self.last_progress_wall or now), 2),
            })
        except Exception as e:
            return (False, {"error": str(e)})

class SoakController:
    def __init__(self, args):
        self.args = args
        self.run_id = str(uuid.uuid4())
        self.current_state = "NORMAL" # Corresponds to THROTTLE_LADDER
        self.consecutive_pressure = 0
        self.start_time = time.time()
        self.total_seconds = args.seconds
        self.ingest_mode = args.mode
        self.stall_detector = StallDetector(args.db, stall_threshold_sec=45) # 45s stall threshold
        
        # Ensure log dir exists
        os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True)
        self.log_decision("STARTUP", f"Run ID: {self.run_id}, Mode: {self.ingest_mode}")
        
        # Reset sample_every to 1 at startup if using config-based approach
        self.update_config_sample_rate(1)

    def log_decision(self, action, reason, extra_data=None):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "ingest_mode": self.ingest_mode,
            "state": self.current_state,
            "current_sample_every": self.get_current_sample_rate(),
            "action": action,
            "reason": reason,
        }
        if extra_data:
            entry.update(extra_data)
        
        print(f"[SOAK] {action}: {reason}")
        try:
            with open(DECISION_LOG_PATH, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[WARN] Failed to write decision log: {e}")

    def get_current_sample_rate(self) -> int:
        vals = {n: v for (n, v) in THROTTLE_LADDER}
        return vals.get(self.current_state, 1)

    def update_config_sample_rate(self, new_rate: int):
        # Read config, replace sample_every = X with sample_every = new_rate
        try:
            if not os.path.exists(CONFIG_PATH):
                return
            
            with open(CONFIG_PATH, 'r') as f:
                content = f.read()
            
            if 'sample_every' in content:
                new_content = re.sub(r'sample_every\s*=\s*\d+', f'sample_every = {new_rate}', content)
            else:
                # Append to [engine] or end
                # Assuming simple toml for now or just append if safe. 
                # Better to replace if exists, or insert under [engine]
                if '[engine]' in content:
                     new_content = content.replace('[engine]', f'[engine]\nsample_every = {new_rate}')
                else:
                     new_content = content + f"\n[engine]\nsample_every = {new_rate}\n"
            
            with open(CONFIG_PATH, 'w') as f:
                f.write(new_content)
        except Exception as e:
             self.log_decision("CONFIG_ERROR", f"Failed to update sample_every: {e}")

    def next_throttle_state(self, cur_state: str) -> Tuple[str, int]:
        names = [n for (n, _) in THROTTLE_LADDER]
        vals  = {n: v for (n, v) in THROTTLE_LADDER}
        if cur_state not in vals:
            return ("NORMAL", 1)
        i = names.index(cur_state)
        j = min(i + 1, len(names) - 1)
        return (names[j], vals[names[j]])

    def restart_engine(self, reason: str):
        self.log_decision("ENGINE_RESTART", reason=reason, extra_data=get_psi())
        subprocess.run(["systemctl", "restart", ENGINE_SERVICE], check=False)
        time.sleep(2)
        subprocess.run(["systemctl", "--no-pager", "status", ENGINE_SERVICE], check=False)

    def stop_engine(self):
        self.log_decision("ENGINE_STOP", "Stopping service via systemctl")
        subprocess.run(["systemctl", "stop", ENGINE_SERVICE], check=False)

    def check_health(self):
        print(f"[SOAK] Running healthcheck: {HEALTHCHECK_SCRIPT}")
        rc = subprocess.call([HEALTHCHECK_SCRIPT])
        if rc != 0:
            self.log_decision("ABORT", "Healthcheck failed")
            sys.exit(1)

    def run_loop(self):
        self.check_health()
        
        # Start initial
        self.restart_engine("Soak Start")

        try:
            while True:
                time.sleep(5) # Analysis tick
                
                # 1. Check Duration
                elapsed = time.time() - self.start_time
                if elapsed > self.total_seconds:
                    self.log_decision("COMPLETE", "Soak duration reached")
                    break

$ sed -n 240,520p scripts/soak_2h.py
                    break

                # 2. Check Abort File
                if os.path.exists(ABORT_FILE):
                    self.log_decision("ABORT", "Operator abort file detected")
                    break

                # 3. Check Engine Service Status & Exit Codes
                # retrieving ExecMainCode from systemctl show
                try:
                    out = subprocess.check_output(
                        ["systemctl", "show", ENGINE_SERVICE, "--property=ExecMainStatus,ActiveState,SubState"], 
                        universal_newlines=True
                    )
                    # Parse properties
                    props = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
                    active_state = props.get("ActiveState", "unknown")
                    sub_state = props.get("SubState", "unknown")
                    
                    if active_state == "failed" or (active_state == "inactive" and sub_state == "dead"):
                         exit_code_str = props.get("ExecMainStatus", "0")
                         exit_code = int(exit_code_str) if exit_code_str.isdigit() else 0
                         
                         action_name, action_logic = EXIT_ACTIONS.get(exit_code, ("UNKNOWN", "abort"))
                         self.log_decision("ENGINE_EXIT", f"Service exited", {"exit_code": exit_code, "action": action_name})
                         
                         if action_logic == "stop":
                             break
                         elif action_logic == "restart_backoff":
                             time.sleep(5)
                             self.restart_engine(f"Restarting after {action_name}")
                         elif action_logic == "retry_then_mock":
                             if self.ingest_mode == "realws":
                                 self.ingest_mode = "mockws"
                                 # We can't easily switch mode without config support for mode or env var. 
                                 # Assuming for now restart resets to config default or we need to update config mode too.
                                 # For this specific task, we focus on reliability. 
                                 # Let's just restart for now.
                                 self.restart_engine("Restarting after protocol error")
                             else:
                                 self.log_decision("ABORT", "MockWS protocol failure")
                                 break
                         elif action_logic == "throttle_up":
                             # Advance throttle
                             next_s, next_val = self.next_throttle_state(self.current_state)
                             if next_s == self.current_state:
                                 self.log_decision("ABORT", "Overload at max throttle")
                                 break
                             self.current_state = next_s
                             self.update_config_sample_rate(next_val)
                             self.restart_engine(f"Throttling up to {next_s} (rate={next_val}) due to OVERLOAD")
                         else: # abort
                             self.log_decision("ABORT", f"Unhandled exit code {exit_code}")
                             break
                except Exception as e:
                    print(f"[WARN] Failed to check service status: {e}")

                # 4. PSI Monitor & Throttle
                psi = get_psi()
                cpu = psi.get("cpu_some_avg10", 0.0)
                mem = psi.get("memory_some_avg10", 0.0)
                io = psi.get("io_some_avg10", 0.0)

                pressure_reason = []
                if cpu > CPU_LIMIT: pressure_reason.append(f"CPU {cpu}")
                if mem > MEM_LIMIT: pressure_reason.append(f"MEM {mem}")
                if io > IO_LIMIT: pressure_reason.append(f"IO {io}")

                if pressure_reason:
                    self.consecutive_pressure += 1
                    next_s, next_val = self.next_throttle_state(self.current_state)
                    
                    if next_s != self.current_state:
                         self.current_state = next_s
                         self.update_config_sample_rate(next_val)
                         self.restart_engine(f"Throttling up to {next_s} due to PSI: {', '.join(pressure_reason)}")
                    else:
                         # Already max throttle
                         self.log_decision("THROTTLE_MAX", f"Sustained pressure under max throttle: {', '.join(pressure_reason)}", psi)
                         if self.consecutive_pressure > 5:
                             self.log_decision("ABORT", "Sustained pressure under max throttle", psi)
                             break
                else:
                    self.consecutive_pressure = 0
                    # Logic to allow recover? For safety in this phase, we generally latch up or hold. 
                    # If we want to recover, we'd step down. For now, strict fail-safe or hold is fine.
                    pass

                # 5. Stall Detection
                is_stalled, stall_data = self.stall_detector.check()
                if is_stalled:
                    self.log_decision("STALL", "Pipeline stalled", stall_data)
                    self.restart_engine("Restarting due to STALL")
                elif stall_data.get("error"):
                     print(f"[WARN] Stall detector error: {stall_data['error']}")

        except KeyboardInterrupt:
            self.log_decision("STOP", "Keyboard Interrupt")
        finally:
            # We don't necessarily stop the service on exit, the soak is just a controller. 
            # But the prompt says "stop immediately" if preflight fails. 
            # If soak finishes, we might leave it running or stop it. 
            # Standard soak behavior: stop when done.
            self.stop_engine()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=7200, help="Soak duration seconds")
    parser.add_argument("--mode", type=str, default="realws", help="Initial ingest mode")
    parser.add_argument("--db", type=str, default="/opt/hybrid-trading-bot/data/bot.db")
    args = parser.parse_args()

    controller = SoakController(args)
    controller.run_loop()

$ sed -n 1,260p engine-rust/src/ingest/realws.rs
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

$ rg -n struct Metrics|tick_count engine-rust/src
engine-rust/src/types.rs:176:pub struct Metrics {
engine-rust/src/types.rs:177:    pub tick_count: std::sync::atomic::AtomicU64,
engine-rust/src/main.rs:256:                tick_count = metrics_heartbeat.tick_count.load(Ordering::Relaxed),
engine-rust/src/main.rs:315:        tick_count = metrics.tick_count.load(Ordering::Relaxed),
engine-rust/src/strategy.rs:27:    let mut tick_count: u64 = 0;
engine-rust/src/strategy.rs:36:        tick_count += 1;
engine-rust/src/strategy.rs:39:        if tick_count % signal_every_n_ticks == 0 {
engine-rust/src/strategy.rs:67:                tick_count = tick_count,
engine-rust/src/ingest/realws.rs:122:                                                metrics.tick_count.fetch_add(1, Ordering::Relaxed);
engine-rust/src/ingest/realws.rs:132:                                            metrics.tick_count.fetch_add(1, Ordering::Relaxed);
engine-rust/src/ingest/mod.rs:102:                let count = metrics.tick_count.fetch_add(1, Ordering::Relaxed);
engine-rust/src/ingest/mod.rs:183:                     metrics.tick_count.fetch_add(1, Ordering::Relaxed);
engine-rust/src/ingest/mod.rs:245:                                                 metrics.tick_count.fetch_add(1, Ordering::Relaxed);

$ sed -n 160,260p engine-rust/src/types.rs
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

    #[test]
    fn test_side_display() {
        assert_eq!(format!("{}", Side::Buy), "BUY");
        assert_eq!(format!("{}", Side::Sell), "SELL");
    }
}

$ sed -n 220,360p engine-rust/src/main.rs
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
        bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
        bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
        risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
        "FINAL METRICS"
    );

    info!("engine-rust shutdown complete");
    Ok(())
}

$ sed -n 1,220p scripts/diagnose_cpu_pressure.sh
sed: can't read scripts/diagnose_cpu_pressure.sh: No such file or directory

$ rg --files -g diagnose_cpu_pressure.sh

$ rg --files -g *.sh
verify_phase3.sh
ops/scripts/mode_game.sh
ops/scripts/lowprio_pnpm.sh
ops/scripts/mode_bot.sh
scripts/port_guard_8501.sh
scripts/healthcheck.sh
scripts/proof_stall_detection.sh
scripts/preflight_phase2.sh
scripts/run_dashboard.sh
scripts/verify_phase2_proofs.sh
scripts/snapshot_health.sh
scripts/verify_phase2_1.sh
scripts/run_engine.sh
scripts/proof_check.sh
scripts/proof_throttling_delta.sh

$ rg -n diagnose_cpu
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1515:$ sed -n 1,220p scripts/diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1516:sed: can't read scripts/diagnose_cpu_pressure.sh: No such file or directory
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1518:$ rg --files -g diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1537:$ rg -n diagnose_cpu

$ rg -n Background Service Check -g *.sh

$ rg --files -g *pressure*

$ sed -n 1,260p scripts/proof_check.sh
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."  # repo root
sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;"
sqlite3 data/bot.db "SELECT symbol, price, ts FROM ticks ORDER BY ts DESC LIMIT 3;"
curl -I http://127.0.0.1:8501 | sed -n '1,20p'

$ rg -n pidstat|systemd-cgtop|iostat -g *.sh

$ rg -n diagnose_cpu_pressure -g *.md
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1515:$ sed -n 1,220p scripts/diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1516:sed: can't read scripts/diagnose_cpu_pressure.sh: No such file or directory
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1518:$ rg --files -g diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1538:docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1515:$ sed -n 1,220p scripts/diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1539:docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1516:sed: can't read scripts/diagnose_cpu_pressure.sh: No such file or directory
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1540:docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1518:$ rg --files -g diagnose_cpu_pressure.sh
docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md:1557:$ rg -n diagnose_cpu_pressure -g *.md

$ sed -n 1,200p scripts/preflight_phase2.sh
#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_phase2_2_1_reliability_metric_integrity.md"
mkdir -p docs/buglog

{
  echo "# Verification Log — Phase 2.2.1 (Reliability + Metric Integrity)"
  echo
  echo "## Execution Context"
  echo "- Date: $(date -Is)"
  echo "- Hostname: $(hostname)"
  echo "- Kernel: $(uname -a)"
  echo "- Git HEAD: $(git rev-parse HEAD)"
  echo
  echo "## Preflight"
  echo '```'
  command -v python3 && python3 --version
  command -v cargo && cargo --version || true
  command -v sqlite3 && sqlite3 --version
  command -v jq && jq --version || echo "jq: MISSING (required for proofs)"
  echo '```'
  echo
  echo "### PSI Baseline (/proc/pressure/*)"
  echo '```'
  for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
    echo "== $f =="
    cat "$f"
    echo
  done
  echo '```'
} | tee "$BUGLOG"

# Required scripts / files must exist
test -f docs/specs/behavior_contract_phase2.md || { echo "Missing spec authority"; exit 1; }
test -f scripts/soak_2h.py || { echo "Missing scripts/soak_2h.py"; exit 1; }

# If you have a healthcheck, run it; otherwise record skip explicitly.
if test -x ./scripts/healthcheck.sh; then
  {
    echo
    echo "### Healthcheck"
    echo '```'
    ./scripts/healthcheck.sh
    echo '```'
  } | tee -a "$BUGLOG"
else
  echo -e "\n### Healthcheck\nSKIP: ./scripts/healthcheck.sh not found or not executable" | tee -a "$BUGLOG"
fi

echo "PREFLIGHT PASS: $BUGLOG"

$ chmod +x scripts/diagnose_cpu_pressure.sh

$ scripts/diagnose_cpu_pressure.sh
--- 1. Timestamp ---
2026-01-09T16:17:49+00:00

--- 2. Host/Kernel ---
slimy-nuc1
Linux slimy-nuc1 6.8.0-90-generic #91-Ubuntu SMP PREEMPT_DYNAMIC Tue Nov 18 14:14:30 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux

--- 3. Uptime ---
 16:17:49 up 14 days, 13:56,  3 users,  load average: 6.38, 6.37, 6.79

--- 4. PSI Snapshot (/proc/pressure/*) ---
== /proc/pressure/cpu ==
some avg10=41.08 avg60=43.33 avg300=44.73 total=389440003549
full avg10=0.00 avg60=0.00 avg300=0.00 total=0

== /proc/pressure/memory ==
some avg10=0.00 avg60=0.03 avg300=0.02 total=13735023
full avg10=0.00 avg60=0.02 avg300=0.00 total=8051402

== /proc/pressure/io ==
some avg10=0.00 avg60=0.00 avg300=0.00 total=2017260713
full avg10=0.00 avg60=0.00 avg300=0.00 total=431945548

--- 5. Load Average ---
6.38 6.37 6.79 8/497 1794340

--- 6. Memory Summary ---
               total        used        free      shared  buff/cache   available
Mem:            15Gi        13Gi       536Mi       216Ki       2.3Gi       2.5Gi
Swap:          4.0Gi       900Mi       3.1Gi

--- 7. Disk Usage ---
Filesystem                         Size  Used Avail Use% Mounted on
tmpfs                              1.6G  1.5M  1.6G   1% /run
/dev/mapper/ubuntu--vg-ubuntu--lv  233G  143G   80G  65% /
tmpfs                              7.8G     0  7.8G   0% /dev/shm
tmpfs                              5.0M     0  5.0M   0% /run/lock
/dev/nvme0n1p2                     2.0G  197M  1.6G  11% /boot
tmpfs                              1.6G   16K  1.6G   1% /run/user/1000

--- 8. Top CPU (10 samples over 10s) ---
Linux 6.8.0-90-generic (slimy-nuc1) 	01/09/26 	_x86_64_	(4 CPU)

16:17:49      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:50        0       324    0.98    0.00    0.00    0.00    0.98     1  systemd-journal
16:17:50     1000       992    0.98    0.00    0.00    2.94    0.98     1  PM2 v6.0.13: Go
16:17:50     1000   1285683   12.75    7.84    0.00   44.12   20.59     3  node
16:17:50     1000   1286051    0.98    0.98    0.00    3.92    1.96     0  language_server
16:17:50     1000   1301437    9.80  170.59    0.00    0.00  180.39     2  rg
16:17:50     1000   1772927    1.96    0.00    0.00    2.94    1.96     3  codex
16:17:50     1000   1794348    0.98    0.98    0.00    0.00    1.96     3  pidstat
16:17:50     1000   1794357   49.02    6.86    0.00    7.84   55.88     2  node /home/slim
16:17:50     1000   1794381   15.69    1.96    0.00    6.86   17.65     2  node /home/slim

16:17:50      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:51        0         1    1.00    0.00    0.00    1.00    1.00     0  systemd
16:17:51        0        17    0.00    1.00    0.00    0.00    1.00     1  rcu_preempt
16:17:51        0       731    0.00    1.00    0.00    0.00    1.00     1  systemd-logind
16:17:51     1000       992    1.00    0.00    0.00    1.00    1.00     1  PM2 v6.0.13: Go
16:17:51     1000   1285655    1.00    0.00    0.00    1.00    1.00     0  node
16:17:51     1000   1285683    9.00    7.00    0.00   40.00   16.00     1  node
16:17:51     1000   1286051    1.00    1.00    0.00    1.00    2.00     1  language_server
16:17:51     1000   1301437   10.00  162.00    0.00    0.00  172.00     2  rg
16:17:51     1000   1772927    2.00    0.00    0.00    2.00    2.00     3  codex
16:17:51     1000   1794348    0.00    1.00    0.00    0.00    1.00     3  pidstat
16:17:51     1000   1794381   65.00    6.00    0.00    7.00   71.00     0  node /home/slim
16:17:51     1000   1794415   16.00    2.00    0.00    5.00   18.00     2  node
16:17:51     1000   1794423    3.00    0.00    0.00    7.00    3.00     0  node

16:17:51      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:52        0         1    0.00    1.00    0.00    0.00    1.00     2  systemd
16:17:52     1000       992    0.00    1.00    0.00    1.00    1.00     2  PM2 v6.0.13: Go
16:17:52     1000   1285655    0.00    1.00    0.00    0.00    1.00     3  node
16:17:52     1000   1285683    0.00   53.00    0.00    3.00   53.00     3  node
16:17:52     1000   1286051    1.00    2.00    0.00    1.00    3.00     0  language_server
16:17:52     1000   1301437    0.00    5.00    0.00    0.00    5.00     2  rg
16:17:52        0   1753261    0.00    1.00    0.00    0.00    1.00     3  kworker/u8:10-events_unbound
16:17:52     1000   1772927    2.00    0.00    0.00    2.00    2.00     0  codex
16:17:52     1000   1794348    1.00    0.00    0.00    1.00    1.00     1  pidstat
16:17:52     1000   1794423   73.00    9.00    0.00    6.00   82.00     3  node /home/slim
16:17:52     1000   1794435   76.00    8.00    0.00    6.00   84.00     2  node /home/slim
16:17:52     1000   1794458   19.00    3.00    0.00    1.00   22.00     0  node
16:17:52     1000   1794471   11.00    1.00    0.00    0.00   12.00     2  node

16:17:52      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:53        0       324    0.00    1.00    0.00    0.00    1.00     3  systemd-journal
16:17:53     1000       992    1.00    0.00    0.00    0.00    1.00     2  PM2 v6.0.13: Go
16:17:53     1000      1012    1.00    0.00    0.00    0.00    1.00     3  node /home/slim
16:17:53     1000    782325    0.00    1.00    0.00    1.00    1.00     3  sshd
16:17:53        0   1049323    1.00    0.00    0.00    0.00    1.00     1  thermald
16:17:53     1000   1285683    0.00   45.00    0.00    7.00   45.00     1  node
16:17:53     1000   1286051    2.00    0.00    0.00    3.00    2.00     3  language_server
16:17:53     1000   1301437    2.00   18.00    0.00    0.00   20.00     2  rg
16:17:53     1000   1772927    3.00    1.00    0.00    3.00    4.00     3  codex
16:17:53     1000   1794348    0.00    1.00    0.00    1.00    1.00     2  pidstat
16:17:53     1000   1794484   74.00    7.00    0.00    2.00   81.00     0  node /home/slim
16:17:53     1000   1794492   69.00    7.00    0.00    1.00   76.00     0  node /home/slim
16:17:53     1000   1794509    9.00    1.00    0.00    0.00   10.00     0  node
16:17:53     1000   1794517    1.00    0.00    0.00    1.00    1.00     1  node

16:17:53      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:54     1000       992    3.00    1.00    0.00    3.00    4.00     2  PM2 v6.0.13: Go
16:17:54     1000   1285683   11.00    6.00    0.00   47.00   17.00     3  node
16:17:54     1000   1286051    1.00    2.00    0.00    5.00    3.00     0  language_server
16:17:54     1000   1301437   11.00  169.00    0.00    0.00  180.00     2  rg
16:17:54     1000   1733966    0.00    1.00    0.00    0.00    1.00     3  engine-rust
16:17:54        0   1753253    0.00    1.00    0.00    0.00    1.00     1  kworker/u8:6-events_unbound
16:17:54     1000   1772927    3.00    0.00    0.00    1.00    3.00     1  codex
16:17:54     1000   1794348    0.00    2.00    0.00    2.00    2.00     2  pidstat
16:17:54     1000   1794551   64.00    8.00    0.00   12.00   72.00     0  node /home/slim
16:17:54     1000   1794563   48.00    7.00    0.00    6.00   55.00     2  node /home/slim

16:17:54      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:55        0        17    0.00    0.99    0.00    0.00    0.99     0  rcu_preempt
16:17:55        0       854    0.00    0.99    0.00    0.00    0.99     0  containerd
16:17:55     1000       992    0.99    0.00    0.00    0.99    0.99     3  PM2 v6.0.13: Go
16:17:55     1000    782325    0.99    0.99    0.00    0.00    1.98     3  sshd
16:17:55     1000   1285584    0.99    0.00    0.00    0.99    0.99     1  node
16:17:55     1000   1285683    7.92    6.93    0.00   35.64   14.85     3  node
16:17:55     1000   1285694    0.99    0.00    0.00    0.00    0.99     1  node
16:17:55     1000   1286051    0.99    0.99    0.00    2.97    1.98     1  language_server
16:17:55     1000   1301437   12.87  169.31    0.00    0.00  182.18     2  rg
16:17:55     1000   1772927    2.97    0.00    0.00    1.98    2.97     3  codex
16:17:55     1000   1794348    0.99    0.99    0.00    0.99    1.98     2  pidstat
16:17:55     1000   1794600   40.59    6.93    0.00    9.90   47.52     1  node /home/slim
16:17:55     1000   1794612   14.85    1.98    0.00    1.98   16.83     0  node

16:17:55      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:56     1000       992    1.00    0.00    0.00    2.00    1.00     0  PM2 v6.0.13: Go
16:17:56     1000   1285683   80.00   21.00    0.00   57.00  101.00     2  node
16:17:56     1000   1286051    1.00    1.00    0.00    3.00    2.00     1  language_server
16:17:56     1000   1301437    7.00  111.00    0.00    0.00  118.00     2  rg
16:17:56     1000   1772927    1.00    1.00    0.00    3.00    2.00     1  codex
16:17:56     1000   1794348    0.00    1.00    0.00    2.00    1.00     2  pidstat
16:17:56     1000   1794612   70.00    6.00    0.00    8.00   76.00     0  node /home/slim
16:17:56     1000   1794632   17.00    3.00    0.00    4.00   20.00     3  node
16:17:56     1000   1794649    2.00    0.00    0.00    4.00    2.00     2  node

16:17:56      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:57        0       849    0.00    1.00    0.00    0.00    1.00     1  fail2ban-server
16:17:57     1000       992    1.00    1.00    0.00    1.00    2.00     1  PM2 v6.0.13: Go
16:17:57     1000   1285584    0.00    1.00    0.00    1.00    1.00     1  node
16:17:57     1000   1285683   90.00   29.00    0.00   64.00  119.00     3  node
16:17:57     1000   1286051    1.00    1.00    0.00    1.00    2.00     2  language_server
16:17:57     1000   1301437    4.00   87.00    0.00    0.00   91.00     2  rg
16:17:57     1000   1772927    2.00    0.00    0.00    3.00    2.00     1  codex
16:17:57     1000   1794348    1.00    1.00    0.00    2.00    2.00     2  pidstat
16:17:57     1000   1794649   62.00    9.00    0.00   36.00   71.00     0  node /home/slim
16:17:57     1000   1794661   33.00    6.00    0.00   27.00   39.00     1  node /home/slim
16:17:57     1000   1794668   34.00    7.00    0.00   11.00   41.00     0  node

16:17:57      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:58        0        17    0.00    1.00    0.00    0.00    1.00     1  rcu_preempt
16:17:58     1000      1012    1.00    0.00    0.00    1.00    1.00     1  node /home/slim
16:17:58     1000   1285683  129.00   55.00    0.00   57.00  184.00     1  node
16:17:58     1000   1286051    1.00    2.00    0.00    0.00    3.00     2  language_server
16:17:58     1000   1301437    4.00   45.00    0.00    0.00   49.00     2  rg
16:17:58        0   1725502    0.00    1.00    0.00    0.00    1.00     3  kworker/u8:7-events_unbound
16:17:58        0   1753261    0.00    1.00    0.00    0.00    1.00     1  kworker/u8:10-events_unbound
16:17:58     1000   1772927    1.00    1.00    0.00    2.00    2.00     3  codex
16:17:58     1000   1794348    0.00    1.00    0.00    0.00    1.00     2  pidstat
16:17:58     1000   1794661   50.00    3.00    0.00   12.00   53.00     0  node /home/slim
16:17:58     1000   1794693   24.00    3.00    0.00   13.00   27.00     3  node
16:17:58     1000   1794710   16.00    2.00    0.00    4.00   18.00     0  node /home/slim

16:17:58      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
16:17:59        0        36    0.00    1.00    0.00    0.00    1.00     3  ksoftirqd/3
16:17:59        0        65    0.00    2.00    0.00    2.00    2.00     3  kswapd0
16:17:59     1000       992    1.00    0.00    0.00    0.00    1.00     0  PM2 v6.0.13: Go
16:17:59     1000    782325    0.00    1.00    0.00    1.00    1.00     0  sshd
16:17:59     1000   1285683   71.00   82.00    0.00    9.00  153.00     1  node
16:17:59     1000   1286051   13.00    0.00    0.00    0.00   13.00     2  language_server
16:17:59     1000   1301437    0.00    1.00    0.00    0.00    1.00     2  rg
16:17:59     1000   1772927    2.00    0.00    0.00    4.00    2.00     0  codex
16:17:59     1000   1794348    1.00    1.00    0.00    1.00    2.00     2  pidstat
16:17:59     1000   1794710   66.00    7.00    0.00   22.00   73.00     1  node /home/slim
16:17:59     1000   1794722   66.00    7.00    0.00    9.00   73.00     0  node /home/slim
16:17:59     1000   1794733    0.00   31.00    0.00   27.00   31.00     3  node
16:17:59     1000   1794735    3.00    1.00    0.00    4.00    4.00     0  node

Average:      UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
Average:        0         1    0.10    0.10    0.00    0.20    0.20     -  systemd
Average:        0        17    0.00    0.30    0.00    0.80    0.30     -  rcu_preempt
Average:        0        36    0.00    0.10    0.00    0.10    0.10     -  ksoftirqd/3
Average:        0        65    0.00    0.20    0.00    0.20    0.20     -  kswapd0
Average:        0       324    0.10    0.10    0.00    0.30    0.20     -  systemd-journal
Average:        0       731    0.00    0.10    0.00    0.00    0.10     -  systemd-logind
Average:        0       849    0.00    0.10    0.00    0.00    0.10     -  fail2ban-server
Average:        0       854    0.00    0.10    0.00    0.00    0.10     -  containerd
Average:     1000       992    1.00    0.30    0.00    1.40    1.30     -  PM2 v6.0.13: Go
Average:     1000      1012    0.20    0.00    0.00    0.40    0.20     -  node /home/slim
Average:     1000    782325    0.10    0.30    0.00    1.00    0.40     -  sshd
Average:        0   1049323    0.10    0.00    0.00    0.00    0.10     -  thermald
Average:     1000   1285584    0.10    0.10    0.00    0.60    0.20     -  node
Average:     1000   1285655    0.10    0.10    0.00    0.60    0.20     -  node
Average:     1000   1285683   40.98   31.21    0.00   36.39   72.18     -  node
Average:     1000   1285694    0.10    0.00    0.00    0.30    0.10     -  node
Average:     1000   1286051    2.29    1.10    0.00    2.09    3.39     -  language_server
Average:     1000   1301437    6.08   94.02    0.00    0.00  100.10     -  rg
Average:        0   1725502    0.00    0.10    0.00    0.10    0.10     -  kworker/u8:7-iou_exit
Average:     1000   1733966    0.00    0.10    0.00    0.00    0.10     -  engine-rust
Average:        0   1753253    0.00    0.10    0.00    0.00    0.10     -  kworker/u8:6-iou_exit
Average:        0   1753261    0.00    0.20    0.00    0.10    0.20     -  kworker/u8:10-iou_exit
Average:     1000   1772927    2.09    0.30    0.00    2.49    2.39     -  codex
Average:     1000   1794348    0.50    1.00    0.00    1.00    1.50     -  pidstat
Average:     1000   1794710    8.18    0.90    0.00    2.59    9.07     -  node /home/slim
Average:     1000   1794722    6.58    0.70    0.00    0.90    7.28     -  node /home/slim
Average:     1000   1794733    0.00    3.09    0.00    2.69    3.09     -  node
Average:     1000   1794735    0.30    0.10    0.00    0.40    0.40     -  node

--- 9. systemd cgroup CPU snapshot ---
Unknown argument to --cpu=: 1

--- 10. Disk I/O Wait ---
          78.78    0.03    8.77    0.04    0.00   12.39

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
dm-0             0.72     15.73     0.00   0.00    0.30    21.86   24.01    228.92     0.00   0.00    2.66     9.54    0.06    115.39     0.00   0.00    1.15  1898.56    0.00    0.00    0.06   1.29
loop0            0.00      0.00     0.00   0.00    0.00     1.27    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00
nvme0n1          0.60     15.74     0.12  16.19    0.26    26.08   15.50    228.92     9.28  37.45    1.88    14.76    0.06    116.81     0.00   0.00    1.16  1921.03    0.51    3.74    0.03   0.81


avg-cpu:  %user   %nice %system %iowait  %steal   %idle
          58.81    0.00   38.96    0.25    0.00    1.99

Device            r/s     rkB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wkB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dkB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
dm-0             6.93     27.72     0.00   0.00    1.00     4.00   38.61    150.50     0.00   0.00    0.31     3.90    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.02   0.69
loop0            0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00      0.00     0.00   0.00    0.00     0.00    0.00    0.00    0.00   0.00
nvme0n1          2.97     27.72     3.96  57.14    1.00     9.33   36.63    150.50     1.98   5.13    0.92     4.11    0.00      0.00     0.00   0.00    0.00     0.00    0.99    3.00    0.04   0.89




$ cat engine-rust/Cargo.toml
[package]
name = "engine-rust"
version = "0.1.0"
edition = "2021"
description = "Phase 2 Rust Pipeline Skeleton - Shadow Mode Trading Engine"
authors = ["hybrid-trading-bot"]

[dependencies]
# Async runtime
tokio = { version = "1", features = ["full", "signal"] }

# Database
sqlx = { version = "0.8", features = ["runtime-tokio", "sqlite", "macros"] }

# Error handling
anyhow = "1"
thiserror = "1"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"
toml = "0.8"
futures = "0.3"

# Networking (Phase 2.1)
tokio-tungstenite = { version = "0.20", features = ["rustls-tls-native-roots"] }
url = "2"

# Utilities
uuid = { version = "1", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
clap = { version = "4", features = ["derive"] }

[dev-dependencies]
proptest = "1"
tokio-test = "0.4"
tempfile = "3"

[[bin]]
name = "engine-rust"
path = "src/main.rs"

[profile.release]
opt-level = 3
lto = true

$ cargo test
   Compiling sqlx-core v0.8.6
   Compiling tokio-rustls v0.24.1
   Compiling rand_chacha v0.9.0
   Compiling proptest v1.9.0
   Compiling tokio-tungstenite v0.20.1
   Compiling sqlx-sqlite v0.8.6
   Compiling sqlx v0.8.6
   Compiling engine-rust v0.1.0 (/opt/hybrid-trading-bot/engine-rust)
warning: unused variable: `symbol`
   --> src/ingest/mod.rs:129:5
    |
129 |     symbol: String,
    |     ^^^^^^ help: if this is intentional, prefix it with an underscore: `_symbol`
    |
    = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `symbol`
   --> src/ingest/mod.rs:198:5
    |
198 |     symbol: String,
    |     ^^^^^^ help: if this is intentional, prefix it with an underscore: `_symbol`

warning: field `makerSide` is never read
   --> src/ingest/realws.rs:195:9
    |
190 |     struct GEvent {
    |            ------ field in this struct
...
195 |         makerSide: Option<String>,
    |         ^^^^^^^^^
    |
    = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: structure field `T` should have a snake case name
   --> src/ingest/realws.rs:176:9
    |
176 |         T: i64,
    |         ^ help: convert the identifier to snake case: `t`
    |
    = note: `#[warn(non_snake_case)]` (part of `#[warn(nonstandard_style)]`) on by default

warning: structure field `makerSide` should have a snake case name
   --> src/ingest/realws.rs:195:9
    |
195 |         makerSide: Option<String>,
    |         ^^^^^^^^^ help: convert the identifier to snake case: `maker_side`

warning: `engine-rust` (lib) generated 5 warnings (run `cargo fix --lib -p engine-rust` to apply 2 suggestions)
warning: unused import: `std::net::SocketAddr`
 --> src/bin/mock_ws.rs:8:5
  |
8 | use std::net::SocketAddr;
  |     ^^^^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(unused_imports)]` (part of `#[warn(unused)]`) on by default

warning: field `kind` is never read
 --> src/ingest/ws_sources.rs:8:9
  |
5 | pub struct WsSourceConfig {
  |            -------------- field in this struct
...
8 |     pub kind: String, // "ticker", etc.
  |         ^^^^
  |
  = note: `WsSourceConfig` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis

warning: unused variable: `data`
  --> src/bin/mock_ws.rs:67:34
   |
67 |                 Ok(Message::Ping(data)) => {
   |                                  ^^^^ help: if this is intentional, prefix it with an underscore: `_data`
   |
   = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `read_handle`
  --> src/bin/mock_ws.rs:63:9
   |
63 |     let read_handle = tokio::spawn(async move {
   |         ^^^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_read_handle`

warning: `engine-rust` (bin "mock_ws" test) generated 3 warnings (run `cargo fix --bin "mock_ws" -p engine-rust --tests` to apply 3 suggestions)
warning: `engine-rust` (lib test) generated 5 warnings (5 duplicates)
warning: `engine-rust` (bin "mock_ws") generated 3 warnings (3 duplicates)
warning: `engine-rust` (bin "engine-rust" test) generated 6 warnings (6 duplicates)
warning: `engine-rust` (bin "engine-rust") generated 6 warnings (5 duplicates)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 1m 15s
     Running unittests src/lib.rs (target/debug/deps/engine_rust-c2dc455cd1669871)

running 18 tests
test config::tests::test_default_risk_caps ... ok
test config::tests::test_shadow_mode_validates ... ok
test config::tests::test_live_mode_fails_without_armed ... ok
test config::tests::test_default_mode_is_shadow ... ok
test execution::tests::test_exposure_tracker_per_symbol_cap ... ok
test execution::tests::test_exposure_tracker_respects_caps ... ok
test execution::tests::test_shadow_execution_has_no_network_fields ... ok
test db::tests::test_pragma_verification_passes ... ok
test db::tests::test_pragma_values_correct ... ok
test db::tests::test_schema_creation ... ok
test strategy::tests::test_signal_determinism ... ok
test strategy::tests::test_signal_generation_every_n_ticks ... ok
test types::tests::test_event_id_unique ... ok
test types::tests::test_reason_code_display ... ok
test types::tests::test_side_display ... ok
test persist::tests::test_persist_signal ... ok
test persist::tests::test_persist_tick ... ok
test persist::tests::test_batch_flush ... ok

test result: ok. 18 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.63s

     Running unittests src/main.rs (target/debug/deps/engine_rust-471868ea68540da5)

running 19 tests
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
test strategy::tests::test_signal_determinism ... ok
test strategy::tests::test_signal_generation_every_n_ticks ... ok
test tests::invalid_toml_is_classified_as_config_error ... ok
test types::tests::test_event_id_unique ... ok
test types::tests::test_reason_code_display ... ok
test types::tests::test_side_display ... ok
test persist::tests::test_persist_signal ... ok
test persist::tests::test_persist_tick ... ok
test persist::tests::test_batch_flush ... ok

test result: ok. 19 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.61s

     Running unittests src/bin/mock_ws.rs (target/debug/deps/mock_ws-7b748e3779c1f9e9)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/pragma_verification.rs (target/debug/deps/pragma_verification-6196832d160b1f9d)

running 5 tests
test test_pragma_verification_passes ... ok
test test_pragma_values_are_correct ... ok
test test_pragma_verification_fails_on_mismatch ... ok
test test_schema_creation ... ok
test test_wal_allows_concurrent_access ... ok

test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.13s

     Running tests/property_tests.rs (target/debug/deps/property_tests-84f5c92aa1f8fb06)

running 7 tests
test per_symbol_exposure_respects_caps ... ok
test order_trade_correctly_linked ... ok
test unit_tests::test_exposure_tracker_release ... ok
test unit_tests::test_shadow_execution_struct_has_no_network_fields ... ok
test shadow_orders_always_marked ... ok
test shadow_execution_makes_zero_network_calls ... ok
test risk_caps_never_exceeded ... ok

test result: ok. 7 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 1.88s

   Doc-tests engine_rust

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s


$ systemctl restart hybrid-engine.service

$ python3 scripts/soak_2h.py --help
usage: soak_2h.py [-h] [--seconds SECONDS] [--mode MODE] [--db DB]
                  [--psi-actions {on,logonly,off}]
                  [--stall-threshold-sec STALL_THRESHOLD_SEC]

options:
  -h, --help            show this help message and exit
  --seconds SECONDS     Soak duration seconds
  --mode MODE           Initial ingest mode
  --db DB
  --psi-actions {on,logonly,off}
                        PSI actions: on=throttle/restart, logonly=record PSI
                        only, off=skip PSI
  --stall-threshold-sec STALL_THRESHOLD_SEC
                        Seconds without tick progress before STALL triggers

$ rg --files -g *.service
ops/systemd/hybrid-health-snapshot.service

$ ls -la ops/systemd
total 20
drwxrwxr-x 3 slimy slimy 4096 Jan  9 11:10 .
drwxrwxr-x 4 slimy slimy 4096 Jan  8 17:59 ..
-rw-rw-r-- 1 slimy slimy  540 Jan  9 11:10 hybrid-health-snapshot.service
-rw-rw-r-- 1 slimy slimy  335 Jan  9 11:10 hybrid-health-snapshot.timer
drwxrwxr-x 2 slimy slimy 4096 Jan  9 11:00 mc-paper.service.d

$ ls -la ops/systemd/mc-paper.service.d
total 16
drwxrwxr-x 2 slimy slimy 4096 Jan  9 11:00 .
drwxrwxr-x 3 slimy slimy 4096 Jan  9 11:10 ..
-rw-rw-r-- 1 slimy slimy  528 Jan  9 10:23 20-resources.conf
-rw-rw-r-- 1 slimy slimy  113 Jan  9 11:00 30-restart-sane.conf

$ cat ops/systemd/mc-paper.service.d/30-restart-sane.conf
[Service]
Restart=on-failure
RestartSec=5

ExecStop=
KillSignal=SIGTERM
TimeoutStopSec=60

SuccessExitStatus=143

$ ls -la ops/systemd/hybrid-engine.service.d
total 12
drwxrwxr-x 2 slimy slimy 4096 Jan  9 16:21 .
drwxrwxr-x 4 slimy slimy 4096 Jan  9 16:21 ..
-rw-rw-r-- 1 slimy slimy  132 Jan  9 16:21 30-restart-exit12.conf

$ git status -sb
## main...origin/main [ahead 10]
 M engine-rust/src/ingest/realws.rs
 M engine-rust/src/main.rs
 M engine-rust/src/types.rs
 M scripts/soak_2h.py
?? docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md
?? ops/systemd/hybrid-engine.service.d/
?? scripts/diagnose_cpu_pressure.sh

$ git diff --stat
 engine-rust/src/ingest/realws.rs | 12 ++++++
 engine-rust/src/main.rs          | 48 +++++++++++++++++++++++-
 engine-rust/src/types.rs         |  2 +
 scripts/soak_2h.py               | 81 ++++++++++++++++++++++++++--------------
 4 files changed, 112 insertions(+), 31 deletions(-)

$ git add ops/systemd/hybrid-engine.service.d/30-restart-exit12.conf

$ git commit -m hardening(systemd): prevent restart on exit 12
[main 20a33b1] hardening(systemd): prevent restart on exit 12
 1 file changed, 5 insertions(+)
 create mode 100644 ops/systemd/hybrid-engine.service.d/30-restart-exit12.conf

$ git diff engine-rust/src/main.rs
diff --git a/engine-rust/src/main.rs b/engine-rust/src/main.rs
index 1e61699..84809c5 100644
--- a/engine-rust/src/main.rs
+++ b/engine-rust/src/main.rs
@@ -23,7 +23,7 @@ use std::sync::atomic::Ordering;
 use std::sync::Arc;
 use tokio::sync::{broadcast, mpsc};
 use tokio::time::{interval, Duration};
-use tracing::{info, warn};
+use tracing::{error, info, warn};
 
 use config::{Config, ExecutionMode};
 use types::Metrics;
@@ -90,7 +90,20 @@ async fn main() -> Result<()> {
 
     // Load configuration
     let mut config = if std::path::Path::new(&args.config).exists() {
-        Config::load(&args.config)?
+        match Config::load(&args.config) {
+            Ok(config) => config,
+            Err(err) => {
+                if is_toml_parse_error(&err) {
+                    error!(
+                        config_path = %args.config,
+                        error = %err,
+                        "config TOML parse failed"
+                    );
+                    std::process::exit(EXIT_CONFIG);
+                }
+                return Err(err);
+            }
+        }
     } else {
         info!(
             config_path = %args.config,
@@ -259,6 +272,8 @@ async fn main() -> Result<()> {
                 trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                 persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                 persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
+                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
+                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                 bp_drops_tick = metrics_heartbeat
                     .backpressure_drops_tick
                     .load(Ordering::Relaxed),
@@ -318,6 +333,8 @@ async fn main() -> Result<()> {
         trade_count = metrics.trade_count.load(Ordering::Relaxed),
         persist_count = metrics.persist_count.load(Ordering::Relaxed),
         persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
+        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
+        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
         bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
         bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
         risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
@@ -327,3 +344,30 @@ async fn main() -> Result<()> {
     info!("engine-rust shutdown complete");
     Ok(())
 }
+
+fn is_toml_parse_error(err: &anyhow::Error) -> bool {
+    err.downcast_ref::<toml::de::Error>().is_some()
+}
+
+#[cfg(test)]
+mod tests {
+    use super::is_toml_parse_error;
+    use crate::config::Config;
+    use std::fs;
+    use std::time::{SystemTime, UNIX_EPOCH};
+
+    #[test]
+    fn invalid_toml_is_classified_as_config_error() {
+        let mut path = std::env::temp_dir();
+        let unique = SystemTime::now()
+            .duration_since(UNIX_EPOCH)
+            .expect("time ok")
+            .as_nanos();
+        path.push(format!("engine_config_invalid_{unique}.toml"));
+
+        fs::write(&path, "invalid = [toml").expect("write invalid toml");
+        let err = Config::load(path.to_str().expect("path utf-8")).unwrap_err();
+        assert!(is_toml_parse_error(&err));
+        let _ = fs::remove_file(&path);
+    }
+}


$ sudo tee /etc/systemd/system/hybrid-engine.service.d/override.conf >/dev/null <<"EOF"
[Service]
# Phase 2.2.2: Switch to release binary (5.7MB vs 103MB debug)
ExecStart=
ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

# Phase 2.2.2: Honor typed exit codes (12=CONFIG should not restart)
Restart=on-failure
RestartPreventExitStatus=12
# Optional: treat 12 as clean for status dashboards
# SuccessExitStatus=12
EOF

$ sudo systemctl daemon-reload

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecStart
Restart=on-failure
RestartPreventExitStatus=12
ExecStart={ path=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; argv[]=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }

$ cargo build --release
   Compiling getrandom v0.2.16
   Compiling ring v0.17.14
   Compiling futures-sink v0.3.31
   Compiling crypto-common v0.1.7
   Compiling futures-channel v0.3.31
   Compiling digest v0.10.7
   Compiling futures-macro v0.3.31
   Compiling zerocopy v0.8.33
   Compiling untrusted v0.9.0
   Compiling rustls v0.21.12
   Compiling rand_core v0.6.4
   Compiling httparse v1.10.1
   Compiling sha2 v0.10.9
   Compiling futures-util v0.3.31
   Compiling fnv v1.0.7
   Compiling base64 v0.21.7
   Compiling rustls-pemfile v1.0.4
   Compiling http v0.2.12
   Compiling ppv-lite86 v0.2.21
   Compiling rand_chacha v0.3.1
   Compiling rand v0.8.5
   Compiling flume v0.11.1
   Compiling futures-executor v0.3.31
   Compiling sqlx-core v0.8.6
   Compiling sha1 v0.10.6
   Compiling utf-8 v0.7.6
   Compiling byteorder v1.5.0
   Compiling data-encoding v2.9.0
   Compiling openssl-probe v0.1.6
   Compiling rustls-native-certs v0.6.3
   Compiling futures v0.3.31
   Compiling sqlx-sqlite v0.8.6
   Compiling sqlx v0.8.6
   Compiling sct v0.7.1
   Compiling rustls-webpki v0.101.7
   Compiling tungstenite v0.20.1
   Compiling tokio-rustls v0.24.1
   Compiling tokio-tungstenite v0.20.1
   Compiling engine-rust v0.1.0 (/opt/hybrid-trading-bot/engine-rust)
warning: unused variable: `symbol`
   --> src/ingest/mod.rs:129:5
    |
129 |     symbol: String,
    |     ^^^^^^ help: if this is intentional, prefix it with an underscore: `_symbol`
    |
    = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `symbol`
   --> src/ingest/mod.rs:198:5
    |
198 |     symbol: String,
    |     ^^^^^^ help: if this is intentional, prefix it with an underscore: `_symbol`

warning: field `makerSide` is never read
   --> src/ingest/realws.rs:195:9
    |
190 |     struct GEvent {
    |            ------ field in this struct
...
195 |         makerSide: Option<String>,
    |         ^^^^^^^^^
    |
    = note: `#[warn(dead_code)]` (part of `#[warn(unused)]`) on by default

warning: structure field `T` should have a snake case name
   --> src/ingest/realws.rs:176:9
    |
176 |         T: i64,
    |         ^ help: convert the identifier to snake case: `t`
    |
    = note: `#[warn(non_snake_case)]` (part of `#[warn(nonstandard_style)]`) on by default

warning: structure field `makerSide` should have a snake case name
   --> src/ingest/realws.rs:195:9
    |
195 |         makerSide: Option<String>,
    |         ^^^^^^^^^ help: convert the identifier to snake case: `maker_side`

warning: `engine-rust` (lib) generated 5 warnings (run `cargo fix --lib -p engine-rust` to apply 2 suggestions)
warning: unused import: `std::net::SocketAddr`
 --> src/bin/mock_ws.rs:8:5
  |
8 | use std::net::SocketAddr;
  |     ^^^^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(unused_imports)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `data`
  --> src/bin/mock_ws.rs:67:34
   |
67 |                 Ok(Message::Ping(data)) => {
   |                                  ^^^^ help: if this is intentional, prefix it with an underscore: `_data`
   |
   = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: unused variable: `read_handle`
  --> src/bin/mock_ws.rs:63:9
   |
63 |     let read_handle = tokio::spawn(async move {
   |         ^^^^^^^^^^^ help: if this is intentional, prefix it with an underscore: `_read_handle`

warning: field `kind` is never read
 --> src/ingest/ws_sources.rs:8:9
  |
5 | pub struct WsSourceConfig {
  |            -------------- field in this struct
...
8 |     pub kind: String, // "ticker", etc.
  |         ^^^^
  |
  = note: `WsSourceConfig` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis

warning: `engine-rust` (bin "mock_ws") generated 3 warnings (run `cargo fix --bin "mock_ws" -p engine-rust` to apply 3 suggestions)
warning: `engine-rust` (bin "engine-rust") generated 6 warnings (5 duplicates)
    Finished `release` profile [optimized] target(s) in 3m 42s

$ (sleep 10; systemctl show -p MainPID --value hybrid-engine.service; kill -STOP <PID>) &

$ sudo python3 scripts/soak_2h.py --seconds 180 --mode deterministic --psi-actions off --stall-threshold-sec 20
/opt/hybrid-trading-bot/scripts/soak_2h.py:154: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
[health] time: 2026-01-09T16:31:20+00:00
[health] db: /opt/hybrid-trading-bot/data/bot.db
[health] port: 8501
[health] ticks: 153961
[health] checking http://127.0.0.1:8501...
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Fri, 09 Jan 2026 16:31:21 GMT
Accept-Ranges: bytes
[health] PASS
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/hybrid-engine.service.d
             └─override.conf
     Active: active (running) since Fri 2026-01-09 16:31:21 UTC; 2s ago
   Main PID: 1827914 (engine-rust)
      Tasks: 8 (limit: 18964)
     Memory: 3.4M (peak: 3.6M)
        CPU: 20ms
     CGroup: /system.slice/hybrid-engine.service
             └─1827914 /opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083641Z","level":"INFO","fields":{"message":"all tasks spawned, pipeline running"},"target":"engine_rust"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083650Z","level":"INFO","fields":{"message":"waiting for shutdown signal (CTRL-C)"},"target":"engine_rust"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083716Z","level":"INFO","fields":{"message":"ingest task started","symbol":"SOL/USDC","interval_ms":500,"sample_every":1,"mode":"SYNTHETIC"},"target":"engine_rust::ingest"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083753Z","level":"INFO","fields":{"message":"strategy task started (deterministic stub)","signal_every_n":10},"target":"engine_rust::strategy"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083764Z","level":"INFO","fields":{"message":"execution task started (shadow adapter, NO NETWORK)","mode":"SHADOW","max_exposure":10000.0,"max_symbol_exposure":5000.0,"max_open_orders":10},"target":"engine_rust::execution"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.083790Z","level":"INFO","fields":{"message":"persist task started (dedicated, non-blocking - I6)","batch_size":100,"flush_interval_ms":1000},"target":"engine_rust::persist"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.085842Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:21 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:21.086113Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":1,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":1,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:31:22 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:22.085455Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:23 slimy-nuc1 engine-rust[1827914]: {"timestamp":"2026-01-09T16:31:23.085859Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}

$ systemctl show -p MainPID --value hybrid-engine.service
1827914

$ kill -STOP 1827914
/opt/hybrid-trading-bot/scripts/soak_2h.py:154: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/hybrid-engine.service.d
             └─override.conf
     Active: active (running) since Fri 2026-01-09 16:31:49 UTC; 2s ago
   Main PID: 1829023 (engine-rust)
      Tasks: 10 (limit: 18964)
     Memory: 3.7M (peak: 4.0M)
        CPU: 17ms
     CGroup: /system.slice/hybrid-engine.service
             └─1829023 /opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074508Z","level":"INFO","fields":{"message":"ingest task started","symbol":"SOL/USDC","interval_ms":500,"sample_every":1,"mode":"SYNTHETIC"},"target":"engine_rust::ingest"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074559Z","level":"INFO","fields":{"message":"strategy task started (deterministic stub)","signal_every_n":10},"target":"engine_rust::strategy"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074585Z","level":"INFO","fields":{"message":"execution task started (shadow adapter, NO NETWORK)","mode":"SHADOW","max_exposure":10000.0,"max_symbol_exposure":5000.0,"max_open_orders":10},"target":"engine_rust::execution"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074628Z","level":"INFO","fields":{"message":"persist task started (dedicated, non-blocking - I6)","batch_size":100,"flush_interval_ms":1000},"target":"engine_rust::persist"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074670Z","level":"INFO","fields":{"message":"all tasks spawned, pipeline running"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074678Z","level":"INFO","fields":{"message":"waiting for shutdown signal (CTRL-C)"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.075956Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.076288Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":1,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":1,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:31:50 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:50.076039Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:51 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:51.075865Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
/opt/hybrid-trading-bot/scripts/soak_2h.py:154: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
[SOAK] STARTUP: Run ID: 9d02287d-d9ba-4bee-8d6b-3941e0295fea, Mode: deterministic
[SOAK] Running healthcheck: /opt/hybrid-trading-bot/scripts/healthcheck.sh
[SOAK] ENGINE_RESTART: Soak Start
[SOAK] STALL: Pipeline stalled
[SOAK] ENGINE_RESTART: Restarting due to STALL
[SOAK] COMPLETE: Soak duration reached
[SOAK] ENGINE_STOP: Stopping service via systemctl

$ tail -n 20 /opt/hybrid-trading-bot/data/ops/soak_decisions.jsonl
{"timestamp": "2026-01-09T15:42:50.571357Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "NORMAL", "current_sample_every": 1, "action": "STARTUP", "reason": "Run ID: 24bef5e0-59f8-4d6f-91d8-60eaeef59b77, Mode: realws"}
{"timestamp": "2026-01-09T15:42:50.663735Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "NORMAL", "current_sample_every": 1, "action": "ENGINE_RESTART", "reason": "Soak Start", "cpu_some_raw": "some avg10=62.33 avg60=59.02 avg300=57.79 total=388424185368", "cpu_some_avg10": 62.33, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2014969539", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:42:57.814290Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE1", "current_sample_every": 5, "action": "ENGINE_RESTART", "reason": "Throttling up to THROTTLE1 due to PSI: CPU 58.8", "cpu_some_raw": "some avg10=58.80 avg60=58.69 avg300=57.76 total=388428096311", "cpu_some_avg10": 58.8, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2014974283", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:04.970893Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE2", "current_sample_every": 10, "action": "ENGINE_RESTART", "reason": "Throttling up to THROTTLE2 due to PSI: CPU 53.94", "cpu_some_raw": "some avg10=53.94 avg60=57.70 avg300=57.56 total=388431841556", "cpu_some_avg10": 53.94, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2014976538", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:12.225091Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "ENGINE_RESTART", "reason": "Throttling up to THROTTLE3 due to PSI: CPU 50.73", "cpu_some_raw": "some avg10=50.73 avg60=56.67 avg300=57.35 total=388435323591", "cpu_some_avg10": 50.73, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2014994441", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:19.454907Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "THROTTLE_MAX", "reason": "Sustained pressure under max throttle: CPU 53.72", "cpu_some_raw": "some avg10=53.72 avg60=56.58 avg300=57.31 total=388439330918", "cpu_some_avg10": 53.72, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2015010611", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:24.540195Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "THROTTLE_MAX", "reason": "Sustained pressure under max throttle: CPU 51.98", "cpu_some_raw": "some avg10=51.98 avg60=56.12 avg300=57.21 total=388441771182", "cpu_some_avg10": 51.98, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2015012917", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:29.608549Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "THROTTLE_MAX", "reason": "Sustained pressure under max throttle: CPU 57.07", "cpu_some_raw": "some avg10=57.07 avg60=56.70 avg300=57.31 total=388445153394", "cpu_some_avg10": 57.07, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2015015722", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:29.608710Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "ABORT", "reason": "Sustained pressure under max throttle", "cpu_some_raw": "some avg10=57.07 avg60=56.70 avg300=57.31 total=388445153394", "cpu_some_avg10": 57.07, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=13272146", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=7698486", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.00 avg300=0.00 total=2015015722", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=431760153", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T15:43:29.608819Z", "run_id": "24bef5e0-59f8-4d6f-91d8-60eaeef59b77", "ingest_mode": "realws", "state": "THROTTLE3", "current_sample_every": 20, "action": "ENGINE_STOP", "reason": "Stopping service via systemctl"}
{"timestamp": "2026-01-09T16:31:20.965426Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "STARTUP", "reason": "Run ID: 9d02287d-d9ba-4bee-8d6b-3941e0295fea, Mode: deterministic"}
{"timestamp": "2026-01-09T16:31:21.014976Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "ENGINE_RESTART", "reason": "Soak Start", "cpu_some_raw": "some avg10=44.36 avg60=50.10 avg300=52.99 total=389867003373", "cpu_some_avg10": 44.36, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.05 avg300=0.11 total=15832595", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.04 avg300=0.06 total=9289105", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.00 avg60=0.01 avg300=0.08 total=2020731163", "io_some_avg10": 0.0, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=432191966", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T16:31:49.019586Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "STALL", "reason": "Pipeline stalled", "ticks_count": 153972, "last_tick_ts": 1767976286, "progress": false, "stall_streak": 1, "seconds_since_progress": 20.24}
{"timestamp": "2026-01-09T16:31:49.020301Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "ENGINE_RESTART", "reason": "Restarting due to STALL", "cpu_some_raw": "some avg10=47.65 avg60=48.78 avg300=52.39 total=389880189520", "cpu_some_avg10": 47.65, "cpu_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=0", "cpu_full_avg10": 0.0, "memory_some_raw": "some avg10=0.00 avg60=0.03 avg300=0.10 total=15833283", "memory_some_avg10": 0.0, "memory_full_raw": "full avg10=0.00 avg60=0.02 avg300=0.05 total=9289128", "memory_full_avg10": 0.0, "io_some_raw": "some avg10=0.08 avg60=0.11 avg300=0.10 total=2020886254", "io_some_avg10": 0.08, "io_full_raw": "full avg10=0.00 avg60=0.00 avg300=0.00 total=432194792", "io_full_avg10": 0.0}
{"timestamp": "2026-01-09T16:34:23.017985Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "COMPLETE", "reason": "Soak duration reached"}
{"timestamp": "2026-01-09T16:34:23.018522Z", "run_id": "9d02287d-d9ba-4bee-8d6b-3941e0295fea", "ingest_mode": "deterministic", "psi_actions": "off", "state": "NORMAL", "current_sample_every": 1, "action": "ENGINE_STOP", "reason": "Stopping service via systemctl"}

$ journalctl -u hybrid-engine.service --since "2026-01-09 16:31:40" --until "2026-01-09 16:32:20" --no-pager
Jan 09 16:31:49 slimy-nuc1 systemd[1]: Stopping hybrid-engine.service - Hybrid Trading Bot Engine...
Jan 09 16:31:49 slimy-nuc1 systemd[1]: hybrid-engine.service: Deactivated successfully.
Jan 09 16:31:49 slimy-nuc1 systemd[1]: Stopped hybrid-engine.service - Hybrid Trading Bot Engine.
Jan 09 16:31:49 slimy-nuc1 systemd[1]: Started hybrid-engine.service - Hybrid Trading Bot Engine.
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.060602Z","level":"INFO","fields":{"message":"engine-rust starting (Phase 2 skeleton)","version":"0.1.0"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.060886Z","level":"INFO","fields":{"message":"configuration loaded (G0: shadow mode default enforced)","mode":"SHADOW","symbol":"SOL/USDC","db_path":"data/bot.db","tick_interval_ms":500,"signal_every_n":10,"heartbeat_secs":10,"run_seconds":"None"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.062964Z","level":"INFO","fields":{"message":"database pool created with WAL mode","db_path":"data/bot.db"},"target":"engine_rust::db"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.064983Z","level":"INFO","fields":{"message":"PRAGMA verification","journal_mode":"wal","synchronous":1,"busy_timeout":5000,"temp_store":2},"target":"engine_rust::db"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.065123Z","level":"INFO","fields":{"message":"all PRAGMAs verified successfully (S1 PASS)"},"target":"engine_rust::db"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.068446Z","level":"INFO","fields":{"message":"schema ensured (ticks, signals, orders, trades tables ready)"},"target":"engine_rust::db"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074355Z","level":"INFO","fields":{"message":"initial database state","ticks":153972,"signals":1164,"orders":1163,"trades":1159},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074413Z","level":"INFO","fields":{"message":"channels created (S6: bounded, backpressure policy: DROP_OLDEST with metrics)","tick_channel":256,"signal_channel":64,"persist_channel":512},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074508Z","level":"INFO","fields":{"message":"ingest task started","symbol":"SOL/USDC","interval_ms":500,"sample_every":1,"mode":"SYNTHETIC"},"target":"engine_rust::ingest"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074559Z","level":"INFO","fields":{"message":"strategy task started (deterministic stub)","signal_every_n":10},"target":"engine_rust::strategy"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074585Z","level":"INFO","fields":{"message":"execution task started (shadow adapter, NO NETWORK)","mode":"SHADOW","max_exposure":10000.0,"max_symbol_exposure":5000.0,"max_open_orders":10},"target":"engine_rust::execution"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074628Z","level":"INFO","fields":{"message":"persist task started (dedicated, non-blocking - I6)","batch_size":100,"flush_interval_ms":1000},"target":"engine_rust::persist"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074670Z","level":"INFO","fields":{"message":"all tasks spawned, pipeline running"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.074678Z","level":"INFO","fields":{"message":"waiting for shutdown signal (CTRL-C)"},"target":"engine_rust"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.075956Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:49 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:49.076288Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":1,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":1,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:31:50 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:50.076039Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:51 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:51.075865Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:52 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:52.078169Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:53 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:53.076093Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:53 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:53.575163Z","level":"INFO","fields":{"message":"signal generated","event_id":"b9b3ece5-d941-40e0-9aa9-406dab4f6c79","symbol":"SOL/USDC","side":"SELL","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":10},"target":"engine_rust::strategy"}
Jan 09 16:31:53 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:53.575222Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"6bff3848-404a-4509-ad3a-777039875d02","signal_id":"b9b3ece5-d941-40e0-9aa9-406dab4f6c79","symbol":"SOL/USDC","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:31:54 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:54.079077Z","level":"INFO","fields":{"message":"batch flushed","persisted":4,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:55 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:55.078395Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:56 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:56.076108Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:57 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:57.075302Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:58 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:58.075837Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:31:58 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:58.575216Z","level":"INFO","fields":{"message":"signal generated","event_id":"dcf045dd-d916-4f8f-a9a7-9a0d0d00de5b","symbol":"SOL/USDC","side":"BUY","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":20},"target":"engine_rust::strategy"}
Jan 09 16:31:58 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:58.575266Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"d486cccf-9316-4bf1-befa-66a9aebaf6a1","signal_id":"dcf045dd-d916-4f8f-a9a7-9a0d0d00de5b","symbol":"SOL/USDC","side":"BUY","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:31:59 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:59.075709Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":20,"signal_count":2,"shadow_orders":2,"trade_count":2,"persist_count":21,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:31:59 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:31:59.080099Z","level":"INFO","fields":{"message":"batch flushed","persisted":5,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:00 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:00.075407Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:01 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:01.075843Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:02 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:02.075466Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:03 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:03.076136Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:03 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:03.575098Z","level":"INFO","fields":{"message":"signal generated","event_id":"1a02d9fd-336d-409f-8c05-4439f2ae4ee5","symbol":"SOL/USDC","side":"SELL","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":30},"target":"engine_rust::strategy"}
Jan 09 16:32:03 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:03.575142Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"0faacf54-1ae4-4c69-994d-71238d50235f","signal_id":"1a02d9fd-336d-409f-8c05-4439f2ae4ee5","symbol":"SOL/USDC","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:32:04 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:04.076846Z","level":"INFO","fields":{"message":"batch flushed","persisted":5,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:05 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:05.076090Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:06 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:06.079688Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:07 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:07.075508Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:08 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:08.078869Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:08 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:08.575277Z","level":"INFO","fields":{"message":"signal generated","event_id":"1638382c-b00c-4d08-ba9b-532cde6aa640","symbol":"SOL/USDC","side":"BUY","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":40},"target":"engine_rust::strategy"}
Jan 09 16:32:08 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:08.575322Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"da3a41a5-fa37-4dbe-9f32-33f528a31a28","signal_id":"1638382c-b00c-4d08-ba9b-532cde6aa640","symbol":"SOL/USDC","side":"BUY","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:32:09 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:09.076340Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":41,"signal_count":4,"shadow_orders":4,"trade_count":4,"persist_count":47,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:32:09 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:09.078833Z","level":"INFO","fields":{"message":"batch flushed","persisted":5,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:10 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:10.075884Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:11 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:11.076755Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:12 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:12.075505Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:13 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:13.079218Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:13 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:13.576838Z","level":"INFO","fields":{"message":"signal generated","event_id":"5fe79e7b-3587-4b51-a436-9e7dc0034d1f","symbol":"SOL/USDC","side":"SELL","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":50},"target":"engine_rust::strategy"}
Jan 09 16:32:13 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:13.576881Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"3641793e-6045-4cdf-b04f-7650655b645d","signal_id":"5fe79e7b-3587-4b51-a436-9e7dc0034d1f","symbol":"SOL/USDC","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:32:14 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:14.077882Z","level":"INFO","fields":{"message":"batch flushed","persisted":5,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:15 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:15.077169Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:16 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:16.075443Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:17 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:17.079385Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:18 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:18.075741Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:32:18 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:18.575044Z","level":"INFO","fields":{"message":"signal generated","event_id":"285f9b69-09ab-49dd-9e4e-f998a3f02316","symbol":"SOL/USDC","side":"BUY","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":60},"target":"engine_rust::strategy"}
Jan 09 16:32:18 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:18.575092Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"33e8795b-23e5-479e-938b-b825a84418c4","signal_id":"285f9b69-09ab-49dd-9e4e-f998a3f02316","symbol":"SOL/USDC","side":"BUY","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:32:19 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:19.077996Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":61,"signal_count":6,"shadow_orders":6,"trade_count":6,"persist_count":73,"persist_errors":0,"ingest_received":0,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:32:19 slimy-nuc1 engine-rust[1829023]: {"timestamp":"2026-01-09T16:32:19.080007Z","level":"INFO","fields":{"message":"batch flushed","persisted":6,"errors":0},"target":"engine_rust::persist"}

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 1

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ cp /opt/hybrid-trading-bot/config/config.toml /opt/hybrid-trading-bot/config/config.toml.bak.20260109163506

$ echo "invalid = [toml" > /opt/hybrid-trading-bot/config/config.toml

$ sudo systemctl restart hybrid-engine.service

$ systemctl status hybrid-engine.service --no-pager
× hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/hybrid-engine.service.d
             └─override.conf
     Active: failed (Result: exit-code) since Fri 2026-01-09 16:35:21 UTC; 5s ago
   Duration: 22ms
    Process: 1837705 ExecStart=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust (code=exited, status=12)
   Main PID: 1837705 (code=exited, status=12)
        CPU: 8ms

Jan 09 16:35:21 slimy-nuc1 systemd[1]: Started hybrid-engine.service - Hybrid Trading Bot Engine.
Jan 09 16:35:21 slimy-nuc1 engine-rust[1837705]: {"timestamp":"2026-01-09T16:35:21.292278Z","level":"INFO","fields":{"message":"engine-rust starting (Phase 2 skeleton)","version":"0.1.0"},"target":"engine_rust"}
Jan 09 16:35:21 slimy-nuc1 engine-rust[1837705]: {"timestamp":"2026-01-09T16:35:21.293083Z","level":"ERROR","fields":{"message":"config TOML parse failed","config_path":"/opt/hybrid-trading-bot/config/config.toml","error":"TOML parse error at line 1, column 12\n  |\n1 | invalid = [toml\n  |            ^\ninvalid string\nexpected `\"`, `'`\n"},"target":"engine_rust"}
Jan 09 16:35:21 slimy-nuc1 systemd[1]: hybrid-engine.service: Main process exited, code=exited, status=12/n/a
Jan 09 16:35:21 slimy-nuc1 systemd[1]: hybrid-engine.service: Failed with result 'exit-code'.

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecMainStatus,NRestarts,ActiveState,SubState
Restart=on-failure
RestartPreventExitStatus=12
NRestarts=0
ExecMainStatus=12
ActiveState=failed
SubState=failed

$ ls -1 /opt/hybrid-trading-bot/config/config.toml.bak.* | tail -n 1
/opt/hybrid-trading-bot/config/config.toml.bak.20260109163506

$ cp /opt/hybrid-trading-bot/config/config.toml.bak.20260109163506 /opt/hybrid-trading-bot/config/config.toml

$ sudo systemctl restart hybrid-engine.service

$ systemctl status hybrid-engine.service --no-pager
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/hybrid-engine.service.d
             └─override.conf
     Active: active (running) since Fri 2026-01-09 16:36:01 UTC; 8s ago
   Main PID: 1839328 (engine-rust)
      Tasks: 8 (limit: 18964)
     Memory: 3.6M (peak: 3.8M)
        CPU: 22ms
     CGroup: /system.slice/hybrid-engine.service
             └─1839328 /opt/hybrid-trading-bot/engine-rust/target/release/engine-rust

Jan 09 16:36:02 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:02.664531Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:03 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:03.663576Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:04 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:04.663434Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:05 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:05.664971Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:06 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:06.164013Z","level":"INFO","fields":{"message":"signal generated","event_id":"2e305756-0cde-4e89-9c43-b9896cb06077","symbol":"SOL/USDC","side":"SELL","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":10},"target":"engine_rust::strategy"}
Jan 09 16:36:06 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:06.164060Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"c917cea0-3255-49f7-9f69-24555423718b","signal_id":"2e305756-0cde-4e89-9c43-b9896cb06077","symbol":"SOL/USDC","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 16:36:06 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:06.665965Z","level":"INFO","fields":{"message":"batch flushed","persisted":4,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:07 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:07.666725Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:08 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:08.665369Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 16:36:09 slimy-nuc1 engine-rust[1839328]: {"timestamp":"2026-01-09T16:36:09.667677Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}

$ sed -n 1,200p /opt/hybrid-trading-bot/config/ws_sources.toml
# WebSocket Sources Configuration
# Priority 1 sources are tried first. If connection fails or drops, next priority is tried.

[[source]]
name = "gemini_btcusd"
url = "wss://api.gemini.com/v1/marketdata/btcusd"
kind = "ticker"
priority = 1

[[source]]
name = "binance_btcusdt"
url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
kind = "ticker"
priority = 99

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
if "ingest_mode" not in content:
    content = content.replace("[engine]\n", "[engine]\ningest_mode = \"REAL_WS\"\n")
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 1", content)
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
ingest_mode = "REAL_WS"
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 1

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ sudo systemctl restart hybrid-engine.service

$ START_TS=2026-01-09T16:38:00+00:00

$ sleep 60

$ journalctl -u hybrid-engine.service --since "2026-01-09T16:38:00+00:00" --no-pager | rg "HEARTBEAT" | tail -n 1
Jan 09 16:38:53 slimy-nuc1 engine-rust[1842935]: {"timestamp":"2026-01-09T16:38:53.635116Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":5,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":5,"persist_errors":0,"ingest_received":5,"ingest_processed":5,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import os, subprocess, json
start_ts = os.environ["START_TS"]
out = subprocess.check_output(["journalctl", "-u", "hybrid-engine.service", "--since", start_ts, "--no-pager"], text=True)
lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
if not lines: raise SystemExit("no heartbeat lines found")
last = lines[-1]
payload = last.rsplit(": ", 1)[-1]
data = json.loads(payload)
fields = data.get("fields", {})
recv = fields.get("ingest_received")
proc = fields.get("ingest_processed")
ratio = (proc / recv) if recv else None
print("heartbeat_line=" + last)
print(f"ingest_received={recv} ingest_processed={proc} ratio={ratio}")
PY
heartbeat_line=Jan 09 16:38:53 slimy-nuc1 engine-rust[1842935]: {"timestamp":"2026-01-09T16:38:53.635116Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":5,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":5,"persist_errors":0,"ingest_received":5,"ingest_processed":5,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
ingest_received=5 ingest_processed=5 ratio=1.0

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 10", content)
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
ingest_mode = "REAL_WS"
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 10

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ sudo systemctl restart hybrid-engine.service

$ START_TS=2026-01-09T16:39:49+00:00

$ sleep 60

$ journalctl -u hybrid-engine.service --since "2026-01-09T16:39:49+00:00" --no-pager | rg "HEARTBEAT" | tail -n 1
Jan 09 16:40:42 slimy-nuc1 engine-rust[1847340]: {"timestamp":"2026-01-09T16:40:42.108708Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":0,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":6,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import os, subprocess, json
start_ts = os.environ["START_TS"]
out = subprocess.check_output(["journalctl", "-u", "hybrid-engine.service", "--since", start_ts, "--no-pager"], text=True)
lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
if not lines: raise SystemExit("no heartbeat lines found")
last = lines[-1]
payload = last.rsplit(": ", 1)[-1]
data = json.loads(payload)
fields = data.get("fields", {})
recv = fields.get("ingest_received")
proc = fields.get("ingest_processed")
ratio = (proc / recv) if recv else None
print("heartbeat_line=" + last)
print(f"ingest_received={recv} ingest_processed={proc} ratio={ratio}")
PY
heartbeat_line=Jan 09 16:40:42 slimy-nuc1 engine-rust[1847340]: {"timestamp":"2026-01-09T16:40:42.108708Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":0,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":6,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
ingest_received=6 ingest_processed=0 ratio=0.0

$ journalctl -u hybrid-engine.service --since "2026-01-09 16:39:30" --until "2026-01-09 16:40:10" --no-pager | rg "connecting|connected"
Jan 09 16:39:32 slimy-nuc1 engine-rust[1847340]: {"timestamp":"2026-01-09T16:39:32.107900Z","level":"INFO","fields":{"message":"connecting...","source":"gemini_btcusd","url":"wss://api.gemini.com/v1/marketdata/btcusd","sample_every":10},"target":"engine_rust::ingest::realws"}
Jan 09 16:39:32 slimy-nuc1 engine-rust[1847340]: {"timestamp":"2026-01-09T16:39:32.386334Z","level":"INFO","fields":{"message":"connected","source":"gemini_btcusd"},"target":"engine_rust::ingest::realws"}

$ cp /opt/hybrid-trading-bot/config/ws_sources.toml /opt/hybrid-trading-bot/config/ws_sources.toml.bak.20260109164130

$ python3 - <<"PY"
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/ws_sources.toml")
content = path.read_text()
content = content.replace("priority = 1", "priority = 99", 1)
content = content.replace("priority = 99", "priority = 1", 1)
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/ws_sources.toml
# WebSocket Sources Configuration
# Priority 1 sources are tried first. If connection fails or drops, next priority is tried.

[[source]]
name = "gemini_btcusd"
url = "wss://api.gemini.com/v1/marketdata/btcusd"
kind = "ticker"
priority = 1

[[source]]
name = "binance_btcusdt"
url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
kind = "ticker"
priority = 99

$ python3 - <<"PY"
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/ws_sources.toml")
content = path.read_text()
content = content.replace("priority = 1", "priority = __TMP__")
content = content.replace("priority = 99", "priority = 1")
content = content.replace("priority = __TMP__", "priority = 99")
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/ws_sources.toml
# WebSocket Sources Configuration
# Priority 1 sources are tried first. If connection fails or drops, next priority is tried.

[[source]]
name = "gemini_btcusd"
url = "wss://api.gemini.com/v1/marketdata/btcusd"
kind = "ticker"
priority = 99

[[source]]
name = "binance_btcusdt"
url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
kind = "ticker"
priority = 1

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 1", content)
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
ingest_mode = "REAL_WS"
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 1

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ sudo systemctl restart hybrid-engine.service

$ journalctl -u hybrid-engine.service --since "-30s" --no-pager | rg "connecting|connected"
Jan 09 16:42:41 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:41.565575Z","level":"INFO","fields":{"message":"connecting...","source":"binance_btcusdt","url":"wss://stream.binance.com:9443/ws/btcusdt@trade","sample_every":1},"target":"engine_rust::ingest::realws"}
Jan 09 16:42:42 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:42.291084Z","level":"WARN","fields":{"message":"source disconnected or failed, switching...","source":"binance_btcusdt"},"target":"engine_rust::ingest::realws"}
Jan 09 16:42:42 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:42.291100Z","level":"INFO","fields":{"message":"connecting...","source":"gemini_btcusd","url":"wss://api.gemini.com/v1/marketdata/btcusd","sample_every":1},"target":"engine_rust::ingest::realws"}
Jan 09 16:42:42 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:42.640161Z","level":"INFO","fields":{"message":"connected","source":"gemini_btcusd"},"target":"engine_rust::ingest::realws"}

$ journalctl -u hybrid-engine.service --since "-2m" --no-pager | rg "ws error|connection failed|disconnected"
Jan 09 16:42:42 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:42.291031Z","level":"WARN","fields":{"message":"connection failed","source":"binance_btcusdt","error":"HTTP error: 451 Unavailable For Legal Reasons"},"target":"engine_rust::ingest::realws"}
Jan 09 16:42:42 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:42:42.291084Z","level":"WARN","fields":{"message":"source disconnected or failed, switching...","source":"binance_btcusdt"},"target":"engine_rust::ingest::realws"}

$ journalctl -u hybrid-engine.service --since "-2m" --no-pager | rg "HEARTBEAT" | tail -n 5
Jan 09 16:43:11 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:43:11.567780Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":5,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":5,"persist_errors":0,"ingest_received":5,"ingest_processed":5,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:43:21 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:43:21.567653Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":11,"signal_count":1,"shadow_orders":1,"trade_count":1,"persist_count":14,"persist_errors":0,"ingest_received":11,"ingest_processed":11,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:43:31 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:43:31.566798Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":12,"signal_count":1,"shadow_orders":1,"trade_count":1,"persist_count":15,"persist_errors":0,"ingest_received":12,"ingest_processed":12,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:43:41 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:43:41.567745Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":12,"signal_count":1,"shadow_orders":1,"trade_count":1,"persist_count":15,"persist_errors":0,"ingest_received":12,"ingest_processed":12,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 16:43:51 slimy-nuc1 engine-rust[1854559]: {"timestamp":"2026-01-09T16:43:51.567646Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":13,"signal_count":1,"shadow_orders":1,"trade_count":1,"persist_count":16,"persist_errors":0,"ingest_received":13,"ingest_processed":13,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 10", content)
path.write_text(content)
PY

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
ingest_mode = "REAL_WS"
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 10

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ sudo systemctl restart hybrid-engine.service

$ START_TS=2026-01-09T16:44:50+00:00

$ sleep 60

$ journalctl -u hybrid-engine.service --since "2026-01-09T16:44:50+00:00" --no-pager | rg "HEARTBEAT" | tail -n 1
Jan 09 16:45:43 slimy-nuc1 engine-rust[1858880]: {"timestamp":"2026-01-09T16:45:43.847544Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":0,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":4,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import os, subprocess, json
start_ts = os.environ["START_TS"]
out = subprocess.check_output(["journalctl", "-u", "hybrid-engine.service", "--since", start_ts, "--no-pager"], text=True)
lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
if not lines: raise SystemExit("no heartbeat lines found")
last = lines[-1]
payload = last.rsplit(": ", 1)[-1]
data = json.loads(payload)
fields = data.get("fields", {})
recv = fields.get("ingest_received")
proc = fields.get("ingest_processed")
ratio = (proc / recv) if recv else None
print("heartbeat_line=" + last)
print(f"ingest_received={recv} ingest_processed={proc} ratio={ratio}")
PY
heartbeat_line=Jan 09 16:45:43 slimy-nuc1 engine-rust[1858880]: {"timestamp":"2026-01-09T16:45:43.847544Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":0,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":4,"ingest_processed":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
ingest_received=4 ingest_processed=0 ratio=0.0

$ ls -1 /opt/hybrid-trading-bot/config/ws_sources.toml.bak.* | tail -n 1
/opt/hybrid-trading-bot/config/ws_sources.toml.bak.20260109164130

$ cp /opt/hybrid-trading-bot/config/ws_sources.toml.bak.20260109164130 /opt/hybrid-trading-bot/config/ws_sources.toml

$ sed -n 1,200p /opt/hybrid-trading-bot/config/ws_sources.toml
# WebSocket Sources Configuration
# Priority 1 sources are tried first. If connection fails or drops, next priority is tried.

[[source]]
name = "gemini_btcusd"
url = "wss://api.gemini.com/v1/marketdata/btcusd"
kind = "ticker"
priority = 1

[[source]]
name = "binance_btcusdt"
url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
kind = "ticker"
priority = 99

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 1", content)
path.write_text(content)
PY

$ sudo systemctl restart hybrid-engine.service

$ START_TS=2026-01-09T16:47:18+00:00

$ sleep 180

$ journalctl -u hybrid-engine.service --since "2026-01-09T16:47:18+00:00" --no-pager | rg "HEARTBEAT" | tail -n 1
Jan 09 16:50:12 slimy-nuc1 engine-rust[1864346]: {"timestamp":"2026-01-09T16:50:12.370096Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":28,"signal_count":2,"shadow_orders":2,"trade_count":2,"persist_count":34,"persist_errors":0,"ingest_received":28,"ingest_processed":28,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import os, subprocess, json
start_ts = os.environ["START_TS"]
out = subprocess.check_output(["journalctl", "-u", "hybrid-engine.service", "--since", start_ts, "--no-pager"], text=True)
lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
if not lines: raise SystemExit("no heartbeat lines found")
last = lines[-1]
payload = last.rsplit(": ", 1)[-1]
data = json.loads(payload)
fields = data.get("fields", {})
recv = fields.get("ingest_received")
proc = fields.get("ingest_processed")
ratio = (proc / recv) if recv else None
print("heartbeat_line=" + last)
print(f"ingest_received={recv} ingest_processed={proc} ratio={ratio}")
PY
heartbeat_line=Jan 09 16:50:12 slimy-nuc1 engine-rust[1864346]: {"timestamp":"2026-01-09T16:50:12.370096Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":28,"signal_count":2,"shadow_orders":2,"trade_count":2,"persist_count":34,"persist_errors":0,"ingest_received":28,"ingest_processed":28,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
ingest_received=28 ingest_processed=28 ratio=1.0

$ python3 - <<"PY"
import re
from pathlib import Path
path = Path("/opt/hybrid-trading-bot/config/config.toml")
content = path.read_text()
content = re.sub(r"sample_every\s*=\s*\d+", "sample_every = 10", content)
path.write_text(content)
PY

$ sudo systemctl restart hybrid-engine.service

$ START_TS=2026-01-09T16:51:05+00:00

$ sleep 180

$ journalctl -u hybrid-engine.service --since "2026-01-09T16:51:05+00:00" --no-pager | rg "HEARTBEAT" | tail -n 1
Jan 09 16:53:57 slimy-nuc1 engine-rust[1872913]: {"timestamp":"2026-01-09T16:53:57.170108Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":1,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":10,"ingest_processed":1,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}

$ python3 - <<"PY"
import os, subprocess, json
start_ts = os.environ["START_TS"]
out = subprocess.check_output(["journalctl", "-u", "hybrid-engine.service", "--since", start_ts, "--no-pager"], text=True)
lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
if not lines: raise SystemExit("no heartbeat lines found")
last = lines[-1]
payload = last.rsplit(": ", 1)[-1]
data = json.loads(payload)
fields = data.get("fields", {})
recv = fields.get("ingest_received")
proc = fields.get("ingest_processed")
ratio = (proc / recv) if recv else None
print("heartbeat_line=" + last)
print(f"ingest_received={recv} ingest_processed={proc} ratio={ratio}")
PY
heartbeat_line=Jan 09 16:53:57 slimy-nuc1 engine-rust[1872913]: {"timestamp":"2026-01-09T16:53:57.170108Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":1,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"ingest_received":10,"ingest_processed":1,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
ingest_received=10 ingest_processed=1 ratio=0.1

$ cp /opt/hybrid-trading-bot/config/config.toml.bak.20260109163506 /opt/hybrid-trading-bot/config/config.toml

$ sudo systemctl restart hybrid-engine.service

$ sed -n 1,200p /opt/hybrid-trading-bot/config/config.toml
[app]
symbol = "SOL/USDC"
db_path = "data/bot.db"

[engine]
tick_interval_ms = 500
start_price = 100.0
price_step = 0.05
volume = 1.0
sample_every = 1

[dashboard]
host = "127.0.0.1"
port = 8501
refresh_seconds = 1

$ git status -sb
## main...origin/main [ahead 11]
 M data/ops/soak_decisions.jsonl
 M engine-rust/src/ingest/realws.rs
 M engine-rust/src/main.rs
 M engine-rust/src/types.rs
 M scripts/soak_2h.py
?? config/config.toml.bak.20260109163506
?? config/ws_sources.toml.bak.20260109164130
?? docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md
?? scripts/diagnose_cpu_pressure.sh

$ rm -f /opt/hybrid-trading-bot/config/config.toml.bak.20260109163506 /opt/hybrid-trading-bot/config/ws_sources.toml.bak.20260109164130

$ git restore data/ops/soak_decisions.jsonl

$ git status -sb
## main...origin/main [ahead 11]
 M engine-rust/src/ingest/realws.rs
 M engine-rust/src/main.rs
 M engine-rust/src/types.rs
 M scripts/soak_2h.py
?? docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md
?? scripts/diagnose_cpu_pressure.sh

$ git add -p engine-rust/src/main.rs
diff --git a/engine-rust/src/main.rs b/engine-rust/src/main.rs
index 1e61699..84809c5 100644
--- a/engine-rust/src/main.rs
+++ b/engine-rust/src/main.rs
@@ -23,7 +23,7 @@ use std::sync::atomic::Ordering;
 use std::sync::Arc;
 use tokio::sync::{broadcast, mpsc};
 use tokio::time::{interval, Duration};
-use tracing::{info, warn};
+use tracing::{error, info, warn};
 
 use config::{Config, ExecutionMode};
 use types::Metrics;
(1/5) Stage this hunk [y,n,q,a,d,j,J,g,/,e,?]? @@ -90,7 +90,20 @@ async fn main() -> Result<()> {
 
     // Load configuration
     let mut config = if std::path::Path::new(&args.config).exists() {
-        Config::load(&args.config)?
+        match Config::load(&args.config) {
+            Ok(config) => config,
+            Err(err) => {
+                if is_toml_parse_error(&err) {
+                    error!(
+                        config_path = %args.config,
+                        error = %err,
+                        "config TOML parse failed"
+                    );
+                    std::process::exit(EXIT_CONFIG);
+                }
+                return Err(err);
+            }
+        }
     } else {
         info!(
             config_path = %args.config,
(2/5) Stage this hunk [y,n,q,a,d,K,j,J,g,/,e,?]? @@ -259,6 +272,8 @@ async fn main() -> Result<()> {
                 trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                 persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                 persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
+                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
+                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                 bp_drops_tick = metrics_heartbeat
                     .backpressure_drops_tick
                     .load(Ordering::Relaxed),
(3/5) Stage this hunk [y,n,q,a,d,K,j,J,g,/,e,?]? @@ -318,6 +333,8 @@ async fn main() -> Result<()> {
         trade_count = metrics.trade_count.load(Ordering::Relaxed),
         persist_count = metrics.persist_count.load(Ordering::Relaxed),
         persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
+        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
+        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
         bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
         bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
         risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
(4/5) Stage this hunk [y,n,q,a,d,K,j,J,g,/,e,?]? @@ -327,3 +344,30 @@ async fn main() -> Result<()> {
     info!("engine-rust shutdown complete");
     Ok(())
 }
+
+fn is_toml_parse_error(err: &anyhow::Error) -> bool {
+    err.downcast_ref::<toml::de::Error>().is_some()
+}
+
+#[cfg(test)]
+mod tests {
+    use super::is_toml_parse_error;
+    use crate::config::Config;
+    use std::fs;
+    use std::time::{SystemTime, UNIX_EPOCH};
+
+    #[test]
+    fn invalid_toml_is_classified_as_config_error() {
+        let mut path = std::env::temp_dir();
+        let unique = SystemTime::now()
+            .duration_since(UNIX_EPOCH)
+            .expect("time ok")
+            .as_nanos();
+        path.push(format!("engine_config_invalid_{unique}.toml"));
+
+        fs::write(&path, "invalid = [toml").expect("write invalid toml");
+        let err = Config::load(path.to_str().expect("path utf-8")).unwrap_err();
+        assert!(is_toml_parse_error(&err));
+        let _ = fs::remove_file(&path);
+    }
+}
(5/5) Stage this hunk [y,n,q,a,d,K,g,/,e,?]? 

$ git diff --cached
diff --git a/engine-rust/src/main.rs b/engine-rust/src/main.rs
index 1e61699..ab9a2d0 100644
--- a/engine-rust/src/main.rs
+++ b/engine-rust/src/main.rs
@@ -23,7 +23,7 @@ use std::sync::atomic::Ordering;
 use std::sync::Arc;
 use tokio::sync::{broadcast, mpsc};
 use tokio::time::{interval, Duration};
-use tracing::{info, warn};
+use tracing::{error, info, warn};
 
 use config::{Config, ExecutionMode};
 use types::Metrics;
@@ -90,7 +90,20 @@ async fn main() -> Result<()> {
 
     // Load configuration
     let mut config = if std::path::Path::new(&args.config).exists() {
-        Config::load(&args.config)?
+        match Config::load(&args.config) {
+            Ok(config) => config,
+            Err(err) => {
+                if is_toml_parse_error(&err) {
+                    error!(
+                        config_path = %args.config,
+                        error = %err,
+                        "config TOML parse failed"
+                    );
+                    std::process::exit(EXIT_CONFIG);
+                }
+                return Err(err);
+            }
+        }
     } else {
         info!(
             config_path = %args.config,
@@ -327,3 +340,30 @@ async fn main() -> Result<()> {
     info!("engine-rust shutdown complete");
     Ok(())
 }
+
+fn is_toml_parse_error(err: &anyhow::Error) -> bool {
+    err.downcast_ref::<toml::de::Error>().is_some()
+}
+
+#[cfg(test)]
+mod tests {
+    use super::is_toml_parse_error;
+    use crate::config::Config;
+    use std::fs;
+    use std::time::{SystemTime, UNIX_EPOCH};
+
+    #[test]
+    fn invalid_toml_is_classified_as_config_error() {
+        let mut path = std::env::temp_dir();
+        let unique = SystemTime::now()
+            .duration_since(UNIX_EPOCH)
+            .expect("time ok")
+            .as_nanos();
+        path.push(format!("engine_config_invalid_{unique}.toml"));
+
+        fs::write(&path, "invalid = [toml").expect("write invalid toml");
+        let err = Config::load(path.to_str().expect("path utf-8")).unwrap_err();
+        assert!(is_toml_parse_error(&err));
+        let _ = fs::remove_file(&path);
+    }
+}

$ git commit -m engine(exitcodes): map TOML parse errors to CONFIG=12 + tests
[main 97a3413] engine(exitcodes): map TOML parse errors to CONFIG=12 + tests
 1 file changed, 42 insertions(+), 2 deletions(-)

$ git add -p engine-rust/src/main.rs
diff --git a/engine-rust/src/main.rs b/engine-rust/src/main.rs
index ab9a2d0..84809c5 100644
--- a/engine-rust/src/main.rs
+++ b/engine-rust/src/main.rs
@@ -272,6 +272,8 @@ async fn main() -> Result<()> {
                 trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                 persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                 persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
+                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
+                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                 bp_drops_tick = metrics_heartbeat
                     .backpressure_drops_tick
                     .load(Ordering::Relaxed),
(1/2) Stage this hunk [y,n,q,a,d,j,J,g,/,e,?]? @@ -331,6 +333,8 @@ async fn main() -> Result<()> {
         trade_count = metrics.trade_count.load(Ordering::Relaxed),
         persist_count = metrics.persist_count.load(Ordering::Relaxed),
         persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
+        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
+        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
         bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
         bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
         risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
(2/2) Stage this hunk [y,n,q,a,d,K,g,/,e,?]? 

$ git add engine-rust/src/types.rs engine-rust/src/ingest/realws.rs scripts/soak_2h.py scripts/diagnose_cpu_pressure.sh

$ git diff --cached
diff --git a/engine-rust/src/ingest/realws.rs b/engine-rust/src/ingest/realws.rs
index ad94722..d3afef6 100644
--- a/engine-rust/src/ingest/realws.rs
+++ b/engine-rust/src/ingest/realws.rs
@@ -116,9 +116,15 @@ async fn run_source_session(
                                     // Gemini
                                     if let Ok(ticks) = parse_gemini_update(&text, symbol) {
                                         for tick in ticks {
+                                            metrics
+                                                .ingest_received
+                                                .fetch_add(1, Ordering::Relaxed);
                                             sequence += 1;
                                             if sequence % sample_every == 0 {
                                                 crate::ingest::send_tick(tick, tick_tx, persist_tx, metrics).await;
+                                                metrics
+                                                    .ingest_processed
+                                                    .fetch_add(1, Ordering::Relaxed);
                                                 metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                             }
                                         }
@@ -126,9 +132,15 @@ async fn run_source_session(
                                 } else if text.contains("\"e\":\"trade\"") || text.contains("\"e\":\"aggTrade\"") {
                                     // Binance
                                     if let Ok(tick) = parse_binance_trade(&text, symbol) {
+                                        metrics
+                                            .ingest_received
+                                            .fetch_add(1, Ordering::Relaxed);
                                         sequence += 1;
                                         if sequence % sample_every == 0 {
                                             crate::ingest::send_tick(tick, tick_tx, persist_tx, metrics).await;
+                                            metrics
+                                                .ingest_processed
+                                                .fetch_add(1, Ordering::Relaxed);
                                             metrics.tick_count.fetch_add(1, Ordering::Relaxed);
                                         }
                                     }
diff --git a/engine-rust/src/main.rs b/engine-rust/src/main.rs
index ab9a2d0..84809c5 100644
--- a/engine-rust/src/main.rs
+++ b/engine-rust/src/main.rs
@@ -272,6 +272,8 @@ async fn main() -> Result<()> {
                 trade_count = metrics_heartbeat.trade_count.load(Ordering::Relaxed),
                 persist_count = metrics_heartbeat.persist_count.load(Ordering::Relaxed),
                 persist_errors = metrics_heartbeat.persist_errors.load(Ordering::Relaxed),
+                ingest_received = metrics_heartbeat.ingest_received.load(Ordering::Relaxed),
+                ingest_processed = metrics_heartbeat.ingest_processed.load(Ordering::Relaxed),
                 bp_drops_tick = metrics_heartbeat
                     .backpressure_drops_tick
                     .load(Ordering::Relaxed),
@@ -331,6 +333,8 @@ async fn main() -> Result<()> {
         trade_count = metrics.trade_count.load(Ordering::Relaxed),
         persist_count = metrics.persist_count.load(Ordering::Relaxed),
         persist_errors = metrics.persist_errors.load(Ordering::Relaxed),
+        ingest_received = metrics.ingest_received.load(Ordering::Relaxed),
+        ingest_processed = metrics.ingest_processed.load(Ordering::Relaxed),
         bp_drops_tick = metrics.backpressure_drops_tick.load(Ordering::Relaxed),
         bp_drops_signal = metrics.backpressure_drops_signal.load(Ordering::Relaxed),
         risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
diff --git a/engine-rust/src/types.rs b/engine-rust/src/types.rs
index 9cea294..b48864f 100644
--- a/engine-rust/src/types.rs
+++ b/engine-rust/src/types.rs
@@ -180,6 +180,8 @@ pub struct Metrics {
     pub trade_count: std::sync::atomic::AtomicU64,
     pub persist_count: std::sync::atomic::AtomicU64,
     pub persist_errors: std::sync::atomic::AtomicU64,
+    pub ingest_received: std::sync::atomic::AtomicU64,
+    pub ingest_processed: std::sync::atomic::AtomicU64,
     pub backpressure_drops_tick: std::sync::atomic::AtomicU64,
     pub backpressure_drops_signal: std::sync::atomic::AtomicU64,
     pub backpressure_drops_persist: std::sync::atomic::AtomicU64,
diff --git a/scripts/diagnose_cpu_pressure.sh b/scripts/diagnose_cpu_pressure.sh
new file mode 100755
index 0000000..a7d1f5b
--- /dev/null
+++ b/scripts/diagnose_cpu_pressure.sh
@@ -0,0 +1,60 @@
+#!/usr/bin/env bash
+set -euo pipefail
+cd /opt/hybrid-trading-bot
+
+echo "--- 1. Timestamp ---"
+date -Is
+echo ""
+
+echo "--- 2. Host/Kernel ---"
+hostname
+uname -a
+echo ""
+
+echo "--- 3. Uptime ---"
+uptime
+echo ""
+
+echo "--- 4. PSI Snapshot (/proc/pressure/*) ---"
+for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
+  echo "== $f =="
+  cat "$f"
+  echo ""
+done
+
+echo "--- 5. Load Average ---"
+cat /proc/loadavg
+echo ""
+
+echo "--- 6. Memory Summary ---"
+free -h
+echo ""
+
+echo "--- 7. Disk Usage ---"
+df -h
+echo ""
+
+echo "--- 8. Top CPU (10 samples over 10s) ---"
+if command -v pidstat >/dev/null 2>&1; then
+  pidstat -u 1 10 | tail -n +1
+else
+  echo "pidstat not installed (sudo apt-get install sysstat)"
+  ps -eo pid,ppid,comm,%cpu,%mem --sort=-%cpu | head -25
+fi
+echo ""
+
+echo "--- 9. systemd cgroup CPU snapshot ---"
+if command -v systemd-cgtop >/dev/null 2>&1; then
+  systemd-cgtop -n 1 --cpu=1 --depth=3 || true
+else
+  echo "systemd-cgtop not available"
+fi
+echo ""
+
+echo "--- 10. Disk I/O Wait ---"
+if command -v iostat >/dev/null 2>&1; then
+  iostat -x 1 2 | tail -n +4
+else
+  echo "iostat not installed (sudo apt-get install sysstat)"
+fi
+echo ""
diff --git a/scripts/soak_2h.py b/scripts/soak_2h.py
index 12b873b..dd0a9a9 100755
--- a/scripts/soak_2h.py
+++ b/scripts/soak_2h.py
@@ -139,7 +139,8 @@ class SoakController:
         self.start_time = time.time()
         self.total_seconds = args.seconds
         self.ingest_mode = args.mode
-        self.stall_detector = StallDetector(args.db, stall_threshold_sec=45) # 45s stall threshold
+        self.psi_actions = args.psi_actions
+        self.stall_detector = StallDetector(args.db, stall_threshold_sec=args.stall_threshold_sec)
         
         # Ensure log dir exists
         os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True)
@@ -153,6 +154,7 @@ class SoakController:
             "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
             "run_id": self.run_id,
             "ingest_mode": self.ingest_mode,
+            "psi_actions": self.psi_actions,
             "state": self.current_state,
             "current_sample_every": self.get_current_sample_rate(),
             "action": action,
@@ -295,35 +297,44 @@ class SoakController:
                     print(f"[WARN] Failed to check service status: {e}")
 
                 # 4. PSI Monitor & Throttle
-                psi = get_psi()
-                cpu = psi.get("cpu_some_avg10", 0.0)
-                mem = psi.get("memory_some_avg10", 0.0)
-                io = psi.get("io_some_avg10", 0.0)
-
-                pressure_reason = []
-                if cpu > CPU_LIMIT: pressure_reason.append(f"CPU {cpu}")
-                if mem > MEM_LIMIT: pressure_reason.append(f"MEM {mem}")
-                if io > IO_LIMIT: pressure_reason.append(f"IO {io}")
-
-                if pressure_reason:
-                    self.consecutive_pressure += 1
-                    next_s, next_val = self.next_throttle_state(self.current_state)
-                    
-                    if next_s != self.current_state:
-                         self.current_state = next_s
-                         self.update_config_sample_rate(next_val)
-                         self.restart_engine(f"Throttling up to {next_s} due to PSI: {', '.join(pressure_reason)}")
+                if self.psi_actions != "off":
+                    psi = get_psi()
+                    cpu = psi.get("cpu_some_avg10", 0.0)
+                    mem = psi.get("memory_some_avg10", 0.0)
+                    io = psi.get("io_some_avg10", 0.0)
+
+                    pressure_reason = []
+                    if cpu > CPU_LIMIT: pressure_reason.append(f"CPU {cpu}")
+                    if mem > MEM_LIMIT: pressure_reason.append(f"MEM {mem}")
+                    if io > IO_LIMIT: pressure_reason.append(f"IO {io}")
+
+                    if pressure_reason:
+                        if self.psi_actions == "logonly":
+                            self.log_decision(
+                                "PSI_LOGONLY",
+                                f"PSI pressure observed (logonly): {', '.join(pressure_reason)}",
+                                psi,
+                            )
+                            self.consecutive_pressure = 0
+                        else:
+                            self.consecutive_pressure += 1
+                            next_s, next_val = self.next_throttle_state(self.current_state)
+                            
+                            if next_s != self.current_state:
+                                 self.current_state = next_s
+                                 self.update_config_sample_rate(next_val)
+                                 self.restart_engine(f"Throttling up to {next_s} due to PSI: {', '.join(pressure_reason)}")
+                            else:
+                                 # Already max throttle
+                                 self.log_decision("THROTTLE_MAX", f"Sustained pressure under max throttle: {', '.join(pressure_reason)}", psi)
+                                 if self.consecutive_pressure > 5:
+                                     self.log_decision("ABORT", "Sustained pressure under max throttle", psi)
+                                     break
                     else:
-                         # Already max throttle
-                         self.log_decision("THROTTLE_MAX", f"Sustained pressure under max throttle: {', '.join(pressure_reason)}", psi)
-                         if self.consecutive_pressure > 5:
-                             self.log_decision("ABORT", "Sustained pressure under max throttle", psi)
-                             break
-                else:
-                    self.consecutive_pressure = 0
-                    # Logic to allow recover? For safety in this phase, we generally latch up or hold. 
-                    # If we want to recover, we'd step down. For now, strict fail-safe or hold is fine.
-                    pass
+                        self.consecutive_pressure = 0
+                        # Logic to allow recover? For safety in this phase, we generally latch up or hold. 
+                        # If we want to recover, we'd step down. For now, strict fail-safe or hold is fine.
+                        pass
 
                 # 5. Stall Detection
                 is_stalled, stall_data = self.stall_detector.check()
@@ -347,6 +358,18 @@ if __name__ == "__main__":
     parser.add_argument("--seconds", type=int, default=7200, help="Soak duration seconds")
     parser.add_argument("--mode", type=str, default="realws", help="Initial ingest mode")
     parser.add_argument("--db", type=str, default="/opt/hybrid-trading-bot/data/bot.db")
+    parser.add_argument(
+        "--psi-actions",
+        choices=["on", "logonly", "off"],
+        default="on",
+        help="PSI actions: on=throttle/restart, logonly=record PSI only, off=skip PSI",
+    )
+    parser.add_argument(
+        "--stall-threshold-sec",
+        type=int,
+        default=45,
+        help="Seconds without tick progress before STALL triggers",
+    )
     args = parser.parse_args()
 
     controller = SoakController(args)

$ git commit -m soak(proofs): add psi-actions flag + rerun proofs 2/3/5 with evidence
[main 1151fff] soak(proofs): add psi-actions flag + rerun proofs 2/3/5 with evidence
 5 files changed, 130 insertions(+), 29 deletions(-)
 create mode 100755 scripts/diagnose_cpu_pressure.sh

$ git status -sb
## main...origin/main [ahead 13]
?? docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git add docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git commit -m docs(buglog): Phase 2.2.3 proof closure evidence
[main 9942e55] docs(buglog): Phase 2.2.3 proof closure evidence
 1 file changed, 3498 insertions(+)
 create mode 100644 docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git status -sb
## main...origin/main [ahead 14]
 M docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ systemctl show hybrid-engine.service -p Restart,RestartPreventExitStatus,ExecStart
Restart=on-failure
RestartPreventExitStatus=12
ExecStart={ path=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; argv[]=/opt/hybrid-trading-bot/engine-rust/target/release/engine-rust ; ignore_errors=no ; start_time=[Fri 2026-01-09 16:54:44 UTC] ; stop_time=[n/a] ; pid=1881587 ; code=(null) ; status=0/0 }

$ git log -5 --oneline
9942e55 docs(buglog): Phase 2.2.3 proof closure evidence
1151fff soak(proofs): add psi-actions flag + rerun proofs 2/3/5 with evidence
97a3413 engine(exitcodes): map TOML parse errors to CONFIG=12 + tests
20a33b1 hardening(systemd): prevent restart on exit 12
b6c49f3 complete(phase2.2.2): systemd hardening + 5 proofs with evidence

$ git add docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git commit --amend --no-edit
[main af4b96a] docs(buglog): Phase 2.2.3 proof closure evidence
 Date: Fri Jan 9 16:58:21 2026 +0000
 1 file changed, 3521 insertions(+)
 create mode 100644 docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git status -sb
## main...origin/main [ahead 14]
 M docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git add docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git commit --amend --no-edit
[main ac1927c] docs(buglog): Phase 2.2.3 proof closure evidence
 Date: Fri Jan 9 16:58:21 2026 +0000
 1 file changed, 3533 insertions(+)
 create mode 100644 docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git status -sb
## main...origin/main [ahead 14]
 M docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md

$ git add docs/buglog/BUG_2026-01-09_phase2_2_3_proof_closure.md
(no output)

$ git commit --amend --no-edit --quiet
(no output)
