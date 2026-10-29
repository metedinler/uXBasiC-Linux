[CmdletBinding()]
param(
    [string]$Uxb = ".\bin\uxb.exe",
    [string]$TestRoot = ".\tests\typed_task_routines",
    [string]$ExpectedRoot = "",
    [string]$ReportRoot = "",
    [switch]$SkipAst,
    [switch]$SkipMir,
    [switch]$EmitMirX64,
    [switch]$UpdateExpected
)

$ErrorActionPreference = "Stop"

if ($ExpectedRoot -eq "") { $ExpectedRoot = Join-Path $TestRoot "expected" }
if ($ReportRoot -eq '') { $ReportRoot = Join-Path '.\reports\typed_task_routines' ((Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + [guid]::NewGuid().ToString('N').Substring(0, 8)) }

$script:Results = @()

function Add-Result {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Status,
        [string]$Detail = ""
    )
    $script:Results += [PSCustomObject]@{ Label = $Label; Status = $Status; Detail = $Detail }
    if ($Status -eq "PASS") { Write-Host "  PASS $Label" -ForegroundColor Green }
    else {
        Write-Host "  $Status $Label" -ForegroundColor Red
        if ($Detail -ne "") { Write-Host $Detail }
    }
}

# Line endings differ per backend (AST writes CRLF, MIR writes LF) and a
# trailing newline is not meaningful here.  Compare on normalized text.
function Get-NormalizedText {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $t = $Text -replace "`r`n", "`n"
    $t = $t -replace "`r", "`n"
    return $t.TrimEnd("`n", " ", "`t")
}

function Get-NormalizedFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $raw = [IO.File]::ReadAllText($Path)
    return Get-NormalizedText -Text $raw
}

function Format-Mismatch {
    param([string]$Expected, [string]$Actual)
    $expLines = @()
    $actLines = @()
    if ($Expected -ne "") { $expLines = $Expected -split "`n" }
    if ($Actual -ne "") { $actLines = $Actual -split "`n" }
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("    beklenen ($($expLines.Count) satir):")
    foreach ($l in $expLines) { [void]$sb.AppendLine("      | $l") }
    [void]$sb.AppendLine("    gercek ($($actLines.Count) satir):")
    foreach ($l in $actLines) { [void]$sb.AppendLine("      | $l") }
    return $sb.ToString().TrimEnd()
}

function Invoke-Uxb {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & $Uxb @Arguments 2>&1 | Out-String
    return [PSCustomObject]@{ ExitCode = $LASTEXITCODE; Output = $output }
}

# Runs one backend of one positive test: the compiler must succeed and the
# captured program output must equal the expected file.
function Test-PositiveBackend {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][string]$ExpectedPath
    )

    if (Test-Path -LiteralPath $OutputPath -PathType Leaf) { throw "Use a fresh report directory; existing evidence is preserved: $OutputPath" }

    $run = Invoke-Uxb -Arguments $Arguments
    if ($run.ExitCode -ne 0) {
        Add-Result -Label $Label -Status "FAIL" -Detail "    cikis kodu $($run.ExitCode)`n$($run.Output)"
        return
    }

    if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
        Add-Result -Label $Label -Status "FAIL" -Detail "    program ciktisi uretilmedi: $OutputPath"
        return
    }

    $actual = Get-NormalizedFile -Path $OutputPath

    if ($UpdateExpected) {
        [IO.File]::WriteAllText($ExpectedPath, $actual + "`n")
        Add-Result -Label $Label -Status "PASS" -Detail ""
        return
    }

    $expected = Get-NormalizedFile -Path $ExpectedPath
    if ($null -eq $expected) {
        Add-Result -Label $Label -Status "FAIL" -Detail "    beklenen cikti dosyasi yok: $ExpectedPath (-UpdateExpected ile uretebilirsiniz, once gozden gecirin)"
        return
    }

    if ($actual -ne $expected) {
        Add-Result -Label $Label -Status "FAIL" -Detail (Format-Mismatch -Expected $expected -Actual $actual)
        return
    }

    Add-Result -Label $Label -Status "PASS"
}

if (-not (Test-Path -LiteralPath $Uxb -PathType Leaf)) { throw "uXBasic compiler not found: $Uxb" }
if (-not (Test-Path -LiteralPath $TestRoot -PathType Container)) { throw "Test directory not found: $TestRoot" }
New-Item -ItemType Directory -Force -Path $ReportRoot | Out-Null
if ($UpdateExpected) {
    New-Item -ItemType Directory -Force -Path $ExpectedRoot | Out-Null
    Write-Host "UYARI: -UpdateExpected acik. Beklenen ciktilar derleyicinin SU ANKI davranisindan yeniden yazilacak." -ForegroundColor Yellow
    Write-Host "       Uretilen dosyalari gozden gecirmeden commit etmeyin." -ForegroundColor Yellow
}

