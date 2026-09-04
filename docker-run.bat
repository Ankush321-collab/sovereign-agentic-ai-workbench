@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo       SOVEREIGN AI WORKBENCH — DOCKER DEPLOYMENT LAUNCHER
echo ==============================================================================
echo.

:: Check if Docker is installed and running
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker command not found in PATH!
    echo Please make sure Docker Desktop is installed and added to your environment PATH.
    echo Download Docker Desktop: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

docker info >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running!
    echo Please launch Docker Desktop and wait until the engine has started.
    pause
    exit /b 1
)

echo [OK] Docker daemon detected.
echo.
echo Select deployment option:
echo   1. Start Full Stack (Backend + Frontend + Ollama)
echo   2. Start with Host Ollama (Uses your existing host models on port 11434)
echo   3. Initialize/Pull default LLM models into Docker Ollama
echo   4. View Stack Logs
echo   5. Stop Stack
echo.
set /p choice="Enter option (1-5, default: 1): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Building and starting Sovereign AI Workbench...
    docker compose --env-file .env.docker up --build -d
    echo.
    echo Services launched:
    echo   - Frontend: http://localhost:5173 or http://localhost:80
    echo   - Backend API Docs: http://localhost:8000/docs
    echo   - Ollama API: http://localhost:11434
    echo.
    docker compose ps
    goto follow_logs
)

if "%choice%"=="2" (
    echo.
    echo Starting stack connected to host machine Ollama...
    set OLLAMA_BASE_URL=http://host.docker.internal:11434
    docker compose --env-file .env.docker up --build -d backend frontend
    echo.
    echo Services launched (using host Ollama):
    echo   - Frontend: http://localhost:5173
    echo   - Backend API Docs: http://localhost:8000/docs
    echo.
    docker compose ps
    goto follow_logs
)

if "%choice%"=="3" (
    echo.
    echo Pulling default LLM models into containerized Ollama...
    docker compose --profile init-models up ollama-init
    goto end
)

if "%choice%"=="4" (
    goto follow_logs
)

if "%choice%"=="5" (
    echo.
    echo Stopping all Sovereign AI Workbench containers...
    docker compose down
    echo Done.
    goto end
)

:follow_logs
echo.
echo Streaming logs (Press Ctrl+C to detach):
docker compose logs -f
goto end

:end
pause
