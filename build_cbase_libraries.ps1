[CmdletBinding()]
param(
    [string]$Root = ".",
    [switch]$InstallDeps,
    [switch]$FetchDeps,
    [switch]$Clean,
    [switch]$RunTests,
    [string[]]$Modules = @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Batch/terminal çağrılarında -Modules uxsqlite,uxjson biçimini de kabul et.
$Modules = @(
    $Modules |
    ForEach-Object { $_ -split "[,;]" } |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ } |
    Select-Object -Unique
)

function Resolve-Tool {
    param(
        [string]$EnvironmentName,
        [string[]]$Candidates
    )
    $envValue = [Environment]::GetEnvironmentVariable($EnvironmentName)
    if ($envValue -and (Test-Path -LiteralPath $envValue)) {
        return (Resolve-Path -LiteralPath $envValue).Path
    }
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Araç bulunamadı: $EnvironmentName"
}

function Ensure-Directory([string]$Path) {
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function Get-PkgFlags {
    param([string[]]$Packages)
    $text = & $script:PkgConfig --cflags --libs @Packages
    if ($LASTEXITCODE -ne 0) {
        throw "pkg-config başarısız: $($Packages -join ', ')"
    }
    return @($text -split "\s+" | Where-Object { $_ })
}

function Invoke-GccBuild {
    param(
        [string]$Name,
        [string[]]$Sources,
        [string[]]$PkgModules = @(),
        [string[]]$ExtraArgs = @()
    )

    $dll = Join-Path $script:BuildBin "$Name.dll"
    $implib = Join-Path $script:BuildLib "lib$Name.dll.a"
    $args = @(
        "-std=c11", "-O2", "-Wall", "-Wextra",
        "-Werror=implicit-function-declaration",
        "-shared", "-static-libgcc",
        "-I$script:CommonInclude"
    )

    $args += $Sources
    if ($PkgModules.Count) {
        $args += Get-PkgFlags -Packages $PkgModules
    }
    $args += $ExtraArgs
    $args += @(
        "-Wl,--out-implib,$implib",
        "-o", $dll
    )

    Write-Host "BUILD $Name"
    & $script:Gcc @args 2>&1 | Tee-Object -FilePath (
        Join-Path $script:Session "$Name.build.log"
    )
    if ($LASTEXITCODE -ne 0) {
        throw "$Name DLL derlemesi başarısız."
    }
    if (-not (Test-Path -LiteralPath $dll)) {
        throw "$Name DLL üretilmedi."
    }
}

function Test-Pe64 {
    param([string]$DllPath)
    $headers = & $script:Objdump -f $DllPath 2>&1
    if ($LASTEXITCODE -ne 0 -or ($headers -notmatch "pei-x86-64")) {
        throw "PE32+ x64 doğrulaması başarısız: $DllPath"
    }
}

function Get-ImportedDlls {
    param([string]$DllPath)
    $text = & $script:Objdump -p $DllPath 2>$null
    if ($LASTEXITCODE -ne 0) { return @() }
    return @(
        $text |
        Select-String -Pattern "DLL Name:\s*(.+)$" |
        ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() } |
        Sort-Object -Unique
    )
}

function Test-IsSystemDll([string]$Name) {
    $upper = $Name.ToUpperInvariant()
    if ($upper -match "^(KERNEL32|USER32|ADVAPI32|SHELL32|OLE32|OLEAUT32|GDI32|WS2_32|CRYPT32|BCRYPT|NTDLL|RPCRT4|COMDLG32|COMCTL32|SHLWAPI|VERSION|WINMM|IPHLPAPI|NORMALIZ|SECUR32|UCRTBASE|VCRUNTIME140|MSVCP140)\.DLL$") {
        return $true
    }
    if ($upper -match "^API-MS-WIN-") { return $true }
    if ($upper -match "^EXT-MS-WIN-") { return $true }
    return $false
}

function Copy-DependenciesRecursive {
    param([string[]]$Roots)

    $queue = [System.Collections.Generic.Queue[string]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )

    foreach ($rootDll in $Roots) { $queue.Enqueue($rootDll) }

    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        foreach ($name in (Get-ImportedDlls -DllPath $current)) {
            if (Test-IsSystemDll $name) { continue }
            if (-not $seen.Add($name)) { continue }

            $candidate = Join-Path $script:UcrtBin $name
            if (-not (Test-Path -LiteralPath $candidate)) {
                $candidate = Join-Path $script:BuildBin $name
            }
            if (-not (Test-Path -LiteralPath $candidate)) {
                throw "Bağımlılık DLL bulunamadı: $name; isteyen: $current"
            }

            Copy-Item -LiteralPath $candidate -Destination $script:DistDeps -Force
            Copy-Item -LiteralPath $candidate -Destination $script:RuntimeBin -Force
            $queue.Enqueue($candidate)
        }
    }
}

