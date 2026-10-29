param(
    [string]$CompilerPath = ".\build\uxbasic_ffi_gui.exe",
    [string]$SourceGlob = "*.bas",
    [string]$OutRoot = "tests\basicCodeTests\out_matrix",
    [switch]$RunNativeExe,
    [switch]$IncludeExternalDllProbes,
    [switch]$IncludeInteractive
)

$ErrorActionPreference = "Stop"

function Resolve-CompilerPath {
    param([string]$PathIn)

    if (Test-Path -LiteralPath $PathIn) {
        return (Resolve-Path -LiteralPath $PathIn).Path
    }

    if (Test-Path -LiteralPath ".\uxbasic.exe") {
        return (Resolve-Path -LiteralPath ".\uxbasic.exe").Path
    }

    throw "Compiler not found. Build it first or pass -CompilerPath."
}

function Invoke-Step {
    param(
        [string]$StepName,
        [string]$LogPath,
        [scriptblock]$Body
    )

    $started = Get-Date
    try {
        $global:LASTEXITCODE = 0
        $output = & $Body 2>&1
        $exit = $LASTEXITCODE
        if ($null -eq $exit) { $exit = 0 }
        $output | Out-File -FilePath $LogPath -Encoding utf8
        return [PSCustomObject]@{
            step = $StepName
            exit = [int]$exit
            ok = ([int]$exit -eq 0)
            ms = [int]((Get-Date) - $started).TotalMilliseconds
            log = $LogPath
        }
    } catch {
        $_ | Out-File -FilePath $LogPath -Encoding utf8
        return [PSCustomObject]@{
            step = $StepName
            exit = -9999
            ok = $false
            ms = [int]((Get-Date) - $started).TotalMilliseconds
            log = $LogPath
        }
    }
}

function Test-ExternalProbe {
    param([string]$Name)
    return ($Name -match "^(34|35|36|37|38|39|40|41)_")
}

function Test-InteractiveProbe {
    param([string]$Name)
    return ($Name -match "messagebox|interactive")
}

function Test-NativeRunSafe {
    param([string]$Name)
    if (Test-InteractiveProbe $Name) { return $false }
    if (Test-ExternalProbe $Name) { return $false }
    return ($Name -match "^(31|32|42|43)_")
}

$compiler = Resolve-CompilerPath $CompilerPath
$root = Resolve-Path -LiteralPath "."
$sourceDir = Join-Path $root "tests\basicCodeTests"
$outRootFull = Join-Path $root $OutRoot
New-Item -ItemType Directory -Force -Path $outRootFull | Out-Null

$sources = Get-ChildItem -LiteralPath $sourceDir -Filter "*.bas" -File |
    Sort-Object Name |
    Where-Object {
        if ($_.Name -notlike $SourceGlob) { return $false }
        if (-not $IncludeExternalDllProbes -and (Test-ExternalProbe $_.Name)) { return $false }
        if (-not $IncludeInteractive -and (Test-InteractiveProbe $_.Name)) { return $false }
        return $true
    }

$rows = @()

