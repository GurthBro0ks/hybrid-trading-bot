//! Mock Websocket Server
//!
//! Emits deterministic ticks to connected clients.
//! Usage: cargo run --bin mock-ws -- --port 9001

use futures::{SinkExt, StreamExt};
use serde::Serialize;
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio::time::{interval, Duration};
use tokio_tungstenite::accept_async;
use tokio_tungstenite::tungstenite::Message;
use tracing::{info, warn};
use uuid::Uuid;

#[derive(Serialize)]
struct Tick {
    event_id: String,
    symbol: String,
    price: f64,
    volume: f64,
    ts: i64,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let addr = "127.0.0.1:9001";
    let listener = TcpListener::bind(&addr).await.expect("Failed to bind");
    info!("Listening on: {}", addr);

    let client_count = Arc::new(AtomicU64::new(0));

    while let Ok((stream, _)) = listener.accept().await {
        let count = client_count.clone();
        tokio::spawn(async move {
            count.fetch_add(1, Ordering::Relaxed);
            handle_connection(stream).await;
            count.fetch_sub(1, Ordering::Relaxed);
        });
    }
}

async fn handle_connection(stream: TcpStream) {
    let addr = stream.peer_addr().expect("connected streams should have a peer address");
    info!("Peer address: {}", addr);

    let ws_stream = accept_async(stream).await.expect("Error during the websocket handshake occurred");
    info!("New WebSocket connection: {}", addr);

    let (mut write, mut read) = ws_stream.split();

    // Spawn ticker task
    let mut timer = interval(Duration::from_millis(500));
    let mut price = 100.0;
    
    // We need to handle incoming messages (Pings/Close) too
    let (tx, mut rx) = tokio::sync::mpsc::channel::<()>(1);
    
    let read_handle = tokio::spawn(async move {
        while let Some(msg) = read.next().await {
            match msg {
                Ok(Message::Close(_)) => break,
                Ok(Message::Ping(data)) => {
                     // Auto-pong is handled by tungstenite usually, but we can reply if needed? 
                     // Tungstenite handles Pings automatically by default in `read`.
                }
                Err(_) => break,
                _ => {}
            }
        }
        let _ = tx.send(()).await;
    });

    loop {
        tokio::select! {
             _ = timer.tick() => {
                 price += 0.1; // Simple linear increase for mock
                 if price > 110.0 { price = 90.0; }
                 let tick = Tick {
                     event_id: Uuid::new_v4().to_string(),
                     symbol: "SOL/USDC".to_string(),
                     price,
                     volume: 1.0,
                     ts: chrono::Utc::now().timestamp_millis(),
                 };
                 let json = serde_json::to_string(&tick).unwrap();
                 if let Err(e) = write.send(Message::Text(json)).await {
                     warn!("Error sending tick: {}", e);
                     break;
                 }
             }
             _ = rx.recv() => {
                 break;
             }
        }
    }
    
    info!("Connection closed: {}", addr);
}
