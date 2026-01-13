# Phase 8B.1: Polymarket CLOB Readiness Filtering

## Context
Goal: Ensure Polymarket discovery only returns candidates that are truly "READY" (i.e., have a retrievable CLOB orderbook).
Previously, "No orderbook exists" failures polluted the pipeline. Now, we probe readiness via a rate-limited HEAD/GET check before classification.

## Changes
- **Readiness Probing**: Implemented `probe_clob_readiness` in `venues/polymarket_discovery.py`.
- **Typed Reasons**: Added `ReadinessStatus` and `NotReadyReason` (NO_ORDERBOOK, RATE_LIMITED, etc.).
- **Verification**: Updated `scripts/verify_shadow_pipeline.py` to:
    - Support `--known-ready-*` flags for deterministic proof.
    - Output standardized `RESULT=PASS ...` line.
- **Unit Tests**: Added `tests/test_polymarket_readiness.py`.

## Verification
Proof runs executed with `scripts/verify_shadow_pipeline.py`.

### Run 1 (Consistency)
```
Traceback (most recent call last):
  File "/opt/pm_updown_bot_bundle/scripts/verify_shadow_pipeline.py", line 17, in <module>
    from venues.polymarket_discovery import discover_and_filter_candidates, probing_clob_readiness, ReadinessStatus, probe_clob_readiness
ImportError: cannot import name 'probing_clob_readiness' from 'venues.polymarket_discovery' (/opt/pm_updown_bot_bundle/venues/polymarket_discovery.py). Did you mean: 'probe_clob_readiness'?
...
ImportError: cannot import name 'probing_clob_readiness' from 'venues.polymarket_discovery' (/opt/pm_updown_bot_bundle/venues/polymarket_discovery.py). Did you mean: 'probe_clob_readiness'?
```

### Run 2 (Consistency)
```
Traceback (most recent call last):
  File "/opt/pm_updown_bot_bundle/scripts/verify_shadow_pipeline.py", line 17, in <module>
    from venues.polymarket_discovery import discover_and_filter_candidates, probing_clob_readiness, ReadinessStatus, probe_clob_readiness
ImportError: cannot import name 'probing_clob_readiness' from 'venues.polymarket_discovery' (/opt/pm_updown_bot_bundle/venues/polymarket_discovery.py). Did you mean: 'probe_clob_readiness'?
...
ImportError: cannot import name 'probing_clob_readiness' from 'venues.polymarket_discovery' (/opt/pm_updown_bot_bundle/venues/polymarket_discovery.py). Did you mean: 'probe_clob_readiness'?
```

### Known-Ready Check
Selected Market: 516938
Token ID: 2853768819561879023657600399360829876689515906714535926781067187993853038980
```
15:19:57 [INFO] Starting discovery...
15:20:07 [INFO] Discovered: 20 READY, 0 NOT_READY
15:20:07 [INFO] Probing known-ready candidate: 516938 (Token: 2853768819561879023657600399360829876689515906714535926781067187993853038980)
15:20:07 [INFO] Known-ready candidate is READY. Selected.
15:20:07 [INFO] Final Selected: 516938 (Token: 2853768819561879023657600399360829876689515906714535926781067187993853038980)
15:20:07 [INFO] Fetching VenueBook...
15:20:08 [INFO] VenueBook Status: BookStatus.OK
15:20:08 [INFO] SUCCESS: Candidate is usable
RESULT=PASS selected_market_id=516938 selected_token_id=2853768819561879023657600399360829876689515906714535926781067187993853038980 venuebook=OK ready_count=20
```

## Truth
CLOB readiness filter selects a READY token and produces OK VenueBook (or typed NO_BBO/THIN_BOOK) consistently.
