# uxsdl3 sarmalayici uretici (S-052): runtime_ext\uxraylib\uxsdl3_adapter.c icindeki `UX_EXPORT` islevlerinden, libsx\uxsdl3\uxsdl3.bas
# dosyasinda HENUZ SARILMAMIS olanlar icin `CALL(DLL, ...)` sarmalayicilari uretir (yeni islev eklenince: uret, cikti dosyasini
# uxsdl3.bas'a ekle, sonra `python tools\library_tools\uxb_library_abi.py --root .` ile imzalari C ile karsilastir).
# Kullanim: pwsh tools\library_tools\gen_uxsdl3_wrappers.ps1 -CFile <adapter.c> -BasFile <uxsdl3.bas> -OutFile <yeni_sarmalayicilar.bas>
# Adlandirma: uxsdl3_get_window_title -> GetWindowTitle (ns/ms/id/bmp... buyuk harfli); paramRename/overrides tablolari sabit adlari yonetir.
# DIKKAT: buyuk harfe cevirmede ToUpperInvariant() kullanilir; tr-TR kulturunde ToUpper() 'i' harfini 'İ' yapip sozcukleri bozar.
# Parametre adlari `type`, `loop`, `ball` gibi uXBasic anahtar sozcuklerine (S-128) carpiyorsa paramRename ile degistirilir.
param([string]$CFile, [string]$BasFile, [string]$OutFile)
$c = [System.IO.File]::ReadAllText($CFile)
$bas = [System.IO.File]::ReadAllText($BasFile)
$existing = New-Object System.Collections.Generic.HashSet[string]
foreach ($m in [regex]::Matches($bas, '"(uxsdl3_[a-z0-9_]+)"')) { [void]$existing.Add($m.Groups[1].Value) }
$overrides = @{
  "uxsdl3_sound_create_tone" = "CreateTone"; "uxsdl3_sound_pause" = "PauseSound"; "uxsdl3_sound_resume" = "ResumeSound"
  "uxsdl3_sound_is_playing" = "IsSoundPlaying"; "uxsdl3_sound_is_paused" = "IsSoundPaused"
  "uxsdl3_sound_set_loop" = "SetSoundLoop"; "uxsdl3_sound_get_loop" = "GetSoundLoop"
  "uxsdl3_sound_set_volume" = "SetSoundVolume"; "uxsdl3_sound_get_volume" = "GetSoundVolume"
  "uxsdl3_sound_length_ms" = "SoundLengthMs"; "uxsdl3_sound_remaining_ms" = "SoundRemainingMs"
  "uxsdl3_sound_frequency" = "SoundFrequency"; "uxsdl3_sound_channels" = "SoundChannels"
}
$tokenMap = @{ "ns"="NS"; "ms"="Ms"; "id"="Id"; "bmp"="BMP"; "led"="LED"; "cpu"="CPU"; "ram"="RAM"; "mb"="MB"; "tv"="TV"; "rgba"="RGBA"; "vsync"="VSync"; "dz"="DZ" }
$paramRename = @{ "type"="kind"; "loop"="looping"; "ball"="ballIndex" }
function PascalName([string]$cname) {
  if ($overrides.ContainsKey($cname)) { return $overrides[$cname] }
  $parts = $cname.Substring(7) -split '_'
  $r = ""
  foreach ($p in $parts) { if ($tokenMap.ContainsKey($p)) { $r += $tokenMap[$p] } else { $r += $p.Substring(0,1).ToUpperInvariant() + $p.Substring(1) } }
  return $r
}
function MapType([string]$t) {
  $t = ($t -replace '\s+',' ').Trim()
  switch ($t) {
    "int" { return @("I32","I32") }
    "unsigned int" { return @("U32","U32") }
    "long long" { return @("I64","I64") }
    "unsigned long long" { return @("U64","U64") }
    "double" { return @("F64","F64") }
    "const char *" { return @("STRING","STRPTR") }
    "void" { return @("VOID","VOID") }
    default { throw "bilinmeyen tip: [$t]" }
  }
}
$ms = [regex]::Matches($c, '(?m)^UX_EXPORT\s+([^\(\r\n]*?[\s\*])(\w+)\s*\(([^)]*)\)')
$sb = New-Object System.Text.StringBuilder
$count = 0; $skipped = 0
$usedNames = New-Object System.Collections.Generic.HashSet[string]
foreach ($m in $ms) {
  $cname = $m.Groups[2].Value
  if ($existing.Contains($cname)) { $skipped++; continue }
  $retC = $m.Groups[1].Value.Trim()
  $ret = MapType $retC
  # parametreler
  $plist = @()
  $ptxt = $m.Groups[3].Value.Trim()
  if ($ptxt -ne "void" -and $ptxt -ne "") {
    foreach ($part in ($ptxt -split ',')) {
      $pt = ($part -replace '\s+',' ').Trim()
      $mm = [regex]::Match($pt, '^(.*?[\s\*])(\w+)$')
      $ptype = MapType $mm.Groups[1].Value
      $pname = $mm.Groups[2].Value
      if ($paramRename.ContainsKey($pname)) { $pname = $paramRename[$pname] }
      $plist += ,@($pname, $ptype[0], $ptype[1])
    }
  }
  # onceki yorum
  $before = $c.Substring([Math]::Max(0, $m.Index - 1800), [Math]::Min(1800, $m.Index))
  $cm = [regex]::Match($before, '(?s)(/\*(?:(?!\*/).)*\*/)[ \t]*\r?\n\s*$')
  $doc = @()
  if ($cm.Success) {
    $body = $cm.Groups[1].Value
    if ($body -notmatch '^/\*\s*(----|====)') {
      $inner = $body.Substring(2, $body.Length - 4)
      foreach ($ln in ($inner -split "`r?`n")) { $t = $ln.Trim(); if ($t -ne "") { $doc += "' " + $t } }
    }
  }
  $wname = PascalName $cname
  if (-not $usedNames.Add($wname)) { throw "yinelenen sarmalayici adi: $wname ($cname)" }
  if ($bas -match "(?im)^\s*(FUNCTION|SUB)\s+$wname\s*\(") { throw "elle yazilmis ad cakismasi: $wname ($cname)" }
  foreach ($d in $doc) { [void]$sb.AppendLine($d) }
  $sig = ($plist | ForEach-Object { "$($_[0]) AS $($_[1])" }) -join ", "
  $types = ($plist | ForEach-Object { $_[2] }) -join ","
  $args = ($plist | ForEach-Object { if ($_[2] -eq "U32") { "U32($($_[0]))" } else { $_[0] } }) -join ", "
  $callTail = ""
  if ($plist.Count -gt 0) { $callTail = ", `"$types`", $args" }
  if ($ret[0] -eq "VOID") {
    [void]$sb.AppendLine("SUB $wname($sig)")
    [void]$sb.AppendLine("    CALL(DLL, `"uxsdl3.dll`", `"$cname`", VOID, CDECL$callTail)")
    [void]$sb.AppendLine("END SUB")
  } else {
    [void]$sb.AppendLine("FUNCTION $wname($sig) AS $($ret[0])")
    [void]$sb.AppendLine("    RETURN CALL(DLL, `"uxsdl3.dll`", `"$cname`", $($ret[1]), CDECL$callTail)")
    [void]$sb.AppendLine("END FUNCTION")
  }
  $count++
}
[System.IO.File]::WriteAllText($OutFile, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
"uretilen: $count  atlanan(zaten var): $skipped  toplam C: $($ms.Count)"