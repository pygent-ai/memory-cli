@echo off
setlocal EnableExtensions

set "CASE_DIR=%~1"
if "%CASE_DIR%"=="" (
  echo Usage: qa_stage.cmd CASE_DIR [AGENT_COMMAND]
  exit /b 2
)

set "AGENT_COMMAND=%~2"
if "%AGENT_COMMAND%"=="" set "AGENT_COMMAND=agent -p --trust --force"

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..\..\..") do set "ROOT_DIR=%%~fI\"
set "PROMPT_TEMPLATE=%ROOT_DIR%experiments\longmemeval\prompts\answer_from_memory.md"
set "WORK_DIR=%CASE_DIR%\work"
set "INPUT_JSON=%WORK_DIR%\input\question_input.json"
set "OUTPUT_DIR=%CASE_DIR%\outputs"
set "LOG_DIR=%CASE_DIR%\logs"
set "PROMPT_FILE=%LOG_DIR%\qa_prompt.txt"
set "STDOUT_FILE=%LOG_DIR%\qa_stdout.txt"
set "STDERR_FILE=%LOG_DIR%\qa_stderr.txt"
set "RAW_JSON_FILE=%LOG_DIR%\qa_raw_agent_output.json"
set "ANSWER_JSON=%OUTPUT_DIR%\answer.json"
set "RENDER_PS1=%ROOT_DIR%experiments\longmemeval\scripts\codex\qa_stage_render_prompt.ps1"
set "WRITE_PS1=%ROOT_DIR%experiments\longmemeval\scripts\codex\qa_stage_write_answer.ps1"
set "INVOKE_PS1=%SCRIPT_DIR%invoke_agent.ps1"

if not exist "%INPUT_JSON%" (
  echo Missing question input: %INPUT_JSON%
  exit /b 2
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%RENDER_PS1%"
if errorlevel 1 exit /b %ERRORLEVEL%

powershell -NoProfile -ExecutionPolicy Bypass -File "%INVOKE_PS1%" -PromptFile "%PROMPT_FILE%" -WorkDir "%WORK_DIR%" -StdoutFile "%STDOUT_FILE%" -StderrFile "%STDERR_FILE%" -AgentCommand "%AGENT_COMMAND%"
set "AGENT_EXIT=%ERRORLEVEL%"
if not "%AGENT_EXIT%"=="0" (
  echo Cursor QA agent failed with exit code %AGENT_EXIT%
  exit /b %AGENT_EXIT%
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%WRITE_PS1%"
if errorlevel 1 exit /b %ERRORLEVEL%

echo Wrote %ANSWER_JSON%
exit /b 0
