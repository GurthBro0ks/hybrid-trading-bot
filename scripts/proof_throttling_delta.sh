#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_phase2_2_2_systemd_hardening_complete_proofs.md"

echo "## Proof 5: Throttling Reduces Ingestion Rate" | tee -a "$BUGLOG"
echo "" | tee -a "$BUGLOG"

measure_rate() {
  local rate=$1
  local label=$2

  echo "Testing $label (sample_every=$rate)..." | tee -a "$BUGLOG"

  # Update config
  sed -i "s/^sample_every = .*/sample_every = $rate/" config/config.toml

  # Restart service
  sudo systemctl restart hybrid-engine.service
  sleep 10  # Warm-up period

  # Measure delta
  local C1=$(sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;")
  sleep 20  # Measurement window
  local C2=$(sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;")

  local delta=$((C2 - C1))
  local rate_per_sec=$(echo "scale=2; $delta / 20" | bc)

  echo "  $label: $delta ticks/20s ($rate_per_sec ticks/sec)" | tee -a "$BUGLOG"
}

echo "### Test Execution" | tee -a "$BUGLOG"
echo '```' | tee -a "$BUGLOG"
measure_rate 1 "BASELINE"
measure_rate 5 "THROTTLE_5x"
measure_rate 10 "THROTTLE_10x"
measure_rate 1 "RESTORED"
echo '```' | tee -a "$BUGLOG"

echo "" | tee -a "$BUGLOG"
echo "Proof 5 complete. Check $BUGLOG"
