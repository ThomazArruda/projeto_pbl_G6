import serial
import time
import numpy as np
import matplotlib
matplotlib.use('TkAgg') # Define o "motor" do gráfico para um que suporte blitting
import matplotlib.pyplot as plt
from collections import deque
import argparse

# --- Argumentos de Linha de Comando ---
parser = argparse.ArgumentParser(description='Plota dados seriais do ESP32 (EMG, ECG, 2x IMU)')
parser.add_argument(
    '--port', 
    type=str, 
    required=True, 
    help='Porta serial (ex: COM3 no Windows, /dev/ttyUSB0 no Linux)'
)
parser.add_argument(
    '--baud', 
    type=int, 
    default=115200, 
    help='Baud rate (padrão: 115200)'
)
args = parser.parse_args()

# --- Configurações ---
BAUD = args.baud
PORT = args.port
FS = 100
N_CHANNELS = 14
WINDOW_SIZE = FS * 5 # Janela de 5 segundos (500 amostras)

# --- Buffers de Dados (um deque para cada canal) ---
data_buffers = [deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE) for _ in range(N_CHANNELS)]

# --- Configuração do Gráfico (2 subplots) ---
fig, ax = plt.subplots(2, 1, figsize=(10, 7), constrained_layout=True)
fig.suptitle(f"Debug dos Sensores da Perna (Porta: {PORT})", fontsize=16)
x_axis = np.arange(0, WINDOW_SIZE)

# --- Gráfico 1: Músculos (EMG/ECG) ---
# O 'animated=True' é essencial para o blitting
ln_emg, = ax[0].plot(x_axis, data_buffers[0], lw=1, color='blue', label='EMG (Quad)', animated=True)
ln_ecg, = ax[0].plot(x_axis, data_buffers[1], lw=1, color='red', label='ECG (Isquio)', animated=True)
ax[0].set_title('Músculos Agonista vs. Antagonista')
ax[0].set_ylim(0, 4096) # Começa com o limite total do ADC
ax[0].legend(loc='upper left')

# --- Gráfico 2: IMUs (Acelerômetro X) ---
ln_imu1, = ax[1].plot(x_axis, data_buffers[2], lw=1, color='green', label='IMU 1 - Ax (Quadril)', animated=True)
ln_imu2, = ax[1].plot(x_axis, data_buffers[8], lw=1, color='purple', label='IMU 2 - Ax (Coxa)', animated=True)
ax[1].set_title('IMUs (Aceleração em X)')
ax[1].set_ylim(-20, 20) # Limite fixo para aceleração (m/s^2)
ax[1].legend(loc='upper left')

# --- Setup de Blitting ---
plt.show(block=False)
fig.canvas.draw()
backgrounds = [fig.canvas.copy_from_bbox(ax[i].bbox) for i in range(2)]

# --- Conexão Serial ---
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    print(f"Conectado a {PORT} em {BAUD} baud.")
except serial.SerialException as e:
    print(f"Erro ao abrir a porta serial {PORT}: {e}")
    exit()

time.sleep(1.0)
ser.flushInput()

# --- Loop Principal de Leitura e Plot (RÁPIDO) ---
try:
    while True:
        # 1. Ler e Processar Dados (O mais rápido possível)
        line = ser.readline()
        if not line:
            continue
        
        try:
            line_str = line.decode('utf-8').strip()
            values_str = line_str.split(',')
            if len(values_str) != N_CHANNELS:
                continue
            values_float = [float(v) for v in values_str]
            for i in range(N_CHANNELS):
                data_buffers[i].append(values_float[i])
        
        except (UnicodeDecodeError, ValueError):
            continue
        
        # 2. Redesenhar o Gráfico (Técnica de Blitting)
        
        # Restaura os fundos (tira a "foto" limpa)
        fig.canvas.restore_region(backgrounds[0])
        fig.canvas.restore_region(backgrounds[1])

        # Ajusta o Eixo Y do Gráfico 1 (Músculos) dinamicamente
        min_val = min(np.min(data_buffers[0]), np.min(data_buffers[1]))
        max_val = max(np.max(data_buffers[0]), np.max(data_buffers[1]))
        ax[0].set_ylim(min_val - (max_val*0.1), max_val + (max_val*0.1)) # Adiciona 10% de margem

        # Seta os novos dados das linhas
        ln_emg.set_ydata(data_buffers[0])
        ln_ecg.set_ydata(data_buffers[1])
        ln_imu1.set_ydata(data_buffers[2])
        ln_imu2.set_ydata(data_buffers[8])

        # Desenha apenas as linhas (a parte rápida)
        ax[0].draw_artist(ln_emg)
        ax[0].draw_artist(ln_ecg)
        ax[1].draw_artist(ln_imu1)
        ax[1].draw_artist(ln_imu2)

        # "Cola" as linhas desenhadas no fundo
        fig.canvas.blit(ax[0].bbox)
        fig.canvas.blit(ax[1].bbox)
        
        fig.canvas.flush_events()

except KeyboardInterrupt:
    print("\nFinalizado pelo usuário.")
finally:
    ser.close()
    plt.ioff()
    print("Porta serial fechada.")

# APAGUE A LINHA ABAIXO ANTES DE SALVAR
