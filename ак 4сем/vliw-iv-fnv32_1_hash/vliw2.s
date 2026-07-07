.data
input_addr:          .word  0x80
output_addr:         .word  0x84

fnv_prime:           .word  0x01000193
fnv_offset_basis:    .word  0x811C9DC5

    .text
    .org 0x100
_start:
    nop                                  / nop                                  / lw a0, 0(zero)   / nop
    nop                                  / nop                                  / lw a1, 4(zero)   / nop
    nop                                  / nop                                  / lw s0fp, 8(zero) / nop
    nop                                  / nop                                  / lw t1, 12(zero)  / nop
    nop                                  / nop                                  / lb t0, 0(a0)     / nop

hash_loop:
    mul t4, t1, s0fp                     / nop                                  / nop              / beqz t0, hash_done
    xor t1, t4, t0                       / nop                                  / lb t0, 0(a0)     / j hash_loop

hash_done:
    nop                                  / nop                                  / sw t1, 0(a1)     / nop
    nop                                  / nop                                  / nop              / halt