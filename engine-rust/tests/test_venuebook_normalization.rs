//! VenueBook normalization and thin-book classification tests
//!
//! Tests:
//! - Polymarket /book parsing and normalization
//! - Kalshi /markets/{ticker}/orderbook parsing with bids-only conversion
//! - Thin-book classification with deterministic subreason mapping
//! - Fail-closed behavior on malformed payloads

mod fixture_io;

use engine_rust::ingest::venuebook::{parse_kalshi_orderbook, parse_polymarket_book};
use engine_rust::strategy::classify_thin_book;
use engine_rust::types::{ReasonCode, VenueBook};
use fixture_io::load_fixture_json;

// --- Polymarket Tests ---

#[test]
fn test_polymarket_deep_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/polymarket/pm_deep.json");
    let book = parse_polymarket_book(&json).expect("Failed to parse pm_deep.json");

    assert_eq!(book.venue, "polymarket");
    assert_eq!(book.symbol, "pm-test-deep");

    // Verify bids sorted descending
    assert_eq!(book.bids.len(), 5);
    assert_eq!(book.best_bid(), Some(52.5));
    assert!(book.bids[0].0 > book.bids[1].0); // 52.5 > 52.0

    // Verify asks sorted ascending
    assert_eq!(book.asks.len(), 5);
    assert_eq!(book.best_ask(), Some(53.0));
    assert!(book.asks[0].0 < book.asks[1].0); // 53.0 < 53.5

    // Verify spread
    assert_eq!(book.spread(), Some(0.5)); // 53.0 - 52.5

    // Not thin (depth = 1000+2500+3000 + 1200+2800+3200 = 13700)
    let (is_thin, _) = classify_thin_book(&book).expect("classify failed");
    assert!(!is_thin, "pm_deep should not be thin");
}

#[test]
fn test_polymarket_thin_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/polymarket/pm_thin.json");
    let book = parse_polymarket_book(&json).expect("Failed to parse pm_thin.json");

    assert_eq!(book.venue, "polymarket");
    assert_eq!(book.best_bid(), Some(48.0));
    assert_eq!(book.best_ask(), Some(52.0));
    assert_eq!(book.spread(), Some(4.0));

    // Thin: depth = 50+30 + 45+25 = 150 < 500
    let (is_thin, reason) = classify_thin_book(&book).expect("classify failed");
    assert!(is_thin, "pm_thin should be thin");
    assert_eq!(
        reason,
        Some(ReasonCode::ThinBookDepthBelowThreshold),
        "pm_thin should be DEPTH_BELOW_THRESHOLD"
    );
}

#[test]
fn test_polymarket_empty_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/polymarket/pm_empty.json");
    let book = parse_polymarket_book(&json).expect("Failed to parse pm_empty.json");

    assert_eq!(book.venue, "polymarket");
    assert_eq!(book.bids.len(), 0);
    assert_eq!(book.asks.len(), 0);
    assert_eq!(book.best_bid(), None);
    assert_eq!(book.best_ask(), None);

    // Thin: NO_BBO (missing best bid/ask)
    let (is_thin, reason) = classify_thin_book(&book).expect("classify failed");
    assert!(is_thin, "pm_empty should be thin");
    assert_eq!(
        reason,
        Some(ReasonCode::ThinBookNoBbo),
        "pm_empty should be NO_BBO"
    );
}

// --- Kalshi Tests ---

#[test]
fn test_kalshi_deep_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/kalshi/k_deep.json");
    let book = parse_kalshi_orderbook(&json).expect("Failed to parse k_deep.json");

    assert_eq!(book.venue, "kalshi");
    assert_eq!(book.symbol, "KALSHI-TEST-DEEP");

    // YES bids: [47, 46, 45, 44, 43]
    assert_eq!(book.bids.len(), 5);
    assert_eq!(book.best_bid(), Some(47.0));

    // YES asks from NO bids: 100-51=49, 100-50=50, 100-49=51, 100-48=52, 100-47=53
    // After sorting ascending: [49, 50, 51, 52, 53]
    assert_eq!(book.asks.len(), 5);
    assert_eq!(book.best_ask(), Some(49.0));

    // Spread: 49 - 47 = 2.0 (< 5.0 threshold, not wide)
    let spread = book.spread().expect("spread should exist");
    assert_eq!(spread, 2.0);

    // Not thin: spread (2.0 < 5.0), depth (300*3 + 300*3 = 1800 > 500)
    let (is_thin, _) = classify_thin_book(&book).expect("classify failed");
    assert!(!is_thin, "k_deep should not be thin");
}

