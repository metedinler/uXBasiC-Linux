param(
    [string]$CompositeBackup = 'build\patch_backup_composite_20260726_222346',
    [string]$PostQuickJsBackup = 'build\patch_backup_post_quickjs_ffi_20260726_222222',
    [string]$NestedTreeQuarantine = 'build\quarantine_nested_20260726_222416',
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = (Resolve-Path -LiteralPath $Root).Path

function Resolve-UnderRoot([string]$PathText) {
    if ([IO.Path]::IsPathRooted($PathText)) {
        return (Resolve-Path -LiteralPath $PathText).Path
    }
    return (Resolve-Path -LiteralPath (Join-Path $Root $PathText)).Path
}

$compositeRoot = Resolve-UnderRoot $CompositeBackup
$postRoot = Resolve-UnderRoot $PostQuickJsBackup
$quarantineRoot = Resolve-UnderRoot $NestedTreeQuarantine

& (Join-Path $PSScriptRoot 'Restore-CodexCompositePatch.ps1') -BackupRoot $compositeRoot
if ($LASTEXITCODE -ne 0) {
    throw "Composite restore failed: $LASTEXITCODE"
}

$postRecordPath = Join-Path $postRoot 'apply_record.json'
$postRecord = Get-Content -LiteralPath $postRecordPath -Raw | ConvertFrom-Json
foreach ($relative in @($postRecord.copiedFiles)) {
    $destination = Join-Path $Root ([string]$relative)
    $backup = Join-Path $postRoot ([string]$relative)
    if (Test-Path -LiteralPath $backup) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $backup -Destination $destination -Force
    } elseif (Test-Path -LiteralPath $destination) {
        Remove-Item -LiteralPath $destination -Force
    }
}

$nestedTrees = @{
    'runtime_ext__runtime_ext' = 'runtime_ext\runtime_ext'
    'libsx__libsx' = 'libsx\libsx'
}
foreach ($entry in $nestedTrees.GetEnumerator()) {
    $source = Join-Path $quarantineRoot $entry.Key
    $destination = Join-Path $Root $entry.Value
    if (Test-Path -LiteralPath $source) {
        if (Test-Path -LiteralPath $destination) {
            throw "Nested-tree restore target already exists: $destination"
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Move-Item -LiteralPath $source -Destination $destination
    }
}

Write-Host 'UXB_CODEX_PATCH_SET_RESTORED'
