#!/usr/bin/env bash
set -u

ROOT="/opt/hybrid-trading-bot"
cd "$ROOT/engine-rust"

echo "=== PHASE 2.1 VERIFICATION ==="
echo "Date: $(date -Is)"

# 1. Replay Verification
echo "--- 1. Testing REPLAY mode ---"
timeout 10s ./target/debug/engine-rust --ingest replay --db /opt/hybrid-trading-bot/data/bot.db --seconds 5 > replay.log 2>&1 || true
if grep -q "mode=REPLAY" replay.log && grep -q "tick_count" replay.log; then
    echo "PASS: Replay mode ran and produced ticks"
else
    echo "FAIL: Replay mode checks failed"
    cat replay.log | head -n 20
fi

# 2. Mock WS Verification (Reconnect)
echo "--- 2. Testing MOCKWS mode (Reconnect) ---"
echo "Starting mock_ws..."
./target/debug/mock_ws > mock_ws.log 2>&1 &
MOCK_PID=$!
sleep 2

echo "Starting engine..."
timeout 15s ./target/debug/engine-rust --ingest mockws --db /opt/hybrid-trading-bot/data/bot.db --ws-url ws://127.0.0.1:9001 --seconds 15 > engine_mock.log 2>&1 &
ENGINE_PID=$!

sleep 5
echo "Simulating server crash (kill mock_ws)..."
kill $MOCK_PID
wait $MOCK_PID 2>/dev/null || true

sleep 3
echo "Restarting mock_ws..."
./target/debug/mock_ws > mock_ws_2.log 2>&1 &
MOCK_PID_2=$!

sleep 5
echo "Stopping engine..."
kill $ENGINE_PID 2>/dev/null || true
kill $MOCK_PID_2 2>/dev/null || true
wait

# Analysis
echo "--- Analysis ---"
echo "Checking for connection..."
if grep -q "connected to mock ws" engine_mock.log; then
    echo "PASS: Engine connected to Mock WS"
else
    echo "FAIL: No connection log found"
fi

echo "Checking for disconnect/retry..."
if grep -q "ws error" engine_mock.log || grep -q "server closed" engine_mock.log || grep -q "connect failed" engine_mock.log; then
    echo "PASS: Engine detected disconnect/failure"
else
    echo "FAIL: No disconnect detected"
fi

echo "Checking for reconnection..."
# We expect "connected to mock ws" to appear at least twice? 
# Or check timestamps? Simplest is just counting occurrences or checking "connected" appears after "failed"
# Let's count "connected to mock ws"
CONNECT_COUNT=$(grep -c "connected to mock ws" engine_mock.log)
echo "Connect count: $CONNECT_COUNT"
if [ "$CONNECT_COUNT" -ge 2 ]; then
    echo "PASS: Reconnected (connected count >= 2)"
else
    echo "FAIL: Did not reconnect (count < 2)"
fi

echo "=== END VERIFICATION ==="
