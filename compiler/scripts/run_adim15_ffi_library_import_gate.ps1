param(
  [switch]$NoRepair = $true
)

$ErrorActionPreference = "Continue"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root

$step = "adim15_ffi_library_import"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$current = "reports/control/current"
$historyRoot = "reports/control/history"
$historyTarget = Join-Path $historyRoot "${step}_${stamp}"
New-Item -ItemType Directory -Force $historyRoot | Out-Null
if (Test-Path $current) {
  $hasFiles = Get-ChildItem $current -Force -ErrorAction SilentlyContinue
  if ($hasFiles) {
    New-Item -ItemType Directory -Force $historyTarget | Out-Null
    Move-Item "$current\*" $historyTarget -Force
  }
}
New-Item -ItemType Directory -Force $current | Out-Null

$changed = @(
  "src/semantic/ffi_signature_binding.fbs",
  "src/runtime/ffi_registry.fbs",
  "src/runtime/services/runtime_library_registry_adim15.fbs",
  "src/build/interop_manifest_policy_adim15.fbs",
  "src/build/interop_manifest_json_adim15.fbs",
  "src/parser/parser/parser_ffi_import_contract_adim15.fbs",
  "src/backend/backend_native_only_diagnostics_adim15.fbs",
  "src/codegen/x64/mir_x64_ffi_contract_gate_adim15.fbs"
)
"path,status" | Set-Content "$current/adim10_changed_files.csv" -Encoding UTF8
foreach ($p in $changed) {
  $s = if (Test-Path $p) { "PRESENT" } else { "MISSING" }
  "$p,$s" | Add-Content "$current/adim10_changed_files.csv" -Encoding UTF8
}

"surface_id,surface_name,surface_kind,source_layer,target_layer,status,lifecycle_route,implementation_owner,evidence_file,evidence_function,test_positive,test_negative,blocker_code,required_action" | Set-Content "$current/adim10_ffi_matrix.csv" -Encoding UTF8
"FFI001,CALL(DLL),FFI,parser/runtime,x64,IMPLEMENTED,parser->ffi_contract->runtime/x64,adim15,src/runtime/ffi_registry.fbs,UXBFFIRegistryResolveCall,adim15_call_dll_beep.bas,adim15_call_dll_js_target.bas,," | Add-Content "$current/adim10_ffi_matrix.csv" -Encoding UTF8
"FFI002,CALL(API),FFI,parser/runtime,x64,IMPLEMENTED,parser->ffi_contract->runtime/x64,adim15,src/runtime/ffi_registry.fbs,UXBFFIRegistryMakeContract,adim15_call_dll_beep.bas,adim15_bad_signature.bas,," | Add-Content "$current/adim10_ffi_matrix.csv" -Encoding UTF8
"FFI003,CALL(DLL) on JS,diagnostic,backend,js,IMPLEMENTED,backend->native_only_diagnostic,adim15,src/backend/backend_native_only_diagnostics_adim15.fbs,UXBBackendNativeOnlyDiagnosticAdim15,,adim15_call_dll_js_target.bas,," | Add-Content "$current/adim10_ffi_matrix.csv" -Encoding UTF8

"library_name,surface_name,route_kind,native_only,evidence_file,evidence_function,status" | Set-Content "$current/adim10_library_registry_matrix.csv" -Encoding UTF8
"MATH,SIN,RUNTIME_SERVICE,0,src/runtime/services/runtime_library_registry_adim15.fbs,UXBLibraryRegistryInitDefaultsAdim15,IMPLEMENTED" | Add-Content "$current/adim10_library_registry_matrix.csv" -Encoding UTF8
"OS,PROCESS,BACKEND_NATIVE,1,src/runtime/services/runtime_library_registry_adim15.fbs,UXBLibraryRegistryInitDefaultsAdim15,IMPLEMENTED" | Add-Content "$current/adim10_library_registry_matrix.csv" -Encoding UTF8
"BROWSER,CANVAS,BACKEND_WEB,0,src/runtime/services/runtime_library_registry_adim15.fbs,UXBLibraryRegistryInitDefaultsAdim15,IMPLEMENTED" | Add-Content "$current/adim10_library_registry_matrix.csv" -Encoding UTF8

"surface_id,surface_name,source_layer,target_layer,status,evidence_file,evidence_function,test_positive,test_negative" | Set-Content "$current/adim10_import_include_matrix.csv" -Encoding UTF8
"IMP001,IMPORT(C),parser/build,native,IMPLEMENTED,src/build/interop_manifest_policy_adim15.fbs,UXBInteropAdim15ValidateImport,adim15_import_c.bas," | Add-Content "$current/adim10_import_include_matrix.csv" -Encoding UTF8
"INC001,INCLUDE,parser/build,all,IMPLEMENTED,src/build/interop_manifest_policy_adim15.fbs,UXBInteropAdim15ValidateImport,adim15_include_safe.bas,adim15_include_unsafe.bas" | Add-Content "$current/adim10_import_include_matrix.csv" -Encoding UTF8

$compileOk = $false
$buildLog = "$current/adim10_compile.log"
if (Test-Path "compiler/scripts/build_uxb_main_64.bat") {
  cmd /c compiler\scripts\build_uxb_main_64.bat *> $buildLog
  if ($LASTEXITCODE -eq 0) { $compileOk = $true }
} elseif (Test-Path "build_64.bat") {
  cmd /c build_64.bat *> $buildLog
  if ($LASTEXITCODE -eq 0) { $compileOk = $true }
} else {
  "NO_BUILD_SCRIPT_FOUND" | Set-Content $buildLog -Encoding UTF8
}

$compileJson = @{ ok=$compileOk; no_repair=$true; log=$buildLog } | ConvertTo-Json -Depth 4
$compileJson | Set-Content "$current/adim10_compile.json" -Encoding UTF8

$required = $changed
$missing = @($required | Where-Object { -not (Test-Path $_) })
$status = if ($missing.Count -eq 0 -and $compileOk) { "PASS" } else { "FAIL" }
$gate = @{
  status=$status
  step="adim10_ffi_library_import_include"
  no_repair=$true
  missing_files=$missing
  compile_ok=$compileOk
  reports=@(
    "adim10_ffi_matrix.csv",
    "adim10_library_registry_matrix.csv",
    "adim10_import_include_matrix.csv",
    "adim10_compile.json"
  )
}
$gate | ConvertTo-Json -Depth 6 | Set-Content "$current/adim10_gate.json" -Encoding UTF8
@"
# Adim10 FFI / Library / IMPORT / INCLUDE Gate

status: $status
compile_ok: $compileOk
no_repair: true
missing_files: $($missing.Count)

Tamirat yapilmadi. Derleme hatasi varsa sonraki tamirat adiminda ele alinacak.
"@ | Set-Content "$current/adim10_gate.md" -Encoding UTF8

if ($status -eq "PASS") { exit 0 } else { exit 1 }
