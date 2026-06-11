@echo off
setlocal
python "%~dp0run_all_parallel.py" %*
exit /b %ERRORLEVEL%
