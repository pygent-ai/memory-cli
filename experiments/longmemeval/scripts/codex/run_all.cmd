@echo off
setlocal
python "%~dp0run_all.py" %*
exit /b %ERRORLEVEL%
