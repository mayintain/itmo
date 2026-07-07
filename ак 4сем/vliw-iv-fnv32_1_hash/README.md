# VLIW-IV FNV-1 32-bit Hash

Реализация функции `fnv32_1_hash(xs)` на архитектуре VLIW-IV.

Функция вычисляет 32-битный FNV-1 hash для входной C-строки, которая заканчивается нулевым байтом.

Алгоритм:

- начальное значение хеша — `0x811C9DC5`;
- на каждом символе строки хеш умножается на `0x01000193`;
- затем выполняется XOR с текущим символом;
- обработка заканчивается, когда считан нулевой байт.

Файлы

- `vliw.s` — исходный код на VLIW-IV
- `vliw2.s` — альтернативная версия исходного кода на VLIW-IV
- `test.yaml` — конфиг для проверки в wrench

Запуск через Docker

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench vliw.s --isa vliw-iv -c test.yaml
```

Запуск второй версии

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench vliw2.s --isa vliw-iv -c test.yaml
```
