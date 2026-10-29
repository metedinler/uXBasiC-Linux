# Bir uXBasic programini AST, canonical-MIR ve native x64 (bld) motorlarinda calistirir, ciktilari tek satirda
# yan yana verir. -Legacy ile eski AST-x64 motoru da eklenir.
#   .\tools\claude\uxb_run3.ps1 -File build\deneme.bas -Uxb .\bin\uxb_claude1_f2f.exe [-NativeRepeat 3] [-Workers 2] [-Legacy]
# Satirlar " | " ile birlestirilir; INFO/WARN satirlari atilir. Native derleme klasoru %TEMP% altinda acilir ve silinir.
param(
    [Parameter(Mandatory = $true)][string]$File,
    [string]$Uxb = '.\bin\uxb.exe',
    [int]$NativeRepeat = 1,
    [string]$Workers = '',
    [switch]$Legacy
)
$ErrorActionPreference = 'Continue'
function Clean([object[]]$lines) { (($lines | Where-Object { $_ -notmatch '^(INFO|WARN)' }) -join ' | ') }

foreach ($eng in 'AST', 'MIR') {
    $a = @('run', $File)
    if ($eng -eq 'MIR') { $a += @('--interpreter-backend', 'MIR') }
    "{0,-7}: {1}" -f $eng, (Clean (& $Uxb @a 2>&1))
}

$modes = @(@{ Name = 'x64'; Extra = @() })
if ($Legacy) { $modes += @{ Name = 'AST-x64'; Extra = @('--x64-mode', 'AST') } }
$uxbDir = Split-Path (Resolve-Path $Uxb)
foreach ($m in $modes) {
    $tmp = Join-Path $env:TEMP ('uxb_run3_' + [IO.Path]::GetFileNameWithoutExtension($File) + '_' + $m.Name + '_' + $PID)
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $b = Clean (& $Uxb bld $File @($m.Extra) --out-root $tmp 2>&1)
    $exe = Get-ChildItem $tmp -Recurse -Filter program.exe | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $exe) {
        "{0,-7}: BUILDFAIL {1}" -f $m.Name, $b
    } else {
        foreach ($dll in 'uxb_runtime.dll', 'uxraylib.dll', 'libraylib.dll', 'glfw3.dll', 'uxsdl3.dll', 'SDL3.dll') {
            $p = Join-Path $uxbDir $dll
            if (Test-Path $p) { Copy-Item $p $exe.DirectoryName -Force }
        }
        if ($Workers -ne '') { $env:UXB_TASK_WORKERS = $Workers }
        $res = foreach ($i in 1..$NativeRepeat) { "$(Clean (& $exe.FullName 2>&1)) [rc=$LASTEXITCODE]" }
        if ($Workers -ne '') { Remove-Item Env:UXB_TASK_WORKERS }
        "{0,-7}: {1}" -f $m.Name, (($res | Group-Object | ForEach-Object { if ($_.Count -gt 1) { "$($_.Name) x$($_.Count)" } else { $_.Name } }) -join ' ;; ')
    }
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
