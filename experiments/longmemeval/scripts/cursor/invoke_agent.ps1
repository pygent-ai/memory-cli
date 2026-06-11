param(
    [Parameter(Mandatory = $true)]
    [string]$PromptFile,

    [Parameter(Mandatory = $true)]
    [string]$WorkDir,

    [Parameter(Mandatory = $true)]
    [string]$StdoutFile,

    [Parameter(Mandatory = $true)]
    [string]$StderrFile,

    [string]$AgentCommand = 'agent -p --trust --force'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'config.ps1')

if (-not (Test-CursorAgentInstalled)) {
    throw "cursor agent CLI not found. $(Get-CursorAgentInstallHint)"
}

if (-not (Test-Path -LiteralPath $PromptFile)) {
    throw "Prompt file not found: $PromptFile"
}

$workDir = (Resolve-Path -LiteralPath $WorkDir).Path
$prompt = Get-Content -Raw -Encoding UTF8 -LiteralPath $PromptFile
$agentArgs = $AgentCommand.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) |
    Where-Object { $_ -ne 'agent' }

$venvScripts = Join-Path $workDir '.venv\Scripts'
if (Test-Path -LiteralPath $venvScripts) {
    $env:PATH = "$venvScripts;$env:PATH"
}

Push-Location $workDir
try {
    & agent @agentArgs --workspace $workDir $prompt 1> $StdoutFile 2> $StderrFile
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
