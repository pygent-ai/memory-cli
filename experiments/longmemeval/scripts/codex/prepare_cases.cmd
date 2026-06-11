@echo off
setlocal
python "%~dp0prepare_cases.py" %*
exit /b %ERRORLEVEL%
