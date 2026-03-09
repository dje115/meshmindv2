#!/usr/bin/env bash
# MeshMind v2 - Pull Ollama models for a profile
# Run: ./scripts/ollama-pull-models.sh cpu-friendly
# Profiles: cpu-friendly | better-quality | minimal

set -e
PROFILE="${1:-cpu-friendly}"

case "$PROFILE" in
    cpu-friendly)   MODELS="llama3.2:3b nomic-embed-text" ;;
    better-quality) MODELS="llama3.2 mistral:7b nomic-embed-text" ;;
    minimal)        MODELS="llama3.2:1b nomic-embed-text" ;;
    *)
        echo "Unknown profile: $PROFILE"
        echo "Profiles: cpu-friendly, better-quality, minimal"
        exit 1
        ;;
esac

if ! command -v ollama &>/dev/null; then
    echo "ollama not found. Install from https://ollama.ai"
    exit 1
fi

echo "MeshMind v2 - Pull models for profile: $PROFILE"
echo "Models: $MODELS"
echo ""

for m in $MODELS; do
    echo "Pulling $m..."
    ollama pull "$m"
    echo "[OK] $m"
done

echo ""
echo "Done. Run ./scripts/ollama-check.sh to verify."
