@echo off
setlocal EnableExtensions

set "CASE_DIR=%~1"
if "%CASE_DIR%"=="" (
  echo Usage: qa_stage.cmd CASE_DIR [AGENT_COMMAND]
  exit /b 2
)

set "AGENT_COMMAND=%~2"
if "%AGENT_COMMAND%"=="" set "AGENT_COMMAND=codex exec --skip-git-repo-check"

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\..\.."
set "PROMPT_TEMPLATE=%ROOT_DIR%\experiments\longmemeval\prompts\answer_from_memory.md"
set "WORK_DIR=%CASE_DIR%\work"
set "INPUT_JSON=%WORK_DIR%\input\question_input.json"
set "OUTPUT_DIR=%CASE_DIR%\outputs"
set "LOG_DIR=%CASE_DIR%\logs"
set "PROMPT_FILE=%LOG_DIR%\qa_prompt.txt"
set "STDOUT_FILE=%LOG_DIR%\qa_stdout.txt"
set "STDERR_FILE=%LOG_DIR%\qa_stderr.txt"
set "RAW_JSON_FILE=%LOG_DIR%\qa_raw_agent_output.json"
set "ANSWER_JSON=%OUTPUT_DIR%\answer.json"
set "RENDER_PS1=%SCRIPT_DIR%qa_stage_render_prompt.ps1"
set "WRITE_PS1=%SCRIPT_DIR%qa_stage_write_answer.ps1"

if not exist "%INPUT_JSON%" (
  echo Missing question input: %INPUT_JSON%
  exit /b 2
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RENDER_PS1%"
if errorlevel 1 exit /b %ERRORLEVEL%

pushd "%WORK_DIR%" || exit /b 2
set "PATH=%WORK_DIR%\.venv\Scripts;%PATH%"
call %AGENT_COMMAND% < "%PROMPT_FILE%" > "%STDOUT_FILE%" 2> "%STDERR_FILE%"
set "AGENT_EXIT=%ERRORLEVEL%"
popd

if not "%AGENT_EXIT%"=="0" (
  echo QA agent failed with exit code %AGENT_EXIT%
  exit /b %AGENT_EXIT%
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%WRITE_PS1%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo Wrote %ANSWER_JSON%
exit /b 0
