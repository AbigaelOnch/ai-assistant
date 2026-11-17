@echo off
title AI Assistant
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause & exit /b 1
)
findstr /x /l /c:"ANTHROPIC_API_KEY=sk-ant-..." .env >nul 2>nul && (
  echo Your Claude API key isn't set yet. Opening .env - paste it after ANTHROPIC_API_KEY= and save.
  notepad .env
)
rem  run_windows.bat            -> chat with the assistant
rem  run_windows.bat run        -> one full check (brief, tasks, drafts)
rem  run_windows.bat approvals  -> approve queued sends
rem  run_windows.bat connect    -> test sign-in to each source
if "%~1"=="" (
  ".venv\Scripts\python.exe" -m assistant chat
) else (
  ".venv\Scripts\python.exe" -m assistant %*
)
pause
