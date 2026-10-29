[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe", [string]$TestRoot = ".\tests\libraries\uxgsl", [string[]]$Only = @())
# uxgsl (GNU Scientific Library koprusu) duman testleri: her program dort motorda (AST, canonical-MIR, native x64, legacy AST-x64)
# calistirilir. Beklenen: programin son PRINT'i olan "<AD>_PASS" satiri. CODEPTR kullanan (geri cagirma) testlerde
# yorumlayicilar (AST/MIR) gercek kod adresi veremez -> NET "requires native x64" hatasi beklenir (S-076); native ve legacy PASS verir.
# Onkosul: bin\uxgsl.dll (+ libgsl-28.dll, libgslcblas-0.dll); derleme bunlari PE import tablosundan bulup cikti klasorune kopyalar.
$ErrorActionPreference = 'Stop'
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
  $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
  if (!$match.Success) { throw 'Cannot find compiler in the model-test wrapper.' }
  $compiler = $match.Groups[1].Value
}
$evidence = Join-Path (Get-Location) ('test_results/libraries_uxgsl/' + [guid]::NewGuid().ToString('N'))
$arguments = @('--uxb',$compiler,'--test-root',(Resolve-Path -LiteralPath $TestRoot).Path,'--output',$evidence,'--temp-builds','--jobs','2')
if ($Only.Count -gt 0) {
  $selected = @(Get-ChildItem -LiteralPath $TestRoot -Filter '*.uxb' -File | Where-Object { $name=$_.BaseName; @($Only | Where-Object { $name -like "*$_*" }).Count -gt 0 } | Select-Object -ExpandProperty BaseName)
  if (!$selected.Count) { throw 'No GSL case matches the requested filter.' }
  $arguments += @('--only') + $selected
}
# Existing six-engine runner checks exits, source/compiler hashes and actual
# output, and owns all temporary products. Callback rejection stays explicit.
& python (Join-Path $PSScriptRoot '../../turkce_ad/run_tests.py') @arguments
$runExit = $LASTEXITCODE
Write-Output "Evidence: $evidence"
exit $runExit
