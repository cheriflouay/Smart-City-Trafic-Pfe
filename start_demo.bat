@echo off
color 0B
title Capgemini Smart City ADAS - Master Control
echo =======================================================
echo    CAPGEMINI SMART CITY ADAS - DISTRIBUTED PLATFORM
echo =======================================================
echo.
echo [1/4] Checking Virtual Environment...
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment 'venv' not found!
    pause
    exit
)

echo [2/4] Starting FastAPI Cloud Backend (Tier 2)...
start "Capgemini Cloud Backend" cmd /c "call venv\Scripts\activate.bat && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak > NUL

echo [3/4] Starting YOLOv8 Edge Node A (Tier 1)...
start "Capgemini Edge Node A" cmd /c "call venv\Scripts\activate.bat && python -m src.analysis.vehicle_counting_smart_light --node NODE_A"
timeout /t 2 /nobreak > NUL

echo [4/4] Starting React Dashboard (Tier 3)...
start "Capgemini React Frontend" cmd /c "cd frontend && npm run dev"
timeout /t 4 /nobreak > NUL

echo.
echo =======================================================
echo ✅ SYSTEM ONLINE. ALL NODES DEPLOYED.
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
taskkill /FI "WindowTitle eq Capgemini Edge Node A*" /T /F > NUL 2>&1
taskkill /FI "WindowTitle eq Capgemini React Frontend*" /T /F > NUL 2>&1
echo ✅ System safely terminated. Goodbye!
timeout /t 2 > NUL