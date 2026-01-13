# Shadow Runner Repo Self-Containment Verification

Date: 2026-01-11T22:14:21+00:00
Git SHA: 8f35cfa42c256dd7ff050c496cf0a59a389cb872
Canonical repo: /opt/pm_updown_bot_bundle
PROOF_DIR: /tmp/proof_shadow_repo_selfcontained_20260111T220308Z

## Context
Goal: repo-owned runner + entrypoint, systemd template/host sync, stub audit/tests, ignore artifacts, and proof that timer updates artifacts without /opt/scripts dependency.

## Checks (PASS/FAIL)
| Check | Result | Evidence |
| --- | --- | --- |
| Repo root with .github + git remote | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/ls_dot_github.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/git_remote.txt |
| Runner copied into repo (no /opt/scripts dependency) | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/sha_runner_copy.txt |
| Repo entrypoint is config-driven (no hardcoded ticker/output) | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/entrypoint_head.txt |
| Systemd ExecStart uses repo entrypoint + envfile | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/systemd_cat_service.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/prove_entrypoint_used.txt |
| Stub modules labeled STUB_ONLY + fail-closed | PASS | repo files + /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/pytest_after_stubs.txt |
| Artifacts ignored by git | PASS | .gitignore |
| Manual service run succeeds | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/systemd_status_service_manual.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/journal_manual.txt |
| Timer updates artifacts (mtime change) | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/stat_before.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/stat_after.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/journal_after_timer.txt |
| Artifacts JSON fields present | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/jq_summary_fields.txt, /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/jq_health_fields.txt |
| No-secrets tripwire (artifacts) | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/rg_tripwire_artifacts.txt |
| Repo tripwire hits are doc/test examples only | PASS (doc/test strings) | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/rg_tripwire_repo.txt |
| Pytest passes | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/pytest_after_stubs.txt |
| Offline CI gate passes | PASS | /tmp/proof_shadow_repo_selfcontained_20260111T220308Z/offline_ci_gate.txt |

## Runner invocation
Systemd ExecStart (repo-only):
- /usr/bin/flock -n /run/hybrid-shadow-runner/lock -c '/usr/bin/python3 /opt/pm_updown_bot_bundle/scripts/run_shadow_prod_entrypoint.py'

## Evidence excerpts
### systemd unit (repo-only entrypoint + envfile)

Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=/opt/pm_updown_bot_bundle
Environment=SHADOW_ARTIFACTS_DIR=/opt/pm_updown_bot_bundle/artifacts/shadow
Environment=SHADOW_JOURNAL_MAX_ROWS=500
Environment=SHADOW_ONCE=1
EnvironmentFile=-/etc/default/hybrid-shadow-runner

RuntimeDirectory=hybrid-shadow-runner
RuntimeDirectoryMode=0755
ExecStart=/usr/bin/flock -n /run/hybrid-shadow-runner/lock -c '/usr/bin/python3 /opt/pm_updown_bot_bundle/scripts/run_shadow_prod_entrypoint.py'

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

### Entry point config line + successful run
9:Jan 11 22:00:00 slimy-nuc1 flock[3395949]: 2026-01-11 22:00:00,186 INFO Completed single iteration (--once)
20:Jan 11 22:01:00 slimy-nuc1 flock[3399742]: 2026-01-11 22:01:00,368 INFO Completed single iteration (--once)
31:Jan 11 22:02:01 slimy-nuc1 flock[3403583]: 2026-01-11 22:02:01,160 INFO Completed single iteration (--once)
42:Jan 11 22:03:01 slimy-nuc1 flock[3407379]: 2026-01-11 22:03:01,406 INFO Completed single iteration (--once)
53:Jan 11 22:04:02 slimy-nuc1 flock[3411380]: 2026-01-11 22:04:02,177 INFO Completed single iteration (--once)
62:Jan 11 22:05:02 slimy-nuc1 flock[3415256]: SHADOW_RUNNER_CONFIG mode=SHADOW ticker=NONE output=/opt/pm_updown_bot_bundle/artifacts/shadow/flight_recorder.csv artifacts_dir=/opt/pm_updown_bot_bundle/artifacts/shadow
68:Jan 11 22:06:03 slimy-nuc1 flock[3419313]: SHADOW_RUNNER_CONFIG mode=SHADOW ticker=NONE output=/opt/pm_updown_bot_bundle/artifacts/shadow/flight_recorder.csv artifacts_dir=/opt/pm_updown_bot_bundle/artifacts/shadow
74:Jan 11 22:07:03 slimy-nuc1 flock[3423253]: SHADOW_RUNNER_CONFIG mode=SHADOW ticker=NONE output=/opt/pm_updown_bot_bundle/artifacts/shadow/flight_recorder.csv artifacts_dir=/opt/pm_updown_bot_bundle/artifacts/shadow

### Timer-driven mtime update
  File: artifacts/shadow/latest_summary.json
  Size: 386       	Blocks: 8          IO Block: 4096   regular file
Device: 252,0	Inode: 7793198     Links: 1
Access: (0600/-rw-------)  Uid: ( 1000/   slimy)   Gid: ( 1000/   slimy)
Access: 2026-01-11 22:12:04.240631957 +0000
Modify: 2026-01-11 22:11:56.701476174 +0000
Change: 2026-01-11 22:11:56.708476319 +0000
 Birth: 2026-01-11 22:11:56.701476174 +0000
  File: artifacts/shadow/health.json
  Size: 368       	Blocks: 8          IO Block: 4096   regular file
Device: 252,0	Inode: 7793195     Links: 1
Access: (0600/-rw-------)  Uid: ( 1000/   slimy)   Gid: ( 1000/   slimy)
...
  File: artifacts/shadow/latest_summary.json
  Size: 386       	Blocks: 8          IO Block: 4096   regular file
Device: 252,0	Inode: 7793441     Links: 1
Access: (0600/-rw-------)  Uid: ( 1000/   slimy)   Gid: ( 1000/   slimy)
Access: 2026-01-11 22:12:57.295721522 +0000
Modify: 2026-01-11 22:12:57.295721522 +0000
Change: 2026-01-11 22:12:57.302721664 +0000
 Birth: 2026-01-11 22:12:57.295721522 +0000
  File: artifacts/shadow/health.json
  Size: 368       	Blocks: 8          IO Block: 4096   regular file
Device: 252,0	Inode: 7793198     Links: 1
Access: (0600/-rw-------)  Uid: ( 1000/   slimy)   Gid: ( 1000/   slimy)

### Tripwire (artifacts)
OK_NO_SECRETS_MATCHED

### Pytest
.....................................................                    [100%]
53 passed in 0.52s

### Offline CI gate
=== Shadow Artifacts Contract CI Verification ===
Project root: /opt/pm_updown_bot_bundle

Using temp directory: /tmp/tmp.tfJ6VaNuQN

=== Step 1: Generate mock artifacts ===
Generating mock artifacts in: /tmp/tmp.tfJ6VaNuQN/artifacts/shadow
SUCCESS: Mock artifacts generated
PASS: Mock artifacts generated

=== Step 2: Verify files exist ===
PASS: All required files exist

=== Step 3: Validate JSON schemas ===
PASS: JSON schemas valid

=== Step 4: Check file sizes ===
PASS: File sizes within limits (summary: 492B, health: 483B)

=== Step 5: TRIPWIRE - Check for secrets ===
