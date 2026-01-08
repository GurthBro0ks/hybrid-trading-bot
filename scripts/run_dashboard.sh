#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."  # repo root
python3 -m venv dashboard/.venv
source dashboard/.venv/bin/activate
python -m pip install --upgrade pip
pip install streamlit pandas toml
streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501
