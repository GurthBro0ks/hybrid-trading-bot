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
