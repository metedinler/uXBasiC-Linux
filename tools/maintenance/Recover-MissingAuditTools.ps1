param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$RagRoot = '',
    [string]$X86Source = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$Root = (Resolve-Path -LiteralPath $Root).Path
if ([string]::IsNullOrWhiteSpace($RagRoot)) { $RagRoot=$env:UXB_RAG_TOOL_ROOT }
if ([string]::IsNullOrWhiteSpace($RagRoot)) { throw 'RagRoot verilmedi. -RagRoot veya UXB_RAG_TOOL_ROOT kullanin.' }
if ([string]::IsNullOrWhiteSpace($X86Source)) { $X86Source=Join-Path $Root '_retired\retired\x86\mir_x86_ffi_contract_gate_adim15.fbs' }
$RagRoot = (Resolve-Path -LiteralPath $RagRoot).Path
$X86Source = (Resolve-Path -LiteralPath $X86Source).Path

$mappings = @(
    @{ Source = 'tools\tests\uxb_all_yama_tests.py'; Destination = 'tools\tests\uxb_all_yama_tests.py' },
    @{ Source = 'tools\tests\uxb_discover_and_run_all_sources.py'; Destination = 'tools\tests\uxb_discover_and_run_all_sources.py' },
    @{ Source = 'tools\release\uxb_release_gate.py'; Destination = 'tools\release\uxb_release_gate.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_collect_parser_nodes.py'; Destination = 'tools\audit\uxb_ast_contract_collect_parser_nodes.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_collect_contract_nodes.py'; Destination = 'tools\audit\uxb_ast_contract_collect_contract_nodes.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_collect_handlers.py'; Destination = 'tools\audit\uxb_ast_contract_collect_handlers.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_build_matrix.py'; Destination = 'tools\audit\uxb_ast_contract_build_matrix.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_fake_status_scan.py'; Destination = 'tools\audit\uxb_ast_contract_fake_status_scan.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_gate.py'; Destination = 'tools\audit\uxb_ast_contract_gate.py' },
    @{ Source = 'tools\audit\uxb_ast_contract_audit.py'; Destination = 'tools\audit\uxb_ast_contract_audit.py' },
    @{ Source = 'tools\audit\uxb_step1_surface_core.py'; Destination = 'tools\audit\uxb_step1_surface_core.py' },
    @{ Source = 'tools\control\uxb_surface_lifecycle_matrix.py'; Destination = 'tools\control\uxb_surface_lifecycle_matrix.py' }
)

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupRoot = Join-Path $Root "build\recovery_backup_audit_tools_$stamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
$records = @()

foreach ($mapping in $mappings) {
    $source = Join-Path $RagRoot $mapping.Source
    $destination = Join-Path $Root $mapping.Destination
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Recovery source is missing: $source"
    }
    $existed = Test-Path -LiteralPath $destination
    if ($existed) {
        $backup = Join-Path $backupRoot $mapping.Destination
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $destination -Destination $backup -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    $records += [pscustomobject]@{
        path = $mapping.Destination
        existed = $existed
        sha256 = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}

$x86Destination = Join-Path $Root 'src\codegen\x86\mir_x86_ffi_contract_gate_adim15.fbs'
if (-not (Test-Path -LiteralPath $X86Source)) {
    throw "x86 FFI recovery source is missing: $X86Source"
}
New-Item -ItemType Directory -Path (Split-Path -Parent $x86Destination) -Force | Out-Null
Copy-Item -LiteralPath $X86Source -Destination $x86Destination -Force
$records += [pscustomobject]@{
    path = 'src\codegen\x86\mir_x86_ffi_contract_gate_adim15.fbs'
    existed = $false
    sha256 = (Get-FileHash -LiteralPath $x86Destination -Algorithm SHA256).Hash.ToLowerInvariant()
}

[ordered]@{
    schema = 'uxb.audit-tool-recovery.v1'
    recoveredAt = (Get-Date).ToString('o')
    ragRoot = $RagRoot
    backupRoot = $backupRoot
    files = $records
} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $backupRoot 'recovery_record.json') -Encoding UTF8

Write-Host 'UXB_MISSING_AUDIT_TOOLS_RECOVERED'
Write-Host "BACKUP=$backupRoot"
