import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict

class Scrambler:
    def __init__(self, taps: List[int]):
        self.taps = taps

    def scramble(self, data: List[int]) -> List[int]:
        max_delay = max(self.taps)
        output = []
        register = [0] * max_delay
        for bit in data:
            feedback = bit
            for tap in self.taps:
                feedback ^= register[tap - 1]
            output.append(feedback)
            register.pop()
            register.insert(0, feedback)
        return output

    def get_formula(self) -> str:
        indices = [f"B_{{i-{t}}}" for t in self.taps]
        return f"B_i = A_i ⊕ {' ⊕ '.join(indices)}"

class PhysicalEncoder:
    @staticmethod
    def nrz_encode(data: List[int]) -> List[float]:
        return [1.0 if bit == 1 else 0.0 for bit in data]

    @staticmethod
    def manchester_encode(data: List[int]) -> List[float]:
        result = []
        for bit in data:
            if bit == 1:
                result.extend([0.0, 1.0])
            else:
                result.extend([1.0, 0.0])
        return result

    @staticmethod
    def ami_encode(data: List[int]) -> List[float]:
        result = []
        polarity = 1.0
        for bit in data:
            if bit == 0:
                result.append(0.0)
            else:
                result.append(polarity)
                polarity *= -1
        return result

def bits_to_hex(bits: List[int]) -> str:
    while len(bits) % 8 != 0:
        bits.append(0)
    hex_str = ""
    for i in range(0, len(bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits[i + j]
        hex_str += f"{byte_val:02X}"
    return hex_str

def calculate_spectrum(signal: List[float], bit_rate: float = 1e9) -> Dict:
    sig_array = np.array(signal)
    N = len(sig_array)
    fft_vals = np.fft.fft(sig_array)
    freqs = np.fft.fftfreq(N, d=1/bit_rate)
    pos_mask = freqs >= 0
    freqs = freqs[pos_mask]
    magnitude = np.abs(fft_vals[pos_mask])
    if np.max(magnitude) > 0:
        magnitude /= np.max(magnitude)
    threshold = 0.1
    significant_indices = np.where(magnitude > threshold)[0]
    if len(significant_indices) > 0:
        f_low = freqs[significant_indices[0]]
        f_high = freqs[significant_indices[-1]]
    else:
        f_low, f_high = 0, bit_rate/2
    return {
        'f_low': f_low,
        'f_high': f_high,
        'bandwidth': f_high - f_low,
        'freqs': freqs,
        'mags': magnitude
    }

def main():
    print("="*60)
    print("ЗАПУСК ПРОГРАММЫ: СКРЕМБЛИРОВАНИЕ И КОДИРОВАНИЕ")
    print("="*60)
    message = "Student"
    message_bytes = message.encode('utf-8')
    original_bits = []
    for byte in message_bytes:
        for i in range(7, -1, -1):
            original_bits.append((byte >> i) & 1)
    print(f"Исходное сообщение: '{message}'")
    print(f"Количество бит: {len(original_bits)}")
    print(f"Первые 32 бита (двоично): {''.join(map(str, original_bits[:32]))}")
    scrambler1 = Scrambler(taps=[3, 5])
    scrambler2 = Scrambler(taps=[5, 7])
    scr_bits_1 = scrambler1.scramble(original_bits.copy())
    scr_bits_2 = scrambler2.scramble(original_bits.copy())
    print("\n--- РЕЗУЛЬТАТЫ СКРЕМБЛИРОВАНИЯ ---")
    print(f"Полином 1 ({scrambler1.get_formula()}):")
    print(f"  HEX: {bits_to_hex(scr_bits_1)}")
    print(f"Полином 2 ({scrambler2.get_formula()}):")
    print(f"  HEX: {bits_to_hex(scr_bits_2)}")
    final_bits = scr_bits_1
    print("\nДля кодирования выбран результат Полинома 1.")
    n_bits_to_plot = 32
    data_subset = final_bits[:n_bits_to_plot]
    print(f"\n--- КОДИРОВАНИЕ (первые {n_bits_to_plot} бит) ---")
    encoder = PhysicalEncoder()
    sig_nrz = encoder.nrz_encode(data_subset)
    sig_man = encoder.manchester_encode(data_subset)
    sig_ami = encoder.ami_encode(data_subset)
    print("Открытие окна с временными диаграммами...")
    fig_timing, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    fig_timing.suptitle('Временные диаграммы кодирования', fontsize=16)
    bit_rate = 1e9
    duration_per_bit = 1 / bit_rate
    t_nrz = np.arange(len(sig_nrz)) * duration_per_bit
    t_man = np.arange(len(sig_man)) * (duration_per_bit / 2)
    axes[0].step(t_nrz, sig_nrz, where='post', linewidth=2, color='blue')
    axes[0].set_ylabel('Уровень (В)')
    axes[0].set_title('NRZ')
    axes[0].grid(True)
    axes[0].set_ylim(-0.2, 1.2)
    axes[1].step(t_man, sig_man, where='post', linewidth=2, color='green')
    axes[1].set_ylabel('Уровень (В)')
    axes[1].set_title('Manchester')
    axes[1].grid(True)
    axes[1].set_ylim(-0.2, 1.2)
    axes[2].step(t_nrz, sig_ami, where='post', linewidth=2, color='red')
    axes[2].set_xlabel('Время (с)')
    axes[2].set_ylabel('Уровень (В)')
    axes[2].set_title('AMI')
    axes[2].grid(True)
    axes[2].set_ylim(-1.2, 1.2)
    plt.tight_layout()
    plt.show()
    print("\n--- АНАЛИЗ СПЕКТРА ---")
    long_signal_bits = final_bits * 10
    sig_nrz_long = encoder.nrz_encode(long_signal_bits)
    sig_man_long = encoder.manchester_encode(long_signal_bits)
    sig_ami_long = encoder.ami_encode(long_signal_bits)
    spec_nrz = calculate_spectrum(sig_nrz_long, bit_rate)
    spec_man = calculate_spectrum(sig_man_long, bit_rate)
    spec_ami = calculate_spectrum(sig_ami_long, bit_rate)
    print(f"NRZ:    Низкая частота: {spec_nrz['f_low']/1e6:.2f} МГц, Ширина полосы: {spec_nrz['bandwidth']/1e6:.2f} МГц")
    print(f"Man:    Низкая частота: {spec_man['f_low']/1e6:.2f} МГц, Ширина полосы: {spec_man['bandwidth']/1e6:.2f} МГц")
    print(f"AMI:    Низкая частота: {spec_ami['f_low']/1e6:.2f} МГц, Ширина полосы: {spec_ami['bandwidth']/1e6:.2f} МГц")
    print("Открытие окна со спектрами...")
    fig_spec, ax_spec = plt.subplots(figsize=(10, 6))
    max_freq_plot = 2e9
    mask_nrz = spec_nrz['freqs'] <= max_freq_plot
    mask_man = spec_man['freqs'] <= max_freq_plot
    mask_ami = spec_ami['freqs'] <= max_freq_plot
    ax_spec.plot(spec_nrz['freqs'][mask_nrz]/1e6, spec_nrz['mags'][mask_nrz], label='NRZ', linewidth=2)
    ax_spec.plot(spec_man['freqs'][mask_man]/1e6, spec_man['mags'][mask_man], label='Manchester', linewidth=2)
    ax_spec.plot(spec_ami['freqs'][mask_ami]/1e6, spec_ami['mags'][mask_ami], label='AMI', linewidth=2)
    ax_spec.set_xlabel('Частота (МГц)')
    ax_spec.set_ylabel('Нормализованная амплитуда')
    ax_spec.set_title('Спектральная плотность мощности')
    ax_spec.legend()
    ax_spec.grid(True)
    plt.show()
    print("\n--- ОБОСНОВАНИЕ ВЫБОРА ---")
    print("Лучший способ: Manchester кодирование.")
    print("1. В спектре отсутствует постоянная составляющая.")
    print("2. Сигнал самосинхронизирующийся.")
    print("3. Позволяет надежно восстанавливать тактовую частоту.")
    print("Минус: Требуется ширина полосы в 2 раза больше, чем у NRZ.")

if __name__ == "__main__":
    main()