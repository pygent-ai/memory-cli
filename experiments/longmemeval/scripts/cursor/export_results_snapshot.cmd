@echo off
setlocal
cd /d "%~dp0..\..\..\.."
python -m experiments.longmemeval.scripts.cursor.export_results_snapshot %*
exit /b %ERRORLEVEL%
