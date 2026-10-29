param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")),
    [string]$Uxb = "",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command py -ErrorAction Stop).Source }

if (-not $SkipBuild) {
    & (Join-Path $Root "build_64.bat")
    if ($LASTEXITCODE -ne 0) { throw "build_64.bat failed: $LASTEXITCODE" }
}

if ([string]::IsNullOrWhiteSpace($Uxb)) {
    $candidates = @(
        (Join-Path $Root "bin\uxb.exe"),
        (Join-Path $Root "uxb.exe"),
        (Join-Path $Root "bin\uxb.exe")
    )
    $Uxb = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $Uxb -or -not (Test-Path $Uxb)) { throw "uxb.exe not found; pass -Uxb <path>" }

$validator = Join-Path $Root "tests\mir_full_json_v2\verify_mir_full_json_v2.py"
$source = Join-Path $Root "tests\mir_full_json_v2\mir_full_json_v2_smoke.uxb"
$out = Join-Path $Root "reports\mir_full_json_v2\mir_full_json_v2_smoke.json"

& $python $validator --root $Root --uxb $Uxb --source $source --out $out
if ($LASTEXITCODE -ne 0) { throw "MIR full JSON v2 smoke failed: $LASTEXITCODE" }

Write-Host "PASS MIR full JSON v2 smoke"
Write-Host "JSON: $out"
