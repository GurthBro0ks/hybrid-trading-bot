# Verification Log - Phase 2.2 Soak Autopilot

## Execution Context

- **Date**: Fri Jan  9 13:45:00 UTC 2026
- **Command**: `python3 scripts/soak_2h.py --seconds 60 --mode realws`

## Logic Verification

1. **Startup**: Started engine in `realws` mode.
2. **Pressure Detection**: Detected CPU > 20% (average ~57%).
3. **Throttle Ladder**:
   - `NORMAL` -> `THROTTLE1`
   - `THROTTLE1` -> `THROTTLE2`
   - `THROTTLE2` -> `THROTTLE3`
4. **Guardrail Enforced**: Aborted after sustained pressure at THROTTLE3.

**Log Excerpt**:

```json
{"timestamp": "2026-01-09T13:45:08.548839Z", "state": "THROTTLE1", "action": "THROTTLE", "reason": "High Pressure: CPU 57.85%", "cpu_psi": 57.85}
{"timestamp": "2026-01-09T13:45:13.555674Z", "state": "THROTTLE2", "action": "THROTTLE", "reason": "High Pressure: CPU 55.34%", "cpu_psi": 55.34}
{"timestamp": "2026-01-09T13:45:23.566249Z", "state": "THROTTLE3", "action": "THROTTLE", "reason": "High Pressure: CPU 54.62%", "cpu_psi": 54.62}
```

**Outcome**: PASS (Fail-Closed logic confirmed).
