@echo off
setlocal
call "%~dp0..\codex\summarize_results.cmd" %*
exit /b %ERRORLEVEL%
