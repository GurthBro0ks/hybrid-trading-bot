# BUG_2026-01-10_fr_strict_thinbook_v2.md

## Preflight

- **Hostname**: slimy-nuc1
- **Date**: 2026-01-10T18:13:20Z
- **PWD**: `/opt/pm_updown_bot_bundle`
- **Branch**: `feat/fr-strict-thinbook-v2`
- **SHA**: `29a087dbade1a40a4a76a07d051f25a0bd985f3f`
- **Status**: DIRTY (Patch attached at `artifacts/proof_20260110_181320/local_dirty_tree.patch`)

## Execution

### 1. Tests

Command: `pytest tests/test_stale_edge.py`
Outcome: PASS (Exit 0)

### 2. Shadow Run

Command: `python3 scripts/run_shadow_stale_edge.py --output ... --minutes 1`
Outcome: PASS (Exit 0)
Summary: `decisions=28 would_trades=0 avg_edge=0.0000 staleness_refusals=28`
(Refusals due to OFFICIAL_FEED_UNAVAILABLE - Binance Geo-Block)

### 3. Verification

Log: `artifacts/proof_20260110_181320/verify.log`
Status: PASS
Schema Check:

- thin_book_reason: OK
- thin_book_threshold_depth_usd: OK
- thin_book_threshold_qty: OK
- thin_book_spread_bps: OK

## Artifacts

- **Proof Directory**: `artifacts/proof_20260110_181320`
- **Env Snapshot**: `env_snapshot.txt` (Sanitized)
- **Patch**: `local_dirty_tree.patch`
- **Journal**: `journal.csv`

## Reason Histogram (Sample)

```text
OFFICIAL_FEED_MISSING: 28
```

(No THIN_BOOK reasons triggered in live shadow run due to upstream feed block, but logic verified in unit tests).
