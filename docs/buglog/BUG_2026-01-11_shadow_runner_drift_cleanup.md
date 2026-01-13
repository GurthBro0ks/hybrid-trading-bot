# Shadow Runner Drift Cleanup

- Date: 2026-01-11
- Repo: /opt/pm_updown_bot_bundle
- Git SHA: 48fded2c5143dd6c8fbb7b75b39ddff54d27b613
- PROOF_DIR: /tmp/proof_shadow_runner_drift_cleanup_20260111T213422Z
- Context: prior NO_PROD_RUNNER_FOUND in `docs/buglog/BUG_2026-01-11_shadow_artifacts_contract_verify.md`

## What changed
- Added repo-owned entrypoint for single-cycle shadow runs.
- Versioned systemd unit templates under `ops/systemd/`.
- Replaced pyc-only runner dependencies with minimal .py modules (no more pyc copying for recorder/risk/strategy/venue imports).
- Updated systemd service to call repo entrypoint with flock.
- Added prod wiring smoke script in-repo.

## RUN_CMD (executed by entrypoint)
- `/usr/bin/python3 /opt/scripts/run_shadow_enhanced.py --once --ticker KALSHI-TEST-DEEP --output /opt/hybrid-trading-bot/artifacts/shadow/flight_recorder.csv`

## PASS/FAIL
- Repo root with `.github` used: PASS (`check_github.txt`)
- Runner CLI/flags proven via code inspection: PASS (`runner_main_args.txt`)
- Repo entrypoint + systemd ExecStart updated: PASS (`systemd_cat_after.txt`)
- Timer active: PASS (`status_timer.txt`)
- Manual run succeeds: PASS (`journal_service_manual.txt`)
- Artifacts exist + JSON fields readable: PASS (`ls_artifacts_shadow.txt`, `jq_summary_fields.txt`, `jq_health_fields.txt`)
- Timer updates mtimes: PASS (`stat_before.txt`, `stat_after.txt`)
- No-secrets tripwire: PASS (`rg_tripwire.txt`)
- Pyc-copy drift removed for runner deps: PASS (`pyc_list_before.txt`, `pyc_list_after.txt`)
- Smoke script verification: PASS (`smoke_verify_prod_wiring.txt`)

## Evidence excerpts

### CLI proof (runner flags)
```
$ sed -n '270,380p' /opt/scripts/run_shadow_enhanced.py
    parser.add_argument("--minutes", type=int, default=1)
    parser.add_argument("--loop-interval-sec", type=float, default=1.0)
    parser.add_argument("--venue", choices=["kalshi"], default="kalshi", help="Trading venue")
    parser.add_argument("--ticker", help="Market ticker (Kalshi)")
    parser.add_argument("--output", default="data/flight_recorder/stale_edge_kalshi_decisions.csv")
    parser.add_argument("--signals", action="store_true", default=True, help="Enable signal analysis")
    parser.add_argument("--once", action="store_true", help="Run a single iteration and exit")
```

### Systemd ExecStart (repo entrypoint)
```
$ systemctl cat hybrid-shadow-runner.service
WorkingDirectory=/opt/pm_updown_bot_bundle
Environment=PYTHONPATH=/opt/pm_updown_bot_bundle
Environment=SHADOW_ARTIFACTS_DIR=/opt/hybrid-trading-bot/artifacts/shadow
ExecStart=/usr/bin/flock -n /run/hybrid-shadow-runner/lock -c '/usr/bin/python3 /opt/pm_updown_bot_bundle/scripts/run_shadow_prod_entrypoint.py'
```

### Timer active
```
$ systemctl status hybrid-shadow-runner.timer --no-pager
Active: active (waiting) since Sun 2026-01-11 21:42:19 UTC; 13ms ago
Trigger: Sun 2026-01-11 21:42:45 UTC; 25s left
```

