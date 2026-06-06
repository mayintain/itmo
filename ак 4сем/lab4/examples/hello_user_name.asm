.equ OUT, 0xFF01

.section text
.org 0

_start:
    print_cstr question
    read_cstr name, 32
    print_cstr hello
    print_cstr name
    print_cstr bang
    print_cstr newline
    halt

.section data
.org 200

question:
    .cstr "What is your name?\n"

hello:
    .cstr "Hello, "

bang:
    .cstr "!"

name:
    .space 32

newline:
    .cstr "\n"