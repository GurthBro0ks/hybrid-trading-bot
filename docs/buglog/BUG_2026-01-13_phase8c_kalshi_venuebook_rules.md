# BUG_2026-01-13_phase8c_kalshi_venuebook_rules.md

## Provenance

- **Host**: NUC1
- **Branch**: `phase8b.2-test-gate` (hosting Phase 8C hardening changes)
- **Commit**: `804a29b`
- **Time**: `2026-01-13T16:46:27Z`
- **Environment**: NUC1 (Python 3.12.3)
- **Status**: CLEAN (no uncommitted code changes)

## Proof of Work

### 1. Baseline Tests

Command: `./scripts/run_tests.sh`
Output:

```text
...................................... [ 76%]
............                           [100%]
50 passed in 0.32s
```

### 2. Smoke Test (Deterministic)

Command:

```bash
python3 scripts/smoke_kalshi_book.py \
  --ticker KXBTC-25DEC31 \
  --fixture-meta tests/fixtures/kalshi/market_metadata.json \
  --fixture-book tests/fixtures/kalshi/ok_book.json
```

Output:

```text
METADATA=OK
ELIGIBILITY=ELIGIBLE source=coinbase
BOOK_PARSE=OK depth=600.0
RESULT=PASS
```

*Exit Code: 0*

### 3. Shadow Runner Artifacts (Kalshi)

Command:

```bash
python3 scripts/run_shadow_stale_edge.py \
  --venue kalshi \
  --market KXBTC-25DEC31 \
  --minutes 1 \
  --loop-interval-sec 60 \
  --output artifacts/shadow/journal_kalshi.csv \
  --fixture-meta tests/fixtures/kalshi/market_metadata.json \
  --fixture-book tests/fixtures/kalshi/ok_book.json
```

Evidence (Files Updated):

```bash
find artifacts/shadow -type f -mmin -5 -print | sort
```

```text
artifacts/shadow/journal_kalshi.csv
```

Output (Artifacts):
`artifacts/shadow/journal_kalshi.csv` (Sample):

```csv
ts,market_id,now,official_mid,official_source,book_source,yes_bid,yes_ask,action,reason
1768323022247,KXBTC-25DEC31,1768323022247,93658.005,coinbase,kalshi,0.47,0.48,NO_TRADE,MODEL_WARMUP
```

*Note: `NO_TRADE` reason=`MODEL_WARMUP`.*

### 4. Tripwire (No Secrets)

*(Fallback - repo has no dedicated script yet)*

Command:

```bash
grep -rEI "API_KEY|SECRET|TOKEN|PASSWORD" . | grep -vE "tests/|artifacts/|\.git/|__pycache__|requirements.txt|ci.yml|discord-notify.yml" || echo "OK_NO_SECRETS_MATCHED"
```

Output:

```text
OK_NO_SECRETS_MATCHED
```

## Fail-Closed Guarantees

1. **Parse Ambiguity**: If `parse_kalshi_book` encounters missing fields, mixed shapes, or invalid scales, it returns `BookFailReason.PARSE_AMBIGUOUS` and the smoke script exits with code 2 (`FAIL`).
2. **Eligibility**: If rules are unsupported, close time is missing, or market is closed, `check_kalshi_eligibility` returns non-ELIGIBLE status. Smoke script exits with code 3.
3. **Feed Routing**: If official feed source is unknown/unsupported, `EligibilityResult.FEED_ROUTING_UNKNOWN` is returned, blocking execution.
4. **Shadow Safety**: Shadow runner requires explicit `--venue kalshi` and defaults to `NO_TRADE` / fails safe if auth is missing (unless fixtures are provided for offline verification).
