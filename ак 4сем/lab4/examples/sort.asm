.equ IN, 0xFF00
.equ OUT, 0xFF01

.section text
.org 0

_start:
    ; Input format:
    ; first character is count
    ; next characters are one-digit numbers
    ; example: 514325 means count=5, array=[1,4,3,2,5]

    ; read count
    mov r0, [IN]
    sub r0, 48
    mov [count], r0

    ; read array
    mov r0, 0
    mov [j], r0

read_loop:
    mov r0, [j]
    mov r1, [count]
    cmp r0, r1
    jz sort_start

    mov r2, [IN]
    sub r2, 48

    mov r3, buf
    add r3, r0
    mov [r3], r2

    add r0, 1
    mov [j], r0
    jmp read_loop

sort_start:
    ; bubble sort
    mov r0, 0
    mov [i], r0

outer:
    ; if i == count - 1, sorting is finished
    mov r0, [count]
    sub r0, 1
    mov r1, [i]
    cmp r1, r0
    jz print_start

    mov r0, 0
    mov [j], r0

inner:
    ; limit = count - 1 - i
    mov r0, [count]
    sub r0, 1
    mov r1, [i]
    sub r0, r1

    mov r1, [j]
    cmp r1, r0
    jz outer_next

    ; addr = buf + j
    mov r0, buf
    mov r1, [j]
    add r0, r1

    ; r2 = buf[j]
    ; r3 = buf[j + 1]
    mov r2, [r0]
    add r0, 1
    mov r3, [r0]

    ; if r2 <= r3, no swap
    cmp r2, r3
    jl no_swap
    jz no_swap

    ; swap
    ; current r0 = buf + j + 1
    mov [r0], r2
    sub r0, 1
    mov [r0], r3

no_swap:
    mov r0, [j]
    add r0, 1
    mov [j], r0
    jmp inner

outer_next:
    mov r0, [i]
    add r0, 1
    mov [i], r0
    jmp outer

print_start:
    mov r0, 0
    mov [j], r0

print_loop:
    mov r0, [j]
    mov r1, [count]
    cmp r0, r1
    jz done

    mov r2, buf
    add r2, r0
    mov r3, [r2]

    ; convert digit 0..9 to ASCII character
    add r3, 48
    mov [OUT], r3

    add r0, 1
    mov [j], r0
    jmp print_loop

done:
    print_cstr newline
    halt

.section data
.org 500

count:
    .word 0

i:
    .word 0

j:
    .word 0

buf:
    .space 16

newline:
    .cstr "\n"