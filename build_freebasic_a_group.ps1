[CmdletBinding()]
param(
 [string]$Root=".",
 [switch]$Clean,
 [switch]$SkipTests,
 [string[]]$Modules=@("uxsystem","uxfs","uxpath","uxprocess","uxlog","uxconfig","uxdatetime","uxuuid")
)
Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$Root=(Resolve-Path -LiteralPath $Root).Path
function Resolve-Fbc {
 if($env:UXB_FBC -and (Test-Path $env:UXB_FBC)){return (Resolve-Path $env:UXB_FBC).Path}
 $c=@(
  (Join-Path $Root "tools\FreeBASIC-1.10.1-win64\fbc64.exe"),
  (Join-Path $Root "tools\FreeBASIC-1.10.1-win64\fbc.exe"),
  "C:\FreeBASIC\fbc64.exe","C:\FreeBASIC\fbc.exe"
 )
 foreach($p in $c){if(Test-Path $p){return (Resolve-Path $p).Path}}
 throw "FreeBASIC compiler bulunamadı. UXB_FBC ayarlayın."
}
$fbc=Resolve-Fbc
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$report=Join-Path $Root "reports\libraries\freebasic_a_group\$stamp"
$build=Join-Path $Root "build\libraries\freebasic_a_group"
$dist=Join-Path $Root "dist\libraries\bin"
$bin=Join-Path $Root "bin"
foreach($d in @($report,$build,$dist,$bin)){New-Item -ItemType Directory -Force -Path $d|Out-Null}
if($Clean){Remove-Item "$build\*" -Recurse -Force -ErrorAction SilentlyContinue}
$results=@()
foreach($m in $Modules){
 $src=Join-Path $Root "runtime_ext\$m\$m.bas"
 if(!(Test-Path $src)){throw "Kaynak yok: $src"}
 $dll=Join-Path $build "$m.dll"
 $args=@("-dll","-w","all","-exx","-g","-i",(Join-Path $Root "runtime_ext\fb_common"),"-x",$dll,$src)
 & $fbc @args 2>&1 | Tee-Object (Join-Path $report "$m.build.log")
 if($LASTEXITCODE -ne 0){throw "$m build FAIL"}
 if(!(Test-Path $dll)){throw "$m.dll üretilmedi"}
 Copy-Item $dll $dist -Force;Copy-Item $dll $bin -Force
 $results += [ordered]@{module=$m;dll=$dll;bytes=(Get-Item $dll).Length;sha256=(Get-FileHash $dll -Algorithm SHA256).Hash.ToLowerInvariant();status="PASS"}
}
$manifest=[ordered]@{schema="uxb.freebasic.a_group.v1";created_at=(Get-Date).ToString("o");fbc=$fbc;modules=$results}
$manifest|ConvertTo-Json -Depth 8|Set-Content (Join-Path $report "manifest.json") -Encoding UTF8
if(!$SkipTests){
 $uxb=Join-Path $Root "bin\uxb.exe";if(!(Test-Path $uxb)){throw "bin\uxb.exe yok"}
 $test=Join-Path $Root "tests\libraries\freebasic_a_group\freebasic_a_group_smoke.uxb"
 & $uxb par $test 2>&1|Tee-Object (Join-Path $report "par.log");if($LASTEXITCODE-ne 0){throw "PAR FAIL"}
 & $uxb int $test 2>&1|Tee-Object (Join-Path $report "ast.log");if($LASTEXITCODE-ne 0){throw "AST FAIL"}
 & $uxb int $test --interpreter-backend MIR 2>&1|Tee-Object (Join-Path $report "mir.log");if($LASTEXITCODE-ne 0){throw "MIR FAIL"}
}
Write-Host "UXB FREEBASIC A GROUP BUILD PASS"
Write-Host "Report: $report"
