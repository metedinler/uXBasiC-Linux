param(
    [Parameter(Mandatory = $true)]
    [string]$BackupRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$BackupRoot = (Resolve-Path -LiteralPath $BackupRoot).Path
$recordPath = Join-Path $BackupRoot 'apply_record.json'
if (-not (Test-Path -LiteralPath $recordPath)) {
    throw "Apply record is missing: $recordPath"
}
$record = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
$targetRoot = [string]$record.targetRoot

foreach ($entry in @($record.files)) {
    $destination = Join-Path $targetRoot ([string]$entry.path)
    if ([bool]$entry.existed) {
        $backup = Join-Path $BackupRoot ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $backup)) {
            throw "Backup file is missing: $backup"
        }
        Copy-Item -LiteralPath $backup -Destination $destination -Force
    } elseif (Test-Path -LiteralPath $destination) {
        Remove-Item -LiteralPath $destination -Force
    }
}

Write-Host 'UXB_CODEX_COMPOSITE_PATCH_RESTORED'
