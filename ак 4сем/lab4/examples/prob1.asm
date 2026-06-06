.section text
.org 0

_start:
    ; Euler problem 4:
    ; largest palindrome made from the product of two 3-digit numbers.
    ; Expected result: 906609.

    mov r0, 0
    mov [max_pal], r0

    mov r0, 999
    mov [i], r0

outer:
    ; Stop if i < 100
    mov r0, [i]
    cmp r0, 100
    jl outer_end

    ; If i * 999 <= max_pal, no better result is possible.
    mov r0, [i]
    mov r1, 999
    mul r0, r1
    mov r1, [max_pal]
    cmp r0, r1
    jl outer_end
    jz outer_end

    ; j = 999
    mov r0, 999
    mov [j], r0

inner:
    ; Stop inner loop when j < i.
    mov r0, [j]
    mov r1, [i]
    cmp r0, r1
    jl outer_next

    ; p = i * j
    mov r0, [i]
    mov r1, [j]
    mul r0, r1
    mov [p], r0

    ; If p <= max_pal, further j values are useless.
    mov r0, [p]
    mov r1, [max_pal]
    cmp r0, r1
    jl outer_next
    jz outer_next

    ; n = p
    mov r0, [p]
    mov [n], r0

    ; rev = 0
    mov r0, 0
    mov [rev], r0

pal_loop:
    ; while n != 0
    mov r0, [n]
    cmp r0, 0
    jz pal_done

    ; digit = n % 10
    mov r0, [n]
    mov r1, 10
    mod r0, r1
    mov [digit], r0

    ; rev = rev * 10 + digit
    mov r0, [rev]
    mov r1, 10
    mul r0, r1
    mov r1, [digit]
    add r0, r1
    mov [rev], r0

    ; n = n / 10
    mov r0, [n]
    mov r1, 10
    div r0, r1
    mov [n], r0

    jmp pal_loop

pal_done:
    ; if rev == p, max_pal = p
    mov r0, [rev]
    mov r1, [p]
    cmp r0, r1
    jnz inner_next

    mov r0, [p]
    mov [max_pal], r0

inner_next:
    ; j = j - 1
    mov r0, [j]
    sub r0, 1
    mov [j], r0
    jmp inner

outer_next:
    ; i = i - 1
    mov r0, [i]
    sub r0, 1
    mov [i], r0
    jmp outer

outer_end:
    print_num [max_pal]
    print_cstr newline
    halt

.section data
.org 400

max_pal:
    .word 0

i:
    .word 0

j:
    .word 0

p:
    .word 0

n:
    .word 0

rev:
    .word 0

digit:
    .word 0

newline:
    .cstr "\n"