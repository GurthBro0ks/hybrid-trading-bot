use anyhow::Result;
use serde::Deserialize;
use sqlx::{sqlite::SqlitePoolOptions, SqlitePool};
use std::{fs, time::{SystemTime, UNIX_EPOCH}};
use tokio::{sync::mpsc, time::{sleep, Duration}};
use tracing::{info, warn};

#[derive(Debug, Deserialize)]
struct Config {
    app: AppConfig,
    engine: EngineConfig,
}

#[derive(Debug, Deserialize)]
struct AppConfig {
    symbol: String,
    db_path: String,
}

#[derive(Debug, Deserialize)]
struct EngineConfig {
    tick_interval_ms: u64,
    start_price: f64,
    price_step: f64,
    volume: f64,
}

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
            sqlx::query("PRAGMA journal_mode = WAL;").execute(&mut *conn).await?;
            sqlx::query("PRAGMA synchronous = NORMAL;").execute(&mut *conn).await?;
            sqlx::query("PRAGMA busy_timeout = 5000;").execute(&mut *conn).await?;
            sqlx::query("PRAGMA temp_store = MEMORY;").execute(&mut *conn).await?;
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
        .with_target(false)
        .init();

    // Load config
    let config_path = "config/config.toml";
    let config_str = fs::read_to_string(config_path)?;
    let config: Config = toml::from_str(&config_str)?;

    let db_path = config.app.db_path.clone();
    let db_url = format!("sqlite://{}?mode=rwc", db_path);
    let schema_path = "shared/schema/schema.sql";

    info!("starting engine; symbol={} db={}", config.app.symbol, db_path);

    // Ensure data dir exists
    if let Some(parent) = std::path::Path::new(&db_path).parent() {
        std::fs::create_dir_all(parent)?;
    }

    let pool = make_pool(&db_url).await?;
    ensure_schema(&pool, schema_path).await?;
    info!("schema ensured");

    // Channels: producer -> persistence writer
    let (tx, mut rx) = mpsc::channel::<Tick>(100);

    // Ingestion mock (generates ticks)
    let symbol = config.app.symbol.clone();
    let start_price = config.engine.start_price;
    let price_step = config.engine.price_step;
    let volume = config.engine.volume;
    let interval = config.engine.tick_interval_ms;

    tokio::spawn(async move {
        let mut price = start_price;
        loop {
            price += price_step; // deterministic drift for proof
            let t = Tick {
                symbol: symbol.clone(),
                price,
                volume,
                ts: now_ts(),
            };
            if tx.send(t).await.is_err() {
                warn!("tick channel closed");
                break;
            }
            sleep(Duration::from_millis(interval)).await;
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
