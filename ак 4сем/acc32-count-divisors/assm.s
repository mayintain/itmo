.data

input_addr:      .word  0x80
n:               .word  0
output_addr:     .word  0x84

one:             .word  1
count:           .word  0
i:               .word  0

.text

_start:
    load         input_addr
    load_acc
    store        n

    bgt          init

error_input:
    load_imm     -1
    store_ind    output_addr
    halt

init:
    load_imm     0
    store        count

    load         one
    store        i

loop_check:
    load         i
    sub          n
    bgt          finish

loop_body:
    load         n
    rem          i
    bnez         next_i

    load         count
    add          one
    store        count

next_i:
    load         i
    add          one
    store        i

    jmp          loop_check

finish:
    load         count
    store_ind    output_addr
    halt
