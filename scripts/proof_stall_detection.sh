#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_phase2_2_2_systemd_hardening_complete_proofs.md"

echo "## Proof 2: Stall Detection" | tee -a "$BUGLOG"
echo "**Requirement**: Deterministic SIGSTOP on MainPID → stall detection → restart" | tee -a "$BUGLOG"
echo "" | tee -a "$BUGLOG"

# Clear old soak logs for clean capture
> data/ops/soak_decisions.jsonl

echo "Starting soak in background (3-minute window)..." | tee -a "$BUGLOG"
sudo python3 scripts/soak_2h.py --seconds 180 --mode realws --db data/bot.db &
SOAK_PID=$!

echo "Soak started (PID: $SOAK_PID), waiting 5s for engine to start..." | tee -a "$BUGLOG"
sleep 5

# Capture MainPID
MAIN_PID=$(systemctl show hybrid-engine.service --property=MainPID --value)
echo "Engine MainPID: $MAIN_PID" | tee -a "$BUGLOG"

# DETERMINISTIC STALL: SIGSTOP the engine process
echo "Sending SIGSTOP to MainPID $MAIN_PID at $(date -Is)" | tee -a "$BUGLOG"
sudo kill -STOP "$MAIN_PID"

# Wait for stall threshold (45s) + detection window
echo "Waiting 70s for stall detection (45s threshold + buffer)..." | tee -a "$BUGLOG"
sleep 70

# Resume process (soak controller should have detected and restarted)
sudo kill -CONT "$MAIN_PID" 2>/dev/null || echo "Process already restarted (expected)" | tee -a "$BUGLOG"

# Wait for soak to complete detection cycle
sleep 10

echo "" | tee -a "$BUGLOG"
echo "### Evidence" | tee -a "$BUGLOG"
echo '```json' | tee -a "$BUGLOG"
grep -E '"action":"STALL"|"action":"ENGINE_RESTART"' data/ops/soak_decisions.jsonl | tail -10 | tee -a "$BUGLOG"
echo '```' | tee -a "$BUGLOG"

# Kill soak controller
kill $SOAK_PID 2>/dev/null || true
wait $SOAK_PID 2>/dev/null || true

echo "Proof 2 capture complete. Check $BUGLOG" | tee -a "$BUGLOG"
