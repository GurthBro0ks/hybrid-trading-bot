"""Stale-edge strategy: fair-value vs implied odds with staleness gates."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
from typing import Deque, Optional

from risk.rules import RiskRules


@dataclass
class BookTop:
    yes_bid: Optional[float]
    yes_ask: Optional[float]
    no_bid: Optional[float]
    no_ask: Optional[float]
    ts_ms: int
    yes_bid_qty: Optional[float] = None
    yes_ask_qty: Optional[float] = None
    no_bid_qty: Optional[float] = None
    no_ask_qty: Optional[float] = None


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
    thin_book_reason: Optional[str] = None
    thin_book_threshold_depth_usd: Optional[float] = None
    thin_book_threshold_qty: Optional[float] = None
    thin_book_spread_bps: Optional[float] = None
    cancel_all: bool = False


class RollingReturnModel:
    def __init__(self, horizon_sec: int, warmup_samples: int, max_returns: int = 1000) -> None:
        self.horizon_ms = horizon_sec * 1000
        self.warmup_samples = warmup_samples
        self.max_returns = max_returns
        self.prices: Deque[tuple[int, float]] = deque()
        self.returns: Deque[float] = deque()

    def update(self, ts_ms: int, price: float) -> None:
        self.prices.append((ts_ms, price))
        cutoff = ts_ms - (self.horizon_ms * 2)
        while self.prices and self.prices[0][0] < cutoff:
            self.prices.popleft()

        target_ts = ts_ms - self.horizon_ms
        ref_price = None
        for sample_ts, sample_price in reversed(self.prices):
            if sample_ts <= target_ts:
                ref_price = sample_price
                break
        if ref_price is not None and ref_price > 0:
            ret = (price - ref_price) / ref_price
            self.returns.append(ret)
            while len(self.returns) > self.max_returns:
                self.returns.popleft()

    def fair_up_prob(self) -> Optional[float]:
        if len(self.returns) < self.warmup_samples:
            return None
        up = sum(1 for r in self.returns if r > 0)
        return up / len(self.returns) if self.returns else None


class StaleEdgeStrategy:
    def __init__(self, rules: RiskRules) -> None:
        self.rules = rules
        self.model = RollingReturnModel(
            horizon_sec=rules.model_horizon_sec,
            warmup_samples=rules.model_warmup_samples,
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
        if now_ts_ms >= market_end_ts_ms:
            return Decision(
                action="CANCEL_REPLACE",
                reason="END_TIME_ANOMALY",
                side=None,
                price=None,
                size=None,
                implied_yes=None,
                implied_no=None,
                fair_up_prob=None,
                edge_yes=None,
                edge_no=None,
                params_hash="",
                cancel_all=True,
            )

        if market_end_ts_ms - now_ts_ms < self.rules.time_to_end_cutoff_sec * 1000:
            return self._no_trade("TIME_TO_END_CUTOFF")

        if official_mid is None or official_ts_ms is None:
            return self._no_trade("OFFICIAL_FEED_MISSING")

        if now_ts_ms - official_ts_ms > self.rules.official_stale_sec * 1000:
            return self._no_trade("STALE_FEED")

        if now_ts_ms - book.ts_ms > self.rules.book_stale_sec * 1000:
            return self._no_trade("STALE_BOOK")

        # Thin Book Checks
        if all(
            x is None for x in [book.yes_bid, book.yes_ask, book.no_bid, book.no_ask]
        ):
            return self._no_trade("THIN_BOOK", thin_book_reason="NO_BBO")

        if (book.yes_bid is None or book.yes_ask is None) or (
            book.no_bid is None or book.no_ask is None
        ):
            return self._no_trade("THIN_BOOK", thin_book_reason="ONE_SIDED")

        # Check Depth
        min_usd = self.rules.thin_book_threshold_depth_usd
        min_qty = self.rules.thin_book_threshold_qty

        # Verify all four sides meet depth
        # Note: If prices are None, caught by ONE_SIDED above, so here they are not None.
        # But qty might be None if caller didn't supply it. Assume 0 if None.
        def _bad_depth(price: Optional[float], qty: Optional[float]) -> bool:
            if price is None: return False # Should not happen here
            q = qty if qty is not None else 0.0
            if q < min_qty: return True
            if price * q < min_usd: return True
            return False

        if (
            _bad_depth(book.yes_bid, book.yes_bid_qty)
            or _bad_depth(book.yes_ask, book.yes_ask_qty)
            or _bad_depth(book.no_bid, book.no_bid_qty)
            or _bad_depth(book.no_ask, book.no_ask_qty)
        ):
            return self._no_trade(
                "THIN_BOOK",
                thin_book_reason="DEPTH_BELOW_THRESHOLD",
                thin_book_threshold_depth_usd=min_usd,
                thin_book_threshold_qty=min_qty,
            )

        yes_spread = self._spread(book.yes_bid, book.yes_ask)
        no_spread = self._spread(book.no_bid, book.no_ask)
        max_spread = self.rules.spread_max
        
        # Calculate max spread encountered in bps
        # If None, treat as infinite? But checked by ONE_SIDED.
        curr_spread = max(yes_spread or 0.0, no_spread or 0.0)
        
        if (yes_spread is not None and yes_spread > max_spread) or (
            no_spread is not None and no_spread > max_spread
        ):
            return self._no_trade(
                "THIN_BOOK",
                thin_book_reason="SPREAD_WIDE",
                thin_book_spread_bps=curr_spread * 10000,
            )

        self.model.update(official_ts_ms, official_mid)
        fair_up_prob = self.model.fair_up_prob()
        if fair_up_prob is None:
            return self._no_trade("MODEL_WARMUP")

        implied_yes = self._entry_implied(book.yes_bid, book.yes_ask)
        implied_no = self._entry_implied(book.no_bid, book.no_ask)
        if implied_yes is None or implied_no is None:
            return self._no_trade("BOOK_INCOMPLETE")

        edge_yes = fair_up_prob - implied_yes
        edge_no = (1.0 - fair_up_prob) - implied_no
        edge_min = self.rules.edge_min()

        yes_spread = self._spread(book.yes_bid, book.yes_ask)
        no_spread = self._spread(book.no_bid, book.no_ask)

        chosen_side = None
        price = None
        edge = None
        spread_ok = False

        if edge_yes >= edge_no and edge_yes > edge_min:
            chosen_side = "YES"
            price = book.yes_ask
            edge = edge_yes
            spread_ok = yes_spread is not None and yes_spread <= self.rules.spread_max
        elif edge_no > edge_min:
            chosen_side = "NO"
            price = book.no_ask
            edge = edge_no
            spread_ok = no_spread is not None and no_spread <= self.rules.spread_max

        if chosen_side is None or price is None or edge is None or not spread_ok:
            return Decision(
                action="NO_TRADE",
                reason="EDGE_TOO_SMALL",
                side=None,
                price=None,
                size=None,
                implied_yes=implied_yes,
                implied_no=implied_no,
                fair_up_prob=fair_up_prob,
                edge_yes=edge_yes,
                edge_no=edge_no,
                params_hash="",
            )

        size = self.rules.min_trade_usd
        params_hash = _params_hash(market_id, chosen_side, price, size)
        return Decision(
            action="PLACE_ORDER",
            reason="EDGE_OK",
            side=chosen_side,
            price=price,
            size=size,
            implied_yes=implied_yes,
            implied_no=implied_no,
            fair_up_prob=fair_up_prob,
            edge_yes=edge_yes,
            edge_no=edge_no,
            params_hash=params_hash,
        )

    def _no_trade(
        self,
        reason: str,
        thin_book_reason: Optional[str] = None,
        thin_book_threshold_depth_usd: Optional[float] = None,
        thin_book_threshold_qty: Optional[float] = None,
        thin_book_spread_bps: Optional[float] = None,
    ) -> Decision:
        return Decision(
            action="NO_TRADE",
            reason=reason,
            side=None,
            price=None,
            size=None,
            implied_yes=None,
            implied_no=None,
            fair_up_prob=None,
            edge_yes=None,
            edge_no=None,
            params_hash="",
            thin_book_reason=thin_book_reason,
            thin_book_threshold_depth_usd=thin_book_threshold_depth_usd,
            thin_book_threshold_qty=thin_book_threshold_qty,
            thin_book_spread_bps=thin_book_spread_bps,
        )

    @staticmethod
    def _entry_implied(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
        if ask is not None:
            return ask
        if bid is not None:
            return bid
        return None

    @staticmethod
    def _spread(bid: Optional[float], ask: Optional[float]) -> Optional[float]:
        if bid is None or ask is None:
            return None
        return max(0.0, ask - bid)


def _params_hash(market_id: str, side: str, price: float, size: float) -> str:
    raw = f"{market_id}:{side}:{price:.6f}:{size:.4f}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
