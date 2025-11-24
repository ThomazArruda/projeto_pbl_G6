import socket
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import argparse
import csv

# --- Configurações ---
UDP_IP = "0.0.0.0" # Escuta em todas as interfaces de rede do PC
UDP_PORT = 4210    # Mesma porta definida no Arduino
FS = 100
WINDOW_SIZE = FS * 5 

# --- Argumentos ---
parser = argparse.ArgumentParser(description='Plota dados via Wi-Fi (UDP)')
parser.add_argument('-o', '--output', type=str, help='Nome do arquivo .csv (opcional)')
args = parser.parse_args()

# --- Buffers (Organizados por ID) ---
data_store = {
    "ESQ": {
        "angle": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE),
        "emg": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE),
        "ecg": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE)
    },
    "DIR": {
        "angle": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE),
        "emg": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE),
        "ecg": deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE)
    }
}

# --- Setup UDP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False) # Modo não-bloqueante para não travar o gráfico
print(f"Escutando UDP na porta {UDP_PORT}...")

# --- Setup CSV ---
csv_file = None; csv_writer = None
if args.output:
    try:
        csv_file = open(args.output, 'w', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file, delimiter=';')
        csv_writer.writerow(['timestamp', 'ID', 'Angle', 'EMG', 'ECG'])
        print(f"Salvando em: {args.output}")
    except Exception as e: print(f"Erro CSV: {e}")

start_time = time.time()

# --- Gráficos ---
fig, ax = plt.subplots(3, 1, figsize=(10, 9), constrained_layout=True)
x = np.arange(0, WINDOW_SIZE)

# Linhas Esquerda (Azul/Vermelho/Verde)
ln_ang_esq, = ax[0].plot(x, [0]*WINDOW_SIZE, 'g', label='Angulo ESQ')
ln_emg_esq, = ax[1].plot(x, [0]*WINDOW_SIZE, 'b', label='EMG ESQ')
ln_ecg_esq, = ax[2].plot(x, [0]*WINDOW_SIZE, 'r', label='ECG ESQ')

# Linhas Direita (Tracejadas ou cores diferentes)
ln_ang_dir, = ax[0].plot(x, [0]*WINDOW_SIZE, 'g--', label='Angulo DIR')
ln_emg_dir, = ax[1].plot(x, [0]*WINDOW_SIZE, 'b--', label='EMG DIR')
ln_ecg_dir, = ax[2].plot(x, [0]*WINDOW_SIZE, 'r--', label='ECG DIR')

ax[0].set_title('Angulação'); ax[0].set_ylim(0, 180); ax[0].legend()
ax[1].set_title('EMG (Quadriceps)'); ax[1].set_ylim(0, 4096); ax[1].legend()
ax[2].set_title('ECG (Isquio)'); ax[2].set_ylim(0, 4096); ax[2].legend()

def update(frame):
    # Lê todos os pacotes acumulados no buffer de rede
    while True:
        try:
            data, addr = sock.recvfrom(1024) # Buffer size
            line = data.decode('utf-8').strip()
            # Formato: ID,ANGULO,EMG,ECG
            parts = line.split(',')
            
            if len(parts) == 4:
                device_id = parts[0] # "ESQ" ou "DIR"
                angle = float(parts[1])
                emg = int(parts[2])
                ecg = int(parts[3])

                if device_id in data_store:
                    data_store[device_id]["angle"].append(angle)
                    data_store[device_id]["emg"].append(emg)
                    data_store[device_id]["ecg"].append(ecg)

                    if csv_writer:
                        t = round(time.time() - start_time, 3)
                        csv_writer.writerow([t, device_id, angle, emg, ecg])

        except BlockingIOError:
            break # Não tem mais dados por enquanto
        except Exception as e:
            print(f"Erro parsing: {e}")
            break

    # Atualiza Gráficos
    ln_ang_esq.set_ydata(data_store["ESQ"]["angle"])
    ln_emg_esq.set_ydata(data_store["ESQ"]["emg"])
    ln_ecg_esq.set_ydata(data_store["ESQ"]["ecg"])

    ln_ang_dir.set_ydata(data_store["DIR"]["angle"])
    ln_emg_dir.set_ydata(data_store["DIR"]["emg"])
    ln_ecg_dir.set_ydata(data_store["DIR"]["ecg"])

    return ln_ang_esq, ln_emg_esq, ln_ecg_esq, ln_ang_dir, ln_emg_dir, ln_ecg_dir

ani = animation.FuncAnimation(fig, update, interval=20, blit=True, cache_frame_data=False)
plt.show()

if csv_file: csv_file.close()
