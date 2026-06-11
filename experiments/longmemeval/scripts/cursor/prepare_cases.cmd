@echo off
setlocal
call "%~dp0..\codex\prepare_cases.cmd" %*
exit /b %ERRORLEVEL%
