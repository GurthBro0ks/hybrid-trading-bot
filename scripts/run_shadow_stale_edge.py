#!/usr/bin/env python3
"""Shadow runner for stale-edge strategy (no trades)."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feeds.binance_spot import get_mid_price
from recorder.trade_journal import TradeJournal
from risk.rules import ExposureTracker, RateLimiter, RiskRules
from sources.resolution_source import is_unknown, resolution_source_from_metadata
from strategies.stale_edge import BookTop, Decision, StaleEdgeStrategy


logger = logging.getLogger("stale_edge_shadow")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _simulate_polymarket_book(
    fair_prob: float,
    now_ms: int,
    spread: float,
    bias: float,
) -> BookTop:
    mid = min(max(fair_prob + bias, 0.02), 0.98)
    yes_bid = max(0.01, mid - spread / 2)
    yes_ask = min(0.99, mid + spread / 2)
    no_bid = max(0.01, 1.0 - yes_ask)
    no_ask = min(0.99, 1.0 - yes_bid)
    return BookTop(
        yes_bid=yes_bid,
        yes_ask=yes_ask,
        no_bid=no_bid,
        no_ask=no_ask,
        yes_bid_qty=1000.0,
        yes_ask_qty=1000.0,
        no_bid_qty=1000.0,
        no_ask_qty=1000.0,
        ts_ms=now_ms,
    )


def _apply_rate_limits(
    decision: Decision,
    now_ms: int,
    order_limiter: RateLimiter,
    cancel_limiter: RateLimiter,
) -> Decision:
    if decision.action == "PLACE_ORDER":
        if not order_limiter.allow(now_ms):
            return Decision(
                action="NO_TRADE",
                reason="RATE_LIMIT",
                side=None,
                price=None,
                size=None,
                implied_yes=decision.implied_yes,
                implied_no=decision.implied_no,
                fair_up_prob=decision.fair_up_prob,
                edge_yes=decision.edge_yes,
                edge_no=decision.edge_no,
                params_hash="",
            )
    if decision.cancel_all:
        if not cancel_limiter.allow(now_ms):
            return Decision(
                action="NO_TRADE",
                reason="CANCEL_RATE_LIMIT",
                side=None,
                price=None,
                size=None,
                implied_yes=decision.implied_yes,
                implied_no=decision.implied_no,
                fair_up_prob=decision.fair_up_prob,
                edge_yes=decision.edge_yes,
                edge_no=decision.edge_no,
                params_hash="",
            )
    return decision


def _apply_exposure_cap(
    decision: Decision, market_id: str, exposure: ExposureTracker, rules: RiskRules
) -> Decision:
    if decision.action != "PLACE_ORDER" or decision.size is None:
        return decision
    if not exposure.can_add(market_id, decision.size, rules):
        return Decision(
            action="NO_TRADE",
            reason="EXPOSURE_CAP",
            side=None,
            price=None,
            size=None,
            implied_yes=decision.implied_yes,
            implied_no=decision.implied_no,
            fair_up_prob=decision.fair_up_prob,
            edge_yes=decision.edge_yes,
            edge_no=decision.edge_no,
            params_hash="",
        )
    exposure.add(market_id, decision.size)
    return decision


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=1)
    parser.add_argument("--loop-interval-sec", type=float, default=1.0)
    parser.add_argument("--market-id", default="pm-demo-market")
    parser.add_argument(
        "--rules-text",
        default="Resolved by Binance BTC/USDT spot price",
    )
    parser.add_argument("--market-end-ts", type=int, default=0)
    parser.add_argument("--force-feed-failure", action="store_true")
    parser.add_argument("--book-spread", type=float, default=0.02)
    parser.add_argument("--book-bias", type=float, default=-0.03)
    parser.add_argument(
        "--output",
        default="data/flight_recorder/stale_edge_decisions.csv",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    rules = RiskRules.from_env()
    strategy = StaleEdgeStrategy(rules)
    journal = TradeJournal(args.output)
    order_limiter = RateLimiter(rules.max_orders_per_min)
    cancel_limiter = RateLimiter(rules.max_cancel_replace_per_min)
    exposure = ExposureTracker()

    metadata = {"rules_text": args.rules_text}
    source = resolution_source_from_metadata(metadata)
    if is_unknown(source):
        logger.error("RESOLUTION_SOURCE_UNKNOWN")

    market_end_ts_ms = (
        args.market_end_ts * 1000
        if args.market_end_ts > 0
        else _now_ms() + 60 * 60 * 1000
    )

    start = time.time()
    duration_sec = args.minutes * 60
    total_decisions = 0
    would_trade = 0
    edge_sum = 0.0
    edge_count = 0
    staleness_refusals = 0
    end_time_anomalies = 0
    feed_abort = False
    last_official_ok_ms = None
    start_ms = _now_ms()

    while time.time() - start < duration_sec:
        now_ms = _now_ms()
        official_mid = None
        official_ts_ms = None

        if not is_unknown(source) and not args.force_feed_failure:
            feed = get_mid_price(symbol=source.symbol.replace("/", ""))
            if feed:
                official_mid, official_ts_ms, _ = feed
                last_official_ok_ms = now_ms
            else:
                logger.warning("OFFICIAL_FEED_UNAVAILABLE")
        elif args.force_feed_failure:
            logger.warning("OFFICIAL_FEED_FORCED_FAILURE")

        if last_official_ok_ms is not None:
            if now_ms - last_official_ok_ms > rules.feed_stale_abort_sec * 1000:
                feed_abort = True
        else:
            if now_ms - start_ms > rules.feed_stale_abort_sec * 1000:
                feed_abort = True

        fair_hint = strategy.model.fair_up_prob() or 0.5
        book = _simulate_polymarket_book(
            fair_prob=fair_hint,
            now_ms=now_ms,
            spread=args.book_spread,
            bias=args.book_bias,
        )

        if is_unknown(source):
            decision = Decision(
                action="NO_TRADE",
                reason="RESOLUTION_SOURCE_UNKNOWN",
                side=None,
                price=None,
                size=None,
                implied_yes=None,
                implied_no=None,
                fair_up_prob=None,
                edge_yes=None,
                edge_no=None,
                params_hash="",
            )
        elif feed_abort:
            decision = Decision(
                action="NO_TRADE",
                reason="FEED_STALE_ABORT",
                side=None,
                price=None,
                size=None,
                implied_yes=None,
                implied_no=None,
                fair_up_prob=None,
                edge_yes=None,
                edge_no=None,
                params_hash="",
            )
        else:
            decision = strategy.evaluate(
                market_id=args.market_id,
                official_mid=official_mid,
                official_ts_ms=official_ts_ms,
                book=book,
                market_end_ts_ms=market_end_ts_ms,
                now_ts_ms=now_ms,
            )

        decision = _apply_rate_limits(decision, now_ms, order_limiter, cancel_limiter)
        decision = _apply_exposure_cap(decision, args.market_id, exposure, rules)

        if decision.cancel_all:
            exposure.reset_market(args.market_id)

        total_decisions += 1
        if decision.action == "PLACE_ORDER":
            would_trade += 1
            edge = max(decision.edge_yes or 0.0, decision.edge_no or 0.0)
            edge_sum += edge
            edge_count += 1
        if decision.reason in {"STALE_FEED", "STALE_BOOK", "OFFICIAL_FEED_MISSING", "FEED_STALE_ABORT"}:
            staleness_refusals += 1
        if decision.reason == "END_TIME_ANOMALY":
            end_time_anomalies += 1

        official_age_ms = now_ms - official_ts_ms if official_ts_ms is not None else ""
        book_age_ms = now_ms - book.ts_ms if book.ts_ms is not None else ""

        journal.record_decision(
            {
                "ts": now_ms,
                "market_id": args.market_id,
                "now": now_ms,
                "market_end_ts": market_end_ts_ms,
                "official_mid": official_mid or "",
                "official_age_ms": official_age_ms,
                "pm_yes_bid": book.yes_bid,
                "pm_yes_ask": book.yes_ask,
                "pm_no_bid": book.no_bid,
                "pm_no_ask": book.no_ask,
                "pm_book_age_ms": book_age_ms,
                "implied_yes": decision.implied_yes or "",
                "implied_no": decision.implied_no or "",
                "fair_up_prob": decision.fair_up_prob or "",
                "edge_yes": decision.edge_yes or "",
                "edge_no": decision.edge_no or "",
                "action": decision.action,
                "reason": decision.reason,
                "thin_book_reason": decision.thin_book_reason or "",
                "thin_book_threshold_depth_usd": decision.thin_book_threshold_depth_usd or "",
                "thin_book_threshold_qty": decision.thin_book_threshold_qty or "",
                "thin_book_spread_bps": decision.thin_book_spread_bps or "",
                "params_hash": decision.params_hash,
            }
        )

        time.sleep(args.loop_interval_sec)

    avg_edge = (edge_sum / edge_count) if edge_count else 0.0
    logger.info(
        "summary decisions=%s would_trades=%s avg_edge=%.4f staleness_refusals=%s end_time_anomalies=%s",
        total_decisions,
        would_trade,
        avg_edge,
        staleness_refusals,
        end_time_anomalies,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
