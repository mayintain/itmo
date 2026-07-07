    .data
buffer:          .byte 95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95,95
input_addr:      .word 0x80
output_addr:     .word 0x84
stack_top:       .word 0x1000
char_stack_top:  .word 0x0F00
overflow_value:  .word 0xcccccccc

    .text
    .org 0x100

_start:
    lui     s0, %hi(input_addr)
    addi    s0, s0, %lo(input_addr)
    lw      s0, 0(s0)

    lui     s1, %hi(output_addr)
    addi    s1, s1, %lo(output_addr)
    lw      s1, 0(s1)

    lui     s2, %hi(buffer)
    addi    s2, s2, %lo(buffer)

    lui     s3, %hi(char_stack_top)
    addi    s3, s3, %lo(char_stack_top)
    lw      s3, 0(s3)

    lui     sp, %hi(stack_top)
    addi    sp, sp, %lo(stack_top)
    lw      sp, 0(sp)

    mv      a0, s0
    mv      a1, s2
    mv      a2, s3
    jal     ra, read_input

    bnez    a1, do_overflow

    mv      a1, s1
    mv      a2, s2
    jal     ra, emit_reversed
    j       halt_program

do_overflow:
    mv      a0, s1
    jal     ra, write_overflow
    j       halt_program

read_input:
    addi    t4, zero, 0
    addi    t5, zero, 0
    addi    t6, zero, 0

read_loop:
    lb      t0, 0(a0)
    addi    t1, t0, -10
    beqz    t1, read_done

    addi    t1, t6, -31
    beqz    t1, read_overflow

    sb      t0, 0(a1)
    addi    a1, a1, 1
    addi    t6, t6, 1

    bnez    t5, read_loop
    beqz    t0, saw_zero

    addi    a2, a2, -4
    sw      t0, 0(a2)
    addi    t4, t4, 1
    j       read_loop

saw_zero:
    addi    t5, zero, 1
    j       read_loop

read_done:
    sb      zero, 0(a1)
    addi    a1, zero, 0
    j       finish_read

read_overflow:
    addi    a1, zero, 1

finish_read:
    mv      a0, t4
    mv      a3, a2
    jr      ra

emit_reversed:
    beqz    a0, write_zero_terminator

pop_loop:
    lw      t0, 0(a3)
    addi    a3, a3, 4

    sb      t0, 0(a2)
    sb      t0, 0(a1)
    addi    a2, a2, 1

    addi    a0, a0, -1
    bnez    a0, pop_loop

write_zero_terminator:
    sb      zero, 0(a2)
    jr      ra

write_overflow:
    lui     t0, %hi(overflow_value)
    addi    t0, t0, %lo(overflow_value)
    lw      t0, 0(t0)
    sw      t0, 0(a0)
    jr      ra

halt_program:
    halt