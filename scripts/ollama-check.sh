#!/usr/bin/env bash
# MeshMind v2 - Verify Ollama is installed and running
# Run: ./scripts/ollama-check.sh
# Optionally: OLLAMA_URL=http://localhost:11434 ./scripts/ollama-check.sh

set -e
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

echo "MeshMind v2 - Ollama Check"
echo ""

# 1. ollama CLI
if ! command -v ollama &>/dev/null; then
    echo "[FAIL] ollama CLI not found. Install from https://ollama.ai"
    exit 1
fi
echo "[OK] ollama : $(ollama --version 2>/dev/null || true)"

# 2. Ollama API reachability
if curl -sf --max-time 5 "$OLLAMA_URL/" >/dev/null 2>&1; then
    echo "[OK] Ollama API reachable at $OLLAMA_URL"
else
    echo "[FAIL] Ollama API unreachable at $OLLAMA_URL"
    echo "  Start Ollama: ollama serve (or launch Ollama app)"
    exit 1
fi

# 3. List models
TAGS=$(curl -sf --max-time 5 "$OLLAMA_URL/api/tags" 2>/dev/null || echo '{"models":[]}')
if echo "$TAGS" | grep -q '"models"'; then
    if command -v jq &>/dev/null; then
        COUNT=$(echo "$TAGS" | jq '.models | length' 2>/dev/null || echo 0)
        if [ "$COUNT" -gt 0 ]; then
            echo "[OK] Models available: $COUNT"
            echo "$TAGS" | jq -r '.models[].name' 2>/dev/null | while read -r name; do
                echo "  - $name"
            done
        else
            echo "[WARN] No models pulled. Run: ./scripts/ollama-pull-models.sh cpu-friendly"
        fi
    else
        echo "[OK] Ollama models endpoint OK (install jq for pretty listing)"
    fi
else
    echo "[WARN] Could not parse model list. Run: ./scripts/ollama-pull-models.sh cpu-friendly"
fi

echo ""
echo "Ollama check complete."
