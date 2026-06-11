@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..\..\..") do set "ROOT_DIR=%%~fI\"
set "RUN_ID=cursor-oracle-500-parallel"
set "RUN_DIR=%ROOT_DIR%experiments\longmemeval\runs-cursor\%RUN_ID%"
set "LOG_FILE=%RUN_DIR%\runner.log"
set "PROCESSED_DIR=datasets\longmemeval\processed\oracle"
set "RAW_FILE=datasets\longmemeval\raw\longmemeval_oracle.json"

pushd "%ROOT_DIR%" || exit /b 1

echo [%DATE% %TIME%] Preparing all oracle cases...
call "%SCRIPT_DIR%prepare_cases.cmd" --raw "%RAW_FILE%" --out-dir "%PROCESSED_DIR%"
if errorlevel 1 (
  echo prepare_cases failed
  popd
  exit /b 1
)

if not exist "%RUN_DIR%" mkdir "%RUN_DIR%"
echo [%DATE% %TIME%] Starting parallel Cursor run: %RUN_ID% > "%LOG_FILE%"
echo workers=5 cases=all >> "%LOG_FILE%"

set "PATH=%LOCALAPPDATA%\cursor-agent;%PATH%"
start "cursor-oracle-500" /b cmd /c "cd /d "%ROOT_DIR%" && set PATH=%LOCALAPPDATA%\cursor-agent;%%PATH%% && python "%SCRIPT_DIR%run_all_parallel.py" --processed-dir "%PROCESSED_DIR%" --cases all --workers 5 --run-id "%RUN_ID%" --agent-timeout-seconds 900 >> "%LOG_FILE%" 2>&1"

echo Started background run: %RUN_ID%
echo Run dir: %RUN_DIR%
echo Progress: %RUN_DIR%\progress.json
echo Log: %LOG_FILE%
echo Check progress with: experiments\longmemeval\scripts\cursor\check_progress.cmd --RunDir "%RUN_DIR%"

popd
exit /b 0
