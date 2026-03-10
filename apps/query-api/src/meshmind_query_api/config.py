"""Query API configuration."""

from __future__ import annotations

import os


def env(key: str, default: str) -> str:
    return os.environ.get(key, default)


DATABASE_URL = env("DATABASE_URL", "postgres://meshmind:meshmind@localhost:5432/meshmind")
QDRANT_URL = env("QDRANT_URL", "http://localhost:6333")
OLLAMA_URL = env("OLLAMA_URL", "http://localhost:11434")
MESHMIND_EMBED_MODEL = env("MESHMIND_EMBED_MODEL", "all-MiniLM-L6-v2")
MESHMIND_ASK_MODEL = env("MESHMIND_ASK_MODEL", "llama3.2")
