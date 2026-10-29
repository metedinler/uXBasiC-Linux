param(
    [Parameter(Mandatory = $true)]
    [string]$PackageRoot,
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = (Resolve-Path -LiteralPath $Root).Path
$PackageRoot = (Resolve-Path -LiteralPath $PackageRoot).Path
$overlay = Join-Path $PackageRoot '01_OVERLAY_TO_UXB_ROOT'

# Only missing release infrastructure and stale v120 test tools are selected.
# Working FFI sources are intentionally not overwritten.
$paths = @(
    'compiler\scripts\run_final_ffi_quickjs_release_gate.ps1',
    'run_final_ffi_quickjs_release.cmd',
    'run_final_ffi_quickjs_release_no_package.cmd',
    'tools\diagnostics\verify_final_ffi_quickjs_release.py',
    'tools\release\package_uxbasic_distribution_final.ps1',
    'tools\tests\run_ffi_contract_fix.ps1',
    'tools\tests\verify_ffi_contract_patch.py'
)

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path $Root "build\patch_backup_final_selective_$stamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$records = @()

foreach ($relative in $paths) {
    $source = Join-Path $overlay $relative
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Final package file is missing: $relative"
    }
    $destination = Join-Path $Root $relative
    $existed = Test-Path -LiteralPath $destination
    if ($existed) {
        $backup = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $destination -Destination $backup -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceHash -ne $destinationHash) {
        throw "Post-copy hash mismatch: $relative"
    }
    $records += [pscustomobject]@{
        path = $relative
        existed = $existed
        sha256 = $destinationHash
    }
}

[ordered]@{
    schema = 'uxb.final-release-selective.v1'
    appliedAt = (Get-Date).ToString('o')
    packageRoot = $PackageRoot
    targetRoot = $Root
    backupRoot = $backupRoot
    files = $records
} | ConvertTo-Json -Depth 6 |
    Set-Content -LiteralPath (Join-Path $backupRoot 'apply_record.json') -Encoding UTF8

Write-Host 'UXB_FINAL_RELEASE_SELECTIVE_APPLY_PASS'
Write-Host "BACKUP=$backupRoot"
