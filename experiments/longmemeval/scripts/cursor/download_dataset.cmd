@echo off
setlocal
call "%~dp0..\codex\download_dataset.cmd" %*
exit /b %ERRORLEVEL%
