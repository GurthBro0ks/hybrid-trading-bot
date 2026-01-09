//! Ingestion task - Deterministic tick generator
//!
//! For Phase 2, generates deterministic ticks locally (no external WS yet)
//! Implements S6 (backpressure) via try_send with counter

use crate::types::{EventId, Metrics, PersistEvent, Tick};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::time::{interval, Duration};
use tracing::{info, warn};

/// Run the ingestion task with deterministic tick generation
///
/// # Arguments
/// * `symbol` - Trading symbol (e.g., "SOL/USDC")
/// * `tick_interval_ms` - Interval between ticks in milliseconds
/// * `tick_tx` - Channel to send ticks to strategy
/// * `persist_tx` - Channel to send ticks to persistence
/// * `metrics` - Shared metrics for heartbeat
/// * `shutdown` - Shutdown signal receiver
pub async fn run_ingest_task(
    symbol: String,
    tick_interval_ms: u64,
    tick_tx: mpsc::Sender<Tick>,
    persist_tx: mpsc::Sender<PersistEvent>,
    metrics: Arc<Metrics>,
    mut shutdown: tokio::sync::broadcast::Receiver<()>,
) {
    let mut timer = interval(Duration::from_millis(tick_interval_ms));
    let mut price = 100.0; // Start price
    let price_step = 0.05; // Deterministic drift

    info!(
        symbol = %symbol,
        interval_ms = tick_interval_ms,
        start_price = price,
        "ingest task started (deterministic generator)"
    );

    loop {
        tokio::select! {
            _ = timer.tick() => {
                // Deterministic price movement - oscillating drift
                let count = metrics.tick_count.fetch_add(1, Ordering::Relaxed);

                // Oscillating pattern: up, down, up, up, down...
                let direction = match count % 5 {
                    0 | 2 | 3 => 1.0,
                    _ => -0.5,
                };
                price += price_step * direction;

                // Ensure price stays positive
                if price < 1.0 {
                    price = 1.0;
                }

                let tick = Tick {
                    event_id: EventId::new(),
                    symbol: symbol.clone(),
                    price,
                    volume: 1.0,
                    ts: crate::types::now_ts_millis(),
                };

                // Send to strategy (with backpressure tracking - S6)
                if tick_tx.try_send(tick.clone()).is_err() {
                    metrics.backpressure_drops_tick.fetch_add(1, Ordering::Relaxed);
                    warn!(
                        reason_code = "BP_DROP_TICK",
                        channel = "tick",
                        "backpressure: dropped tick (channel full)"
                    );
                }

                // Send to persist (non-blocking - I6)
                if persist_tx.try_send(PersistEvent::Tick(tick)).is_err() {
                    metrics.backpressure_drops_persist.fetch_add(1, Ordering::Relaxed);
                    // Don't warn for every persist drop, it's expected under load
                }
            }
            _ = shutdown.recv() => {
                info!("ingest task received shutdown signal");
                break;
            }
        }
    }

    info!(
        total_ticks = metrics.tick_count.load(Ordering::Relaxed),
        "ingest task ended"
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_tick_generation() {
        let metrics = Arc::new(Metrics::new());
        let (tick_tx, mut tick_rx) = mpsc::channel(10);
        let (persist_tx, _persist_rx) = mpsc::channel(10);
        let (shutdown_tx, shutdown_rx) = tokio::sync::broadcast::channel(1);

        // Spawn ingest task
        let metrics_clone = metrics.clone();
        let handle = tokio::spawn(async move {
            run_ingest_task(
                "TEST/USD".to_string(),
                10, // Fast for testing
                tick_tx,
                persist_tx,
                metrics_clone,
                shutdown_rx,
            )
            .await;
        });

        // Wait for some ticks
        tokio::time::sleep(Duration::from_millis(50)).await;

        // Should have received ticks
        let tick = tick_rx.try_recv();
        assert!(tick.is_ok());

        // Shutdown
        shutdown_tx.send(()).unwrap();
        handle.await.unwrap();
    }

    #[tokio::test]
    async fn test_deterministic_price_movement() {
        // Test that price movement is deterministic
        let mut price = 100.0;
        let price_step = 0.05;

        for count in 0..10u64 {
            let direction = match count % 5 {
                0 | 2 | 3 => 1.0,
                _ => -0.5,
            };
            price += price_step * direction;
        }

        // After 10 iterations: +1, -0.5, +1, +1, -0.5, +1, -0.5, +1, +1, -0.5
        // = +1 -0.5 +1 +1 -0.5 = +2.0 for first 5
        // = +1 -0.5 +1 +1 -0.5 = +2.0 for second 5
        // Total = 100 + 4*0.05 = 100.20... approximately
        assert!(price > 100.0 && price < 101.0);
    }
}
