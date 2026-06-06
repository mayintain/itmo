from __future__ import annotations

from pathlib import Path

import pytest

from isa import write_binary, write_hex_debug
from machine import run_machine
from translator import Assembler

ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build" / "pytest"


TEST_CASES = [
    {
        "name": "hello",
        "source": "examples/hello.asm",
        "input": "",
        "expected_output": "Hello, world!\n",
        "pipeline": False,
    },
    {
        "name": "cat",
        "source": "examples/cat.asm",
        "input": "abc",
        "expected_output": "abc",
        "pipeline": False,
    },
    {
        "name": "hello_user_name",
        "source": "examples/hello_user_name.asm",
        "input": "Alice\n",
        "expected_output": "What is your name?\nHello, Alice!\n",
        "pipeline": False,
    },
    {
        "name": "sort",
        "source": "examples/sort.asm",
        "input": "514325",
        "expected_output": "12345\n",
        "pipeline": False,
    },
    {
        "name": "double_precision",
        "source": "examples/double_precision.asm",
        "input": "",
        "expected_output": "high=1 low=0\nresult=1:0\n",
        "pipeline": False,
    },
    {
        "name": "prob1",
        "source": "examples/prob1.asm",
        "input": "",
        "expected_output": "906609\n",
        "pipeline": False,
    },
    {
        "name": "pipeline_demo_seq",
        "source": "examples/pipeline_demo.asm",
        "input": "",
        "expected_output": "201\n",
        "pipeline": False,
    },
    {
        "name": "pipeline_demo_pipe",
        "source": "examples/pipeline_demo.asm",
        "input": "",
        "expected_output": "201\n",
        "pipeline": True,
    },
]


@pytest.mark.parametrize("case", TEST_CASES, ids=[str(case["name"]) for case in TEST_CASES])
def test_golden_programs(case: dict[str, str | bool]) -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    name = str(case["name"])
    source_path = ROOT / str(case["source"])
    bin_path = BUILD_DIR / f"{name}.bin"
    log_path = BUILD_DIR / f"{name}.log"

    input_text = str(case["input"])
    input_path: Path | None = None

    if input_text:
        input_path = BUILD_DIR / f"{name}.input"
        input_path.write_text(input_text, encoding="utf-8")

    assembler = Assembler()
    words = assembler.assemble(source_path)
    write_binary(words, bin_path)
    write_hex_debug(
        words,
        bin_path.with_suffix(".hex"),
        labels={addr: name for name, addr in assembler.labels.items()},
        data_comments=assembler.data_comments,
    )

    output = run_machine(
        bin_path=bin_path,
        input_path=input_path,
        log_path=log_path,
        pipeline=bool(case["pipeline"]),
    )

    assert output == case["expected_output"]

    assert bin_path.exists()
    assert bin_path.stat().st_size > 0

    hex_path = bin_path.with_suffix(".hex")
    assert hex_path.exists()
    assert hex_path.stat().st_size > 0

    assert log_path.exists()
    assert log_path.stat().st_size > 0

    log_text = log_path.read_text(encoding="utf-8")
    assert "tick=" in log_text
    assert "micro=" in log_text
