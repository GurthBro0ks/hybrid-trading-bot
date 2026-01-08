#!/bin/bash
PID_FILE="/tmp/hybrid_engine.pid"
DB_FILE="/opt/hybrid-trading-bot/data/bot.db"

if [ -f "$PID_FILE" ]; then
    echo "Engine running at PID: $(cat $PID_FILE)"
else
    echo "Engine PID file missing!"
fi

echo "Checking DB writes..."
for i in {1..5}; do
    sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM ticks;"
    sleep 1
done
sqlite3 "$DB_FILE" "SELECT symbol, price, ts FROM ticks ORDER BY ts DESC LIMIT 3;"
