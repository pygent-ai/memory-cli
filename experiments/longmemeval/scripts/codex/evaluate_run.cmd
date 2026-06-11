@echo off
setlocal
python "%~dp0evaluate_run.py" %*
exit /b %ERRORLEVEL%
