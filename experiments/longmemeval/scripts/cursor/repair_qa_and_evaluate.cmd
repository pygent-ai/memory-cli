@echo off
setlocal
python "%~dp0repair_qa_and_evaluate.py" %*
exit /b %ERRORLEVEL%
