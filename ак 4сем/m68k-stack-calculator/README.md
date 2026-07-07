# M68K Stack-Based Calculator

Реализация стекового калькулятора на архитектуре **M68K**.

Программа читает выражение в обратной польской записи из memory-mapped input, обрабатывает числа и арифметические операции с помощью стека, а затем записывает результат в memory-mapped output.

Поддерживаемые операции:

- `+` — сложение;
- `-` — вычитание;
- `*` — умножение;
- `/` — деление.

При ошибке выражения программа записывает в output значение `-1`.

При переполнении программа записывает в output значение `0xcccccccc`.

## файлы

- `m68k.s` — исходный код на M68K без `link/unlk`
- `m68k_link.s` — версия исходного кода на M68K с использованием `link/unlk`
- `tests/test_1.yaml` — тест для `2 3 + -> 5`
- `tests/test_2.yaml` — тест для `2 3 4 * + -> 14`
- `tests/test_3.yaml` — тест для `8 2 / -> 4`
- `tests/test_4.yaml` — тест для некорректного выражения `2 + -> -1`

## запуск через Docker

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench m68k.s --isa m68k -c tests/test_1.yaml
```

## запуск версии с link/unlk

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench m68k_link.s --isa m68k -c tests/test_1.yaml
```
