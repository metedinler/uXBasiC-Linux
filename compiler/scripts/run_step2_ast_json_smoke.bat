@echo off
setlocal
cd /d "%~dp0..\.."
if not exist reports\step2 mkdir reports\step2
bin\uxb.exe tests\basicCodeTests\1__dup1.bas --ast-json-out reports\step2\smoke.ast.json --ast-contract-json-out reports\step2\smoke.ast_contract_report.json --ast-contract-check
endlocal
