#!/usr/bin/env bash
set -euo pipefail

echo "[mode] GAME MODE: allow Minecraft more headroom (still capped); keep dashboard alive"
sudo systemctl set-property hybrid-dashboard.service CPUWeight=100 >/dev/null 2>&1 || true
sudo systemctl set-property mc-paper.service CPUQuota=180% Nice=5 >/dev/null 2>&1 || true
echo "[mode] GAME MODE active: mc-paper relaxed to 180%/nice-5, dashboard normal"
