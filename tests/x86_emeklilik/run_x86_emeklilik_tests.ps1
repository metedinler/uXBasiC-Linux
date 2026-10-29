[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')

# S-666 (x86 emeklilik, Asama 3): x86 adi hangi yoldan verilirse verilsin ayni acik emekli iletisi doner.
#   1) CLI: `x86` fiili, --emit-x86, --target-x86, --target x86|win32|windows32|i386|i686 -> CLI_TARGET_RETIRED (tum fiillerde).
#      Eskiden yalniz `x86` fiili reddediliyor, `run --target-x86` sessizce calisiyor, `bld --target x86` sessizce x64 EXE uretiyordu.
#   2) Satir ici makine kodu: INLINE("x86"|"x86_32"|"i386"|"win32",...) -> bld hattinda "x86 (32-bit) INLINE blocks are retired".
#   3) Interop arac zinciri: UXB_TARGET_ARCH=x86... ve INLINE politikasindaki ARCH=x86 -> "retired 32-bit (x86) target".
#   4) (Asama 4) Arac betikleri: uxb_switchboard.ps1 -Mode build-compiler-x86 / -NativeArch x86 ve Resolve-UxbCompilerExe -Arch x86
#      acik emekli hatasi verir; 32 bit fbc ile derleyici kaynagi derlenmeye calisilinca ilk hata uxb_main_wrapper.bas'taki #Error'dur.
# Kontrol (x64) kollari degismeden calisir.
# UXB_TEST_SOURCE_ROOT: (istege bagli) 4. grubun fbc32 sinamasi icin kaynak koku; bos ise depo koku. Aday kaynagi canliya inmeden sinamak icindir.

$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$dir = Join-Path $root 'tests\x86_emeklilik'
$basit = Join-Path $dir 'basit.uxb'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('uxb_x86_emeklilik_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $temp | Out-Null
$oldArch = $env:UXB_TARGET_ARCH
$passed = 0
$total = 0
$failed = 0

function Check([string]$name, [bool]$ok) {
    $script:total++
    if ($ok) { $script:passed++ } else { $script:failed++; Write-Host ('FAIL ' + $name) }
}

function Run([string[]]$arguments) {
    $lines = @(& $compiler @arguments 2>&1)
    return [pscustomobject]@{ Code = $LASTEXITCODE; Text = ($lines | Out-String) }
}

function RunPwsh([string[]]$arguments) {
    $lines = @(& pwsh -NoProfile @arguments 2>&1)
    return [pscustomobject]@{ Code = $LASTEXITCODE; Text = ($lines | Out-String) }
}

function CheckCliRetired([string]$name, [string[]]$arguments) {
    $r = Run $arguments
    Check $name ($r.Code -ne 0 -and $r.Text.Contains('CLI_TARGET_RETIRED') -and $r.Text.Contains('x86 hedefi emekli edildi'))
}

function CheckBldText([string]$name, [string]$file, [string]$needle) {
    $r = Run @('bld', (Join-Path $dir $file), '--out-root', $temp)
    Check $name ($r.Code -ne 0 -and $r.Text.Contains($needle))
}

try {
    # 1) CLI: her yol ayni hatayi verir
    CheckCliRetired 'cli x86 fiili' @('x86', $basit)
    CheckCliRetired 'cli run --emit-x86' @('run', $basit, '--emit-x86')
    CheckCliRetired 'cli run --target-x86' @('run', $basit, '--target-x86')
    CheckCliRetired 'cli run --target x86' @('run', $basit, '--target', 'x86')
    CheckCliRetired 'cli run --target win32' @('run', $basit, '--target', 'win32')
    CheckCliRetired 'cli run --target windows32' @('run', $basit, '--target', 'windows32')
    CheckCliRetired 'cli run --target i386' @('run', $basit, '--target', 'i386')
    CheckCliRetired 'cli run --target i686' @('run', $basit, '--target', 'i686')
    CheckCliRetired 'cli fiilsiz --emit-x86' @($basit, '--emit-x86')
    CheckCliRetired 'cli bld --target x86' @('bld', $basit, '--target', 'x86', '--out-root', $temp)
    $js = Join-Path $temp 'x86.js'
    CheckCliRetired 'cli jsw --target win32' @('jsw', $basit, '--target', 'win32', '--js-out', $js)
    Check 'cli jsw --target win32 dosya yazmaz' (-not (Test-Path -LiteralPath $js))

    $r = Run @('run', $basit)
    Check 'kontrol run basit' ($r.Code -eq 0 -and $r.Text.Contains('42'))
    $r = Run @('run', $basit, '--target', 'x64')
    Check 'kontrol run --target x64' ($r.Code -eq 0 -and $r.Text.Contains('42') -and -not $r.Text.Contains('CLI_TARGET_RETIRED'))

    # 2) Satir ici makine kodu (dogrulama bld hattindadir)
    $inlineRetired = 'x86 (32-bit) INLINE blocks are retired'
    CheckBldText 'inline arch x86' 'inline_x86.uxb' $inlineRetired
    CheckBldText 'inline arch x86_32' 'inline_x86_32.uxb' $inlineRetired
    CheckBldText 'inline arch i386' 'inline_i386.uxb' $inlineRetired
    CheckBldText 'inline arch win32' 'inline_win32.uxb' $inlineRetired
    $r = Run @('bld', (Join-Path $dir 'inline_x64.uxb'), '--out-root', $temp)
    Check 'kontrol inline x64 emekli iletisi vermez' (-not $r.Text.Contains($inlineRetired) -and -not $r.Text.Contains('retired 32-bit'))

    # 3) Interop arac zinciri: UXB_TARGET_ARCH ve INLINE politikasindaki ARCH=
    $archRetired = 'retired 32-bit (x86) target'
    foreach ($v in @('x86', 'X86_32', 'i386', 'i686', 'win32', 'windows32', '32')) {
        $env:UXB_TARGET_ARCH = $v
        $r = Run @('bld', $basit, '--out-root', $temp)
        Check ('env UXB_TARGET_ARCH=' + $v) ($r.Code -ne 0 -and $r.Text.Contains($archRetired))
    }
    $env:UXB_TARGET_ARCH = 'x64'
    $r = Run @('bld', $basit, '--out-root', $temp)
    Check 'kontrol env UXB_TARGET_ARCH=x64' ($r.Code -eq 0 -and -not $r.Text.Contains($archRetired))
    if ($null -eq $oldArch) { Remove-Item Env:UXB_TARGET_ARCH -ErrorAction SilentlyContinue } else { $env:UXB_TARGET_ARCH = $oldArch }
    CheckBldText 'inline politika ARCH=x86' 'inline_arch_politika.uxb' $archRetired

    # 4) Arac betikleri ve 32 bit derleme korumasi
    $switchboard = Join-Path $root 'tool_py\tools\control\uxb_switchboard.ps1'
    $helpers = Join-Path $root 'tool_py\tools\control\workspace_root_helpers.ps1'
    $r = RunPwsh @('-File', $switchboard, '-Mode', 'build-compiler-x86')
    Check 'betik switchboard -Mode build-compiler-x86' ($r.Code -ne 0 -and $r.Text.Contains('x86 (32 bit) emekli edildi'))
    $r = RunPwsh @('-File', $switchboard, '-Mode', 'native-toolchain-auto', '-NativeArch', 'x86', '-Source', $basit)
    Check 'betik switchboard -NativeArch x86' ($r.Code -ne 0 -and $r.Text.Contains('x86 (32 bit) emekli edildi'))
    $r = RunPwsh @('-Command', ". '$helpers'; Resolve-UxbCompilerExe -WorkspaceRoot '$root' -Arch x86")
    Check 'betik Resolve-UxbCompilerExe -Arch x86' ($r.Code -ne 0 -and $r.Text.Contains('main_32.exe') -and $r.Text.Contains('emekli edildi'))
    $r = RunPwsh @('-Command', ". '$helpers'; Resolve-UxbCompilerExe -WorkspaceRoot '$root' -Arch x64")
    Check 'kontrol Resolve-UxbCompilerExe -Arch x64' ($r.Code -eq 0 -and $r.Text.Contains('main_64.exe'))
    Check 'run_ffi_conv3_native_lanes.ps1 ve build_32.bat arsive tasindi' (-not (Test-Path -LiteralPath (Join-Path $root 'build_32.bat')) -and -not (Test-Path -LiteralPath (Join-Path $root 'tools\run_ffi_conv3_native_lanes.ps1')) -and (Test-Path -LiteralPath (Join-Path $root '_retired\x86\build_32.bat')))

    $srcRoot = if ($env:UXB_TEST_SOURCE_ROOT) { $env:UXB_TEST_SOURCE_ROOT } else { $root }
    $fbDir = Join-Path $root 'tools\FreeBASIC-1.10.1-win64'
    $fbc32 = Join-Path $fbDir 'fbc32.exe'
    $wrapper = Join-Path $srcRoot 'src\wrappers\uxb_main_wrapper.bas'
    if ((Test-Path -LiteralPath $fbc32) -and (Test-Path -LiteralPath $wrapper)) {
        $oldPath = $env:PATH
        $env:PATH = (Join-Path $fbDir 'bin\win32') + ';' + (Join-Path $fbDir 'bin\win64') + ';' + $env:PATH
        Push-Location (Split-Path $wrapper -Parent)
        try { $lines = @(& $fbc32 -lang fb -r -o (Join-Path $temp 'x32.asm') $wrapper 2>&1); $code = $LASTEXITCODE } finally { Pop-Location; $env:PATH = $oldPath }
        $text = ($lines | Out-String)
        $first = ($lines | Where-Object { $_ -match 'error' } | Select-Object -First 1)
        Check 'fbc32 derleyici kaynagini derleyemez: ilk hata #Error iletisi' ($code -ne 0 -and ("$first").Contains('32 bit (x86) derleme emekli edildi') -and $text.Contains('uxb_main_wrapper.bas'))
    } else {
        Write-Host 'ATLANDI: fbc32.exe ya da uxb_main_wrapper.bas bulunamadi (32 bit derleme korumasi sinanmadi)'
    }
} finally {
    if ($null -eq $oldArch) { Remove-Item Env:UXB_TARGET_ARCH -ErrorAction SilentlyContinue } else { $env:UXB_TARGET_ARCH = $oldArch }
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}

Write-Output ('Toplam: ' + $total + ' PASS: ' + $passed + ' FAIL: ' + $failed)
if ($failed -gt 0) { exit 1 }
exit 0
