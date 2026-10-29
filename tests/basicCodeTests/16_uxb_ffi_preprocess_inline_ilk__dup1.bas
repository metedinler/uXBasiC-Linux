%%DEFINE FLAG 1
%%IF FLAG
DIM preX AS I32
%%ELSE
DIM preY AS I32
%%ENDIF

IMPORT(C, "extras/uxstat/uxstat_stub.c")
INLINE("x64","nasm","sub","abi=win64;preserve=rbx,rsi,rdi,r12,r13,r14,r15;stack=16;shadow=32")
mov rax, 1
END INLINE

a = 77
CALL(DLL, "kernel32.dll", "GetTickCount", I32, a)
PRINT "ffi-call-done"
