param([string]$Uxb='.\bin\uxb.exe', [string]$TestRoot=$PSScriptRoot, [string[]]$Only=@())
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$runnerArgs = @('--uxb', $compiler, '--test-root', $TestRoot, '--temp-builds', '--jobs', '4')
if ($Only.Count -gt 0) { $runnerArgs += '--only'; $runnerArgs += $Only }
& python (Join-Path $PSScriptRoot '..\turkce_ad\run_tests.py') @runnerArgs
exit $LASTEXITCODE
