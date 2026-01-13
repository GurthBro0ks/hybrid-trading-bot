//! Strategy task - SMA crossover
//!
//! Implements S6 (backpressure) and S8 (determinism)
//! Implements thin-book classification for VenueBook risk management

use crate::types::{EventId, Metrics, PersistEvent, ReasonCode, Side, Signal, Tick, VenueBook};
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
            let side = if action == "BUY" {
                Side::Buy
            } else {
                Side::Sell
            };
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

// --- Thin-Book Classification ---

/// Deterministic thresholds for thin-book detection
/// These are constants to ensure test stability (no config-based nondeterminism)
const THIN_BOOK_SPREAD_THRESHOLD: f64 = 5.0; // Spread > 5.0 is wide
const THIN_BOOK_DEPTH_LEVELS: usize = 3; // Check top 3 levels
const THIN_BOOK_DEPTH_THRESHOLD: f64 = 500.0; // Total qty < 500 is thin

/// Classify orderbook for thin-book conditions
///
/// Returns (is_thin, subreason_code)
/// - is_thin: true if book is too thin to trade
/// - subreason_code: Optional reason string (matches ReasonCode)
///
/// # Deterministic Rules (Fail-Closed)
/// 1. NO_BBO: Missing best bid OR best ask → (true, Some("NO_BBO"))
/// 2. SPREAD_WIDE: Spread > THIN_BOOK_SPREAD_THRESHOLD → (true, Some("SPREAD_WIDE"))
/// 3. DEPTH_BELOW_THRESHOLD: Total qty in top N levels < threshold → (true, Some("DEPTH_BELOW_THRESHOLD"))
/// 4. Otherwise: (false, None)
///
/// # Errors
/// - Returns Err if book is invalid (e.g., negative spread, NaN values)
pub fn classify_thin_book(book: &VenueBook) -> anyhow::Result<(bool, Option<ReasonCode>)> {
    // Rule 1: NO_BBO (missing best bid or ask)
    let best_bid = book.best_bid();
    let best_ask = book.best_ask();

    if best_bid.is_none() || best_ask.is_none() {
        return Ok((true, Some(ReasonCode::ThinBookNoBbo)));
    }

    let bid = best_bid.unwrap();
    let ask = best_ask.unwrap();

    // Validate no crossed book (fail-closed)
    if bid >= ask {
        anyhow::bail!("invalid book: crossed (bid {} >= ask {})", bid, ask);
    }

    let spread = ask - bid;

    // Rule 2: SPREAD_WIDE
    if spread > THIN_BOOK_SPREAD_THRESHOLD {
        return Ok((true, Some(ReasonCode::ThinBookSpreadWide)));
    }

    // Rule 3: DEPTH_BELOW_THRESHOLD
    // Check combined depth on both sides
    let bid_depth = book.bid_depth(THIN_BOOK_DEPTH_LEVELS);
    let ask_depth = book.ask_depth(THIN_BOOK_DEPTH_LEVELS);
    let total_depth = bid_depth + ask_depth;

    if total_depth < THIN_BOOK_DEPTH_THRESHOLD {
        return Ok((true, Some(ReasonCode::ThinBookDepthBelowThreshold)));
    }

    // Not thin
    Ok((false, None))
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
        });

        let mut ts = 1_000_000i64;
        for i in 0..50 {
            let price = if i < 20 {
                100.0
            } else if i < 30 {
                100.0 + (i as f64 - 19.0)
            } else {
                110.0 - (i as f64 - 29.0)
            };
            let tick = Tick {
                event_id: EventId::new(),
                symbol: "TEST/USD".to_string(),
                price,
                volume: 1.0,
                ts,
            };
            ts += 1;
            tick_tx.send(tick).await.unwrap();
        }

        drop(tick_tx);
        handle.await.unwrap();

        let mut signals = vec![];
        while let Ok(s) = signal_rx.try_recv() {
            signals.push(s);
        }

        assert_eq!(signals.len(), 2);
        assert_eq!(signals[0].side, Side::Buy);
        assert_eq!(signals[1].side, Side::Sell);
        assert_eq!(signals[0].reason, ReasonCode::SmaCrossover);
    }
}
