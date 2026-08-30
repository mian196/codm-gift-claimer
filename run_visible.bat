@echo off
title CODM Daily Gift Claimer - Interactive Browser Mode
cd /d "%~dp0"

echo =======================================================
echo   CODM Daily Gift Claimer - Visible Browser Mode
echo =======================================================
echo.

if not exist .venv (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Clear state file temporarily so you can watch it run right now
if exist config\state.json (
    echo [INFO] Resetting today's state cache for live test run...
    del /f /q config\state.json
)

echo [INFO] Launching visible browser...
echo.
.venv\Scripts\python.exe claimer.py --visible --hold-open 10

echo.
echo =======================================================
echo   Process finished.
echo =======================================================
pause
