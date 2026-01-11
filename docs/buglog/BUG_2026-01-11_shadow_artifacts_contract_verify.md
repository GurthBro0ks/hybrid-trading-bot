# Shadow Artifacts Contract Verification

- Date: 2026-01-11T20:16:48+00:00
- Git SHA: 48fded2c5143dd6c8fbb7b75b39ddff54d27b613
- PROOF_DIR: /tmp/proof_shadow_artifacts_verify_20260111T201648Z

## What Was Verified
- Repo root verified, proof capture set up, and git baseline recorded.
- Inventory of Shadow Artifacts contract files and test/scripts/workflow locations.
- Recorder package provenance, schema columns, writer safety (atomic writes + fsync, bounded rows, call-time max rows, no assert-only enforcement), and sanitizer behavior.
- Runner wiring evidence via systemd/docker/cron and /opt/scripts presence.
- Local artifact emission using repo smoke generator (fallback) with artifact presence + JSON fields.
- Secret tripwire scan against emitted artifacts.
- Journal CSV header equals JOURNAL_COLUMNS.
- Pytest and offline CI gate; workflow triggers validated.

## Exact Commands
```bash
pwd
ls -la | head
test -d .github || (echo "FATAL: not in repo root (no .github/)"; exit 2)
export PROOF_DIR="/tmp/proof_shadow_artifacts_verify_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$PROOF_DIR"
export BUGLOG="docs/buglog/BUG_$(date +%Y-%m-%d)_shadow_artifacts_contract_verify.md"
mkdir -p docs/buglog
date -Is | tee "$PROOF_DIR/date.txt"
git rev-parse HEAD | tee "$PROOF_DIR/git_head.txt"
git status --porcelain | tee "$PROOF_DIR/git_status.txt"
ls -la docs/artifacts | tee "$PROOF_DIR/ls_docs_artifacts.txt" || true
ls -la recorder | tee "$PROOF_DIR/ls_recorder.txt" || true
ls -la scripts/smoke | tee "$PROOF_DIR/ls_scripts_smoke.txt" || true
ls -la .github/workflows | tee "$PROOF_DIR/ls_workflows.txt" || true
ls -la tests | tee "$PROOF_DIR/ls_tests.txt" || true
# key file presence loop (see inventory_key_files.txt)
find recorder -maxdepth 2 -type f | sort | tee "$PROOF_DIR/recorder_file_list.txt"
find recorder -name "*.pyc" -o -name "__pycache__" | tee "$PROOF_DIR/recorder_pyc_list.txt" || true
python3 - <<'PY' | tee "$PROOF_DIR/recorder_import_provenance.txt"
import recorder, sys
print("recorder.__file__ =", recorder.__file__)
print("sys.path[0:5] =", sys.path[0:5])
PY
python3 - <<'PY' | tee "$PROOF_DIR/recorder_import_provenance_expanded.txt"
import recorder, sys
print("recorder.__file__ =", recorder.__file__)
print("sys.path entries:")
for i, p in enumerate(sys.path[:8]):
    print(f"  [{i}] {p}")
PY
python3 - <<'PY' | tee "$PROOF_DIR/journal_schema_introspect.txt"
from recorder.journal_schema import JOURNAL_COLUMNS
print("JOURNAL_COLUMNS_count", len(JOURNAL_COLUMNS))
print("first_10", JOURNAL_COLUMNS[:10])
print("last_10", JOURNAL_COLUMNS[-10:])
expected = [
  "signal_book_arbitrage_edge_bps",
  "signal_book_arbitrage_reason",
  "signal_book_arbitrage_confidence",
  "signal_book_staleness_edge_bps",
  "signal_book_staleness_reason",
  "signal_book_staleness_confidence",
]
missing = [c for c in expected if c not in JOURNAL_COLUMNS]
print("missing_expected_signal_cols", missing)
PY
python3 - <<'PY' | tee "$PROOF_DIR/journal_schema_introspect_expanded.txt"
from recorder.journal_schema import JOURNAL_COLUMNS
print("JOURNAL_COLUMNS_count", len(JOURNAL_COLUMNS))
print("first_10", JOURNAL_COLUMNS[:10])
print("last_10", JOURNAL_COLUMNS[-10:])
expected = [
  "signal_book_arbitrage_edge_bps",
  "signal_book_arbitrage_reason",
  "signal_book_arbitrage_confidence",
  "signal_book_staleness_edge_bps",
  "signal_book_staleness_reason",
  "signal_book_staleness_confidence",
]
missing = [c for c in expected if c not in JOURNAL_COLUMNS]
print("expected_signal_cols_present", len(missing) == 0)
print("missing_expected_signal_cols", missing)
print("signal_cols_excerpt", [c for c in JOURNAL_COLUMNS if c.startswith("signal_")][:10])
PY
sed -n '1,240p' recorder/shadow_artifacts.py | tee "$PROOF_DIR/shadow_artifacts_py_head.txt"
sed -n '240,520p' recorder/shadow_artifacts.py | tee "$PROOF_DIR/shadow_artifacts_py_tail.txt"
rg -n "os\.replace|fsync|mkstemp|NamedTemporaryFile|\.tmp\.|atomic" recorder/shadow_artifacts.py | tee "$PROOF_DIR/rg_atomic_write.txt" || true
rg -n "SHADOW_JOURNAL_MAX_ROWS|getenv\(\"SHADOW_JOURNAL_MAX_ROWS\"|journal_max_rows" recorder/shadow_artifacts.py | tee "$PROOF_DIR/rg_max_rows.txt" || true
rg -n "^\s*assert\b" recorder/shadow_artifacts.py | tee "$PROOF_DIR/rg_asserts.txt" || true
rg -n "api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password" recorder/shadow_artifacts.py | tee "$PROOF_DIR/rg_secret_words_in_writer.txt" || true
rg -n "JOURNAL_COLUMNS|get_max_rows|sanitize_" recorder/shadow_artifacts.py | tee "$PROOF_DIR/rg_schema_sanitize_usage.txt" || true
python3 - <<'PY' | tee "$PROOF_DIR/sanitizer_behavior.txt"
from recorder.shadow_artifacts import sanitize_text
danger = "Authorization: Bearer abc123 api_key=XYZ secret=foo token=bar private_key=baz password=qux"
safe = sanitize_text(danger)
print("IN:", danger)
print("OUT:", safe)
low = safe.lower()
keywords = ["authorization", "bearer", "api_key", "api-key", "secret", "token", "private_key", "private-key", "password"]
present = [k for k in keywords if k in low]
print("keywords_still_present", present)
print("len_out", len(safe))
PY
ls -la scripts | tee "$PROOF_DIR/ls_scripts.txt"
rg -n "write_shadow_artifacts|shadow_artifacts|artifacts/shadow|latest_summary|latest_journal|health\.json" scripts | tee "$PROOF_DIR/rg_runner_wiring_scripts.txt" || true
rg -n "write_shadow_artifacts" -S . | tee "$PROOF_DIR/rg_write_shadow_artifacts_repo.txt" || true
ls -la /opt/scripts 2>/dev/null | tee "$PROOF_DIR/ls_opt_scripts.txt" || true
test -f /opt/scripts/run_shadow_enhanced.py && echo "FOUND:/opt/scripts/run_shadow_enhanced.py" | tee "$PROOF_DIR/opt_runner_found.txt" || true
systemctl list-units --type=service | rg -i "shadow|trader|bot|hybrid|stale|edge" | tee "$PROOF_DIR/systemd_units_grep.txt" || true
systemctl cat hybrid-dashboard.service | tee "$PROOF_DIR/systemd_cat_hybrid-dashboard.service.txt" || true
systemctl status hybrid-dashboard.service --no-pager | tee "$PROOF_DIR/systemd_status_hybrid-dashboard.service.txt" || true
systemctl cat hybrid-engine.service | tee "$PROOF_DIR/systemd_cat_hybrid-engine.service.txt" || true
systemctl status hybrid-engine.service --no-pager | tee "$PROOF_DIR/systemd_status_hybrid-engine.service.txt" || true
rg -n "run_shadow|shadow_enhanced|shadow_artifacts" /etc/systemd /lib/systemd 2>/dev/null | tee "$PROOF_DIR/rg_systemd_shadow.txt" || true
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Command}}' | tee "$PROOF_DIR/docker_ps.txt" || true
ls -la docker-compose*.yml compose*.yml 2>/dev/null | tee "$PROOF_DIR/ls_compose.txt" || true
rg -n "run_shadow|stale_edge|python3 scripts/|/opt/scripts/" -S . 2>/dev/null | tee "$PROOF_DIR/rg_compose_runner.txt" || true
crontab -l 2>/dev/null | tee "$PROOF_DIR/crontab.txt" || true
ls -la /etc/cron.* 2>/dev/null | tee "$PROOF_DIR/ls_etc_cron.txt" || true
rg -n "run_shadow|shadow_enhanced|stale_edge|artifacts/shadow" /etc/cron.* /etc/crontab 2>/dev/null | tee "$PROOF_DIR/rg_cron_shadow.txt" || true
if [ -s "$PROOF_DIR/rg_systemd_shadow.txt" ]; then echo "SYSTEMD_SHADOW_MATCHES=YES"; else echo "SYSTEMD_SHADOW_MATCHES=NO"; fi | tee "$PROOF_DIR/systemd_shadow_match_check.txt"
if [ -s "$PROOF_DIR/rg_cron_shadow.txt" ]; then echo "CRON_SHADOW_MATCHES=YES"; else echo "CRON_SHADOW_MATCHES=NO"; fi | tee "$PROOF_DIR/cron_shadow_match_check.txt"
if [ -s "$PROOF_DIR/docker_ps.txt" ]; then echo "DOCKER_PS_NONEMPTY=YES"; else echo "DOCKER_PS_NONEMPTY=NO"; fi | tee "$PROOF_DIR/docker_ps_check.txt"
{ echo "RECORDER_FILES:"; sed -n '1,10p' "$PROOF_DIR/recorder_file_list.txt"; echo "RECORDER_PYC:"; cat "$PROOF_DIR/recorder_pyc_list.txt"; } | tee "$PROOF_DIR/recorder_pyc_summary.txt"
SHADOW_ARTIFACTS_DIR=/tmp python3 scripts/smoke/gen_mock_shadow_artifacts.py --help | tee "$PROOF_DIR/gen_mock_help.txt"
SHADOW_ARTIFACTS_DIR=artifacts/shadow python3 scripts/smoke/gen_mock_shadow_artifacts.py 2>&1 | tee "$PROOF_DIR/run_once.log"
ls -la artifacts/shadow | head | tee "$PROOF_DIR/ls_shadow_head.txt"
jq -r '.schema_version,.mode,.last_refresh,.last_error' artifacts/shadow/latest_summary.json | tee "$PROOF_DIR/jq_summary_fields.txt"
jq -r '.schema_version,.mode,.last_run_at,.last_error' artifacts/shadow/health.json | tee "$PROOF_DIR/jq_health_fields.txt"
rg -n -i "api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password" artifacts/shadow && echo "FAIL_SECRETS_MATCHED" || echo "OK_NO_SECRETS_MATCHED" | tee "$PROOF_DIR/rg_tripwire.txt"
python3 - <<'PY' | tee "$PROOF_DIR/journal_header_check.txt"
import csv
from recorder.journal_schema import JOURNAL_COLUMNS
p="artifacts/shadow/latest_journal.csv"
with open(p,newline="") as f:
    r=csv.reader(f)
    header=next(r)
print("header_matches:", header==JOURNAL_COLUMNS)
print("header_len:", len(header), "schema_len:", len(JOURNAL_COLUMNS))
PY
python3 - <<'PY' | tee "$PROOF_DIR/journal_header_check_expanded.txt"
import csv
from recorder.journal_schema import JOURNAL_COLUMNS
p="artifacts/shadow/latest_journal.csv"
with open(p,newline="") as f:
    r=csv.reader(f)
    header=next(r)
print("header_matches:", header==JOURNAL_COLUMNS)
print("header_len:", len(header))
print("schema_len:", len(JOURNAL_COLUMNS))
print("header_first_10:", header[:10])
print("header_last_10:", header[-10:])
PY
pytest -q | tee "$PROOF_DIR/pytest.txt"
bash scripts/smoke/verify-shadow-artifacts-ci.sh | tee "$PROOF_DIR/ci_gate_local.txt"
sed -n '1,220p' .github/workflows/shadow-artifacts-ci.yml | tee "$PROOF_DIR/workflow_head.txt"
```

