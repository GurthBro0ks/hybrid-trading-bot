#!/usr/bin/env python3
"""
Phase 8B.1: Verify Shadow Pipeline with CLOB Readiness
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Ensure repo root is in path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from venues.polymarket_discovery import discover_and_filter_candidates, ReadinessStatus, probe_clob_readiness
from venues.polymarket import fetch_polymarket_venuebook, BookStatus
from venuebook.types import BookFailReason

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("verify_pipeline")

def main():
    parser = argparse.ArgumentParser(description="Verify Shadow Pipeline with CLOB Readiness")
    parser.add_argument("--fixture-mode", action="store_true", help="Run in offline fixture mode")
    parser.add_argument("--known-ready-market-id", help="Pre-known market ID to select if ready")
    parser.add_argument("--known-ready-token-id", help="Pre-known token ID to select if ready")
    args = parser.parse_args()

    if args.fixture_mode:
        os.environ["POLYMARKET_FIXTURE_MODE"] = "1"
        logger.info("FIXTURE MODE ENABLED")

    proof_dir = os.environ.get("PROOF_DIR")
    if not proof_dir:
        logger.warning("PROOF_DIR not set, using /tmp")
        proof_dir = "/tmp"
    
    logger.info("Starting discovery...")
    results = discover_and_filter_candidates(max_candidates=20)
    
    ready = results["ready"]
    not_ready = results["not_ready"]
    
    logger.info(f"Discovered: {len(ready)} READY, {len(not_ready)} NOT_READY")
    
    # Save output to proof dir
    with open(f"{proof_dir}/discovery_summary.txt", "w") as f:
        f.write(f"READY: {len(ready)}\n")
        f.write(f"NOT_READY: {len(not_ready)}\n")
    
    # Candidate selection logic
    selected_candidate = None
    selection_source = "DISCOVERY"

    # 1. Try known-ready if provided
    if args.known_ready_market_id and args.known_ready_token_id:
        logger.info(f"Probing known-ready candidate: {args.known_ready_market_id} (Token: {args.known_ready_token_id})")
        kr_result = probe_clob_readiness(args.known_ready_token_id) # API changed to only token_id
        if kr_result.status == ReadinessStatus.READY:
            selected_candidate = {
                "id": args.known_ready_market_id,
                "token_id": args.known_ready_token_id,
                "clobTokenIds": [args.known_ready_token_id] 
            }
            selection_source = "KNOWN_READY"
            logger.info("Known-ready candidate is READY. Selected.")
        else:
            logger.warning(f"Known-ready candidate is NOT READY: {kr_result.reason}")

    # 2. Fallback to discovery
    if not selected_candidate:
        if ready:
            selected_candidate = ready[0]
            logger.info("Selected first READY candidate from discovery.")
        else:
            logger.error("No READY candidates found in discovery and known-ready failed/missing!")

    ready_count = len(ready)

    if not selected_candidate:
        print(f"RESULT=FAIL ready_count={ready_count} reason=NO_READY_CANDIDATES")
        sys.exit(1)

    market_id = selected_candidate.get("id") or selected_candidate.get("market_id")
    token_id = selected_candidate.get("token_id")
    if not token_id:
        clob_ids = selected_candidate.get("clobTokenIds") 
        token_id = clob_ids[0] if clob_ids else "UNKNOWN"
    
    logger.info(f"Final Selected: {market_id} (Token: {token_id})")
    
    # Fetch VenueBook
    logger.info("Fetching VenueBook...")
    book = fetch_polymarket_venuebook(token_id)
    
    logger.info(f"VenueBook Status: {book.status}")
    if book.fail_reason:
        logger.info(f"VenueBook FailReason: {book.fail_reason}")
    
    allowed_reasons = {
        None, # OK
        BookFailReason.NO_BBO,
        BookFailReason.DEPTH_BELOW_THRESHOLD, 
        BookFailReason.SPREAD_WIDE
    }
    
    venuebook_outcome = "UNKNOWN"
    is_success = False
    
    if book.status == BookStatus.OK:
        is_success = True
        venuebook_outcome = "OK"
    elif book.fail_reason in allowed_reasons:
        is_success = True
        if book.fail_reason == BookFailReason.NO_BBO:
            venuebook_outcome = "NO_BBO"
        else:
            venuebook_outcome = "THIN_BOOK"
    else:
        is_success = False
        venuebook_outcome = book.fail_reason.name if book.fail_reason else "ERROR"

    result_status = "PASS" if is_success and (ready_count >= 1 or selection_source == "KNOWN_READY") else "FAIL"
    
    summary_line = (
        f"RESULT={result_status} "
        f"selected_market_id={market_id} "
        f"selected_token_id={token_id} "
        f"venuebook={venuebook_outcome} "
        f"ready_count={ready_count}"
    )
    
    print(summary_line)
    
    with open(f"{proof_dir}/verify_shadow_pipeline.txt", "a") as f:
        f.write(summary_line + "\n")

    if is_success:
        logger.info("SUCCESS: Candidate is usable")
        with open(f"{proof_dir}/ready_example.txt", "w") as f:
            f.write(f"KNOWN_READY market_id={market_id} token_id={token_id}\n")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: Candidate failed validation")
        sys.exit(1)

if __name__ == "__main__":
    main()
