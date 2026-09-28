param(
    [Alias('Uxb')][string]$Compiler = 'bin/uxb.exe',
    [string]$ReportPath = 'reports/library_type_contract/results.json'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $root
try {
    $compilerPath = (Resolve-Path $Compiler).Path
    $fbc = Join-Path $root 'tools/FreeBASIC-1.10.1-win64/fbc64.exe'
    $results = @()
    $outDir = Join-Path $root 'tmp/library_type_contract'
    [void](New-Item -ItemType Directory -Force $outDir)
    foreach ($unit in @('test_library_type_contract', 'test_library_type_lifecycle', 'test_library_payload')) {
        $exe = Join-Path $outDir ($unit + '.exe')
        & $fbc -lang fb -exx -x $exe (Join-Path $PSScriptRoot ($unit + '.bas'))
        if ($LASTEXITCODE -ne 0) { throw "Unit build failed: $unit" }
        $output = @(& $exe 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
        $passed = $code -eq 0 -and (($output -join "`n") -match '^PASS ')
        $results += [pscustomobject]@{name=$unit; passed=$passed; exit_code=$code; output=($output -join "`n")}
    }
    $cases = @(
        @{name='library_owned_value'; expected="hello`nhello`nhello`nHELLO`nhello`nhello`nhello`nhello"; lifecycle=$true; clones=$true},
        @{name='library_shared_value'; expected="HELLO`nhello`nHELLO"; lifecycle=$true; clones=$true},
        @{name='library_owned_error'; error='division by zero'; lifecycle=$true; clones=$true},
        @{name='library_owned_limit'; error='step limit'; lifecycle=$true; clones=$true; steps=100},
        @{name='neg_owned_arity'; error='expects one operand'; semantic=$true},
        @{name='neg_owned_operand'; error='operand mismatch'; semantic=$true},
        @{name='neg_owned_member'; error='member not declared'; semantic=$true},
        @{name='manifest_type_declaration'; expected='MANIFEST_TYPE_OK'},
        @{name='neg_manifest_type_typo'; error='unknown type: MEASURE_TYPO'; semantic=$true},
        @{name='rational_value_transfer'; expected="3/1`n3/1`n4/1`n3/1`n4/1`n9/1"},
        @{name='rational_fraction_transfer'; expected="3/2`n3/2`n0/1`n5/1`n3/2`n0/1`n0/1"},
        @{name='rational_mir_add_value'; expected='3/1'},
        @{name='rational_mir_ops_value'; expected="2/1`n24/1`n3/2"},
        @{name='rational_mir_compare_value'; expected="EQ`nGT"},
        @{name='rational_lifecycle'; expected="3/1`n3/1`n3/1"},
        @{name='library_type_field_copy'; expected="hello`nhello`nhello"; lifecycle=$true; clones=$true},
        @{name='rational_include_manifest_semantic'; expected='3/1'},
        @{name='rational_libtype_source_relative'; expected='12/1'},
        @{name='rational_libtype_package_search'; expected='13/1'},
        @{name='rational_libtype_missing_provider_runtime'; error='library type provider missing'},
        @{name='rational_libtype_missing_manifest'; error='manifest not found'; semantic=$true},
        @{name='rational_libtype_bad_extension'; error='LIBTYPE: unsafe or unsupported manifest path'; semantic=$true},
        @{name='neg_dynamic_payload_lifecycle'; error='lifecycle lowering unavailable: DYNAMIC_PAYLOAD'; semantic=$true}
    )
    foreach ($case in $cases) {
        $source = Join-Path $PSScriptRoot ($case.name + '.uxb')
        $steps = if ($case.steps) { $case.steps } else { 20000 }
        $cliArgs = @('run', $source, '--interpreter-backend', 'MIR', '--max-steps', $steps)
        if ($case.semantic) { $cliArgs = @('sem', $source) }
        $statsPath = Join-Path $outDir ($case.name + '_' + [Guid]::NewGuid().ToString('N') + '.json')
        if ($case.lifecycle) { $cliArgs += @('--mir-exec-result-json-out', $statsPath) }
        $output = @(& $compilerPath @cliArgs 2>&1 | ForEach-Object { "$_" })
        $code = $LASTEXITCODE
        $raw = $output -join "`n"
        $actual = (($output | Where-Object { $_ -notmatch '^INFO:' -and $_.Trim() -ne '' }) -join "`n").Trim()
        if ($case.error) {
            $passed = $code -ne 0 -and $raw.Contains($case.error)
        } else {
            $passed = $code -eq 0 -and $actual -ceq $case.expected
        }
        $stats = $null
        if ($case.lifecycle) {
            if (Test-Path -LiteralPath $statsPath) {
                $artifact = Get-Content -LiteralPath $statsPath -Raw | ConvertFrom-Json
                $stats = $artifact.library_type_lifecycle
            }
            $passed = $passed -and $null -ne $stats -and $stats.live -eq 0 -and $stats.allocations -gt 0 -and $stats.allocations -eq $stats.drops
            if ($case.clones) { $passed = $passed -and $stats.clones -gt 0 }
        }
        $results += [pscustomobject]@{name=$case.name; passed=$passed; exit_code=$code; output=$raw; lifecycle=$stats}
    }
    $managedSource = Join-Path $PSScriptRoot 'library_shared_value.uxb'
    $targets = @(
        @{name='AST'; args=@('run', $managedSource, '--interpreter-backend', 'AST')},
        @{name='NATIVE'; args=@('bld', $managedSource, '--build-x64')},
        @{name='JS'; args=@('jsw', $managedSource)},
        @{name='WAT'; args=@('wat', $managedSource)},
        @{name='WASM'; args=@('wat', $managedSource, '--emit-wasm'); diagnosticTarget='WAT'}
    )
    foreach ($target in $targets) {
        $cliArgs = $target.args
        $raw = (@(& $compilerPath @cliArgs 2>&1 | ForEach-Object { "$_" }) -join "`n")
        $code = $LASTEXITCODE
        $diagnosticTarget = if ($target.diagnosticTarget) { $target.diagnosticTarget } else { $target.name }
        $passed = $code -ne 0 -and $raw.Contains("library type lifecycle provider unavailable for $diagnosticTarget")
        $results += [pscustomobject]@{name="managed_target_$($target.name)"; passed=$passed; exit_code=$code; output=$raw}
    }
    $reportFile = [IO.Path]::GetFullPath((Join-Path $root $ReportPath))
    [void](New-Item -ItemType Directory -Force (Split-Path $reportFile -Parent))
    [pscustomobject]@{
        schema='uxb.library_type.tests.v1'
        compiler=$compilerPath
        compiler_sha256=(Get-FileHash $compilerPath -Algorithm SHA256).Hash
        results=$results
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportFile -Encoding UTF8
    foreach ($result in $results) {
        $status = if ($result.passed) { 'PASS' } else { 'FAIL' }
        Write-Host "$status $($result.name)"
        if (-not $result.passed) { Write-Host $result.output; Write-Host ($result.lifecycle | ConvertTo-Json -Compress) }
    }
    $failed = @($results | Where-Object { -not $_.passed }).Count
    Write-Host "Toplam: $($results.Count) PASS: $($results.Count - $failed) FAIL: $failed"
    if ($failed -gt 0) { exit 1 }
    Write-Host "PASS library_type_contract suite $($results.Count)/$($results.Count)"
} finally {
    Pop-Location
}
