.equ OUT, 0xFF01
.section text
.org 0
_start:
    print_cstr msg
    halt
.section data
.org 100
msg:
    .cstr "Hello, world!\n"
