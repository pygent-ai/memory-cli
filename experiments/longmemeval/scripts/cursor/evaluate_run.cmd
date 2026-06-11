@echo off
setlocal
call "%~dp0..\codex\evaluate_run.cmd" %*
exit /b %ERRORLEVEL%
