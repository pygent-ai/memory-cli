$ErrorActionPreference = 'Stop'

$stdout = Get-Content -Raw -Encoding UTF8 -LiteralPath $env:STDOUT_FILE
$match = [regex]::Match($stdout, '(?s)\{.*\}')
if (-not $match.Success) {
    throw 'QA agent stdout did not contain a JSON object.'
}

$agent = $match.Value | ConvertFrom-Json
$q = Get-Content -Raw -Encoding UTF8 -LiteralPath $env:INPUT_JSON | ConvertFrom-Json

$result = [ordered]@{
    question_id = $q.question_id
    question = $q.question
    question_date = $q.question_date
    answer = [string]$agent.answer
    search_queries_and_cli_results = @($agent.search_queries_and_cli_results)
    notes = [string]$agent.notes
}

[System.IO.File]::WriteAllText(
    $env:RAW_JSON_FILE,
    ($agent | ConvertTo-Json -Depth 20),
    [System.Text.UTF8Encoding]::new($false)
)
[System.IO.File]::WriteAllText(
    $env:ANSWER_JSON,
    ($result | ConvertTo-Json -Depth 20),
    [System.Text.UTF8Encoding]::new($false)
)
