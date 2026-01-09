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

    #[test]
    fn test_side_display() {
        assert_eq!(format!("{}", Side::Buy), "BUY");
        assert_eq!(format!("{}", Side::Sell), "SELL");
    }
}
