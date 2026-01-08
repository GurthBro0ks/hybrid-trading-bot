use anyhow::Result;
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use std::{fs, time::{SystemTime, UNIX_EPOCH}};
use tokio::{sync::mpsc, time::{sleep, Duration}};
use tracing::{info, warn};

#[derive(Debug, Clone)]
struct Tick {
    symbol: String,
    price: f64,
    volume: f64,
    ts: i64,
}

fn now_ts() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() as i64
}

async fn make_pool(db_url: &str) -> Result<SqlitePool> {
    let pool = SqlitePoolOptions::new()
        .max_connections(5)
        .after_connect(|conn, _meta| Box::pin(async move {
            sqlx::query("PRAGMA journal_mode = WAL;").execute(conn).await?;
            sqlx::query("PRAGMA synchronous = NORMAL;").execute(conn).await?;
            sqlx::query("PRAGMA busy_timeout = 5000;").execute(conn).await?;
            sqlx::query("PRAGMA temp_store = MEMORY;").execute(conn).await?;
            Ok(())
        }))
        .connect(db_url)
        .await?;
    Ok(pool)
}

async fn ensure_schema(pool: &SqlitePool, schema_path: &str) -> Result<()> {
    let sql = fs::read_to_string(schema_path)?;
    for stmt in sql.split(';').map(|s| s.trim()).filter(|s| !s.is_empty()) {
        sqlx::query(stmt).execute(pool).await?;
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .init();

    let db_path = "/opt/hybrid-trading-bot/data/bot.db";
    let db_url = format!("sqlite://{}", db_path);
    let schema_path = "/opt/hybrid-trading-bot/shared/schema/schema.sql";

    info!("starting engine; db={}", db_path);

    // Ensure data dir exists
    std::fs::create_dir_all("/opt/hybrid-trading-bot/data")?;

    let pool = make_pool(&db_url).await?;
    ensure_schema(&pool, schema_path).await?;
    info!("schema ensured");

    // Channels: producer -> persistence writer
    let (tx, mut rx) = mpsc::channel::<Tick>(100);

    // Ingestion mock (generates ticks)
    tokio::spawn(async move {
        let mut price = 100.0_f64;
        loop {
            price += 0.05; // deterministic drift for proof
            let t = Tick {
                symbol: "SOL/USDC".to_string(),
                price,
                volume: 1.0,
                ts: now_ts(),
            };
            if tx.send(t).await.is_err() {
                warn!("tick channel closed");
                break;
            }
            sleep(Duration::from_millis(500)).await;
        }
    });

    // Persistence task (single writer loop)
    loop {
        if let Some(t) = rx.recv().await {
            sqlx::query(
                "INSERT INTO ticks(symbol, price, volume, ts) VALUES(?, ?, ?, ?)"
            )
            .bind(&t.symbol)
            .bind(t.price)
            .bind(t.volume)
            .bind(t.ts)
            .execute(&pool)
            .await?;
            info!("tick saved: {} price={:.4} ts={}", t.symbol, t.price, t.ts);
        } else {
            break;
        }
    }

    Ok(())
}
