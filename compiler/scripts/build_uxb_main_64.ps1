param(
    [string]$Root = '',
    [switch]$Force,
    [switch]$Release,
    [switch]$Debug,
    [switch]$SkipX86,
    [string]$OutputPath = '',
    [switch]$StageRuntimeOnly,
    [string[]]$HostLibraries = @('uxgsl.dll','uxraylib.dll','uxsdl3.dll','uxcapi.dll')
)
$ErrorActionPreference='Stop'
$HostLibraries = @($HostLibraries | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ } | Select-Object -Unique)
if ($Release -and $Debug) { throw '-Release ve -Debug birlikte kullanilamaz.' }
$releaseMode = -not $Debug
# YAMA: host compiler build is x64-only by default. Set UXB_BUILD_X86=1 to opt in.
if ($env:UXB_BUILD_X86 -ne '1') { $SkipX86 = $true }
function Resolve-UxbRoot([string]$Start) {
    if ([string]::IsNullOrWhiteSpace($Start)) { $Start=$PSScriptRoot }
    $p=(Resolve-Path $Start).Path
    while ($true) {
        if ((Test-Path (Join-Path $p 'src\main.bas')) -and (Test-Path (Join-Path $p 'compiler'))) { return $p }
        if (Test-Path (Join-Path $p 'uxb\src\main.bas')) { return (Join-Path $p 'uxb') }
        $parent=Split-Path $p -Parent; if ($parent -eq $p) { throw "uXBasic root bulunamadi: $Start" }; $p=$parent
    }
}
function Get-PeMachine([string]$Path) {
    $bytes=[IO.File]::ReadAllBytes($Path); $pe=[BitConverter]::ToInt32($bytes,0x3c); $m=[BitConverter]::ToUInt16($bytes,$pe+4)
    if ($m -eq 0x8664) { return 'x64' }; if ($m -eq 0x014c) { return 'x86' }; return ('0x{0:X4}' -f $m)
}
function Invoke-FbcBuild([string]$Fbc,[string]$Source,[string]$Out,[string]$Expected,[string]$Log,[switch]$ReleaseMode) {
    $generator=if($Expected -eq 'x64'){'gas64'}else{'gas'}
    $args=@('-v','-lang','fb','-gen',$generator,'-w','all','-exx','-mt')
    # S-543: yorumlayicilar kullanici ozyinelemesini FreeBASIC ozyinelemesiyle yurutur; 64 MB ana yigin derinlik 1000'i karsilar
    # (src/common/uxb_stackdepth.fbs gercek yigin boyutundan guvenli derinligi hesaplar). Deger bir SINIR degildir, istenen
    # boyut secilebilir: S-653 (uxffi.dll gercek adres ile belirteci ayiramiyordu; yigin buyuyunce heap adresleri belirtec
    # bandina girip "stale or invalid pointer handle token" veriyordu) runtime_ext/uxffi/uxffi.c'de kok nedeninden cozuldu.
    # Not: S-653 oncesi uxffi.dll ile 128 MB'in ustu VARPTR'li MIR CALL(DLL)'i dusurur.
    if ($Expected -eq 'x64') { $args += @('-t','65536') }
    if ($ReleaseMode) { $args += @('-O','2','-strip') } else { $args += '-g' }
    $args += @('-o',[IO.Path]::ChangeExtension($Out,'.o'),'-x',$Out,$Source)
    "FBC=$Fbc`r`nSOURCE=$Source`r`nOUTPUT=$Out`r`nARGS=$($args -join ' ')`r`n" | Set-Content $Log -Encoding UTF8
    $timer=[Diagnostics.Stopwatch]::StartNew()
    Write-Host "FBC_BUILD_START arch=$Expected generator=$generator source=$Source"
    Push-Location (Split-Path $Source -Parent)
    $savedErrorActionPreference=$ErrorActionPreference
    try {
        # fbc/gcc writes warnings to stderr. Capture the complete diagnostic and
        # decide from its exit code instead of aborting the still-running build.
        $ErrorActionPreference='Continue'
        $o=@(& $Fbc @args 2>&1)
        $rc=$LASTEXITCODE
    } finally {
        $ErrorActionPreference=$savedErrorActionPreference
        Pop-Location
    }
    $timer.Stop()
    "ELAPSED_SECONDS=$([Math]::Round($timer.Elapsed.TotalSeconds,3))`r`nEXIT_CODE=$rc" | Add-Content $Log -Encoding UTF8
    Write-Host "FBC_BUILD_END arch=$Expected exit=$rc elapsed_seconds=$([Math]::Round($timer.Elapsed.TotalSeconds,3))"
    if ($o.Count -gt 0) { $o | Tee-Object -FilePath $Log -Append | ForEach-Object { Write-Host $_ } }
    if ($rc -ne 0 -or !(Test-Path $Out)) { throw "FreeBASIC build failed expected=$Expected rc=$rc log=$Log" }
    $arch=Get-PeMachine $Out
    if ($arch -ne $Expected) { throw "Compiler host mimarisi yanlis: expected=$Expected actual=$arch file=$Out" }
}
$uxb=Resolve-UxbRoot $Root
$fb=Join-Path $uxb 'tools\FreeBASIC-1.10.1-win64'
$fbc64=Join-Path $fb 'fbc64.exe'; $fbc32=Join-Path $fb 'fbc32.exe'
if (!(Test-Path $fbc64)) { throw "fbc64.exe bulunamadi: $fbc64" }
if (!$SkipX86 -and !(Test-Path $fbc32)) { throw "fbc32.exe bulunamadi: $fbc32" }
$wrapper=Join-Path $uxb 'src\wrappers\uxb_main_wrapper.bas'; $main=Join-Path $uxb 'src\main.bas'; $source=if(Test-Path $wrapper){$wrapper}else{$main}
if (!(Test-Path $source)) { throw 'Compiler giris kaynagi bulunamadi' }
$build=Join-Path $uxb 'build\compiler'; $bin=Join-Path $uxb 'bin'; $logs=Join-Path $uxb 'reports\libraries\logs'
New-Item -ItemType Directory -Force $build,$bin,$logs | Out-Null
# GCC 16 needs MSYS2 winpthread clock_gettime64; bundled FBC DLL is older.
$env:PATH=('C:\msys64\ucrt64\bin',(Join-Path $fb 'bin\win64'),(Join-Path $fb 'bin\win32'),(Join-Path $uxb 'tools\wabt\bin'),$env:PATH) -join ';'
# Canonical x64 output is bin\uxb.exe; x86 is a host compatibility companion.
$x64=Join-Path $bin 'uxb.exe'
if ($OutputPath) {
    $x64=[IO.Path]::GetFullPath((Join-Path $uxb $OutputPath))
    if (!$x64.StartsWith($uxb + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($x64) -ne '.exe') { throw 'OutputPath must be an EXE within the active repository.' }
    $build=Split-Path $x64 -Parent
    $logs=Join-Path $build 'logs'
    New-Item -ItemType Directory -Force -Path $build | Out-Null
    New-Item -ItemType Directory -Force -Path $logs | Out-Null
    $SkipX86=$true
}
function Copy-InterpreterBridge {
    # A private compiler must also run from a clean CWD. Both interpreters
    # resolve their validated uxffi bridge beside the compiler executable.
    if (!$OutputPath) { return }
    . (Join-Path $uxb 'UXB-Common.ps1')
    $bridge=Join-Path $bin 'uxffi.dll'
    if (!(Test-Path -LiteralPath $bridge)) { throw "Compiler interpreter bridge missing: $bridge" }
    $ffiDeps=@(Get-ChildItem -LiteralPath $bin -Filter 'libffi-*.dll' -File)
    if (!$ffiDeps.Count) { throw "Compiler interpreter bridge dependency missing: $bin/libffi-*.dll" }
    # Dependencies first: never expose the bridge before its closure exists.
    $roots=@($ffiDeps.FullName) + @($bridge)
    foreach ($library in $HostLibraries) {
        if ($library -notmatch '^[A-Za-z0-9_.-]+\.dll$') { throw "HostLibraries requires DLL basenames: $library" }
        $installed=Join-Path $bin $library
        if (!(Test-Path -LiteralPath $installed)) { throw "Selected host library is not installed: $installed" }
        $roots += $installed
    }
    $dumpCandidates=@($env:UXB_OBJDUMP, (Join-Path $fb 'bin/win64/objdump.exe'),
        'C:/msys64/ucrt64/bin/objdump.exe','C:/Program Files/CodeBlocks/MinGW/bin/objdump.exe')
    $dump=@($dumpCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }) | Select-Object -First 1
    if (!$dump) { throw 'PE dependency inspection requires UXB_OBJDUMP or an installed objdump.exe' }
    # Resolve the complete closure before publishing any file. No PATH-dependent
    # selection and no copy of unrelated DLLs from the shared bin directory.
    $closure=@(Get-UxbRuntimeDllClosure -Roots $roots -SourceDirectories @($bin) -Objdump $dump)
    foreach ($entry in $closure) {
        if ((Get-PeMachine $entry.Path) -ne 'x64') { throw "Private x64 host dependency has wrong architecture: $($entry.Path)" }
    }
    $hostDlls=@($closure.Path)
    foreach ($hostDll in $hostDlls) {
        $destination=Join-Path $build ([IO.Path]::GetFileName($hostDll))
        if ([IO.Path]::GetFullPath($hostDll) -ieq [IO.Path]::GetFullPath($destination)) { continue }
        if ((Test-Path -LiteralPath $destination) -and (Get-FileHash -LiteralPath $destination).Hash -eq (Get-FileHash -LiteralPath $hostDll).Hash) { continue }
        Copy-Item -LiteralPath $hostDll -Destination $destination -Force -ErrorAction Stop
    }
    $bridgeManifest=@($hostDlls | ForEach-Object {
        $staged=Get-Item -LiteralPath (Join-Path $build ([IO.Path]::GetFileName($_)))
        @{name=$staged.Name;bytes=$staged.Length;sha256=(Get-FileHash -LiteralPath $staged.FullName).Hash.ToLowerInvariant()}
    })
    @{schema='uxb.compiler_interpreter_runtime.v1';roots=@($roots | ForEach-Object { [IO.Path]::GetFileName($_) });files=$bridgeManifest} | ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath (Join-Path $build 'compiler_interpreter_runtime.json') -Encoding UTF8
}
if ($StageRuntimeOnly) {
    if (!$OutputPath -or !(Test-Path -LiteralPath $x64)) { throw '-StageRuntimeOnly requires an existing private -OutputPath compiler' }
    if ((Get-PeMachine $x64) -ne 'x64') { throw 'Runtime staging requires an x64 compiler' }
    Copy-InterpreterBridge
    Write-Host "COMPILER_RUNTIME_STAGED output=$x64"
    exit 0
}
$x64temp=Join-Path $build 'uxb_x64.new.exe'
if (!$Force -and (Test-Path $x64)) {
    $sourceRoots=@(
        (Join-Path $uxb 'src'),
        (Join-Path $uxb 'src\hooks')
    )
    $newestInput=Get-ChildItem -LiteralPath $sourceRoots -Recurse -File |
        Where-Object { $_.Extension -in @('.bas','.bi','.fbs') } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    $exeItem=Get-Item -LiteralPath $x64
    if ($newestInput -and $exeItem.LastWriteTimeUtc -ge $newestInput.LastWriteTimeUtc) {
        Copy-InterpreterBridge
        Write-Host "COMPILER_UP_TO_DATE output=$x64 newest_input=$($newestInput.FullName)"
        Write-Host 'COMPILER_ARCH=x64'
        exit 0
    }
}
Invoke-FbcBuild $fbc64 $source $x64temp 'x64' (Join-Path $logs 'compiler_x64_fbc.log') -ReleaseMode:$releaseMode
# Do not rename a binary used by another session or deploy redundant copies
# into source folders. A private OutputPath permits concurrent development.
if (Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($x64)) -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -ieq $x64 }) { throw "Compiler target is running: $x64; use -OutputPath." }
Move-Item -LiteralPath $x64temp -Destination $x64 -Force -ErrorAction Stop
Copy-InterpreterBridge
if (!$SkipX86) {
    $x86temp=Join-Path $build 'uxb_x86.new.exe'; $x86=Join-Path $bin 'uxb_x86.exe'
    Invoke-FbcBuild $fbc32 $source $x86temp 'x86' (Join-Path $logs 'compiler_x86_fbc.log') -ReleaseMode:$releaseMode
    Move-Item -Force $x86temp $x86
}
$summary=@{schema='uxb.compiler_hosts.v1';x64=$x64;x64_alias='';x86=if($SkipX86){''}else{'bin/uxb_x86.exe'};target_codegen='x64';generated_at=(Get-Date).ToString('o')}
$summary | ConvertTo-Json | Set-Content (Join-Path $build 'compiler_hosts.json') -Encoding UTF8
Write-Host "OK: x64 compiler=$x64"
if (!$SkipX86) { Write-Host "OK: x86 host=$(Join-Path $bin 'uxb_x86.exe')" }
Write-Host 'COMPILER_ARCH=x64'
exit 0
