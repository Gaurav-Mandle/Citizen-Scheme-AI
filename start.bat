@echo off
TITLE Citizen Scheme AI Launcher
cls
echo ======================================================================
echo          CITIZEN SCHEME AI - SAFE SWITCH LAUNCHER
echo ======================================================================
echo.
echo Please choose the interface mode:
echo.
echo   [1] Modern Web Portal (FastAPI + Tailwind SPA on http://127.0.0.1:8000)
echo   [2] Classic Streamlit Interface (Untouched app.py on http://localhost:8501)
echo   [3] Run System Test Suite (pytest tests -v)
echo   [4] Exit
echo.
set /p choice="Enter choice [1-4] (default is 1): "

if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Launching Modern Web Portal...
    python run.py --ui modern
    pause
    exit /b
)

if "%choice%"=="2" (
    echo.
    echo Launching Classic Streamlit Interface...
    python run.py --ui classic
    pause
    exit /b
)

if "%choice%"=="3" (
    echo.
    echo Running Pytest Suite...
    python run.py --test
    pause
    exit /b
)

if "%choice%"=="4" (
    echo Exiting.
    exit /b
)

echo Invalid choice. Starting default Modern Web Portal...
python run.py --ui modern
pause
