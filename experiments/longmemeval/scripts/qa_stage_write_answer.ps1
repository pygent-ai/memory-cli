$ErrorActionPreference = 'Stop'

$stdout = Get-Content -Raw -LiteralPath $env:STDOUT_FILE
$match = [regex]::Match($stdout, '(?s)\{.*\}')
if (-not $match.Success) {
    throw 'QA agent stdout did not contain a JSON object.'
}

$agent = $match.Value | ConvertFrom-Json
$q = Get-Content -Raw -LiteralPath $env:INPUT_JSON | ConvertFrom-Json

$result = [ordered]@{
    question_id = $q.question_id
    question = $q.question
    question_date = $q.question_date
    answer = [string]$agent.answer
    search_queries_and_cli_results = @($agent.search_queries_and_cli_results)
    notes = [string]$agent.notes
}

$agent | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $env:RAW_JSON_FILE -Encoding UTF8
$result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $env:ANSWER_JSON -Encoding UTF8
