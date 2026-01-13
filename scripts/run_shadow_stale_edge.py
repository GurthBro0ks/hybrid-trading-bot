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

from feeds.router import get_official_price
from recorder.trade_journal import TradeJournal
from risk.rules import ExposureTracker, RateLimiter, RiskRules
from sources.resolution_source import is_unknown, resolution_source_from_metadata
from strategies.reasons import ReasonCode
from strategies.stale_edge import BookTop, Decision, StaleEdgeStrategy
from venuebook.types import BookStatus
from venues.polymarket import fetch_polymarket_venuebook
from venues.kalshi import fetch_kalshi_venuebook
from venues.kalshi_fetch import fetch_market
from eligibility.kalshi_rules import check_kalshi_eligibility, is_market_open, EligibilityResult


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
                reason=ReasonCode.RATE_LIMIT,
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
                reason=ReasonCode.CANCEL_RATE_LIMIT,
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
            reason=ReasonCode.EXPOSURE_CAP,
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
    parser.add_argument("--mode", choices=["live", "sim"], default="live")
    parser.add_argument("--loop-interval-sec", type=float, default=1.0)
    parser.add_argument("--venue", choices=["polymarket", "kalshi"], default=None)
    parser.add_argument("--market", dest="market_id_cli", default=None)
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
    parser.add_argument("--fixture-meta", help="Path to market metadata json fixture")
    parser.add_argument("--fixture-book", help="Path to orderbook json fixture")
    args = parser.parse_args()

    market_id = args.market_id_cli or args.market_id

    # Mocking if fixtures provided (Copied from smoke_kalshi_book.py)
    if args.fixture_meta or args.fixture_book:
        import json
        from unittest.mock import MagicMock, patch
        
        def mock_get(url, **kwargs):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            # Order matters: check orderbook first to avoid 'markets' substring collision
            if "orderbook" in url and args.fixture_book:
                with open(args.fixture_book) as f:
                    data = json.load(f)
                mock_resp.json.return_value = data
            elif "markets" in url and args.fixture_meta:
                with open(args.fixture_meta) as f:
                    data = json.load(f)
                mock_resp.json.return_value = {"market": data}
            else:
                mock_resp.status_code = 404
            return mock_resp

        p = patch("requests.get", side_effect=mock_get)
        p.start()
        logger.info("Running with FIXTURES (requests.get mocked)")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    rules = RiskRules.from_env()
    strategy = StaleEdgeStrategy(rules)
    journal = TradeJournal(args.output)
    order_limiter = RateLimiter(rules.max_orders_per_min)
    cancel_limiter = RateLimiter(rules.max_cancel_replace_per_min)
    exposure = ExposureTracker()

    # Metadata & Eligibility
    source = None
    market_close_ts = None
    
    if args.venue == "kalshi":
        # 1. Fetch Metadata
        try:
            meta = fetch_market(market_id)
            # 2. Check Eligibility
            res, src_res = check_kalshi_eligibility(meta)
            if res != EligibilityResult.ELIGIBLE:
                logger.error(f"KALSHI_NOT_ELIGIBLE: {res.name}")
                return 1
            if src_res is None:
                logger.error("KALSHI_RESOLUTION_SOURCE_UNKNOWN")
                return 1
            source = src_res
            
            # Parse close time for time gating
            try:
                ct_str = meta.get("close_time", "")
                if ct_str.endswith('Z'):
                    ct_str = ct_str[:-1] + '+00:00'
                from datetime import datetime
                market_close_ts = datetime.fromisoformat(ct_str).timestamp()
            except Exception:
                logger.error("KALSHI_CLOSE_TIME_PARSE_ERROR")
                return 1
                
        except Exception as e:
            logger.error(f"KALSHI_METADATA_FETCH_FAILED: {e}")
            return 1
    else:
        # Polymarket / Default fallback
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
        source_name = "NONE"

        # Time Gating (Kalshi only for now, or generic if we had close ts for PM)
        if args.venue == "kalshi" and market_close_ts is not None:
             if not is_market_open(now_ms/1000.0, market_close_ts):
                 logger.info("MARKET_CLOSED")
                 # We can either break or just record decision MARKET_CLOSED
                 # For shadow runner, maybe just log and wait? 
                 # Or treat as NO_TRADE.
                 pass

        if not is_unknown(source) and not args.force_feed_failure:
            feed = get_official_price(symbol_pair=source.symbol)
            if feed:
                official_mid, official_ts_ms, _, source_name = feed
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
        mock_used = False
        book = None
        book_source = "NONE"
        book_latency_ms = None
        book_http_status = None
        book_missing_reason = None

        if args.mode == "sim":
            book_source = "mock"
            book = _simulate_polymarket_book(
                fair_prob=fair_hint,
                now_ms=now_ms,
                spread=args.book_spread,
                bias=args.book_bias,
            )
            mock_used = True
        else:
            # LIVE MODE: prohibit mocks.
            if args.venue == "kalshi":
                if market_close_ts is not None and not is_market_open(now_ms/1000.0, market_close_ts):
                    book_missing_reason = "MARKET_CLOSED"
                else:
                    book_source = "kalshi"
                    t0 = time.time()
                    try:
                        vbook = fetch_kalshi_venuebook(market_id)
                        book_latency_ms = int((time.time() - t0) * 1000)
                        book_http_status = 200 if vbook.status == BookStatus.OK else None
                        
                        if vbook.status == BookStatus.OK:
                            # VenueBook to BookTop
                            # Kalshi is naturally YES/NO binary.
                            book = BookTop(
                                yes_bid=vbook.best_bid,
                                yes_ask=vbook.best_ask,
                                no_bid=None,
                                no_ask=None,
                                ts_ms=now_ms
                            )
                            # Derive implicit sides (Kalshi usually gives both, but BookTop struct is weird)
                            # We'll fill what we have.
                            # Actually, Kalshi VenueBook should have NO side if it's there.
                            # But VenueBook types only has best_bid/best_ask which are typically for the primary contract (YES).
                            # If we want NO prices, we need to check if VenueBook supports it.
                            # Looking at venues/kalshi_fetch.py and venues/kalshi.py...
                            # venues/kalshi.py parse_kalshi_book returns best_bid/best_ask from YES side (or derived from NO).
                            # It doesn't explicitly return NO side prices in the top level fields.
                            # So we do strict complement 1 - yes.
                            if book.yes_bid is not None:
                                book.no_ask = 1.0 - book.yes_bid
                            if book.yes_ask is not None:
                                book.no_bid = 1.0 - book.yes_ask
                        else:
                            book_missing_reason = (
                                vbook.fail_reason.name if vbook.fail_reason is not None else "UNKNOWN"
                            )
                            logger.error(f"BOOK_FETCH_FAILED: {book_missing_reason}")
                            
                    except Exception as e:
                        book_missing_reason = "PARSE_ERROR"
                        logger.error(f"BOOK_PARSE_FAILED: {str(e)}")

            elif args.venue == "polymarket":
                book_source = "polymarket"
                t0 = time.time()
                try:
                    vbook = fetch_polymarket_venuebook(market_id)
                    book_latency_ms = int((time.time() - t0) * 1000)
                    book_http_status = 200 if vbook.status == BookStatus.OK else None

                    if vbook.status == BookStatus.OK:
                        # Convert VenueBook to legacy BookTop for strategy compatibility
                        book = BookTop(
                            yes_bid=vbook.best_bid,
                            yes_ask=vbook.best_ask,
                            no_bid=None,  # Polymarket CLOB is one-sided (YES token)
                            no_ask=None,
                            ts_ms=now_ms,
                        )
                        # Fix for BookTop: it needs no_bid/no_ask to not crash strategy
                        # If it's a binary market, we can derive them if we know which side the token is.
                        # Assuming market_id is the token for YES.
                        if book.yes_bid is not None:
                            book.no_ask = 1.0 - book.yes_bid
                        if book.yes_ask is not None:
                            book.no_bid = 1.0 - book.yes_ask
                    else:
                        book_missing_reason = (
                            vbook.fail_reason.name if vbook.fail_reason is not None else "UNKNOWN"
                        )
                        logger.error(f"BOOK_FETCH_FAILED: {book_missing_reason}")

                except Exception as e:
                    book_missing_reason = "PARSE_ERROR"
                    logger.error(f"BOOK_PARSE_FAILED: {str(e)}")
            else:
                book_missing_reason = "NO_CONFIG"
                mock_used = False

        if is_unknown(source):
            decision = Decision(
                action="NO_TRADE",
                reason=ReasonCode.RESOLUTION_SOURCE_UNKNOWN,
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
                reason=ReasonCode.FEED_STALE_ABORT,
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
        elif book is None:
            decision = Decision(
                action="NO_TRADE",
                reason=ReasonCode.BOOK_DATA_MISSING,
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
                market_id=market_id,
                official_mid=official_mid,
                official_ts_ms=official_ts_ms,
                book=book,
                market_end_ts_ms=market_end_ts_ms,
                now_ts_ms=now_ms,
            )

        decision = _apply_rate_limits(decision, now_ms, order_limiter, cancel_limiter)
        decision = _apply_exposure_cap(decision, market_id, exposure, rules)

        if decision.cancel_all:
            exposure.reset_market(market_id)

        total_decisions += 1
        if decision.action == "PLACE_ORDER":
            would_trade += 1
            edge = max(decision.edge_yes or 0.0, decision.edge_no or 0.0)
            edge_sum += edge
            edge_count += 1
        if decision.reason in {ReasonCode.STALE_FEED, ReasonCode.STALE_BOOK, ReasonCode.OFFICIAL_FEED_MISSING, ReasonCode.FEED_STALE_ABORT}:
            staleness_refusals += 1
        if decision.reason == ReasonCode.END_TIME_ANOMALY:
            end_time_anomalies += 1

        official_age_ms = now_ms - official_ts_ms if official_ts_ms is not None else ""
        book_age_ms = now_ms - book.ts_ms if book is not None and book.ts_ms is not None else ""

        journal.record_decision(
            {
                "ts": now_ms,
                "market_id": market_id,
                "now": now_ms,
                "market_end_ts": market_end_ts_ms,
                "official_mid": official_mid or "",
                "official_source": source_name,
                "official_age_ms": official_age_ms,
                "book_source": book_source,
                "book_latency_ms": book_latency_ms or "",
                "book_http_status": book_http_status or "",
                "book_missing_reason": book_missing_reason or "",
                "yes_bid": book.yes_bid if book else "",
                "yes_ask": book.yes_ask if book else "",
                "no_bid": book.no_bid if book else "",
                "no_ask": book.no_ask if book else "",
                "book_age_ms": book_age_ms if book else "",
                "mock_used": str(mock_used).lower(),
                "implied_yes": decision.implied_yes or "",
                "implied_no": decision.implied_no or "",
                "fair_up_prob": decision.fair_up_prob or "",
                "edge_yes": decision.edge_yes or "",
                "edge_no": decision.edge_no or "",
                "action": decision.action,
                "reason": decision.reason,
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
