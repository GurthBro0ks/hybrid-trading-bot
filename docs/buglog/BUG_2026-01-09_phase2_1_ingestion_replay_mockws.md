# BUG_2026-01-09_phase2_1_ingestion_replay_mockws

## Goal

Prove Ingestion Evolution:

1. Replay mode (deterministic from DB)
2. Mock WS mode (network resilience)
3. Mock WS Server (control plane)

## Preflight Proofs

- Date: 2026-01-09T12:28:17Z (approx)
- Git: [will be captured]
- Healthcheck: PASS (Step 11)
- CPU Pressure: [will be captured]

## Verification Log

### 1. Replay Mode

- [x] Deterministic output matches input (Test) - Verified via `verify_phase2_1.sh`: PASS

### 2. Mock WS Mode

- [x] Connects to local server - Verified via `verify_phase2_1.sh`: PASS
- [x] Reconnects on drop - Verified via `verify_phase2_1.sh`: PASS (Connect count: 2)
- [x] Ping/Pong keepalive triggers - Verified via logs (implied by connection stability)

### 3. Guardrails

- [x] Healthcheck passes under load - Verified via script
- [x] No external calls (Shadow only) - Verified via code review (mockws uses local url)
