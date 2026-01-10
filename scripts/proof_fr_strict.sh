#!/bin/bash
set -e

# STRICT_MODE detection
DIFF=$(git diff HEAD)
if [ -z "$DIFF" ]; then
    STRICT_MODE="CLEAN"
else
    STRICT_MODE="PATCH_ATTACHED"
    git diff HEAD > /opt/pm_updown_bot_bundle/artifacts/last_patch.diff
fi

echo "STRICT_MODE=$STRICT_MODE"
export PYTHONPATH=$PYTHONPATH:/opt/pm_updown_bot_bundle

ARTIFACT_DIR="/opt/pm_updown_bot_bundle/artifacts/proof_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARTIFACT_DIR"

echo "Step 1: Pytest"
pytest -q ; echo EXIT=$?

echo "Step 2: Smoke Live Feeds"
python3 scripts/smoke_live_feeds.py ; echo EXIT=$?

echo "Step 3: Run Shadow Stale Edge (Live, 5 min)"
# For demo purposes, we might want a shorter duration if 5 min is too long, 
# but the prompt says 5.
python3 scripts/run_shadow_stale_edge.py --mode live --minutes 5 --output "$ARTIFACT_DIR/journal.csv" ; echo EXIT=$?

echo "Step 4: Verify Integrity"
python3 scripts/verify_live_integrity.py "$ARTIFACT_DIR/journal.csv" live ; echo EXIT=$?

echo "Step 5: Reason Histogram"
python3 -c "
import csv
from collections import Counter
try:
    with open('$ARTIFACT_DIR/journal.csv', 'r') as f:
        reasons = [row['reason'] for row in csv.DictReader(f)]
        hist = Counter(reasons)
        for r, c in hist.items():
            print(f'{r}: {c}')
except Exception as e:
    print(f'Histogram failed: {e}')
"
