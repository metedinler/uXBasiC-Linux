param(
    [string]$Uxb = 'bin\uxb.exe',
    [string]$Cikti = (Join-Path $env:TEMP 'uxb_tarif_dene')
)
# Kılavuz V2, Bölüm 2.7.2 "Sık kullanılan tarifler" tablosundaki her komutu verilen derleyiciyle çalıştırır ve
# [ad] kod=<çıkış> <süre> <üretilen dosya boyutları> | <ilk üç çıktı satırı> biçiminde özetler.
# İki derleme karşılaştırılırken süre alanı yok sayılmalıdır. Kullanım (proje kökünden):
#   pwsh -File tools\kitap\kilavuz_v2\yoklama\tarif_dene.ps1 -Uxb bin\uxb_kilavuz_20261013_2224.exe
$ErrorActionPreference = 'Continue'
$kok = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$uxb = (Resolve-Path $Uxb).Path
$d = $Cikti
New-Item -ItemType Directory -Force $d | Out-Null
Set-Location $kok
$enc = New-Object System.Text.UTF8Encoding($false)

$k = Join-Path $d 'k.uxb'
[System.IO.File]::WriteAllText($k, "DIM a AS I32`r`na = 6 * 7`r`nPRINT ""merhaba ""; a`r`n", $enc)
$sonsuz = Join-Path $d 'sonsuz.uxb'
[System.IO.File]::WriteAllText($sonsuz, "DIM i AS I64`r`nDO`r`n    i = i + 1`r`nLOOP`r`n", $enc)
$hata = Join-Path $d 'hata.uxb'
[System.IO.File]::WriteAllText($hata, "DIM a AS I32`r`na = `r`nPRINT a`r`n", $enc)

function T([string]$ad, [string[]]$a, [string[]]$dosya = @()) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $out = (& $uxb @a 2>&1 | Out-String)
    $kod = $LASTEXITCODE
    $sw.Stop()
    $dz = foreach ($f in $dosya) { if (Test-Path $f) { "{0}={1}B" -f (Split-Path $f -Leaf), (Get-Item $f).Length } else { "{0}=YOK" -f (Split-Path $f -Leaf) } }
    $ilk = (($out -split "`r?`n" | Where-Object { $_.Trim() -and $_ -notmatch '^INFO' } | Select-Object -First 3) -join ' / ')
    if ($ilk.Length -gt 230) { $ilk = $ilk.Substring(0, 230) }
    "[{0}] kod={1} {2}s {3} | {4}" -f $ad, $kod, [Math]::Round($sw.Elapsed.TotalSeconds, 1), ($dz -join ' '), $ilk
}

$o = Join-Path $d 'out'
T 'run'            @('run', $k, '--out-root', $o)
T 'run MIR'        @('run', $k, '--interpreter-backend', 'MIR', '--out-root', $o)
T 'max-steps AST'  @('run', $sonsuz, '--max-steps', '100000', '--out-root', $o)
T 'max-steps MIR'  @('run', $sonsuz, '--max-steps', '100000', '--interpreter-backend', 'MIR', '--out-root', $o)
$e1 = Join-Path $d 'k.exe'
T 'bld x64'        @('bld', $k, '--build-x64', '--build-x64-out', $e1, '--out-root', $o) @($e1)
if (Test-Path $e1) { "   EXE cikti: " + ((& $e1 2>&1 | Out-String).Trim()) }
$e2 = Join-Path $d 'k_ast.exe'
T 'bld x64 AST'    @('bld', $k, '--build-x64', '--build-x64-out', $e2, '--x64-mode', 'AST', '--out-root', $o) @($e2)
if (Test-Path $e2) { "   EXE(AST) cikti: " + ((& $e2 2>&1 | Out-String).Trim()) }
$asm = Join-Path $d 'k.asm'
T 'x64 nasm'       @('x64', $k, '--emit-x64-nasm', '--emit-x64-nasm-out', $asm, '--out-root', $o) @($asm)
$js = Join-Path $d 'k.js'
T 'jsw'            @('jsw', $k, '--js-out', $js, '--out-root', $o) @($js)
if (Test-Path $js) { "   node: " + ((& node $js 2>&1 | Out-String).Trim()) }
$html = Join-Path $d 'k.html'; $js2 = Join-Path $d 'k2.js'
T 'jsw browser'    @('jsw', $k, '--emit-browser', '--html-out', $html, '--js-out', $js2, '--out-root', $o) @($html, $js2)
$wat = Join-Path $d 'k.wat'
T 'wat'            @('wat', $k, '--emit-wat', '--wat-out', $wat, '--out-root', $o) @($wat)
$wasm = Join-Path $d 'k.wasm'; $wat2 = Join-Path $d 'k2.wat'
T 'wasm'           @('wat', $k, '--emit-wasm', '--wasm-out', $wasm, '--wat-out', $wat2, '--wat2wasm=tools\wabt\bin\wat2wasm.exe', '--out-root', $o) @($wasm, $wat2)
$pre = Join-Path $d 'k_genisletilmis.uxb'
T 'lex pre'        @('lex', $k, '--preprocessed-out', $pre, '--out-root', $o) @($pre)
$tok = Join-Path $d 'tokenler.json'
T 'lex tokens'     @('lex', $k, '--tokens-json-out', $tok, '--out-root', $o) @($tok)
$ast = Join-Path $d 'ast.json'
T 'ast'            @('ast', $k, '--ast-json-out', $ast, '--out-root', $o) @($ast)
$s = Join-Path $d 's.json'; $t = Join-Path $d 't.json'
T 'sem'            @('sem', $k, '--symbol-table-json-out', $s, '--type-table-json-out', $t, '--out-root', $o) @($s, $t)
$mir = Join-Path $d 'mir.json'
T 'mir canon'      @('mir', $k, '--semantic', '--canonical-mir-json-out', $mir, '--out-root', $o) @($mir)
$ops = Join-Path $d 'ops.json'
T 'mir opcodes'    @('mir', $k, '--semantic', '--mir-opcodes-json-out', $ops, '--out-root', $o) @($ops)
$tir = Join-Path $d 'tir.csv'
T 'sem tir'        @('sem', $k, '--type-infer-report-csv-out', $tir, '--out-root', $o) @($tir)
$sure = Join-Path $d 'sure.json'
T 'time-passes'    @('run', $k, '--time-passes', '--layer-timing-json-out', $sure, '--out-root', $o) @($sure)
T 'diag json'      @('run', $hata, '--diag-format', 'json', '--out-root', $o)
T 'quiet'          @('run', $k, '--quiet', '--out-root', $o)
$so = Join-Path $d 'cikti.txt'
T 'stdout-out'     @('run', $k, '--stdout-out', $so, '--out-root', $o) @($so)
$e3 = Join-Path $d 'k_w4.exe'
T 'task-workers'   @('bld', $k, '--build-x64', '--build-x64-out', $e3, '--task-workers', '4', '--out-root', $o) @($e3)
"--- yardim / surum / hatalar ---"
$h = (& $uxb hlp 2>&1 | Out-String); "hlp satir: " + (($h -split "`r?`n").Count)
$v = (& $uxb ver 2>&1 | Out-String); "ver: " + $v.Trim()
T 'bilinmeyen secenek' @('run', $k, '--yok-boyle-secenek')
T 'uzanti .bi'     @('run', (Join-Path $d 'x.bi'))
