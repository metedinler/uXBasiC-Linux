param(
    [ValidateSet('auto','std','libuv','tbb','full')][string]$Variant='auto',
    [string]$Root='',
    [string]$OutputDirectory='',
    [switch]$SkipPublish
)
$ErrorActionPreference='Stop'

function Find-UxbRoot([string]$start) {
    if ([string]::IsNullOrWhiteSpace($start)) { $start=$PSScriptRoot }
    $p=(Resolve-Path $start).Path
    while ($true) {
        if ((Test-Path (Join-Path $p 'src')) -and (Test-Path (Join-Path $p 'native\uxb_runtime'))) { return $p }
        $parent=Split-Path $p -Parent
        if ($parent -eq $p) { throw 'uXBasic root bulunamadi' }
        $p=$parent
    }
}
function First-Command([string[]]$names) {
    foreach ($n in $names) {
        if ([string]::IsNullOrWhiteSpace($n)) { continue }
        if (Test-Path -LiteralPath $n -PathType Leaf) { return (Resolve-Path -LiteralPath $n).Path }
        $c=Get-Command $n -ErrorAction SilentlyContinue
        if ($c) { return $c.Source }
    }
    return ''
}
function Get-PkgFlags([string]$pkgconf,[string]$name) {
    if ([string]::IsNullOrWhiteSpace($pkgconf)) { return @() }
    & $pkgconf --exists $name 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    $raw=& $pkgconf --cflags --libs $name 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    return (($raw -join ' ') -split '\s+') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
}
function Pe-Machine([string]$path) {
    $b=[IO.File]::ReadAllBytes($path)
    if ($b.Length -lt 256) { return 'invalid' }
    $o=[BitConverter]::ToInt32($b,0x3c)
    $m=[BitConverter]::ToUInt16($b,$o+4)
    if ($m -eq 0x8664) { return 'x64' }
    if ($m -eq 0x14c) { return 'x86' }
    return ('0x{0:X4}' -f $m)
}
function Resolve-LibuvFlags([string]$pkgconf,[string]$mingwRoot) {
    $flags=Get-PkgFlags $pkgconf 'libuv'
    if ($flags.Count -gt 0) { return $flags }
    $header=Join-Path $mingwRoot 'include\uv.h'
    $libdir=Join-Path $mingwRoot 'lib'
    if (!(Test-Path $header)) { return @() }
    foreach ($name in @('libuv.dll.a','libuv-1.dll.a')) {
        $candidate=Join-Path $libdir $name
        if (Test-Path $candidate) { return @("-I$($mingwRoot)\include","-L$libdir",$candidate) }
    }
    return @()
}
function Resolve-TbbFlags([string]$pkgconf,[string]$mingwRoot) {
    $libdir=Join-Path $mingwRoot 'lib'
    $header1=Join-Path $mingwRoot 'include\oneapi\tbb\task_group.h'
    $header2=Join-Path $mingwRoot 'include\tbb\task_group.h'
    $hasHeader=(Test-Path $header1) -or (Test-Path $header2)
    $tbb12=Join-Path $libdir 'libtbb12.dll.a'
    $tbb=Join-Path $libdir 'libtbb.dll.a'
    if ($hasHeader -and (Test-Path $tbb12)) { return @("-I$($mingwRoot)\include","-L$libdir",'-ltbb12') }
    if ($hasHeader -and (Test-Path $tbb)) { return @("-I$($mingwRoot)\include","-L$libdir",'-ltbb') }
    $flags=Get-PkgFlags $pkgconf 'tbb'
    if ($flags.Count -eq 0) { return @() }
    if ((Test-Path $tbb12) -and ($flags -contains '-ltbb')) {
        $flags=@($flags | ForEach-Object { if ($_ -eq '-ltbb') { '-ltbb12' } else { $_ } })
    }
    return $flags
}

