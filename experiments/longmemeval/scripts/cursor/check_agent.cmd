@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  ". '%~dp0config.ps1'; if (Test-CursorAgentInstalled) { Write-Host 'cursor agent CLI is available.'; exit 0 } else { Write-Host (Get-CursorAgentInstallHint); exit 1 }"
exit /b %ERRORLEVEL%
