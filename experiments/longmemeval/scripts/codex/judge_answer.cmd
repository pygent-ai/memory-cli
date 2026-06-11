@echo off
setlocal
python "%~dp0judge_answer.py" %*
exit /b %ERRORLEVEL%
