.equ OUT, 0xFF01
.section text
.org 0
_start:
    mov r0, 0
    mov r1, 200
loop:
    cmp r0, r1
    jg done
    add r0, 1
    add r2, r0
    add r3, r2
    jmp loop
done:
    print_num r0
    print_cstr newline
    halt
.section data
.org 100
newline:
    .cstr "\n"
