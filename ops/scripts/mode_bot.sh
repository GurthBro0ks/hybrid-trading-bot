#!/usr/bin/env bash
set -euo pipefail

echo "[mode] BOT MODE: prioritize hybrid services; cage Minecraft harder"
sudo systemctl set-property hybrid-dashboard.service CPUWeight=200 >/dev/null 2>&1 || true
sudo systemctl set-property mc-paper.service CPUQuota=120% Nice=15 >/dev/null 2>&1 || true
echo "[mode] BOT MODE active: dashboard boosted, mc-paper caged to 120%/nice-15"
