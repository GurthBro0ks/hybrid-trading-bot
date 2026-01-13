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
    Replay, // From DB (ticks table)
    MockWs, // WebSocket (ws://localhost...)
    RealWs, // Real WebSocket ingestion (Option A)
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
    #[serde(default)]
    pub replay_file: Option<String>,
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
            replay_file: None,
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_mode_is_shadow() {
        let config = Config::default();
        assert_eq!(config.mode, ExecutionMode::Shadow);
    }

    #[test]
    fn test_live_mode_fails_without_armed() {
        let config = Config {
            mode: ExecutionMode::Live,
            live_armed: false,
            ..Default::default()
        };
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_shadow_mode_validates() {
        let config = Config::default();
        assert!(config.validate().is_ok());
    }

    #[test]
    fn test_default_risk_caps() {
        let caps = RiskCaps::default();
        assert_eq!(caps.max_exposure_usd, 10_000.0);
        assert_eq!(caps.max_symbol_exposure_usd, 5_000.0);
        assert_eq!(caps.max_open_orders, 10);
    }
}
