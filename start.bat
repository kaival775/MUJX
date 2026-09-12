@echo off
title Let's Go 3.0 - Full Stack Launcher
color 0A
setlocal enabledelayedexpansion

echo.
echo  =============================================
echo  ^|                                           ^|
echo  ^|     LET'S GO 3.0 - FULL STACK LAUNCHER    ^|
echo  ^|     Annadata Saathi Agriculture Platform   ^|
echo  ^|                                           ^|
echo  =============================================
echo.

:: ─────────────────────────────────────────────
:: STEP 0: Detect Python 3.11
:: ─────────────────────────────────────────────
set "PYTHON_EXE="

:: Check common Python 3.11 paths
if exist "C:\Program Files\Python311\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Python311\python.exe"
)
if exist "C:\Python311\python.exe" (
    set "PYTHON_EXE=C:\Python311\python.exe"
)

:: Fallback: try system python
if "%PYTHON_EXE%"=="" (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
        echo  [WARN] Python 3.11 not found at default path.
        echo         Using system python. Some packages may not work.
    ) else (
        echo  [ERROR] Python not found! Please install Python 3.11.
        echo         Download: https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

echo  [OK] Python: %PYTHON_EXE%
echo.

:: ─────────────────────────────────────────────
:: STEP 1: Check .env files
:: ─────────────────────────────────────────────
echo  [1/5] Checking environment files...

if not exist "%~dp0backend\.env" (
    if exist "%~dp0backend\.env.example" (
        echo  [WARN] backend\.env not found! Copying from .env.example...
        copy "%~dp0backend\.env.example" "%~dp0backend\.env" >nul
        echo  [INFO] Please update backend\.env with your actual API keys.
    ) else (
        echo  [ERROR] backend\.env not found and no .env.example available!
        echo         Please create backend\.env with required environment variables.
        pause
        exit /b 1
    )
)

if not exist "%~dp0frontend\.env" (
    if exist "%~dp0frontend\.env.example" (
        echo  [WARN] frontend\.env not found! Copying from .env.example...
        copy "%~dp0frontend\.env.example" "%~dp0frontend\.env" >nul
        echo  [INFO] Please update frontend\.env with your actual config.
    )
)

echo  [OK] Environment files ready.
echo.

:: ─────────────────────────────────────────────
:: STEP 2: Install Backend Dependencies
:: ─────────────────────────────────────────────
echo  [2/5] Installing backend dependencies...
echo        This may take a minute on first run...

"%PYTHON_EXE%" -m pip install -r "%~dp0backend\requirements.txt" --quiet --disable-pip-version-check 2>nul
if !errorlevel! neq 0 (
    echo  [WARN] Some backend packages may have failed to install.
    echo         The server will still attempt to start.
) else (
    echo  [OK] Backend dependencies installed.
)

:: Install google-genai separately (needed but not in requirements.txt)
"%PYTHON_EXE%" -m pip install google-genai --quiet --disable-pip-version-check 2>nul

echo.

:: ─────────────────────────────────────────────
:: STEP 3: Install Frontend Dependencies
:: ─────────────────────────────────────────────
echo  [3/5] Checking frontend dependencies...

where npm >nul 2>&1
if !errorlevel! neq 0 (
    echo  [ERROR] npm not found! Please install Node.js.
    echo         Download: https://nodejs.org/
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo        Installing npm packages (first run)...
    cd /d "%~dp0frontend"
    npm install --silent 2>nul
    cd /d "%~dp0"
    echo  [OK] Frontend packages installed.
) else (
    echo  [OK] Frontend packages already installed.
)
echo.

:: ─────────────────────────────────────────────
:: STEP 4: Start Backend Server
:: ─────────────────────────────────────────────
echo  [4/5] Starting Backend Server (FastAPI)...
echo        Port: 8000
start "LetsGo 3.0 - Backend (Port 8000)" cmd /k "title LetsGo 3.0 - Backend ^& color 0B ^& cd /d %~dp0backend ^& echo. ^& echo  ========================================= ^& echo  ^|  BACKEND SERVER - FastAPI / Uvicorn   ^| ^& echo  ^|  http://localhost:8000                ^| ^& echo  ========================================= ^& echo. ^& "%PYTHON_EXE%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to initialize
echo        Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak >nul
echo  [OK] Backend server launched.
echo.

:: ─────────────────────────────────────────────
:: STEP 5: Start Frontend Dev Server
:: ─────────────────────────────────────────────
echo  [5/5] Starting Frontend Dev Server (Vite)...
echo        Port: 5173
start "LetsGo 3.0 - Frontend (Port 5173)" cmd /k "title LetsGo 3.0 - Frontend ^& color 0D ^& cd /d %~dp0frontend ^& echo. ^& echo  ========================================= ^& echo  ^|  FRONTEND SERVER - Vite               ^| ^& echo  ^|  http://localhost:5173                ^| ^& echo  ========================================= ^& echo. ^& npm run dev"

:: Wait for frontend to initialize
timeout /t 3 /nobreak >nul
echo  [OK] Frontend dev server launched.
echo.

:: ─────────────────────────────────────────────
:: DONE
:: ─────────────────────────────────────────────
echo.
echo  =============================================
echo  ^|                                           ^|
echo  ^|       ALL SERVERS STARTED!                ^|
echo  ^|                                           ^|
echo  ^|   Backend:   http://localhost:8000         ^|
echo  ^|   API Docs:  http://localhost:8000/docs    ^|
echo  ^|   Frontend:  http://localhost:5173         ^|
echo  ^|   Dashboard: http://localhost:5173/dashboard^|
echo  ^|                                           ^|
echo  ^|   To stop: close the server windows       ^|
echo  ^|                                           ^|
echo  =============================================
echo.

:: Open browser after a short delay
timeout /t 3 /nobreak >nul
echo  Opening app in browser...
start http://localhost:5173

echo.
echo  Press any key to close this launcher window.
echo  (Servers will keep running in their own windows)
pause >nul
