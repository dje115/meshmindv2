#!/usr/bin/env bash
# MeshMind v2 - Run tests (Linux/macOS)
# Run: ./scripts/test.sh

set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
cargo test -p meshmind-control-api
