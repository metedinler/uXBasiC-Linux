[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')),
    [string]$OutputDirectory = '',
    [switch]$SkipGate
)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path $Root).Path
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $Root 'dist\release' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

if (-not $SkipGate) {
    & (Join-Path $Root 'run_uxwasmrt_gate.ps1') -Root $Root
}

$required = @(
    'bin\uxb.exe','bin\uxwasmrt.dll','bin\wasmtime.dll',
    'tools\wabt\bin\wat2wasm.exe','tools\wabt\bin\wasm-validate.exe',
    'runtime\browser\ux_wasm_bridge.js','include\modules\uxwasmrt.uxmh',
    'libsx\uxwasmrt\uxwasmrt.bas','tests\libraries\uxwasmrt\test_uxwasmrt.py',
    'tests\libraries\uxwasmrt\verify_distribution.py',
    'tests\libraries\uxwasmrt\core_i32_smoke.wasm',
    'tests\libraries\uxwasmrt\invalid_import.wasm'
)
foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $relative))) {
        throw "Distribution input missing: $relative"
    }
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$name = "uxbasic_wasm_core_i32_win64_$stamp"
$stage = Join-Path $OutputDirectory $name
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-Tree([string]$Relative) {
    $source = Join-Path $Root $Relative
    if (-not (Test-Path -LiteralPath $source)) { return }
    $destination = Join-Path $stage $Relative
    New-Item -ItemType Directory -Force -Path (Split-Path $destination -Parent) | Out-Null
    Copy-Item -Recurse -Force -LiteralPath $source -Destination $destination
}

Copy-Tree 'bin'
Copy-Tree 'include'
Copy-Tree 'libsx'
Copy-Tree 'runtime\browser'
Copy-Tree 'tools\wabt\bin'
Copy-Tree 'tests\libraries\uxwasmrt'
Copy-Tree 'runtime_ext\uxwasmrt\THIRD_PARTY_NOTICE.md'

$readme = @'
# uXBasic WAT/WASM çalışma dağıtımı

Profil: core-i32
Native sağlayıcı: uxwasmrt.dll + Wasmtime standard wasm-c-api
Browser sağlayıcı: yerleşik WebAssembly + runtime/browser/ux_wasm_bridge.js

Doğrulama:

    python .\tests\libraries\uxwasmrt\verify_distribution.py --root .

WASM üretme örneği:

    .\bin\uxb.exe --source .\tests\libraries\uxwasmrt\compiler_core_i32.uxb --emit-wasm --wasm-wat-out .\program.wat --wasm-out .\program.wasm --wat2wasm .\tools\wabt\bin\wat2wasm.exe

Bu sürümde güvenilir üretim sözleşmesi i32 parametre/sonuç ve compiler'ın mevcut ux.host_call4/print importlarıdır. String, linear-memory ABI, WASI ve Component Model bu pakette etkin değildir.
'@
Set-Content -Encoding UTF8 -LiteralPath (Join-Path $stage 'README_WASM_RUNTIME_TR.md') -Value $readme

$verifyJson = Join-Path $stage 'wasm_distribution_verify.json'
$global:LASTEXITCODE = 0
Push-Location $stage
try {
    & python '.\tests\libraries\uxwasmrt\verify_distribution.py' '--root' '.' '--json-out' $verifyJson
    $verifyExit = $LASTEXITCODE
} finally { Pop-Location }
if ($verifyExit -ne 0) { throw "Staged WASM distribution verification failed exit=$verifyExit" }

$hashes = @()
Get-ChildItem -Recurse -File $stage | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($stage.Length).TrimStart('\','/') -replace '\\','/'
    $hashes += [ordered]@{
        path = $relative
        bytes = $_.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    }
}
$manifest = [ordered]@{
    schema = 'uxb.wasm.distribution.manifest.v1'
    status = 'PASS'
    profile = 'core-i32'
    generatedUtc = (Get-Date).ToUniversalTime().ToString('o')
    files = $hashes
}
$manifest | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $stage 'release_manifest.json')

$zip = Join-Path $OutputDirectory "$name.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal

$verifyStage = Join-Path $OutputDirectory "$name.verify"
if (Test-Path $verifyStage) { Remove-Item -Recurse -Force $verifyStage }
Expand-Archive -LiteralPath $zip -DestinationPath $verifyStage -Force
$global:LASTEXITCODE = 0
Push-Location $verifyStage
try {
    & python '.\tests\libraries\uxwasmrt\verify_distribution.py' '--root' '.' '--json-out' '.\wasm_distribution_verify_after_zip.json'
    $verifyZipExit = $LASTEXITCODE
} finally { Pop-Location }
if ($verifyZipExit -ne 0) { throw "Extracted distribution verification failed exit=$verifyZipExit" }

$result = [ordered]@{
    schema = 'uxb.wasm.distribution.package.v1'
    status = 'PASS'
    zip = $zip
    bytes = (Get-Item $zip).Length
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $zip).Hash.ToLowerInvariant()
    verifiedExtract = $verifyStage
}
$resultPath = "$zip.verify.json"
$result | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $resultPath
Write-Host "WASM_DISTRIBUTION_ZIP=$zip"
Write-Host "WASM_DISTRIBUTION_VERIFY=$resultPath"
Write-Host 'UXB_WASM_DISTRIBUTION_PACKAGE_PASS'
