#!/usr/bin/env python3
"""Tick-accurate microcoded processor simulator with optional pipeline."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from isa import (
    IN_PORT,
    MEMORY_SIZE,
    OUT_PORT,
    Opcode,
    OperandType,
    decode_header,
    instruction_length,
    load_program_into_memory,
    read_binary,
    sign_extend_imm,
)


class MicroOp(Enum):
    FETCH_ADDR = auto()
    FETCH_READ = auto()
    FETCH_LATCH = auto()
    DECODE = auto()
    READ_OPERAND = auto()
    LOAD_MEM = auto()
    STORE_MEM = auto()
    ALU_ADD = auto()
    ALU_SUB = auto()
    ALU_MUL = auto()
    ALU_DIV = auto()
    ALU_MOD = auto()
    SET_FLAGS = auto()
    JUMP = auto()
    OUTPUT_CHAR = auto()
    INPUT_CHAR = auto()
    LATCH_PC = auto()
    WRITE_REG = auto()
    READ_IMM = auto()
    INC_PTR = auto()
    CHECK_ZERO = auto()
    PRINT_DIGIT = auto()
    HALT = auto()
    NOP = auto()


@dataclass
class Decoded:
    opcode: Opcode
    op1_type: OperandType
    op1_reg: int
    op2_type: OperandType
    op2_reg: int
    addr: int
    length: int
    words: list[int]
    imm_words: list[int] = field(default_factory=list)


class DataPath:
    def __init__(self) -> None:
        self.memory: list[int] = [0] * MEMORY_SIZE
        self.r = [0, 0, 0, 0]
        self.pc = 0
        self.ir = 0
        self.mar = 0
        self.mdr = 0
        self.sp = 0
        self.zf = 0
        self.nf = 0
        self.cf = 0
        self.halted = False
        self.input_buf = ""
        self.input_pos = 0
        self.output_buf = ""
        self._operand_idx = 0
        self._alu_result = 0
        self._jump_target = 0
        self._str_ptr = 0
        self._str_max = 0
        self._print_num_val = 0
        self._print_digit_stack: list[int] = []

    def read_mem(self, addr: int) -> int:
        addr &= 0xFFFF
        if addr == IN_PORT:
            if self.input_pos >= len(self.input_buf):
                return 0
            ch = self.input_buf[self.input_pos]
            self.input_pos += 1
            return ord(ch) & 0xFF
        return self.memory[addr] & 0xFFFFFFFF

    def write_mem(self, addr: int, value: int) -> None:
        addr &= 0xFFFF
        value &= 0xFFFFFFFF
        if addr == OUT_PORT:
            self.output_buf += chr(value & 0xFF)
            return
        self.memory[addr] = value

    def get_operand(self, op_type: OperandType, reg: int, imm_idx: int, decoded: Decoded) -> int:
        if op_type == OperandType.REG:
            return self.r[reg] & 0xFFFFFFFF
        if op_type == OperandType.IMM:
            if imm_idx < len(decoded.imm_words):
                return decoded.imm_words[imm_idx] & 0xFFFFFFFF
            return 0
        if op_type == OperandType.MEM:
            if reg < 4:
                addr = self.r[reg] & 0xFFFF
            else:
                addr = decoded.imm_words[0] if decoded.imm_words else 0
            return self.read_mem(addr)
        if op_type == OperandType.LABEL:
            if imm_idx < len(decoded.imm_words):
                return decoded.imm_words[imm_idx] & 0xFFFFFFFF
            return 0
        return 0

    def set_reg(self, reg: int, value: int) -> None:
        self.r[reg] = value & 0xFFFFFFFF

    def update_flags(self, result: int) -> None:
        result &= 0xFFFFFFFF
        self.zf = 1 if result == 0 else 0
        self.nf = 1 if (result & 0x80000000) else 0

    def update_flags_sub(self, a: int, b: int) -> None:
        a &= 0xFFFFFFFF
        b &= 0xFFFFFFFF
        diff = (a - b) & 0xFFFFFFFF
        self.zf = 1 if diff == 0 else 0
        self.nf = 1 if (diff & 0x80000000) else 0
        self.cf = 1 if a < b else 0


def decode_instruction(memory: list[int], pc: int) -> Decoded:
    header = memory[pc] if pc < len(memory) else 0
    opcode, op1_type, op1_reg, op2_type, op2_reg = decode_header(header)
    length = instruction_length(opcode, op1_type, op2_type, op1_reg, op2_reg)
    words = [memory[pc + i] if pc + i < len(memory) else 0 for i in range(length)]
    imm_words: list[int] = []
    if length > 1:
        imm_words = words[1:]
    return Decoded(opcode, op1_type, op1_reg, op2_type, op2_reg, pc, length, words, imm_words)


def micro_sequence_for(decoded: Decoded) -> list[MicroOp]:
    """Return microprogram; loops expanded by control unit for cstr I/O."""
    op = decoded.opcode
    if op == Opcode.HALT:
        return [MicroOp.HALT]
    if op == Opcode.PRINT_CSTR:
        return [
            MicroOp.READ_OPERAND,
            MicroOp.LOAD_MEM,
            MicroOp.CHECK_ZERO,
            MicroOp.OUTPUT_CHAR,
            MicroOp.INC_PTR,
        ]
    if op == Opcode.READ_CSTR:
        return [
            MicroOp.READ_OPERAND,
            MicroOp.INPUT_CHAR,
            MicroOp.STORE_MEM,
            MicroOp.INC_PTR,
            MicroOp.CHECK_ZERO,
        ]
    if op == Opcode.PRINT_NUM:
        return [MicroOp.READ_OPERAND, MicroOp.PRINT_DIGIT]
    if op in (Opcode.JMP, Opcode.JZ, Opcode.JNZ, Opcode.JG, Opcode.JL):
        return [MicroOp.READ_OPERAND, MicroOp.JUMP]
    if op == Opcode.MOV:
        return [MicroOp.READ_OPERAND, MicroOp.WRITE_REG]
    if op == Opcode.CMP:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_SUB, MicroOp.SET_FLAGS]
    if op == Opcode.ADD:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_ADD, MicroOp.WRITE_REG]
    if op == Opcode.SUB:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_SUB, MicroOp.WRITE_REG]
    if op == Opcode.MUL:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_MUL, MicroOp.WRITE_REG]
    if op == Opcode.DIV:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_DIV, MicroOp.WRITE_REG]
    if op == Opcode.MOD:
        return [MicroOp.READ_OPERAND, MicroOp.ALU_MOD, MicroOp.WRITE_REG]
    return [MicroOp.NOP]


class ControlUnit:
    FETCH_SEQ = [MicroOp.FETCH_ADDR, MicroOp.FETCH_READ, MicroOp.FETCH_LATCH, MicroOp.DECODE]
    CSTR_BODY = [MicroOp.LOAD_MEM, MicroOp.CHECK_ZERO, MicroOp.OUTPUT_CHAR, MicroOp.INC_PTR]
    READ_BODY = [MicroOp.INPUT_CHAR, MicroOp.STORE_MEM, MicroOp.INC_PTR, MicroOp.CHECK_ZERO]

    def __init__(self, dp: DataPath, pipeline: bool = False) -> None:
        self.dp = dp
        self.pipeline = pipeline
        self.tick = 0
        self.log_lines: list[str] = []
        self.micro: MicroOp = MicroOp.FETCH_ADDR
        self.micro_idx = 0
        self.seq: list[MicroOp] = list(self.FETCH_SEQ)
        self.decoded: Decoded | None = None
        self._src_val = 0
        self._alu_result = 0
        self._dst_addr = 0
        self._str_max = 0
        self._chars_read = 0
        self.phase = "fetch"  # fetch | exec
        self._hold_advance = False
        # Pipeline
        self.if_pc = 0
        self.if_idx = 0
        self.id_decoded: Decoded | None = None
        self.ex_seq: list[MicroOp] = []
        self.ex_idx = 0
        self.ex_decoded: Decoded | None = None
        self.ex_active = False
        self.if_active = True
        self.id_active = False

    def run(self) -> None:
        while not self.dp.halted:
            self._log_tick()
            if self.pipeline:
                self._tick_pipeline()
            else:
                self._tick_sequential()
            self.tick += 1
            if self.tick > 10_000_000:
                raise RuntimeError("tick limit exceeded")

    def _tick_sequential(self) -> None:
        self._exec_micro(self.micro)
        if self.dp.halted:
            return
        if self._hold_advance:
            self._hold_advance = False
            return
        self._advance_sequential()

    def _advance_sequential(self) -> None:
        if self.phase == "exec" and self.decoded and self.micro == MicroOp.INC_PTR:
            if self.decoded.opcode == Opcode.PRINT_CSTR:
                self.micro_idx = 0
                self.micro = self.seq[0]
                return
        if self.phase == "exec" and self.decoded and self.micro == MicroOp.CHECK_ZERO:
            if self.decoded.opcode == Opcode.PRINT_CSTR:
                if self.dp.mdr == 0:
                    self._start_fetch()
                    return
                self.micro_idx = 2
                self.micro = self.seq[2]
                return
            if self.decoded.opcode == Opcode.READ_CSTR:
                if (
                    self.dp.mdr == 0
                    or self.dp.mdr == ord("\n")
                    or self._chars_read >= self._str_max
                ):
                    self.dp.write_mem(self.dp.mar, 0)
                    self._start_fetch()
                    return
                self.micro_idx = 0
                self.micro = self.seq[0]
                return
        self.micro_idx += 1
        if self.micro_idx < len(self.seq):
            self.micro = self.seq[self.micro_idx]
            return
        self._start_fetch()

    def _start_fetch(self) -> None:
        self.phase = "fetch"
        self.seq = list(self.FETCH_SEQ)
        self.micro_idx = 0
        self.micro = self.seq[0]
        self.decoded = None

    def _tick_pipeline(self) -> None:
        # EX stage: one micro-op per tick
        if self.ex_active and self.ex_idx < len(self.ex_seq):
            self.decoded = self.ex_decoded
            self.micro = self.ex_seq[self.ex_idx]
            self._exec_micro(self.micro)
            if self.dp.halted:
                return
            if self._pipeline_ex_stall():
                return
            self.ex_idx += 1
            if self.ex_idx >= len(self.ex_seq):
                self.ex_active = False
                self.ex_decoded = None
                self.decoded = None
        # ID -> EX handoff
        if self.id_active and not self.ex_active and self.id_decoded:
            self.ex_decoded = self.id_decoded
            self.ex_seq = self._exec_sequence(self.id_decoded)
            self.ex_idx = 0
            self.ex_active = True
            self.id_active = False
            self.id_decoded = None
        # IF stage when EX/ID idle
        if self.if_active and not self.id_active and not self.ex_active:
            self._pipeline_fetch_step()

    def _pipeline_ex_stall(self) -> bool:
        """Return True if EX must continue next tick for variable-length micro loops."""
        if not self.ex_decoded:
            return False

        if self.ex_decoded.opcode == Opcode.PRINT_CSTR:
            if self.micro == MicroOp.CHECK_ZERO:
                if self.dp.mdr == 0:
                    # End of C string: finish EX stage.
                    self.ex_idx = len(self.ex_seq) - 1
                    return False

                # Non-zero character: continue with OUTPUT_CHAR.
                self.ex_idx = 2
                return True

            if self.micro == MicroOp.INC_PTR:
                self.ex_idx = 0
                return True

        if self.ex_decoded.opcode == Opcode.READ_CSTR:
            if self.micro == MicroOp.CHECK_ZERO:
                if (
                    self.dp.mdr == 0
                    or self.dp.mdr == ord("\n")
                    or self._chars_read >= self._str_max
                ):
                    # End of input string: finish EX stage.
                    self.ex_idx = len(self.ex_seq) - 1
                    return False

                # Continue reading the next character.
                self.ex_idx = 0
                return True

        return False

    def _pipeline_fetch_step(self) -> None:
        m = self.FETCH_SEQ[self.if_idx]
        self.micro = m
        if m == MicroOp.FETCH_ADDR:
            self.dp.mar = self.if_pc
        elif m == MicroOp.FETCH_READ:
            self.dp.mdr = self.dp.read_mem(self.dp.mar)
        elif m == MicroOp.FETCH_LATCH:
            self.dp.ir = self.dp.mdr
            self.if_pc += 1
        elif m == MicroOp.DECODE:
            addr = self.if_pc - 1
            self.id_decoded = decode_instruction(self.dp.memory, addr)

            next_pc = addr + self.id_decoded.length
            self.dp.pc = next_pc
            self.if_pc = next_pc

            self.id_active = True
            self.if_idx = 0
            return
        self.if_idx += 1

    def _exec_sequence(self, decoded: Decoded) -> list[MicroOp]:
        self.decoded = decoded
        if decoded.opcode == Opcode.PRINT_CSTR:
            self._setup_print_cstr(decoded)
            return list(self.CSTR_BODY)
        if decoded.opcode == Opcode.READ_CSTR:
            self._setup_read_cstr(decoded)
            return list(self.READ_BODY)
        return micro_sequence_for(decoded)

    def _exec_micro(self, micro: MicroOp) -> None:
        dp = self.dp
        if self.pipeline and self.ex_active:
            decoded = self.ex_decoded
        else:
            decoded = self.decoded
        self.micro = micro

        if micro == MicroOp.FETCH_ADDR:
            dp.mar = dp.pc
        elif micro == MicroOp.FETCH_READ:
            dp.mdr = dp.read_mem(dp.mar)
        elif micro == MicroOp.FETCH_LATCH:
            dp.ir = dp.mdr
            dp.pc += 1
        elif micro == MicroOp.DECODE:
            addr = dp.pc - 1
            self.decoded = decode_instruction(dp.memory, addr)
            dp.pc = addr + self.decoded.length
            self.phase = "exec"
            if self.decoded.opcode == Opcode.PRINT_CSTR:
                self._setup_print_cstr(self.decoded)
                self.seq = list(self.CSTR_BODY)
            elif self.decoded.opcode == Opcode.READ_CSTR:
                self._setup_read_cstr(self.decoded)
                self.seq = list(self.READ_BODY)
            else:
                self.seq = micro_sequence_for(self.decoded)
            self.micro_idx = 0
            self.micro = self.seq[0] if self.seq else MicroOp.HALT
            self._hold_advance = True
        elif micro == MicroOp.READ_OPERAND and decoded:
            self._read_operands(decoded)
        elif micro == MicroOp.LOAD_MEM:
            dp.mdr = dp.read_mem(dp.mar)
        elif micro == MicroOp.STORE_MEM:
            if decoded and decoded.opcode == Opcode.READ_CSTR:
                if dp.mdr == 0 or dp.mdr == ord("\n"):
                    dp.write_mem(dp.mar, 0)
                else:
                    dp.write_mem(dp.mar, dp.mdr)
                    self._chars_read += 1
            else:
                dp.write_mem(dp.mar, dp.mdr)
        elif micro == MicroOp.WRITE_REG and decoded:
            if decoded.op1_type == OperandType.MEM:
                dp.write_mem(self._dst_addr, self._src_val)
            elif decoded.opcode == Opcode.MOV:
                dp.set_reg(decoded.op1_reg, self._src_val)
            else:
                dp.set_reg(decoded.op1_reg, self._alu_result)
        elif micro == MicroOp.ALU_ADD and decoded:
            a = dp.get_operand(decoded.op1_type, decoded.op1_reg, 0, decoded)
            self._alu_result = (a + self._src_val) & 0xFFFFFFFF
            dp.cf = 1 if (a + self._src_val) > 0xFFFFFFFF else 0
        elif micro == MicroOp.ALU_SUB and decoded:
            a = dp.get_operand(decoded.op1_type, decoded.op1_reg, 0, decoded)
            self._alu_result = (a - self._src_val) & 0xFFFFFFFF
            dp.update_flags_sub(a, self._src_val)
        elif micro == MicroOp.ALU_MUL and decoded:
            a = dp.get_operand(decoded.op1_type, decoded.op1_reg, 0, decoded)
            self._alu_result = (a * self._src_val) & 0xFFFFFFFF
        elif micro == MicroOp.ALU_DIV and decoded:
            a = dp.get_operand(decoded.op1_type, decoded.op1_reg, 0, decoded)
            b = self._src_val
            self._alu_result = (a // b) if b else 0
        elif micro == MicroOp.ALU_MOD and decoded:
            a = dp.get_operand(decoded.op1_type, decoded.op1_reg, 0, decoded)
            b = self._src_val
            self._alu_result = (a % b) if b else 0
        elif micro == MicroOp.SET_FLAGS:
            dp.update_flags(self._alu_result)
        elif micro == MicroOp.JUMP and decoded:
            target = decoded.imm_words[0] if decoded.imm_words else 0
            take = False
            if decoded.opcode == Opcode.JMP:
                take = True
            elif decoded.opcode == Opcode.JZ:
                take = dp.zf == 1
            elif decoded.opcode == Opcode.JNZ:
                take = dp.zf == 0
            elif decoded.opcode == Opcode.JG:
                take = dp.zf == 0 and dp.nf == 0
            elif decoded.opcode == Opcode.JL:
                take = dp.nf == 1
            if take:
                dp.pc = target
                if self.pipeline:
                    self.if_pc = target

                    # Flush wrong-path pipeline state after a taken branch.
                    self.if_idx = 0
                    self.id_active = False
                    self.id_decoded = None
        elif micro == MicroOp.OUTPUT_CHAR:
            dp.write_mem(OUT_PORT, dp.mdr)
        elif micro == MicroOp.INPUT_CHAR:
            dp.mdr = dp.read_mem(IN_PORT)
        elif micro == MicroOp.INC_PTR:
            dp.mar += 1
        elif micro == MicroOp.CHECK_ZERO:
            pass  # advance handled in _advance_sequential / pipeline stall
        elif micro == MicroOp.PRINT_DIGIT and decoded:
            val = self._src_val
            if decoded.op1_type == OperandType.REG:
                val = dp.r[decoded.op1_reg]
            elif decoded.op1_type == OperandType.IMM and decoded.imm_words:
                val = sign_extend_imm(decoded.imm_words[0])
            self._print_number(val)
        elif micro == MicroOp.HALT:
            dp.halted = True

    def _setup_print_cstr(self, decoded: Decoded) -> None:
        addr = decoded.imm_words[0] if decoded.imm_words else 0
        self.dp.mar = addr

    def _setup_read_cstr(self, decoded: Decoded) -> None:
        self.dp.mar = decoded.imm_words[0] if decoded.imm_words else 0
        self._str_max = decoded.imm_words[1] if len(decoded.imm_words) > 1 else 32
        self._chars_read = 0

    def _read_operands(self, decoded: Decoded) -> None:
        if decoded.op1_type == OperandType.MEM:
            if decoded.op1_reg < 4:
                self._dst_addr = self.dp.r[decoded.op1_reg] & 0xFFFF
            elif decoded.imm_words:
                self._dst_addr = decoded.imm_words[0]
        if decoded.op2_type == OperandType.REG:
            self._src_val = self.dp.r[decoded.op2_reg]
        elif decoded.op2_type == OperandType.IMM:
            self._src_val = sign_extend_imm(decoded.imm_words[-1]) if decoded.imm_words else 0
        elif decoded.op2_type == OperandType.MEM:
            if decoded.op2_reg < 4:
                addr = self.dp.r[decoded.op2_reg] & 0xFFFF
                self._src_val = self.dp.read_mem(addr)
            elif decoded.imm_words:
                self._src_val = self.dp.read_mem(decoded.imm_words[0])
        elif decoded.op2_type == OperandType.LABEL and decoded.imm_words:
            self._src_val = decoded.imm_words[-1]
        if decoded.opcode == Opcode.PRINT_NUM:
            if decoded.op1_type == OperandType.REG:
                self._src_val = self.dp.r[decoded.op1_reg]
            elif decoded.op1_type == OperandType.IMM and decoded.imm_words:
                self._src_val = sign_extend_imm(decoded.imm_words[0])
            elif decoded.op1_type == OperandType.MEM:
                if decoded.op1_reg < 4:
                    addr = self.dp.r[decoded.op1_reg] & 0xFFFF
                elif decoded.imm_words:
                    addr = decoded.imm_words[0] & 0xFFFF
                else:
                    addr = 0
                self._src_val = self.dp.read_mem(addr)
            elif decoded.op1_type == OperandType.LABEL and decoded.imm_words:
                self._src_val = decoded.imm_words[0]

    def _print_number(self, val: int) -> None:
        val = sign_extend_imm(val)
        if val == 0:
            self.dp.write_mem(OUT_PORT, ord("0"))
            return
        negative = val < 0
        if negative:
            val = -val
            self.dp.write_mem(OUT_PORT, ord("-"))
        digits: list[int] = []
        while val > 0:
            digits.append(val % 10)
            val //= 10
        for d in reversed(digits):
            self.dp.write_mem(OUT_PORT, ord(str(d)))

    def _log_tick(self) -> None:
        dp = self.dp
        out_esc = dp.output_buf.replace("\n", "\\n")
        if self.pipeline:
            if_stage = f"pc:{self.if_pc:04x}" if self.if_active else "-"
            id_stage = f"{self.id_decoded.opcode.name.lower()}" if self.id_decoded else "-"
            ex_stage = (
                f"{self.ex_decoded.opcode.name.lower()}:{self.micro.name}"
                if self.ex_active and self.ex_decoded
                else "-"
            )
            pipe = f" IF={if_stage} ID={id_stage} EX={ex_stage}"
        else:
            pipe = ""
        line = (
            f"tick={self.tick + 1:06d} pc={dp.pc:04x} ir={dp.ir:08x} micro={self.micro.name}"
            f" mar={dp.mar:04x} mdr={dp.mdr:08x}"
            f" r0={sign_extend_imm(dp.r[0])} r1={sign_extend_imm(dp.r[1])}"
            f" r2={sign_extend_imm(dp.r[2])} r3={sign_extend_imm(dp.r[3])}"
            f' zf={dp.zf} nf={dp.nf} cf={dp.cf} out="{out_esc}"{pipe}'
        )
        self.log_lines.append(line)

    def _log_io_event(self, event: str) -> None:
        self.log_lines.append(f"  io: {event}")


def run_machine(
    bin_path: Path,
    input_path: Path | None,
    log_path: Path | None,
    pipeline: bool,
) -> str:
    words = read_binary(bin_path)
    dp = DataPath()
    load_program_into_memory(words, dp.memory)

    if input_path and input_path.exists():
        dp.input_buf = input_path.read_text(encoding="utf-8")

    cu = ControlUnit(dp, pipeline=pipeline)

    if pipeline:
        cu.if_pc = 0

    try:
        cu.run()
    finally:
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("\n".join(cu.log_lines) + "\n", encoding="utf-8")

    return dp.output_buf


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate processor")
    parser.add_argument("program", type=Path)
    parser.add_argument("input", type=Path, nargs="?", default=None)
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument("--pipeline", action="store_true")
    args = parser.parse_args()

    output = run_machine(args.program, args.input, args.log, args.pipeline)
    sys.stdout.write(output)
    if output and not output.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
