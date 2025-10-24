@echo off
setlocal

set "PS1=%~dp0windows_env.ps1"

if not exist "%PS1%" (
  echo "%PS1%" Not Found.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

endlocal
