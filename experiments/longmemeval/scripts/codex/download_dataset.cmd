@echo off
setlocal
python "%~dp0download_dataset.py" %*
exit /b %ERRORLEVEL%
