[CmdletBinding()]
param(
    [string]$Root = ".",
    [string]$Uxb = "",
    [switch]$BuildUxffi,
    [switch]$RunX64
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-FirstExisting {
    param([string[]]$Candidates)
    foreach ($candidate in $Candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and
            (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return ""
}

$Root = (Resolve-Path -LiteralPath $Root).Path
if ([string]::IsNullOrWhiteSpace($Uxb)) {
    $Uxb = Join-Path $Root "bin\uxb.exe"
}
if (-not (Test-Path -LiteralPath $Uxb)) {
    throw "uXBasic executable not found: $Uxb"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path $Root "reports\libraries\ffi_contract\$stamp"
New-Item -ItemType Directory -Path $report -Force | Out-Null

$staticVerifier = Join-Path $Root "tools\tests\verify_ffi_contract_patch.py"
if (-not (Test-Path -LiteralPath $staticVerifier)) {
    throw "static verifier missing: $staticVerifier"
}
python $staticVerifier `
    --root $Root `
    --json-out (Join-Path $report "static_validation.json") |
    Tee-Object -FilePath (Join-Path $report "static_validation.log")
if ($LASTEXITCODE -ne 0) {
    throw "static FFI contract validation failed"
}

if ($BuildUxffi) {
    $build = Join-Path $Root "runtime_ext\uxffi\build_uxffi_dll.bat"
    if (-not (Test-Path -LiteralPath $build)) {
        throw "uxffi build script missing: $build"
    }
    & $build 2>&1 | Tee-Object -FilePath (Join-Path $report "build_uxffi.log")
    if ($LASTEXITCODE -ne 0) {
        throw "uxffi.dll build failed"
    }
}

$gcc = Resolve-FirstExisting @(
    $env:UXB_GCC,
    "C:\msys64\ucrt64\bin\x86_64-w64-mingw32-gcc.exe",
    "C:\msys64\ucrt64\bin\gcc.exe"
)
if ([string]::IsNullOrWhiteSpace($gcc)) {
    throw "MSYS2 UCRT64 GCC not found; set UXB_GCC"
}

$testDllSource = Join-Path $Root "tests\libraries\ffi_contract\uxb_ffi_contract_test.c"
$testDll = Join-Path $Root "bin\uxb_ffi_contract_test.dll"
& $gcc `
    -std=c11 -O2 -Wall -Wextra -Werror `
    -shared -static-libgcc `
    -o $testDll $testDllSource `
    2>&1 | Tee-Object -FilePath (Join-Path $report "build_test_dll.log")
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $testDll)) {
    throw "FFI contract test DLL build failed"
}

$positive = Join-Path $Root "tests\libraries\ffi_contract\ffi_contract_positive.uxb"
$statement = Join-Path $Root "tests\libraries\ffi_contract\ffi_contract_statement_form.uxb"
$positiveArity10 = Join-Path $Root "tests\libraries\ffi_contract\positive_arity10_parse.uxb"
$negativeType = Join-Path $Root "tests\libraries\ffi_contract\negative_type_count.uxb"
$negativeArity = Join-Path $Root "tests\libraries\ffi_contract\negative_arity11.uxb"
$negativeConvention = Join-Path $Root "tests\libraries\ffi_contract\negative_invalid_convention.uxb"

function Invoke-UxbExpectPass {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [string]$RequiredText = ""
    )
    $output = @(& $Uxb @Arguments 2>&1)
    $output | Set-Content -LiteralPath (Join-Path $report "$Name.log") -Encoding UTF8
    $output | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed"
    }
    $joined = $output -join "`n"
    if (-not [string]::IsNullOrWhiteSpace($RequiredText) -and
        $joined -notmatch [regex]::Escape($RequiredText)) {
        throw "$Name did not print required marker: $RequiredText"
    }
    return $joined
}

