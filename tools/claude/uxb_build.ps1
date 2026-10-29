# uXBasic derleyicisini (FreeBASIC) bin\uxb_<Name>.exe olarak derler.
#   .\tools\claude\uxb_build.ps1 -Name claude1_f2g
# Hedef exe o anda calisiyorsa (baska bir test/oturum kullaniyor) DERLEMEZ: 2026-09-27'de ayni exe'ye iki
# derleme ayni anda yazdi. Cikti: "rc=<kod>" + ilk 15 hata satiri. bin\uxb.exe (Codex'in ana derleyicisi)
# -Name ile hedeflenemez.
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[A-Za-z0-9_]+$')][string]$Name,
    # Kaynak kok (src/wrappers iceren). Bos = bu deponun canli agaci. Ozel calisma kopyasindan
    # derlemek icin (Codex'in canli agac hash dogrulamasini bozmamak icin): -SourceRoot <kopya>. Cikti HEP bu deponun bin\ klasorune yazilir.
    [string]$SourceRoot = ''
)
$ErrorActionPreference = 'Continue'
$uxb = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if ($Name -in @('uxb', 'x64', 'm', 'x64_m')) { "rc=99 -- ana derleyici adlari (uxb/uxb_x64/uxb_m) bu betikle ezilmez"; exit 99 }
$out = Join-Path $uxb "bin\uxb_$Name.exe"
$busy = Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($out)) -ErrorAction SilentlyContinue | Where-Object { $_.Path -and ($_.Path -ieq $out) }
if ($busy) { "rc=98 -- $out su an calisiyor (PID $($busy.Id -join ',')); baska bir ad sec ya da bitmesini bekle"; exit 98 }
$fbcRunning = Get-CimInstance Win32_Process -Filter "Name='fbc64.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*$out*" }
if ($fbcRunning) { "rc=97 -- ayni hedefe baska bir fbc64 derlemesi suruyor (PID $($fbcRunning.ProcessId -join ','))"; exit 97 }

$fb = Join-Path $uxb 'tools\FreeBASIC-1.10.1-win64'
$env:PATH = ((Join-Path $fb 'bin\win64'), (Join-Path $fb 'bin\win32'), 'C:\msys64\ucrt64\bin', $env:PATH) -join ';'
$srcRoot = if ($SourceRoot -ne '') { (Resolve-Path $SourceRoot).Path } else { $uxb }
$src = Join-Path $srcRoot 'src\wrappers\uxb_main_wrapper.bas'
# Frozen historical worktrees can still carry the old layout.
if (!(Test-Path $src)) { $src = Join-Path $srcRoot 'compiler\wrappers\uxb_main_wrapper.bas' }
Push-Location (Split-Path $src -Parent)
# -t 65536: 64 MB ana yigin (S-543). -exx yigin denetimi yalniz bu bayrakla buyuyen ANA is parcacigi yigina uyar;
# bayraksiz derleme 2 MB yiginla MIR'de derinlik ~50, AST'de ~200 civarinda coker (src/common/uxb_stackdepth.fbs).
# Deger bir sinir degildir: S-653 (uxffi.dll gercek adres ile belirteci ayiramiyordu) runtime_ext/uxffi/uxffi.c'de cozuldu;
# S-653 oncesi uxffi.dll ile 128 MB'in ustu VARPTR'li MIR CALL(DLL)'i "stale or invalid pointer handle token" ile dusururdu.
$o = @(& (Join-Path $fb 'fbc64.exe') -lang fb -gen gas64 -w all -exx -mt -t 65536 -O 2 -strip -o ([IO.Path]::ChangeExtension($out,'.o')) -x $out $src 2>&1)
$rc = $LASTEXITCODE
Pop-Location
"rc=$rc  exe=$out"
$o | Where-Object { $_ -match 'error' } | Select-Object -First 15
exit $rc
