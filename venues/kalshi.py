"""STUB_ONLY: Compatibility shim for SHADOW runner import graph.

Must remain read-only and must not place orders or make authenticated network calls.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class KalshiVenue:
    def __init__(self, env: str = "prod") -> None:
        self.env = env

    def place_order(self, *args, **kwargs):
        raise RuntimeError("STUB_ONLY_NO_TRADING")

    def cancel_order(self, *args, **kwargs):
        raise RuntimeError("STUB_ONLY_NO_TRADING")

    def cancel_all(self, *args, **kwargs):
        raise RuntimeError("STUB_ONLY_NO_TRADING")

    def get_orderbook(self, ticker: str, depth: int = 10) -> Dict[str, Any]:
        return {"yes": [], "no": []}

    def get_best_prices(
        self, orderbook: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        yes: List[List[float]] = orderbook.get("yes") or []
        no: List[List[float]] = orderbook.get("no") or []

        yes_bid = max((row[0] for row in yes if row), default=None)
        yes_ask = min((row[0] for row in yes if row), default=None)
        no_bid = max((row[0] for row in no if row), default=None)
        no_ask = min((row[0] for row in no if row), default=None)
        return yes_bid, yes_ask, no_bid, no_ask
