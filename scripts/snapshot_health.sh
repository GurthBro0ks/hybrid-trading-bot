#!/usr/bin/env bash
# Flight Recorder Protocol - Health Snapshot Logger
# Logs CPU cage, load, pressure, service quotas, and healthcheck status
# Must complete in < 5 seconds

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$ROOT/data/ops"
LOG_FILE="$LOG_DIR/health_snapshots.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Snapshot block
{
  echo "=== [$(date -Is)] Flight Recorder Snapshot ==="

  # System state
  echo "UPTIME: $(uptime)"
  echo "LOAD: $(cat /proc/loadavg)"

  # CPU pressure (if available)
  if [ -f /proc/pressure/cpu ]; then
    echo "CPU_PRESSURE:"
    cat /proc/pressure/cpu | sed 's/^/  /'
  fi

  # mc-paper service CPU settings (if systemd available)
  if command -v systemctl &>/dev/null; then
    CPU_QUOTA=$(systemctl show mc-paper.service --property=CPUQuotaPercentU --value 2>/dev/null || echo "N/A")
    CPU_WEIGHT=$(systemctl show mc-paper.service --property=CPUWeight --value 2>/dev/null || echo "N/A")
    MEMORY_LIMIT=$(systemctl show mc-paper.service --property=MemoryLimit --value 2>/dev/null || echo "N/A")
    echo "MC_PAPER_QUOTAS:"
    echo "  CPUQuotaPercentU: $CPU_QUOTA"
    echo "  CPUWeight: $CPU_WEIGHT"
    echo "  MemoryLimit: $MEMORY_LIMIT"
  fi

  # Java process snapshot (1 line only)
  JAVA_TOP=$(top -bn1 -p "$(pgrep -f java || echo '1')" 2>/dev/null | grep java || echo "java not found")
  if [ -n "$JAVA_TOP" ]; then
    echo "JAVA_TOP: $JAVA_TOP"
  fi

  # Hybrid healthcheck
  echo -n "HEALTHCHECK: "
  if bash "$ROOT/scripts/healthcheck.sh" 2>&1 | tail -n 1 | grep -q PASS; then
    echo "PASS"
  else
    echo "FAIL"
  fi

  echo ""
} >> "$LOG_FILE"

exit 0
