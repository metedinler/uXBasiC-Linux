' ADIM30 POSITIVE 05 — Windows GUI via API/DLL, native-only surface
' This test is meant to prove parsing/semantic/native routing. It must not silently transpile to JS/WASM.
DECLARE FUNCTION MessageBoxA LIB "user32.dll" ALIAS "MessageBoxA" (BYVAL hwnd AS PTR, BYVAL text AS STRING, BYVAL caption AS STRING, BYVAL flags AS I32) AS I32
CALL(API, "user32.dll", "MessageBoxA", 0, "uXBasic GUI API test", "uXBasic", 0)
PRINT "GUI-API-ROUTE"
