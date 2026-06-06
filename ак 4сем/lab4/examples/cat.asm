.equ IN, 0xFF00
.equ OUT, 0xFF01
.section text
.org 0
_start:
loop:
    mov r0, [IN]
    cmp r0, 0
    jz end
    mov [OUT], r0
    jmp loop
end:
    halt
