import numpy as np
import matplotlib.pyplot as plt

MAP_4B5B = {
    '0000': '11110', '0001': '01001', '0010': '10100', '0011': '10101',
    '0100': '01010', '0101': '01011', '0110': '01110', '0111': '01111',
    '1000': '10010', '1001': '10011', '1010': '10110', '1011': '10111',
    '1100': '11010', '1101': '11011', '1110': '11100', '1111': '11101'
}

def encode_4b5b(bin_str):
    if len(bin_str) % 4 != 0:
        bin_str = bin_str.ljust(len(bin_str) + (4 - len(bin_str)%4), '0')
    encoded = ''
    for i in range(0, len(bin_str), 4):
        nibble = bin_str[i:i+4]
        encoded += MAP_4B5B.get(nibble, '00000')
    return encoded

def to_hex(bin_str):
    padded = bin_str.ljust(len(bin_str) + (4 - len(bin_str)%4)%4, '0')
    return hex(int(padded, 2))[2:].upper()

source_bin = "110110101010100111001101010010101001110011010111001010011100"
encoded_bin = encode_4b5b(source_bin)
hex_str = to_hex(encoded_bin)

L_orig = len(source_bin)
L_new = len(encoded_bin)
redundancy = (L_new - L_orig) / L_orig

print("=== РЕЗУЛЬТАТЫ ЛОГИЧЕСКОГО КОДИРОВАНИЯ ===")
print(f"Двоичный код (4B/5B): {encoded_bin}")
print(f"Шестнадцатеричный код: {hex_str}")
print(f"Длина нового сообщения: {L_new} бит ({L_new/8:.3f} байт)")
print(f"Избыточность: {redundancy:.2f} ({redundancy*100:.0f}%)")


first_32_bits = encoded_bin[:32]
samples_per_bit = 100
t_axis = np.arange(len(first_32_bits) * samples_per_bit) / samples_per_bit

# NRZ-I генерация
def gen_nrzi(bits, spb):
    sig = np.zeros(len(bits)*spb, dtype=int)
    level = 0
    idx = 0
    for b in bits:
        if b == '1': level = 1 - level
        sig[idx:idx+spb] = level
        idx += spb
    return sig

def gen_manchester(bits, spb):
    sig = np.zeros(len(bits)*spb, dtype=int)
    half = spb // 2
    idx = 0
    for b in bits:
        if b == '0': sig[idx:idx+half], sig[idx+half:idx+spb] = 1, 0
        else:        sig[idx:idx+half], sig[idx+half:idx+spb] = 0, 1
        idx += spb
    return sig

nrzi_sig = gen_nrzi(first_32_bits, samples_per_bit)
manch_sig = gen_manchester(first_32_bits, samples_per_bit)

plt.figure(figsize=(12, 6))
plt.step(t_axis, nrzi_sig, where='post', label='NRZ-I', linewidth=2)
plt.step(t_axis, manch_sig, where='post', label='Манчестер', linewidth=2)
plt.title('Временные диаграммы первых 32 бит закодированного сообщения')
plt.xlabel('Время (в тактах бита)')
plt.ylabel('Уровень напряжения')
plt.yticks([0, 1], ['Низкий (0)', 'Высокий (1)'])
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

Rb = 1e9  # 1 Гбит/с (линейная скорость)
Tb = 1/Rb

print("\n=== СПЕКТРАЛЬНЫЙ АНАЛИЗ (при Rb = 1 Гбит/с) ===")
print(f"Период бита T_b = {Tb*1e9:.2f} нс")
print(f"\n{'Параметр':<25} | {'NRZ-I':<10} | {'Манчестер':<10}")
print("-" * 50)
print(f"{'Нижняя граница f_min (ГГц)':<25} | {'~0.00':<10} | {'~0.00 (DC-нуль)':<10}")
print(f"{'Верхняя граница f_max (ГГц)':<25} | {'1.00':<10} | {'2.00':<10}")
print(f"{'Средняя частота f_avg (ГГц)':<25} | {'~0.50':<10} | {'1.00':<10}")
print(f"{'Требуемая полоса B (ГГц)':<25} | {'1.00':<10} | {'2.00':<10}")

print("\n=== ОБОСНОВАНИЕ ВЫБОРА ===")
print("Наилучший способ: NRZ-I.")
print("При пропускной способности канала 1 ГГц NRZ-I укладывается в полосу полностью.")
print("Манчестер требует 2 ГГц, что превышает ограничение канала и приведёт к")
print("сильным искажениям или снижению скорости в 2 раза.")
print("Код 4B/5B уже решает проблему длинных последовательностей нулей,")
print("поэтому синхронизация NRZ-I будет стабильной.")