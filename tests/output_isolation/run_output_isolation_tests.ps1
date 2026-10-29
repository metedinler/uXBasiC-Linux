param([string]$Uxb='.\bin\uxb.exe')
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$output = Join-Path (Get-Location).Path ('reports\output_isolation_' + [Guid]::NewGuid().ToString('N'))
& python (Join-Path $PSScriptRoot 'run_tests.py') --uxb $compiler --output $output
exit $LASTEXITCODE