$uxb=Find-UxbRoot $Root
$src=Join-Path $uxb 'native\uxb_runtime'
$build=Join-Path $src 'build'
if ($OutputDirectory) { $build=[IO.Path]::GetFullPath($OutputDirectory) }
$reports=Join-Path $uxb 'reports\libraries\logs'
if ($SkipPublish) { $reports=$build }
New-Item -ItemType Directory -Force $build,$reports | Out-Null

$gxx=First-Command @($env:UXB_GXX,$env:CXX,'C:\msys64\ucrt64\bin\x86_64-w64-mingw32-g++.exe','C:\msys64\ucrt64\bin\g++.exe','g++.exe')
if (-not $gxx) { throw 'MSYS2 UCRT64 g++ bulunamadi' }
$gxxBin=Split-Path $gxx -Parent
$mingwRoot=if ($env:UXB_MINGW_ROOT) { (Resolve-Path $env:UXB_MINGW_ROOT).Path } else { Split-Path $gxxBin -Parent }
$pkgconf=First-Command @($env:UXB_PKG_CONFIG,(Join-Path $gxxBin 'pkg-config.exe'),(Join-Path $gxxBin 'pkgconf.exe'),'pkg-config.exe','pkgconf.exe')
$env:PATH=(($gxxBin,(Join-Path $uxb 'bin'),$env:PATH) -join ';')

$uv=Resolve-LibuvFlags $pkgconf $mingwRoot
$tbb=Resolve-TbbFlags $pkgconf $mingwRoot
$useUv=$Variant -in @('auto','libuv','full') -and $uv.Count -gt 0
$useTbb=$Variant -in @('auto','tbb','full') -and $tbb.Count -gt 0
if ($Variant -in @('libuv','full') -and -not $useUv) { throw "libuv gelistirme dosyalari bulunamadi: $mingwRoot" }
if ($Variant -in @('tbb','full') -and -not $useTbb) { throw "oneTBB import library bulunamadi. Beklenen: $mingwRoot\lib\libtbb12.dll.a veya libtbb.dll.a" }

$sources=@(
 'uxb_runtime.cpp','uxb_runtime_mir.cpp','uxb_runtime_state.cpp','uxb_runtime_task.cpp','uxb_runtime_task_v2.cpp','uxb_runtime_sync.cpp','uxb_runtime_shell.cpp',
 'backends\runtime_backend.cpp','backends\std_backend.cpp','backends\libuv_backend.cpp','backends\tbb_backend.cpp'
) | ForEach-Object { Join-Path $src $_ }
$out=Join-Path $build 'uxb_runtime.dll'
$implib=Join-Path $build 'libuxb_runtime.dll.a'
$log=Join-Path $reports ("uxb_runtime_{0}_gxx.log" -f $Variant)
$args=@('-std=gnu++17','-O2','-Wall','-Wextra','-Werror','-DUXB_RT_BUILD_DLL','-shared',"-I$src")
if ($useUv) { $args += '-DUXB_WITH_LIBUV' }
if ($useTbb) { $args += '-DUXB_WITH_TBB' }
$args += $sources
if ($useUv) { $args += $uv }
if ($useTbb) { $args += $tbb }
$args += @('-static-libgcc','-static-libstdc++','-Wl,--enable-auto-import',"-Wl,--out-implib,$implib",'-o',$out)

"GXX=$gxx`r`nMINGW_ROOT=$mingwRoot`r`nPKGCONF=$pkgconf`r`nVARIANT=$Variant`r`nLIBUV=$useUv FLAGS=$($uv -join ' ')`r`nTBB=$useTbb FLAGS=$($tbb -join ' ')`r`nARGS=$($args -join ' ')`r`n" | Set-Content $log -Encoding UTF8
Write-Host "GXX=$gxx"
Write-Host "VARIANT=$Variant LIBUV=$useUv TBB=$useTbb"
$output=@(& $gxx @args 2>&1)
$rc=$LASTEXITCODE
if ($output.Count -gt 0) { $output | Tee-Object -FilePath $log -Append | ForEach-Object { Write-Host $_ } }
if ($rc -ne 0 -or !(Test-Path $out)) { throw "uxb_runtime.dll build failed rc=$rc log=$log" }
if ((Pe-Machine $out) -ne 'x64') { throw 'uxb_runtime.dll x64 degil' }

