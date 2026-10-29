[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Out,

    [string]$ProjectName = "",
    [string]$Profile = "",
    [string]$Uxb = "",
    [switch]$StrictDiagnostics,
    [switch]$StrictCoverage
)

$ErrorActionPreference = "Stop"
$toolRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$uxbRoot = (Resolve-Path (Join-Path $toolRoot "..\..\..")).Path
$sourcePath = (Resolve-Path $Source).Path
$outPath = [System.IO.Path]::GetFullPath($Out)

if (-not $Uxb) {
    $Uxb = Join-Path $uxbRoot "bin\uxb.exe"
}
$uxbPath = (Resolve-Path $Uxb).Path

if (-not $ProjectName) {
    $ProjectName = [System.IO.Path]::GetFileNameWithoutExtension($sourcePath)
}

$jsonDir = Join-Path $outPath "_uxb_json"
New-Item -ItemType Directory -Path $jsonDir -Force | Out-Null
$astJson = Join-Path $jsonDir "ast.json"

Write-Host "[1/2] uXBasic AST JSON üretiliyor..."
& $uxbPath ast $sourcePath --ast-json-out $astJson --quiet
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $astJson)) {
    throw "uxb.exe AST üretimi başarısız oldu (exit=$LASTEXITCODE): $sourcePath"
}

# Kaynak satırları, yorumlar ve CALL DLL/API ifadeleri eksiksiz korunsun.
Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $jsonDir "preprocessed.uxb") -Force

$argsList = @(
    (Join-Path $toolRoot "uxbasic2pdsxS.py"),
    "--json-dir", $jsonDir,
    "--ast-json", $astJson,
    "--source", $sourcePath,
    "--out", $outPath,
    "--project-name", $ProjectName
)
if ($Profile) { $argsList += @("--profile", $Profile) }
if ($StrictDiagnostics) { $argsList += "--strict-diagnostics" }
if ($StrictCoverage) { $argsList += "--strict-coverage" }

Write-Host "[2/2] pdsX BASX/proje çıktısı üretiliyor..."
& python @argsList
if ($LASTEXITCODE -ne 0) {
    throw "uxbasic2pdsxS dönüşümü başarısız oldu (exit=$LASTEXITCODE)."
}

Write-Host "PDSX_OK project=$(Join-Path $outPath ($ProjectName + '.prj'))"
