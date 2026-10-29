[CmdletBinding()]
param(
    [string]$Uxb = (Join-Path $PSScriptRoot '..\..\bin\uxb.exe'),
    [string]$ReportRoot = (Join-Path $PSScriptRoot '..\..\reports\surface_gaps')
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null
$rows = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'surface_tests.csv')
$failures = @()

foreach ($row in $rows) {
    $source = Join-Path $PSScriptRoot $row.source
    $expectedPath = Join-Path $PSScriptRoot $row.expected
    $actualPath = Join-Path $ReportRoot ($row.id + '.stdout.txt')
    $stderrPath = Join-Path $ReportRoot ($row.id + '.stderr.txt')

    & $Uxb par $source --quiet
    if ($LASTEXITCODE -ne 0) {
        $failures += "$($row.id): parser exit=$LASTEXITCODE"
        continue
    }
    & $Uxb run $source --interpreter-backend $row.backend --quiet `
        --stdout-out $actualPath --stderr-out $stderrPath
    if ($LASTEXITCODE -ne 0) {
        $failures += "$($row.id): runtime exit=$LASTEXITCODE"
        continue
    }

    $expected = (Get-Content -LiteralPath $expectedPath -Raw).Replace("`r`n","`n").TrimEnd()
    $actual = (Get-Content -LiteralPath $actualPath -Raw).Replace("`r`n","`n").TrimEnd()
    if ($actual -cne $expected) {
        $failures += "$($row.id): stdout mismatch"
        Write-Host "--- EXPECTED $($row.id) ---"
        Write-Host $expected
        Write-Host "--- ACTUAL $($row.id) ---"
        Write-Host $actual
    } else {
        Write-Host "PASS $($row.id): $($row.features)"
    }
}

$summary = [PSCustomObject]@{
    schema = 'uxbasic.surface-gap-tests.v1'
    total = $rows.Count
    passed = $rows.Count - $failures.Count
    failed = $failures.Count
    failures = $failures
}
$summary | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $ReportRoot 'summary.json') -Encoding UTF8
if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}
Write-Host "PASS: $($rows.Count)/$($rows.Count) uncovered-surface tests."
