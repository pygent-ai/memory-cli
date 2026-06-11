@echo off
setlocal EnableExtensions
call "%~dp0qa_stage.cmd" %*
exit /b %ERRORLEVEL%