function Invoke-UxbExpectFail {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [string]$RequiredPattern
    )
    $output = @(& $Uxb @Arguments 2>&1)
    $output | Set-Content -LiteralPath (Join-Path $report "$Name.log") -Encoding UTF8
    $output | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -eq 0) {
        throw "$Name unexpectedly passed"
    }
    $joined = $output -join "`n"
    if ($joined -notmatch $RequiredPattern) {
        throw "$Name failed without the expected diagnostic: $RequiredPattern"
    }
}

$oldPath = $env:PATH
try {
    $env:PATH = (
        (Join-Path $Root "bin"),
        (Join-Path $Root "dist\libraries\bin"),
        (Join-Path $Root "dist\libraries\deps"),
        "C:\msys64\ucrt64\bin",
        $oldPath
    ) -join ";"

    Invoke-UxbExpectPass "par_positive" @("par", $positive) | Out-Null
    Invoke-UxbExpectPass "par_statement" @("par", $statement) | Out-Null
    Invoke-UxbExpectPass "par_positive_arity10" @("par", $positiveArity10) | Out-Null

    Invoke-UxbExpectFail `
        "par_negative_type_count" `
        @("par", $negativeType) `
        "type-list count mismatch"

    Invoke-UxbExpectFail `
        "par_negative_arity11" `
        @("par", $negativeArity) `
        "ABI10|at most 10|exceed"

    Invoke-UxbExpectFail `
        "par_negative_convention" `
        @("par", $negativeConvention) `
        "invalid calling convention"

    $astOutput = Invoke-UxbExpectPass `
        "ast_positive" `
        @("int", $positive, "--interpreter-backend", "AST") `
        "UXB_FFI_CONTRACT_PASS"

    $mirOutput = Invoke-UxbExpectPass `
        "mir_positive" `
        @("int", $positive, "--interpreter-backend", "MIR") `
        "UXB_FFI_CONTRACT_PASS"

    Invoke-UxbExpectPass `
        "ast_statement" `
        @("int", $statement, "--interpreter-backend", "AST") `
        "UXB_FFI_STATEMENT_PASS" | Out-Null

    Invoke-UxbExpectPass `
        "mir_statement" `
        @("int", $statement, "--interpreter-backend", "MIR") `
        "UXB_FFI_STATEMENT_PASS" | Out-Null

    if ($astOutput -notmatch "UXB_FFI_CONTRACT_PASS" -or
        $mirOutput -notmatch "UXB_FFI_CONTRACT_PASS") {
        throw "AST/MIR observable result parity failed"
    }

    $x64Status = "NOT_RUN"
    if ($RunX64) {
        $exe = Join-Path $report "ffi_contract_positive.exe"
        Invoke-UxbExpectPass `
            "x64_build" `
            @("bld", $positive, "--build-x64", "--build-x64-out", $exe) |
            Out-Null

        $x64Output = @(& $exe 2>&1)
        $x64Output | Tee-Object -FilePath (Join-Path $report "x64_run.log")
        if ($LASTEXITCODE -ne 0 -or
            (($x64Output -join "`n") -notmatch "UXB_FFI_CONTRACT_PASS")) {
            throw "x64 executable failed or returned the wrong output"
        }
        $x64Status = "PASS"
    }

    $summary = [ordered]@{
        schema = "uxb.ffi.contract.fix.v3"
        status = "PASS"
        root = $Root
        report = $report
        uxffi_built = [bool]$BuildUxffi
        parser = "PASS"
        ast = "PASS"
        mir = "PASS"
        x64 = $x64Status
        contract = [ordered]@{
            version_min = 131
            max_runtime_args = 10
            legacy_default_arg_type = "I32"
        }
    }
    $summary | ConvertTo-Json -Depth 6 |
        Set-Content -LiteralPath (Join-Path $report "summary.json") -Encoding UTF8
}
finally {
    $env:PATH = $oldPath
}

Write-Host "UXB_FFI_CONTRACT_FIX_PASS"
Write-Host "Report: $report"
