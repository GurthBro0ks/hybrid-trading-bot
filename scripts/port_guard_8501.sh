#!/usr/bin/env bash
set -euo pipefail
PORT=8501
USER_EXPECTED="slimy"

# Find listener PID (if any)
PID="$(ss -ltnp 2>/dev/null | awk -v p=":${PORT}" '$4 ~ p {print $NF}' | head -n1 | sed -E 's/.*pid=([0-9]+).*/\1/' || true)"
if [ -z "${PID}" ]; then
  echo "[portguard] port ${PORT} is free"
  exit 0
fi

OWNER="$(ps -o user= -p "$PID" 2>/dev/null | awk '{print $1}' || true)"
CMD="$(ps -o comm= -p "$PID" 2>/dev/null || true)"
ARGS="$(ps -o args= -p "$PID" 2>/dev/null || true)"

echo "[portguard] port ${PORT} in use by pid=${PID} owner=${OWNER} cmd=${CMD}"
echo "[portguard] args: ${ARGS}"

if [ "${OWNER}" != "${USER_EXPECTED}" ]; then
  echo "[portguard] REFUSING: owner is not ${USER_EXPECTED}"
  exit 1
fi

# Only kill python/streamlit-ish
if echo "${ARGS}" | grep -Eqi '(streamlit|python)'; then
  echo "[portguard] killing pid ${PID}"
  kill "${PID}" 2>/dev/null || true
  sleep 1
  exit 0
fi

echo "[portguard] REFUSING: not python/streamlit"
exit 1
