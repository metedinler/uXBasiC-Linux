[CmdletBinding()]
param(
    [string]$Root = ".",
    [switch]$InstallDeps,
    [switch]$Clean,
    [switch]$RunTests,
    [ValidateSet("stable", "experimental")]
    [string]$Profile = "stable",
    [string[]]$Modules = @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot '../../UXB-Common.ps1')

function Resolve-Root([string]$Value) {
    $candidate = (Resolve-Path -LiteralPath $Value).Path
    if ((Test-Path (Join-Path $candidate "runtime_ext")) -and
        (Test-Path (Join-Path $candidate "libsx"))) {
        return $candidate
    }
    if ((Test-Path (Join-Path $candidate "uxb\runtime_ext")) -and
        (Test-Path (Join-Path $candidate "uxb\libsx"))) {
        return (Join-Path $candidate "uxb")
    }
    throw "uXBasic kökü bulunamadı: $candidate"
}

function Ensure-Directory([string]$Path) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Resolve-Tool(
    [string]$EnvironmentName,
    [string[]]$Candidates
) {
    $fromEnvironment = [Environment]::GetEnvironmentVariable($EnvironmentName)
    if ($fromEnvironment -and (Test-Path -LiteralPath $fromEnvironment)) {
        return (Resolve-Path -LiteralPath $fromEnvironment).Path
    }
    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    throw "Araç bulunamadı: $EnvironmentName"
}

function Invoke-Logged(
    [string]$Program,
    [string[]]$Arguments,
    [string]$LogPath,
    [string]$WorkingDirectory
) {
    Write-Host "RUN $Program $($Arguments -join ' ')"
    Push-Location -LiteralPath $WorkingDirectory
    try {
        $oldErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = & $Program @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
        Pop-Location
    }
    $output | Set-Content -LiteralPath $LogPath -Encoding UTF8
    if ($output) { $output | Write-Host }
    if ($exitCode -ne 0) {
        throw "Komut başarısız exit=$exitCode log=$LogPath"
    }
}

function Get-PkgTokens([string]$Mode, [string]$Module) {
    $value = & $script:PkgConfig "--$Mode" $Module 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "pkg-config başarısız: $Module --$Mode"
    }
    return @($value -split "\s+" | Where-Object { $_ })
}

