param(
    [switch]$NoRepair = $true,
    [string]$Python = "",
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Continue"

function Write-TextFile($Path, $Text) {
    $dir = Split-Path -Parent $Path
    if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
    $Text | Set-Content -Encoding UTF8 $Path
}

function JsonEscape([string]$s) {
    if ($null -eq $s) { return "" }
    return ($s -replace '\\','\\' -replace '"','\"' -replace "`r",'\r' -replace "`n",'\n')
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
Set-Location $RepoRoot

$step = "adim14_backend_js_wasm_browser"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$current = "reports/control/current"
$historyRoot = "reports/control/history"
$historyTarget = Join-Path $historyRoot "${step}_${stamp}"
New-Item -ItemType Directory -Force $historyRoot | Out-Null
if (Test-Path $current) {
    $items = Get-ChildItem $current -Force -ErrorAction SilentlyContinue
    if ($items) {
        New-Item -ItemType Directory -Force $historyTarget | Out-Null
        Move-Item "$current\*" $historyTarget -Force
    }
}
New-Item -ItemType Directory -Force $current | Out-Null

$expectedActual = @()
$errorRows = @()

function Add-ExpectedActual($Name, $Expected, $Actual, $Status) {
    $script:expectedActual += [pscustomobject]@{ test=$Name; expected=$Expected; actual=$Actual; status=$Status }
}

function Add-ErrorRow($Class, $Layer, $File, $Expected, $Actual, $Fix) {
    $script:errorRows += [pscustomobject]@{
        error_class_tr=$Class; layer=$Layer; file=$File; expected=$Expected; actual=$Actual; required_fix=$Fix
    }
}

# Required files after patch merge.
$required = @(
    "src/codegen/js/uxb_js_backend_contract_adim14.fbs",
    "src/codegen/js/uxb_js_emit_buffer_adim14.fbs",
    "src/codegen/js/uxb_js_backend_strict_adim14.fbs",
    "src/codegen/wasm/uxb_wat_emit_buffer_adim14.fbs",
    "src/codegen/wasm/uxb_wasm_type_bridge_adim14.fbs",
    "src/codegen/wasm/uxb_wasm_backend_strict_adim14.fbs",
    "src/codegen/browser/uxb_browser_artifact_adim14.fbs",
    "src/backend/uxb_backend_web_gate_adim14.fbs",
    "src/backend/uxb_backend_web_report_adim14.fbs"
)

$missing = @()
foreach ($f in $required) {
    if (!(Test-Path $f)) { $missing += $f }
}
if ($missing.Count -gt 0) {
    foreach ($m in $missing) { Add-ErrorRow "DOSYA_EKSIK" "adim14" $m "file exists" "missing" "patch dosyasini ayni yola kopyala" }
}
Add-ExpectedActual "required_patch_files" "0 missing" "$($missing.Count) missing" $(if ($missing.Count -eq 0) {"PASS"} else {"FAIL"})

# Build command: do not repair.
$compileOk = $false
$buildLog = Join-Path $current "adim14_compile.log"
$buildBatCandidates = @(
    "compiler/scripts/build_uxb_main_64.bat",
    "build_64.bat",
    "compiler/scripts/build_uxb_main_64.bat"
)
$buildBat = $null
foreach ($b in $buildBatCandidates) { if (Test-Path $b) { $buildBat = $b; break } }

if ($null -ne $buildBat) {
    $env:UXB_FORCE_REBUILD = "1"
    # UXB_FIX: invoke build script through PowerShell call operator to avoid cmd path parsing issues.
    & $buildBat *> $buildLog
    if ($LASTEXITCODE -eq 0) { $compileOk = $true }
    Add-ExpectedActual "compile" "exit 0" "exit $LASTEXITCODE via $buildBat" $(if ($compileOk) {"PASS"} else {"FAIL"})
} else {
    Add-ErrorRow "DERLEME_ARACI_YOK" "build" "compiler/scripts" "build script exists" "missing" "mevcut build script yolunu bu scriptte belirt"
    Add-ExpectedActual "compile" "build script exists" "missing" "FAIL"
}

$compileJson = @{
    ok = $compileOk
    build_script = $buildBat
    log = $buildLog
    no_repair = $true
} | ConvertTo-Json -Depth 5
Write-TextFile (Join-Path $current "adim14_compile.json") $compileJson

# If compile fails, do not run emit tests and do not repair.
if (-not $compileOk) {
    Add-ErrorRow "COMPILE_FAIL" "build" $buildLog "FreeBASIC compile PASS" "FAIL" "tamir yapma; son yamadan sonra ayri analiz et"
} else {
    $exeCandidates = @(
        "build/uxb_main_64.exe",
        "bin/uxb.exe",
        "uxb_main_64.exe",
        "dist/uxb_main_64.exe"
    )
    $exe = $null
    foreach ($e in $exeCandidates) { if (Test-Path $e) { $exe = $e; break } }
    if ($null -eq $exe) {
        Add-ErrorRow "EXE_BULUNAMADI" "runtime" "uxb_main_64.exe" "exe exists after compile" "missing" "build script output yolunu kontrol et"
        Add-ExpectedActual "exe_exists" "exists" "missing" "FAIL"
    } else {
        Add-ExpectedActual "exe_exists" "exists" $exe "PASS"

        # JS smoke.
        $jsOut = "reports/control/current/adim14_program.js"
        & $exe "tests/adim14/positive/adim14_emit_js.bas" "--emit-js" "--js-out" $jsOut *> (Join-Path $current "adim14_emit_js.log")
        $jsExit = $LASTEXITCODE
        $jsExists = Test-Path $jsOut
        Add-ExpectedActual "emit_js" "exit 0 and js exists" "exit $jsExit exists=$jsExists" $(if ($jsExit -eq 0 -and $jsExists) {"PASS"} else {"FAIL"})
        if (!($jsExit -eq 0 -and $jsExists)) { Add-ErrorRow "JS_EMIT_FAIL" "backend_js" $jsOut "js artifact" "missing/fail" "backend JS dispatch/context/output yolunu kontrol et" }

        # WAT smoke.
        $watOut = "reports/control/current/adim14_program.wat"
        & $exe "tests/adim14/positive/adim14_emit_wat.bas" "--emit-wat" "--wat-out" $watOut *> (Join-Path $current "adim14_emit_wat.log")
        $watExit = $LASTEXITCODE
        $watExists = Test-Path $watOut
        Add-ExpectedActual "emit_wat" "exit 0 and wat exists" "exit $watExit exists=$watExists" $(if ($watExit -eq 0 -and $watExists) {"PASS"} else {"FAIL"})
        if (!($watExit -eq 0 -and $watExists)) { Add-ErrorRow "WAT_EMIT_FAIL" "backend_wasm" $watOut "wat artifact" "missing/fail" "WASM backend WAT path/context kontrol et" }

        # Negative: JS AST fallback must fail.
        & $exe "tests/adim14/negative/adim14_emit_js_ast_fallback.bas" "--emit-js" "--codegen-source" "AST" *> (Join-Path $current "adim14_neg_js_ast.log")
        $negJsAstExit = $LASTEXITCODE
        Add-ExpectedActual "negative_js_ast_fallback" "non-zero exit" "exit $negJsAstExit" $(if ($negJsAstExit -ne 0) {"PASS"} else {"FAIL"})
        if ($negJsAstExit -eq 0) { Add-ErrorRow "AST_FALLBACK_GECMIS" "backend_js" "backend gate" "JS AST fallback fail" "passed" "web gate codegenSourceMode=MIR zorunlu yap" }

        # Negative: emit-wasm without WABT should fail if wat2wasm missing.
        $wat2wasm = "tools/wabt/bin/wat2wasm.exe"
        if (!(Test-Path $wat2wasm)) {
            & $exe "tests/adim14/negative/adim14_emit_wasm_no_wabt.bas" "--mode=full" "--emit-wasm" *> (Join-Path $current "adim14_neg_wasm_no_wabt.log")
            $negWasmExit = $LASTEXITCODE
            Add-ExpectedActual "negative_emit_wasm_no_wabt" "non-zero exit when wat2wasm missing" "exit $negWasmExit" $(if ($negWasmExit -ne 0) {"PASS"} else {"FAIL"})
            if ($negWasmExit -eq 0) { Add-ErrorRow "WABT_EKSIK_GIZLENMIS" "backend_wasm" $wat2wasm "emit-wasm fail if tool missing" "passed" "requireWasmBinary gate ekle" }
        } else {
            Add-ExpectedActual "negative_emit_wasm_no_wabt" "skipped because wat2wasm exists" "wat2wasm exists" "SKIP"
        }
    }
}

$expectedActual | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $current "adim14_expected_actual.csv")
$errorRows | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $current "adim14_error_classification.csv")

$failed = @($expectedActual | Where-Object { $_.status -eq "FAIL" })
$ok = ($failed.Count -eq 0 -and $missing.Count -eq 0 -and $compileOk)
$gate = @{
    ok = $ok
    step = "ADIM14_BACKEND_JS_WASM_BROWSER"
    no_repair = $true
    current_archived_to = $historyTarget
    compile_ok = $compileOk
    failed_count = $failed.Count
    error_count = $errorRows.Count
} | ConvertTo-Json -Depth 5
Write-TextFile (Join-Path $current "adim14_backend_web_gate.json") $gate

$md = @()
$md += "# ADIM14 Backend Web Gate"
$md += ""
$md += "- ok: $ok"
$md += "- compile_ok: $compileOk"
$md += "- no_repair: true"
$md += "- failed_count: $($failed.Count)"
$md += "- error_count: $($errorRows.Count)"
$md += ""
$md += "Bu script otomatik tamirat yapmaz. Hata varsa son yamadan sonra ayrı analiz edilecek."
Write-TextFile (Join-Path $current "adim14_backend_web_gate.md") ($md -join "`n")

if ($ok) { exit 0 } else { exit 1 }
