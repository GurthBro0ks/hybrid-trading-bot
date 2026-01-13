#!/usr/bin/env python3
"""Enhanced shadow runner with signal integration and PnL accounting."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recorder.trade_journal import TradeJournal
from risk.eligibility import EligibilityGate
from risk.rules import ExposureTracker, RateLimiter, RiskRules
from strategies.stale_edge import BookTop, Decision, StaleEdgeStrategy

# Import signal modules (fall back to no-op stubs if unavailable)
try:
    from signals.base import SignalResult
    from signals.book_arbitrage import BookArbitrageSignal
    from signals.book_staleness import BookStalenessSignal
    _signals_import_error = None
except Exception as exc:
    _signals_import_error = exc

    class SignalResult:
        def __init__(
            self,
            reason: str,
            name: str,
            edge_gross_bps: float = 0.0,
            confidence: float = 0.0,
            extras: Optional[Dict[str, Any]] = None,
        ) -> None:
            self.reason = reason
            self.name = name
            self.edge_gross_bps = edge_gross_bps
            self.confidence = confidence
            self.extras = extras or {}
            self.timestamp = time.time()

        @classmethod
        def no_trade(cls, reason: str, name: str, extras: Optional[Dict[str, Any]] = None) -> "SignalResult":
            return cls(reason=reason, name=name, edge_gross_bps=0.0, confidence=0.0, extras=extras)

    class BookArbitrageSignal:
        def analyze(self, orderbook, market_data) -> "SignalResult":
            return SignalResult.no_trade(
                "SIGNAL_UNAVAILABLE",
                "book_arbitrage",
                {"error": str(_signals_import_error)},
            )

    class BookStalenessSignal:
        def analyze(self, orderbook, market_data) -> "SignalResult":
            return SignalResult.no_trade(
                "SIGNAL_UNAVAILABLE",
                "book_staleness",
                {"error": str(_signals_import_error)},
            )

# For Kalshi support (fall back to stub if unavailable)
try:
    from venues.kalshi import KalshiVenue
    _kalshi_import_error = None
except Exception as exc:
    _kalshi_import_error = exc

    class KalshiVenue:
        def __init__(self, env: str = "prod") -> None:
            self.env = env

        def get_orderbook(self, ticker: str, depth: int = 10) -> Dict[str, Any]:
            return {"error": f"KALSHI_UNAVAILABLE: {_kalshi_import_error}"}

        def get_best_prices(
            self, orderbook: Dict[str, Any]
        ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
            return None, None, None, None

# Shadow artifacts writer
from recorder.shadow_artifacts import write_shadow_artifacts, sanitize_text
from recorder.journal_schema import JOURNAL_COLUMNS


logger = logging.getLogger("stale_edge_shadow")


@dataclass
class VirtualPosition:
    daily_pnl: float = 0.0
    daily_loss: float = 0.0
    total_loss: float = 0.0
    size: float = 0.0
    avg_price: float = 0.0


@dataclass
class PnlState:
    daily_pnl: float = 0.0
    daily_loss: float = 0.0
    total_loss: float = 0.0
    open_markets: int = 0


def _normalize_decision(decision: Decision, source: Optional[Decision] = None, filter_reason: str = "") -> Decision:
    """Ensure decision has expected attributes across strategy versions."""
    if not hasattr(decision, "edge_gross_bps"):
        setattr(decision, "edge_gross_bps", getattr(source, "edge_gross_bps", None))
    if not hasattr(decision, "edge_net_bps"):
        setattr(decision, "edge_net_bps", getattr(source, "edge_net_bps", None))
    if not hasattr(decision, "spread_bps"):
        setattr(decision, "spread_bps", getattr(source, "spread_bps", None))
    if not hasattr(decision, "depth_total"):
        setattr(decision, "depth_total", getattr(source, "depth_total", None))
    if not hasattr(decision, "regime"):
        setattr(decision, "regime", getattr(source, "regime", ""))
    if not hasattr(decision, "filter_reason"):
        setattr(decision, "filter_reason", filter_reason or getattr(source, "filter_reason", ""))
    if not hasattr(decision, "microstructure_flags"):
        setattr(decision, "microstructure_flags", list(getattr(source, "microstructure_flags", [])))
    if not hasattr(decision, "cancel_all"):
        setattr(decision, "cancel_all", getattr(source, "cancel_all", False))
    if not hasattr(decision, "params_hash"):
        setattr(decision, "params_hash", getattr(source, "params_hash", ""))
    return decision


def _now_ms() -> int:
    return int(time.time() * 1000)


def _no_trade_from(decision: Decision, reason: str) -> Decision:
    return _normalize_decision(
        Decision(
            action="NO_TRADE",
            reason=reason,
            side=None,
            price=None,
            size=None,
            implied_yes=getattr(decision, "implied_yes", None),
            implied_no=getattr(decision, "implied_no", None),
            fair_up_prob=getattr(decision, "fair_up_prob", None),
            edge_yes=getattr(decision, "edge_yes", None),
            edge_no=getattr(decision, "edge_no", None),
            params_hash=getattr(decision, "params_hash", ""),
            cancel_all=False,
        ),
        source=decision,
        filter_reason=reason,
    )


def _apply_rate_limits(
    decision: Decision,
    now_ms: int,
    order_limiter: RateLimiter,
    cancel_limiter: RateLimiter,
) -> Decision:
    if decision.action == "PLACE_ORDER":
        if not order_limiter.allow(now_ms):
            return _no_trade_from(decision, "RATE_LIMIT")
    if decision.cancel_all:
        if not cancel_limiter.allow(now_ms):
            return _no_trade_from(decision, "CANCEL_RATE_LIMIT")
    return decision


def get_kalshi_market_data(ticker: str, venue) -> Tuple[Optional[float], Optional[float], float, int, Dict[str, Any]]:
    """Get enhanced orderbook data from Kalshi venue."""
    try:
        orderbook = venue.get_orderbook(ticker)
        if "error" in orderbook:
            return None, None, 0.0, 0, {}
        
        yes_bid, yes_ask, no_bid, no_ask = venue.get_best_prices(orderbook)
        
        # Calculate spread and depth
        spread_bps = None
        if yes_bid is not None and yes_ask is not None:
            spread_bps = (yes_ask - yes_bid) * 10000 / yes_bid
        
        # Calculate depth from orderbook
        depth_total = 0.0
        if "yes" in orderbook and isinstance(orderbook["yes"], list):
            depth_total = sum(item[1] for item in orderbook["yes"] if len(item) > 1)
        if "no" in orderbook and isinstance(orderbook["no"], list):
            depth_total += sum(item[1] for item in orderbook["no"] if len(item) > 1)
        
        # Return orderbook for signal analysis
        return yes_bid, yes_ask, spread_bps, depth_total, orderbook
        
    except Exception as e:
        logger.warning(f"Failed to get Kalshi market data: {e}")
        return None, None, 0.0, 0, {}


def run_signal_analysis(ticker: str, venue: KalshiVenue, orderbook: Dict[str, Any]) -> Dict[str, SignalResult]:
    """Run all signal analyses on the current orderbook."""
    market_data = {
        'venue': venue,
        'ticker': ticker,
        'timestamp': time.time()
    }
    
    signals = {
        'book_arbitrage': BookArbitrageSignal(),
        'book_staleness': BookStalenessSignal()
    }
    
    results = {}
    for name, signal in signals.items():
        try:
            result = signal.analyze(orderbook, market_data)
            result.timestamp = time.time()
            results[name] = result
        except Exception as e:
            logger.warning(f"Signal {name} failed: {e}")
            results[name] = SignalResult.no_trade(f"SIGNAL_ERROR_{name}", name, {"error": str(e)})
    
    return results


def apply_signal_gates(decision: Decision, signal_results: Dict[str, SignalResult]) -> Tuple[Decision, Dict[str, Any]]:
    """Apply signal-based gating to trading decisions."""
    gate_extras = {}
    
    # Check for shock/staleness signals - these should block trading
    staleness_result = signal_results.get('book_staleness')
    if staleness_result and "SHOCK_DETECTED" in staleness_result.reason:
        decision = _no_trade_from(decision, f"STALENESS_GATE_{staleness_result.reason}")
        gate_extras['staleness_gate'] = staleness_result.extras
    
    # Check arbitrage opportunities - enhance edge calculations
    arb_result = signal_results.get('book_arbitrage')
    if arb_result and arb_result.edge_gross_bps > 0:
        gate_extras['arbitrage_edge'] = {
            'edge_bps': arb_result.edge_gross_bps,
            'confidence': arb_result.confidence,
            'extras': arb_result.extras
        }
        # Could potentially enhance decision edge with arbitrage info
        if decision.action in ("WOULD_ENTER", "WOULD_EXIT") and decision.edge_net_bps is not None:
            # Combine edges or take max depending on strategy
            if decision.edge_gross_bps is None:
                decision.edge_gross_bps = arb_result.edge_gross_bps
            else:
                decision.edge_gross_bps = max(decision.edge_gross_bps, arb_result.edge_gross_bps)
    
    return decision, gate_extras


def calculate_enhanced_pnl(decision: Decision, signal_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate enhanced PnL metrics using signal information."""
    pnl_metrics = {
        'base_edge_bps': decision.edge_net_bps or 0.0,
        'signal_adjusted_edge_bps': decision.edge_net_bps or 0.0,
        'confidence_weighted_edge_bps': 0.0
    }
    
    # Adjust edge based on arbitrage signal
    arb_result = signal_results.get('book_arbitrage')
    if arb_result and arb_result.edge_gross_bps > 0:
        pnl_metrics['signal_adjusted_edge_bps'] = max(
            pnl_metrics['base_edge_bps'], 
            arb_result.edge_gross_bps
        )
        
        # Apply confidence weighting if available
        if arb_result.confidence:
            weight = arb_result.confidence
            pnl_metrics['confidence_weighted_edge_bps'] = (
                pnl_metrics['base_edge_bps'] * (1 - weight) + 
                arb_result.edge_gross_bps * weight
            )
    
    return pnl_metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Enhanced shadow runner with signal integration")
    parser.add_argument("--minutes", type=int, default=1)
    parser.add_argument("--loop-interval-sec", type=float, default=1.0)
    parser.add_argument("--venue", choices=["kalshi"], default="kalshi", help="Trading venue")
    parser.add_argument("--ticker", help="Market ticker (Kalshi)")
    parser.add_argument("--rules-text", help="Rules text")
    parser.add_argument("--market-end-ts", type=int, default=0)
    parser.add_argument("--taker-fee-bps", type=float)
    parser.add_argument("--maker-fee-bps", type=float)
    parser.add_argument("--sim-costs", action="store_true")
    parser.add_argument("--output", default="data/flight_recorder/stale_edge_kalshi_decisions.csv")
    parser.add_argument("--signals", action="store_true", default=True, help="Enable signal analysis")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
    args = parser.parse_args()

    # Validate arguments
    if args.venue == "kalshi" and not args.ticker:
        print("error: --ticker required for kalshi", file=sys.stderr)
        return 2
    if not args.rules_text:
        args.rules_text = "Kalshi market"

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    rules = RiskRules.from_env()
    if args.taker_fee_bps is not None:
        rules.taker_fee_bps = args.taker_fee_bps
    if args.maker_fee_bps is not None:
        rules.maker_fee_bps = args.maker_fee_bps
    if not args.sim_costs:
        rules.taker_fee_bps = 0.0
        rules.maker_fee_bps = 0.0
        rules.slippage_bps = 0.0

    cooldown_sec = getattr(rules, "cooldown_sec", 0)
    eligibility = EligibilityGate(cooldown_sec)
    try:
        strategy = StaleEdgeStrategy(rules, eligibility)
    except TypeError:
        strategy = StaleEdgeStrategy(rules)
    journal = TradeJournal(args.output)
    order_limiter = RateLimiter(rules.max_orders_per_min)
    cancel_limiter = RateLimiter(rules.max_cancel_replace_per_min)
    exposure = ExposureTracker()

    market_end_ts_ms = args.market_end_ts * 1000 if args.market_end_ts > 0 else 0

    # Initialize venue
    kalshi_venue = KalshiVenue(env=os.getenv("KALSHI_ENV", "prod"))

    start = time.time()
    duration_sec = args.minutes * 60
    total_decisions = 0
    would_trade = 0
    edge_sum = 0.0
    edge_count = 0
    reasons = Counter()
    events = Counter()
    positions: Dict[str, VirtualPosition] = {}
    pnl_state = PnlState()
    kill_switch = False
    signal_stats = Counter()
    arbitrage_opportunities = 0

    # Shadow artifact tracking
    start_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    artifact_last_error: Optional[str] = None
    artifact_last_success_at: Optional[str] = None
    journal_rows_for_artifacts: list = []

    print(f"Starting enhanced {args.venue} shadow run for {args.minutes} minutes...")
    print(f"Signal analysis: {'ENABLED' if args.signals else 'DISABLED'}")
    
    while True:
        now_ms = _now_ms()
        now_sec = now_ms / 1000.0
        elapsed = now_sec - start
        
        if elapsed >= duration_sec:
            logger.info(f"Completed {duration_sec} seconds")
            break
        
        # Build market snapshot
        market_snapshot = {
            "now_ms": now_ms,
            "market_end_ts_ms": market_end_ts_ms,
            "market_class": "KALSHI_PREDICTION",
            "required_symbol": "UNKNOWN",
            "rules_end_ts": None,
            "end_ts_source": "VENUE",
        }
        
        # Get enhanced market data
        yes_bid, yes_ask, spread_bps, depth_total, orderbook = get_kalshi_market_data(args.ticker, kalshi_venue)
        
        # Run signal analysis if enabled
        signal_results = {}
        signal_extras = {}
        if args.signals and orderbook:
            signal_results = run_signal_analysis(args.ticker, kalshi_venue, orderbook)
            
            # Track signal statistics
            for signal_name, result in signal_results.items():
                signal_stats[f"{signal_name}_{result.reason}"] += 1
                if result.edge_gross_bps > 0:
                    signal_stats[f"{signal_name}_edge_opportunity"] += 1
            
            # Count arbitrage opportunities
            arb_result = signal_results.get('book_arbitrage')
            if arb_result and "ARBITRAGE_EDGE" in arb_result.reason:
                arbitrage_opportunities += 1
        
        market_snapshot.update({
            "venue": "KALSHI",
            "symbol": args.ticker,
            "pm_yes_bid": yes_bid,
            "pm_yes_ask": yes_ask,
            "pm_no_bid": (100.0 - yes_ask) if yes_ask is not None else None,
            "pm_no_ask": (100.0 - yes_bid) if yes_bid is not None else None,
            "book_ok": yes_bid is not None,
            "book_err": "" if yes_bid is not None else "NO_DATA",
            "pm_book_age_ms": 0,
            "spread_bps": spread_bps or 0.0,
            "depth_total": depth_total,
            
            # Kalshi-specific fields
            "official_required_venue": "KALSHI",
            "official_used_venue": "KALSHI", 
            "official_used_endpoint": "API",
            "official_mid": None,
            "official_ok": False,
            "official_err": "SELF_REFERENTIAL",
            "official_age_ms": 0,
        })

        # Run strategy
        try:
            if hasattr(strategy, "evaluate_market"):
                decision = strategy.evaluate_market(market_snapshot)
            else:
                no_bid = (100.0 - yes_ask) if yes_ask is not None else None
                no_ask = (100.0 - yes_bid) if yes_bid is not None else None
                book = BookTop(
                    yes_bid=yes_bid,
                    yes_ask=yes_ask,
                    no_bid=no_bid,
                    no_ask=no_ask,
                    ts_ms=now_ms,
                )
                decision = strategy.evaluate(
                    market_id=args.ticker,
                    official_mid=None,
                    official_ts_ms=None,
                    book=book,
                    market_end_ts_ms=market_end_ts_ms,
                    now_ts_ms=now_ms,
                )
            decision = _normalize_decision(decision)
        except Exception as e:
            logger.error(f"Strategy evaluation failed: {e}")
            decision = _normalize_decision(
                Decision(
                    action="NO_TRADE",
                    reason="STRATEGY_ERROR",
                    side=None,
                    price=None,
                    size=None,
                    implied_yes=None,
                    implied_no=None,
                    fair_up_prob=None,
                    edge_yes=None,
                    edge_no=None,
                    params_hash="",
                    cancel_all=False,
                ),
                filter_reason="STRATEGY_ERROR",
            )
        
        # Apply signal-based gating
        if signal_results:
            decision, signal_extras = apply_signal_gates(decision, signal_results)
        
        decision = _apply_rate_limits(decision, now_ms, order_limiter, cancel_limiter)
        total_decisions += 1
        
        if decision.action in ("WOULD_ENTER", "WOULD_EXIT"):
            would_trade += 1
            if decision.edge_net_bps is not None:
                edge_sum += decision.edge_net_bps
                edge_count += 1
        
        reasons[decision.reason] += 1
        if decision.action in ("WOULD_ENTER", "WOULD_EXIT", "PLACE_ORDER"):
            events[decision.action] += 1
        
        # Calculate enhanced PnL metrics
        pnl_metrics = calculate_enhanced_pnl(decision, signal_results)
        
        # Enhanced journal row with signal data
        journal_row = {
            "ts": now_ms,
            "market_id": args.ticker,
            "now": now_ms,
            "market_end_ts": market_end_ts_ms,
            "venue": market_snapshot["venue"],
            "symbol": market_snapshot["symbol"],
            "official_required_venue": market_snapshot["official_required_venue"],
            "official_used_venue": market_snapshot["official_used_venue"],
            "official_used_endpoint": market_snapshot["official_used_endpoint"],
            "official_mid": market_snapshot["official_mid"],
            "official_ok": market_snapshot["official_ok"],
            "official_err": market_snapshot["official_err"],
            "official_age_ms": market_snapshot["official_age_ms"],
            "pm_yes_bid": market_snapshot["pm_yes_bid"],
            "pm_yes_ask": market_snapshot["pm_yes_ask"],
            "pm_no_bid": market_snapshot["pm_no_bid"],
            "pm_no_ask": market_snapshot["pm_no_ask"],
            "book_ok": market_snapshot["book_ok"],
            "book_err": market_snapshot["book_err"],
            "pm_book_age_ms": market_snapshot["pm_book_age_ms"],
            "implied_yes": decision.implied_yes,
            "implied_no": decision.implied_no,
            "fair_up_prob": decision.fair_up_prob,
            "edge_yes": decision.edge_yes,
            "edge_no": decision.edge_no,
            "edge_gross_bps": decision.edge_gross_bps,
            "edge_net_bps": decision.edge_net_bps,
            "spread_bps": market_snapshot["spread_bps"],
            "depth_total": market_snapshot["depth_total"],
            "market_class": market_snapshot["market_class"],
            "required_symbol": market_snapshot["required_symbol"],
            "rules_end_ts": market_snapshot["rules_end_ts"],
            "end_ts_source": market_snapshot["end_ts_source"],
            "regime": decision.regime,
            "action": decision.action,
            "reason": decision.reason,
            "filter_reason": decision.filter_reason,
            "microstructure_flags": json.dumps(decision.microstructure_flags),
            "daily_pnl": pnl_state.daily_pnl,
            "daily_loss": pnl_state.daily_loss,
            "total_loss": pnl_state.total_loss,
            "open_markets": pnl_state.open_markets,
            "kill_switch": kill_switch,
            "params_hash": decision.params_hash,
        }
        
        # Add signal-specific fields
        if signal_results:
            for signal_name, result in signal_results.items():
                journal_row[f"signal_{signal_name}_edge_bps"] = result.edge_gross_bps
                journal_row[f"signal_{signal_name}_reason"] = result.reason
                if result.confidence:
                    journal_row[f"signal_{signal_name}_confidence"] = result.confidence
        
        # Add arbitrage-specific fields
        if signal_extras.get('arbitrage_edge'):
            arb_data = signal_extras['arbitrage_edge']
            journal_row["arb_cost_cents"] = arb_data['extras'].get('arb_cost_cents')
            journal_row["arb_edge_cents"] = arb_data['extras'].get('arb_edge_cents')
        
        journal.record_decision(journal_row)

        # Collect for shadow artifacts
        journal_rows_for_artifacts.append(journal_row)

        # Build and write shadow artifacts
        try:
            summary = {
                "schema_version": "shadow_summary_v1",
                "mode": "SHADOW",
                "last_refresh": datetime.now(timezone.utc).isoformat(),
                "strategy": "stale_edge_enhanced",
                "run_id": start_timestamp,
                "market": args.ticker,
                "decision": decision.action,
                "reason": decision.reason,
                "subreason": decision.filter_reason or "",
                "edge_bps": decision.edge_net_bps,
                "pm_yes_mid": (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else None,
                "fair_yes_prob": decision.fair_up_prob,
                "notes": "",
                "last_error": sanitize_text(artifact_last_error),
            }

            health = {
                "schema_version": "shadow_health_v1",
                "mode": "SHADOW",
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "last_success_at": artifact_last_success_at,
                "last_error_at": None,
                "last_error": sanitize_text(artifact_last_error),
                "last_latency_ms": int((time.time() - start) * 1000),
                "artifacts_written": True,
                "journal_rows": len(journal_rows_for_artifacts),
                "build": {"git_sha": None, "version": None},
                "uptime_sec": int(time.time() - start),
            }

            write_shadow_artifacts(
                summary,
                journal_rows_for_artifacts,
                health,
                header_cols=JOURNAL_COLUMNS,
            )
            artifact_last_success_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            artifact_last_error = str(e)
            logger.warning(f"Failed to write shadow artifacts: {e}")

        if total_decisions % 30 == 0:
            logger.info(f"{total_decisions} decisions, {would_trade} would trade, {arbitrage_opportunities} arb opportunities")

        if args.once:
            logger.info("Completed single iteration (--once)")
            break

        time.sleep(args.loop_interval_sec)

    # Enhanced summary
    avg_edge = edge_sum / edge_count if edge_count > 0 else 0.0
    logger.info(f"Summary: {total_decisions} decisions, {would_trade} would trade, avg edge {avg_edge:.1f} bps")
    logger.info(f"Reasons: {dict(reasons.most_common(5))}")
    logger.info(f"Events: {dict(events.most_common(5))}")
    logger.info(f"Signal stats: {dict(signal_stats.most_common(10))}")
    logger.info(f"Arbitrage opportunities: {arbitrage_opportunities}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