### Manual run + journald
```
$ journalctl -u hybrid-shadow-runner.service --no-pager -n 120
Jan 11 21:42:51 slimy-nuc1 flock[3331187]: Starting enhanced kalshi shadow run for 1 minutes...
Jan 11 21:42:51 slimy-nuc1 flock[3331187]: Signal analysis: ENABLED
Jan 11 21:42:51 slimy-nuc1 flock[3331187]: 2026-01-11 21:42:51,389 INFO Completed single iteration (--once)
Jan 11 21:42:51 slimy-nuc1 flock[3331187]: 2026-01-11 21:42:51,390 INFO Reasons: {'NO_DATA': 1}
Jan 11 21:42:51 slimy-nuc1 systemd[1]: Finished hybrid-shadow-runner.service - Hybrid Trading Bot - Shadow Runner (Artifacts Emitter).
```

### Artifacts + JSON fields
```
$ ls -la /opt/hybrid-trading-bot/artifacts/shadow
-rw-rw-r-- 1 slimy slimy 3209 Jan 11 21:42 flight_recorder.csv
-rw------- 1 slimy slimy  368 Jan 11 21:42 health.json
-rw------- 1 slimy slimy 1026 Jan 11 21:42 latest_journal.csv
-rw------- 1 slimy slimy  386 Jan 11 21:42 latest_summary.json

$ jq -r '.schema_version,.mode,.last_refresh,.last_error' /opt/hybrid-trading-bot/artifacts/shadow/latest_summary.json
shadow_summary_v1
SHADOW
2026-01-11T21:42:51.360798+00:00

$ jq -r '.schema_version,.mode,.last_run_at,.last_error' /opt/hybrid-trading-bot/artifacts/shadow/health.json
shadow_health_v1
SHADOW
2026-01-11T21:42:51.360825+00:00
```

### Timer updates mtimes
```
$ stat /opt/hybrid-trading-bot/artifacts/shadow/latest_summary.json /opt/hybrid-trading-bot/artifacts/shadow/health.json
Modify: 2026-01-11 21:42:51.368649625 +0000
Modify: 2026-01-11 21:42:51.380649843 +0000

$ stat /opt/hybrid-trading-bot/artifacts/shadow/latest_summary.json /opt/hybrid-trading-bot/artifacts/shadow/health.json
Modify: 2026-01-11 21:43:52.155754392 +0000
Modify: 2026-01-11 21:43:52.163754537 +0000
```

### No-secrets tripwire
```
$ rg -n -i "api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password" /opt/hybrid-trading-bot/artifacts/shadow
OK_NO_SECRETS_MATCHED
```

### Pyc-copy drift removal
```
$ find /opt/pm_updown_bot_bundle/recorder /opt/pm_updown_bot_bundle/risk /opt/pm_updown_bot_bundle/strategies /opt/pm_updown_bot_bundle/venues -maxdepth 2 -type f -name '*.pyc'
/opt/pm_updown_bot_bundle/recorder/trade_journal.pyc
/opt/pm_updown_bot_bundle/risk/eligibility.pyc
/opt/pm_updown_bot_bundle/risk/rules.pyc
/opt/pm_updown_bot_bundle/strategies/stale_edge.pyc
/opt/pm_updown_bot_bundle/venues/kalshi.pyc

$ find /opt/pm_updown_bot_bundle/recorder /opt/pm_updown_bot_bundle/risk /opt/pm_updown_bot_bundle/strategies /opt/pm_updown_bot_bundle/venues -maxdepth 2 -type f -name '*.pyc'
/opt/pm_updown_bot_bundle/strategies/reasons.pyc
/opt/pm_updown_bot_bundle/venues/base.pyc
/opt/pm_updown_bot_bundle/venues/kalshi_classify.pyc
```

### Smoke verification
```
$ bash scripts/smoke/verify-prod-shadow-runner-wiring.sh
OK_SERVICE_ENTRYPOINT
OK_TIMER_ACTIVE
OK_ARTIFACTS_PRESENT
OK_JQ_FIELDS
OK_TRIPWIRE
OK_MTIME_SKIP_NO_SUDO
```
