param([switch]$Force,[switch]$Release,[switch]$Debug,[string]$OutputPath='',
      [switch]$StageRuntimeOnly,[string[]]$HostLibraries=@('uxgsl.dll','uxraylib.dll','uxsdl3.dll','uxcapi.dll'))
& "$PSScriptRoot/compiler/scripts/build_uxb_main_64.ps1" -Root $PSScriptRoot -Force:$Force -Release:$Release -Debug:$Debug -SkipX86 -OutputPath $OutputPath -StageRuntimeOnly:$StageRuntimeOnly -HostLibraries $HostLibraries
exit $LASTEXITCODE
