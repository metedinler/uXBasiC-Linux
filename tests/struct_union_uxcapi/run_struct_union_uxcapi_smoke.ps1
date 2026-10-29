[CmdletBinding()]
param(
    [switch]$BuildCompiler,
    [switch]$SkipRuntimeSmoke,
    [string]$Uxb = ""
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$reports = Join-Path $root "reports\struct_union_uxcapi"
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$runtimeBin = Join-Path $root "dist\libraries\bin"
$compilerBin = Join-Path $root "bin"
$msysBin = if ($env:UXB_MSYS2_ROOT) {
    Join-Path $env:UXB_MSYS2_ROOT "ucrt64\bin"
} else {
    "C:\msys64\ucrt64\bin"
}
$env:PATH = (@($runtimeBin, $compilerBin, $msysBin, $env:PATH) -join ";")

python (Join-Path $PSScriptRoot "verify_patch.py") --root $root
if ($LASTEXITCODE -ne 0) { throw "Static verification failed" }

if ($BuildCompiler) {
    & (Join-Path $root "build_64.bat")
    if ($LASTEXITCODE -ne 0) { throw "Compiler build failed" }
}

& (Join-Path $root "runtime_ext\uxcapi\build_uxcapi_dll.bat")
if ($LASTEXITCODE -ne 0) { throw "uxcapi.dll build failed" }

& (Join-Path $PSScriptRoot "build_testlib.bat")
if ($LASTEXITCODE -ne 0) { throw "Aggregate test DLL build failed" }

if ([string]::IsNullOrWhiteSpace($Uxb)) {
    $candidates = @(
        (Join-Path $root "bin\uxb.exe"),
        (Join-Path $root "uxb.exe"),
        (Join-Path $root "compiler\uxb.exe")
    )
    $Uxb = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if ([string]::IsNullOrWhiteSpace($Uxb) -or -not (Test-Path $Uxb)) {
    throw "uxb.exe bulunamadi. -Uxb ile yolu verin veya -BuildCompiler kullanin."
}

$layoutSource = Join-Path $PSScriptRoot "struct_union_layout_smoke.uxb"
$mirJson = Join-Path $reports "struct_union_layout.mir.json"
$layoutLog = Join-Path $reports "struct_union_layout.stdout.txt"

Push-Location $root
try {
    & $Uxb $layoutSource --mir-full-json-out $mirJson 2>&1 | Tee-Object -FilePath $layoutLog
    if ($LASTEXITCODE -ne 0) { throw "STRUCT/UNION layout compile failed" }

    python (Join-Path $PSScriptRoot "validate_mir_records.py") $mirJson
    if ($LASTEXITCODE -ne 0) { throw "MIR record_types validation failed" }

    if (-not $SkipRuntimeSmoke) {
        $ffiSource = Join-Path $PSScriptRoot "aggregate_ffi_smoke.uxb"
        $ffiLog = Join-Path $reports "aggregate_ffi.stdout.txt"
        & $Uxb run $ffiSource --quiet 2>&1 | Tee-Object -FilePath $ffiLog
        if ($LASTEXITCODE -ne 0) { throw "Aggregate FFI smoke failed" }

        $text = Get-Content -Raw $ffiLog
        $patterns = @{
            "TYPE_FINALIZE" = 'TYPE_FINALIZE=\s*1'
            "TYPE_SIZE" = 'TYPE_SIZE=\s*8'
            "TYPE_ALIGN" = 'TYPE_ALIGN=\s*4'
            "SUM" = 'SUM=\s*4(?:\.0+)?'
            "ADD_X" = 'ADD_X=\s*11\.5'
            "ADD_Y" = 'ADD_Y=\s*22\.5'
        }
        foreach ($name in $patterns.Keys) {
            if ($text -notmatch $patterns[$name]) {
                throw "Aggregate FFI output missing or wrong: $name"
            }
        }
    }
} finally {
    Pop-Location
}

Write-Host "PASS: STRUCT + UNION + uxcapi aggregate smoke"
