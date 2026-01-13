import math
import os
import time
from typing import List, Optional, Tuple

from venuebook.types import BookFailReason, BookStatus, VenueBook
from venues.kalshi_fetch import KalshiFetchError, fetch_book


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


def _env_nonnegative_float_alias(primary: str, alias: str, default: float) -> float:
    raw_primary = os.getenv(primary)
    raw_alias = os.getenv(alias)
    if raw_primary and raw_alias and raw_primary != raw_alias:
        raise ValueError(f"{primary} conflicts with {alias}")
    raw = raw_primary or raw_alias
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{primary} must be a non-negative float")
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{primary} must be a non-negative float")
    return value


DEPTH_NOTIONAL_MIN = _env_nonnegative_float_alias(
    "KALSHI_DEPTH_NOTIONAL_MIN",
    "K_DEPTH_NOTIONAL_MIN",
    100.0,
)
SPREAD_MAX = _env_nonnegative_float_alias("KALSHI_SPREAD_MAX", "K_SPREAD_MAX", 0.05)


def _fail_book(
    ts: float,
    reason: BookFailReason,
    raw: Optional[dict],
    depth_qty_total: float = 0.0,
    depth_notional_total_usd: Optional[float] = None,
) -> VenueBook:
    return VenueBook(
        venue="kalshi",
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
    levels = []
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


def _detect_scale(prices: List[float]) -> Optional[float]:
    if not prices:
        return None
    has_le_one = any(p <= 1.0 for p in prices)
    has_gt_one = any(p > 1.0 for p in prices)
    if has_le_one and has_gt_one:
        return None
    if any(p > 100.0 for p in prices):
        return None
    return 100.0 if has_gt_one else 1.0


def _total_depth(levels: List[Tuple[float, float]]) -> float:
    return sum(qty for _, qty in levels)


def _total_notional(levels: List[Tuple[float, float]]) -> float:
    return sum(price * qty for price, qty in levels)


def parse_kalshi_book(data: dict, *, ts: Optional[float] = None) -> VenueBook:
    ts_val = time.time() if ts is None else float(ts)
    if not isinstance(data, dict):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=None)

    raw = data
    payload = data.get("orderbook", data)
    if not isinstance(payload, dict):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    yes_container = payload.get("yes") if isinstance(payload.get("yes"), dict) else None
    no_container = payload.get("no") if isinstance(payload.get("no"), dict) else None

    yes_bid_raw = payload.get("yes_bid") or (yes_container.get("bids") if yes_container else None)
    yes_ask_raw = payload.get("yes_ask") or (yes_container.get("asks") if yes_container else None)
    no_bid_raw = payload.get("no_bid") or (no_container.get("bids") if no_container else None)
    no_ask_raw = payload.get("no_ask") or (no_container.get("asks") if no_container else None)

    if (
        yes_bid_raw is None
        and yes_ask_raw is None
        and no_bid_raw is None
        and no_ask_raw is None
    ):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    try:
        yes_bids = _parse_levels(yes_bid_raw, "yes_bid") if yes_bid_raw is not None else []
        yes_asks = _parse_levels(yes_ask_raw, "yes_ask") if yes_ask_raw is not None else []
        no_bids = _parse_levels(no_bid_raw, "no_bid") if no_bid_raw is not None else []
        no_asks = _parse_levels(no_ask_raw, "no_ask") if no_ask_raw is not None else []
    except (ValueError, TypeError):
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    scale_prices = [price for price, _ in yes_bids + yes_asks]
    if not scale_prices:
        scale_prices = [price for price, _ in no_bids + no_asks]
    scale = _detect_scale(scale_prices)
    if scale is None:
        return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)

    if not yes_bids and no_asks:
        derived = []
        for price, qty in no_asks:
            if price > scale:
                return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)
            derived.append((scale - price, qty))
        yes_bids = derived

    if not yes_asks and no_bids:
        derived = []
        for price, qty in no_bids:
            if price > scale:
                return _fail_book(ts_val, BookFailReason.PARSE_AMBIGUOUS, raw=raw)
            derived.append((scale - price, qty))
        yes_asks = derived

    if not yes_bids or not yes_asks:
        depth_qty_total = _total_depth(yes_bids) + _total_depth(yes_asks)
        depth_notional_total_usd = (
            _total_notional([(p / scale, q) for p, q in yes_bids])
            + _total_notional([(p / scale, q) for p, q in yes_asks])
        )
        return _fail_book(
            ts_val,
            BookFailReason.NO_BBO,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    bids = [(price / scale, qty) for price, qty in yes_bids]
    asks = [(price / scale, qty) for price, qty in yes_asks]

    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0])

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    if best_bid >= best_ask:
        depth_qty_total = _total_depth(bids) + _total_depth(asks)
        depth_notional_total_usd = _total_notional(bids) + _total_notional(asks)
        return _fail_book(
            ts_val,
            BookFailReason.PARSE_AMBIGUOUS,
            raw=raw,
            depth_qty_total=depth_qty_total,
            depth_notional_total_usd=depth_notional_total_usd,
        )

    depth_qty_total = _total_depth(bids) + _total_depth(asks)
    depth_notional_total_usd = _total_notional(bids) + _total_notional(asks)

    if depth_notional_total_usd < DEPTH_NOTIONAL_MIN:
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
        venue="kalshi",
        ts=ts_val,
        best_bid=best_bid,
        best_ask=best_ask,
        depth_qty_total=depth_qty_total,
        depth_notional_total_usd=depth_notional_total_usd,
        status=BookStatus.OK,
        fail_reason=None,
        raw=raw,
    )


def fetch_kalshi_venuebook(
    market: str,
    *,
    token: Optional[str] = None,
    timeout_s: float = 5.0,
) -> VenueBook:
    ts_val = time.time()
    try:
        raw = fetch_book(market, token=token, timeout_s=timeout_s)
    except KalshiFetchError:
        return _fail_book(ts_val, BookFailReason.BOOK_UNAVAILABLE, raw=None)
    return parse_kalshi_book(raw, ts=ts_val)
