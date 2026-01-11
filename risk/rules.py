"""Risk rule stubs for shadow runner compatibility."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
from typing import Deque


@dataclass
class RiskRules:
    max_orders_per_min: int = 10
    max_cancel_replace_per_min: int = 5
    taker_fee_bps: float = 0.0
    maker_fee_bps: float = 0.0
    slippage_bps: float = 0.0
    cooldown_sec: int = 0

    @classmethod
    def from_env(cls) -> "RiskRules":
        def _get_int(name: str, default: int) -> int:
            raw = os.environ.get(name)
            return int(raw) if raw is not None and raw != "" else default

        def _get_float(name: str, default: float) -> float:
            raw = os.environ.get(name)
            return float(raw) if raw is not None and raw != "" else default

        return cls(
            max_orders_per_min=_get_int("RISK_MAX_ORDERS_PER_MIN", 10),
            max_cancel_replace_per_min=_get_int("RISK_MAX_CANCEL_REPLACE_PER_MIN", 5),
            taker_fee_bps=_get_float("RISK_TAKER_FEE_BPS", 0.0),
            maker_fee_bps=_get_float("RISK_MAKER_FEE_BPS", 0.0),
            slippage_bps=_get_float("RISK_SLIPPAGE_BPS", 0.0),
            cooldown_sec=_get_int("RISK_COOLDOWN_SEC", 0),
        )


class RateLimiter:
    def __init__(self, max_per_min: int) -> None:
        self.max_per_min = int(max_per_min)
        self._events: Deque[int] = deque()

    def allow(self, now_ms: int) -> bool:
        if self.max_per_min <= 0:
            return True
        cutoff = now_ms - 60_000
        while self._events and self._events[0] < cutoff:
            self._events.popleft()
        if len(self._events) >= self.max_per_min:
            return False
        self._events.append(now_ms)
        return True


class ExposureTracker:
    def __init__(self) -> None:
        self._exposure = 0.0

    def update(self, delta: float) -> None:
        self._exposure += float(delta)

    def total(self) -> float:
        return self._exposure