function Fetch-Yyjson {
    $version = "0.12.0"
    $expected = "610a38a5e59192063f5f581ce0c3c1869971c458ea11b58dfe00d1c8269e255d"
    $url = "https://github.com/ibireme/yyjson/archive/refs/tags/$version.tar.gz"
    $archive = Join-Path $script:Downloads "yyjson-$version.tar.gz"
    $target = Join-Path $script:DepsRoot "yyjson-$version"

    if (Test-Path -LiteralPath (Join-Path $target "src\yyjson.c")) {
        return $target
    }
    if (-not $FetchDeps) {
        throw "yyjson kaynağı yok. -FetchDeps kullanın."
    }

    Ensure-Directory $script:Downloads
    Write-Host "DOWNLOAD yyjson $version"
    Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing

    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        Remove-Item -LiteralPath $archive -Force
        throw "yyjson SHA256 uyuşmuyor. Beklenen=$expected Gerçek=$actual"
    }

    Ensure-Directory $script:DepsRoot
    & tar.exe -xf $archive -C $script:DepsRoot
    if ($LASTEXITCODE -ne 0) {
        throw "yyjson arşivi çıkarılamadı."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $target "src\yyjson.c"))) {
        throw "yyjson kaynak düzeni beklenen biçimde değil."
    }
    return $target
}

$Root = (Resolve-Path -LiteralPath $Root).Path
$MsysRoot = if ($env:UXB_MSYS2_ROOT) { $env:UXB_MSYS2_ROOT } else { "C:\msys64" }
$UcrtBin = Join-Path $MsysRoot "ucrt64\bin"

$Gcc = Resolve-Tool "UXB_GCC" @(
    (Join-Path $UcrtBin "x86_64-w64-mingw32-gcc.exe"),
    (Join-Path $UcrtBin "gcc.exe")
)
$PkgConfig = Resolve-Tool "UXB_PKG_CONFIG" @(
    (Join-Path $UcrtBin "pkgconf.exe"),
    (Join-Path $UcrtBin "pkg-config.exe")
)
$Pacman = Resolve-Tool "UXB_PACMAN" @(
    (Join-Path $MsysRoot "usr\bin\pacman.exe")
)
$Objdump = Resolve-Tool "UXB_OBJDUMP" @(
    (Join-Path $UcrtBin "objdump.exe"),
    (Join-Path $UcrtBin "x86_64-w64-mingw32-objdump.exe")
)

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Session = Join-Path $Root "reports\libraries\cbase\$stamp"
$BuildRoot = Join-Path $Root "build\libraries\cbase"
$BuildBin = Join-Path $BuildRoot "bin"
$BuildLib = Join-Path $BuildRoot "lib"
$Downloads = Join-Path $BuildRoot "downloads"
$DepsRoot = Join-Path $BuildRoot "_deps"
$DistBin = Join-Path $Root "dist\libraries\bin"
$DistDeps = Join-Path $Root "dist\libraries\deps"
$DistLib = Join-Path $Root "dist\libraries\lib"
$RuntimeBin = Join-Path $Root "bin"
$CommonInclude = Join-Path $Root "runtime_ext\cbase_common"

foreach ($dir in @(
    $Session, $BuildRoot, $BuildBin, $BuildLib, $Downloads, $DepsRoot,
    $DistBin, $DistDeps, $DistLib, $RuntimeBin
)) { Ensure-Directory $dir }

if ($Clean) {
    Remove-Item -LiteralPath $BuildBin -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $BuildLib -Recurse -Force -ErrorAction SilentlyContinue
    Ensure-Directory $BuildBin
    Ensure-Directory $BuildLib
}

$packages = @(
    "mingw-w64-ucrt-x86_64-gcc",
    "mingw-w64-ucrt-x86_64-pkgconf",
    "mingw-w64-ucrt-x86_64-sqlite3",
    "mingw-w64-ucrt-x86_64-curl",
    "mingw-w64-ucrt-x86_64-pcre2",
    "mingw-w64-ucrt-x86_64-zstd",
    "mingw-w64-ucrt-x86_64-libarchive",
    "mingw-w64-ucrt-x86_64-libsodium"
)

if ($InstallDeps) {
    Write-Host "MSYS2 UCRT64 paketleri kuruluyor..."
    & $Pacman -S --needed --noconfirm @packages 2>&1 |
        Tee-Object -FilePath (Join-Path $Session "pacman.log")
    if ($LASTEXITCODE -ne 0) {
        throw "Pacman bağımlılık kurulumu başarısız. Önce MSYS2 içinde pacman -Syu çalıştırın."
    }
}

$pkgChecks = @{
    uxsqlite = @("sqlite3")
    uxhttp = @("libcurl")
    uxregex = @("libpcre2-8")
    uxcompress = @("libzstd")
    uxarchive = @("libarchive")
    uxcrypto = @("libsodium")
}

foreach ($module in $Modules) {
    if ($pkgChecks.ContainsKey($module)) {
        foreach ($pkg in $pkgChecks[$module]) {
            & $PkgConfig --exists $pkg
            if ($LASTEXITCODE -ne 0) {
                throw "pkg-config modülü bulunamadı: $pkg. -InstallDeps kullanın."
            }
        }
    }
}

