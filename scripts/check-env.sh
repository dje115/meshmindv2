#!/usr/bin/env bash
# MeshMind v2 - Environment check (Linux/macOS)
# Run: ./scripts/check-env.sh

set -e
errors=0

echo "MeshMind v2 - Environment Check (Linux/macOS)"
echo ""

check() {
    if command -v "$1" &>/dev/null; then
        echo "[OK] $1 : $($1 --version 2>/dev/null || true)"
        return 0
    else
        echo "[FAIL] $1 not found"
        ((errors++)) || true
        return 1
    fi
}

check rustup
check cargo
check node
check npm
check docker

if command -v ollama &>/dev/null; then
    echo "[OK] ollama : $(ollama --version 2>/dev/null || true)"
    ollama list 2>/dev/null | grep -q llama && echo "  models: llama present" || echo "[WARN] No llama model"
else
    echo "[WARN] Ollama not installed"
fi

if command -v python3 &>/dev/null || command -v python &>/dev/null; then
    py=$(command -v python3 2>/dev/null || command -v python)
    echo "[OK] python : $($py --version 2>/dev/null || true)"
else
    echo "[WARN] Python not installed"
fi

echo ""
[ "$errors" -eq 0 ] || exit 1
echo "Environment check complete."
