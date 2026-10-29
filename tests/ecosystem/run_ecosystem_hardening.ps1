param([string]$Root='')
$ErrorActionPreference='Stop'
if ([string]::IsNullOrWhiteSpace($Root)) { $Root=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
& python (Join-Path $PSScriptRoot 'test_ecosystem_hardening.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& python (Join-Path $Root 'tools\library_tools\uxb_library_source_gate.py') --root $Root
exit $LASTEXITCODE
