[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$sources = @(
    @{ Path = (Join-Path $root 'tests\diagnostics\s444_uncaught_throw.uxb'); Marker = 'hata' },
    @{ Path = (Join-Path $root 'tests\diagnostics\s444_uncaught_assert.uxb'); Marker = 'bozuk' }
)
$passed = 0
$total = 0
$failed = 0
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s444_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null

function Check([string]$name, [bool]$ok) {
    $script:total++
    if ($ok) { $script:passed++ } else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

try {
    foreach ($case in $sources) {
        $stem = [IO.Path]::GetFileNameWithoutExtension($case.Path)
        $js = Join-Path $temp ($stem + '.js')
        & $compiler jsw $case.Path '--js-out' $js *> $null
        $compileExit = $LASTEXITCODE
        $log = Join-Path $temp ($stem + '.log')
        $nodeExit = 0
        if ($compileExit -eq 0 -and (Test-Path $js)) {
            node $js *> $log
            $nodeExit = $LASTEXITCODE
        }
        $text = if (Test-Path $log) { Get-Content $log -Raw } else { '' }
        Check ($stem + ' compile') ($compileExit -eq 0 -and (Test-Path $js))
        Check ($stem + ' uncaught-error') ($compileExit -eq 0 -and $nodeExit -ne 0 -and $text.Contains('uXBasic runtime error: ' + $case.Marker) -and $text.Contains('once') -and -not $text.Contains('sonra'))
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
