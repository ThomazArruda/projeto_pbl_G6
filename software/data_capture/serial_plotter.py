"""Ferramenta de linha de comando para visualizar sinais EMG/ECG enviados pela ESP32.

O script lê dados do monitor serial (ou gera dados simulados) e os exibe em dois
subgráficos usando Matplotlib. É útil para depurar a comunicação entre o firmware
Arduino/ESP32 e o computador antes de integrar o fluxo em aplicações maiores.
"""

from __future__ import annotations

import argparse
import math
import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

try:
    import serial  # type: ignore
except ImportError as exc:  # pragma: no cover - feedback amigável
    print(
        "O pacote 'pyserial' é obrigatório para a captura dos dados. "
        "Instale-o com 'pip install pyserial'.",
        file=sys.stderr,
    )
    raise


@dataclass
class Sample:
    """Amostra única contendo leituras normalizadas dos sensores."""

    timestamp: float
    ecg: float
    emg: float


class SampleSource:
    """Interface que produz amostras do monitor serial ou dados simulados."""

    def __init__(self, port: str, baud_rate: int, demo_mode: bool = False) -> None:
        self.demo_mode = demo_mode
        self._start_time = time.time()
        self._serial = None

        if not demo_mode:
            try:
                self._serial = serial.Serial(port, baud_rate, timeout=1)
            except serial.SerialException as exc:
                raise SystemExit(
                    f"Não foi possível abrir a porta serial '{port}': {exc}"
                ) from exc

    def read(self) -> Optional[Sample]:
        """Lê uma nova amostra ou retorna ``None`` quando não há dados disponíveis."""

        now = time.time()
        elapsed = now - self._start_time

        if self.demo_mode:
            # Gera sinais artificiais para demonstrar o fluxo.
            ecg_value = 2048 + 800 * math.sin(2 * math.pi * 1.2 * elapsed)
            emg_value = 1500 + 600 * math.sin(2 * math.pi * 0.8 * elapsed + math.pi / 4)
            # Adiciona ruído para simular variabilidade.
            ecg_value += random.uniform(-120, 120)
            emg_value += random.uniform(-150, 150)
            return Sample(elapsed, ecg_value, emg_value)

        if self._serial is None:
            return None

        try:
            raw_line = self._serial.readline().decode("utf-8", errors="ignore").strip()
        except serial.SerialException as exc:
            raise SystemExit(f"Erro ao ler a porta serial: {exc}") from exc

        if not raw_line:
            return None

        parsed = _parse_serial_line(raw_line)
        if parsed is None:
            return None

        return Sample(elapsed, parsed["ecg"], parsed["emg"])

    def close(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()


def _parse_serial_line(line: str) -> Optional[Dict[str, float]]:
    """Interpreta as mensagens no formato ``ECG: <valor>, EMG: <valor>``."""

    try:
        parts = [segment.strip() for segment in line.split(",") if segment.strip()]
        data: Dict[str, float] = {}
        for part in parts:
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip().lower()
            data[key] = float(value.strip())
    except ValueError:
        return None

    if "ecg" in data and "emg" in data:
        return data
    return None


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visualiza em tempo real sinais EMG/ECG enviados pela ESP32."
    )
    parser.add_argument(
        "--port",
        help="Porta serial onde a ESP32 está conectada (ex.: COM3 ou /dev/ttyUSB0).",
    )
    parser.add_argument(
        "--baud", type=int, default=115200, help="Taxa de transmissão (baud rate)."
    )
    parser.add_argument(
        "--window",
        type=int,
        default=500,
        help="Número de amostras recentes exibidas por gráfico.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Executa em modo demonstração sem necessidade de hardware conectado.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.demo and not args.port:
        parser.error("Informe a porta serial com --port ou use o modo demonstração --demo.")

    source = SampleSource(args.port or "", args.baud, demo_mode=args.demo)
    buffer_time: Deque[float] = deque(maxlen=args.window)
    buffer_ecg: Deque[float] = deque(maxlen=args.window)
    buffer_emg: Deque[float] = deque(maxlen=args.window)

    fig, (ax_ecg, ax_emg) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    line_ecg, = ax_ecg.plot([], [], label="ECG", color="tab:blue")
    line_emg, = ax_emg.plot([], [], label="EMG", color="tab:orange")

    ax_ecg.set_ylabel("ECG (ADC)")
    ax_ecg.legend(loc="upper right")
    ax_ecg.grid(True, alpha=0.3)

    ax_emg.set_xlabel("Tempo (s)")
    ax_emg.set_ylabel("EMG (ADC)")
    ax_emg.legend(loc="upper right")
    ax_emg.grid(True, alpha=0.3)

    def update(_frame: int):
        sample = source.read()
        if sample is None:
            return line_ecg, line_emg

        buffer_time.append(sample.timestamp)
        buffer_ecg.append(sample.ecg)
        buffer_emg.append(sample.emg)

        line_ecg.set_data(buffer_time, buffer_ecg)
        line_emg.set_data(buffer_time, buffer_emg)

        if buffer_time:
            times = list(buffer_time)
            x_end = times[-1] if times[-1] > times[0] else times[0] + 1
            ax_ecg.set_xlim(times[0], x_end)

            all_values = list(buffer_ecg) + list(buffer_emg)
            if all_values:
                ymin = min(all_values)
                ymax = max(all_values)
                padding = max((ymax - ymin) * 0.1, 50)
                ax_ecg.set_ylim(ymin - padding, ymax + padding)
                ax_emg.set_ylim(ymin - padding, ymax + padding)

        return line_ecg, line_emg

    _ = FuncAnimation(fig, update, interval=50, blit=False)

    try:
        plt.tight_layout()
        plt.show()
    finally:
        source.close()


if __name__ == "__main__":
    main()
