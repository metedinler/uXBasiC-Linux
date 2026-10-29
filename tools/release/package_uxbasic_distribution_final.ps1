[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$GateSummary,
    [string]$OutputDirectory = '',
    [switch]$KeepStage
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$Root=(Resolve-Path -LiteralPath $Root).Path
$GateSummary=(Resolve-Path -LiteralPath $GateSummary).Path
$gate=Get-Content -Raw -LiteralPath $GateSummary | ConvertFrom-Json
if ([string]$gate.status -ne 'PASS') { throw 'Release package refused: final gate is not PASS.' }
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) { $OutputDirectory=Join-Path $Root 'dist\release' }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$name='uxbasic_win64_'+$stamp
$stageBase=Join-Path $Root ('build\release_stage\'+$name)
$stage=Join-Path $stageBase 'uxbasic'
if (Test-Path $stageBase) { Remove-Item -Recurse -Force $stageBase }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Copy-TreeFiltered([string]$Relative) {
    $source=Join-Path $Root $Relative
    if (-not (Test-Path $source)) { return }
    $dest=Join-Path $stage $Relative
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
        $r=$_.FullName.Substring($source.Length).TrimStart('\','/')
        $lower=$r.ToLowerInvariant()
        $leaf=$_.Name.ToLowerInvariant()
        if ($lower -match '(^|\\)(node_modules|__pycache__|\.pytest_cache|build|obj|freebasic-1\.10\.1-win64)(\\|$)') { return }
        if (($Relative -eq 'libsx' -and $lower.StartsWith('libsx\')) -or ($Relative -eq 'manifests' -and $lower.StartsWith('manifests\'))) { return }
        if ($_.Extension.ToLowerInvariant() -in @('.pdb','.ilk','.exp','.o','.obj','.a','.bak','.tmp','.log')) { return }
        if ($leaf -match '^(eski_|\(eskix86\)|old_)' -or $leaf -match '\.pre_.*\.bak$' -or $leaf -match '^uxb\.exe\.pre_') { return }
        $to=Join-Path $dest $r
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $to) | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $to -Force
    }
}
foreach ($dir in @('bin','include','libsx','runtime','manifests','docs','examples','tests','tools','runtime_ext')) { Copy-TreeFiltered $dir }

# IDE and external bridge deliverables are deliberately kept as separate
# installable archives inside the portable compiler distribution.
$vsix=Get-ChildItem -LiteralPath (Join-Path $Root 'dist\vscode') -Filter '*.vsix' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($vsix) {
    New-Item -ItemType Directory -Force -Path (Join-Path $stage 'vscode') | Out-Null
    Copy-Item -LiteralPath $vsix.FullName -Destination (Join-Path $stage ('vscode\'+$vsix.Name)) -Force
}
$pdsxZip=Get-ChildItem -LiteralPath (Join-Path $Root 'dist\pdsx') -Filter '*.zip' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($pdsxZip) {
    New-Item -ItemType Directory -Force -Path (Join-Path $stage 'extras') | Out-Null
    Copy-Item -LiteralPath $pdsxZip.FullName -Destination (Join-Path $stage ('extras\'+$pdsxZip.Name)) -Force
}

# Native library builds are staged under dist/libraries/bin. Runtime DLLs must
# sit next to uxb.exe in the portable package so Windows can resolve transitive
# dependencies without requiring a machine-specific PATH.
$libraryBin=Join-Path $Root 'dist\libraries\bin'
if (Test-Path $libraryBin) {
    Get-ChildItem -LiteralPath $libraryBin -File | Where-Object {
        $_.Extension.ToLowerInvariant() -notin @('.pdb','.ilk','.exp','.o','.obj','.a','.bak','.tmp','.log')
    } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $stage ('bin\'+$_.Name)) -Force
    }
}
foreach ($file in @('README.md','README_TR.md','LICENSE','LICENSE.txt','pck_son(20.07).md')) {
    $src=Join-Path $Root $file; if (Test-Path $src) { Copy-Item $src (Join-Path $stage $file) -Force }
}
$required=@(
    'bin\uxb.exe','bin\uxffi.dll','bin\uxjsrt.dll','bin\uxconfig.dll',
    'bin\uxcapi.dll','bin\uxcabi.dll',
    'bin\uxraylib.dll','bin\libraylib.dll','bin\glfw3.dll',
    'bin\uxsdl3.dll','bin\SDL3.dll',
    'bin\uxterminal.dll','bin\uxlogic.dll','bin\lua54.dll',
    'runtime\js\common\ux_runtime_core.js','runtime\js\quickjs\ux_runtime_quickjs.js',
    'libsx\uxjsruntime\uxjsruntime.bas','libsx\uxraylib\uxraylib.bas',
    'include\modules\uxraylib.uxmh','include\modules\uxterminal.uxmh','include\modules\uxlogic.uxmh',
    'docs\UXB_MULTIMEDIA_WRAPPERS_20260728_TR.md',
    'docs\UXB_DLL_WRAPPER_API_ENVANTERI_20260729.md',
    'docs\UXB_SPRITE_TERMINAL_LUA_PROLOG_FUZZY_20260729_TR.md',
    'docs\UXB_EXE_CLI_DERLEME_KITABI_TR.md',
    'tools\pdsx\uxbasic2pdsxS\run_uxbasic_to_pdsx.ps1',
    'tools\uxclazz\uxclazz.py','tools\uxbdll\uxbdll.py',
    'bin\uxclz.dll','bin\uxscalar_module.dll'
)
$required += @('vscode\uxbasic-workbench-0.3.0.vsix','extras\uxbasic2pdsxS_uxbasic_uyumlu_20260729.zip')
$missing=@($required | Where-Object { -not (Test-Path (Join-Path $stage $_)) })
if ($missing.Count) { throw ('Distribution missing required files: '+($missing -join ', ')) }
function Assert-Pe64([string]$Path) {
    [byte[]]$b=[IO.File]::ReadAllBytes($Path)
    if ($b.Length -lt 256 -or $b[0] -ne 0x4d -or $b[1] -ne 0x5a) { throw "Not PE: $Path" }
    $pe=[BitConverter]::ToInt32($b,0x3c)
    if ($pe -lt 0 -or $pe+26 -ge $b.Length) { throw "Bad PE offset: $Path" }
    $machine=[BitConverter]::ToUInt16($b,$pe+4); $magic=[BitConverter]::ToUInt16($b,$pe+24)
    if ($machine -ne 0x8664 -or $magic -ne 0x20b) { throw "Not x64 PE32+: $Path" }
}
foreach ($pe in @('bin\uxb.exe','bin\uxffi.dll','bin\uxjsrt.dll','bin\uxconfig.dll')) { Assert-Pe64 (Join-Path $stage $pe) }
Copy-Item -LiteralPath $GateSummary -Destination (Join-Path $stage 'FINAL_GATE_SUMMARY.json') -Force
$files=Get-ChildItem -LiteralPath $stage -Recurse -File | Sort-Object FullName
$manifest=@()
foreach ($f in $files) {
    $manifest += [ordered]@{path=$f.FullName.Substring($stage.Length+1).Replace('\','/');bytes=$f.Length;sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash.ToLowerInvariant()}
}
@{schema='uxbasic.win64.release.v1';created=(Get-Date).ToString('o');gateSummary='FINAL_GATE_SUMMARY.json';fileCount=$manifest.Count;files=$manifest} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $stage 'SHA256SUMS.json')
$zip=Join-Path $OutputDirectory ($name+'.zip')
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal
$verify=Join-Path $stageBase 'verify_extract'
Expand-Archive -LiteralPath $zip -DestinationPath $verify -Force
$extracted=Join-Path $verify 'uxbasic'
foreach ($r in $required) { if (-not (Test-Path (Join-Path $extracted $r))) { throw "ZIP verification missing: $r" } }
$helpOut=Join-Path $stageBase 'help.stdout.log'; $helpErr=Join-Path $stageBase 'help.stderr.log'
$p=Start-Process -FilePath (Join-Path $extracted 'bin\uxb.exe') -ArgumentList @('--help') -WorkingDirectory $extracted -PassThru -NoNewWindow -RedirectStandardOutput $helpOut -RedirectStandardError $helpErr
if (-not $p.WaitForExit(60000)) { try{$p.Kill()}catch{}; throw 'Packaged uxb.exe --help timed out' }
if ($p.ExitCode -ne 0) { throw "Packaged uxb.exe --help failed exit=$($p.ExitCode)" }
$verifyJson=Join-Path $OutputDirectory ($name+'.verify.json')
@{schema='uxbasic.win64.release.verify.v1';status='PASS';zip=$zip;zipBytes=(Get-Item $zip).Length;zipSha256=(Get-FileHash -Algorithm SHA256 $zip).Hash.ToLowerInvariant();fileCount=$manifest.Count;helpExit=0} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $verifyJson
if (-not $KeepStage) { Remove-Item -Recurse -Force $stageBase }
Write-Host 'UXB_DISTRIBUTION_PACKAGE_PASS'
Write-Host "RELEASE_ZIP=$zip"
Write-Host "VERIFY_JSON=$verifyJson"
