[CmdletBinding()]
param(
    [string[]]$EntryPoint = @("src\wrappers\uxb_main_wrapper.bas"),
    [string]$ArchiveRoot = "build\freebasic_c_sources",
    [string]$Fbc = "tools\FreeBASIC-1.10.1-win64\fbc64.exe",
    [switch]$ForceRegenerate
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$fbcPath = (Resolve-Path (Join-Path $root $Fbc)).Path
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archive = Join-Path $root (Join-Path $ArchiveRoot $stamp)
$objectRoot = Join-Path $archive "_objects"
New-Item -ItemType Directory -Force -Path $archive,$objectRoot | Out-Null

function Get-RelativePathCompat([string]$BasePath, [string]$TargetPath) {
    $baseUri = New-Object Uri(($BasePath.TrimEnd("\") + "\"))
    $targetUri = New-Object Uri($TargetPath)
    return [Uri]::UnescapeDataString($baseUri.MakeRelativeUri($targetUri).ToString()).Replace("/","\")
}

$manifest = @()
foreach ($relativeEntry in $EntryPoint) {
    $source = (Resolve-Path (Join-Path $root $relativeEntry)).Path
    $sourceItem = Get-Item -LiteralPath $source
    $generatedC = [IO.Path]::ChangeExtension($source, ".c")
    $hadExistingC = Test-Path -LiteralPath $generatedC
    if ($hadExistingC -and $ForceRegenerate) {
        throw "Guvenlik: -ForceRegenerate var olan C dosyasinin ustune yazamaz: $generatedC"
    }

    $relativeSource = Get-RelativePathCompat $root $source
    $relativeC = [IO.Path]::ChangeExtension($relativeSource, ".c")
    $archiveC = Join-Path $archive $relativeC
    $archiveDir = Split-Path -Parent $archiveC
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
    $object = Join-Path $objectRoot ([IO.Path]::GetFileNameWithoutExtension($source) + ".o")

    if (-not $hadExistingC) {
        Push-Location $sourceItem.DirectoryName
        try {
            & $fbcPath -lang fb -gen gcc -r -c -x $object $sourceItem.Name
            if ($LASTEXITCODE -ne 0) { throw "FreeBASIC C backend basarisiz: $relativeSource exit=$LASTEXITCODE" }
        } finally {
            Pop-Location
        }
    }
    if (-not (Test-Path -LiteralPath $generatedC)) {
        throw "FreeBASIC ara C dosyasi uretilmedi: $generatedC"
    }

    if ($hadExistingC) {
        Copy-Item -LiteralPath $generatedC -Destination $archiveC
    } else {
        Move-Item -LiteralPath $generatedC -Destination $archiveC
    }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archiveC).Hash
    $manifest += [pscustomobject]@{
        source = $relativeSource.Replace("\","/")
        generated_c = $relativeC.Replace("\","/")
        sha256 = $hash
        bytes = (Get-Item -LiteralPath $archiveC).Length
        origin = $(if ($hadExistingC) { "preexisting_generated_c" } else { "generated_now" })
    }
}

$manifestPath = Join-Path $archive "manifest.json"
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
Write-Host "FREEBASIC_C_ARCHIVE_OK $archive"
Write-Host "MANIFEST $manifestPath"
