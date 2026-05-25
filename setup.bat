@echo off
:: CODM Daily Gift Claimer Local Setup Utility
cd /d "%~dp0"
echo ===================================================
echo   CODM Daily Free Gift Claimer - Local Setup
echo ===================================================
echo.

:: 1. Verify/Install Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Python not found. Installing Python using winget...
    winget install --id Python.Python.3 -h --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python automatically. Please install Python 3 manually from python.org.
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Python has been successfully installed!
    echo [IMPORTANT] Please restart this command prompt window and run setup.bat again to complete setup.
    pause
    exit /b 0
) else (
    echo [SUCCESS] Python is already installed.
    python --version
)
echo.

:: 2. Setup python virtual environment
echo [INFO] Setting up virtual environment in .venv folder...
if not exist .venv (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Virtual environment .venv already exists.
)
echo.

:: 3. Install requirements and playwright chromium
echo [INFO] Installing requirements.txt inside virtual environment...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed.
echo.

echo [INFO] Installing Playwright Chromium browser binaries...
.venv\Scripts\playwright.exe install chromium
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Playwright Chromium browser.
    pause
    exit /b 1
)
echo [SUCCESS] Playwright Chromium browser installed successfully.
echo.

:: 4. Create config directory and template profiles/settings if not present
echo [INFO] Configuring local directories and template configuration files...
if not exist config (
    mkdir config
)

:: Create config/profiles.json template if not exists
if not exist config\profiles.json (
    (
        echo [
        echo   { "name": "PlayerName", "uid": "Your21DigitPlayerUIDHere" }
        echo ]
    ) > config\profiles.json
    echo [SUCCESS] Created sample profiles config in config/profiles.json.
) else (
    echo [INFO] Profiles config already exists in config/profiles.json.
)

:: Create config/settings.json template if not exists
if not exist config\settings.json (
    (
        echo {
        echo   "DISCORD_WEBHOOK_URL": ""
        echo }
    ) > config\settings.json
    echo [SUCCESS] Created template settings in config/settings.json.
) else (
    echo [INFO] Settings config already exists in config/settings.json.
)
echo.

:: 5. Register Startup trigger (Try Task Scheduler first, fallback to Windows Startup Folder)
echo [INFO] Registering startup trigger...
schtasks /create /tn "CODM_Gift_Claimer" /tr "\"%~dp0start.bat\"" /sc onlogon /f >nul 2>&1
if %errorlevel% EQU 0 goto TASK_SUCCESS

echo [INFO] Task Scheduler registration failed (requires Administrator privileges).
echo [INFO] Falling back to Windows Startup Folder (user-level startup, no admin needed)...

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if not exist "%STARTUP_DIR%" goto STARTUP_FAILED

echo @echo off> "%STARTUP_DIR%\CODM_Gift_Claimer.bat"
echo cd /d "%~dp0">> "%STARTUP_DIR%\CODM_Gift_Claimer.bat"
echo start "" /b "start.bat">> "%STARTUP_DIR%\CODM_Gift_Claimer.bat"
echo [SUCCESS] Created startup shortcut in Windows Startup Folder!
echo [SUCCESS] The script will run automatically every time you log into Windows.
goto REGISTRATION_END

:TASK_SUCCESS
echo [SUCCESS] Windows Task Scheduler task registered successfully!
echo [SUCCESS] The script will run automatically every time you log into Windows.
goto REGISTRATION_END

:STARTUP_FAILED
echo [WARNING] Startup folder not found. Please launch the script manually using start.bat.

:REGISTRATION_END
echo.

echo ===================================================
echo   Local Setup Completed Successfully!
echo ===================================================
echo.
echo [Action Needed]:
echo 1. Check/Edit config/profiles.json with your actual CODM profile(s).
echo 2. Check/Edit config/settings.json to add a Discord Webhook if desired.
echo 3. Run start.bat to perform a manual test run.
echo.
pause
exit /b 0
