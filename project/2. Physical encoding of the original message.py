import numpy as np
import matplotlib.pyplot as plt

MESSAGE = b'ABCD'
BIT_RATE = 1e9
TB = 1.0 / BIT_RATE
SAMPLES_PER_BIT = 10
N_BITS = len(MESSAGE) * 8

bits = np.array([int(b) for byte in MESSAGE for b in format(byte, '08b')])

def nrz_l(b):
    return np.where(b == 1, 1.0, 0.0)

def nrz_i(b):
    sig = np.zeros_like(b, dtype=float)
    state = 0.0
    for i, val in enumerate(b):
        if val == 1:
            state = 1.0 - state
        sig[i] = state
    return sig

def manchester(b):
    sig = np.zeros(2 * len(b))
    for i, val in enumerate(b):
        if val == 0:  # 1 -> 0
            sig[2*i], sig[2*i+1] = 1.0, 0.0
        else:         # 0 -> 1
            sig[2*i], sig[2*i+1] = 0.0, 1.0
    return sig

def ami(b):
    sig = np.zeros_like(b, dtype=float)
    pol = 1.0
    for i, val in enumerate(b):
        if val == 1:
            sig[i] = pol
            pol *= -1.0
    return sig

dt = TB / SAMPLES_PER_BIT
t_sampled = np.arange(N_BITS * SAMPLES_PER_BIT) * dt

sig_nrz_l = np.repeat(nrz_l(bits), SAMPLES_PER_BIT)
sig_nrz_i = np.repeat(nrz_i(bits), SAMPLES_PER_BIT)
sig_ami   = np.repeat(ami(bits), SAMPLES_PER_BIT)
sig_man   = np.repeat(manchester(bits), SAMPLES_PER_BIT // 2)

fig, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True)
titles = ['NRZ-L', 'NRZ-I', 'Manchester', 'AMI']
signals = [sig_nrz_l, sig_nrz_i, sig_man, sig_ami]
t_ns = t_sampled * 1e9

for ax, title, sig in zip(axes, titles, signals):
    ax.step(t_ns, sig, where='post', linewidth=1.5)
    ax.set_title(f'{title} кодирование (первые 4 байта)')
    ax.set_ylabel('Амплитуда')
    ax.set_ylim(-1.2, 1.2)
    ax.grid(True, alpha=0.3)

axes[-1].set_xlabel('Время, нс')
plt.tight_layout()
plt.show()

print("="*70)
print("Расчёт спектральных характеристик (Rb = 1 Гбит/с, Tb = 1 нс)")
print("="*70)

params = {
    'NRZ-L':     {'f_min': 0.0, 'f_max': 1.0, 'f_avg': 0.5,  'B': 1.0},
    'NRZ-I':     {'f_min': 0.0, 'f_max': 1.0, 'f_avg': 0.5,  'B': 1.0},
    'Манчестер': {'f_min': 0.5, 'f_max': 2.0, 'f_avg': 1.25, 'B': 1.5},
    'AMI':       {'f_min': 0.0, 'f_max': 1.0, 'f_avg': 0.5,  'B': 0.5}
}

print(f"{'Метод':<12} | {'f_min, ГГц':<10} | {'f_max, ГГц':<10} | {'f_avg, ГГц':<10} | {'B, ГГц':<8}")
print("-" * 70)
for method, p in params.items():
    print(f"{method:<12} | {p['f_min']:<10.2f} | {p['f_max']:<10.2f} | {p['f_avg']:<10.2f} | {p['B']:<8.2f}")

print("\nПримечание: расчёты выполнены по первому нулю АЧХ для прямоугольных импульсов.")
print("В реальных системах применяется формировка (raised cosine), снижающая B до ~0.5Rb.")