#!/usr/bin/env bash
# MeshMind v2 - Run core (Linux/macOS)
# Run: ./scripts/run.sh

set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
cargo run -p meshmind-control-api
