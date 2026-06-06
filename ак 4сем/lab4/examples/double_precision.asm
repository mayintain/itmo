.equ OUT, 0xFF01

.section text
.org 0

_start:
    ; 64-bit addition:
    ; high:low = 0x00000000:0xFFFFFFFF
    ; add 1
    ; expected result = 0x00000001:0x00000000

    mov r0, 0
    mov r1, 0xFFFFFFFF
    mov r2, 1

    ; low = low + 1
    add r1, r2

    ; if low == 0 after addition, carry happened
    cmp r1, 0
    jnz no_carry

    ; carry: high = high + 1
    add r0, 1

no_carry:
    print_cstr label_hi
    print_num r0
    print_cstr label_lo
    print_num r1
    print_cstr label_eq
    print_num r0
    print_cstr sep
    print_num r1
    print_cstr newline
    halt

.section data
.org 300

label_hi:
    .cstr "high="

label_lo:
    .cstr " low="

label_eq:
    .cstr "\nresult="

sep:
    .cstr ":"

newline:
    .cstr "\n"