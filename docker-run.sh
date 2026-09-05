#!/usr/bin/env bash
set -e

echo "=============================================================================="
echo "       SOVEREIGN AI WORKBENCH — DOCKER DEPLOYMENT LAUNCHER"
echo "=============================================================================="
echo ""

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker command not found in PATH."
    echo "Please install Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker daemon is not running."
    echo "Please start the Docker service (e.g. 'sudo systemctl start docker' or start Docker Desktop)."
    exit 1
fi

echo "[OK] Docker daemon detected."
echo ""
echo "Select deployment option:"
echo "  1. Start Full Stack (Backend + Frontend + Ollama)"
echo "  2. Start with Host Ollama (Uses your existing host models on port 11434)"
echo "  3. Initialize/Pull default LLM models into Docker Ollama"
echo "  4. View Stack Logs"
echo "  5. Stop Stack"
echo ""
read -rp "Enter option (1-5, default: 1): " choice
choice="${choice:-1}"

case "$choice" in
  1)
    echo "Building and starting Sovereign AI Workbench..."
    docker compose --env-file .env.docker up --build -d
    echo ""
    echo "Services launched:"
    echo "  - Frontend: http://localhost:5173 or http://localhost:80"
    echo "  - Backend API Docs: http://localhost:8000/docs"
    echo "  - Ollama API: http://localhost:11434"
    echo ""
    docker compose ps
    docker compose logs -f
    ;;
  2)
    echo "Starting stack connected to host machine Ollama..."
    export OLLAMA_BASE_URL="http://host.docker.internal:11434"
    docker compose --env-file .env.docker up --build -d backend frontend
    echo ""
    echo "Services launched (using host Ollama):"
    echo "  - Frontend: http://localhost:5173"
    echo "  - Backend API Docs: http://localhost:8000/docs"
    echo ""
    docker compose ps
    docker compose logs -f
    ;;
  3)
    echo "Pulling default LLM models into containerized Ollama..."
    docker compose --profile init-models up ollama-init
    ;;
  4)
    docker compose logs -f
    ;;
  5)
    echo "Stopping all Sovereign AI Workbench containers..."
    docker compose down
    echo "Done."
    ;;
  *)
    echo "Invalid option."
    exit 1
    ;;
esac
