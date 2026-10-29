DECLARE FUNCTION puts CDECL LIB "msvcrt.dll" ALIAS "puts" (BYVAL s AS STRPTR) AS I32
IMPORT(C, "native/uxb_probe.c")
IMPORT(CPP, "native/uxb_probe.cpp")
IMPORT(ASM, "native/uxb_probe.asm")
INLINE(x64, nasm, ABI=WIN64)
; inline route probe
END INLINE
CALL(DLL, "msvcrt.dll", "puts", "STRPTR->I32", "FFI_ROUTE_OK")
CALL(API, "kernel32.dll", "GetTickCount", "->U32")
PRINT "FFI_NATIVE_ROUTE_OK"
