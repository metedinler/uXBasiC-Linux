param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $Root).Path
if (-not $OutputRoot) {
    $OutputRoot = Join-Path (Split-Path $Root -Parent) "release_packages"
}
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$name = "UXBASIC_ABI10_QUICKJS_WASMTIME_PCK_$stamp"
$stage = Join-Path $OutputRoot $name
$zip = Join-Path $OutputRoot "$name.zip"
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-Tree([string]$Source, [string]$Target) {
    if (-not (Test-Path -LiteralPath $Source)) { throw "Missing package input: $Source" }
    New-Item -ItemType Directory -Force -Path (Split-Path $Target -Parent) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Target -Recurse -Force
}

New-Item -ItemType Directory -Force -Path (Join-Path $stage "bin") | Out-Null
Get-ChildItem (Join-Path $Root "bin") -File |
    Where-Object {
        $_.Extension -in ".dll", ".exe" -and
        $_.Name -notmatch "(?i)eski|backup|\.bak"
    } |
    Copy-Item -Destination (Join-Path $stage "bin") -Force

Copy-Tree (Join-Path $Root "docs\uxb_pck_book") (Join-Path $stage "docs\uxb_pck_book")
Copy-Tree (Join-Path $Root "docs\uxbasic_pck_kitaplar") (Join-Path $stage "docs\uxbasic_pck_kitaplar")
Copy-Item -LiteralPath (Join-Path $Root "pck_son(20.07).md") -Destination (Join-Path $stage "docs") -Force
Copy-Tree (Join-Path $Root "include") (Join-Path $stage "include")
Copy-Tree (Join-Path $Root "libsx") (Join-Path $stage "libsx")
Copy-Tree (Join-Path $Root "runtime\browser") (Join-Path $stage "runtime\browser")
Copy-Tree (Join-Path $Root "build\manual\config") (Join-Path $stage "config")

$exampleMap = @(
    @("tests\libraries\ffi_final\ffi_freebasic_roundtrip.uxb", "examples\01_ffi_abi10"),
    @("tests\run_ffi_attestation_smoke.bas", "examples\02_strict_attestation"),
    @("tests\libraries\uxjsruntime\uxjsruntime_smoke.uxb", "examples\03_quickjs"),
    @("tests\libraries\uxjsruntime\generated_js_e2e.uxb", "examples\03_quickjs"),
    @("tests\libraries\uxwasmrt\uxwasmrt_smoke.uxb", "examples\04_wasmtime"),
    @("tests\libraries\uxwasmrt\compiler_core_i32.uxb", "examples\04_wasmtime"),
    @("tests\libraries\uxwasmrt\core_i32_smoke.wat", "examples\04_wasmtime"),
    @("tests\libraries\uxwasmrt\core_i32_smoke.wasm", "examples\04_wasmtime")
)
Copy-Tree (Join-Path $Root "release_assets\examples") (Join-Path $stage "examples")
foreach ($item in $exampleMap) {
    $target = Join-Path $stage $item[1]
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Copy-Item -LiteralPath (Join-Path $Root $item[0]) -Destination $target -Force
}

New-Item -ItemType Directory -Force -Path (Join-Path $stage "tests") | Out-Null
Copy-Tree (Join-Path $Root "tests\libraries\ffi_final") (Join-Path $stage "tests\ffi_final")
Copy-Tree (Join-Path $Root "tests\libraries\ffi_contract") (Join-Path $stage "tests\ffi_contract")
Copy-Tree (Join-Path $Root "tests\libraries\uxjsruntime") (Join-Path $stage "tests\uxjsruntime")
Copy-Tree (Join-Path $Root "tests\libraries\uxwasmrt") (Join-Path $stage "tests\uxwasmrt")
Get-ChildItem (Join-Path $Root "reports") -File -Filter *.exe |
    Copy-Item -Destination (Join-Path $stage "tests") -Force

