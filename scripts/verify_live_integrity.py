#!/usr/bin/env python3
"""Verifier for live vs sim integrity."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

def verify_journal(path: str, mode: str) -> bool:
    if not Path(path).exists():
        print(f"ERROR: Journal {path} not found")
        return False
        
    errors = 0
    rows = 0
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            mock_used = row.get("mock_used", "").lower() == "true"
            if mode == "live" and mock_used:
                print(f"ERROR: Row {rows} has mock_used=true in live mode")
                errors += 1
            if mode == "sim" and not mock_used:
                # This might be okay if some rows don't use mocks even in sim mode?
                # But usually sim mode uses mocks.
                pass
                
    if errors > 0:
        print(f"FAILED: {errors} integrity errors found in {rows} rows")
        return False
    
    print(f"PASSED: Integrity check clean for {rows} rows in {mode} mode")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: verify_live_integrity.py <journal_csv> <mode>")
        sys.exit(1)
    
    success = verify_journal(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
