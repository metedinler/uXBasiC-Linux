.intel_syntax noprefix
.text
.globl CheckRegs
.def CheckRegs; .scl 2; .type 32; .endef
CheckRegs:
    push rbx
    push r12
    push r13
    sub rsp, 48
    mov rbx, rcx
    mov [rsp+32], rbx
    mov r12, 0x1020304050607080
    mov r13, 0x1122334455667788
    call rbx
    xor eax, eax
    mov r10, 0x1020304050607080
    cmp r12, r10
    je .Lr12_ok
    or eax, 1
.Lr12_ok:
    mov r10, 0x1122334455667788
    cmp r13, r10
    je .Lr13_ok
    or eax, 2
.Lr13_ok:
    cmp rbx, [rsp+32]
    je .Lrbx_ok
    or eax, 4
.Lrbx_ok:
    add rsp, 48
    pop r13
    pop r12
    pop rbx
    ret
