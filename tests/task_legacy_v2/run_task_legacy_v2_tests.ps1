param([string]$Uxb='.\bin\uxb.exe')
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
& python (Join-Path $PSScriptRoot '..\turkce_ad\run_tests.py') --uxb $compiler --test-root $PSScriptRoot --temp-builds --jobs 2
exit $LASTEXITCODE
