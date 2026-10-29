param([string]$Compiler = 'bin/uxb_codex2_operators.exe', [switch]$Native)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $root
try {
    $compilerPath = (Resolve-Path $Compiler).Path
    $report = Join-Path $root 'reports/operators_codex2'
    New-Item -ItemType Directory -Force $report | Out-Null
    $results = @()
    foreach ($test in Get-ChildItem $PSScriptRoot -Filter '*.uxb') {
        $expected = (Get-Content -Raw (Join-Path $PSScriptRoot ($test.BaseName + '.expected.txt'))).Replace("`r", '').Trim()
        $modes = @('AST', 'MIR')
        if ($Native) { $modes += @('AST-X64', 'MIR-X64') }
        foreach ($mode in $modes) {
            $label = $test.BaseName + '-' + $mode
            if ($mode.EndsWith('-X64')) {
                $nativeDir = Join-Path $report $label
                New-Item -ItemType Directory -Force $nativeDir | Out-Null
                $exe = Join-Path $nativeDir ($label + '.exe')
                $build = @(& $compilerPath bld $test.FullName --build-x64 --x64-mode ($mode.Split('-')[0]) --build-x64-out $exe --quiet 2>&1)
                $rc = $LASTEXITCODE
                $build | Set-Content (Join-Path $report ($label + '.build.txt'))
                if ($rc -ne 0) { throw "$label build failed ($rc): $build" }
                $stdout = Join-Path $report ($label + '.native.stdout.txt')
                $stderr = Join-Path $report ($label + '.native.stderr.txt')
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/x64_compare/run_with_timeout.ps1 -ExePath $exe -StdoutPath $stdout -StderrPath $stderr -TimeoutMs 10000
                $nativeRc = $LASTEXITCODE
                $output = @((Get-Content -Raw $stdout), (Get-Content -Raw $stderr))
                $LASTEXITCODE = $nativeRc
            } else {
                $output = @(& $compilerPath run $test.FullName --interpreter-backend $mode --quiet 2>&1)
            }
            $rc = $LASTEXITCODE
            $actual = ($output -join "`n").Replace("`r", '').Trim()
            $actual | Set-Content (Join-Path $report ($label + '.stdout.txt'))
            $ok = $rc -eq 0 -and $actual -eq $expected
            $results += [pscustomobject]@{test=$label; pass=$ok; exit=$rc}
            Write-Output "$label PASS=$ok exit=$rc"
        }
    }
    $results | ConvertTo-Json | Set-Content (Join-Path $report 'results.json')
    if (@($results | Where-Object { -not $_.pass }).Count) { throw 'Operator regression failed; inspect reports/operators_codex2' }
} finally { Pop-Location }
