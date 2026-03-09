#!/usr/bin/env bash
# MeshMind v2 - Bootstrap (Linux/macOS)
# Run: ./scripts/bootstrap.sh

set -e
root="$(cd "$(dirname "$0")/.." && pwd)"

echo "MeshMind v2 - Bootstrap"
echo ""

# 1. Run environment check
if [ -f "$root/scripts/check-env.sh" ]; then
    echo "Running environment check..."
    "$root/scripts/check-env.sh" || exit 1
else
    echo "[WARN] scripts/check-env.sh not found"
fi

# 2. Create data directory
mkdir -p "$root/data"
echo "[OK] Data directory ready"

# 3. Fetch Cargo dependencies
echo ""
echo "Fetching Rust dependencies..."
cd "$root"
cargo fetch 2>/dev/null || true
echo "[OK] Cargo dependencies ready"

echo ""
echo "Bootstrap complete. Ready for development."
echo "  Run control-api: ./scripts/run.sh"
echo "  Run tests: ./scripts/test.sh"
