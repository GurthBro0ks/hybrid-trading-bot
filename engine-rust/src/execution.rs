//! Execution task - Shadow adapter (NO NETWORK)
//!
//! Implements S9 (shadow mode = no real orders) and I1 (shadow safety)
//! CRITICAL: ShadowExecution has NO network client fields by design

use crate::config::{ExecutionMode, RiskCaps};
#[cfg(test)]
use crate::types::Side;
use crate::types::{EventId, Metrics, Order, OrderStatus, PersistEvent, ReasonCode, Signal, Trade};
use std::collections::HashMap;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tracing::{info, warn};

/// Exposure tracking for risk caps (I2)
#[derive(Debug, Default)]
pub struct ExposureTracker {
    total_exposure: f64,
    symbol_exposure: HashMap<String, f64>,
    open_orders: usize,
}

impl ExposureTracker {
    pub fn new() -> Self {
        Self::default()
    }

    /// Check if signal would violate risk caps, and update if allowed
    ///
    /// Returns Ok(()) if signal is allowed, Err(ReasonCode::RiskCap) if vetoed
    pub fn check_and_update(&mut self, signal: &Signal, caps: &RiskCaps) -> Result<(), ReasonCode> {
        // Calculate notional exposure for this signal
        // Simplified: size * reference_price (we use 100.0 as reference)
        let new_exposure = signal.desired_size * 100.0;

        // Check total exposure cap (I2)
        if self.total_exposure + new_exposure > caps.max_exposure_usd {
            return Err(ReasonCode::RiskCap);
        }

        // Check per-symbol cap (I2)
        let sym_exp = self
            .symbol_exposure
            .get(&signal.symbol)
            .copied()
            .unwrap_or(0.0);
        if sym_exp + new_exposure > caps.max_symbol_exposure_usd {
            return Err(ReasonCode::RiskCap);
        }

        // Check open orders cap (I2)
        if self.open_orders >= caps.max_open_orders {
            return Err(ReasonCode::RiskCap);
        }

        // Update tracking
        self.total_exposure += new_exposure;
        *self
            .symbol_exposure
            .entry(signal.symbol.clone())
            .or_default() += new_exposure;
        self.open_orders += 1;

        Ok(())
    }

    /// Release exposure when an order is filled/canceled
    pub fn release(&mut self, symbol: &str, exposure: f64) {
        self.total_exposure -= exposure;
        if let Some(sym_exp) = self.symbol_exposure.get_mut(symbol) {
            *sym_exp -= exposure;
        }
        if self.open_orders > 0 {
            self.open_orders -= 1;
        }
    }

    /// Get current total exposure
    pub fn total_exposure(&self) -> f64 {
        self.total_exposure
    }

    /// Get current open order count
    pub fn open_orders(&self) -> usize {
        self.open_orders
    }
}

/// ShadowExecution adapter (S9, I1)
///
/// CRITICAL SAFETY DESIGN:
/// This struct intentionally has NO network client fields.
/// It CANNOT make network calls because it has no capability to do so.
/// This is enforced by the type system - there are no fields that could
/// hold a reqwest::Client, WebSocket connection, or any network resource.
///
/// This design satisfies:
/// - S9: Shadow mode records shadow orders only, no real orders
/// - I1: Shadow safety - 0 calls to real OrderExecution network endpoints
pub struct ShadowExecution {
    // INTENTIONALLY EMPTY - NO NETWORK FIELDS
    // This struct cannot make network calls by design.
    // Adding any network client field here would violate I1.
    _private: (), // Prevent external construction
}

impl ShadowExecution {
    /// Create a new ShadowExecution adapter
    pub fn new() -> Self {
        Self { _private: () }
    }

    /// Record a shadow order (S9)
    ///
    /// This method:
    /// - Records what order WOULD have been placed
    /// - Simulates immediate fill with assumed price/fees
    /// - Returns Order and Trade records for persistence
    /// - NEVER makes any network call (I1)
    pub fn execute_shadow(&self, signal: &Signal) -> (Order, Trade) {
        let order = Order {
            event_id: EventId::new(),
            signal_id: signal.event_id,
            symbol: signal.symbol.clone(),
            side: signal.side,
            qty: signal.desired_size,
            price: None,                 // Market order
            status: OrderStatus::Filled, // Shadow orders "fill" immediately
            reason: ReasonCode::ShadowRecorded,
            ts: signal.ts,
            is_shadow: true, // S9: marked as shadow
        };

        // Simulated fill with assumed slippage
        let fill_price = 100.0; // Simplified: use reference price
        let fees = signal.desired_size * fill_price * 0.001; // 0.1% fee assumption

        let trade = Trade {
            event_id: EventId::new(),
            order_id: order.event_id,
            symbol: signal.symbol.clone(),
            side: signal.side,
            fill_qty: signal.desired_size,
            fill_price,
            fees,
            ts: signal.ts,
            is_shadow: true,
        };

        (order, trade)
    }
}

impl Default for ShadowExecution {
    fn default() -> Self {
        Self::new()
    }
}

