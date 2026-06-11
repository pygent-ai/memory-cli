param(
    [string]$RunDir = ""
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'config.ps1')

if (-not $RunDir) {
    $runsRoot = Join-Path $ProjectRoot 'experiments\longmemeval\runs-cursor'
    $latest = Get-ChildItem -Path $runsRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "No runs found under $runsRoot"
    }
    $RunDir = $latest.FullName
}

$progressPath = Join-Path $RunDir 'progress.json'
if (-not (Test-Path -LiteralPath $progressPath)) {
    throw "Missing progress file: $progressPath"
}

$progress = Get-Content -Raw -Encoding UTF8 -LiteralPath $progressPath | ConvertFrom-Json
$completed = [int]$progress.completed
$failed = [int]$progress.failed
$skipped = [int]$progress.skipped
$total = [int]$progress.total
$running = @($progress.running)
$pending = @($progress.pending)
$metricsCount = (Get-ChildItem -Path (Join-Path $RunDir 'cases\*\outputs\metrics.json') -ErrorAction SilentlyContinue).Count
$done = $completed + $failed + $skipped
if ($metricsCount -gt $completed) {
    $completed = $metricsCount
    $done = $completed + $failed + $skipped
}
$pct = if ($total -gt 0) { [math]::Round(($done / $total) * 100, 1) } else { 0 }

Write-Host "Run dir: $RunDir"
Write-Host "Updated: $($progress.updated_at)"
Write-Host "Progress: $done / $total ($pct%)"
Write-Host "  completed: $completed (metrics files: $metricsCount)"
Write-Host "  failed:    $failed"
Write-Host "  skipped:   $skipped"
Write-Host "  running:   $($running.Count) $(if ($running.Count) { '[' + ($running -join ', ') + ']' } else { '' })"
Write-Host "  pending:   $($pending.Count)"

if ($progress.summary) {
    Write-Host ""
    Write-Host "Current aggregate metrics:"
    $progress.summary.overall | ConvertTo-Json -Depth 4
}