foreach ($src in $sources) {
    $caseName = [IO.Path]::GetFileNameWithoutExtension($src.Name)
    $caseOut = Join-Path $outRootFull $caseName
    New-Item -ItemType Directory -Force -Path $caseOut | Out-Null

    $astJson = Join-Path $caseOut "ast.json"
    $inventoryJson = Join-Path $caseOut "inventory.json"
    $pipelineJson = Join-Path $caseOut "pipeline.json"
    $x64Out = Join-Path $caseOut "x64build"

    $steps = @()

    $steps += Invoke-Step "json" (Join-Path $caseOut "json.log") {
        & $compiler $src.FullName --ast-json-out $astJson --inventory-json-out $inventoryJson --pipeline-json-out $pipelineJson
    }

    $steps += Invoke-Step "semantic" (Join-Path $caseOut "semantic.log") {
        & $compiler $src.FullName --semantic
    }

    $steps += Invoke-Step "ast_run" (Join-Path $caseOut "exec_ast.log") {
        & $compiler $src.FullName --execmem
    }

    $steps += Invoke-Step "mir_run" (Join-Path $caseOut "exec_mir.log") {
        & $compiler $src.FullName --execmem --interpreter-backend MIR
    }

    $steps += Invoke-Step "x64_build" (Join-Path $caseOut "build_x64.log") {
        & $compiler $src.FullName --build-x64 --build-x64-out $x64Out
    }

    $nativeRunStatus = "SKIP"
    $nativeRunExit = ""
    $nativeRunLog = Join-Path $caseOut "run_x64.log"
    if ($RunNativeExe -and (Test-NativeRunSafe $src.Name)) {
        $exePath = Join-Path $x64Out "program.exe"
        if (Test-Path -LiteralPath $exePath) {
            $runStep = Invoke-Step "x64_run" $nativeRunLog {
                & $exePath
            }
            $nativeRunStatus = $(if ($runStep.ok) { "OK" } elseif ($runStep.exit -ne -9999) { "RAN_EXIT_" + $runStep.exit } else { "FAIL" })
            $nativeRunExit = $runStep.exit
            $steps += $runStep
        } else {
            "program.exe missing" | Out-File -FilePath $nativeRunLog -Encoding utf8
            $nativeRunStatus = "MISSING"
            $nativeRunExit = -1
        }
    } elseif (Test-InteractiveProbe $src.Name) {
        $nativeRunStatus = "SKIP_INTERACTIVE"
    } elseif (Test-ExternalProbe $src.Name) {
        $nativeRunStatus = "SKIP_EXTERNAL_DLL"
    }

    $row = [PSCustomObject]@{
        name = $src.Name
        json = $(if (($steps | Where-Object step -eq "json").ok) { "OK" } else { "FAIL" })
        semantic = $(if (($steps | Where-Object step -eq "semantic").ok) { "OK" } else { "FAIL" })
        ast_run = $(if (($steps | Where-Object step -eq "ast_run").ok) { "OK" } else { "FAIL" })
        mir_run = $(if (($steps | Where-Object step -eq "mir_run").ok) { "OK" } else { "FAIL" })
        x64_build = $(if (($steps | Where-Object step -eq "x64_build").ok) { "OK" } else { "FAIL" })
        x64_run = $nativeRunStatus
        x64_run_exit = $nativeRunExit
        out_dir = $caseOut
    }
    $rows += $row
}

$csvPath = Join-Path $outRootFull "matrix.csv"
$jsonPath = Join-Path $outRootFull "matrix.json"
$mdPath = Join-Path $outRootFull "matrix.md"

$rows | Export-Csv -NoTypeInformation -Encoding utf8 -Path $csvPath
$rows | ConvertTo-Json -Depth 4 | Out-File -FilePath $jsonPath -Encoding utf8

$md = @()
$md += "# uXBasic basicCodeTests Matrix"
$md += ""
$md += "- compiler: ``$compiler``"
$md += "- generated: $(Get-Date -Format s)"
$md += "- source glob: ``$SourceGlob``"
$md += "- native run: $RunNativeExe"
$md += ""
$md += "| Source | JSON | Semantic | AST | MIR | x64 Build | x64 Run |"
$md += "|---|---|---|---|---|---|---|"
foreach ($row in $rows) {
    $md += "| ``$($row.name)`` | $($row.json) | $($row.semantic) | $($row.ast_run) | $($row.mir_run) | $($row.x64_build) | $($row.x64_run) |"
}
$md | Out-File -FilePath $mdPath -Encoding utf8

Write-Host "matrix csv: $csvPath"
Write-Host "matrix json: $jsonPath"
Write-Host "matrix md: $mdPath"

$hasFailure = $false
foreach ($row in $rows) {
    if ($row.json -eq "FAIL" -or
        $row.semantic -eq "FAIL" -or
        $row.ast_run -eq "FAIL" -or
        $row.mir_run -eq "FAIL" -or
        $row.x64_build -eq "FAIL" -or
        $row.x64_run -eq "FAIL" -or
        $row.x64_run -eq "MISSING") {
        $hasFailure = $true
    }
}

if ($hasFailure) {
    exit 1
}

exit 0