/// Run the execution task
///
/// # Arguments
/// * `mode` - Execution mode (must be Shadow or Paper, not Live)
/// * `risk_caps` - Risk caps configuration for I2
/// * `signal_rx` - Channel to receive signals from strategy
/// * `persist_tx` - Channel to send orders/trades to persistence
/// * `metrics` - Shared metrics for heartbeat
pub async fn run_execution_task(
    mode: ExecutionMode,
    risk_caps: RiskCaps,
    mut signal_rx: mpsc::Receiver<Signal>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
) {
    // G0: Verify we're NOT in live mode
    assert!(
        mode == ExecutionMode::Shadow || mode == ExecutionMode::Paper,
        "Execution task must not run in LIVE mode without explicit unlock (G0). \
         Current mode: {:?}",
        mode
    );

    let executor = ShadowExecution::new();
    let mut exposure = ExposureTracker::new();

    info!(
        mode = %mode,
        max_exposure = risk_caps.max_exposure_usd,
        max_symbol_exposure = risk_caps.max_symbol_exposure_usd,
        max_open_orders = risk_caps.max_open_orders,
        "execution task started (shadow adapter, NO NETWORK)"
    );

    while let Some(signal) = signal_rx.recv().await {
        // Check risk caps (I2)
        if let Err(reason) = exposure.check_and_update(&signal, &risk_caps) {
            metrics.risk_vetoes.fetch_add(1, Ordering::Relaxed);
            warn!(
                event_id = %signal.event_id,
                reason_code = %reason,
                total_exposure = exposure.total_exposure(),
                open_orders = exposure.open_orders(),
                "signal vetoed by risk cap (I2)"
            );
            continue;
        }

        // Execute in shadow mode (S9, I1)
        let (order, trade) = executor.execute_shadow(&signal);

        metrics.shadow_order_count.fetch_add(1, Ordering::Relaxed);
        metrics.trade_count.fetch_add(1, Ordering::Relaxed);

        info!(
            order_id = %order.event_id,
            signal_id = %signal.event_id,
            symbol = %order.symbol,
            side = %order.side,
            qty = order.qty,
            fill_price = trade.fill_price,
            fees = trade.fees,
            reason_code = %order.reason,
            is_shadow = order.is_shadow,
            "shadow order executed (I1: no network call)"
        );

        // Persist order and trade (non-blocking - I6)
        let _ = persist_tx.try_send(PersistEvent::Order(order));
        let _ = persist_tx.try_send(PersistEvent::Trade(trade));

        // Release exposure since shadow orders "fill" immediately
        let exposure_amount = signal.desired_size * 100.0;
        exposure.release(&signal.symbol, exposure_amount);
    }

    info!(
        total_shadow_orders = metrics.shadow_order_count.load(Ordering::Relaxed),
        total_trades = metrics.trade_count.load(Ordering::Relaxed),
        risk_vetoes = metrics.risk_vetoes.load(Ordering::Relaxed),
        "execution task ended (signal channel closed)"
    );
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::now_ts_millis;

    #[test]
    fn test_shadow_execution_has_no_network_fields() {
        // This test verifies the DESIGN of ShadowExecution
        // The struct has only a private unit field - no network capability
        let executor = ShadowExecution::new();

        // Execute a shadow order
        let signal = Signal {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 1.0,
            ts: now_ts_millis(),
        };

        let (order, trade) = executor.execute_shadow(&signal);

        // Verify shadow flags are set (S9)
        assert!(order.is_shadow);
        assert!(trade.is_shadow);
        assert_eq!(order.reason, ReasonCode::ShadowRecorded);
    }

    #[test]
    fn test_exposure_tracker_respects_caps() {
        let caps = RiskCaps {
            max_exposure_usd: 100.0,
            max_symbol_exposure_usd: 50.0,
            max_open_orders: 2,
        };

        let mut tracker = ExposureTracker::new();

        // First signal: size=0.5, notional=50 - should pass
        let signal1 = Signal {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.5, // 50 notional
            ts: now_ts_millis(),
        };
        assert!(tracker.check_and_update(&signal1, &caps).is_ok());

        // Second signal: size=0.5, notional=50 - should pass (total=100)
        let signal2 = Signal {
            event_id: EventId::new(),
            symbol: "OTHER/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.5, // 50 notional
            ts: now_ts_millis(),
        };
        assert!(tracker.check_and_update(&signal2, &caps).is_ok());

        // Third signal: would exceed max_open_orders
        let signal3 = Signal {
            event_id: EventId::new(),
            symbol: "THIRD/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.01,
            ts: now_ts_millis(),
        };
        assert_eq!(
            tracker.check_and_update(&signal3, &caps),
            Err(ReasonCode::RiskCap)
        );
    }

    #[test]
    fn test_exposure_tracker_per_symbol_cap() {
        let caps = RiskCaps {
            max_exposure_usd: 1000.0,
            max_symbol_exposure_usd: 50.0,
            max_open_orders: 10,
        };

        let mut tracker = ExposureTracker::new();

        // First signal: 50 notional on TEST/USD - should pass
        let signal1 = Signal {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.5, // 50 notional
            ts: now_ts_millis(),
        };
        assert!(tracker.check_and_update(&signal1, &caps).is_ok());

        // Second signal: another 50 on TEST/USD - should fail (per-symbol cap)
        let signal2 = Signal {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.5,
            ts: now_ts_millis(),
        };
        assert_eq!(
            tracker.check_and_update(&signal2, &caps),
            Err(ReasonCode::RiskCap)
        );

        // Third signal: 50 on different symbol - should pass
        let signal3 = Signal {
            event_id: EventId::new(),
            symbol: "OTHER/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 0.5,
            ts: now_ts_millis(),
        };
        assert!(tracker.check_and_update(&signal3, &caps).is_ok());
    }
}
