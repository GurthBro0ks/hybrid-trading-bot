#!/usr/bin/env python3
"""
Entrypoint for Hybrid Shadow Runner Service.
Orchestrates discovery and execution of the shadow strategy.
"""

import sys
import os
import shutil
import subprocess
import time
import json
import logging
from pathlib import Path

# Setup paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from venues.polymarket_discovery import discover_and_filter_candidates

# Config
ARTIFACTS_DIR = os.environ.get("SHADOW_ARTIFACTS_DIR", str(ROOT / "artifacts/shadow"))
CROSS_REPO_DIR = "/opt/hybrid-trading-bot/artifacts/shadow"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("shadow_entrypoint")

def main():
    logger.info("Starting Shadow Prod Entrypoint...")
    
    # Ensure dirs exist
    Path(ARTIFACTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(CROSS_REPO_DIR).mkdir(parents=True, exist_ok=True)

    # 1. Discovery
    logger.info("Running discovery...")
    try:
        results = discover_and_filter_candidates(max_candidates=20)
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        sys.exit(1)

    ready = results["ready"]
    if not ready:
        logger.warning("No READY candidates found. Exiting cleanly (service will retry).")
        # Write a "stale" or "empty" summary so NUC2 knows we tried?
        # Or just exit.
        sys.exit(0) 
    
    candidate = ready[0]
    market_id = candidate.get("id")
    clob_ids = candidate.get("clobTokenIds")
    # Use Token ID for execution if available, else Market ID (though likely fails)
    # Polymarket CLOB uses Token ID.
    token_id = clob_ids[0] if clob_ids else market_id
    
    logger.info(f"Selected candidate: {market_id} (Token: {token_id})")
    
    # 2. Run Shadow Strategy
    # We output to a known location in local artifacts
    journal_path = f"{ARTIFACTS_DIR}/latest_journal.csv"
    
    cmd = [
        "python3", str(ROOT / "scripts/run_shadow_stale_edge.py"),
        "--market-id", token_id,
        "--minutes", "1",
        "--mode", "live",
        "--venue", "polymarket",
        "--output", journal_path
    ]
    
    logger.info(f"Executing strategy: {' '.join(cmd)}")
    ret = subprocess.run(cmd, capture_output=False)
    
    if ret.returncode != 0:
        logger.error(f"Shadow strategy run failed with code {ret.returncode}")
        # We might still want to publish what we have? No.
        sys.exit(ret.returncode)
        
    # 3. Publish Artifacts to Cross-Repo/NUC2 path
    # Copy journal
    logger.info(f"Publishing artifacts to {CROSS_REPO_DIR}...")
    try:
        # Resolve real paths to avoid SameFileError on symlinks
        src = os.path.realpath(journal_path)
        dst = os.path.realpath(f"{CROSS_REPO_DIR}/latest_journal.csv")
        if src != dst:
            shutil.copy(journal_path, f"{CROSS_REPO_DIR}/latest_journal.csv")
        else:
            logger.info("Journal already in target directory (aliased). Skipping copy.")
    except Exception as e:
        logger.warning(f"Copy failed (non-fatal): {e}")

    try:
        # Create and write summary
        summary = {
            "ts": int(time.time() * 1000),
            "market_id": market_id,
            "status": "OK",
            "check_ts": int(time.time()),
            "candidates_count": len(ready)
        }
        with open(f"{CROSS_REPO_DIR}/latest_summary.json", "w") as f:
            json.dump(summary, f)
            
        logger.info("Artifacts published successfully.")
        
    except Exception as e:
        logger.error(f"Failed to publish artifacts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
