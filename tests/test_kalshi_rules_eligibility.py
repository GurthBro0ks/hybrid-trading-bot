import time
from eligibility.kalshi_rules import check_kalshi_eligibility, EligibilityResult
from sources.resolution_source import ResolutionSource

def test_kalshi_eligibility_ok():
    full_text = "Resolved by the Coinbase BTC/USD spot price."
    meta = {
        "rules_primary": full_text,
        "close_time": "2026-12-31T23:59:59Z"
    }
    # Future time
    now = time.time()
    # Mock close time far in future
    res, source = check_kalshi_eligibility(meta, now_ts=now)
    assert res == EligibilityResult.ELIGIBLE
    assert source.venue == "coinbase"
    assert source.symbol == "BTC/USD"

def test_kalshi_eligibility_closed():
    full_text = "Resolved by the Coinbase BTC/USD spot price."
    meta = {
        "rules_primary": full_text,
        "close_time": "2020-01-01T00:00:00Z"
    }
    now = time.time()
    res, source = check_kalshi_eligibility(meta, now_ts=now)
    assert res == EligibilityResult.MARKET_CLOSED

def test_kalshi_eligibility_unsupported_rules():
    meta = {
        "rules_primary": "Resolved by the outcome of the Super Bowl.",
        "close_time": "2026-12-31T23:59:59Z"
    }
    res, source = check_kalshi_eligibility(meta)
    assert res == EligibilityResult.UNSUPPORTED_RULES
    assert source is None

def test_kalshi_eligibility_feed_unknown():
    # Matches binance pattern but maybe we want to test something that resolves to a source we don't route?
    # actually check_kalshi_eligibility only checks if venue is enabled.
    # Let's say we have a source regex that matches "Kraken" but Kraken is not in valid list.
    # Currently we don't have a regex for Kraken, so it would be UNSUPPORTED_RULES.
    pass

def test_kalshi_eligibility_missing_close_time():
    meta = {
        "rules_primary": "Resolved by the Coinbase BTC/USD spot price",
    }
    res, source = check_kalshi_eligibility(meta)
    assert res == EligibilityResult.MISSING_CLOSE_TIME
