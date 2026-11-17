@echo off
setlocal
title AI Assistant - setup
cd /d "%~dp0"

echo === AI Assistant setup ===
where python >nul 2>nul || (
  echo Python was not found. Install "Python 3.13" from the Microsoft Store, then run this again.
  pause & exit /b 1
)
python --version

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo Creating virtual environment...
  python -m venv .venv || goto :fail
)

echo.
echo Installing packages (takes a minute or two)...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet || goto :fail

if not exist secrets mkdir secrets
if not exist .env copy .env.example .env >nul

echo.
echo ==========================================================
echo  Setup finished.
echo.
echo  Notepad will now open your settings file (.env):
echo    1. Paste your Claude API key after ANTHROPIC_API_KEY=
echo       (get one at https://console.anthropic.com)
echo    2. Save (Ctrl+S) and close Notepad.
echo.
echo  Gmail and Outlook need one-time sign-in setup - see the
echo  README sections "Connect Gmail" and "Connect Outlook".
echo  Until then the assistant runs without them.
echo.
echo  Then double-click run_windows.bat to start the assistant.
echo ==========================================================
notepad .env
pause
exit /b 0

:fail
echo.
echo Setup failed - see the error above.
pause
exit /b 1
