@echo off
title VAJRA - Sovereign Air-Gapped AI Workbench
echo ======================================================================
echo    VAJRA: SOVEREIGN AIR-GAPPED AI WORKBENCH (SIH 2026 EDITION)
echo    100%% On-Premises Execution // Defense and PSU Sovereign Node
echo ======================================================================
echo.
cd /d "%~dp0\.."

echo [*] Verifying Python Environment...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found in PATH!
    pause
    exit /b 1
)

echo [*] Booting Sovereign Desktop Workstation...
python launcher\run_desktop.py
pause
