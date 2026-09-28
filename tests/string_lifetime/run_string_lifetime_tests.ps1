[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe")
# S-157: STRING degiskeni / dizi elemani / TYPE ve CLASS alani / yerel donus metni, kendisinden sonraki
# metin islemlerinde ezilmemeli. Dort motorlu karsilastirma task_model kosucusuyla ayni.
& (Join-Path $PSScriptRoot "..\task_model\run_task_model_tests.ps1") -Uxb $Uxb -TestRoot $PSScriptRoot
exit $LASTEXITCODE
