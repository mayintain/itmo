    .data
    .org 0x100

input_addr:       .word  0x80
output_addr:      .word  0x84
overflow_value:   .word  0xcccccccc
current_number:   .word  0
in_number:        .word  0
stack_top:        .word  0x800
stack_counter:    .word  0
buffer:           .byte  0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0

buffer_limit:     .word 64
ten_value:        .word 10
one_value:        .word 1
two_value:        .word 2
space_value:      .word 32
plus_value:       .word 43
minus_value:      .word 45
multiply_value:   .word 42
divide_value:     .word 47
ascii_zero:       .word 48
ascii_nine:       .word 57
zero_value:       .word 0
error_value:      .word -1


    .text
    .org 0x200

_start:
    movea.l  stack_top, A7
    movea.l  (A7), A7

    movea.l  input_addr, A0
    movea.l  (A0), A0

    movea.l  output_addr, A1
    movea.l  (A1), A1

    movea.l  current_number, A2
    movea.l  in_number, A3
    movea.l  stack_counter, A4
    movea.l  overflow_value, A5

    movea.l buffer_limit, A6
    move.l (A6), D6

    movea.l  ten_value, A6
    move.l   (A6), D5

    movea.l  one_value, A6
    move.l   (A6), D4

    movea.l  space_value, A6
    move.l   (A6), D3

    movea.l  buffer, A6
    clr.l D7

read_line_loop:
    cmp.l    D6, D7
    bge      overflow_case

    move.b   (A0), D0
    cmp.b    D5, D0
    beq      parse_init

    move.b   D0, (A6)+
    add.l    D4, D7
    jmp      read_line_loop

parse_init:
    move.b   D5, (A6)
    movea.l  buffer, A0

read_next_symb:
    move.b   (A0)+, D0

    cmp.b    D5, D0
    beq      end_input

    cmp.b    D3, D0
    beq      space_case

    movea.l  plus_value, A6
    jsr      compare_equal_symbol
    beq      plus_symb

    movea.l  minus_value, A6
    jsr      compare_equal_symbol
    beq      minus_symb

    movea.l  multiply_value, A6
    jsr      compare_equal_symbol
    beq      multipl_symb

    movea.l  divide_value, A6
    jsr      compare_equal_symbol
    beq      div_symb

    movea.l  ascii_zero, A6
    jsr      compare_order_symbol
    blt      error_case

    movea.l  ascii_nine, A6
    jsr      compare_order_symbol
    bgt      error_case

digit_symb:
    clr.l    D1
    move.b   D0, D1
    movea.l  ascii_zero, A6
    move.b   (A6), D2
    sub.b    D2, D1
    move.l   (A2), D2
    mul.l    D5, D2
    bvs      overflow_case
    add.l    D1, D2
    bvs      overflow_case
    move.l   D2, (A2)
    move.l   D4, (A3)
    jmp      read_next_symb

space_case:
    move.l   (A3), D1
    sub.l    D4, D1
    bne      read_next_symb

    move.l   (A2), -(A7)
    jsr      clear_number_state

    jsr      increment_stack_counter
    jmp      read_next_symb

end_input:
    move.l   (A3), D1
    sub.l    D4, D1
    bne      finish_expression

    move.l   (A2), -(A7)
    jsr      clear_number_state
    jsr      increment_stack_counter

finish_expression:
    move.l   (A4), D0
    sub.l    D4, D0
    bne      error_case

    move.l   (A7)+, D0
    move.l   D0, (A1)
    jmp      halt_program

plus_symb:
    jsr      check_two_operands

    move.l   (A7)+, D1
    move.l   (A7)+, D2
    
    add.l    D1, D2
    bvs      overflow_case
    jmp      finish_binary_op

minus_symb:
    jsr      check_two_operands

    move.l   (A7)+, D1
    move.l   (A7)+, D2

    sub.l    D1, D2
    bvs      overflow_case
    jmp      finish_binary_op

multipl_symb:
    jsr      check_two_operands

    move.l   (A7)+, D1
    move.l   (A7)+, D2

    mul.l    D1, D2
    bvs      overflow_case
    jmp      finish_binary_op

div_symb:
    jsr      check_two_operands

    move.l   (A7)+, D1
    move.l   (A7)+, D2

    movea.l  zero_value, A6
    move.l   (A6), D0
    cmp.l    D0, D1
    beq      error_case

    div.l    D1, D2
    bvs      overflow_case
    jmp      finish_binary_op

finish_binary_op:
    move.l   D2, -(A7)
    jsr      decrement_stack_counter
    jmp      read_next_symb

clear_number_state:
    movea.l  zero_value, A6
    move.l   (A6), D2
    move.l   D2, (A2)
    move.l   D2, (A3)
    rts

compare_equal_symbol:
    move.b   (A6), D1
    cmp.b    D1, D0
    rts

compare_order_symbol:
    move.b   (A6), D1
    move.b   D0, D2
    sub.b    D1, D2
    rts

decrement_stack_counter:
    move.l   (A4), D0
    sub.l    D4, D0
    move.l   D0, (A4)
    rts

increment_stack_counter:
    move.l   (A4), D1
    add.l    D4, D1
    move.l   D1, (A4)
    rts

check_two_operands:
    move.l   (A4), D0
    movea.l  two_value, A6
    move.l   (A6), D1
    sub.l    D1, D0
    blt      error_case
    rts

overflow_case:
    move.l   (A5), D0
    move.l   D0, (A1)
    jmp      halt_program

error_case:
    movea.l  error_value, A6
    move.l   (A6), D0
    move.l   D0, (A1)
    jmp      halt_program

halt_program:
    halt
