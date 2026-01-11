#!/usr/bin/env bash
set -euo pipefail

SERVICE="hybrid-shadow-runner.service"
TIMER="hybrid-shadow-runner.timer"
ENTRYPOINT="/opt/pm_updown_bot_bundle/scripts/run_shadow_prod_entrypoint.py"
ART_DIR="/opt/hybrid-trading-bot/artifacts/shadow"

systemctl cat "$SERVICE" | rg -n "$ENTRYPOINT" >/dev/null
printf 'OK_SERVICE_ENTRYPOINT\n'

systemctl is-active --quiet "$TIMER"
printf 'OK_TIMER_ACTIVE\n'

if [[ ! -d "$ART_DIR" ]]; then
  echo "ERROR: missing artifacts dir: $ART_DIR" >&2
  exit 1
fi

for f in latest_summary.json latest_journal.csv health.json; do
  if [[ ! -f "$ART_DIR/$f" ]]; then
    echo "ERROR: missing artifact $ART_DIR/$f" >&2
    exit 1
  fi
done
printf 'OK_ARTIFACTS_PRESENT\n'

jq -r '.schema_version,.mode,.last_refresh,.last_error' "$ART_DIR/latest_summary.json" >/dev/null
jq -r '.schema_version,.mode,.last_run_at,.last_error' "$ART_DIR/health.json" >/dev/null
printf 'OK_JQ_FIELDS\n'

if rg -n -i "api[_-]?key|secret|token|authorization|bearer|private[_-]?key|password" "$ART_DIR" >/dev/null; then
  echo "ERROR: secrets tripwire matched" >&2
  exit 1
fi
printf 'OK_TRIPWIRE\n'

if sudo -n true 2>/dev/null; then
  before=$(stat -c %Y "$ART_DIR/latest_summary.json" "$ART_DIR/health.json" | tr '\n' ' ')
  sudo -n systemctl start "$SERVICE"
  sleep 2
  after=$(stat -c %Y "$ART_DIR/latest_summary.json" "$ART_DIR/health.json" | tr '\n' ' ')
  if [[ "$before" == "$after" ]]; then
    echo "ERROR: mtime did not change after service run" >&2
    exit 1
  fi
  printf 'OK_MTIME_UPDATED\n'
else
  printf 'OK_MTIME_SKIP_NO_SUDO\n'
fi
