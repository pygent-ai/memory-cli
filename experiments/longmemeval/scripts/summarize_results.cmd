@echo off
setlocal
python "%~dp0summarize_results.py" %*
exit /b %ERRORLEVEL%
