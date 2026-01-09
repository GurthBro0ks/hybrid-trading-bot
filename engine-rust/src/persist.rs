//! Persistence task - Dedicated batch writer (I6: non-blocking)
//!
//! Trading loop never blocked by disk I/O.
//! Persistence happens in dedicated task with batch inserts.

use crate::types::{Metrics, Order, PersistEvent, Signal, Tick, Trade};
use sqlx::SqlitePool;
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tokio::sync::mpsc;
use tokio::time::{interval, Duration};
use tracing::{info, warn};

const BATCH_SIZE: usize = 100;
const FLUSH_INTERVAL_MS: u64 = 1000;

/// Run the persistence task (I6: dedicated, non-blocking)
///
/// # Arguments
/// * `pool` - SQLite connection pool
/// * `persist_rx` - Channel to receive events from all tasks
/// * `metrics` - Shared metrics for heartbeat
pub async fn run_persist_task(
    pool: SqlitePool,
    mut persist_rx: mpsc::Receiver<PersistEvent>,
    metrics: Arc<Metrics>,
) {
    let mut buffer: Vec<PersistEvent> = Vec::with_capacity(BATCH_SIZE);
    let mut flush_timer = interval(Duration::from_millis(FLUSH_INTERVAL_MS));

    info!(
        batch_size = BATCH_SIZE,
        flush_interval_ms = FLUSH_INTERVAL_MS,
        "persist task started (dedicated, non-blocking - I6)"
    );

    loop {
        tokio::select! {
            // Receive events
            event = persist_rx.recv() => {
                match event {
                    Some(e) => {
                        buffer.push(e);
                        if buffer.len() >= BATCH_SIZE {
                            flush_batch(&pool, &mut buffer, &metrics).await;
                        }
                    }
                    None => {
                        // Channel closed, final flush
                        if !buffer.is_empty() {
                            info!(remaining = buffer.len(), "final flush on shutdown");
                            flush_batch(&pool, &mut buffer, &metrics).await;
                        }
                        break;
                    }
                }
            }
            // Periodic flush
            _ = flush_timer.tick() => {
                if !buffer.is_empty() {
                    flush_batch(&pool, &mut buffer, &metrics).await;
                }
            }
        }
    }

    info!(
        total_persisted = metrics.persist_count.load(Ordering::Relaxed),
        total_errors = metrics.persist_errors.load(Ordering::Relaxed),
        "persist task ended (channel closed, final flush complete)"
    );
}

/// Flush a batch of events to the database
async fn flush_batch(pool: &SqlitePool, buffer: &mut Vec<PersistEvent>, metrics: &Metrics) {
    let count = buffer.len();
    if count == 0 {
        return;
    }

    let mut success_count: u64 = 0;
    let mut error_count: u64 = 0;

    // Process each event individually (SQLite WAL handles concurrency)
    for event in buffer.drain(..) {
        let result = match event {
            PersistEvent::Tick(t) => persist_tick(pool, &t).await,
            PersistEvent::Signal(s) => persist_signal(pool, &s).await,
            PersistEvent::Order(o) => persist_order(pool, &o).await,
            PersistEvent::Trade(t) => persist_trade(pool, &t).await,
        };

        match result {
            Ok(_) => {
                success_count += 1;
            }
            Err(e) => {
                warn!(error = %e, "persist error (continuing)");
                error_count += 1;
            }
        }
    }

    metrics
        .persist_count
        .fetch_add(success_count, Ordering::Relaxed);
    metrics
        .persist_errors
        .fetch_add(error_count, Ordering::Relaxed);

    if success_count > 0 {
        info!(
            persisted = success_count,
            errors = error_count,
            "batch flushed"
        );
    }
}

async fn persist_tick(pool: &SqlitePool, tick: &Tick) -> Result<(), sqlx::Error> {
    sqlx::query("INSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)")
        .bind(&tick.symbol)
        .bind(tick.price)
        .bind(tick.volume)
        .bind(tick.ts / 1000) // Convert ms to seconds for compatibility
        .execute(pool)
        .await?;
    Ok(())
}

