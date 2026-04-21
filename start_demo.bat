@echo off
color 0B
title Capgemini Smart City ADAS - Master Control
echo =======================================================
echo    CAPGEMINI SMART CITY ADAS - DISTRIBUTED PLATFORM
echo =======================================================
echo.
echo [1/3] Checking Virtual Environment...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'venv' not found!
    pause
    exit
)

echo [2/3] Starting FastAPI Cloud Backend (Tier 2)...
:: 🚨 REMOVED --reload so the server doesn't crash when videos are uploaded
start "Capgemini Cloud Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn src.api.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak > NUL

:: 🚨 REMOVED the Edge Node auto-start step! The backend handles this dynamically now.

echo [3/3] Starting React Dashboard (Tier 3)...
start "Capgemini React Frontend" cmd /c "cd frontend && npm run dev"
timeout /t 4 /nobreak > NUL

echo.
echo =======================================================
echo ✅ SYSTEM ONLINE. AWAITING DASHBOARD SIMULATION LAUNCH.
echo =======================================================
echo Opening Dashboard in your default browser...

:: Open the React app in the default web browser
start http://localhost:5173

echo.
echo Press any key to safely shut down the entire system...
pause > NUL

:: --- GRACEFUL SHUTDOWN LOGIC ---
echo.
echo 🛑 Shutting down Capgemini ADAS Platform...
taskkill /FI "WindowTitle eq Capgemini Cloud Backend*" /T /F > NUL 2>&1
taskkill /FI "WindowTitle eq Capgemini React Frontend*" /T /F > NUL 2>&1

:: Also kill any ghost python processes spawned by the dashboard
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *vehicle_counting_smart_light*" > NUL 2>&1

echo ✅ System safely terminated.
Goodbye!
timeout /t 2 > NUL