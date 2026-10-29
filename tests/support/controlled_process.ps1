# Shared library-test process boundary: isolated working directory, exit code,
# bounded execution, and complete redirected output. No workspace cleanup.
function Invoke-UxbControlledProcess {
    param([string]$Exe, [string[]]$Arguments, [string]$WorkingDirectory, [int]$TimeoutSec = 240)
    $psi = [Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    if ([IO.Path]::GetExtension($Exe) -ieq '.cmd') {
        # The all-model runner can supply its own temporary batch wrapper.
        if (($Exe + ($Arguments -join '')) -match '[&|<>%^!]') { throw 'Unsafe batch-wrapper argument' }
        $psi.FileName = $env:ComSpec
        $psi.Arguments = '/d /s /c ""' + $Exe + '" ' + (($Arguments | ForEach-Object { '"' + $_ + '"' }) -join ' ') + '"'
    } else {
        foreach ($arg in $Arguments) { [void]$psi.ArgumentList.Add($arg) }
    }
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $process = [Diagnostics.Process]::Start($psi)
    try {
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $timedOut = -not $process.WaitForExit($TimeoutSec * 1000)
        if ($timedOut) { $process.Kill($true) }
        $process.WaitForExit()
        [pscustomobject]@{
            ExitCode = $process.ExitCode
            TimedOut = $timedOut
            Output = $stdout.Result + "`n" + $stderr.Result
            ElapsedSeconds = [Math]::Round($watch.Elapsed.TotalSeconds, 3)
        }
    } finally { $process.Dispose(); $watch.Stop() }
}

function Remove-UxbOwnedTemporaryDirectory {
    param([string]$Path)
    $tempPrefix = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    $target = [IO.Path]::GetFullPath($Path)
    if (-not $target.StartsWith($tempPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Temporary cleanup outside the system temporary directory: $target"
    }
    if ([IO.Directory]::Exists($target)) { [IO.Directory]::Delete($target, $true) }
}
