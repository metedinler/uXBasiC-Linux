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
    foreach ($unit in @('test_library_type_contract', 'test_library_type_lifecycle', 'test_library_payload', 'test_library_type_error_catalog')) {
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
        @{name='library_byval_return'; expected="hello`nHELLO"; lifecycle=$true; clones=$true},
        @{name='library_array_value_copy'; expected="hello`nHELLO"; lifecycle=$true; clones=$true},
        @{name='library_scope_throw_cleanup'; expected="7`ncaught"; lifecycle=$true},
        @{name='library_throw_propagation_cleanup'; expected='caught'; lifecycle=$true},
        @{name='rational_include_manifest_semantic'; expected='3/1'},
        @{name='rational_libtype_source_relative'; expected='12/1'},
        @{name='rational_libtype_package_search'; expected='13/1'},
        @{name='rational_libtype_missing_provider_runtime'; error='library type provider missing'; code='UXB_LIBTYPE_PROVIDER_MISSING'},
        @{name='rational_libtype_unsupported_operation'; error='provider operation unavailable'; code='UXB_LIBTYPE_PROVIDER_OPERATION_UNAVAILABLE'},
        @{name='rational_libtype_missing_mir_capability'; error='provider unavailable for MIR: RATIONAL'; code='UXB_LIBTYPE_PROVIDER_UNAVAILABLE'},
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
            if ($case.code) { $passed = $passed -and $raw.Contains($case.code) }
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
        @{name='AST_X64'; args=@('bld', $managedSource, '--build-x64', '--x64-mode', 'AST'); diagnosticTarget='NATIVE'},
        @{name='MIR_X64'; args=@('bld', $managedSource, '--build-x64', '--x64-mode', 'MIR'); diagnosticTarget='NATIVE'},
        @{name='NATIVE'; args=@('bld', $managedSource, '--build-x64'); diagnosticTarget='NATIVE'},
        @{name='JS'; args=@('jsw', $managedSource)},
        @{name='WAT'; args=@('wat', $managedSource)},
        @{name='WASM'; args=@('wat', $managedSource, '--emit-wasm'); diagnosticTarget='WAT'}
    )
    foreach ($target in $targets) {
        $diagPath = Join-Path $outDir ($target.name + '_diagnostics_' + [Guid]::NewGuid().ToString('N') + '.json')
        $cliArgs = @($target.args) + @('--all-diagnostics-json-out', $diagPath)
        $raw = (@(& $compilerPath @cliArgs 2>&1 | ForEach-Object { "$_" }) -join "`n")
        $code = $LASTEXITCODE
        $diagnosticTarget = if ($target.diagnosticTarget) { $target.diagnosticTarget } else { $target.name }
        $diagnosticCode = ''
        $diagnosticPhase = ''
        $diagnosticMessage = ''
        if (Test-Path -LiteralPath $diagPath) {
            $diagnosticPayload = Get-Content -LiteralPath $diagPath -Raw | ConvertFrom-Json
            $diagnostic = @($diagnosticPayload.diagnostics) | Where-Object { $_.code -eq 'UXB_LIBTYPE_PROVIDER_UNAVAILABLE' } | Select-Object -First 1
            if ($null -ne $diagnostic) {
                $diagnosticCode = $diagnostic.code
                $diagnosticPhase = $diagnostic.phase
                $diagnosticMessage = $diagnostic.message_en
            }
        }
        $passed = $code -ne 0 -and
                  $raw.Contains("library type lifecycle provider unavailable for $diagnosticTarget") -and
                  $diagnosticCode -eq 'UXB_LIBTYPE_PROVIDER_UNAVAILABLE' -and
                  $diagnosticPhase -eq 'target_validation' -and
                  $diagnosticMessage.Contains($diagnosticTarget)
        $results += [pscustomobject]@{name="managed_target_$($target.name)"; passed=$passed; exit_code=$code; output=$raw; diagnostic_code=$diagnosticCode; diagnostic_phase=$diagnosticPhase; diagnostic_message=$diagnosticMessage}
    }
    $mirDiagPath = Join-Path $outDir ('MIR_diagnostics_' + [Guid]::NewGuid().ToString('N') + '.json')
    $mirArgs = @('run', $managedSource, '--interpreter-backend', 'MIR', '--all-diagnostics-json-out', $mirDiagPath)
    $mirOutputLines = @(& $compilerPath @mirArgs 2>&1 | ForEach-Object { "$_" })
    $mirCode = $LASTEXITCODE
    $mirActual = (($mirOutputLines | Where-Object { $_ -notmatch '^INFO:' -and $_.Trim() -ne '' }) -join "`n").Trim()
    $mirExpected = "HELLO`nhello`nHELLO"
    $mirDiagClean = $true
    if (Test-Path -LiteralPath $mirDiagPath) {
        $mirPayload = Get-Content -LiteralPath $mirDiagPath -Raw | ConvertFrom-Json
        $mirDiagClean = @($mirPayload.diagnostics) | Where-Object { $_.code -like 'UXB_LIBTYPE_PROVIDER_*' } | Measure-Object | Select-Object -ExpandProperty Count
        $mirDiagClean = $mirDiagClean -eq 0
    }
    $mirPassed = $mirCode -eq 0 -and $mirActual -ceq $mirExpected -and $mirDiagClean
    $results += [pscustomobject]@{name='managed_target_MIR'; passed=$mirPassed; exit_code=$mirCode; output=($mirOutputLines -join "`n"); diagnostic_code=''; diagnostic_phase=''; diagnostic_message='provider supported; no provider error expected'}

    $mirStructuralCases = @(
        @{name='b3_owned_transfer'; source='library_owned_value.uxb'; required=@('TEXT_VALUE.CLONE'); forbidden=@('TEXT_VALUE.COPY')},
        @{name='b3_shared_transfer'; source='library_shared_value.uxb'; required=@('TEXT_REF.RETAIN','TEXT_REF.CLONE'); forbidden=@()},
        @{name='b3_return_drop'; source='library_byval_return.uxb'; required=@('TEXT_VALUE.CLONE','TEXT_VALUE.DROP'); forbidden=@()},
        @{name='b3_throw_propagation_drop'; source='library_throw_propagation_cleanup.uxb'; required=@('TEXT_VALUE.DROP'); forbidden=@()}
    )
    foreach ($structuralCase in $mirStructuralCases) {
        $mirPath = Join-Path $outDir ($structuralCase.name + '_' + [Guid]::NewGuid().ToString('N') + '.json')
        $mirOutput = @(& $compilerPath mir (Join-Path $PSScriptRoot $structuralCase.source) --dump-mir --mir-full-json-out $mirPath 2>&1 | ForEach-Object { "$($_)" })
        $mirCode = $LASTEXITCODE
        $callNames = @()
        if (Test-Path -LiteralPath $mirPath) {
            $mirPayload = Get-Content -LiteralPath $mirPath -Raw | ConvertFrom-Json
            foreach ($fn in @($mirPayload.module.functions)) {
                foreach ($block in @($fn.blocks)) {
                    foreach ($instruction in @($block.instructions)) {
                        if ($instruction.opcode -eq 'CALL' -and $instruction.operands.Count -gt 0) {
                            $callNames += [string]$instruction.operands[0]
                        }
                    }
                }
            }
        }
        $passed = $mirCode -eq 0
        foreach ($requiredName in $structuralCase.required) { $passed = $passed -and ($callNames -contains $requiredName) }
        foreach ($forbiddenName in $structuralCase.forbidden) { $passed = $passed -and (-not ($callNames -contains $forbiddenName)) }
        $results += [pscustomobject]@{name=$structuralCase.name; passed=$passed; exit_code=$mirCode; output=(($mirOutput + ($callNames -join ', ')) -join "`n"); diagnostic_code=''; diagnostic_phase='canonical_mir'; diagnostic_message='lifecycle lowering structure'}
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
