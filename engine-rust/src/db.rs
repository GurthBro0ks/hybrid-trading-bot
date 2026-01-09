//! Database module for SQLite with WAL mode
//!
//! Implements S1 (PRAGMA verification), I5 (storage performance), G3 (PRAGMA evidence)

use anyhow::{bail, Context, Result};
use sqlx::sqlite::{SqliteConnectOptions, SqlitePoolOptions};
use sqlx::{Row, SqlitePool};
use std::str::FromStr;
use tracing::info;

/// Required PRAGMA values (I5)
#[derive(Debug, Clone)]
pub struct PragmaRequirements {
    pub journal_mode: String, // "wal"
    pub synchronous: i64,     // 1 (NORMAL)
    pub busy_timeout: i64,    // >= 1000
    pub temp_store: i64,      // 2 (MEMORY)
}

impl Default for PragmaRequirements {
    fn default() -> Self {
        Self {
            journal_mode: "wal".to_string(),
            synchronous: 1,     // NORMAL
            busy_timeout: 5000, // 5 seconds
            temp_store: 2,      // MEMORY
        }
    }
}

/// Create SQLite connection pool with PRAGMAs applied (S1)
pub async fn create_pool(db_path: &str) -> Result<SqlitePool> {
    let db_url = format!("sqlite://{}?mode=rwc", db_path);

    let options = SqliteConnectOptions::from_str(&db_url)?
        .journal_mode(sqlx::sqlite::SqliteJournalMode::Wal)
        .synchronous(sqlx::sqlite::SqliteSynchronous::Normal)
        .busy_timeout(std::time::Duration::from_millis(5000))
        .pragma("temp_store", "MEMORY");

    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .connect_with(options)
        .await
        .context("Failed to create database pool")?;

    info!(db_path = %db_path, "database pool created with WAL mode");

    Ok(pool)
}

/// Verify PRAGMAs match requirements (S1, G3)
pub async fn verify_pragmas(pool: &SqlitePool, req: &PragmaRequirements) -> Result<()> {
    // Query current PRAGMA values
    let journal: String = sqlx::query_scalar("PRAGMA journal_mode;")
        .fetch_one(pool)
        .await
        .context("Failed to query journal_mode")?;

    let sync: i64 = sqlx::query("PRAGMA synchronous;")
        .fetch_one(pool)
        .await
        .context("Failed to query synchronous")?
        .get(0);

    let timeout: i64 = sqlx::query("PRAGMA busy_timeout;")
        .fetch_one(pool)
        .await
        .context("Failed to query busy_timeout")?
        .get(0);

    let temp: i64 = sqlx::query("PRAGMA temp_store;")
        .fetch_one(pool)
        .await
        .context("Failed to query temp_store")?
        .get(0);

    // Log for G3/G4 evidence
    info!(
        journal_mode = %journal,
        synchronous = sync,
        busy_timeout = timeout,
        temp_store = temp,
        "PRAGMA verification"
    );

    // Verify values (S1)
    if journal.to_lowercase() != req.journal_mode {
        bail!(
            "PRAGMA journal_mode mismatch: got '{}', expected '{}'",
            journal,
            req.journal_mode
        );
    }

    if sync != req.synchronous {
        bail!(
            "PRAGMA synchronous mismatch: got {}, expected {}",
            sync,
            req.synchronous
        );
    }

    if timeout < req.busy_timeout {
        bail!(
            "PRAGMA busy_timeout too low: got {}, minimum {}",
            timeout,
            req.busy_timeout
        );
    }

    if temp != req.temp_store {
        bail!(
            "PRAGMA temp_store mismatch: got {}, expected {}",
            temp,
            req.temp_store
        );
    }

    info!("all PRAGMAs verified successfully (S1 PASS)");
    Ok(())
}

/// Ensure schema exists - creates tables if missing
pub async fn ensure_schema(pool: &SqlitePool) -> Result<()> {
    // Create ticks table
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS ticks (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            volume REAL NOT NULL,
            ts INTEGER NOT NULL
        );
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query("CREATE INDEX IF NOT EXISTS idx_ticks_ts ON ticks(ts);")
        .execute(pool)
        .await?;

    // Create signals table
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            kind TEXT NOT NULL,
            value REAL NOT NULL,
            ts INTEGER NOT NULL
        );
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query("CREATE INDEX IF NOT EXISTS idx_signals_ts ON signals(ts);")
        .execute(pool)
        .await?;

    // Create orders table
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL,
            status TEXT NOT NULL,
            ts INTEGER NOT NULL
        );
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query("CREATE INDEX IF NOT EXISTS idx_orders_ts ON orders(ts);")
        .execute(pool)
        .await?;

    // Create trades table (new for Phase 2)
    sqlx::query(
        r#"
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            event_id TEXT NOT NULL UNIQUE,
            order_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            fill_qty REAL NOT NULL,
            fill_price REAL NOT NULL,
            fees REAL NOT NULL,
            ts INTEGER NOT NULL,
            is_shadow INTEGER NOT NULL DEFAULT 1
        );
        "#,
    )
    .execute(pool)
    .await?;

    sqlx::query("CREATE INDEX IF NOT EXISTS idx_trades_ts ON trades(ts);")
        .execute(pool)
        .await?;

    sqlx::query("CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades(order_id);")
        .execute(pool)
        .await?;

    info!("schema ensured (ticks, signals, orders, trades tables ready)");
    Ok(())
}

/// Get current row counts for verification
pub async fn get_row_counts(pool: &SqlitePool) -> Result<(i64, i64, i64, i64)> {
    let ticks: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM ticks")
        .fetch_one(pool)
        .await?;
    let signals: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM signals")
        .fetch_one(pool)
        .await?;
    let orders: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM orders")
        .fetch_one(pool)
        .await?;
    let trades: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM trades")
        .fetch_one(pool)
        .await?;

    Ok((ticks, signals, orders, trades))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    #[tokio::test]
    async fn test_pragma_verification_passes() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();
        let req = PragmaRequirements::default();

        // Should pass with default requirements
        verify_pragmas(&pool, &req).await.unwrap();
    }

    #[tokio::test]
    async fn test_pragma_values_correct() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();

        // Query actual values
        let journal: String = sqlx::query_scalar("PRAGMA journal_mode;")
            .fetch_one(&pool)
            .await
            .unwrap();
        let sync: i64 = sqlx::query("PRAGMA synchronous;")
            .fetch_one(&pool)
            .await
            .unwrap()
            .get(0);
        let timeout: i64 = sqlx::query("PRAGMA busy_timeout;")
            .fetch_one(&pool)
            .await
            .unwrap()
            .get(0);
        let temp: i64 = sqlx::query("PRAGMA temp_store;")
            .fetch_one(&pool)
            .await
            .unwrap()
            .get(0);

        // Assert exact values (S1)
        assert_eq!(journal.to_lowercase(), "wal");
        assert_eq!(sync, 1); // NORMAL
        assert!(timeout >= 1000);
        assert_eq!(temp, 2); // MEMORY
    }

    #[tokio::test]
    async fn test_schema_creation() {
        let tmp = NamedTempFile::new().unwrap();
        let db_path = tmp.path().to_str().unwrap();

        let pool = create_pool(db_path).await.unwrap();
        ensure_schema(&pool).await.unwrap();

        // Verify tables exist
        let (ticks, signals, orders, trades) = get_row_counts(&pool).await.unwrap();
        assert_eq!(ticks, 0);
        assert_eq!(signals, 0);
        assert_eq!(orders, 0);
        assert_eq!(trades, 0);
    }
}
