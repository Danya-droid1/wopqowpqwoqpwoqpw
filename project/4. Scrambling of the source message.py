#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import struct


class Scrambler:

    def __init__(self, polynomial: str = "3_5"):

        self.polynomial = polynomial
        if polynomial == "3_5":
            self.taps = [3, 5]  # Отводы регистра
        elif polynomial == "5_7":
            self.taps = [5, 7]
        else:
            raise ValueError("Неподдерживаемый полином. Используйте '3_5' или '5_7'")

    def scramble(self, data: List[int]) -> List[int]:

        max_delay = max(self.taps)
        output = []
        # Инициализация регистра сдвига
        register = [0] * max_delay

        for bit in data:
            # Вычисляем выходной бит
            xor_sum = bit
            for tap in self.taps:
                xor_sum ^= register[tap - 1]

            output.append(xor_sum)

            # Сдвигаем регистр
            register.pop()
            register.insert(0, xor_sum)

        return output

    def get_polynomial_description(self) -> str:

        if self.polynomial == "3_5":
            return "B_i = A_i ⊕ B_{i-3} ⊕ B_{i-5}"
        else:
            return "B_i = A_i ⊕ B_{i-5} ⊕ B_{i-7}"


class PhysicalEncoder:


    @staticmethod
    def nrz_encode(data: List[int]) -> List[float]:

        return [1.0 if bit == 1 else 0.0 for bit in data]

    @staticmethod
    def manchester_encode(data: List[int]) -> List[float]:

        result = []
        for bit in data:
            if bit == 1:
                result.extend([0.0, 1.0])  # Переход 0->1
            else:
                result.extend([1.0, 0.0])  # Переход 1->0
        return result

    @staticmethod
    def differential_manchester_encode(data: List[int]) -> List[float]:

        result = []
        current_level = 1.0

        for bit in data:
            if bit == 0:
                # Переход в начале бита
                current_level = 1.0 - current_level
                result.extend([current_level, 1.0 - current_level])
            else:
                # Нет перехода в начале
                result.extend([current_level, 1.0 - current_level])
            current_level = result[-1]

        return result

    @staticmethod
    def ami_encode(data: List[int]) -> List[float]:

        result = []
        last_positive = False

        for bit in data:
            if bit == 0:
                result.append(0.0)
            else:
                if last_positive:
                    result.append(-1.0)
                    last_positive = False
                else:
                    result.append(1.0)
                    last_positive = True

        return result


class SpectrumAnalyzer:


    @staticmethod
    def calculate_spectrum(encoded_signal: List[float], bit_rate: float = 1e9) -> Dict:

        signal = np.array(encoded_signal)
        n = len(signal)

        # Вычисляем БПФ
        fft = np.fft.fft(signal)
        freq = np.fft.fftfreq(n, d=1 / bit_rate)

        # Берем только положительную часть
        positive_mask = freq >= 0
        freq = freq[positive_mask]
        magnitude = np.abs(fft[positive_mask])

        # Нормализуем
        magnitude = magnitude / np.max(magnitude) if np.max(magnitude) > 0 else magnitude

        # Находим границы частот (где мощность > 1% от максимума)
        significant_indices = np.where(magnitude > 0.01)[0]

        if len(significant_indices) > 0:
            f_low = freq[significant_indices[0]]
            f_high = freq[significant_indices[-1]]
        else:
            f_low = 0
            f_high = bit_rate

        # Средняя частота (взвешенная)
        total_magnitude = np.sum(magnitude)
        if total_magnitude > 0:
            f_avg = np.sum(freq * magnitude) / total_magnitude
        else:
            f_avg = 0

        # Полоса пропускания
        bandwidth = f_high - f_low

        return {
            'f_low': f_low,
            'f_high': f_high,
            'f_avg': f_avg,
            'bandwidth': bandwidth,
            'frequencies': freq,
            'magnitudes': magnitude
        }


