"""STUB_ONLY: Compatibility shim for SHADOW runner import graph.

Must remain read-only and must not place orders or make authenticated network calls.
"""

from __future__ import annotations


class EligibilityGate:
    def __init__(self, cooldown_sec: int = 0) -> None:
        self.cooldown_sec = max(int(cooldown_sec), 0)
        self._last_trade_ts_ms: dict[str, int] = {}

    def is_eligible(self, market_id: str, now_ts_ms: int) -> bool:
        if self.cooldown_sec <= 0:
            return True
        last_ts = self._last_trade_ts_ms.get(market_id)
        if last_ts is None:
            return True
        return (now_ts_ms - last_ts) >= self.cooldown_sec * 1000

    def mark_trade(self, market_id: str, now_ts_ms: int) -> None:
        self._last_trade_ts_ms[market_id] = now_ts_ms
