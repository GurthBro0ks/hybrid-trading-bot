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

from venues.polymarket_discovery import discover_and_filter_candidates, ReadinessStatus
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
        
    if not ready:
        logger.error("No READY candidates found!")
        sys.exit(1)
        
    # Select first ready candidate
    candidate = ready[0]
    market_id = candidate.get("id")
    # Determine token_id (logic from discovery)
    clob_ids = candidate.get("clobTokenIds") 
    token_id = clob_ids[0] if clob_ids else "UNKNOWN"
    
    logger.info(f"Selected candidate: {market_id} (Token: {token_id})")
    
    # Fetch VenueBook
    logger.info("Fetching VenueBook...")
    book = fetch_polymarket_venuebook(token_id)
    
    logger.info(f"VenueBook Status: {book.status}")
    if book.fail_reason:
        logger.info(f"VenueBook FailReason: {book.fail_reason}")
    
    # Output result line
    result_code = book.status.name
    if book.status != BookStatus.OK and book.fail_reason:
        result_code = book.fail_reason.name
        
    summary_line = (
        f"RESULT: discovered={len(ready)+len(not_ready)} ready={len(ready)} "
        f"selected={market_id}:{token_id} venuebook={result_code}"
    )
    print(summary_line)
    
    with open(f"{proof_dir}/verify_shadow_pipeline.txt", "a") as f:
        f.write(summary_line + "\n")
        
    # Verification Logic
    # We accept OK, NO_BBO, THIN_BOOK (mapped from DEPTH_BELOW_THRESHOLD or SPREAD_WIDE in legacy?)
    # VenueBook types: OK, NO_TRADE
    # Fail reasons: NO_BBO, BOOK_UNAVAILABLE, PARSE_AMBIGUOUS, DEPTH_BELOW_THRESHOLD, SPREAD_WIDE
    
    allowed_reasons = {
        None, # OK
        BookFailReason.NO_BBO,
        BookFailReason.DEPTH_BELOW_THRESHOLD, 
        BookFailReason.SPREAD_WIDE
    }
    
    is_success = False
    
    if book.status == BookStatus.OK:
        is_success = True
    elif book.fail_reason in allowed_reasons:
        is_success = True
    else:
        # e.g. BOOK_UNAVAILABLE, PARSE_AMBIGUOUS
        is_success = False
        
    if is_success:
        logger.info("SUCCESS: Candidate is usable (or cleanly empty/thin)")
        # Identify "Thin" vs "No BBO" vs "OK" for reporting
        if book.status == BookStatus.OK:
            outcome = "OK"
        elif book.fail_reason == BookFailReason.NO_BBO:
            outcome = "NO_BBO"
        else:
            outcome = "THIN_BOOK" # Generalized for depth/spread issues
            
        with open(f"{proof_dir}/ready_example.txt", "w") as f:
            f.write(f"READY_EXAMPLE market_id={market_id} token_id={token_id}\n")
            
        sys.exit(0)
    else:
        logger.error(f"FAILURE: Candidate failed with {book.fail_reason}")
        sys.exit(1)

if __name__ == "__main__":
    main()
