//! VenueBook normalization - Fail-closed parsing for Polymarket and Kalshi
//!
//! Implements strict, deterministic parsing with validation.
//! Rejects malformed/ambiguous payloads (fail-closed).

use crate::types::{Level, VenueBook};
use anyhow::{anyhow, bail, Result};
use serde_json::Value;

/// Parse Polymarket /book endpoint response
///
/// Expected schema:
/// ```json
/// {
///   "market": "...",
///   "bids": [[price, size], ...],
///   "asks": [[price, size], ...]
/// }
/// ```
///
/// # Validation
/// - Rejects missing fields
/// - Rejects non-array bids/asks
/// - Rejects negative prices or quantities
/// - Rejects NaN or infinite values
/// - Ensures bids sorted descending, asks sorted ascending
pub fn parse_polymarket_book(value: &Value) -> Result<VenueBook> {
    let obj = value
        .as_object()
        .ok_or_else(|| anyhow!("polymarket book: root must be object"))?;

    let market = obj
        .get("market")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("polymarket book: missing or invalid 'market' field"))?;

    let bids_array = obj
        .get("bids")
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("polymarket book: 'bids' must be array"))?;

    let asks_array = obj
        .get("asks")
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("polymarket book: 'asks' must be array"))?;

    let mut bids = parse_levels(bids_array, "bids")?;
    let mut asks = parse_levels(asks_array, "asks")?;

    // Sort bids descending (best bid first)
    bids.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    // Sort asks ascending (best ask first)
    asks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

    Ok(VenueBook {
        venue: "polymarket".to_string(),
        symbol: market.to_string(),
        bids,
        asks,
    })
}

/// Parse Kalshi /markets/{ticker}/orderbook endpoint response
///
/// Expected schema:
/// ```json
/// {
///   "ticker": "...",
///   "yes_bid": [[price_cents, size], ...],
///   "no_bid": [[price_cents, size], ...]
/// }
/// ```
///
/// # Kalshi Bids-Only Conversion
/// Kalshi provides YES bids and NO bids. We convert to coherent book:
/// - YES bids → YES bids (buy YES at price)
/// - NO bids → YES asks (sell YES at 100 - no_bid_price)
/// - YES asks derived from NO bids: yes_ask_price = 100 - no_bid_price
/// - NO asks derived from YES bids: no_ask_price = 100 - yes_bid_price
///
/// # Validation
/// - Rejects missing fields
/// - Rejects prices outside [0, 100] range
/// - Rejects negative quantities
/// - Rejects NaN or infinite values
/// - Ensures coherent spread (no negative spread if both sides exist)
pub fn parse_kalshi_orderbook(value: &Value) -> Result<VenueBook> {
    let obj = value
        .as_object()
        .ok_or_else(|| anyhow!("kalshi book: root must be object"))?;

    let ticker = obj
        .get("ticker")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("kalshi book: missing or invalid 'ticker' field"))?;

    let yes_bid_array = obj
        .get("yes_bid")
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("kalshi book: 'yes_bid' must be array"))?;

    let no_bid_array = obj
        .get("no_bid")
        .and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("kalshi book: 'no_bid' must be array"))?;

    let yes_bids = parse_levels(yes_bid_array, "yes_bid")?;
    let no_bids = parse_levels(no_bid_array, "no_bid")?;

    // Validate Kalshi price bounds [0, 100]
    for (price, _) in yes_bids.iter().chain(no_bids.iter()) {
        if *price < 0.0 || *price > 100.0 {
            bail!("kalshi book: price {} out of bounds [0, 100]", price);
        }
    }

    // Convert: YES bids stay as bids
    let mut bids = yes_bids.clone();
    bids.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    // Convert: NO bids → YES asks (yes_ask_price = 100 - no_bid_price)
    let mut asks: Vec<Level> = no_bids
        .iter()
        .map(|(no_bid_price, qty)| (100.0 - no_bid_price, *qty))
        .collect();
    asks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

    // Validate coherent spread (no crossed book)
    if let (Some((best_bid, _)), Some((best_ask, _))) = (bids.first(), asks.first()) {
        if best_bid >= best_ask {
            bail!(
                "kalshi book: crossed book detected (bid {} >= ask {})",
                best_bid,
                best_ask
            );
        }
    }

    Ok(VenueBook {
        venue: "kalshi".to_string(),
        symbol: ticker.to_string(),
        bids,
        asks,
    })
}

