# S-025: timeout-bounded process runner used by the compiler's --x64-mode BOTH
# real-execution comparison (backend_x64_real_execution_compare.fbs). Runs one
# built executable with stdin closed (never blocks waiting for input), captures
# stdout/stderr to files, and kills it if it runs past the timeout instead of
# hanging the compiler on a user program with an infinite loop.
#
# Exit code: the child process's own exit code, or 124 on timeout (matches the
# conventional GNU coreutils `timeout` sentinel).
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$StdoutPath,
    [Parameter(Mandatory = $true)][string]$StderrPath,
    [int]$TimeoutMs = 10000
)

$ErrorActionPreference = "Stop"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $ExePath
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.RedirectStandardInput = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$proc = [System.Diagnostics.Process]::Start($psi)
$proc.StandardInput.Close()
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()

$finished = $proc.WaitForExit($TimeoutMs)

if (-not $finished) {
    # $proc.Kill($true) (recursive tree-kill) requires .NET Core 3+; this script
    # can run under Windows PowerShell 5.1 (.NET Framework), where that overload
    # does not exist and silently no-ops inside a try/catch, leaving the runaway
    # process alive. taskkill /T /F works on every PowerShell/.NET version.
    try { & taskkill.exe /PID $proc.Id /T /F 2>&1 | Out-Null } catch {}
    try { $proc.Kill() } catch {}
    Start-Sleep -Milliseconds 200
    $partialOut = ""
    $partialErr = ""
    try { if ($stdoutTask.Wait(500)) { $partialOut = $stdoutTask.Result } } catch {}
    try { if ($stderrTask.Wait(500)) { $partialErr = $stderrTask.Result } } catch {}
    [IO.File]::WriteAllText($StdoutPath, $partialOut)
    [IO.File]::WriteAllText($StderrPath, "TIMEOUT after ${TimeoutMs}ms`n" + $partialErr)
    exit 124
}

[IO.File]::WriteAllText($StdoutPath, $stdoutTask.Result)
[IO.File]::WriteAllText($StderrPath, $stderrTask.Result)
exit $proc.ExitCode
