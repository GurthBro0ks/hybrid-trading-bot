//! Unit tests for S1: DB PRAGMAs verified at startup
//!
//! These tests verify that SQLite PRAGMAs are correctly applied and verified.

use engine_rust::db::{
    create_pool, ensure_schema, get_row_counts, verify_pragmas, PragmaRequirements,
};
use sqlx::Row;
use tempfile::NamedTempFile;

/// S1: Test that PRAGMA verification passes with correct settings
#[tokio::test]
async fn test_pragma_verification_passes() {
    let tmp = NamedTempFile::new().unwrap();
    let db_path = tmp.path().to_str().unwrap();

    let pool = create_pool(db_path).await.unwrap();
    let req = PragmaRequirements::default();

    // Should pass with default requirements
    let result = verify_pragmas(&pool, &req).await;
    assert!(
        result.is_ok(),
        "PRAGMA verification should pass: {:?}",
        result
    );
}

/// S1: Test that PRAGMA values are exactly as expected
#[tokio::test]
async fn test_pragma_values_are_correct() {
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

    // Assert exact values (S1, I5)
    assert_eq!(
        journal.to_lowercase(),
        "wal",
        "journal_mode should be WAL for concurrent access"
    );
    assert_eq!(sync, 1, "synchronous should be NORMAL (1)");
    assert!(
        timeout >= 1000,
        "busy_timeout should be at least 1000ms, got {}",
        timeout
    );
    assert_eq!(temp, 2, "temp_store should be MEMORY (2)");
}

/// S1: Test that PRAGMA verification fails with incorrect settings
#[tokio::test]
async fn test_pragma_verification_fails_on_mismatch() {
    let tmp = NamedTempFile::new().unwrap();
    let db_path = tmp.path().to_str().unwrap();

    let pool = create_pool(db_path).await.unwrap();

    // Create requirements with impossible busy_timeout
    let req = PragmaRequirements {
        journal_mode: "wal".to_string(),
        synchronous: 1,
        busy_timeout: 999999999, // Impossibly high
        temp_store: 2,
    };

    // Should fail because actual timeout is lower
    let result = verify_pragmas(&pool, &req).await;
    assert!(
        result.is_err(),
        "Should fail with impossible busy_timeout requirement"
    );
}

/// Test that schema creation works correctly
#[tokio::test]
async fn test_schema_creation() {
    let tmp = NamedTempFile::new().unwrap();
    let db_path = tmp.path().to_str().unwrap();

    let pool = create_pool(db_path).await.unwrap();
    ensure_schema(&pool).await.unwrap();

    // Verify all tables exist
    let (ticks, signals, orders, trades) = get_row_counts(&pool).await.unwrap();

    // All should be 0 in fresh database
    assert_eq!(ticks, 0);
    assert_eq!(signals, 0);
    assert_eq!(orders, 0);
    assert_eq!(trades, 0);

    // Verify tables exist by trying to insert
    sqlx::query(
        "INSERT INTO ticks(symbol, price, volume, ts) VALUES('TEST', 100.0, 1.0, 1234567890)",
    )
    .execute(&pool)
    .await
    .expect("ticks table should exist");

    sqlx::query(
        "INSERT INTO signals(symbol, kind, value, ts) VALUES('TEST', 'BUY', 0.5, 1234567890)",
    )
    .execute(&pool)
    .await
    .expect("signals table should exist");

    sqlx::query("INSERT INTO orders(symbol, side, qty, price, status, ts) VALUES('TEST', 'BUY', 1.0, 100.0, 'FILLED', 1234567890)")
        .execute(&pool)
        .await
        .expect("orders table should exist");

    sqlx::query("INSERT INTO trades(event_id, order_id, symbol, side, fill_qty, fill_price, fees, ts, is_shadow) VALUES('abc', 'def', 'TEST', 'BUY', 1.0, 100.0, 0.1, 1234567890, 1)")
        .execute(&pool)
        .await
        .expect("trades table should exist");

    // Verify counts
    let (ticks, signals, orders, trades) = get_row_counts(&pool).await.unwrap();
    assert_eq!(ticks, 1);
    assert_eq!(signals, 1);
    assert_eq!(orders, 1);
    assert_eq!(trades, 1);
}

/// Test WAL mode allows concurrent reads
#[tokio::test]
async fn test_wal_allows_concurrent_access() {
    let tmp = NamedTempFile::new().unwrap();
    let db_path = tmp.path().to_str().unwrap();

    let pool = create_pool(db_path).await.unwrap();
    ensure_schema(&pool).await.unwrap();

    // Insert some data
    for i in 0..10 {
        sqlx::query("INSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)")
            .bind("TEST")
            .bind(100.0 + i as f64)
            .bind(1.0)
            .bind(1234567890 + i)
            .execute(&pool)
            .await
            .unwrap();
    }

    // Concurrent reads should work
    let handles: Vec<_> = (0..5)
        .map(|_| {
            let pool = pool.clone();
            tokio::spawn(async move {
                let count: i64 = sqlx::query_scalar("SELECT COUNT(*) FROM ticks")
                    .fetch_one(&pool)
                    .await
                    .unwrap();
                count
            })
        })
        .collect();

    for handle in handles {
        let count = handle.await.unwrap();
        assert_eq!(count, 10);
    }
}
