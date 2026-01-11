"""STUB_ONLY: Compatibility shim for SHADOW runner import graph.

Must remain read-only and must not place orders or make authenticated network calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BookTop:
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float]
    no_ask: Optional[float]
    ts_ms: int


@dataclass
class Decision:
    action: str
    reason: str
    side: Optional[str]
    price: Optional[float]
    size: Optional[float]
    implied_yes: Optional[float]
    implied_no: Optional[float]
    fair_up_prob: Optional[float]
    edge_yes: Optional[float]
    edge_no: Optional[float]
    params_hash: str
    cancel_all: bool = False
    edge_gross_bps: Optional[float] = None
    edge_net_bps: Optional[float] = None
    spread_bps: Optional[float] = None
    depth_total: Optional[float] = None
    regime: str = ""
    filter_reason: str = ""
    microstructure_flags: List[str] = field(default_factory=list)


class StaleEdgeStrategy:
    def __init__(self, rules, eligibility=None) -> None:
        self.rules = rules
        self.eligibility = eligibility

    def evaluate_market(self, snapshot: dict) -> Decision:
        yes_bid = snapshot.get("pm_yes_bid")
        yes_ask = snapshot.get("pm_yes_ask")
        implied_yes = None
        implied_no = None
        if yes_bid is not None and yes_ask is not None:
            implied_yes = (yes_bid + yes_ask) / 2.0
            implied_no = 100.0 - implied_yes
        reason = "NO_DATA" if implied_yes is None else "NO_EDGE"
        return Decision(
            action="NO_TRADE",
            reason=reason,
            side=None,
            price=None,
            size=None,
            implied_yes=implied_yes,
            implied_no=implied_no,
            fair_up_prob=(implied_yes / 100.0) if implied_yes is not None else None,
            edge_yes=0.0 if implied_yes is not None else None,
            edge_no=0.0 if implied_no is not None else None,
            edge_gross_bps=0.0,
            edge_net_bps=0.0,
            spread_bps=snapshot.get("spread_bps"),
            depth_total=snapshot.get("depth_total"),
            regime="STUB",
            params_hash="",
            cancel_all=False,
            filter_reason="",
            microstructure_flags=[],
        )

    def evaluate(
        self,
        market_id: str,
        official_mid: Optional[float],
        official_ts_ms: Optional[int],
        book: BookTop,
        market_end_ts_ms: int,
        now_ts_ms: int,
    ) -> Decision:
        snapshot = {
            "pm_yes_bid": book.yes_bid,
            "pm_yes_ask": book.yes_ask,
            "spread_bps": None,
            "depth_total": None,
        }
        return self.evaluate_market(snapshot)
