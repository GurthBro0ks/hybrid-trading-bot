# Shadow Artifacts Contract v1.0

## Overview

This contract defines the stable, read-only artifact paths for shadow trading mode. These artifacts are designed to be consumed by the UI dashboard and monitoring systems.

## Contract Version

- **Schema Version**: `shadow_summary_v1`, `shadow_health_v1`
- **Contract Status**: STABLE (additive-only changes permitted)

---

## Stable Paths

All artifacts are written to a single directory. Default: `artifacts/shadow/`

| File | Purpose | Max Size |
|------|---------|----------|
| `latest_summary.json` | Current decision state | 10KB |
| `latest_journal.csv` | Bounded decision history | N rows |
| `health.json` | System health metrics | 10KB |

---

## Environment Overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `SHADOW_ARTIFACTS_DIR` | `artifacts/shadow` | Override output directory |
| `SHADOW_JOURNAL_MAX_ROWS` | `500` | Max rows in journal CSV |

---

## Schema: latest_summary.json

```json
{
  "schema_version": "shadow_summary_v1",
  "mode": "SHADOW",
  "last_refresh": "2026-01-11T18:30:00.000000+00:00",
  "strategy": "stale_edge_enhanced",
  "run_id": "20260111_183000",
  "market": "INXD-26JAN11-T4398.5",
  "decision": "NO_TRADE",
  "reason": "NO_EDGE",
  "subreason": "",
  "edge_bps": null,
  "pm_yes_mid": 45.5,
  "fair_yes_prob": 0.42,
  "notes": "",
  "last_error": ""
}
```

### Required Fields (v1)

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Always `"shadow_summary_v1"` |
| `mode` | string | Always `"SHADOW"` |
| `last_refresh` | string | ISO8601 UTC timestamp |
| `strategy` | string | Strategy name |
| `run_id` | string | Run identifier |
| `market` | string | Market ID (safe, no secrets) |
| `decision` | string | Action taken |
| `reason` | string | Primary reason |
| `subreason` | string | Secondary reason (may be empty) |
| `edge_bps` | number\|null | Edge in basis points |
| `pm_yes_mid` | number\|null | PM yes mid price |
| `fair_yes_prob` | number\|null | Fair probability |
| `notes` | string | Sanitized notes (max 200 chars) |
| `last_error` | string | Sanitized error (max 200 chars) |

---

## Schema: health.json

```json
{
  "schema_version": "shadow_health_v1",
  "mode": "SHADOW",
  "last_run_at": "2026-01-11T18:30:00.000000+00:00",
  "last_success_at": "2026-01-11T18:30:00.000000+00:00",
  "last_error_at": null,
  "last_error": "",
  "last_latency_ms": 150,
  "artifacts_written": true,
  "journal_rows": 42,
  "build": {
    "git_sha": "abc1234",
    "version": null
  },
  "uptime_sec": 3600,
  "schema_mismatch": false
}
```

### Required Fields (v1)

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Always `"shadow_health_v1"` |
| `mode` | string | Always `"SHADOW"` |
| `last_run_at` | string | ISO8601 UTC timestamp |
| `last_success_at` | string\|null | Last successful artifact write |
| `last_error_at` | string\|null | Last error timestamp |
| `last_error` | string | Sanitized error (max 200 chars) |
| `last_latency_ms` | int\|null | Loop latency in ms |
| `artifacts_written` | bool | Whether artifacts were written |
| `journal_rows` | int | Number of rows in journal |
| `build` | object | `{git_sha: string|null, version: string|null}` |
| `uptime_sec` | int\|null | Uptime in seconds |
| `schema_mismatch` | bool | True if CSV header differs from expected |

---

## Schema: latest_journal.csv

The journal CSV uses a **static column list** defined in `recorder/journal_schema.py`. All columns are always emitted; missing values use empty string.

### Column List (JOURNAL_COLUMNS)

See `recorder/journal_schema.py` for the canonical column list.

### Bounded Rows

- Default: 500 rows maximum
- Override: `SHADOW_JOURNAL_MAX_ROWS` environment variable
- When bound exceeded: oldest rows are dropped, newest retained

---

## Sanitization Rules

All text fields that might contain sensitive data MUST be sanitized before writing to artifacts.

### Forbidden Substrings (case-insensitive)

The following patterns are removed from any artifact text:
- `api_key`, `api-key`, `apikey`
- `secret`
- `token`
- `authorization`
- `bearer`
- `private_key`, `private-key`, `privatekey`
- `password`

### Additional Rules

1. Strip newlines (replace with space)
2. Cap text at 200 characters
3. Long hex/base64 blobs may be redacted
4. When in doubt, return a safe default like `"REQUEST_FAILED"`

---

## Atomic Write Protocol

All artifact writes MUST be atomic to prevent partial/corrupt files:

1. Write to temporary file in same directory (e.g., `.latest_summary.json.tmp`)
2. Call `fsync()` on file descriptor
3. Use `os.replace()` to atomically move temp to final path

This ensures readers always see a complete file.

---

## Additive-Only Policy

For v1 contract stability:

1. **New fields**: May be added to JSON schemas (additive)
2. **New columns**: May be appended to end of JOURNAL_COLUMNS
3. **Existing fields**: MUST NOT be renamed, removed, or change type
4. **Column order**: MUST be preserved for CSV compatibility

---

## CI Verification

The contract is enforced by an offline CI gate that:

1. Generates mock artifacts with secret-laden test data
2. Verifies sanitizer removes all secrets
3. Validates JSON schema requirements
4. Checks file size limits
5. Runs tripwire to detect any leaked secrets

### Tripwire Command

```bash
rg -n -i "api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password" artifacts/shadow
```

Expected result: **No matches** (exit code 1 from rg)
