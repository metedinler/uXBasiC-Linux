param([string]$Uxb = '.\bin\uxb.exe', [string]$Only = '')
# S-672: every preprocessor directive must have an observable effect (see ai_koordinasyon\ONISLEMCI_ETKI_MATRISI_20261025.md).
$compiler = (Resolve-Path -LiteralPath $Uxb).Path
if ([IO.Path]::GetExtension($compiler) -eq '.cmd') {
    $match = [regex]::Match([IO.File]::ReadAllText($compiler), '(?m)^"([^"\r\n]+\.exe)" %\*')
    if (!$match.Success) { throw 'Cannot find the compiler in the model-test wrapper.' }
    $compiler = $match.Groups[1].Value
}
$output = Join-Path (Get-Location).Path ('reports\preprocessor_effects_' + [Guid]::NewGuid().ToString('N'))
$extra = @()
if ($Only -ne '') { $extra = @('--only', $Only) }
& python -I (Join-Path $PSScriptRoot 'run_effects.py') --uxb $compiler --output $output @extra
exit $LASTEXITCODE