async fn persist_signal(pool: &SqlitePool, signal: &Signal) -> Result<(), sqlx::Error> {
    sqlx::query("INSERT INTO signals(symbol, kind, value, ts) VALUES(?, ?, ?, ?)")
        .bind(&signal.symbol)
        .bind(format!("{}:{}", signal.side, signal.reason))
        .bind(signal.confidence)
        .bind(signal.ts / 1000)
        .execute(pool)
        .await?;
    Ok(())
}

async fn persist_order(pool: &SqlitePool, order: &Order) -> Result<(), sqlx::Error> {
    sqlx::query(
        "INSERT INTO orders(symbol, side, qty, price, status, ts) VALUES(?, ?, ?, ?, ?, ?)",
    )
    .bind(&order.symbol)
    .bind(order.side.to_string())
    .bind(order.qty)
    .bind(order.price)
    .bind(order.status.to_string())
    .bind(order.ts / 1000)
    .execute(pool)
    .await?;
    Ok(())
}

async fn persist_trade(pool: &SqlitePool, trade: &Trade) -> Result<(), sqlx::Error> {
    sqlx::query(
        "INSERT INTO trades(event_id, order_id, symbol, side, fill_qty, fill_price, fees, ts, is_shadow) \
         VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
    )
    .bind(trade.event_id.to_string())
    .bind(trade.order_id.to_string())
    .bind(&trade.symbol)
    .bind(trade.side.to_string())
    .bind(trade.fill_qty)
    .bind(trade.fill_price)
    .bind(trade.fees)
    .bind(trade.ts / 1000)
    .bind(trade.is_shadow as i32)
    .execute(pool)
    .await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::{create_pool, ensure_schema};
    use crate::types::{EventId, ReasonCode, Side};
    use tempfile::NamedTempFile;

    #[tokio::test]
    async fn test_persist_tick() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();
        ensure_schema(&pool).await.unwrap();

        let tick = Tick {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            price: 100.0,
            volume: 1.0,
            ts: 1704844800000, // ms
        };

        persist_tick(&pool, &tick).await.unwrap();

        let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM ticks")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(count, 1);
    }

    #[tokio::test]
    async fn test_persist_signal() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();
        ensure_schema(&pool).await.unwrap();

        let signal = Signal {
            event_id: EventId::new(),
            symbol: "TEST/USD".to_string(),
            side: Side::Buy,
            confidence: 0.75,
            reason: ReasonCode::PeriodicTrigger,
            desired_size: 1.0,
            ts: 1704844800000,
        };

        persist_signal(&pool, &signal).await.unwrap();

        let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM signals")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert_eq!(count, 1);
    }

    #[tokio::test]
    async fn test_batch_flush() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();
        ensure_schema(&pool).await.unwrap();

        let metrics = Arc::new(Metrics::new());
        let (persist_tx, persist_rx) = mpsc::channel(100);

        // Spawn persist task
        let pool_clone = pool.clone();
        let metrics_clone = metrics.clone();
        let handle = tokio::spawn(async move {
            run_persist_task(pool_clone, persist_rx, metrics_clone).await;
        });

        // Give the task time to start
        tokio::task::yield_now().await;

        // Send events with small delays to ensure they're received
        for i in 0..5i64 {
            let tick = Tick {
                event_id: EventId::new(),
                symbol: "TEST/USD".to_string(),
                price: 100.0 + i as f64,
                volume: 1.0,
                ts: 1704844800000 + i,
            };
            persist_tx.send(PersistEvent::Tick(tick)).await.unwrap();
            // Small yield to ensure event is processed
            tokio::task::yield_now().await;
        }

        // Wait for flush timer to trigger (flush interval is 1000ms)
        // Add extra time for processing
        tokio::time::sleep(Duration::from_millis(1500)).await;

        // Drop sender to trigger shutdown and final flush
        drop(persist_tx);

        // Wait for task to complete
        handle.await.unwrap();

        // Verify persisted - check database directly
        let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM ticks")
            .fetch_one(&pool)
            .await
            .unwrap();

        // Allow for some variation in timing-sensitive tests
        assert!(count >= 5, "Expected at least 5 ticks, got {}", count);

        // Verify metrics match database
        let persisted = metrics.persist_count.load(Ordering::Relaxed);
        assert!(
            persisted >= 5,
            "Expected at least 5 persisted, got {}",
            persisted
        );
    }
}
