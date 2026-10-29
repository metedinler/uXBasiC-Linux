param([switch]$NoRepair)
$ErrorActionPreference='Stop'
function Find-UxbRoot([string]$Start){
  if([string]::IsNullOrWhiteSpace($Start)){ $Start='.' }
  $p=(Resolve-Path $Start).Path
  if([string]::IsNullOrWhiteSpace($p)){ $p=(Get-Location).Path }
  while($true){
    if([string]::IsNullOrWhiteSpace($p)){ throw 'uXBasic root not found (empty path)' }
    if((Test-Path (Join-Path $p 'src\main.bas')) -and (Test-Path (Join-Path $p 'compiler\scripts'))){ return $p }
    if((Test-Path (Join-Path $p 'uxb\src\main.bas')) -and (Test-Path (Join-Path $p 'uxb\compiler\scripts'))){ return (Join-Path $p 'uxb') }
    $q=Split-Path $p -Parent
    if($q -eq $p){ throw 'uXBasic root not found' }
    $p=$q
  }
}
$root=Find-UxbRoot (Get-Location).Path
Set-Location $root
$rotateScript = "compiler\scripts\rotate_current_reports.ps1"
if (Test-Path $rotateScript) {
  powershell -NoProfile -ExecutionPolicy Bypass -File $rotateScript -StepName "adim32b_strict"
}
$env:UXB_FORCE_REBUILD='1'
& cmd /c "compiler\scripts\build_uxb_main_64.bat" *> "reports/control/current/adim32b_build.log"
if($LASTEXITCODE -ne 0){ exit 1 }
$py='python'
$venv=Join-Path (Split-Path $root -Parent) '.venv\Scripts\python.exe'
if(Test-Path $venv){ $py=$venv }
& $py "tools/control/uxb_adim32b_strict_runner.py" --root . --plan "tests/adim32b_strict/expected/adim32b_strict_plan.csv" --out "reports/control/current/adim32b_strict" --exe "bin/uxb.exe"
exit $LASTEXITCODE
