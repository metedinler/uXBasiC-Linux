param([switch]$NoRepair)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference = $false

function Find-Root {
  $p=(Get-Location).Path
  while($true){
    if((Test-Path (Join-Path $p 'uxb\src\main.bas')) -and (Test-Path (Join-Path $p 'build_64.bat'))){ return $p }
    $parent=Split-Path $p -Parent
    if($parent -eq $p){ throw 'Root not found' }
    $p=$parent
  }
}

$root=Find-Root
Set-Location $root
$outDir='uxb\reports\control\current'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$compileLog=Join-Path $outDir 'adim45_compile.log'
$runLog=Join-Path $outDir 'adim45_run.log'
$gateJson=Join-Path $outDir 'adim45_error_system_gate.json'

cmd /c build_64.bat *> $compileLog
$buildExit=$LASTEXITCODE

$exe='uxb\bin\uxb.exe'
if(-not (Test-Path $exe)){
  $exe='uxb\build\uxb_main_64.exe'
}

$errLog='uxb\dist\loglar\adim45_test.hata.log'
$langCsv='uxb\src\error_i18n_template.csv'
$sample='uxb\tests\adim30_10step\positive\01_core_flow.bas'

if(Test-Path $errLog){ Remove-Item $errLog -Force }

$runExit=-1
if($buildExit -ne 0 -and (Test-Path $exe)){
  $compileText = Get-Content $compileLog -Raw -ErrorAction SilentlyContinue
  if($compileText -match 'OK:'){ $buildExit = 0 }
}
if($buildExit -eq 0 -and (Test-Path $exe) -and (Test-Path $sample)){
  $cmd = '"' + $exe + '" --source "' + $sample + '" --error-log-out "' + $errLog + '" --error-language-file "' + $langCsv + '" --error-to-terminal > "' + $runLog + '" 2>&1'
  cmd /c $cmd
  $runExit=$LASTEXITCODE
}

$hasErrLog=Test-Path $errLog
$hasCode=0
if($hasErrLog){
  $t=Get-Content $errLog -Raw -ErrorAction SilentlyContinue
  if($t -match 'E\.[0-9]{4}'){$hasCode=1}
}

$result=[ordered]@{
  step='ADIM45_ERROR_SYSTEM'
  build_exit_code=$buildExit
  run_exit_code=$runExit
  ok=($buildExit -eq 0 -and $hasErrLog -and $hasCode)
  exe_path=$exe
  error_log_path=$errLog
  compile_log='uxb/reports/control/current/adim45_compile.log'
  run_log='uxb/reports/control/current/adim45_run.log'
}

$result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $gateJson
if($result.ok){ exit 0 } else { exit 1 }
