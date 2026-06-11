@echo off
setlocal
call "%~dp0..\codex\judge_answer.cmd" %*
exit /b %ERRORLEVEL%
