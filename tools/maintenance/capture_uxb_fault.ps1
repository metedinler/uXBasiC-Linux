[CmdletBinding()]
param(
    [string]$Executable = '',
    [string[]]$Arguments = @(),
    [string]$WorkingDirectory = '',
    [string]$OutputDirectory = '',
    [ValidateRange(1,7200)][int]$TimeoutSeconds = 120
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if (!$WorkingDirectory) { $WorkingDirectory = $root }
$WorkingDirectory = (Resolve-Path -LiteralPath $WorkingDirectory).Path
if (!$OutputDirectory) { $OutputDirectory = Join-Path $root ('reports/fault_capture/' + (Get-Date -Format 'yyyyMMdd_HHmmss_ffff')) }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path

if (-not ('UxbFaultMemoryProbe' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UxbFaultMemoryProbe {
 [StructLayout(LayoutKind.Sequential)]
 public struct MemoryStatus {
  public uint length, load;
  public ulong totalPhysical, availablePhysical, totalCommit, availableCommit;
  public ulong totalVirtual, availableVirtual, availableExtendedVirtual;
 }
 [DllImport("kernel32.dll", SetLastError=true)]
 static extern bool GlobalMemoryStatusEx(ref MemoryStatus state);
 public static MemoryStatus Read() {
  MemoryStatus state = new MemoryStatus(); state.length = (uint)Marshal.SizeOf(state);
  if (!GlobalMemoryStatusEx(ref state)) throw new System.ComponentModel.Win32Exception();
  return state;
 }
}
'@
}
function Read-MemorySnapshot {
    try { return @{status='ok'; values=[UxbFaultMemoryProbe]::Read()} }
    catch { return @{status='unavailable'; error=$_.Exception.Message} }
}
$started = Get-Date
$record = [ordered]@{
    schema='uxb.fault_capture.v1'; started=$started.ToString('o'); finished=''
    memoryBefore=Read-MemorySnapshot; memoryAfter=$null; process=$null
    applicationEvents=@(); resourceEvents=@(); eventReadErrors=@()
    compilerHashes=@(); processes=@()
    limitation='Global memory changes include other applications. A clean run does not prove absence of a leak or corruption.'
}
if ($Executable) {
    $exe = (Resolve-Path -LiteralPath $Executable).Path
    $info = [Diagnostics.ProcessStartInfo]::new()
    if (-not $info.PSObject.Properties['ArgumentList']) { throw 'Run this collector with PowerShell 7 or newer.' }
    $info.FileName=$exe; $info.WorkingDirectory=$WorkingDirectory
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process=[Diagnostics.Process]::new(); $process.StartInfo=$info
    $watch=[Diagnostics.Stopwatch]::StartNew()
    $peakPrivate=0L; $peakWorking=0L; $timedOut=$false; $memorySamples=0
    try {
        if (!$process.Start()) { throw 'Probe process could not start.' }
        $pidValue=$process.Id
        $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
        while (!$process.WaitForExit(200)) {
            $process.Refresh()
            $peakPrivate=[Math]::Max($peakPrivate,$process.PrivateMemorySize64)
            $peakWorking=[Math]::Max($peakWorking,$process.PeakWorkingSet64)
            $memorySamples++
            if ($watch.Elapsed.TotalSeconds -ge $TimeoutSeconds) {
                $timedOut=$true
                # Only this collector's own child is stopped on timeout.
                $process.Kill($true); $process.WaitForExit(); break
            }
        }
        $watch.Stop()
        $stdout.Result | Set-Content -LiteralPath (Join-Path $OutputDirectory 'stdout.txt') -Encoding utf8
        $stderr.Result | Set-Content -LiteralPath (Join-Path $OutputDirectory 'stderr.txt') -Encoding utf8
        $exitUnsigned=[BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$process.ExitCode),0)
        $record.process=@{executable=$exe;arguments=$Arguments;pid=$pidValue;exit=$process.ExitCode;exitHex=('0x{0:X8}' -f $exitUnsigned);timeout=$timedOut;seconds=$watch.Elapsed.TotalSeconds;memorySamples=$memorySamples;peakPrivateSampled=$(if($memorySamples){$peakPrivate}else{$null});peakWorkingSet=$(if($memorySamples){$peakWorking}else{$null});sha256=(Get-FileHash -LiteralPath $exe).Hash}
    } finally { $process.Dispose() }
}
$record.memoryAfter=Read-MemorySnapshot
foreach ($query in @(
    @{Key='applicationEvents';Filter=@{LogName='Application';Id=1000,1001,1002;StartTime=$started.AddMinutes(-2)}},
    @{Key='resourceEvents';Filter=@{LogName='System';ProviderName='Microsoft-Windows-Resource-Exhaustion-Detector';StartTime=$started.AddMinutes(-2)}}
)) {
    try {
        $events=@(Get-WinEvent -FilterHashtable $query.Filter -ErrorAction Stop)
        if ($query.Key -eq 'applicationEvents') { $events=@($events | Where-Object {$_.Message -match '(?i)uxb|program.exe|fbc64.exe|nasm.exe|cc1.exe'}) }
        $record[$query.Key]=@($events | Select-Object -First 30 TimeCreated,Id,ProviderName,Message)
    } catch { $record.eventReadErrors += @{channel=$query.Key;error=$_.Exception.Message} }
}
foreach ($file in @('bin/uxb.exe','bin/uxb_runtime.dll','bin/uxffi.dll')) {
    $path=Join-Path $root $file
    if (Test-Path -LiteralPath $path) { $record.compilerHashes += @{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash} }
}
$record.processes=@(Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -match '^(uxb|program|fbc64|nasm|ld|claude|ollama|ollama app)$'} | Select-Object ProcessName,Id,PrivateMemorySize64,WorkingSet64)
$record.finished=(Get-Date).ToString('o')
$path=Join-Path $OutputDirectory 'capture.json'
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding utf8
Write-Output $path
if ($record.process -and ($record.process.timeout -or $record.process.exit -ne 0)) { exit 1 }
