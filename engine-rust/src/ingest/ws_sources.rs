use anyhow::Result;
use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct WsSourceConfig {
    pub name: String,
    pub url: String,
    pub kind: String, // "ticker", etc.
    pub priority: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct WsSourcesConfig {
    pub source: Vec<WsSourceConfig>,
}

impl WsSourcesConfig {
    pub fn load(path: &str) -> Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: WsSourcesConfig = toml::from_str(&content)?;
        Ok(config)
    }
}
