param([switch]$NoRepair)
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
function Find-UxbRoot {
  $p=(Get-Location).Path
  while ($true) {
    if ((Test-Path (Join-Path $p "src\main.bas")) -and (Test-Path (Join-Path $p "compiler\scripts"))) { return $p }
    $parent=Split-Path $p -Parent
    if ($parent -eq $p) { throw "uXBasic root not found" }
    $p=$parent
  }
}
$root=Find-UxbRoot
Set-Location $root
New-Item -ItemType Directory -Force -Path "reports\control\current" | Out-Null
$env:UXB_FORCE_REBUILD="1"
$buildLog="reports\control\current\adim35_big_number_build.log"
if (Test-Path "build_64.bat") { cmd /c build_64.bat *> $buildLog }
elseif (Test-Path "compiler\scripts\build_uxb_main_64.bat") { cmd /c compiler\scripts\build_uxb_main_64.bat *> $buildLog }
else { throw "No build script found" }
if ($LASTEXITCODE -ne 0) { throw "Build failed; see $buildLog" }
$wrapperExe = "bin\uxb.exe"
if (-not (Test-Path $wrapperExe)) { throw "Wrapper exe not found: $wrapperExe" }

$results = @()
$tests = Get-ChildItem "tests\adim35_big_number\positive" -Filter "*.bas" -ErrorAction SilentlyContinue
foreach ($t in $tests) {
  $outDir = "reports\control\current\adim35_big_number\$($t.BaseName)"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $log = Join-Path $outDir "run.log"
  $cmdLine = '"' + $wrapperExe + '" mir "' + $t.FullName + '" --emit-ast "' + (Join-Path $outDir "ast.json") + '" --emit-mir "' + (Join-Path $outDir "mir.json") + '" > "' + $log + '" 2>&1'
  cmd /c $cmdLine
  $results += [pscustomobject]@{test=$t.BaseName; kind="positive"; exit=$LASTEXITCODE; result=($(if($LASTEXITCODE -eq 0){"PASS"}else{"FAIL"})); log=$log}
}
$tests = Get-ChildItem "tests\adim35_big_number\negative" -Filter "*.bas" -ErrorAction SilentlyContinue
foreach ($t in $tests) {
  $outDir = "reports\control\current\adim35_big_number\$($t.BaseName)"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $log = Join-Path $outDir "run.log"
  $cmdLine = '"' + $wrapperExe + '" sem "' + $t.FullName + '" > "' + $log + '" 2>&1'
  cmd /c $cmdLine
  $results += [pscustomobject]@{test=$t.BaseName; kind="negative"; exit=$LASTEXITCODE; result=($(if($LASTEXITCODE -ne 0){"PASS"}else{"FAIL"})); log=$log}
}
$csv = "reports\control\current\adim35_big_number_results.csv"
$results | Export-Csv -NoTypeInformation -Encoding UTF8 $csv
$fail = @($results | Where-Object { $_.result -ne "PASS" }).Count
$gate = [ordered]@{step="ADIM35_BIG_NUMBER"; status=($(if($fail -eq 0){"PASS"}else{"FAIL"})); test_count=@($results).Count; fail_count=$fail; result_csv=$csv}
$gate | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "reports\control\current\adim35_big_number_gate.json"
if ($fail -ne 0) { exit 1 } else { exit 0 }
