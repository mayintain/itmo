    .data

input_addr:      .word  0x80
output_addr:     .word  0x84

zero:            .word  0
one:             .word  1
bit_mask:        .word  1
loop_count:      .word  15

left:            .word  0
right:           .word  0

    .text
    .org 0x100

_start:
    init_input

    @p loop_count
    >r

loop:
    @p right
    @p bit_mask
    and

    @p left
    -if left_zero

    @p one
    compare_bits ;

left_zero:
    @p zero

compare_bits:
    xor
    if bits_equal

    @p zero
    write_result

bits_equal:
    @p left
    2*
    !p left

    @p right
    2/
    !p right

    next loop

    @p one
    write_result

init_input:
    @p input_addr
    a!
    @

    dup
    !p left
    !p right
    ;

write_result:
    @p output_addr
    a!
    !
    halt