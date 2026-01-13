import math
import os
import time
from typing import List, Optional, Tuple

from venuebook.types import BookFailReason, BookStatus, VenueBook
from venues.polymarket_fetch import PolymarketFetchError, fetch_book


def _env_nonnegative_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a non-negative float")
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a non-negative float")
    return value


DEPTH_QTY_MIN = _env_nonnegative_float("PM_DEPTH_QTY_MIN", 100.0)
SPREAD_MAX = _env_nonnegative_float("PM_SPREAD_MAX", 0.05)


def _fail_book(
    ts: float,
    reason: BookFailReason,
    raw: Optional[dict],
    depth_qty_total: float = 0.0,
    depth_notional_total_usd: Optional[float] = None,
) -> VenueBook:
    return VenueBook(
        venue="polymarket",
        ts=ts,
        best_bid=None,
        best_ask=None,
        depth_qty_total=float(depth_qty_total),
        depth_notional_total_usd=depth_notional_total_usd,
        status=BookStatus.NO_TRADE,
        fail_reason=reason,
        raw=raw,
    )


def _parse_levels(arr: list, field_name: str) -> List[Tuple[float, float]]:
    levels: List[Tuple[float, float]] = []
    if not isinstance(arr, list):
        raise ValueError(f"{field_name}: must be a list")
    shape = None
    for idx, item in enumerate(arr):
        if isinstance(item, dict):
            if shape == "list":
                raise ValueError(f"{field_name}: mixed level shapes")
            shape = "dict"
            if "price" not in item:
                raise ValueError(f"{field_name}: level {idx} missing price")
            qty_fields = [k for k in ("size", "qty", "quantity") if k in item]
            if not qty_fields:
                raise ValueError(f"{field_name}: level {idx} missing size/qty")
            if len(qty_fields) > 1:
                values = [item[k] for k in qty_fields]
                if any(v != values[0] for v in values[1:]):
                    raise ValueError(f"{field_name}: level {idx} ambiguous qty fields")
            qty_key = qty_fields[0]
            try:
                price = float(item.get("price"))
                qty = float(item.get(qty_key))
            except (ValueError, TypeError):
                raise ValueError(f"{field_name}: level {idx} price/qty must be numeric")
        elif isinstance(item, list) and len(item) == 2:
            if shape == "dict":
                raise ValueError(f"{field_name}: mixed level shapes")
            shape = "list"
            try:
                price = float(item[0])
                qty = float(item[1])
            except (ValueError, TypeError):
                raise ValueError(f"{field_name}: level {idx} price/qty must be numeric")
        else:
            raise ValueError(f"{field_name}: level {idx} invalid shape")

        if not math.isfinite(price) or not math.isfinite(qty):
            raise ValueError(f"{field_name}: level {idx} not finite")
        if price < 0.0 or qty < 0.0:
            raise ValueError(f"{field_name}: level {idx} negative")

        levels.append((price, qty))
    return levels


def _total_depth(levels: List[Tuple[float, float]]) -> float:
    return sum(qty for _, qty in levels)


def _total_notional(levels: List[Tuple[float, float]]) -> float:
    return sum(price * qty for price, qty in levels)


def parse_polymarket_book(data: dict, *, ts: Optional[float] = None) -> VenueBook:
    ts_val = time.time() if ts is None else float(ts)
    if not isinstance(data, dict):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=None)

    raw = data
    market = data.get("market")
    if not isinstance(market, str):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    bids_raw = data.get("bids")
    asks_raw = data.get("asks")
    if bids_raw is None and asks_raw is None:
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    try:
        bids = _parse_levels(bids_raw if bids_raw is not None else [], "bids")
        asks = _parse_levels(asks_raw if asks_raw is not None else [], "asks")
    except (ValueError, TypeError):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    for price, _ in bids + asks:
        if price > 1.0:
            return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0])

    depth_qty_total = _total_depth(bids) + _total_depth(asks)
    depth_notional_total_usd = _total_notional(bids) + _total_notional(asks)

    if not bids or not asks:
        return _fail_book(
            ts_val,
            BookFailReason.NO_BBO,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    if best_bid >= best_ask:
        return _fail_book(
            ts_val,
            BookFailReason.PARSE_AMBIGUOUS,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    if depth_qty_total < DEPTH_QTY_MIN:
        return _fail_book(
            ts_val,
            BookFailReason.DEPTH_BELOW_THRESHOLD,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    spread = best_ask - best_bid
    if spread > SPREAD_MAX:
        return _fail_book(
            ts_val,
            BookFailReason.SPREAD_WIDE,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    return VenueBook(
        venue="polymarket",
        ts=ts_val,
        best_bid=best_bid,
        best_ask=best_ask,
        depth_qty_total=depth_qty_total,
        depth_notional_total_usd=depth_notional_total_usd,
        status=BookStatus.OK,
        fail_reason=None,
        raw=raw,
    )


def fetch_polymarket_venuebook(market: str, *, timeout_s: float = 5.0) -> VenueBook:
    ts_val = time.time()

    # Check for fixture mode via env
    if os.environ.get("POLYMARKET_FIXTURE_MODE") == "1":
         # Load from ok_book.json
         import json
         from pathlib import Path
         fix_path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "polymarket" / "ok_book.json"
         if fix_path.exists():
             with open(fix_path, 'r') as f:
                 raw = json.load(f)
                 return parse_polymarket_book(raw, ts=ts_val)

    try:
        raw = fetch_book(market, timeout_s=timeout_s)
    except PolymarketFetchError:
        return _fail_book(ts_val, BookFailReason.BOOK_UNAVAILABLE, raw=None)
    return parse_polymarket_book(raw, ts=ts_val)