$variantCopy=Join-Path $build ("uxb_runtime_{0}.dll" -f $Variant)
Copy-Item -Force $out $variantCopy
if ($SkipPublish) {
    foreach ($dep in @('libwinpthread-1.dll','libuv-1.dll','libtbb12.dll','libgcc_s_seh-1.dll','libstdc++-6.dll')) {
        $depSource=Join-Path $gxxBin $dep
        if (Test-Path -LiteralPath $depSource) { Copy-Item -LiteralPath $depSource -Destination (Join-Path $build $dep) -Force }
    }
    @{schema='uxb.runtime_build.v2';status='PASS';variant=$Variant;libuv=$useUv;tbb=$useTbb;dll=$out;machine='x64';published=$false;log=$log} |
        ConvertTo-Json | Set-Content (Join-Path $build 'build_result.json') -Encoding UTF8
    Write-Host "OK: isolated runtime=$out"
    exit 0
}
foreach ($dir in @('dist\runtime_ext','dist\libraries\bin','bin')) {
    $d=Join-Path $uxb $dir
    New-Item -ItemType Directory -Force $d | Out-Null
    Copy-Item -Force $out (Join-Path $d 'uxb_runtime.dll')
}

$runtimeDeps=@('libwinpthread-1.dll')
if ($useUv) { $runtimeDeps += 'libuv-1.dll' }
if ($useTbb) { $runtimeDeps += @('libtbb12.dll','libgcc_s_seh-1.dll','libstdc++-6.dll') }
foreach ($dep in $runtimeDeps) {
    $depSrc=Join-Path $gxxBin $dep
    if (!(Test-Path $depSrc)) { throw "uxb_runtime dependency missing: $depSrc" }
    Copy-Item -Force $depSrc (Join-Path $build $dep)
    foreach ($dir in @('dist\runtime_ext','dist\libraries\bin','bin')) {
        $d=Join-Path $uxb $dir
        New-Item -ItemType Directory -Force $d | Out-Null
        Copy-Item -Force $depSrc (Join-Path $d $dep)
    }
}
$variantDir=Join-Path $uxb 'dist\libraries\variants'
New-Item -ItemType Directory -Force $variantDir | Out-Null
Copy-Item -Force $out (Join-Path $variantDir ("uxb_runtime_{0}.dll" -f $Variant))
$libdir=Join-Path $uxb 'dist\libraries\lib'
New-Item -ItemType Directory -Force $libdir | Out-Null
Copy-Item -Force $implib (Join-Path $libdir 'libuxb_runtime.dll.a')

$deps=@('libgcc_s_seh-1.dll','libstdc++-6.dll','libwinpthread-1.dll')
if ($useUv) { $deps += 'libuv-1.dll' }
if ($useTbb) { $deps += @('libtbb12.dll','libtbbmalloc.dll','libtbbbind_2_5.dll') }
foreach ($dep in $deps | Select-Object -Unique) {
    $s=Join-Path $gxxBin $dep
    if (Test-Path $s) {
        foreach ($dir in @('dist\libraries\deps','bin')) {
            $d=Join-Path $uxb $dir
            New-Item -ItemType Directory -Force $d | Out-Null
            Copy-Item -Force $s (Join-Path $d $dep)
        }
    }
}
$result=@{
    schema='uxb.runtime_build.v2'; status='PASS'; variant=$Variant; libuv=$useUv; tbb=$useTbb;
    dll=$out; variant_copy=$variantCopy; machine='x64'; log=$log; generated_at=(Get-Date).ToString('o')
}
$result | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $build 'build_result.json') -Encoding UTF8
Write-Host "OK: $out"
Write-Host "RUNTIME_COPY: $(Join-Path $uxb 'bin\uxb_runtime.dll')"
Write-Host "VARIANT_COPY: $variantCopy"
