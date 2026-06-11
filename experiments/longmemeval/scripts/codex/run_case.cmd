@echo off
setlocal
python "%~dp0run_case.py" %*
exit /b %ERRORLEVEL%