New-Item -ItemType Directory -Force -Path (Join-Path $stage "reports") | Out-Null
Copy-Item -LiteralPath (Join-Path $Root "reports\pck_document_audit_20260727.json") -Destination (Join-Path $stage "reports") -Force
$latestFfi = Get-ChildItem (Join-Path $Root "reports\final_ffi_quickjs_release") -Directory | Sort-Object Name -Descending | Select-Object -First 1
$latestWasm = Get-ChildItem (Join-Path $Root "reports\wasm\uxwasmrt") -Directory | Sort-Object Name -Descending | Select-Object -First 1
Copy-Tree $latestFfi.FullName (Join-Path $stage "reports\final_ffi_quickjs_release")
Copy-Tree $latestWasm.FullName (Join-Path $stage "reports\wasmtime")

$signRows = Get-ChildItem (Join-Path $stage "bin") -File |
    Where-Object { $_.Extension -in ".dll", ".exe" } |
    ForEach-Object {
        $sig = Get-AuthenticodeSignature -LiteralPath $_.FullName
        [ordered]@{
            path = $_.FullName.Substring($stage.Length + 1).Replace("\", "/")
            status = [string]$sig.Status
            signer_subject = if ($sig.SignerCertificate) { $sig.SignerCertificate.Subject } else { "" }
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
[ordered]@{
    schema = "uxb.authenticode-status.v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    note = "NotSigned means no production code-signing certificate was available; SHA-256 manifest still verifies package integrity."
    files = @($signRows)
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage "AUTHENTICODE_STATUS.json") -Encoding UTF8

@'
# uXBasic ABI10 + QuickJS + Wasmtime + PCK paketi

Bu paket `dist` altında üretilmemiştir. ABI10 API 131, strict attestation,
QuickJS ve Wasmtime dış çalışma zamanı doğrulamalarının güncel raporlarını,
aktif DLL/EXE dosyalarını, testleri ve ayrı örnek klasörlerini içerir.

`AUTHENTICODE_STATUS.json` gerçek Windows imza durumunu; `MANIFEST_SHA256.json`
ise paket içi bütünlüğü gösterir. Makinede özel kod-imzalama sertifikası
bulunmadığından `NotSigned` ikililer imzalı olarak sunulmamıştır.

Doğrulama:

```powershell
.\VERIFY_PACKAGE.ps1
```
'@ | Set-Content -LiteralPath (Join-Path $stage "README_FIRST_TR.md") -Encoding UTF8

@'
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$manifest = Get-Content -Raw -LiteralPath (Join-Path $root "MANIFEST_SHA256.json") | ConvertFrom-Json
foreach ($row in $manifest.files) {
    $path = Join-Path $root ($row.path.Replace("/", "\"))
    if (-not (Test-Path -LiteralPath $path)) { throw "Eksik dosya: $($row.path)" }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    if ($actual -ne $row.sha256) { throw "Hash uyusmazligi: $($row.path)" }
}
& (Join-Path $root "bin\uxb.exe") --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Paketlenmis uxb.exe --help basarisiz" }
Write-Host "UXB_EXTERNAL_RELEASE_PACKAGE_VERIFY_PASS"
'@ | Set-Content -LiteralPath (Join-Path $stage "VERIFY_PACKAGE.ps1") -Encoding UTF8

$manifestRows = Get-ChildItem $stage -Recurse -File |
    Where-Object { $_.Name -ne "MANIFEST_SHA256.json" } |
    ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($stage.Length + 1).Replace("\", "/")
            bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
[ordered]@{
    schema = "uxb.release-manifest.v1"
    generated_utc = [DateTime]::UtcNow.ToString("o")
    files = @($manifestRows)
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage "MANIFEST_SHA256.json") -Encoding UTF8

& (Join-Path $stage "VERIFY_PACKAGE.ps1")
Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal
if (-not (Test-Path -LiteralPath $zip)) { throw "ZIP olusturulamadi" }

$verifyDir = Join-Path $OutputRoot "$name.verify"
Expand-Archive -LiteralPath $zip -DestinationPath $verifyDir
$expandedRoot = Join-Path $verifyDir $name
& (Join-Path $expandedRoot "VERIFY_PACKAGE.ps1")

$zipHash = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
Write-Host "UXB_EXTERNAL_RELEASE_PACKAGE_PASS"
Write-Host "ZIP=$zip"
Write-Host "SHA256=$zipHash"
