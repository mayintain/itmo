# F32a Binary Palindrome

реализация функции `is_binary_palindrome(n)` на архитектуре **F32a**.

функция проверяет, является ли 32-битное двоичное представление числа палиндромом:
- возвращает `1`, если представление симметрично;
- возвращает `0`, если нет.

## файлы

- `assm.s` — исходный код на F32a
- `tests/test_1.yaml` — тест для `5 -> 0`
- `tests/test_2.yaml` — тест для `15 -> 0`
- `tests/test_3.yaml` — тест для `4026531855 -> 1`
- `tests/test_4.yaml` — тест для `3221225474 -> 0`

## запуск через Docker

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  ryukzak/wrench:latest \
  wrench assm.s --isa f32a -c tests/test_1.yaml
