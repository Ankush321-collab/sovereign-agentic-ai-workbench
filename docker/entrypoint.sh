#!/bin/sh
set -e

# Ensure data directories exist (in case host mount overrides them)
mkdir -p /app/data/uploads /app/data/outputs /app/data/knowledge

echo "============================================================"
echo " Starting Sovereign AI Workbench Backend (Air-Gapped Mode)"
echo " OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://localhost:11434}"
echo " Port: ${PORT:-8000}"
echo "============================================================"

exec uvicorn backend.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
