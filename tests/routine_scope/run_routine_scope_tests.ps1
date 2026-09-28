[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe")
# S-167 (BYREF takma ad) + S-168 (rutin yereli/parametresi globali golgeler): dort motorlu karsilastirma
# task_model kosucusuyla ayni (expected\_engines.txt, teste ozel expected\<ad>.engines.txt).
& (Join-Path $PSScriptRoot "..\task_model\run_task_model_tests.ps1") -Uxb $Uxb -TestRoot $PSScriptRoot
exit $LASTEXITCODE
