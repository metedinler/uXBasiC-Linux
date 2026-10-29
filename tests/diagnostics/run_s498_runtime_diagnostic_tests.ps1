[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Continue'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$source = Join-Path $root 'tests\diagnostics\s444_uncaught_throw.uxb'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s498_' + [Guid]::NewGuid().ToString('N'))
$total = 0
$passed = 0
$failed = 0
New-Item -ItemType Directory -Force $temp | Out-Null

function Check([string]$name, [bool]$ok, [string]$detail = '') {
    $script:total++
    if ($ok) {
        $script:passed++
        Write-Host ('PASS ' + $name)
    } else {
        $script:failed++
        Write-Host ('FAIL ' + $name)
        if ($detail) { Write-Host ('  ' + $detail) }
    }
}

try {
    foreach ($backend in @('AST', 'MIR')) {
        $all = Join-Path $temp ($backend.ToLowerInvariant() + '_all.json')
        $vscode = Join-Path $temp ($backend.ToLowerInvariant() + '_vscode.json')
        $args = @('run', $source, '--interpreter-backend', $backend, '--all-diagnostics-json-out', $all, '--vscode-diagnostics-json-out', $vscode)
        $lines = @(& $compiler @args 2>&1)
        $exitCode = $LASTEXITCODE
        $allOk = $false
        $vscodeOk = $false
        $detail = ($lines -join ' ')
        if (Test-Path -LiteralPath $all) {
            try {
                $json = Get-Content -LiteralPath $all -Raw | ConvertFrom-Json
                $allOk = $json.count -gt 0 -and $json.error_count -gt 0 -and $json.diagnostics.Count -gt 0
                $detail = 'count=' + $json.count + ' error_count=' + $json.error_count
            } catch { $detail = 'all_diagnostics JSON parse failed: ' + $_.Exception.Message }
        }
        if (Test-Path -LiteralPath $vscode) {
            try {
                $vscodeJson = Get-Content -LiteralPath $vscode -Raw | ConvertFrom-Json
                $vscodeOk = @($vscodeJson).Count -gt 0
            } catch { $detail += ' vscode JSON parse failed: ' + $_.Exception.Message }
        }
        Check ($backend + ' all_diagnostics') ($exitCode -ne 0 -and $allOk) $detail
        Check ($backend + ' vscode_diagnostics') ($exitCode -ne 0 -and $vscodeOk) ('path=' + $vscode)
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