$positive = Get-ChildItem -LiteralPath $TestRoot -Filter "0*.uxb" | Sort-Object Name
$negative = Get-ChildItem -LiteralPath $TestRoot -Filter "negative_*.uxb" | Sort-Object Name

foreach ($test in $positive) {
    $base = $test.BaseName
    $expectedPath = Join-Path $ExpectedRoot "$base.txt"
    Write-Host "[$($test.Name)]"

    if (-not $SkipAst) {
        $outPath = Join-Path $ReportRoot "${base}_ast_stdout.txt"
        Test-PositiveBackend -Label "AST/$($test.Name)" -OutputPath $outPath -ExpectedPath $expectedPath -Arguments @(
            "int", $test.FullName, "--interpreter-backend", "AST", "--stdout-out", $outPath
        )
    }

    if (-not $SkipMir) {
        $outPath = Join-Path $ReportRoot "${base}_mir_stdout.txt"
        Test-PositiveBackend -Label "MIR/$($test.Name)" -OutputPath $outPath -ExpectedPath $expectedPath -Arguments @(
            "int", $test.FullName, "--interpreter-backend", "MIR", "--mir-program-output-out", $outPath
        )
    }

    if ($EmitMirX64) {
        $asmPath = Join-Path $ReportRoot "${base}_mir.asm"
        if (Test-Path -LiteralPath $asmPath -PathType Leaf) { throw "Use a fresh report directory; existing evidence is preserved: $asmPath" }
        $run = Invoke-Uxb -Arguments @(
            "x64", $test.FullName, "--codegen-source", "MIR", "--x64-mode", "MIR", "--emit-x64-nasm-out", $asmPath
        )
        if ($run.ExitCode -ne 0) {
            Add-Result -Label "MIR-x64/$($test.Name)" -Status "FAIL" -Detail "    cikis kodu $($run.ExitCode)`n$($run.Output)"
        }
        elseif (-not (Test-Path -LiteralPath $asmPath -PathType Leaf)) {
            Add-Result -Label "MIR-x64/$($test.Name)" -Status "FAIL" -Detail "    NASM ciktisi uretilmedi: $asmPath"
        }
        elseif ((Get-Item -LiteralPath $asmPath).Length -eq 0) {
            Add-Result -Label "MIR-x64/$($test.Name)" -Status "FAIL" -Detail "    NASM ciktisi bos: $asmPath"
        }
        else {
            Add-Result -Label "MIR-x64/$($test.Name)" -Status "PASS"
        }
    }
}

foreach ($test in $negative) {
    $base = $test.BaseName
    $label = "NEGATIVE/$($test.Name)"
    Write-Host "[$($test.Name)]"

    $run = Invoke-Uxb -Arguments @("sem", $test.FullName, "--stop-after", "sem")
    if ($run.ExitCode -eq 0) {
        Add-Result -Label $label -Status "FAIL" -Detail "    beklenmedik sekilde basarili oldu"
        continue
    }

    # A non-zero exit alone does not prove the intended diagnostic fired; any
    # unrelated failure would also exit non-zero.  Require the expected text.
    $expectedErrPath = Join-Path $ExpectedRoot "$base.err.txt"
    $expectedErr = Get-NormalizedFile -Path $expectedErrPath
    if ($null -eq $expectedErr -or $expectedErr -eq "") {
        Add-Result -Label $label -Status "FAIL" -Detail "    beklenen hata metni dosyasi yok/bos: $expectedErrPath"
        continue
    }

    $actualOut = Get-NormalizedText -Text $run.Output
    if ($actualOut.Contains($expectedErr)) {
        Add-Result -Label $label -Status "PASS"
    }
    else {
        Add-Result -Label $label -Status "FAIL" -Detail "    beklenen hata metni bulunamadi: '$expectedErr'`n    derleyici ciktisi:`n$($run.Output)"
    }
}

$passCount = @($script:Results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = @($script:Results | Where-Object { $_.Status -ne "PASS" }).Count

Write-Host ""
Write-Host "==================== OZET ===================="
Write-Host "Toplam: $($script:Results.Count)   PASS: $passCount   FAIL: $failCount"
if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "Basarisiz kontroller:" -ForegroundColor Red
    foreach ($r in ($script:Results | Where-Object { $_.Status -ne "PASS" })) {
        Write-Host "  - $($r.Label)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "Tum kontroller gecti." -ForegroundColor Green
exit 0
