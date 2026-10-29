[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$sources = @(
    @{ Path = (Join-Path $root 'tests\diagnostics\s443_magic_bitwise.uxb'); Expected = @('4','14','6') },
    @{ Path = (Join-Path $root 'tests\diagnostics\s443_magic_object_and.uxb'); Expected = @('4') }
)
$passed = 0
$total = 0
$failed = 0
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_s443_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null

function Check([string]$name, [bool]$ok) {
    $script:total++
    if ($ok) { $script:passed++ } else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

try {
    foreach ($case in $sources) {
        $stem = [IO.Path]::GetFileNameWithoutExtension($case.Path)
        $expectedText = $case.Expected -join "`n"

        $astOut = Join-Path $temp ($stem + '_ast.out')
        & $compiler run $case.Path '--program-output-out' $astOut *> $null
        Check ($stem + ' AST') ($LASTEXITCODE -eq 0 -and (Get-Content $astOut -Raw).Trim() -replace "`r`n", "`n" -eq $expectedText)

        $mirOut = Join-Path $temp ($stem + '_mir.out')
        & $compiler run $case.Path '--interpreter-backend' 'MIR' '--program-output-out' $mirOut *> $null
        Check ($stem + ' MIR') ($LASTEXITCODE -eq 0 -and (Get-Content $mirOut -Raw).Trim() -replace "`r`n", "`n" -eq $expectedText)

        $exe = Join-Path $temp ($stem + '.exe')
        & $compiler bld $case.Path '--build-x64' '--build-x64-out' $exe *> $null
        $nativeOut = Join-Path $temp ($stem + '_native.out')
        if ($LASTEXITCODE -eq 0 -and (Test-Path $exe)) { & $exe *> $nativeOut }
        Check ($stem + ' MIR-x64') ($LASTEXITCODE -eq 0 -and (Test-Path $nativeOut) -and ((Get-Content $nativeOut -Raw).Trim() -replace "`r`n", "`n" -eq $expectedText))

        $js = Join-Path $temp ($stem + '.js')
        & $compiler jsw $case.Path '--js-out' $js *> $null
        $jsOut = Join-Path $temp ($stem + '_js.out')
        if ($LASTEXITCODE -eq 0 -and (Test-Path $js)) { node $js *> $jsOut }
        Check ($stem + ' JS') ($LASTEXITCODE -eq 0 -and (Test-Path $jsOut) -and ((Get-Content $jsOut -Raw).Trim() -replace "`r`n", "`n" -eq $expectedText))
    }
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
