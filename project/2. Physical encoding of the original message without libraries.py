MESSAGE = b'ABCD'          # 4 байта: 0x41, 0x42, 0x43, 0x44
BIT_RATE = 1e9             # 1 Гбит/с
TB = 1.0 / BIT_RATE        # 1 нс

def message_to_bits(msg):
    bits = []
    for byte in msg:
        bits.extend([int(b) for b in format(byte, '08b')])
    return bits

bits = message_to_bits(MESSAGE)


def encode_nrz_l(bits):
    return [1.0 if b == 1 else 0.0 for b in bits]

def encode_nrz_i(bits):
    signal, state = [], 0.0
    for b in bits:
        if b == 1:
            state = 1.0 - state
        signal.append(state)
    return signal

def encode_manchester(bits):
    signal = []
    for b in bits:
        # 0 -> 1->0 (высокий->низкий), 1 -> 0->1 (низкий->высокий)
        signal.extend([1.0, 0.0] if b == 0 else [0.0, 1.0])
    return signal

def encode_ami(bits):
    signal, polarity = [], 1.0
    for b in bits:
        if b == 1:
            signal.append(polarity)
            polarity *= -1.0
        else:
            signal.append(0.0)
    return signal


def draw_ascii_waveform(signal, title):
    """Рисует ступенчатую диаграмму символами псевдографики."""
    level_map = {1.0: 0, 0.0: 1, -1.0: 2}
    w = 3  # ширина одного отсчёта в символах
    n = len(signal)
    grid = [[" " for _ in range(n * w + 3)] for _ in range(3)]

    for i, v in enumerate(signal):
        r = level_map.get(v, 1)
        for j in range(w):
            grid[r][i * w + j + 2] = "─"
        # Вертикальный фронт
        if i > 0 and signal[i] != signal[i - 1]:
            r_prev = level_map.get(signal[i - 1], 1)
            r_curr = r
            for rr in range(min(r_prev, r_curr), max(r_prev, r_curr) + 1):
                grid[rr][i * w + 2] = "│"

    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}")
    print(" +1 │ " + "".join(grid[0]))
    print("  0 │ " + "".join(grid[1]))
    print(" -1 │ " + "".join(grid[2]))
    print("    │ " + " " * (n * w // 3) + "Время (длительность бита) -->")



encoders = {
    "NRZ-L (Non-Return-to-Zero Level)": encode_nrz_l,
    "NRZ-I (Non-Return-to-Zero Inverted)": encode_nrz_i,
    "Манчестерский код": encode_manchester,
    "AMI (Alternate Mark Inversion)": encode_ami
}

signals = {}
for name, func in encoders.items():
    sig = func(bits)
    signals[name] = sig
    draw_ascii_waveform(sig, name)



print(f"\n{'='*80}")
print(" РАСЧЁТ СПЕКТРАЛЬНЫХ ПАРАМЕТРОВ (Rb = 1 Гбит/с, Tb = 1 нс)")
print(f"{'='*80}")
print(f"{'Метод':<25} | {'f_min, ГГц':<10} | {'f_max, ГГц':<10} | {'f_avg, ГГц':<10} | {'B, ГГц':<8}")
print("-" * 80)

spectral_data = [
    ("NRZ-L",          0.00, 1.00, 0.50, 1.00, "DC есть, 1-й нуль при Rb"),
    ("NRZ-I",          0.00, 1.00, 0.50, 1.00, "Спектр идентичен NRZ-L, зависит от данных"),
    ("Манчестер",      0.00, 2.00, 1.00, 2.00, "Нет DC, 1-й нуль при 2Rb, синхронизация в каждом бите"),
    ("AMI",            0.00, 1.00, 0.50, 1.00, "Нет DC, 1-й нуль при Rb, эффективная B ~ 0.5Rb")
]

for method, fmin, fmax, favg, bw, note in spectral_data:
    print(f"{method:<25} | {fmin:<10.2f} | {fmax:<10.2f} | {favg:<10.2f} | {bw:<8.2f}")

print("\n Примечание:")
print(" • f_max определено по частоте первого нуля АЧХ спектральной плотности мощности.")
print(" • f_avg = (f_min + f_max)/2 (аппроксимация центра энергии основного лепестка).")
print(" • B = f_max - f_min (ширина основного лепестка). В реальных системах применяют")
print("   формировку импульсов (raised-cosine), что снижает B до 0.5Rb..0.7Rb без потерь.")



print(f"\n{'='*80}")
print(" СРАВНИТЕЛЬНЫЙ АНАЛИЗ И ОБОСНОВАНИЕ ВЫБОРА")
print(f"{'='*80}")

analysis_text = """
ДОСТОИНСТВА И НЕДОСТАТКИ:
1. NRZ-L/NRZ-I:
   [+] Минимальная требуемая полоса (B = Rb), простейшая реализация.
   [-] Отсутствие тактовой синхронизации при длинных сериях одинаковых битов.
   [-] Присутствует постоянная составляющая (DC), что вызывает дрейф нуля в усилителях.

2. Манчестерский код:
   [+] Гарантированный переход в середине каждого бита → встроенная синхронизация.
   [+] Отсутствие DC-компоненты → подходит для трансформаторной и оптической связи.
   [-] Удвоенная полоса пропускания (B = 2Rb) → выше требования к каналу.
   [-] Более сложная схема детектирования на приёмнике.

3. AMI:
   [+] Отсутствие DC, высокая спектральная эффективность.
   [+] Помехоустойчивость за счёт чередования полярности.
   [-] Потеря синхронизации при длинных последовательностях нулей (решается скрэмблированием HDB3/B8ZS).

ВЫБОР ДВУХ НАИЛУЧШИХ СПОСОБОВ:
1. Манчестерский код – оптимален для задач, где критична надёжность тактовой синхронизации
   и требуется передача по каналам с гальванической развязкой. Удвоенная полоса компенсируется
   простотой приёмника и устойчивостью к низкочастотным помехам.
2. AMI – оптимален для магистральных каналов с ограниченной полосой. Сочетание нулевой DC-компоненты
   и узкого спектра делает его стандартом в телекоммуникациях (E1/T1, оптика). Недостаток с нулями
   устраняется стандартными методами скрэмблирования, что не меняет базовую физическую природу кода.

ОБОСНОВАНИЕ: Для канала 1 Гбит/с выбор зависит от приоритета. Если приоритет – синхронизация и помехоустойчивость, 
выбираем Манчестер. Если приоритет – экономия спектра и дальность передачи, выбираем AMI. Оба метода широко 
аппаратно реализованы и соответствуют современным стандартам высокоскоростной передачи."""

print(analysis_text)
print(f"{'='*80}")
print(" Расчёт и диаграммы выполнены успешно.")