# Acc32 Count Divisors

Реализация функции `count_divisors(n)` на архитектуре **acc32**.

## Файлы

- `assm.s` — исходный код на acc32
- `test.yaml` — конфиг для проверки в wrench

## Запуск через Docker

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench assm.s --isa acc32 -c test.yaml
