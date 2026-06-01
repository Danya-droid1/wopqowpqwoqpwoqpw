def main():
    # 1. Формирование таблицы кодировки согласно заданию
    encoding_table = {}

    # Заглавные кириллические буквы (А-Я, без Ё) -> от C0 до DF
    for i, ch in enumerate("АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"):
        encoding_table[ch] = 0xC0 + i

    # Строчные кириллические буквы (а-я, без ё) -> от E0 до FF
    for i, ch in enumerate("абвгдежзийклмнопрстуфхцчшщъыьэюя"):
        encoding_table[ch] = 0xE0 + i

    # Цифры 0-9 -> от 30 до 39
    for i in range(10):
        encoding_table[str(i)] = 0x30 + i

    # Пробел и знаки препинания
    encoding_table.update({" ": 0x20, ",": 0x2C, ".": 0x2E})

    # 2. Ввод сообщения
    message = input("Введите исходное сообщение: ")

    # 3. Кодирование
    hex_codes = []
    bin_codes = []

    for char in message:
        if char not in encoding_table:
            print(f"\nОшибка: символ '{char}' отсутствует в таблице кодировки.")
            return

        code_val = encoding_table[char]
        # Форматирование: 2 знака HEX в верхнем регистре, 8 знаков BIN с ведущими нулями
        hex_codes.append(f"{code_val:02X}")
        bin_codes.append(f"{code_val:08b}")

    # 4. Вывод результатов в требуемом формате
    byte_len = len(message)
    bit_len = byte_len * 8

    print(f"\nисходное сообщение: {message}")
    print(f"в шестнадцатеричном коде: {' '.join(hex_codes)}")
    print(f"в двоичном коде: {' '.join(bin_codes)}")
    print(f"длина сообщения:   {byte_len} байт ({bit_len} бит)")


if __name__ == "__main__":
    main()