function Find-VendorDll([object]$Library) {
    foreach ($pattern in $Library.dll_globs) {
        $matches = @(
            Get-ChildItem -LiteralPath $script:UcrtBin `
                -Filter $pattern -File -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending
        )
        if ($matches.Count -gt 0) {
            return $matches[0].FullName
        }
    }
    throw "Vendor DLL bulunamadı: $($Library.name)"
}

function Get-ImportedDlls([string]$DllPath) {
    @(Get-UxbPeImportedDllNames -Path $DllPath -Objdump $script:Objdump)
}

function Test-SystemDll([string]$Name) {
    if ($env:SystemRoot) {
        $systemCandidate = Join-Path $env:SystemRoot ("System32\" + $Name)
        if (Test-Path -LiteralPath $systemCandidate) {
            return $true
        }
    }
    $upper = $Name.ToUpperInvariant()
    if ($upper -match "^(KERNEL32|USER32|ADVAPI32|SHELL32|OLE32|OLEAUT32|GDI32|WS2_32|WLDAP32|DNSAPI|CRYPT32|BCRYPT|NTDLL|RPCRT4|COMDLG32|COMCTL32|SHLWAPI|VERSION|WINMM|IPHLPAPI|NORMALIZ|SECUR32|UCRTBASE|MSVCRT)\.DLL$") {
        return $true
    }
    if ($upper -match "^API-MS-WIN-") { return $true }
    if ($upper -match "^EXT-MS-WIN-") { return $true }
    return $false
}

function Copy-DependencyClosure([string[]]$RootDlls) {
    $queue = [System.Collections.Generic.Queue[string]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )
    foreach ($dll in $RootDlls) { $queue.Enqueue($dll) }

    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        foreach ($name in (Get-ImportedDlls $current)) {
            if (Test-SystemDll $name) { continue }
            if (-not $seen.Add($name)) { continue }

            $candidate = Join-Path $script:UcrtBin $name
            if (-not (Test-Path -LiteralPath $candidate)) {
                $candidate = Join-Path $script:DistBin $name
            }
            if (-not (Test-Path -LiteralPath $candidate)) {
                throw "Geçişli DLL bağımlılığı bulunamadı: $name isteyen=$current"
            }

            Copy-Item -LiteralPath $candidate -Destination $script:DistDeps -Force
            Copy-Item -LiteralPath $candidate -Destination $script:RuntimeBin -Force
            $queue.Enqueue($candidate)
        }
    }
}

function Assert-Pe64([string]$DllPath) {
    $text = & $script:Objdump -f $DllPath 2>&1
    $headerText = ($text | Out-String)
    if ($LASTEXITCODE -ne 0 -or $headerText -notmatch "pei-x86-64") {
        throw "PE32+ x64 doğrulaması başarısız: $DllPath"
    }
}

function Build-InlineShim(
    [object]$Library,
    [string]$ReportPath
) {
    $report = Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    if ([int]$report.inline_shim_count -eq 0) {
        return $null
    }

    $source = Join-Path $script:RootPath (
        "runtime_ext\c_full_generated\$($Library.name)\$($Library.name)_uxshim.c"
    )
    $target = Join-Path $script:DistBin "$($Library.name)_uxshim.dll"
    $implib = Join-Path $script:DistLib "lib$($Library.name)_uxshim.dll.a"
    $flags = @(
        "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-shared", "-static-libgcc",
        "-I$script:IncludeRoot"
    )
    $flags += Get-PkgTokens "cflags" $Library.pkg_config
    $flags += @(
        $source,
        "-Wl,--out-implib,$implib"
    )
    $flags += Get-PkgTokens "libs" $Library.pkg_config
    $flags += @("-o", $target)

    Invoke-Logged $script:Gcc $flags (
        Join-Path $script:Session "$($Library.name)_shim_build.log"
    ) $script:RootPath

    Assert-Pe64 $target
    Copy-Item -LiteralPath $target -Destination $script:RuntimeBin -Force
    return $target
}

$normalizedModules = @()
foreach ($moduleItem in $Modules) {
    foreach ($part in ([string]$moduleItem -split ",")) {
        $trimmed = $part.Trim()
        if ($trimmed) { $normalizedModules += $trimmed }
    }
}
$Modules = @($normalizedModules | Sort-Object -Unique)

$RootPath = Resolve-Root $Root
$MsysRoot = if ($env:UXB_MSYS2_ROOT) { $env:UXB_MSYS2_ROOT } else { "C:\msys64" }
$UcrtBin = Join-Path $MsysRoot "ucrt64\bin"
$IncludeRoot = Join-Path $MsysRoot "ucrt64\include"
if ($env:PATH -notlike "$UcrtBin*") {
    $env:PATH = "$UcrtBin;$env:PATH"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Session = Join-Path $RootPath "reports\libraries\c_full\$stamp"
$DistBin = Join-Path $RootPath "dist\libraries\bin"
$DistDeps = Join-Path $RootPath "dist\libraries\deps"
$DistLib = Join-Path $RootPath "dist\libraries\lib"
$RuntimeBin = Join-Path $RootPath "bin"
$Generated = Join-Path $RootPath "runtime_ext\c_full_generated"
$SystemManifestPath = Join-Path $RootPath "manifests\c_full_api_system.json"

foreach ($folder in @(
    $Session, $DistBin, $DistDeps, $DistLib, $RuntimeBin, $Generated
)) {
    Ensure-Directory $folder
}

# Read the requested package set before resolving GCC/Clang.  This allows the
# default one-command build to install a missing toolchain through pacman.
$system = Get-Content -LiteralPath $SystemManifestPath -Raw -Encoding UTF8 |
    ConvertFrom-Json
$known = @{}
foreach ($library in $system.libraries) {
    $known[$library.name] = $library
}
foreach ($name in $Modules) {
    if (-not $known.ContainsKey($name)) {
        throw "Bilinmeyen modül: $name"
    }
}

$packages = @($system.tool_packages)
foreach ($name in $Modules) {
    $packages += [string]$known[$name].package
}
$packages = @($packages | Sort-Object -Unique)

# pacman is the only tool that must exist before dependency installation.
$Pacman = Resolve-Tool "UXB_PACMAN" @(
    (Join-Path $MsysRoot "usr\bin\pacman.exe")
)

if ($InstallDeps) {
    $installArgs = @("-S", "--needed", "--noconfirm") + $packages
    Invoke-Logged -Program $Pacman -Arguments $installArgs -LogPath (
        Join-Path $Session "pacman_install.log"
    ) -WorkingDirectory $RootPath
}

# Resolve the actual compiler tools after package installation.
$Gcc = Resolve-Tool "UXB_GCC" @(
    (Join-Path $UcrtBin "x86_64-w64-mingw32-gcc.exe"),
    (Join-Path $UcrtBin "gcc.exe")
)
$Clang = Resolve-Tool "UXB_CLANG" @(
    (Join-Path $UcrtBin "clang.exe")
)
$PkgConfig = Resolve-Tool "UXB_PKG_CONFIG" @(
    (Join-Path $UcrtBin "pkgconf.exe"),
    (Join-Path $UcrtBin "pkg-config.exe")
)
$Objdump = Resolve-Tool "UXB_OBJDUMP" @(
    (Join-Path $UcrtBin "objdump.exe"),
    (Join-Path $UcrtBin "x86_64-w64-mingw32-objdump.exe")
)

if ($Clean) {
    Remove-Item -LiteralPath $Generated -Recurse -Force -ErrorAction SilentlyContinue
    Ensure-Directory $Generated
    foreach ($name in @(
        "uxsqlite", "uxhttp", "uxjson", "uxregex",
        "uxcompress", "uxarchive", "uxcrypto"
    )) {
        Remove-Item -LiteralPath (
            Join-Path $RootPath "libsx\$name\$name.bas"
        ) -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath (
            Join-Path $RootPath "include\modules\$name.uxmh"
        ) -Force -ErrorAction SilentlyContinue
    }
}

foreach ($package in $packages) {
    & $Pacman -Q $package >$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Gerekli MSYS2 paketi kurulu değil: $package"
    }
    $check = & $Pacman -Qkk $package 2>&1
    $check | Set-Content -LiteralPath (
        Join-Path $Session ("package_check_" + ($package -replace '[^A-Za-z0-9_.-]', '_') + ".log")
    ) -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        throw "Paket bütünlük kontrolü başarısız: $package"
    }
}

# Build the general libffi call engine first.
$uxcapiBuild = Join-Path $RootPath "runtime_ext\uxcapi\build_uxcapi_dll.bat"
Invoke-Logged "cmd.exe" @("/d", "/c", $uxcapiBuild) (
    Join-Path $Session "uxcapi_build.log"
) $RootPath
$uxcapiDll = Join-Path $DistBin "uxcapi.dll"
Assert-Pe64 $uxcapiDll

$generator = Join-Path $RootPath "tools\library_tools\uxb_c_full_bindgen.py"
$python = if ($env:UXB_PYTHON) { $env:UXB_PYTHON } else { "python" }

$vendorDlls = @()
$shimDlls = @()
$surfaceReports = @()
foreach ($name in $Modules) {
    $library = $known[$name]
    $dllPath = Find-VendorDll $library
    $vendorDlls += $dllPath

    Copy-Item -LiteralPath $dllPath -Destination $DistDeps -Force
    Copy-Item -LiteralPath $dllPath -Destination $RuntimeBin -Force

    $manifestPath = Join-Path $RootPath "manifests\c_full\$name.json"
    $arguments = @(
        $generator,
        "--root", $RootPath,
        "--manifest", $manifestPath,
        "--clang", $Clang,
        "--objdump", $Objdump,
        "--include-root", $IncludeRoot,
        "--dll", $dllPath,
        "--profile", $Profile,
        "--report-dir", $Session
    )
    Invoke-Logged $python $arguments (
        Join-Path $Session "$name.bindgen.log"
    ) $RootPath

    $reportPath = Join-Path $Session "$($name)_surface.json"
    $surfaceReports += $reportPath
    $shim = Build-InlineShim $library $reportPath
    if ($shim) { $shimDlls += $shim }
}

# Stage all transitive DLL imports. Vendor DLLs remain in deps; generated
# first-party uxcapi and shim DLLs remain in bin.
Copy-DependencyClosure (@($uxcapiDll) + $vendorDlls + $shimDlls)

$surfaceSummary = @()
$totalUnbound = 0
foreach ($reportPath in $surfaceReports) {
    $surface = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 |
        ConvertFrom-Json
    $totalUnbound += [int]$surface.unbound_function_count
    $surfaceSummary += [ordered]@{
        module = $surface.module
        engine = $surface.engine
        license = $surface.license
        homepage = $surface.homepage
        header_functions = $surface.header_function_count
        generated_functions = $surface.generated_function_count
        exported_functions = $surface.exported_function_count
        inline_shims = $surface.inline_shim_count
        variadic_functions = $surface.variadic_function_count
        constants = $surface.constant_count
        unbound = $surface.unbound_function_count
    }
}
if ($totalUnbound -ne 0) {
    throw "Tam C API kapısı başarısız: unbound function count=$totalUnbound"
}

$allRuntimeDlls = @(
    Get-ChildItem -LiteralPath $DistBin -Filter "*.dll" -File
    Get-ChildItem -LiteralPath $DistDeps -Filter "*.dll" -File
)
$runtimeFiles = @()
foreach ($dll in $allRuntimeDlls) {
    Assert-Pe64 $dll.FullName
    $runtimeFiles += [ordered]@{
        name = $dll.Name
        path = $dll.FullName.Substring($RootPath.Length).TrimStart("\")
        bytes = $dll.Length
        sha256 = (
            Get-FileHash -LiteralPath $dll.FullName -Algorithm SHA256
        ).Hash.ToLowerInvariant()
    }
}

$versions = @{}
foreach ($package in $packages) {
    $line = & $Pacman -Q $package
    if ($LASTEXITCODE -eq 0) {
        $parts = $line -split "\s+", 2
        $versions[$parts[0]] = $parts[1]
    }
}

$runtimeManifest = [ordered]@{
    schema = "uxb.c.full_api.runtime.v1"
    generated_at = (Get-Date).ToString("o")
    profile = $Profile
    status = "PASS"
    packages = $versions
    surfaces = $surfaceSummary
    runtime_files = $runtimeFiles
}
$runtimeManifestPath = Join-Path $Session "runtime_manifest.json"
$runtimeManifest | ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $runtimeManifestPath -Encoding UTF8

if ($RunTests) {
    $uxb = Join-Path $RuntimeBin "uxb.exe"
    if (-not (Test-Path -LiteralPath $uxb)) {
        throw "RunTests istendi fakat bin\uxb.exe yok."
    }

    $testSource = Join-Path $RootPath "runtime_ext\uxcapi\tests\uxcapi_test.c"
    $testDll = Join-Path $Session "uxcapi_test.dll"
    $testBuildArgs = @(
        "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-shared", "-static-libgcc",
        $testSource,
        "-o", $testDll
    )
    Invoke-Logged -Program $Gcc -Arguments $testBuildArgs -LogPath (
        Join-Path $Session "uxcapi_test_build.log"
    ) -WorkingDirectory $RootPath
    Assert-Pe64 $testDll

    $test = Join-Path $RootPath "tests\libraries\c_full_api\full_api_smoke.uxb"
    $oldPath = $env:PATH
    try {
        $env:PATH = "$Session;$RuntimeBin;$DistBin;$DistDeps;$UcrtBin;$oldPath"

        Invoke-Logged $uxb @("par", $test) (
            Join-Path $Session "smoke_par.log"
        ) $RootPath

        Invoke-Logged $uxb @("int", $test) (
            Join-Path $Session "smoke_ast.log"
        ) $RootPath

        Invoke-Logged $uxb @(
            "int", $test, "--interpreter-backend", "MIR"
        ) (
            Join-Path $Session "smoke_mir.log"
        ) $RootPath
    }
    finally {
        $env:PATH = $oldPath
    }
}

Write-Host ""
Write-Host "UXB C FULL API BUILD PASS"
Write-Host "Profile:  $Profile"
Write-Host "Manifest: $runtimeManifestPath"
Write-Host "Functions:"
foreach ($surface in $surfaceSummary) {
    Write-Host (
        "  {0}: generated={1} inline={2} variadic={3} unbound={4}" -f
        $surface.module,
        $surface.generated_functions,
        $surface.inline_shims,
        $surface.variadic_functions,
        $surface.unbound
    )
}
