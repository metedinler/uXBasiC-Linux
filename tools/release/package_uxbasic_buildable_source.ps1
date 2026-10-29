[CmdletBinding()]
param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")),
    [string]$OutputDirectory = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path -LiteralPath $Root).Path
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $Root "dist\release" }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$name = "uxbasic_buildable_source_20260729"
$stageBase = Join-Path $Root "build\source_release_stage"
$stage = Join-Path $stageBase $name
if (Test-Path -LiteralPath $stageBase) {
    $resolved = [System.IO.Path]::GetFullPath($stageBase)
    if (-not $resolved.StartsWith([System.IO.Path]::GetFullPath((Join-Path $Root "build")))) {
        throw "Unsafe source stage path: $resolved"
    }
    Remove-Item -LiteralPath $stageBase -Recurse -Force
}
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$trees = @(
    "src","compiler","include","libsx","runtime","runtime_ext","native",
    "manifests","config","tools","tool_py","tests","examples","docs",
    "vscode-extension","ide"
)
$skipDirectory = '(^|\\)(node_modules|__pycache__|\.pytest_cache|\.git|\.patch_backup|build|dist|obj|chroma|rag_db)(\\|$)'
$skipExtension = @(".exe",".dll",".pdb",".ilk",".exp",".o",".obj",".a",".lib",".zip",".7z",".rar",".pyc",".tmp",".log")

foreach ($tree in $trees) {
    $source = Join-Path $Root $tree
    if (-not (Test-Path -LiteralPath $source)) { continue }
    Get-ChildItem -LiteralPath $source -Recurse -File | ForEach-Object {
        $relativeInTree = $_.FullName.Substring($source.Length).TrimStart('\','/')
        $relative = Join-Path $tree $relativeInTree
        $lower = $relative.ToLowerInvariant()
        if ($lower -match $skipDirectory) { return }
        $isBundledFreeBasic = $lower.StartsWith("tools\freebasic-1.10.1-win64\")
        if (-not $isBundledFreeBasic -and $_.Extension.ToLowerInvariant() -in $skipExtension) { return }
        if ($_.Length -gt 100MB) { return }
        $destination = Join-Path $stage $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
}

# The bundled FreeBASIC directory is a workspace junction. Get-ChildItem does
# not descend into reparse points during the filtered pass, so copy this
# explicitly; it is required for an offline, actually buildable source ZIP.
$freeBasicSource = Join-Path $Root "tools\FreeBASIC-1.10.1-win64"
$freeBasicDestination = Join-Path $stage "tools\FreeBASIC-1.10.1-win64"
if (Test-Path -LiteralPath $freeBasicSource) {
    New-Item -ItemType Directory -Path $freeBasicDestination -Force | Out-Null
    Copy-Item -Path (Join-Path $freeBasicSource "*") -Destination $freeBasicDestination -Recurse -Force
}

foreach ($file in @(
    "build.bat","build_32.bat","build_64.bat","build_release.bat",
    "BUILD_UXB_LIBRARY_SYSTEM.ps1","RUN_UXCLAZZ_UXBDLL_WINDOWS_TESTS.ps1",
    "README.md","README_TR.md","LICENSE","LICENSE.txt"
)) {
    $source = Join-Path $Root $file
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $stage $file) -Force
    }
}

$required = @(
    "src\main_program_entry.fbs","src\wrappers\uxb_main_wrapper.bas",
    "build_64.bat","tools\FreeBASIC-1.10.1-win64\fbc.exe",
    "tools\release\package_uxbasic_buildable_source.ps1",
    "vscode-extension\package.json"
)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $stage $_)) })
if ($missing.Count) { throw "Buildable source package missing: $($missing -join ', ')" }

$manifest = Get-ChildItem -LiteralPath $stage -Recurse -File | Sort-Object FullName | ForEach-Object {
    [ordered]@{
        path = $_.FullName.Substring($stage.Length + 1).Replace('\','/')
        bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
[ordered]@{
    schema = "uxbasic.buildable_source.v1"
    created = (Get-Date).ToString("o")
    fileCount = @($manifest).Count
    files = @($manifest)
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $stage "SHA256SUMS.json") -Encoding UTF8

$zip = Join-Path $OutputDirectory ($name + ".zip")
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Compress-Archive -LiteralPath $stage -DestinationPath $zip -CompressionLevel Optimal

$verify = Join-Path $stageBase "verify"
Expand-Archive -LiteralPath $zip -DestinationPath $verify -Force
foreach ($file in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path (Join-Path $verify $name) $file))) {
        throw "Source ZIP verification missing: $file"
    }
}

[ordered]@{
    schema = "uxbasic.buildable_source.verify.v1"
    status = "PASS"
    zip = $zip
    zipBytes = (Get-Item -LiteralPath $zip).Length
    sha256 = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json | Set-Content -LiteralPath ($zip + ".verify.json") -Encoding UTF8

Write-Host "UXB_BUILDABLE_SOURCE_PACKAGE_PASS"
Write-Host "SOURCE_ZIP=$zip"
