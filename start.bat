@echo off
:: Silent runner for CODM Daily Gift Claimer
cd /d "%~dp0"
if not exist .venv (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Run script headlessly using the virtual environment interpreter
.venv\Scripts\python.exe claimer.py --hold-open 0
exit /b 0
