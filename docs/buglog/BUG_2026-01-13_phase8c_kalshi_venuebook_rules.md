# BUG_2026-01-13_phase8c_kalshi_venuebook_rules.md

## Provenance

- **Host**: NUC1
- **Branch**: phase8b.2-test-gate
- **HEAD**: d26e12e (baseline) + edits
- **Python**: 3.12 (approx)
- **Proof Run Time UTC**: 2026-01-13T16:38:00Z (approx)

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
  --loop-interval-sec 1 \
  --output artifacts/shadow/journal_kalshi.csv \
  --fixture-meta tests/fixtures/kalshi/market_metadata.json \
  --fixture-book tests/fixtures/kalshi/ok_book.json
```

Output (Artifacts):
`artifacts/shadow/journal_kalshi.csv` (Sample):

```csv
ts,market_id,now,official_mid,official_source,book_source,pm_yes_bid,pm_yes_ask,action
1768322288683,KXBTC-25DEC31,1768322288683,93501.905,coinbase,kalshi,0.47,0.48,NO_TRADE
1768322289825,KXBTC-25DEC31,1768322289825,93537.995,coinbase,kalshi,0.47,0.48,NO_TRADE
```

*Note: `NO_TRADE` due to MODEL_WARMUP or SAFE_MODE, but artifacts are emitted and parsed correctly.*

### 4. Tripwire (No Secrets)

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
