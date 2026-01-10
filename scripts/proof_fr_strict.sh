#!/bin/bash
set -u

PROOF_ID="proof_$(date +%Y%m%d_%H%M%S)"
PROOF_DIR="artifacts/$PROOF_ID"
mkdir -p "$PROOF_DIR"
VERIFY_LOG="$PROOF_DIR/verify.log"

echo "Start Proof Run at $(date)" | tee -a "$VERIFY_LOG"
echo "Hostname: $(hostname)" | tee -a "$VERIFY_LOG"
echo "PWD: $(pwd)" | tee -a "$VERIFY_LOG"
echo "Branch: $(git rev-parse --abbrev-ref HEAD)" | tee -a "$VERIFY_LOG"
echo "SHA: $(git rev-parse HEAD)" | tee -a "$VERIFY_LOG"

# Clean Tree Policy
STATUS=$(git status --porcelain)
if [ -n "$STATUS" ]; then
    echo "Tree is DIRTY. Creating patch..." | tee -a "$VERIFY_LOG"
    git diff > "$PROOF_DIR/local_dirty_tree.patch"
    # Also capture untracked files list just in case
    git status >> "$PROOF_DIR/git_status.txt"
    echo "Patch created at $PROOF_DIR/local_dirty_tree.patch" | tee -a "$VERIFY_LOG"
else
    echo "Tree is CLEAN." | tee -a "$VERIFY_LOG"
fi

# Env Snapshot (Sanitized)
echo "Capturing Env..."
env | grep -E '^(BOT_|PM_|POLYMARKET_|KALSHI_|COINBASE_|BINANCE_|GEMINI_|RPC_)' | \
    grep -vE 'KEY|TOKEN|SECRET|PASSWORD|AUTH' > "$PROOF_DIR/env_snapshot.txt" || true

# Run Tests
echo "Running Unit Tests..." | tee -a "$VERIFY_LOG"
export PYTHONPATH=${PYTHONPATH:-}:.
pytest tests/test_stale_edge.py > "$PROOF_DIR/test_output.txt" 2>&1
TEST_EXIT=$?
echo "pytest EXIT=$TEST_EXIT" | tee -a "$VERIFY_LOG"

if [ $TEST_EXIT -ne 0 ]; then
    echo "FAIL: Tests failed." | tee -a "$VERIFY_LOG"
    cat "$PROOF_DIR/test_output.txt"
    exit 1
fi

# Run Shadow Bot
echo "Running Shadow Bot..." | tee -a "$VERIFY_LOG"
# Short run 0.1 minutes (6 seconds) to generate some lines
python3 scripts/run_shadow_stale_edge.py --output "$PROOF_DIR/journal.csv" --minutes 1 --loop-interval-sec 0.1 > "$PROOF_DIR/shadow_output.txt" 2>&1
SHADOW_EXIT=$?
echo "run_shadow_stale_edge.py EXIT=$SHADOW_EXIT" | tee -a "$VERIFY_LOG"

# Verify Journal
echo "Verifying Journal Schema..." | tee -a "$VERIFY_LOG"
HEADER=$(head -n1 "$PROOF_DIR/journal.csv")
REQUIRED="thin_book_reason,thin_book_threshold_depth_usd,thin_book_threshold_qty,thin_book_spread_bps"

MISSING=0
for col in $(echo $REQUIRED | tr "," " "); do
    if [[ "$HEADER" != *"$col"* ]]; then
        echo "FAIL: Missing column $col" | tee -a "$VERIFY_LOG"
        MISSING=1
    fi
done

if [ $MISSING -eq 0 ]; then
    echo "PASS: Journal Schema Verified." | tee -a "$VERIFY_LOG"
    echo "Values Sample:" | tee -a "$VERIFY_LOG"
    # Show non-empty thin_book_reason if any, or just first few lines
    awk -F, '{print $18, $19, $20, $21}' "$PROOF_DIR/journal.csv" | head -n 5 | tee -a "$VERIFY_LOG"
else
    echo "FAIL: Schema check failed." | tee -a "$VERIFY_LOG"
    exit 1
fi

echo "Proof Artifact: $PROOF_DIR" | tee -a "$VERIFY_LOG"
