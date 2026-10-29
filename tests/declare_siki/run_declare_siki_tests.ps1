[CmdletBinding()]
param([string]$Uxb = ".\bin\uxb.exe")
# S-544, Mete 2026-10-28: DECLARE optional, including forward calls.
# Historical neg_ forward-use fixtures now require actual successful output.
# Explicit missing definitions and signature mismatches remain errors.
# Kosucu tests\oop_parity ile ortaktir (ayni biçim); yalniz test koku farklidir.
& (Join-Path $PSScriptRoot "..\oop_parity\run_oop_parity_tests.ps1") -Uxb $Uxb -TestRoot $PSScriptRoot
exit $LASTEXITCODE
