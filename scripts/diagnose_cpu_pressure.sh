#!/usr/bin/env bash
set -euo pipefail
cd /opt/hybrid-trading-bot

echo "--- 1. Timestamp ---"
date -Is
echo ""

echo "--- 2. Host/Kernel ---"
hostname
uname -a
echo ""

echo "--- 3. Uptime ---"
uptime
echo ""

echo "--- 4. PSI Snapshot (/proc/pressure/*) ---"
for f in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
  echo "== $f =="
  cat "$f"
  echo ""
done

echo "--- 5. Load Average ---"
cat /proc/loadavg
echo ""

echo "--- 6. Memory Summary ---"
free -h
echo ""

echo "--- 7. Disk Usage ---"
df -h
echo ""

echo "--- 8. Top CPU (10 samples over 10s) ---"
if command -v pidstat >/dev/null 2>&1; then
  pidstat -u 1 10 | tail -n +1
else
  echo "pidstat not installed (sudo apt-get install sysstat)"
  ps -eo pid,ppid,comm,%cpu,%mem --sort=-%cpu | head -25
fi
echo ""

echo "--- 9. systemd cgroup CPU snapshot ---"
if command -v systemd-cgtop >/dev/null 2>&1; then
  systemd-cgtop -n 1 --cpu=1 --depth=3 || true
else
  echo "systemd-cgtop not available"
fi
echo ""

echo "--- 10. Disk I/O Wait ---"
if command -v iostat >/dev/null 2>&1; then
  iostat -x 1 2 | tail -n +4
else
  echo "iostat not installed (sudo apt-get install sysstat)"
fi
echo ""