## Checks (PASS/FAIL)
### File Inventory - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/inventory_key_files.txt
```
FOUND: docs/artifacts/SHADOW_ARTIFACTS_CONTRACT.md
FOUND: recorder/journal_schema.py
FOUND: recorder/shadow_artifacts.py
FOUND: recorder/__init__.py
FOUND: tests/test_shadow_artifacts_contract.py
FOUND: tests/test_shadow_artifacts_no_secrets.py
FOUND: scripts/smoke/gen_mock_shadow_artifacts.py
FOUND: scripts/smoke/verify-shadow-artifacts-ci.sh
FOUND: .github/workflows/shadow-artifacts-ci.yml
FOUND: docs/buglog/BUG_2026-01-11_shadow_artifacts_contract.md
```

### Recorder Package + Schema + Writer Safety - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/recorder_import_provenance_expanded.txt
```
recorder.__file__ = /opt/pm_updown_bot_bundle/recorder/__init__.py
sys.path entries:
  [0] 
  [1] /usr/lib/python312.zip
  [2] /usr/lib/python3.12
  [3] /usr/lib/python3.12/lib-dynload
  [4] /home/slimy/.local/lib/python3.12/site-packages
  [5] /usr/local/lib/python3.12/dist-packages
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/journal_schema_introspect_expanded.txt
```
JOURNAL_COLUMNS_count 52
first_10 ['ts', 'market_id', 'now', 'market_end_ts', 'venue', 'symbol', 'official_required_venue', 'official_used_venue', 'official_used_endpoint', 'official_mid']
last_10 ['kill_switch', 'params_hash', 'signal_book_arbitrage_edge_bps', 'signal_book_arbitrage_reason', 'signal_book_arbitrage_confidence', 'signal_book_staleness_edge_bps', 'signal_book_staleness_reason', 'signal_book_staleness_confidence', 'arb_cost_cents', 'arb_edge_cents']
expected_signal_cols_present True
missing_expected_signal_cols []
signal_cols_excerpt ['signal_book_arbitrage_edge_bps', 'signal_book_arbitrage_reason', 'signal_book_arbitrage_confidence', 'signal_book_staleness_edge_bps', 'signal_book_staleness_reason', 'signal_book_staleness_confidence']
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/rg_atomic_write.txt
```
1:"""Shadow artifacts writer with atomic writes and secret sanitization.
7:- Atomic writes (tmp + fsync + os.replace)
113:def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
114:    """Write JSON atomically using tmp + fsync + replace.
132:    # Write to temp file, fsync, then replace
133:    fd, tmp_path = tempfile.mkstemp(
140:            os.fsync(f.fileno())
141:        os.replace(tmp_path, path)
151:def atomic_write_csv_bounded(
158:    """Write CSV atomically with bounded rows.
200:    # Write to temp file, fsync, then replace
201:    fd, tmp_path = tempfile.mkstemp(
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/shadow_artifacts_py_tail.txt
```

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Resolve paths
    base_dir = resolve_artifacts_dir(artifacts_dir)
    summary_path = base_dir / SUMMARY_FILE
    journal_path = base_dir / JOURNAL_FILE
    health_path = base_dir / HEALTH_FILE

    # Use provided header or default
    cols = header_cols if header_cols is not None else JOURNAL_COLUMNS

    # Get max rows at call time (not import time)
    max_rows = get_max_rows()
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/sanitizer_behavior.txt
```
IN: Authorization: Bearer abc123 api_key=XYZ secret=foo token=bar private_key=baz password=qux
OUT: [REDACTED] [REDACTED] [REDACTED] [REDACTED]
keywords_still_present []
len_out 43
```
NOTE: .pyc-only artifact observed (trade_journal).
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/recorder_pyc_summary.txt
```
RECORDER_FILES:
recorder/__init__.py
recorder/__pycache__/__init__.cpython-312.pyc
recorder/__pycache__/journal_schema.cpython-312.pyc
recorder/__pycache__/shadow_artifacts.cpython-312.pyc
recorder/__pycache__/trade_journal.cpython-312.pyc
recorder/journal_schema.py
recorder/shadow_artifacts.py
RECORDER_PYC:
recorder/__pycache__
```

