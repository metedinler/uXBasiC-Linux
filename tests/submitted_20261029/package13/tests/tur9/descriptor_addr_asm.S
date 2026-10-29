.intel_syntax noprefix
.text
.globl descriptor_addr_asm
.type descriptor_addr_asm,@function
# Linux SysV harness for the SAME emitted index-guard and address arithmetic.
# rdi=descriptor, rsi=source index, rdx=element stride; rax=element address or NULL.
# This does not exercise Win64 call setup or uXBasic's compiler.
descriptor_addr_asm:
    mov rcx, rdi
    mov rax, rsi
    test rcx, rcx
    jz .Lbad
    cmp qword ptr [rcx], 0
    je .Lbad
    mov r11, qword ptr [rcx + 8]
    cmp r11, qword ptr [rcx + 16]
    jg .Lbad
    cmp rax, r11
    jl .Lbad
    cmp rax, qword ptr [rcx + 16]
    jg .Lbad
    imul r11, rdx
    mov rcx, qword ptr [rcx]
    sub rcx, r11
    imul rax, rdx
    add rcx, rax
    mov rax, rcx
    ret
.Lbad:
    xor eax, eax
    ret
.section .note.GNU-stack,"",@progbits
