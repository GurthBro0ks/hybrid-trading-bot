#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."  # repo root
sqlite3 data/bot.db "SELECT COUNT(*) FROM ticks;"
sqlite3 data/bot.db "SELECT symbol, price, ts FROM ticks ORDER BY ts DESC LIMIT 3;"
curl -I http://127.0.0.1:8501 | sed -n '1,20p'