/// Parse price levels from JSON array
///
/// Expects: [[price, qty], ...]
/// Validates: no negatives, no NaN, no infinite
fn parse_levels(arr: &[Value], field_name: &str) -> Result<Vec<Level>> {
    let mut levels = Vec::new();

    for (idx, item) in arr.iter().enumerate() {
        let level_arr = item
            .as_array()
            .ok_or_else(|| anyhow!("{}: level {} must be array", field_name, idx))?;

        if level_arr.len() != 2 {
            bail!(
                "{}: level {} must have exactly 2 elements [price, qty]",
                field_name,
                idx
            );
        }

        let price = level_arr[0]
            .as_f64()
            .ok_or_else(|| anyhow!("{}: level {} price must be number", field_name, idx))?;

        let qty = level_arr[1]
            .as_f64()
            .ok_or_else(|| anyhow!("{}: level {} qty must be number", field_name, idx))?;

        // Fail-closed validation
        if !price.is_finite() {
            bail!("{}: level {} price not finite: {}", field_name, idx, price);
        }
        if !qty.is_finite() {
            bail!("{}: level {} qty not finite: {}", field_name, idx, qty);
        }
        if price < 0.0 {
            bail!("{}: level {} price negative: {}", field_name, idx, price);
        }
        if qty < 0.0 {
            bail!("{}: level {} qty negative: {}", field_name, idx, qty);
        }

        levels.push((price, qty));
    }

    Ok(levels)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_polymarket_valid() {
        let json = r#"{
            "market": "test-market",
            "bids": [[52.0, 100.0], [51.0, 200.0]],
            "asks": [[53.0, 150.0], [54.0, 250.0]]
        }"#;
        let value: Value = serde_json::from_str(json).unwrap();
        let book = parse_polymarket_book(&value).unwrap();

        assert_eq!(book.venue, "polymarket");
        assert_eq!(book.symbol, "test-market");
        assert_eq!(book.bids.len(), 2);
        assert_eq!(book.asks.len(), 2);
        assert_eq!(book.best_bid(), Some(52.0));
        assert_eq!(book.best_ask(), Some(53.0));
    }

    #[test]
    fn test_parse_polymarket_negative_price() {
        let json = r#"{
            "market": "test",
            "bids": [[-10.0, 100.0]],
            "asks": [[53.0, 150.0]]
        }"#;
        let value: Value = serde_json::from_str(json).unwrap();
        assert!(parse_polymarket_book(&value).is_err());
    }

    #[test]
    fn test_parse_kalshi_valid() {
        let json = r#"{
            "ticker": "TEST-KALSHI",
            "yes_bid": [[48, 100], [47, 200]],
            "no_bid": [[50, 150], [51, 250]]
        }"#;
        let value: Value = serde_json::from_str(json).unwrap();
        let book = parse_kalshi_orderbook(&value).unwrap();

        assert_eq!(book.venue, "kalshi");
        assert_eq!(book.symbol, "TEST-KALSHI");
        // YES bids: 48, 47
        assert_eq!(book.best_bid(), Some(48.0));
        // YES asks from NO bids: 100-50=50, 100-51=49
        // After sorting ascending: [49, 50]
        assert_eq!(book.best_ask(), Some(49.0));
    }

    #[test]
    fn test_parse_kalshi_out_of_bounds() {
        let json = r#"{
            "ticker": "TEST",
            "yes_bid": [[105, 100]],
            "no_bid": []
        }"#;
        let value: Value = serde_json::from_str(json).unwrap();
        assert!(parse_kalshi_orderbook(&value).is_err());
    }
}
