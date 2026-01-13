#!/usr/bin/env bash
# Shadow Artifacts Contract CI Verification
#
# This script verifies the Shadow Artifacts Contract v1.0 in an offline environment.
# It generates mock artifacts with secret-laden data and verifies:
# 1. All required files are created
# 2. JSON schemas are valid
# 3. File sizes are within limits
# 4. NO secrets appear in output (tripwire)
#
# Exit codes:
#   0: All checks passed
#   1: Verification failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Shadow Artifacts Contract CI Verification ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Create temp directory for artifacts
TMP_DIR=$(mktemp -d)
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Using temp directory: $TMP_DIR"

# Set up artifacts directory
export SHADOW_ARTIFACTS_DIR="$TMP_DIR/artifacts/shadow"
mkdir -p "$SHADOW_ARTIFACTS_DIR"

# Change to project root for imports to work
cd "$PROJECT_ROOT"

echo ""
echo "=== Step 1: Generate mock artifacts ==="
python3 scripts/smoke/gen_mock_shadow_artifacts.py
echo "PASS: Mock artifacts generated"

echo ""
echo "=== Step 2: Verify files exist ==="
if [[ ! -f "$SHADOW_ARTIFACTS_DIR/latest_summary.json" ]]; then
    echo "FAIL: latest_summary.json not found"
    exit 1
fi
if [[ ! -f "$SHADOW_ARTIFACTS_DIR/latest_journal.csv" ]]; then
    echo "FAIL: latest_journal.csv not found"
    exit 1
fi
if [[ ! -f "$SHADOW_ARTIFACTS_DIR/health.json" ]]; then
    echo "FAIL: health.json not found"
    exit 1
fi
echo "PASS: All required files exist"

echo ""
echo "=== Step 3: Validate JSON schemas ==="
# Check summary has required fields
if ! jq -e '.schema_version and .mode' "$SHADOW_ARTIFACTS_DIR/latest_summary.json" >/dev/null 2>&1; then
    echo "FAIL: latest_summary.json missing required fields"
    exit 1
fi
# Check health has required fields
if ! jq -e '.schema_version and .mode' "$SHADOW_ARTIFACTS_DIR/health.json" >/dev/null 2>&1; then
    echo "FAIL: health.json missing required fields"
    exit 1
fi
# Check schema versions
SUMMARY_VERSION=$(jq -r '.schema_version' "$SHADOW_ARTIFACTS_DIR/latest_summary.json")
HEALTH_VERSION=$(jq -r '.schema_version' "$SHADOW_ARTIFACTS_DIR/health.json")
if [[ "$SUMMARY_VERSION" != "shadow_summary_v1" ]]; then
    echo "FAIL: Invalid summary schema_version: $SUMMARY_VERSION"
    exit 1
fi
if [[ "$HEALTH_VERSION" != "shadow_health_v1" ]]; then
    echo "FAIL: Invalid health schema_version: $HEALTH_VERSION"
    exit 1
fi
# Check mode
SUMMARY_MODE=$(jq -r '.mode' "$SHADOW_ARTIFACTS_DIR/latest_summary.json")
HEALTH_MODE=$(jq -r '.mode' "$SHADOW_ARTIFACTS_DIR/health.json")
if [[ "$SUMMARY_MODE" != "SHADOW" ]]; then
    echo "FAIL: Invalid summary mode: $SUMMARY_MODE"
    exit 1
fi
if [[ "$HEALTH_MODE" != "SHADOW" ]]; then
    echo "FAIL: Invalid health mode: $HEALTH_MODE"
    exit 1
fi
echo "PASS: JSON schemas valid"

echo ""
echo "=== Step 4: Check file sizes ==="
SUMMARY_SIZE=$(stat -c%s "$SHADOW_ARTIFACTS_DIR/latest_summary.json" 2>/dev/null || stat -f%z "$SHADOW_ARTIFACTS_DIR/latest_summary.json")
HEALTH_SIZE=$(stat -c%s "$SHADOW_ARTIFACTS_DIR/health.json" 2>/dev/null || stat -f%z "$SHADOW_ARTIFACTS_DIR/health.json")
MAX_SIZE=10240

if [[ $SUMMARY_SIZE -ge $MAX_SIZE ]]; then
    echo "FAIL: latest_summary.json too large: $SUMMARY_SIZE bytes (limit: $MAX_SIZE)"
    exit 1
fi
if [[ $HEALTH_SIZE -ge $MAX_SIZE ]]; then
    echo "FAIL: health.json too large: $HEALTH_SIZE bytes (limit: $MAX_SIZE)"
    exit 1
fi
echo "PASS: File sizes within limits (summary: ${SUMMARY_SIZE}B, health: ${HEALTH_SIZE}B)"

echo ""
echo "=== Step 5: TRIPWIRE - Check for secrets ==="
# This is the critical security check
# We use rg (ripgrep) with simple patterns - NO fancy regex
TRIPWIRE_PATTERN="api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password"

if command -v rg >/dev/null 2>&1; then
    # Use ripgrep if available
    if rg -n -i "$TRIPWIRE_PATTERN" "$TMP_DIR/artifacts"; then
        echo ""
        echo "FAIL_SECRETS_MATCHED"
        echo "ERROR: Secrets detected in artifacts! Sanitizer failed."
        exit 1
    fi
else
    # Fallback to grep
    if grep -r -n -i -E "$TRIPWIRE_PATTERN" "$TMP_DIR/artifacts"; then
        echo ""
        echo "FAIL_SECRETS_MATCHED"
        echo "ERROR: Secrets detected in artifacts! Sanitizer failed."
        exit 1
    fi
fi

echo "OK_NO_SECRETS_MATCHED"
echo "PASS: No secrets found in artifacts"

echo ""
echo "=== Step 6: Show sanitized content (debug) ==="
echo "--- latest_summary.json last_error field ---"
jq -r '.last_error' "$SHADOW_ARTIFACTS_DIR/latest_summary.json"
echo ""
echo "--- health.json last_error field ---"
jq -r '.last_error' "$SHADOW_ARTIFACTS_DIR/health.json"
echo ""

echo "=== ALL CHECKS PASSED ==="
exit 0