#[test]
fn test_kalshi_one_sided_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/kalshi/k_one_sided.json");
    let book = parse_kalshi_orderbook(&json).expect("Failed to parse k_one_sided.json");

    assert_eq!(book.venue, "kalshi");

    // YES bids: [60, 59]
    assert_eq!(book.best_bid(), Some(60.0));

    // NO bids empty → no YES asks
    assert_eq!(book.asks.len(), 0);
    assert_eq!(book.best_ask(), None);

    // Thin: NO_BBO (missing asks)
    let (is_thin, reason) = classify_thin_book(&book).expect("classify failed");
    assert!(is_thin, "k_one_sided should be thin");
    assert_eq!(
        reason,
        Some(ReasonCode::ThinBookNoBbo),
        "k_one_sided should be NO_BBO"
    );
}

#[test]
fn test_kalshi_empty_book() {
    let json = load_fixture_json("tests/fixtures/venuebook/kalshi/k_empty.json");
    let book = parse_kalshi_orderbook(&json).expect("Failed to parse k_empty.json");

    assert_eq!(book.venue, "kalshi");
    assert_eq!(book.bids.len(), 0);
    assert_eq!(book.asks.len(), 0);

    // Thin: NO_BBO
    let (is_thin, reason) = classify_thin_book(&book).expect("classify failed");
    assert!(is_thin);
    assert_eq!(reason, Some(ReasonCode::ThinBookNoBbo));
}

#[test]
fn test_kalshi_wide_spread() {
    let json = load_fixture_json("tests/fixtures/venuebook/kalshi/k_wide.json");
    let book = parse_kalshi_orderbook(&json).expect("Failed to parse k_wide.json");

    assert_eq!(book.venue, "kalshi");

    // YES bids: [30, 29]
    assert_eq!(book.best_bid(), Some(30.0));

    // YES asks from NO bids: 100-25=75, 100-24=76
    // After sorting: [75, 76]
    assert_eq!(book.best_ask(), Some(75.0));

    // Spread: 75 - 30 = 45.0 (WIDE, > 5.0)
    let spread = book.spread().expect("spread should exist");
    assert_eq!(spread, 45.0);

    // Thin: SPREAD_WIDE
    let (is_thin, reason) = classify_thin_book(&book).expect("classify failed");
    assert!(is_thin, "k_wide should be thin");
    assert_eq!(
        reason,
        Some(ReasonCode::ThinBookSpreadWide),
        "k_wide should be SPREAD_WIDE"
    );
}

// --- Malformed Payload Tests (Fail-Closed) ---

#[test]
fn test_polymarket_bad_shape() {
    let json = load_fixture_json("tests/fixtures/venuebook/malformed/pm_bad_shape.json");
    let result = parse_polymarket_book(&json);
    assert!(result.is_err(), "pm_bad_shape should fail parsing");
}

#[test]
fn test_kalshi_bad_shape() {
    let json = load_fixture_json("tests/fixtures/venuebook/malformed/k_bad_shape.json");
    let result = parse_kalshi_orderbook(&json);
    assert!(result.is_err(), "k_bad_shape should fail parsing");
}

#[test]
fn test_ambiguous_price() {
    let json = load_fixture_json("tests/fixtures/venuebook/malformed/ambiguous_price.json");
    let result = parse_polymarket_book(&json);
    assert!(
        result.is_err(),
        "ambiguous_price should fail (negative price/qty)"
    );
}

// --- Thin-Book Classifier Direct Tests ---

#[test]
fn test_classify_crossed_book_fails() {
    // Manually construct a crossed book (bid >= ask)
    let crossed_book = VenueBook {
        venue: "test".to_string(),
        symbol: "CROSSED".to_string(),
        bids: vec![(60.0, 100.0)],
        asks: vec![(55.0, 100.0)], // ask < bid (crossed)
    };

    let result = classify_thin_book(&crossed_book);
    assert!(result.is_err(), "crossed book should fail classification");
}

#[test]
fn test_classify_healthy_book() {
    let healthy_book = VenueBook {
        venue: "test".to_string(),
        symbol: "HEALTHY".to_string(),
        bids: vec![(50.0, 200.0), (49.0, 300.0), (48.0, 400.0)],
        asks: vec![(51.0, 200.0), (52.0, 300.0), (53.0, 400.0)],
    };

    // Spread = 1.0 (< 5.0)
    // Depth = 200+300+400 + 200+300+400 = 1800 (> 500)
    let (is_thin, reason) = classify_thin_book(&healthy_book).expect("classify failed");
    assert!(!is_thin, "healthy book should not be thin");
    assert_eq!(reason, None);
}
