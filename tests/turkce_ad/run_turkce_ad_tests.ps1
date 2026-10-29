[CmdletBinding()]
param([string]$Uxb = '.\bin\uxb.exe')
& python (Join-Path $PSScriptRoot 'run_tests.py') --uxb $Uxb
exit $LASTEXITCODE
