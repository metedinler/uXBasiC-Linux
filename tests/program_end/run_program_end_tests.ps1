[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe")
# S-156: END semantigi -- dort motorlu karsilastirma task_model kosucusuyla ayni (expected\_engines.txt,
# teste ozel expected\<ad>.engines.txt). Ayrica kosucu yazmamak icin onu bu klasorle cagirir.
& (Join-Path $PSScriptRoot "..\task_model\run_task_model_tests.ps1") -Uxb $Uxb -TestRoot $PSScriptRoot
exit $LASTEXITCODE
