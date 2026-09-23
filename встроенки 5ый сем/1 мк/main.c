#include "main.h"
#include "tm1637.h"
#include "keyboard.h"

volatile uint32_t tickCount;
uint32_t last_display_update;
uint16_t counter;
char lastKey;
uint32_t lastScanTime;

// переменные для работы калькулятора

int operand1 = -1; // первый операнд, значение "-1" = операнд не введен

int operand2 = -1; // второй операнд, значение "-1" = операнд не введен

// храним символ выбранной математической операции:
// '\0' - операция еще не выбрана
// '+', '-', '*', '/' - знаки операций
char operation = '\0'; 

int result = 0; // результат вычисления


void osSystickHandler(void) {
  tickCount++;
}


void initGPIO() {
  // Включаем тактирование GPIOA и GPIOB
  RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN;

  // Настраиваем PA5 как выход
  GPIOA->MODER = (GPIOA->MODER & ~(3 << 10)) | (1 << 10);
  GPIOA->OTYPER &= ~(1 << 5);
  GPIOA->OSPEEDR |= (1 << 10);
}

void initUSART2() {
  // Включаем тактирование USART2
  RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

  // Настраиваем PA2 и PA3 в альтернативный режим
  GPIOA->MODER = (GPIOA->MODER & ~(0xF << 4)) | (0xA << 4);
  GPIOA->AFR[0] = (GPIOA->AFR[0] & ~(0xFF << 8)) | (1 << 8) | (1 << 12);

  // Настраиваем USART2
  USART2->BRR = 417; // 48MHz/115200
  USART2->CR1 = USART_CR1_TE | USART_CR1_UE;
}

void initSysTick() {
  SysTick->LOAD = 47999; // 1ms при 48MHz
  SysTick->VAL = 0;
  SysTick->CTRL = (1 << 2) | (1 << 1) | (1 << 0);
}

int _write(int file, uint8_t *ptr, int len) {
  for (int i = 0; i < len; i++) {
    while (!(USART2->ISR & USART_ISR_TXE));
    USART2->TDR = ptr[i];
  }
  return len;
}

// вспомогательная функция для чистых вычислений
int calculate(int num1, int num2, char op, int *error) {
  *error = 0;
  switch (op) {
    case '+': return num1 + num2;
    case '-': return num1 - num2;
    case '*': return num1 * num2;
    case '/':
      if (num2 == 0) {
        *error = 1;
        return 0;
      }
      return num1 / num2;
    default:
      return 0;
  }
}

// вспомогательная функция для отображения знака операции на TM1637
void display_operation_symbol(char op) {
  tm1637_clear(); // полностью очищаем дисплей перед выводом нового знака
  switch (op) {
    case '+':
      // выводим букву П в первом разряде
      tm1637_display_digit(1, 0x37); 
      break;
    case '-':
      // выводим два минуса по центру дисплея
      tm1637_display_digit(1, 0x40); 
      tm1637_display_digit(2, 0x40);
      break;
    case '*':
      // выводим символ Х (в виде буквы Н) во втором разряде
      tm1637_display_digit(2, 0x76); 
      break;
    case '/':
      // выводим косую черту деления
      tm1637_display_digit(1, 0x52); 
      break;
  }
}



// обработка нажатой клавиши
void processKey(char key) { // в key находится символ нажатой клавиши

  // если нажата цифра
  if (key >= '0' && key <= '9') {
    int number = key - '0'; // символ -> число

    // если первый операнд еще не введен
    if (operand1 == -1) {
      operand1 = number;
      tm1637_display_number(operand1); // показываем число на дисплее
      printf("First operand: %d\n", operand1);
    }

    // если первый операнд уже введен, операция выбрана, а второй операнд еще не введен
    else if (operation != '\0' && operand2 == -1) {
      operand2 = number;
      tm1637_display_number(operand2); // показываем второй операнд на дисплее
      printf("Second operand: %d\n", operand2);
    }
  }

  // если нажата *, выбираем операцию
  else if (key == '*') {

    // операцию можно выбирать после ввода первого операнда и до ввода второго операнда
    if (operand1 != -1 && operand2 == -1) {
      
      // циклически переключаем символ операции при каждом нажатии на звездочку
      switch (operation) {
        case '\0': operation = '+'; break;
        case '+':  operation = '-'; break;
        case '-':  operation = '*'; break;
        case '*':  operation = '/'; break; // исправлена опечатка перебора знака умножения
        case '/':  operation = '+'; break;
      }

      // отображаем выбранный знак операции на дисплее
      display_operation_symbol(operation);

      // выводим выбранный символ операции в консоль
      switch (operation) {
        case '+': printf("Operation: +\n"); break;
        case '-': printf("Operation: -\n"); break;
        case '*': printf("Operation: *\n"); break;
        case '/': printf("Operation: /\n"); break;
      }
    }
  }

  // если нажата #, выполняем вычисление
  else if (key == '#') {

    // вычисляем только если введены оба операнда и выбрана операция
    if (operand1 != -1 && operation != '\0' && operand2 != -1) {
      int calc_error = 0;

      // производим математический расчет через функцию
      result = calculate(operand1, operand2, operation, &calc_error);

      // проверяем деление на ноль
      if (calc_error == 1) {
        printf("Error: division by zero!\n");

        // очищаем дисплей, так как результата нет
        tm1637_clear();

        // сбрасываем значения, чтобы можно было
        // начать новое вычисление
        operand1 = -1;
        operand2 = -1;
        operation = '\0';

        return;
      }
      
      // выводим результат в Serial Monitor
      printf("Result: %d\n", result);

      // показываем результат на дисплее
      tm1637_display_number(result);


      // сбрасываем значения, чтобы можно было
      // сразу начать новое вычисление
      operand1 = -1;
      operand2 = -1;
      operation = '\0';
    }
  }
}

int main(void) {
  initGPIO();
  initUSART2();
  initSysTick();
  initKeyboard();
  tm1637_init();

  printf("Hello, %s!\n", "Wokwi Simulation");

  // GPIOA->ODR |= (1 << 5); // Включаем LED (в работе калькулятора не используется)

  while (1) {
    scanKeyboard(); // постоянная проверка состояния клавиатуры
  }

  return 0;
}