$yyjson = $null
if ($Modules -contains "uxjson") {
    $yyjson = Fetch-Yyjson
}

foreach ($module in $Modules) {
    switch ($module) {
        "uxsqlite" {
            Invoke-GccBuild "uxsqlite" @(
                (Join-Path $Root "runtime_ext\uxsqlite\uxsqlite.c")
            ) @("sqlite3")
        }
        "uxhttp" {
            Invoke-GccBuild "uxhttp" @(
                (Join-Path $Root "runtime_ext\uxhttp\uxhttp.c")
            ) @("libcurl")
        }
        "uxjson" {
            Invoke-GccBuild "uxjson" @(
                (Join-Path $Root "runtime_ext\uxjson\uxjson.c"),
                (Join-Path $yyjson "src\yyjson.c")
            ) @() @("-I$(Join-Path $yyjson 'src')")
        }
        "uxregex" {
            Invoke-GccBuild "uxregex" @(
                (Join-Path $Root "runtime_ext\uxregex\uxregex.c")
            ) @("libpcre2-8")
        }
        "uxcompress" {
            Invoke-GccBuild "uxcompress" @(
                (Join-Path $Root "runtime_ext\uxcompress\uxcompress.c")
            ) @("libzstd")
        }
        "uxarchive" {
            Invoke-GccBuild "uxarchive" @(
                (Join-Path $Root "runtime_ext\uxarchive\uxarchive.c")
            ) @("libarchive")
        }
        "uxcrypto" {
            Invoke-GccBuild "uxcrypto" @(
                (Join-Path $Root "runtime_ext\uxcrypto\uxcrypto.c")
            ) @("libsodium")
        }
        default {
            throw "Bilinmeyen modül: $module"
        }
    }
}

$dlls = @()
foreach ($module in $Modules) {
    $dll = Join-Path $BuildBin "$module.dll"
    Test-Pe64 $dll
    Copy-Item -LiteralPath $dll -Destination $DistBin -Force
    Copy-Item -LiteralPath $dll -Destination $RuntimeBin -Force

    $implib = Join-Path $BuildLib "lib$module.dll.a"
    if (Test-Path -LiteralPath $implib) {
        Copy-Item -LiteralPath $implib -Destination $DistLib -Force
    }
    $dlls += $dll
}

Copy-DependenciesRecursive -Roots $dlls

$packageVersions = @{}
foreach ($package in $packages) {
    $query = & $Pacman -Q $package 2>$null
    if ($LASTEXITCODE -eq 0 -and $query) {
        $parts = $query -split "\s+", 2
        $packageVersions[$parts[0]] = $parts[1]
    }
}
$packageVersions["yyjson"] = "0.12.0"

$artifacts = foreach ($module in $Modules) {
    $path = Join-Path $DistBin "$module.dll"
    [ordered]@{
        module = $module
        dll = $path.Substring($Root.Length).TrimStart("\")
        sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes = (Get-Item -LiteralPath $path).Length
        architecture = "PE32+ x64"
    }
}

$manifest = [ordered]@{
    schema = "uxb.cbase.runtime.v1"
    created_at = (Get-Date).ToString("o")
    root = $Root
    toolchain = [ordered]@{
        gcc = $Gcc
        pkg_config = $PkgConfig
        pacman = $Pacman
        objdump = $Objdump
    }
    packages = $packageVersions
    modules = $artifacts
}
$manifestPath = Join-Path $Session "cbase_runtime_manifest.json"
$manifest | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $manifestPath -Encoding UTF8

if ($RunTests) {
    $uxb = Join-Path $Root "bin\uxb.exe"
    if (-not (Test-Path -LiteralPath $uxb)) {
        throw "RunTests istendi ancak bin\uxb.exe bulunamadı."
    }

    $oldPath = $env:PATH
    try {
        $env:PATH = "$RuntimeBin;$DistBin;$DistDeps;$UcrtBin;$oldPath"
        $test = Join-Path $Root "tests\libraries\cbase\cbase_smoke.uxb"

        & $uxb par $test 2>&1 |
            Tee-Object -FilePath (Join-Path $Session "test_par.log")
        if ($LASTEXITCODE -ne 0) { throw "cbase parser smoke FAIL" }

        & $uxb int $test 2>&1 |
            Tee-Object -FilePath (Join-Path $Session "test_ast.log")
        if ($LASTEXITCODE -ne 0) { throw "cbase AST smoke FAIL" }

        & $uxb int $test --interpreter-backend MIR 2>&1 |
            Tee-Object -FilePath (Join-Path $Session "test_mir.log")
        if ($LASTEXITCODE -ne 0) { throw "cbase MIR smoke FAIL" }
    }
    finally {
        $env:PATH = $oldPath
    }
}

Write-Host ""
Write-Host "UXB CBASE BUILD PASS"
Write-Host "Manifest: $manifestPath"
Write-Host "DLL:      $DistBin"
Write-Host "Deps:     $DistDeps"
