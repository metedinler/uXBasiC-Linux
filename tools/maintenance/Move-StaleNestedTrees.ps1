param([string]$Root=(Resolve-Path (Join-Path $PSScriptRoot "..\..")),[switch]$Apply)
$ErrorActionPreference='Stop'; $Root=(Resolve-Path $Root).Path
$targets=@('runtime_ext\runtime_ext','libsx\libsx')
$found=@($targets | Where-Object { Test-Path (Join-Path $Root $_) })
if ($found.Count -eq 0) { Write-Host 'UXB_NESTED_TREE_CLEAN'; exit 0 }
$found | ForEach-Object { Write-Host "STALE_NESTED_TREE=$_" }
if (-not $Apply) { Write-Host 'DRY_RUN_ONLY: rerun with -Apply to move, never delete.'; exit 0 }
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; $q=Join-Path $Root ("build\quarantine_nested_"+$stamp); New-Item -ItemType Directory -Force -Path $q | Out-Null
foreach($rel in $found){ $src=Join-Path $Root $rel; $dst=Join-Path $q ($rel -replace '[\\/]','__'); Move-Item -LiteralPath $src -Destination $dst }
Write-Host "UXB_NESTED_TREE_MOVED=$q"
