#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: lowprio_pnpm.sh <pnpm args...>"
  echo "example: lowprio_pnpm.sh install"
  exit 2
fi

echo "[lowprio] running pnpm with nice+15 and idle I/O class"
exec nice -n 15 ionice -c3 pnpm "$@"