class TimingDiagram:


    @staticmethod
    def plot_encoding(data: List[int], encoded: List[float],
                      encoding_name: str, bit_rate: float = 1e9,
                      num_bits: int = 8) -> plt.Figure:

        # Берем первые num_bits бит
        data = data[:num_bits]

        # Для Manchester и Differential Manchester - 2 отсчета на бит
        if encoding_name in ["Manchester", "Differential Manchester"]:
            samples_per_bit = 2
            encoded = encoded[:num_bits * samples_per_bit]
        else:
            samples_per_bit = 1
            encoded = encoded[:num_bits]

        # Создаем временную ось
        bit_duration = 1 / bit_rate
        if samples_per_bit == 2:
            time = np.arange(len(encoded)) * (bit_duration / 2)
        else:
            time = np.arange(len(encoded)) * bit_duration

        # Создаем фигуру
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Исходные данные
        ax1.step(np.arange(len(data) + 1), np.hstack([data[0], data]),
                 where='post', linewidth=2, color='blue')
        ax1.set_ylim(-0.5, 1.5)
        ax1.set_yticks([0, 1])
        ax1.set_title(f'Исходные данные ({num_bits} бит)', fontsize=12)
        ax1.set_xlabel('Бит')
        ax1.set_ylabel('Уровень')
        ax1.grid(True, alpha=0.3)

        # Закодированный сигнал
        ax2.step(np.hstack([time, time[-1] + bit_duration / samples_per_bit]),
                 np.hstack([encoded[0], encoded]),
                 where='post', linewidth=2, color='red')
        ax2.set_ylim(-1.5, 1.5)
        ax2.set_title(f'{encoding_name} кодирование', fontsize=12)
        ax2.set_xlabel('Время (с)')
        ax2.set_ylabel('Напряжение (усл. ед.)')
        ax2.grid(True, alpha=0.3)

        # Добавляем подписи битов
        for i, bit in enumerate(data):
            ax1.text(i + 0.5, 1.2, str(bit), ha='center', fontsize=10)

        plt.tight_layout()
        return fig


class DataConverter:

    @staticmethod
    def bytes_to_bits(data: bytes) -> List[int]:

        bits = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def bits_to_bytes(bits: List[int]) -> bytes:

        # Дополняем до кратности 8
        while len(bits) % 8 != 0:
            bits.append(0)

        result = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            result.append(byte)

        return bytes(result)

    @staticmethod
    def bits_to_hex(bits: List[int]) -> str:

        byte_data = DataConverter.bits_to_bytes(bits.copy())
        return byte_data.hex().upper()

    @staticmethod
    def bits_to_binary_string(bits: List[int]) -> str:

        return ''.join(str(b) for b in bits)


def justify_polynomial_choice(scrambler1: Scrambler, scrambler2: Scrambler) -> str:

    justification = """
    ОБОСНОВАНИЕ ВЫБОРА ПОЛИНОМА ДЛЯ СКРЕМБЛИРОВАНИЯ:

    """

    # Полином 1: B_i = A_i ⊕ B_{i-3} ⊕ B_{i-5}
    justification += f"1. Полином {scrambler1.get_polynomial_description()}\n"
    justification += "   Преимущества:\n"
    justification += "   - Меньшая длина регистра (5 бит) - проще аппаратная реализация\n"
    justification += "   - Меньшая задержка обработки\n"
    justification += "   - Достаточная степень перемешивания для большинства приложений\n"
    justification += "   - Хорошие статистические свойства выходной последовательности\n\n"

    # Полином 2: B_i = A_i ⊕ B_{i-5} ⊕ B_{i-7}
    justification += f"2. Полином {scrambler2.get_polynomial_description()}\n"
    justification += "   Преимущества:\n"
    justification += "   - Большая длина регистра (7 бит) - лучшее перемешивание\n"
    justification += "   - Более длинные псевдослучайные последовательности\n"
    justification += "   - Лучшая защита от длинных последовательностей одинаковых битов\n"
    justification += "   Недостатки:\n"
    justification += "   - Более сложная аппаратная реализация\n"
    justification += "   - Большая задержка\n\n"

    justification += "ВЫВОД: Для данной задачи выбираем полином 3_5, так как он обеспечивает\n"
    justification += "достаточное качество скремблирования при меньшей сложности реализации.\n"

    return justification


