#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_phase2_2_1_reliability_metric_integrity.md"
mkdir -p docs/buglog

{
  echo "# Verification Log — Phase 2.2.1 (Reliability + Metric Integrity)"
  echo
  echo "## Execution Context"
  echo "- Date: $(date -Is)"
  echo "- Hostname: $(hostname)"
  echo "- Kernel: $(uname -a)"
  echo "- Git HEAD: $(git rev-parse HEAD)"
  echo
  echo "## Preflight"
  echo '```'
  command -v python3 && python3 --version
  command -v cargo && cargo --version || true
  command -v sqlite3 && sqlite3 --version
  command -v jq && jq --version || echo "jq: MISSING (required for proofs)"
  echo '```'
  echo
  echo "### PSI Baseline (/proc/pressure/*)"
  echo '```'
  for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
    echo "== $f =="
    cat "$f"
    echo
  done
  echo '```'
} | tee "$BUGLOG"

# Required scripts / files must exist
test -f docs/specs/behavior_contract_phase2.md || { echo "Missing spec authority"; exit 1; }
test -f scripts/soak_2h.py || { echo "Missing scripts/soak_2h.py"; exit 1; }

# If you have a healthcheck, run it; otherwise record skip explicitly.
if test -x ./scripts/healthcheck.sh; then
  {
    echo
    echo "### Healthcheck"
    echo '```'
    ./scripts/healthcheck.sh
    echo '```'
  } | tee -a "$BUGLOG"
else
  echo -e "\n### Healthcheck\nSKIP: ./scripts/healthcheck.sh not found or not executable" | tee -a "$BUGLOG"
fi

echo "PREFLIGHT PASS: $BUGLOG"
