@echo off
setlocal
cd /d "%~dp0..\..\.."
if "%~1"=="" (
  echo Usage: run_emit_x64_ast_asm.bat source.bas
  exit /b 2
)
if not exist uxb\_work\native mkdir uxb\_work\native
if not exist uxb\bin\uxb.exe (
  call build_compiler_64.bat
)
uxb\bin\uxb.exe "%~1" --emit-x64-nasm --codegen-source AST --emit-x64-nasm-out "uxb\_work\native\ast_out.nasm" --x64-codegen-policy-json-out "uxb\_work\native\ast_policy.json"
endlocal
