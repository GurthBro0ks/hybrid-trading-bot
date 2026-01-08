#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."  # repo root
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}"
source "$HOME/.cargo/env" 2>/dev/null || true
mkdir -p data
nice -n 10 cargo run --manifest-path engine/Cargo.toml
