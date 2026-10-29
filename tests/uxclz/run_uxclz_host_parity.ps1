param(
    [string]$Uxb = ".\bin\uxb.exe"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$uxbPath = (Resolve-Path (Join-Path $root $Uxb)).Path
$source = Join-Path $PSScriptRoot "uxclz_host_parity.uxb"
$reportRoot = Join-Path $root "reports\uxclz_host_parity"
$dllDir = Join-Path $root "runtime_ext\uxclz\build"
$oldPath = $env:PATH

New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
$env:PATH = "$dllDir;$oldPath"

try {
    $cases = @(
        @{ Name = "ast"; Args = @("run", $source, "--interpreter-backend", "AST", "--quiet") },
        @{ Name = "mir"; Args = @("run", $source, "--interpreter-backend", "MIR", "--quiet") },
        @{ Name = "ast_x64"; Args = @("bld", $source, "--x64-mode", "AST", "--codegen-source", "AST", "--build-x64-out", (Join-Path $reportRoot "uxclz_ast.exe"), "--quiet") },
        @{ Name = "mir_x64"; Args = @("bld", $source, "--x64-mode", "MIR", "--codegen-source", "MIR", "--build-x64-out", (Join-Path $reportRoot "uxclz_mir.exe"), "--quiet") }
    )

    foreach ($case in $cases) {
        $output = & $uxbPath @($case.Args) 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "$($case.Name) failed:`n$($output -join [Environment]::NewLine)"
        }
        if ($case.Name -in @("ast", "mir") -and ($output -join "`n") -notmatch "UXCLZ_HOST_PARITY_PASS") {
            throw "$($case.Name) did not print the PASS marker."
        }
        Write-Host "[uxclz-parity] $($case.Name) PASS"
    }

    foreach ($exe in @("uxclz_ast.exe", "uxclz_mir.exe")) {
        $stdoutPath = Join-Path $reportRoot "$exe.stdout.txt"
        $stderrPath = Join-Path $reportRoot "$exe.stderr.txt"
        $process = Start-Process -FilePath (Join-Path $reportRoot $exe) -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
        $output = (Get-Content -LiteralPath $stdoutPath -Raw) + (Get-Content -LiteralPath $stderrPath -Raw)
        if ($process.ExitCode -ne 0 -or $output -notmatch "UXCLZ_HOST_PARITY_PASS") {
            throw "$exe host execution failed:`n$output"
        }
        Write-Host "[uxclz-parity] $exe host PASS"
    }
} finally {
    $env:PATH = $oldPath
}

Write-Host "UXCLZ_HOST_PARITY status=PASS"
