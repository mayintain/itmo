#!/usr/bin/env python3
"""Two-pass assembler for the custom ASM language."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from isa import (
    IN_PORT,
    OUT_PORT,
    REG_NAMES,
    Opcode,
    OperandType,
    encode_header,
    write_binary,
    write_hex_debug,
)

RE_SECTION = re.compile(r"\.section\s+(text|data)\s*$", re.I)
RE_ORG = re.compile(r"\.org\s+(\d+|0x[0-9a-f]+)\s*$", re.I)
RE_EQU = re.compile(r"\.equ\s+(\w+)\s*,\s*(.+?)\s*$", re.I)
RE_WORD = re.compile(r"\.word\s+(-?\d+|0x[0-9a-f]+)\s*$", re.I)
RE_SPACE = re.compile(r"\.space\s+(\d+)\s*$", re.I)
RE_CSTR = re.compile(r'\.cstr\s+"(.*)"\s*$', re.I)
RE_LABEL = re.compile(r"^(\w+):\s*$")
RE_INSTR = re.compile(
    r"^(\w+)\s+(.+?)\s*$|^(halt)\s*$",
    re.I,
)

INDIRECT_MEM = 0xF  # reg field marker for direct memory address in next word


@dataclass
class Line:
    file: str
    line_no: int
    text: str


@dataclass
class SectionState:
    name: str = "text"
    org: int = 0
    pc: int = 0


@dataclass
class Assembler:
    constants: dict[str, int] = field(default_factory=dict)
    labels: dict[str, int] = field(default_factory=dict)
    reverse_labels: dict[int, str] = field(default_factory=dict)
    text_words: list[int | None] = field(default_factory=list)  # None = placeholder
    data_words: list[int | None] = field(default_factory=list)
    data_comments: dict[int, str] = field(default_factory=dict)
    section: SectionState = field(default_factory=SectionState)
    errors: list[str] = field(default_factory=list)

    def error(self, line: Line, msg: str) -> None:
        self.errors.append(f"{line.file}:{line.line_no}: {msg}")

    def parse_value(self, expr: str, line: Line) -> int | None:
        expr = expr.strip()
        if expr in self.constants:
            return self.constants[expr]
        if expr.startswith("0x") or expr.startswith("0X"):
            return int(expr, 16)
        if expr.isdigit() or (expr.startswith("-") and expr[1:].isdigit()):
            return int(expr)
        if expr in self.labels:
            return self.labels[expr]
        if expr in REG_NAMES:
            return int(REG_NAMES[expr])
        self.error(line, f"unknown symbol: {expr}")
        return None

    def strip_comment(self, text: str) -> str:
        if ";" in text:
            return text.split(";", 1)[0].strip()
        return text.strip()

    def collect_lines(self, path: Path) -> list[Line]:
        lines: list[Line] = []
        for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            text = self.strip_comment(raw)
            if text:
                lines.append(Line(str(path), i, text))
        return lines

    def collect_labels(self, lines: list[Line]) -> None:
        """First pass: collect label addresses only."""
        text_pc = 0
        data_pc = 0
        in_text = True
        for line in lines:
            m = RE_SECTION.match(line.text)
            if m:
                in_text = m.group(1).lower() == "text"
                continue
            m = RE_ORG.match(line.text)
            if m:
                org = self.parse_value(m.group(1), line)
                if org is not None:
                    if in_text:
                        text_pc = org
                    else:
                        data_pc = org
                continue
            m = RE_LABEL.match(line.text)
            if m:
                self.labels[m.group(1)] = text_pc if in_text else data_pc
                self.reverse_labels[self.labels[m.group(1)]] = m.group(1)
                continue
            if in_text:
                if line.text.lower() == "halt":
                    text_pc += 1
                elif self.is_instruction(line):
                    text_pc += self.instr_size_pass1(line)
            else:
                data_pc += self.data_size(line)

    def pass1(self, lines: list[Line]) -> None:
        for line in lines:
            m = RE_EQU.match(line.text)
            if m:
                val = self.parse_value(m.group(2).strip(), line)
                if val is not None:
                    self.constants[m.group(1).upper()] = val
                    self.constants[m.group(1)] = val
        self.collect_labels(lines)
        for line in lines:
            if not (
                RE_SECTION.match(line.text)
                or RE_ORG.match(line.text)
                or RE_EQU.match(line.text)
                or RE_LABEL.match(line.text)
                or RE_WORD.match(line.text)
                or RE_SPACE.match(line.text)
                or RE_CSTR.match(line.text)
                or line.text.lower() == "halt"
                or self.is_instruction(line)
            ):
                self.error(line, f"unknown directive/instruction: {line.text}")

    def data_size(self, line: Line) -> int:
        m = RE_WORD.match(line.text)
        if m:
            return 1
        m = RE_SPACE.match(line.text)
        if m:
            return int(m.group(1))
        m = RE_CSTR.match(line.text)
        if m:
            s = self.decode_cstr(m.group(1))
            return len(s) + 1
        return 0

    def decode_cstr(self, s: str) -> str:
        return bytes(s, "utf-8").decode("unicode_escape")

    def is_instruction(self, line: Line) -> bool:
        t = line.text.lower()
        if t == "halt":
            return True
        ops = (
            "mov",
            "add",
            "sub",
            "mul",
            "div",
            "mod",
            "cmp",
            "jmp",
            "jz",
            "jnz",
            "jg",
            "jl",
            "print_cstr",
            "read_cstr",
            "print_num",
        )
        return any(t.startswith(op) for op in ops)

    def _operand_extra_words(self, op: str) -> int:
        op = op.strip()
        if op in REG_NAMES:
            return 0
        if op.startswith("[") and op.endswith("]"):
            inner = op[1:-1].strip()
            return 0 if inner in REG_NAMES else 1
        return 1

    def instr_size_pass1(self, line: Line) -> int:
        parts = line.text.split(None, 1)
        mnem = parts[0].lower()
        if mnem == "halt":
            return 1
        if mnem in ("print_cstr", "jmp", "jz", "jnz", "jg", "jl", "print_num"):
            return 2
        if mnem == "read_cstr":
            return 3
        if mnem in ("mov", "add", "sub", "mul", "div", "mod", "cmp"):
            rest = parts[1] if len(parts) > 1 else ""
            if "," not in rest:
                return 2
            dst, src = [x.strip() for x in rest.split(",", 1)]
            return 1 + self._operand_extra_words(dst) + self._operand_extra_words(src)
        return 2

    def pass2(self, lines: list[Line]) -> list[int]:
        memory: dict[int, int] = {}
        self.section = SectionState("text", 0, 0)
        text_pc = 0
        data_pc = 0
        in_text = True

        def put_text(pc: int, val: int) -> None:
            memory[pc] = val

        def put_data(pc: int, val: int, comment: str = "") -> None:
            memory[pc] = val
            if comment:
                self.data_comments[pc] = comment

        for line in lines:
            m = RE_SECTION.match(line.text)
            if m:
                in_text = m.group(1).lower() == "text"
                continue
            m = RE_ORG.match(line.text)
            if m:
                org = self.parse_value(m.group(1), line)
                if org is None:
                    continue
                if in_text:
                    text_pc = org
                else:
                    data_pc = org
                continue
            m = RE_EQU.match(line.text)
            if m:
                continue
            m = RE_LABEL.match(line.text)
            if m:
                continue
            if in_text:
                if line.text.lower() == "halt":
                    put_text(text_pc, encode_header(Opcode.HALT))
                    text_pc += 1
                    continue
                if self.is_instruction(line):
                    words = self.encode_instruction(line, fix_labels=True)
                    for w in words:
                        put_text(text_pc, w)
                        text_pc += 1
                    continue
            else:
                m = RE_WORD.match(line.text)
                if m:
                    v = self.parse_value(m.group(1), line)
                    if v is not None:
                        put_data(data_pc, v & 0xFFFFFFFF, f"data: {v}")
                        data_pc += 1
                    continue
                m = RE_SPACE.match(line.text)
                if m:
                    count = int(m.group(1))
                    for _ in range(count):
                        put_data(data_pc, 0, "data: 0")
                        data_pc += 1
                    continue
                m = RE_CSTR.match(line.text)
                if m:
                    s = self.decode_cstr(m.group(1))
                    for ch in s:
                        put_data(data_pc, ord(ch), f"data: {repr(ch)}")
                        data_pc += 1
                    put_data(data_pc, 0, "data: '\\0'")
                    data_pc += 1
                    continue

        max_addr = max(memory.keys()) if memory else 0
        result = [0] * (max_addr + 1)
        for addr, val in memory.items():
            result[addr] = val
        return result

    def parse_operand(self, s: str, line: Line) -> tuple[OperandType, int, int | None]:
        s = s.strip()
        if s in REG_NAMES:
            return OperandType.REG, int(REG_NAMES[s]), None
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if inner in REG_NAMES:
                return OperandType.MEM, int(REG_NAMES[inner]), None
            val = self.parse_value(inner, line)
            if val is not None:
                return OperandType.MEM, INDIRECT_MEM, val
        val = self.parse_value(s, line)
        if val is not None:
            return OperandType.IMM, 0, val
        if s in self.labels:
            return OperandType.MEM, INDIRECT_MEM, self.labels[s]
        self.error(line, f"bad operand: {s}")
        return OperandType.NONE, 0, None

    def encode_instruction(self, line: Line, fix_labels: bool) -> list[int]:
        text = line.text.strip()
        lower = text.lower()
        if lower == "halt":
            return [encode_header(Opcode.HALT)]

        parts = text.split(None, 1)
        mnem = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        if mnem == "print_cstr":
            addr = self.parse_value(rest.strip(), line)
            if addr is None:
                return [encode_header(Opcode.PRINT_CSTR)]
            return [encode_header(Opcode.PRINT_CSTR), addr & 0xFFFFFFFF]

        if mnem == "read_cstr":
            a, b = [x.strip() for x in rest.split(",", 1)]
            addr = self.parse_value(a, line)
            maxlen = self.parse_value(b, line)
            if addr is None or maxlen is None:
                return [encode_header(Opcode.READ_CSTR)]
            return [encode_header(Opcode.READ_CSTR), addr & 0xFFFFFFFF, maxlen & 0xFFFFFFFF]

        if mnem == "print_num":
            op1_type, op1_reg, extra = self.parse_operand(rest, line)
            words = [encode_header(Opcode.PRINT_NUM, op1_type, op1_reg)]
            if extra is not None:
                words.append(extra & 0xFFFFFFFF)
            return words

        jumps = {
            "jmp": Opcode.JMP,
            "jz": Opcode.JZ,
            "jnz": Opcode.JNZ,
            "jg": Opcode.JG,
            "jl": Opcode.JL,
        }
        if mnem in jumps:
            target = self.parse_value(rest.strip(), line)
            if target is None:
                return [encode_header(jumps[mnem])]
            return [encode_header(jumps[mnem]), target & 0xFFFFFFFF]

        alu_map = {
            "mov": Opcode.MOV,
            "add": Opcode.ADD,
            "sub": Opcode.SUB,
            "mul": Opcode.MUL,
            "div": Opcode.DIV,
            "mod": Opcode.MOD,
            "cmp": Opcode.CMP,
        }
        if mnem in alu_map:
            if "," not in rest:
                self.error(line, "expected two operands")
                return [encode_header(alu_map[mnem])]
            dst_s, src_s = [x.strip() for x in rest.split(",", 1)]
            op1_type, op1_reg, extra1 = self.parse_operand(dst_s, line)
            op2_type, op2_reg, extra2 = self.parse_operand(src_s, line)
            words = [encode_header(alu_map[mnem], op1_type, op1_reg, op2_type, op2_reg)]
            if (
                op1_type in (OperandType.IMM, OperandType.LABEL)
                and extra1 is not None
                or op1_type == OperandType.MEM
                and op1_reg == INDIRECT_MEM
                and extra1 is not None
            ):
                words.append(extra1 & 0xFFFFFFFF)
            if (
                op2_type in (OperandType.IMM, OperandType.LABEL)
                and extra2 is not None
                or op2_type == OperandType.MEM
                and op2_reg == INDIRECT_MEM
                and extra2 is not None
            ):
                words.append(extra2 & 0xFFFFFFFF)
            return words

        self.error(line, f"unknown instruction {mnem}")
        return [0]

    def assemble(self, source: Path) -> list[int]:
        lines = self.collect_lines(source)
        self.pass1(lines)
        if self.errors:
            raise AssemblerError("\n".join(self.errors))
        return self.pass2(lines)


class AssemblerError(Exception):
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble .asm to .bin and .hex")
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    asm = Assembler()
    # Predefined port constants
    asm.constants.setdefault("IN", IN_PORT)
    asm.constants.setdefault("OUT", OUT_PORT)
    asm.constants.setdefault("IN_PORT", IN_PORT)
    asm.constants.setdefault("OUT_PORT", OUT_PORT)

    try:
        words = asm.assemble(args.source)
    except AssemblerError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    write_binary(words, args.output)
    hex_path = args.output.with_suffix(".hex")
    write_hex_debug(words, hex_path, asm.reverse_labels, asm.data_comments)
    print(f"Assembled {len(words)} words -> {args.output}")
    print(f"Debug hex -> {hex_path}")


if __name__ == "__main__":
    main()
