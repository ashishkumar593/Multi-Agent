@echo off
title Autonomous AI Company - Operations Cockpit
color 0A

echo ==================================================================
echo   🏢 AUTONOMOUS AI COMPANY: OPERATIONS COCKPIT
echo   Multi-Agent Operating System with Executive Glassmorphism UI
echo ==================================================================
echo.

:: Check for Python installation
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py -3.13
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PY_CMD=python
    ) else (
        echo [ERROR] Python is not found in system PATH.
        pause
        exit /b 1
    )
)

echo [INFO] Using Python: %PY_CMD%
echo [INFO] Launching Streamlit Operations Cockpit on http://localhost:8501 ...
echo [INFO] Press Ctrl+C in this terminal to shut down the server.
echo.

%PY_CMD% -m streamlit run frontend/app.py --server.port=8501 --server.headless=false --browser.gatherUsageStats=false

pause
