$ErrorActionPreference = 'Stop'

$q = Get-Content -Raw -Encoding UTF8 -LiteralPath $env:INPUT_JSON | ConvertFrom-Json
$template = Get-Content -Raw -Encoding UTF8 -LiteralPath $env:PROMPT_TEMPLATE
$questionText = $q.question + "`n`nQuestion date: " + $q.question_date
$prompt = $template.Replace('{{QUESTION}}', $questionText)

[System.IO.File]::WriteAllText(
    $env:PROMPT_FILE,
    $prompt,
    [System.Text.UTF8Encoding]::new($false)
)
