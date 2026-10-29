param([ValidateSet('minimal','core','all')][string]$Set='core',[string[]]$Library=@(),[switch]$FetchDeps,[switch]$Clean,[switch]$StrictAll,[switch]$StrictRuntime,[switch]$BuildCompiler,[switch]$AuditOnly,[switch]$DeployOnly)
& "$PSScriptRoot/compiler/scripts/build_libraries.ps1" -Root $PSScriptRoot -Set $Set -Library $Library -FetchDeps:$FetchDeps -Clean:$Clean -StrictAll:$StrictAll -StrictRuntime:$StrictRuntime -BuildCompiler:$BuildCompiler -AuditOnly:$AuditOnly -DeployOnly:$DeployOnly
exit $LASTEXITCODE
