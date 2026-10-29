param([Parameter(Mandatory=$true)][string]$Script, [Parameter(Mandatory=$true)][string]$Goal)
$ErrorActionPreference = "Stop"
$candidates = @(
    (Join-Path $env:ProgramFiles "swipl\bin\swipl.exe"),
    (Get-Command swipl.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
)
$swipl = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $swipl) { throw "SWI-Prolog bulunamadi." }
& $swipl -q -s $Script -g $Goal -t halt
exit $LASTEXITCODE
