#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="$ROOT/data/bot.db"
PORT="${1:-8501}"

echo "[health] time: $(date -Is)"
echo "[health] db: $DB"
echo "[health] port: $PORT"

# DB readable?
if ! sqlite3 "$DB" "SELECT name FROM sqlite_master WHERE type='table' AND name='ticks';" | grep -q ticks; then
  echo "[health] FAIL: ticks table not found"
  exit 1
fi

# Tick count
COUNT="$(sqlite3 "$DB" "SELECT COUNT(*) FROM ticks;")"
echo "[health] ticks: $COUNT"
if [ "$COUNT" -lt 10 ]; then
  echo "[health] FAIL: insufficient ticks ($COUNT < 10)"
  exit 1
fi

# Dashboard HTTP
echo "[health] checking http://127.0.0.1:${PORT}..."
if ! curl -fsSI "http://127.0.0.1:${PORT}" 2>/dev/null | head -n 5; then
  echo "[health] FAIL: dashboard unreachable"
  exit 1
fi

echo "[health] PASS"
exit 0
