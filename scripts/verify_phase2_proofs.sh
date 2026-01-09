#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_phase2_2_1_reliability_metric_integrity.md"

echo "## Phase 4: Verification Proofs" >> "$BUGLOG"

# --- Proof 1: PSI Integrity ---
echo "### Proof 1: PSI Integrity" >> "$BUGLOG"
echo "Running soak for 30s..."
echo "fancymoon373" | sudo -S timeout 35s python3 scripts/soak_2h.py --seconds 30 --mode realws --db data/bot.db || true

echo '```' >> "$BUGLOG"
jq -r 'select(.action=="THROTTLE" or .action=="EXIT_HANDLER" or .action=="ENGINE_RESTART" or .action=="STARTUP") | [.timestamp,.action,.cpu_some_avg10,.cpu_some_raw] | @tsv' data/ops/soak_decisions.jsonl | tail -10 >> "$BUGLOG"
echo '```' >> "$BUGLOG"

# --- Proof 5: Throttling (Sample Rate) ---
echo "### Proof 5: Throttling Reduction" >> "$BUGLOG"

measure_rate() {
  local rate=$1
  # Update config
  sed -i "s/^sample_every = .*/sample_every = $rate/" config/config.toml
  echo "fancymoon373" | sudo -S systemctl restart hybrid-engine.service
  sleep 10 # Wait for startup
  
  local C1=$(sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;")
  sleep 20
  local C2=$(sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;")
  local diff=$((C2-C1))
  echo "Rate@$rate (20s delta): $diff ticks"
}

echo '```' >> "$BUGLOG"
measure_rate 1 >> "$BUGLOG"
measure_rate 10 >> "$BUGLOG"
echo '```' >> "$BUGLOG"

# Reset config
sed -i "s/^sample_every = .*/sample_every = 1/" config/config.toml
echo "fancymoon373" | sudo -S systemctl restart hybrid-engine.service

# --- Proof 2: Stall Detection ---
echo "### Proof 2: Stall Detection" >> "$BUGLOG"
echo "Starting soak in background..."
echo "fancymoon373" | sudo -S python3 scripts/soak_2h.py --seconds 180 --mode realws --db data/bot.db &
SOAK_PID=$!

echo "Simulating stall with SIGSTOP..."
echo "fancymoon373" | sudo -S pkill -STOP -f engine-rust

echo "Waiting for stall detection (threshold 45s)..."
sleep 60

echo "Checking logs for STALL and RESTART..."
echo '```' >> "$BUGLOG"
grep -E '"action":"STALL"|"action":"ENGINE_RESTART"' data/ops/soak_decisions.jsonl | tail -10 >> "$BUGLOG"
echo '```' >> "$BUGLOG"

kill $SOAK_PID || true
wait $SOAK_PID || true

# --- Proof 3: Typed Exit Codes ---
echo "### Proof 3: Typed Exit Codes" >> "$BUGLOG"
# Force config error (Exit 12)
cp config/config.toml config/config.toml.bak
echo "garbage_line = 123" >> config/config.toml
echo "fancymoon373" | sudo -S systemctl restart hybrid-engine.service
sleep 5
echo "Checking for Exit Code 12 (Config Error)..."
echo '```' >> "$BUGLOG"
systemctl status hybrid-engine.service --no-pager | grep "Result: exit-code" || true >> "$BUGLOG"
journalctl -u hybrid-engine.service -n 10 --no-pager >> "$BUGLOG"
echo '```' >> "$BUGLOG"
# Restore
mv config/config.toml.bak config/config.toml
echo "fancymoon373" | sudo -S systemctl restart hybrid-engine.service

# --- Proof 4: Concurrency ---
echo "### Proof 4: Concurrency" >> "$BUGLOG"
echo "Running concurrent reads..."
echo '```' >> "$BUGLOG"
for i in {1..5}; do
  sqlite3 data/bot.db "SELECT COUNT(*), MAX(ts) FROM ticks;"
  sleep 1
done >> "$BUGLOG" 2>&1
echo '```' >> "$BUGLOG"

echo "Verification Complete. Check $BUGLOG"