### Runner Wiring (Systemd/Docker/Cron) - FAIL (runner not proven)
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/systemd_units_grep.txt
```
  hybrid-dashboard.service                                                                  loaded active     running      Hybrid Trading Bot Dashboard
  hybrid-engine.service                                                                     loaded active     running      Hybrid Trading Bot Engine
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/systemd_cat_hybrid-engine.service.txt
```
# /etc/systemd/system/hybrid-engine.service
[Unit]
Description=Hybrid Trading Bot Engine
After=network.target

[Service]
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/systemd_shadow_match_check.txt
```
SYSTEMD_SHADOW_MATCHES=NO
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/cron_shadow_match_check.txt
```
CRON_SHADOW_MATCHES=NO
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/docker_ps_check.txt
```
DOCKER_PS_NONEMPTY=NO
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/opt_runner_found.txt
```
FOUND:/opt/scripts/run_shadow_enhanced.py
```

### Artifacts Emitted (Local Smoke Fallback) - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/ls_shadow_head.txt
```
total 20
drwxrwxr-x 2 slimy slimy 4096 Jan 11 20:18 .
drwxrwxr-x 6 slimy slimy 4096 Jan 11 18:38 ..
-rw------- 1 slimy slimy  483 Jan 11 20:18 health.json
-rw------- 1 slimy slimy 1389 Jan 11 20:18 latest_journal.csv
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/run_once.log
```
Generating mock artifacts in: artifacts/shadow
SUCCESS: Mock artifacts generated
```

