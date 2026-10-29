param([Parameter(Mandatory=$true)][string]$Script, [string[]]$Arguments)
$ErrorActionPreference = "Stop"
$lua = (Get-Command lua.exe -ErrorAction Stop).Source
& $lua $Script @Arguments
exit $LASTEXITCODE
