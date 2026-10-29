# MIR Full JSON v2 testi

Aynı CLI seçeneği kullanılır:

```powershell
.\bin\uxb.exe .\tests\mir_full_json_v2\mir_full_json_v2_smoke.uxb `
  --mir-full-json-out .\reports\mir_full_json_v2\mir_full_json_v2_smoke.json `
  --quiet
```

Yalnız statik yama kontrolü:

```powershell
python .\tests\mir_full_json_v2\verify_mir_full_json_v2.py --root .
```

Build yapmadan mevcut `uxb.exe` ile tam smoke:

```powershell
pwsh .\tests\mir_full_json_v2\run_mir_full_json_v2_smoke.ps1 -SkipBuild -Uxb .\bin\uxb.exe
```

Build ve smoke birlikte:

```powershell
pwsh .\tests\mir_full_json_v2\run_mir_full_json_v2_smoke.ps1
```