### JSON Field Checks - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/jq_summary_fields.txt
```
shadow_summary_v1
SHADOW
2026-01-11T20:18:23.407864+00:00
Failed to connect: [REDACTED] [REDACTED] [REDACTED] [REDACTED] [REDACTED]
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/jq_health_fields.txt
```
shadow_health_v1
SHADOW
2026-01-11T20:18:23.407885+00:00
Failed to connect: [REDACTED] [REDACTED] [REDACTED] [REDACTED] [REDACTED]
```

### Tripwire No-Secrets - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/ci_gate_local.txt
```

=== Step 4: Check file sizes ===
PASS: File sizes within limits (summary: 492B, health: 483B)

=== Step 5: TRIPWIRE - Check for secrets ===
OK_NO_SECRETS_MATCHED
PASS: No secrets found in artifacts

=== Step 6: Show sanitized content (debug) ===
```
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/rg_tripwire.txt
```
OK_NO_SECRETS_MATCHED
```

### Journal Header Match - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/journal_header_check_expanded.txt
```
header_matches: True
header_len: 52
schema_len: 52
header_first_10: ['ts', 'market_id', 'now', 'market_end_ts', 'venue', 'symbol', 'official_required_venue', 'official_used_venue', 'official_used_endpoint', 'official_mid']
header_last_10: ['kill_switch', 'params_hash', 'signal_book_arbitrage_edge_bps', 'signal_book_arbitrage_reason', 'signal_book_arbitrage_confidence', 'signal_book_staleness_edge_bps', 'signal_book_staleness_reason', 'signal_book_staleness_confidence', 'arb_cost_cents', 'arb_edge_cents']
```

### Pytest - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/pytest.txt
```
.................................................                        [100%]
49 passed in 0.43s
```

### Offline CI Gate - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/ci_gate_local.txt
```
=== Shadow Artifacts Contract CI Verification ===
Project root: /opt/pm_updown_bot_bundle

Using temp directory: /tmp/tmp.FJDyeNlOKP

=== Step 1: Generate mock artifacts ===
Generating mock artifacts in: /tmp/tmp.FJDyeNlOKP/artifacts/shadow
SUCCESS: Mock artifacts generated
PASS: Mock artifacts generated

=== Step 2: Verify files exist ===
PASS: All required files exist
```

### Workflow Scope - PASS
PROOF: /tmp/proof_shadow_artifacts_verify_20260111T201648Z/workflow_head.txt
```
name: shadow-artifacts-ci

on:
  push:
    branches: [main]
    paths:
      - 'recorder/**'
      - 'scripts/smoke/**'
      - 'tests/test_shadow_artifacts*.py'
      - '.github/workflows/shadow-artifacts-ci.yml'
  pull_request:
    paths:
```
