# Phase 8B.1: Polymarket Discovery CLOB Readiness Filter (Probed, Typed)

## Summary

Implemented a predictable "CLOB readiness" filter for Polymarket discovery.

- **Discovery**: Fetches candidates from Gamma API.
- **Filtering**: Probes `https://clob.polymarket.com/book` (HEAD/GET) with rate limiting.
- **Buckets**: Splits candidates into `ready` (OK/200) and `not_ready` (404/429/5xx).
- **Verification**: `verify_shadow_pipeline.py` ensures we can select a READY candidate and successfully fetch its VenueBook.

## Proof Assessment

**Command**:

```bash
python3 scripts/verify_shadow_pipeline.py 2>&1 | tee "$PROOF_DIR/verify_shadow_pipeline.txt"
```

**Proof Directory**: `/tmp/proof_phase8B1_20260113T010235Z`

**Key Result**:
`RESULT: discovered=20 ready=20 selected=516938:2853768819561879023657600399360829876689515906714535926781067187993853038980 venuebook=OK`

**Ready Example**:
`READY_EXAMPLE market_id=516938 token_id=2853768819561879023657600399360829876689515906714535926781067187993853038980`

**Secrets**:
No secrets printed. Logs are safe.

## Outcome

CLOB readiness filter selects a ready token and produces OK VenueBook (or NO_BBO/THIN_BOOK).
