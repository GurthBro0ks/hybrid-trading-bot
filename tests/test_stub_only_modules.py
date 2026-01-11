import importlib
import inspect

import pytest


STUB_MODULES = [
    "recorder.trade_journal",
    "risk",
    "risk.eligibility",
    "risk.rules",
    "strategies",
    "strategies.stale_edge",
    "venues",
    "venues.kalshi",
]


def test_stub_modules_labeled() -> None:
    for name in STUB_MODULES:
        module = importlib.import_module(name)
        assert module.__doc__ and "STUB_ONLY" in module.__doc__


def test_stub_modules_no_requests() -> None:
    for name in STUB_MODULES:
        module = importlib.import_module(name)
        source = inspect.getsource(module)
        assert "requests" not in source


def test_kalshi_no_trading() -> None:
    from venues.kalshi import KalshiVenue

    venue = KalshiVenue()
    for method_name in ("place_order", "cancel_order", "cancel_all"):
        with pytest.raises(RuntimeError, match="STUB_ONLY_NO_TRADING"):
            getattr(venue, method_name)()


def test_strategy_no_trade() -> None:
    from strategies.stale_edge import BookTop, StaleEdgeStrategy

    strategy = StaleEdgeStrategy(rules={})
    decision = strategy.evaluate_market({"pm_yes_bid": 50.0, "pm_yes_ask": 51.0})
    assert decision.action == "NO_TRADE"

    decision = strategy.evaluate(
        market_id="TEST",
        official_mid=None,
        official_ts_ms=None,
        book=BookTop(
            yes_bid=50.0,
            yes_ask=51.0,
            no_bid=49.0,
            no_ask=50.0,
            ts_ms=0,
        ),
        market_end_ts_ms=0,
        now_ts_ms=0,
    )
    assert decision.action == "NO_TRADE"
