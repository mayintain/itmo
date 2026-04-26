    .data

input_addr:      .word  0x80
output_addr:     .word  0x84
const_1:         .word  0x1
left:            .word  0
right:           .word  0

    .text
    .org 0x100

_start:
    @p input_addr a! @

    dup
    !p left
    !p right

    lit 15 >r

loop:
    @p right
    @p const_1
    and

    @p left
    -if left_zero
    lit 1
    compare_bits ;

left_zero:
    lit 0

compare_bits:
    xor
    if bits_equal

    lit 0
    @p output_addr a! !
    halt

bits_equal:
    @p left
    2*
    !p left

    @p right
    2/
    !p right

    next loop

    lit 1
    @p output_addr a! !
    halt
