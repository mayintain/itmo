# RISC-IV Reverse String C-String

Реализация программы переворота C-строки на архитектуре RISC-IV.

Программа читает входную строку из memory-mapped input, сохраняет символы до нулевого байта в стек, а затем выводит их в обратном порядке.

Функция работает со строкой в формате C-string:

- символы читаются до нулевого байта `0`;
- символы до `0` выводятся в обратном порядке;
- если входные данные превышают размер буфера, в output записывается `0xcccccccc`.

Файлы

- `risc.s` — исходный код на RISC-IV
- `test.yaml` — конфиг для проверки в wrench

Запуск через Docker

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench risc.s --isa risc-iv -c test.yaml
```
