param(
    [Parameter(Mandatory = $true)]
    [string]$StageRoot,
    [string]$TargetRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$StageRoot = (Resolve-Path -LiteralPath $StageRoot).Path
$TargetRoot = (Resolve-Path -LiteralPath $TargetRoot).Path
$DeepRoot = Join-Path $StageRoot 'UXB_DEEP_FFI_QUICKJS_WASM_READY_20260726_SINGLE_PACKAGE\UXB_DEEP_FFI_QUICKJS_WASM_READY_20260726'
$ExternalRoot = Join-Path $StageRoot 'UXB_EXTERNAL_LIBRARY_CORE_FIX_20260728_DIRECT_ROOT'

$mappings = @()

# The v131 finalization package owns the overlapping executor/MIR/uxffi files.
# Take only the newer source-front-end and x64 contract work from the 28.07
# package, plus its independent regression tests.
$externalPaths = @(
    'src\parser\parser\parser_stmt_dispatch.fbs',
    'src\semantic\ffi_signature_binding.fbs',
    'src\codegen\x64\ffi_call_backend.fbs',
    'src\codegen\x64\mir_x64_ffi_contract_gate_adim15.fbs',
    'runtime_ext\uxffi\fetch_uxffi_deps_msys2.bat',
    'tests\libraries\ffi_contract\uxb_ffi_contract_test.c',
    'tests\libraries\ffi_contract\ffi_contract_positive.uxb',
    'tests\libraries\ffi_contract\ffi_contract_statement_form.uxb',
    'tests\libraries\ffi_contract\positive_arity10_parse.uxb',
    'tests\libraries\ffi_contract\negative_type_count.uxb',
    'tests\libraries\ffi_contract\negative_arity11.uxb',
    'tests\libraries\ffi_contract\negative_invalid_convention.uxb',
    'tools\tests\run_ffi_contract_fix.ps1',
    'tools\tests\verify_ffi_contract_patch.py'
)
foreach ($relative in $externalPaths) {
    $mappings += [pscustomobject]@{
        Source = Join-Path $ExternalRoot $relative
        Relative = $relative
        Owner = 'external-core-20260728'
    }
}

# QuickJS hardening is orthogonal to the v131 FFI finalization and is absent
# from the current tree even though the basic QuickJS runtime already exists.
$deepOverlayRoots = @(
    (Join-Path $DeepRoot '02_UXJSRT_HARDENING_PATCH\overlay')
    (Join-Path $DeepRoot '03_TESTS_AND_GATES\overlay')
)
$deepPaths = @(
    'libsx\uxjsruntime\uxjsruntime.bas',
    'runtime\js\common\ux_runtime_core.js',
    'runtime\js\quickjs\ux_runtime_quickjs.js',
    'runtime_ext\uxjsruntime\build_uxjsrt.bat',
    'runtime_ext\uxjsruntime\build_uxjsrt.ps1',
    'runtime_ext\uxjsruntime\fetch_quickjs.ps1',
    'runtime_ext\uxjsruntime\quickjs.lock.json',
    'runtime_ext\uxjsruntime\THIRD_PARTY_NOTICE.md',
    'runtime_ext\uxjsruntime\uxjsrt.c',
    'runtime_ext\uxjsruntime\uxjsrt.def',
    'runtime_ext\uxjsruntime\uxjsrt.h',
    'src\codegen\js\js_emitter.fbs',
    'src\codegen\js\js_mir_runtime_emit.fbs',
    'src\codegen\js\runtime\js_runtime_embedded_generated.fbs',
    'src\codegen\js\runtime\js_runtime_writer.fbs',
    'include\modules\uxjsruntime.uxmh',
    'tests\libraries\uxjsruntime\generated_js_e2e.uxb',
    'tests\libraries\uxjsruntime\smoke_hardened.js',
    'tests\native\ffi_contract\test_uxffi_contract.py',
    'tests\native\ffi_contract\uxb_ffi_token_test.c',
    'tests\probes\ffi_bridge_contract_smoke.uxb',
    'tests\probes\ffi_ptr64_probe.uxb',
    'tools\js_runtime\generate_js_runtime_fbs.py',
    'tools\tests\verify_deep_fix_patch.py'
)
foreach ($relative in $deepPaths) {
    $source = $null
    foreach ($overlayRoot in $deepOverlayRoots) {
        $candidate = Join-Path $overlayRoot $relative
        if (Test-Path -LiteralPath $candidate) {
            $source = $candidate
            break
        }
    }
    if (-not $source) {
        throw "Deep overlay file is missing: $relative"
    }
    $mappings += [pscustomobject]@{
        Source = $source
        Relative = $relative
        Owner = 'quickjs-hardening-20260726'
    }
}

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path $TargetRoot "build\patch_backup_composite_$stamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$records = @()

foreach ($mapping in $mappings) {
    if (-not (Test-Path -LiteralPath $mapping.Source)) {
        throw "Patch source is missing: $($mapping.Source)"
    }
    $destination = Join-Path $TargetRoot $mapping.Relative
    $existed = Test-Path -LiteralPath $destination
    $oldHash = $null
    if ($existed) {
        $oldHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        $backup = Join-Path $backupRoot $mapping.Relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $destination -Destination $backup -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $mapping.Source -Destination $destination -Force
    $newHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceHash = (Get-FileHash -LiteralPath $mapping.Source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($newHash -ne $sourceHash) {
        throw "Post-copy hash mismatch: $($mapping.Relative)"
    }
    $records += [pscustomobject]@{
        path = $mapping.Relative
        owner = $mapping.Owner
        existed = $existed
        oldSha256 = $oldHash
        newSha256 = $newHash
    }
}

$record = [ordered]@{
    schema = 'uxb.codex-composite-patch.v1'
    appliedAt = (Get-Date).ToString('o')
    stageRoot = $StageRoot
    targetRoot = $TargetRoot
    backupRoot = $backupRoot
    files = $records
}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backupRoot 'apply_record.json') -Encoding UTF8

Write-Host 'UXB_CODEX_COMPOSITE_PATCH_APPLIED'
Write-Host "BACKUP=$backupRoot"
Write-Host "FILES=$($records.Count)"
