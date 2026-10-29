param(
    [Alias('Uxb')][string]$Compiler = 'bin/uxb.exe'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $root
try {
    $compilerPath = (Resolve-Path $Compiler).Path
    $source = Join-Path $root 'tests/library_type_contract/rational_mir_ops_value.uxb'
    $outDir = Join-Path $root 'tmp/s499_libtype_target_gate'
    [void](New-Item -ItemType Directory -Force $outDir)
    $results = @()

    $targets = @(
        @{name='MIR'; args=@('run', $source, '--interpreter-backend', 'MIR'); expected="2/1`n24/1`n3/2"; success=$true},
        @{name='AST'; args=@('run', $source, '--interpreter-backend', 'AST'); diagnosticTarget='AST'},
        @{name='AST_X64'; args=@('bld', $source, '--build-x64', '--x64-mode', 'AST'); diagnosticTarget='NATIVE'},
        @{name='MIR_X64'; args=@('bld', $source, '--build-x64', '--x64-mode', 'MIR'); diagnosticTarget='NATIVE'},
        @{name='NATIVE'; args=@('bld', $source, '--build-x64'); diagnosticTarget='NATIVE'},
        @{name='JS'; args=@('jsw', $source); diagnosticTarget='JS'},
        @{name='WAT'; args=@('wat', $source); diagnosticTarget='WAT'},
        @{name='WASM'; args=@('wat', $source, '--emit-wasm'); diagnosticTarget='WAT'}
    )

    foreach ($target in $targets) {
        $diagPath = Join-Path $outDir ($target.name + '_' + [Guid]::NewGuid().ToString('N') + '.json')
        $output = @(& $compilerPath @($target.args) '--all-diagnostics-json-out' $diagPath 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
        $raw = $output -join "`n"
        $passed = $false
        $diagnosticCode = ''
        $diagnosticPhase = ''
        $diagnosticMessage = ''

        if ($target.success) {
            $actual = (($output | Where-Object { $_ -notmatch '^INFO:' -and $_.Trim() -ne '' }) -join "`n").Trim()
            $passed = $code -eq 0 -and $actual -ceq $target.expected
        } else {
            if (Test-Path -LiteralPath $diagPath) {
                $payload = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
                $diagnostic = @($payload.diagnostics) | Where-Object { $_.code -eq 'UXB_LIBTYPE_PROVIDER_UNAVAILABLE' } | Select-Object -First 1
                if ($null -ne $diagnostic) {
                    $diagnosticCode = $diagnostic.code
                    $diagnosticPhase = $diagnostic.phase
                    $diagnosticMessage = $diagnostic.message_en
                }
            }
            $targetName = $target.diagnosticTarget
            $passed = $code -ne 0 -and
                      $raw.Contains("UXB_LIBTYPE_PROVIDER_UNAVAILABLE: library type provider unavailable for ${targetName}: RATIONAL") -and
                      $diagnosticCode -eq 'UXB_LIBTYPE_PROVIDER_UNAVAILABLE' -and
                      $diagnosticPhase -eq 'target_validation' -and
                      $diagnosticMessage.Contains($targetName)
        }
        $results += [pscustomobject]@{
            name = $target.name
            passed = $passed
            exit_code = $code
            diagnostic_code = $diagnosticCode
            diagnostic_phase = $diagnosticPhase
            output = $raw
        }
    }

    foreach ($result in $results) {
        $status = if ($result.passed) { 'PASS' } else { 'FAIL' }
        Write-Host "$status $($result.name)"
        if (-not $result.passed) { Write-Host $result.output }
    }
    $failed = @($results | Where-Object { -not $_.passed }).Count
    Write-Host "Toplam: $($results.Count) PASS: $($results.Count - $failed) FAIL: $failed"
    if ($failed -gt 0) { exit 1 }
} finally {
    Pop-Location
}
exit 0
