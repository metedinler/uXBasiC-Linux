[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Uxb,
    [string]$Objdump = 'C:/msys64/ucrt64/bin/objdump.exe',
    [string]$Report = 'reports/workspace_maintenance/host_package_contract.json'
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $root 'UXB-Common.ps1')
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
$package = Split-Path $compiler -Parent
$manifest = Get-Content -Raw -LiteralPath (Join-Path $package 'compiler_interpreter_runtime.json') | ConvertFrom-Json
$results = [Collections.Generic.List[object]]::new()
function Check([string]$Name, [bool]$Passed) {
    $results.Add([pscustomobject]@{name=$Name;passed=$Passed})
    if (!$Passed) { throw "Host package contract failed: $Name" }
}
foreach ($relative in @('UXB-Common.ps1','build_64.ps1','compiler/scripts/build_c_full_api.ps1','compiler/scripts/build_cbase_libraries.ps1',
    'compiler/scripts/build_uxb_main_64.ps1','tests/run_all_model_tests.ps1','tests/libraries/uxgsl/run_uxgsl_smoke_tests.ps1')) {
    $tokens=$null; $errors=$null
    [void][Management.Automation.Language.Parser]::ParseFile((Join-Path $root $relative),[ref]$tokens,[ref]$errors)
    Check "syntax:$relative" ($errors.Count -eq 0)
}
$roots = @($manifest.roots | ForEach-Object { Join-Path $root "bin/$_" })
$closure = @(Get-UxbRuntimeDllClosure -Roots $roots -SourceDirectories @((Join-Path $root 'bin')) -Objdump $Objdump)
Check 'manifest matches actual transitive imports' ((($closure.Name | Sort-Object) -join ',') -ceq (($manifest.files.name | Sort-Object) -join ','))
$mismatches = @($manifest.files | Where-Object {
    $staged = Join-Path $package $_.name
    !(Test-Path -LiteralPath $staged) -or (Get-FileHash -LiteralPath $staged).Hash -ine $_.sha256
})
Check 'staged DLL identities match manifest' ($mismatches.Count -eq 0)
$missingMessage = ''
try {
    # This test source directory deliberately has no vendor DLLs. A real PE
    # dependency must fail explicitly instead of returning a partial closure.
    Get-UxbRuntimeDllClosure -Roots @((Join-Path $root 'bin/uxraylib.dll')) -SourceDirectories @($PSScriptRoot) -Objdump $Objdump | Out-Null
} catch { $missingMessage=$_.Exception.Message }
Check 'missing dependency fails explicitly' ($missingMessage -like 'Missing runtime dependency:*')
$data = @{compiler=$compiler;sha256=(Get-FileHash -LiteralPath $compiler).Hash.ToLowerInvariant();
    total=$results.Count;passed=@($results | Where-Object passed).Count;results=$results.ToArray();missing_dependency=$missingMessage}
$reportPath=[IO.Path]::GetFullPath((Join-Path $root $Report))
[void][IO.Directory]::CreateDirectory((Split-Path $reportPath -Parent))
$data | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding utf8
Write-Output "Toplam: $($data.total)   PASS: $($data.passed)   FAIL: 0"
