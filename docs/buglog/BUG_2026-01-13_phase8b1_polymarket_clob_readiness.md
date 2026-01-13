# BUG_2026-01-13_phase8b1_polymarket_clob_readiness.md

## Rationale

Gamma active markets do not always have an initialized CLOB orderbook. Probing `/midpoint` ensure we only select markets where a `VenueBook` can actually be fetched.

## Mapping Rules & Failures

- **Gamma Parsing**: Scans `clobTokenIds` and `outcomes` to map "Yes" -> `token_id`.
- **CLOB Readiness**: Probes `GET /midpoint?token_id=...`.
- **Failure Enums**:
  - `CLOB_NO_ORDERBOOK`: 404 with specific message.
  - `CLOB_RATE_LIMITED`: 429.
  - `INVALID_TOKEN_ID`: 400.
  - `GAMMA_PARSE_ERROR`: Malformed Gamma data.

## Ops Guardrails

- `MAX_PROBES_PER_RUN`: 20
- `BASE_BACKOFF`: 0.25s (with jitter)
- `CACHE_TTL_READY`: 1800s
- `CACHE_TTL_NOT_READY`: 300s

## Proof of Implementation

### 1. Test Suite (Online/Offline)

```bash
./scripts/run_tests.sh
```

Output:

```text
134 passed in 0.99s
```

### 2. Verification Script (Fixture Mode)

```bash
python3 scripts/verify_shadow_pipeline.py --fixture-mode --known-ready-market 0x123 --known-ready-token 0x456
```

Output:

```text
20:10:13 [INFO] FIXTURE MODE ENABLED
20:10:13 [INFO] Starting discovery...
20:10:13 [INFO] Discovered: 1 READY, 0 NOT_READY
20:10:13 [INFO] Probing known-ready candidate: 0x123 (Token: 0x456)
20:10:13 [INFO] Known-ready candidate is READY. Selected.
20:10:13 [INFO] Final Selected: 0x123 (Token: 0x456)
20:10:13 [INFO] Fetching VenueBook...
20:10:13 [INFO] VenueBook Status: BookStatus.OK
RESULT=PASS selected_market_id=0x123 selected_token_id=0x456 venuebook=OK ready_count=1
```

### 3. Tripwire Scan

```bash
./scripts/tripwire_no_secrets.sh
```

Output:

```text
Starting tripwire scan...
Using ripgrep (rg)...
OK_NO_SECRETS_MATCHED
```

## Readiness Semantic Confirmation

"Gamma active ≠ CLOB ready" is confirmed via mapping rules. Soft failures (404) are cached for 300s to avoid hammering Polymarket while allowing for eventual initialization.
