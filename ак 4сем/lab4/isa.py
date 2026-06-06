"""Instruction Set Architecture: opcodes, encoding, binary I/O, disassembly."""

from __future__ import annotations

import struct
from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

WORD_SIZE = 4
MEMORY_SIZE = 0x10000  # 64K words

# Memory-mapped I/O (word addresses)
IN_PORT = 0xFF00
OUT_PORT = 0xFF01


class Opcode(IntEnum):
    HALT = 0
    MOV = 1
    ADD = 2
    SUB = 3
    MUL = 4
    DIV = 5
    MOD = 6
    CMP = 7
    JMP = 8
    JZ = 9
    JNZ = 10
    JG = 11
    JL = 12
    PRINT_CSTR = 13
    READ_CSTR = 14
    PRINT_NUM = 15


class OperandType(IntEnum):
    NONE = 0
    REG = 1
    IMM = 2
    MEM = 3
    LABEL = 4


class Register(IntEnum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3


REG_NAMES = {f"r{i}": Register(i) for i in range(4)}
OPCODE_NAMES = {op.name.lower(): op for op in Opcode}


@dataclass
class DecodedInstruction:
    address: int
    opcode: Opcode
    op1_type: OperandType
    op1_reg: int
    op2_type: OperandType
    op2_reg: int
    words: list[int]

    @property
    def length(self) -> int:
        return len(self.words)


def encode_header(
    opcode: Opcode,
    op1_type: OperandType = OperandType.NONE,
    op1_reg: int = 0,
    op2_type: OperandType = OperandType.NONE,
    op2_reg: int = 0,
) -> int:
    return (
        (int(opcode) << 24)
        | (int(op1_type) << 20)
        | (op1_reg << 16)
        | (int(op2_type) << 12)
        | (op2_reg << 8)
    ) & 0xFFFFFFFF


def decode_header(word: int) -> tuple[Opcode, OperandType, int, OperandType, int]:
    opcode = Opcode((word >> 24) & 0xFF)
    op1_type = OperandType((word >> 20) & 0xF)
    op1_reg = (word >> 16) & 0xF
    op2_type = OperandType((word >> 12) & 0xF)
    op2_reg = (word >> 8) & 0xF
    return opcode, op1_type, op1_reg, op2_type, op2_reg


def sign_extend_imm(value: int) -> int:
    value &= 0xFFFFFFFF
    if value & 0x80000000:
        return value - 0x100000000
    return value


def write_binary(words: Iterable[int], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        for w in words:
            f.write(struct.pack("<I", w & 0xFFFFFFFF))


def read_binary(path: Path) -> list[int]:
    data = path.read_bytes()
    if len(data) % WORD_SIZE != 0:
        msg = f"Binary file size must be multiple of {WORD_SIZE}"
        raise ValueError(msg)
    return [struct.unpack("<I", data[i : i + WORD_SIZE])[0] for i in range(0, len(data), WORD_SIZE)]


def disassemble_word(addr: int, word: int) -> str:
    opcode, op1_type, op1_reg, op2_type, op2_reg = decode_header(word)
    name = opcode.name.lower()
    parts = [f"{addr:04x} - {word:08x} - {name}"]
    if op1_type != OperandType.NONE:
        parts.append(_fmt_operand(op1_type, op1_reg))
    if op2_type != OperandType.NONE:
        parts.append(_fmt_operand(op2_type, op2_reg))
    return " ".join(parts)


def _fmt_operand(op_type: OperandType, reg: int) -> str:
    if op_type == OperandType.REG:
        return f"r{reg}"
    if op_type == OperandType.IMM:
        return f"imm#{reg}"
    if op_type == OperandType.MEM:
        return f"[r{reg}]" if reg < 4 else f"[{reg:#x}]"
    if op_type == OperandType.LABEL:
        return f"@{reg:#x}"
    return "?"


def disassemble_program(words: list[int], labels: dict[int, str] | None = None) -> list[str]:
    """Disassemble variable-length instructions starting at address 0."""
    labels = labels or {}
    lines: list[str] = []
    pc = 0
    while pc < len(words):
        addr = pc
        header = words[pc]
        opcode, op1_type, op1_reg, op2_type, op2_reg = decode_header(header)
        length = instruction_length(opcode, op1_type, op2_type, op1_reg, op2_reg)
        chunk = words[pc : pc + length]
        detail = _disasm_detail(opcode, op1_type, op1_reg, op2_type, op2_reg, chunk, labels)
        lines.append(f"{addr:04x} - {header:08x} - {detail}")
        for i in range(1, length):
            extra = words[pc + i]
            lines.append(
                f"{addr + i:04x} - {extra:08x} - operand: {extra} ({_operand_extra(extra)})"
            )
        pc += length
    return lines


def _operand_extra(word: int) -> str:
    if 32 <= word < 127:
        return repr(chr(word))
    return str(sign_extend_imm(word))


def _disasm_detail(
    opcode: Opcode,
    op1_type: OperandType,
    op1_reg: int,
    op2_type: OperandType,
    op2_reg: int,
    words: list[int],
    labels: dict[int, str],
) -> str:
    name = opcode.name.lower()
    if opcode == Opcode.HALT:
        return "halt"
    if opcode == Opcode.PRINT_CSTR:
        addr = words[1] if len(words) > 1 else 0
        lbl = labels.get(addr, f"0x{addr:x}")
        return f"print_cstr {lbl}"
    if opcode == Opcode.READ_CSTR:
        addr = words[1] if len(words) > 1 else 0
        maxlen = words[2] if len(words) > 2 else 0
        lbl = labels.get(addr, f"0x{addr:x}")
        return f"read_cstr {lbl}, {maxlen}"
    if opcode == Opcode.PRINT_NUM:
        return f"print_num {_operand_str(op1_type, op1_reg, words, 1, labels)}"
    if opcode in (Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JG, Opcode.JL):
        target = words[1] if len(words) > 1 else 0
        lbl = labels.get(target, f"0x{target:x}")
        return f"{name} {lbl}"
    # Two-operand ALU / MOV / CMP
    dst = _operand_str(op1_type, op1_reg, words, 1, labels)
    src = _operand_str(op2_type, op2_reg, words, 2, labels)
    if opcode == Opcode.MOV:
        return f"mov {dst}, {src}"
    if opcode == Opcode.CMP:
        return f"cmp {dst}, {src}"
    return f"{name} {dst}, {src}"


def _operand_str(
    op_type: OperandType,
    reg: int,
    words: list[int],
    word_idx: int,
    labels: dict[int, str],
) -> str:
    if op_type == OperandType.REG:
        return f"r{reg}"
    if op_type == OperandType.IMM and word_idx < len(words):
        return str(sign_extend_imm(words[word_idx]))
    if op_type == OperandType.MEM:
        if reg < 4:
            return f"[r{reg}]"
        if word_idx < len(words):
            addr = words[word_idx]
            lbl = labels.get(addr, f"0x{addr:x}")
            return f"[{lbl}]"
        return "[?]"
    if op_type == OperandType.LABEL and word_idx < len(words):
        addr = words[word_idx]
        return labels.get(addr, f"0x{addr:x}")
    return "?"


def instruction_length(
    opcode: Opcode,
    op1_type: OperandType,
    op2_type: OperandType,
    op1_reg: int = 0,
    op2_reg: int = 0,
) -> int:
    if opcode == Opcode.HALT:
        return 1
    if opcode in (Opcode.PRINT_CSTR, Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JG, Opcode.JL):
        return 2
    if opcode == Opcode.READ_CSTR:
        return 3
    if opcode == Opcode.PRINT_NUM:
        if op1_type == OperandType.REG:
            return 1
        if op1_type in (OperandType.IMM, OperandType.LABEL):
            return 2
        if op1_type == OperandType.MEM and op1_reg >= 4:
            return 2
        return 1
    extra = 0
    if (
        op1_type in (OperandType.IMM, OperandType.LABEL)
        or op1_type == OperandType.MEM
        and op1_reg >= 4
    ):
        extra += 1
    if (
        op2_type in (OperandType.IMM, OperandType.LABEL)
        or op2_type == OperandType.MEM
        and op2_reg >= 4
    ):
        extra += 1
    return 1 + extra


def write_hex_debug(
    words: list[int],
    path: Path,
    labels: dict[int, str] | None = None,
    data_comments: dict[int, str] | None = None,
) -> None:
    """Write human-readable .hex file."""
    labels = labels or {}
    data_comments = data_comments or {}
    lines = disassemble_program(words, labels)
    # Merge data comments for non-code regions
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
        for addr, comment in sorted(data_comments.items()):
            if addr < len(words):
                w = words[addr]
                f.write(f"{addr:04x} - {w:08x} - {comment}\n")


def load_program_into_memory(words: list[int], memory: list[int], start: int = 0) -> None:
    for i, w in enumerate(words):
        if start + i < len(memory):
            memory[start + i] = w & 0xFFFFFFFF
