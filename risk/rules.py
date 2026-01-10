"""Risk rules and rate limiting for stale-edge strategy."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import os
from typing import Deque, Dict


@dataclass
class RiskRules:
    max_exposure_total: float = 20.0
    max_exposure_per_market: float = 20.0
    min_trade_usd: float = 1.0
    max_trade_usd: float = 5.0
    max_orders_per_min: int = 6
    max_cancel_replace_per_min: int = 6
    time_to_end_cutoff_sec: int = 900
    official_stale_sec: int = 10
    book_stale_sec: int = 5
    feed_stale_abort_sec: int = 30
    spread_max: float = 0.05
    fees_est: float = 0.01
    spread_buffer: float = 0.01
    model_error_tax: float = 0.02
    model_horizon_sec: int = 300
    model_warmup_samples: int = 5
    shadow_min_days: int = 1
    thin_book_threshold_depth_usd: float = 20.0
    thin_book_threshold_qty: float = 5.0

    @classmethod
    def from_env(cls) -> "RiskRules":
        def _get_float(key: str, default: float) -> float:
            val = os.getenv(key)
            return float(val) if val is not None else default

        def _get_int(key: str, default: int) -> int:
            val = os.getenv(key)
            return int(val) if val is not None else default

        return cls(
            max_exposure_total=_get_float("STALE_EDGE_MAX_EXPOSURE_TOTAL", cls.max_exposure_total),
            max_exposure_per_market=_get_float(
                "STALE_EDGE_MAX_EXPOSURE_PER_MARKET", cls.max_exposure_per_market
            ),
            min_trade_usd=_get_float("STALE_EDGE_MIN_TRADE_USD", cls.min_trade_usd),
            max_trade_usd=_get_float("STALE_EDGE_MAX_TRADE_USD", cls.max_trade_usd),
            max_orders_per_min=_get_int("STALE_EDGE_MAX_ORDERS_PER_MIN", cls.max_orders_per_min),
            max_cancel_replace_per_min=_get_int(
                "STALE_EDGE_MAX_CANCEL_REPLACE_PER_MIN", cls.max_cancel_replace_per_min
            ),
            time_to_end_cutoff_sec=_get_int(
                "STALE_EDGE_TIME_TO_END_CUTOFF_SEC", cls.time_to_end_cutoff_sec
            ),
            official_stale_sec=_get_int("STALE_EDGE_OFFICIAL_STALE_SEC", cls.official_stale_sec),
            book_stale_sec=_get_int("STALE_EDGE_BOOK_STALE_SEC", cls.book_stale_sec),
            feed_stale_abort_sec=_get_int(
                "STALE_EDGE_FEED_STALE_ABORT_SEC", cls.feed_stale_abort_sec
            ),
            spread_max=_get_float("STALE_EDGE_SPREAD_MAX", cls.spread_max),
            fees_est=_get_float("STALE_EDGE_FEES_EST", cls.fees_est),
            spread_buffer=_get_float("STALE_EDGE_SPREAD_BUFFER", cls.spread_buffer),
            model_error_tax=_get_float("STALE_EDGE_MODEL_ERROR_TAX", cls.model_error_tax),
            model_horizon_sec=_get_int("STALE_EDGE_MODEL_HORIZON_SEC", cls.model_horizon_sec),
            model_warmup_samples=_get_int(
                "STALE_EDGE_MODEL_WARMUP_SAMPLES", cls.model_warmup_samples
            ),
            shadow_min_days=_get_int("STALE_EDGE_SHADOW_MIN_DAYS", cls.shadow_min_days),
            thin_book_threshold_depth_usd=_get_float(
                "STALE_EDGE_THIN_BOOK_THRESHOLD_DEPTH_USD", cls.thin_book_threshold_depth_usd
            ),
            thin_book_threshold_qty=_get_float(
                "STALE_EDGE_THIN_BOOK_THRESHOLD_QTY", cls.thin_book_threshold_qty
            ),
        )

    def edge_min(self) -> float:
        return self.fees_est + self.spread_buffer + self.model_error_tax


class RateLimiter:
    def __init__(self, max_per_min: int) -> None:
        self.max_per_min = max_per_min
        self.timestamps: Deque[int] = deque()

    def allow(self, now_ms: int) -> bool:
        window_ms = 60_000
        while self.timestamps and now_ms - self.timestamps[0] > window_ms:
            self.timestamps.popleft()
        if len(self.timestamps) >= self.max_per_min:
            return False
        self.timestamps.append(now_ms)
        return True


class ExposureTracker:
    def __init__(self) -> None:
        self.total_exposure = 0.0
        self.market_exposure: Dict[str, float] = defaultdict(float)

    def can_add(self, market_id: str, notional: float, rules: RiskRules) -> bool:
        if self.total_exposure + notional > rules.max_exposure_total:
            return False
        if self.market_exposure[market_id] + notional > rules.max_exposure_per_market:
            return False
        return True

    def add(self, market_id: str, notional: float) -> None:
        self.total_exposure += notional
        self.market_exposure[market_id] += notional

    def reset_market(self, market_id: str) -> None:
        self.total_exposure -= self.market_exposure.get(market_id, 0.0)
        self.market_exposure[market_id] = 0.0
