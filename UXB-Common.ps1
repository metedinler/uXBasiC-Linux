Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-UxbRunnerRoot {
    param([string]$Root)
    if ([string]::IsNullOrWhiteSpace($Root)) {
        $Root = $PSScriptRoot
    }
    $resolved = (Resolve-Path -LiteralPath $Root).Path
    if (!(Test-Path -LiteralPath (Join-Path $resolved 'src/main.bas'))) { throw "uXBasic source root required: $resolved" }
    return $resolved
}

function Get-UxbExePath {
    param([string]$Root, [string]$UxbExe)
    if (-not [string]::IsNullOrWhiteSpace($UxbExe)) {
        return (Resolve-Path $UxbExe).Path
    }
    $candidate = Join-Path $Root "bin\uxb.exe"
    if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
    throw "uXBasic exe bulunamadi. Beklenen: bin\uxb.exe"
}

function New-UxbRunId {
    return (Get-Date).ToString("yyyyMMdd_HHmmss")
}

function Get-UxbPeImportedDllNames {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Objdump)
    $lines = @(& $Objdump -p $Path 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "PE import inspection failed: $Path`n$($lines -join "`n")" }
    @($lines | Select-String -Pattern 'DLL Name:\s*(.+)$' |
        ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() } | Sort-Object -Unique)
}

function Get-UxbRuntimeDllClosure {
    param([Parameter(Mandatory)][string[]]$Roots,
          [Parameter(Mandatory)][string[]]$SourceDirectories,
          [Parameter(Mandatory)][string]$Objdump)
    $queue = [Collections.Generic.Queue[string]]::new()
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $result = [Collections.Generic.List[object]]::new()
    foreach ($root in $Roots) { $queue.Enqueue((Resolve-Path -LiteralPath $root).Path) }
    while ($queue.Count) {
        $file = $queue.Dequeue()
        $name = [IO.Path]::GetFileName($file)
        if (!$seen.Add($name)) { continue }
        $imports = @(Get-UxbPeImportedDllNames -Path $file -Objdump $Objdump)
        $result.Add([pscustomobject]@{Path=$file; Name=$name; Imports=$imports})
        foreach ($dependency in $imports) {
            if ($dependency -match '^(api-ms-|ext-ms-)' -or
                (Test-Path -LiteralPath (Join-Path $env:SystemRoot "System32/$dependency"))) { continue }
            if ($dependency -notmatch '^[A-Za-z0-9_.-]+\.dll$') { throw "Invalid PE dependency name: $dependency required by $file" }
            if ($seen.Contains($dependency)) { continue }
            $source = $null
            foreach ($directory in $SourceDirectories) {
                $candidate = Join-Path $directory $dependency
                if (Test-Path -LiteralPath $candidate -PathType Leaf) { $source=$candidate; break }
            }
            if (!$source) { throw "Missing runtime dependency: $dependency required by $file" }
            $queue.Enqueue($source)
        }
    }
    $result.ToArray()
}

function New-UxbSafeName {
    param([string]$Path)
    $name = [IO.Path]::GetFileNameWithoutExtension($Path)
    $name = $name -replace '[^A-Za-z0-9_\-]+', '_'
    if ([string]::IsNullOrWhiteSpace($name)) { $name = "source" }
    return $name
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
    return (Resolve-Path $Path).Path
}

function Write-TextFileUtf8 {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir) { Ensure-Dir $dir | Out-Null }
    Set-Content -Path $Path -Value $Text -Encoding UTF8
}

function Invoke-UxbLogged {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$WorkDir,
        [Parameter(Mandatory=$true)][string]$LogDir,
        [string]$Name = "command"
    )
    Ensure-Dir $LogDir | Out-Null
    $cmdText = '"' + $Exe + '" ' + (($Arguments | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' ')
    Write-TextFileUtf8 (Join-Path $LogDir "$Name.command.txt") $cmdText
    $stdout = Join-Path $LogDir "$Name.stdout.log"
    $stderr = Join-Path $LogDir "$Name.stderr.log"
    Push-Location $WorkDir
    try {
        & $Exe @Arguments 1> $stdout 2> $stderr
        $rc = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    $result = [ordered]@{
        name = $Name
        rc = $rc
        command = $cmdText
        stdout = $stdout
        stderr = $stderr
    }
    $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path (Join-Path $LogDir "$Name.result.json")
    return $result
}

function Find-Wat2Wasm {
    param([string]$Root, [string]$Wat2Wasm)
    if (-not [string]::IsNullOrWhiteSpace($Wat2Wasm) -and (Test-Path $Wat2Wasm)) { return (Resolve-Path $Wat2Wasm).Path }
    $candidates = @(
        (Join-Path $Root "tools\wabt\bin\wat2wasm.exe"),
        (Join-Path $Root "wabt\bin\wat2wasm.exe"),
        "C:\msys64\ucrt64\bin\wat2wasm.exe",
        "C:\msys64\mingw64\bin\wat2wasm.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return (Resolve-Path $c).Path } }
    $cmd = Get-Command wat2wasm.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return ""
}

function New-HeaderDriverIfNeeded {
    param([string]$Source, [string]$OutDir)
    $ext = [IO.Path]::GetExtension($Source).ToLowerInvariant()
    if ($ext -ne ".uxbh") { return (Resolve-Path $Source).Path }
    Ensure-Dir $OutDir | Out-Null
    $full = (Resolve-Path $Source).Path
    $driver = Join-Path $OutDir "__header_driver.uxb"
    $safe = $full.Replace('"', '""')
    $text = @"
REM Otomatik header driver. .uxbh dogrudan program degildir.
INCLUDE "$safe"
PRINT "HEADER_DRIVER_OK"
"@
    Write-TextFileUtf8 $driver $text
    return (Resolve-Path $driver).Path
}

function Copy-BrowserFallbackIfNeeded {
    param([string]$Root, [string]$WebDir, [string]$HtmlPath)
    if (Test-Path $HtmlPath) { return }
    $tpl = Join-Path $Root "tools\release_runners\templates\browser_index_fallback.html"
    if (Test-Path $tpl) {
        Copy-Item $tpl $HtmlPath -Force
    } else {
        Write-TextFileUtf8 $HtmlPath "<html><body><h1>uXBasic Browser Runner</h1><script type='module' src='./program.js'></script></body></html>"
    }
}