def compare_encoding_methods(spectrum_results: Dict, bit_rate: float = 1e9) -> str:


    comparison = """
    СРАВНЕНИЕ МЕТОДОВ ФИЗИЧЕСКОГО КОДИРОВАНИЯ:

    """

    for method, spectrum in spectrum_results.items():
        comparison += f"\n{method}:\n"
        comparison += f"  - Нижняя граница частоты: {spectrum['f_low'] / 1e6:.2f} МГц\n"
        comparison += f"  - Верхняя граница частоты: {spectrum['f_high'] / 1e6:.2f} МГц\n"
        comparison += f"  - Средняя частота: {spectrum['f_avg'] / 1e6:.2f} МГц\n"
        comparison += f"  - Полоса пропускания: {spectrum['bandwidth'] / 1e6:.2f} МГц\n"

    comparison += "\n\nАНАЛИЗ И ВЫБОР ЛУЧШЕГО МЕТОДА:\n\n"

    # Анализ каждого метода
    comparison += "1. NRZ (Non-Return-to-Zero):\n"
    comparison += "   + Простота реализации\n"
    comparison += "   + Минимальная полоса пропускания\n"
    comparison += "   + Эффективное использование спектра\n"
    comparison += "   - Проблема с синхронизацией при длинных последовательностях 0 или 1\n"
    comparison += "   - Наличие постоянной составляющей\n\n"

    comparison += "2. Manchester:\n"
    comparison += "   + Встроенная синхронизация (переход в середине каждого бита)\n"
    comparison += "   + Отсутствие постоянной составляющей\n"
    comparison += "   + Самосинхронизирующийся код\n"
    comparison += "   - Требуется удвоенная полоса пропускания\n"
    comparison += "   - Ниже эффективность использования спектра\n\n"

    comparison += "3. AMI (Alternate Mark Inversion):\n"
    comparison += "   + Отсутствие постоянной составляющей\n"
    comparison += "   + Обнаружение ошибок (нарушение чередования)\n"
    comparison += "   + Эффективное использование спектра\n"
    comparison += "   - Проблема синхронизации при длинных последовательностях 0\n"
    comparison += "   - Требуется трехуровневый сигнал\n\n"

    # Выбор лучшего метода
    comparison += "ВЫВОД И ОБОСНОВАНИЕ ВЫБОРА:\n\n"

    # Определяем лучший метод на основе характеристик
    nrz_bw = spectrum_results['NRZ']['bandwidth']
    man_bw = spectrum_results['Manchester']['bandwidth']
    ami_bw = spectrum_results['AMI']['bandwidth']

    best_method = "Manchester"
    reason = ""

    if spectrum_results['Manchester']['f_low'] > 0.1 * bit_rate:
        reason = """Manchester кодирование выбрано как лучший метод, потому что:
        1. Обеспечивает надежную синхронизацию за счет переходов в середине каждого бита
        2. Не имеет постоянной составляющей, что важно для передачи через трансформаторы
        3. Позволяет обнаруживать некоторые типы ошибок
        4. Широко используется в стандартах Ethernet (10BASE-T)

        Несмотря на удвоенную полосу пропускания, для скорости 1 Гбит/с это приемлемо."""
    elif spectrum_results['AMI']['f_low'] > 0:
        best_method = "AMI"
        reason = """AMI кодирование выбрано как лучший метод, потому что:
        1. Отсутствует постоянная составляющая
        2. Эффективное использование полосы пропускания
        3. Возможность обнаружения ошибок
        4. Используется в телефонных линиях (T1/E1)"""
    else:
        best_method = "NRZ"
        reason = """NRZ кодирование выбрано как лучший метод, потому что:
        1. Минимальная требуемая полоса пропускания
        2. Простота реализации
        3. Максимальная эффективность использования спектра
        4. Подходит для высокоскоростных приложений

        Однако требуется дополнительное кодирование (например, 8b/10b) для обеспечения синхронизации."""

    comparison += f"ЛУЧШИЙ МЕТОД: {best_method}\n\n"
    comparison += reason

    return comparison


