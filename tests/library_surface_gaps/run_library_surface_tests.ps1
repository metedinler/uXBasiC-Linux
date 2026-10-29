[CmdletBinding()]
param(
    [string]$Uxb = (Join-Path $PSScriptRoot '..\..\bin\uxb.exe'),
    [string]$ReportRoot = (Join-Path $PSScriptRoot '..\..\reports\library_surface_gaps'),
    [string[]]$Libraries = @()
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null
$rows = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'library_surface_tests.csv')
if ($Libraries.Count -gt 0) {
    $rows = @($rows | Where-Object { $_.library -in $Libraries })
}
$results = @()

foreach ($row in $rows) {
    $source = Join-Path $PSScriptRoot $row.source
    $expected = (Get-Content (Join-Path $PSScriptRoot $row.expected) -Raw).Trim()
    $stdout = Join-Path $ReportRoot ($row.library + '.stdout.txt')
    & $Uxb par $source --quiet
    $parseExit = $LASTEXITCODE
    $runExit = -1
    $actual = ''
    if ($parseExit -eq 0) {
        & $Uxb run $source --interpreter-backend AST --quiet --stdout-out $stdout
        $runExit = $LASTEXITCODE
        if (Test-Path $stdout) { $actual = (Get-Content $stdout -Raw).Trim() }
    }
    $passed = $parseExit -eq 0 -and $runExit -eq 0 -and $actual -ceq $expected
    $results += [PSCustomObject]@{
        library = $row.library
        api_count = [int]$row.api_count
        parse_exit = $parseExit
        run_exit = $runExit
        passed = $passed
    }
    Write-Host "$($row.library): APIs=$($row.api_count) parse=$parseExit run=$runExit pass=$passed"
}

$failed = @($results | Where-Object { -not $_.passed })
$results | Export-Csv -LiteralPath (Join-Path $ReportRoot 'results.csv') -NoTypeInformation -Encoding UTF8
[PSCustomObject]@{
    schema = 'uxbasic.library-surface-gap-tests.v1'
    libraries = $results.Count
    api_signatures = ($results | Measure-Object api_count -Sum).Sum
    passed = $results.Count - $failed.Count
    failed = $failed.Count
} | ConvertTo-Json | Set-Content (Join-Path $ReportRoot 'summary.json') -Encoding UTF8

if ($failed.Count -gt 0) {
    Write-Error "Library surface failures: $($failed.library -join ', ')"
    exit 1
}
Write-Host "PASS: $($results.Count) libraries, $(($results | Measure-Object api_count -Sum).Sum) previously-uncovered API signatures."
