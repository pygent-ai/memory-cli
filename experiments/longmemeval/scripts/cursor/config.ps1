# Shared defaults for Cursor-backed LongMemEval scripts.
$ErrorActionPreference = 'Stop'

$Script:CursorScriptsDir = $PSScriptRoot
$Script:ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$Script:LongMemEvalScriptsDir = Join-Path $ProjectRoot 'experiments\longmemeval\scripts\codex'
$Script:LongMemEvalPromptsDir = Join-Path $ProjectRoot 'experiments\longmemeval\prompts'

$Script:DefaultAgentCommand = 'agent -p --trust --force'
$Script:DefaultAgentTimeoutSeconds = 900
$Script:DefaultRunsDir = Join-Path $ProjectRoot 'experiments\longmemeval\runs-cursor'

$Script:CursorAgentScript = Join-Path $env:LOCALAPPDATA 'cursor-agent\agent.ps1'

function Test-CursorAgentInstalled {
    if (Get-Command agent -ErrorAction SilentlyContinue) {
        return $true
    }
    return Test-Path -LiteralPath $Script:CursorAgentScript
}

function Get-CursorAgentInstallHint {
    return "Install Cursor CLI with: irm 'https://cursor.com/install?win32=true' | iex"
}