def main():


    print("=" * 70)
    print("ПРОГРАММА ДЛЯ СКРЕМБЛИРОВАНИЯ И ФИЗИЧЕСКОГО КОДИРОВАНИЯ ДАННЫХ")
    print("=" * 70)

    # Исходные данные для примера (можно заменить на свои)
    original_message = "Hello, World! This is a test message for scrambling."
    original_bytes = original_message.encode('utf-8')

    print(f"\nИсходное сообщение: {original_message}")
    print(f"Длина: {len(original_bytes)} байт")

    # Преобразование в биты
    converter = DataConverter()
    original_bits = converter.bytes_to_bits(original_bytes)

    print(f"\nИсходные данные в двоичном виде (первые 64 бита):")
    print(converter.bits_to_binary_string(original_bits[:64]))
    print(f"\nИсходные данные в HEX (первые 16 байт):")
    print(converter.bits_to_hex(original_bits[:128]))

    # Создание скремблеров
    scrambler1 = Scrambler("3_5")
    scrambler2 = Scrambler("5_7")

    # Обоснование выбора полинома
    print("\n" + "=" * 70)
    print(justify_polynomial_choice(scrambler1, scrambler2))

    # Скремблирование
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ СКРЕМБЛИРОВАНИЯ:")
    print("=" * 70)

    scrambled_bits1 = scrambler1.scramble(original_bits.copy())
    scrambled_bits2 = scrambler2.scramble(original_bits.copy())

    print(f"\n1. Скремблирование полиномом {scrambler1.get_polynomial_description()}:")
    print(f"   Двоичный вид (первые 64 бита): {converter.bits_to_binary_string(scrambled_bits1[:64])}")
    print(f"   HEX вид (первые 16 байт): {converter.bits_to_hex(scrambled_bits1[:128])}")

    print(f"\n2. Скремблирование полиномом {scrambler2.get_polynomial_description()}:")
    print(f"   Двоичный вид (первые 64 бита): {converter.bits_to_binary_string(scrambled_bits2[:64])}")
    print(f"   HEX вид (первые 16 байт): {converter.bits_to_hex(scrambled_bits2[:128])}")

    # Выбираем первый вариант для дальнейшего кодирования
    scrambled_bits = scrambled_bits1
    print("\nДля дальнейшего кодирования используем первый вариант скремблирования.")

    # Физическое кодирование
    print("\n" + "=" * 70)
    print("ФИЗИЧЕСКОЕ КОДИРОВАНИЕ:")
    print("=" * 70)

    encoder = PhysicalEncoder()
    bit_rate = 1e9  # 1 Гбит/с

    # Кодируем первые 32 бита для наглядности
    test_bits = scrambled_bits[:32]

    nrz_encoded = encoder.nrz_encode(test_bits)
    manchester_encoded = encoder.manchester_encode(test_bits)
    ami_encoded = encoder.ami_encode(test_bits)

    print(f"\nКодирование первых 32 бит скремблированного сообщения:")
    print(f"Исходные биты: {converter.bits_to_binary_string(test_bits)}")
    print(f"NRZ: {nrz_encoded}")
    print(f"Manchester: {manchester_encoded}")
    print(f"AMI: {ami_encoded}")

    # Построение временных диаграмм для первых 8 бит
    print("\nПостроение временных диаграмм для первых 8 бит...")

    fig1 = TimingDiagram.plot_encoding(test_bits, nrz_encoded, "NRZ", bit_rate, num_bits=8)
    fig1.savefig('nrz_encoding.png', dpi=300)
    print("Сохранено: nrz_encoding.png")

    fig2 = TimingDiagram.plot_encoding(test_bits, manchester_encoded, "Manchester", bit_rate, num_bits=8)
    fig2.savefig('manchester_encoding.png', dpi=300)
    print("Сохранено: manchester_encoding.png")

    fig3 = TimingDiagram.plot_encoding(test_bits, ami_encoded, "AMI", bit_rate, num_bits=8)
    fig3.savefig('ami_encoding.png', dpi=300)
    print("Сохранено: ami_encoding.png")

    # Анализ спектра
    print("\n" + "=" * 70)
    print("АНАЛИЗ СПЕКТРАЛЬНЫХ ХАРАКТЕРИСТИК:")
    print("=" * 70)

    analyzer = SpectrumAnalyzer()

    # Для Manchester нужно закодировать все биты
    full_manchester = encoder.manchester_encode(scrambled_bits)
    full_ami = encoder.ami_encode(scrambled_bits)

    spectrum_nrz = analyzer.calculate_spectrum(nrz_encoded, bit_rate)
    spectrum_man = analyzer.calculate_spectrum(manchester_encoded, bit_rate)
    spectrum_ami = analyzer.calculate_spectrum(ami_encoded, bit_rate)

    spectrum_results = {
        'NRZ': spectrum_nrz,
        'Manchester': spectrum_man,
        'AMI': spectrum_ami
    }

    for method, spectrum in spectrum_results.items():
        print(f"\n{method}:")
        print(f"  Нижняя граница частоты: {spectrum['f_low'] / 1e6:.4f} МГц")
        print(f"  Верхняя граница частоты: {spectrum['f_high'] / 1e6:.4f} МГц")
        print(f"  Средняя частота: {spectrum['f_avg'] / 1e6:.4f} МГц")
        print(f"  Полоса пропускания: {spectrum['bandwidth'] / 1e6:.4f} МГц")

    # Построение спектров
    fig4, ax = plt.subplots(figsize=(12, 6))
    ax.plot(spectrum_nrz['frequencies'] / 1e6, spectrum_nrz['magnitudes'],
            label='NRZ', linewidth=2)
    ax.plot(spectrum_man['frequencies'] / 1e6, spectrum_man['magnitudes'],
            label='Manchester', linewidth=2)
    ax.plot(spectrum_ami['frequencies'] / 1e6, spectrum_ami['magnitudes'],
            label='AMI', linewidth=2)
    ax.set_xlabel('Частота (МГц)')
    ax.set_ylabel('Нормализованная амплитуда')
    ax.set_title('Спектральные характеристики методов кодирования')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 3000)  # Ограничиваем диапазон для наглядности
    fig4.savefig('spectrum_comparison.png', dpi=300)
    print("\nСохранено: spectrum_comparison.png")

    # Сравнение и выбор лучшего метода
    print("\n" + "=" * 70)
    print(compare_encoding_methods(spectrum_results, bit_rate))

    print("\n" + "=" * 70)
    print("ПРОГРАММА ЗАВЕРШИЛА РАБОТУ")
    print("=" * 70)
    print("\nСозданные файлы:")
    print("  - nrz_encoding.png (временная диаграмма NRZ)")
    print("  - manchester_encoding.png (временная диаграмма Manchester)")
    print("  - ami_encoding.png (временная диаграмма AMI)")
    print("  - spectrum_comparison.png (сравнение спектров)")


if __name__ == "__main__":
    main()