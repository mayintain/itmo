PYTHON = python3
RUFF = $(PYTHON) -m ruff
MYPY = $(PYTHON) -m mypy
.PHONY: lint format typecheck check test hello cat hello-user-name sort double-precision prob1 pipeline clean
lint:
	$(RUFF) check .

format:
	$(RUFF) format .

typecheck:
	$(MYPY)

check: lint typecheck test
test:
	$(PYTHON) -m pytest -v

hello:
	$(PYTHON) translator.py examples/hello.asm build/hello.bin
	$(PYTHON) machine.py build/hello.bin --log build/hello.log

cat:
	printf "abc" > build/cat.input
	$(PYTHON) translator.py examples/cat.asm build/cat.bin
	$(PYTHON) machine.py build/cat.bin build/cat.input --log build/cat.log

hello-user-name:
	printf "Alice\n" > build/hello_user_name.input
	$(PYTHON) translator.py examples/hello_user_name.asm build/hello_user_name.bin
	$(PYTHON) machine.py build/hello_user_name.bin build/hello_user_name.input --log build/hello_user_name.log

sort:
	printf "514325" > build/sort.input
	$(PYTHON) translator.py examples/sort.asm build/sort.bin
	$(PYTHON) machine.py build/sort.bin build/sort.input --log build/sort.log

double-precision:
	$(PYTHON) translator.py examples/double_precision.asm build/double_precision.bin
	$(PYTHON) machine.py build/double_precision.bin --log build/double_precision.log

prob1:
	$(PYTHON) translator.py examples/prob1.asm build/prob1.bin
	$(PYTHON) machine.py build/prob1.bin --log build/prob1.log

pipeline:
	$(PYTHON) translator.py examples/pipeline_demo.asm build/pipeline_demo.bin
	$(PYTHON) machine.py build/pipeline_demo.bin --log build/pipeline_demo_seq.log
	$(PYTHON) machine.py build/pipeline_demo.bin --pipeline --log build/pipeline_demo_pipe.log

clean:
	rm -rf build/*
	touch build/.gitkeep
