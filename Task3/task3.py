# Код с википедии https://ru.wikipedia.org/wiki/%D0%9A%D0%BE%D0%B4_%D0%A5%D1%8D%D0%BC%D0%BC%D0%B8%D0%BD%D0%B3%D0%B0
# 100100101110001
# 11110010001011110001
# Код для проврки кода с википедии
# 11110110001011110001

# ---------- ЦВЕТА ----------
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    # Данные (информационные биты)
    DATA = "\033[36m"  # голубой
    # Проверочные биты
    PARITY = "\033[33m"  # жёлтый
    # Ошибка
    ERROR = "\033[91m"  # ярко-красный
    # Исправленный бит
    FIXED = "\033[92m"  # ярко-зелёный
    # Номера позиций
    POSITION = "\033[90m"  # серый


def is_parity_bit(pos):
    """Проверяет, является ли позиция степенью двойки (проверочный бит)"""
    i = 0
    while 2**i <= pos:
        if 2**i == pos:
            return True
        i += 1
    return False


# ---------- ЧАСТЬ 1: вычисление y ----------


def insert_parity_bits(data):
    m = len(data)
    r = 0

    # считаем сколько нужно проверочных битов
    while (2**r) < (m + r + 1):
        r += 1

    res = []
    j = 0
    k = 0

    for i in range(1, m + r + 1):
        if i == 2**j:
            res.append(0)
            j += 1
        else:
            res.append(int(data[k]))
            k += 1

    return res, r


def calculate_parity_bits(arr, r):
    n = len(arr)

    for i in range(r):
        pos = 2**i
        parity = 0

        for j in range(1, n + 1):
            if j & pos:
                parity ^= arr[j - 1]

        arr[pos - 1] = parity

    return arr


# ---------- ЧАСТЬ 2: поиск ошибки ----------


def detect_error(arr, r):
    n = len(arr)
    error_pos = 0

    for i in range(r):
        pos = 2**i
        parity = 0

        for j in range(1, n + 1):
            if j & pos:
                parity ^= arr[j - 1]

        if parity != 0:
            error_pos += pos

    return error_pos


# ---------- ВИЗУАЛИЗАЦИЯ ----------


def print_with_positions(arr, error_pos=0):
    """Выводит биты с номерами позиций и цветами"""
    n = len(arr)

    # Строка номеров позиций
    pos_line = Colors.POSITION
    for i in range(1, n + 1):
        pos_line += f"{i:^5}"
    pos_line += Colors.RESET
    print(pos_line)

    # Разделитель
    print(Colors.POSITION + "-----" * n + Colors.RESET)

    # Строка битов
    bit_line = ""
    for i, bit in enumerate(arr):
        pos = i + 1
        if error_pos == pos:
            # Ошибочный бит - красный
            bit_line += f"{Colors.ERROR}{Colors.BOLD}{bit:^5}{Colors.RESET}"
        elif is_parity_bit(pos):
            # Проверочный бит - жёлтый
            bit_line += f"{Colors.PARITY}{bit:^5}{Colors.RESET}"
        else:
            # Информационный бит - голубой
            bit_line += f"{Colors.DATA}{bit:^5}{Colors.RESET}"

    print(bit_line)


def print_mapping(data, arr, r):
    """Показывает, какие биты данных куда встали"""
    # Показываем исходные данные
    print(
        f"\n{Colors.BOLD}Исходные данные:{Colors.RESET} {Colors.DATA}{data}{Colors.RESET}"
    )
    print(f"{Colors.BOLD}Проверочные биты:{Colors.RESET}")
    for i in range(r):
        pos = 2**i
        print(f"  y{i} (позиция {pos}) = {Colors.PARITY}{arr[pos - 1]}{Colors.RESET}")


def print_error_details(arr, error_pos, r):
    """Подробная информация об ошибке"""
    print(f"\n{Colors.BOLD}{Colors.ERROR}⚠ ОБНАРУЖЕНА ОШИБКА!{Colors.RESET}")
    print(f"Ошибка в позиции: {Colors.ERROR}{Colors.BOLD}{error_pos}{Colors.RESET}")

    # Показываем бит до исправления
    print(f"\nДо исправления:")
    print_with_positions(arr, error_pos)

    # Исправляем
    arr[error_pos - 1] ^= 1

    print(
        f"\nПосле исправления (бит в позиции {error_pos} изменён {Colors.ERROR}{1 - arr[error_pos - 1]}{Colors.RESET} → {Colors.FIXED}{arr[error_pos - 1]}{Colors.RESET}):"
    )
    print_with_positions(arr, 0)


# ---------- ОСНОВНАЯ ЧАСТЬ ----------

data = input("Введите последовательность (x): ")

arr, r = insert_parity_bits(data)
arr = calculate_parity_bits(arr, r)

print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
print(f"{Colors.BOLD}КОД ХЭММИНГА{Colors.RESET}")
print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

print_mapping(data, arr, r)

print(f"\n{Colors.BOLD}Итоговый код Хэмминга:{Colors.RESET}")
print_with_positions(arr)

# Вывод для копирования
print(f"\n{Colors.BOLD}Для копирования:{Colors.RESET} {''.join(map(str, arr))}")

# -------- проверка ошибки --------

print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
code = input(f"{Colors.BOLD}Введите код для проверки ошибки:{Colors.RESET} ")
code_arr = list(map(int, code))

error = detect_error(code_arr, r)

print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
if error == 0:
    print(f"{Colors.FIXED}{Colors.BOLD}✓ Ошибок нет{Colors.RESET}")
    print_with_positions(code_arr)
else:
    print_error_details(code_arr, error, r)
