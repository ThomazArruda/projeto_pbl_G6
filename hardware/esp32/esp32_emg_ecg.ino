// Firmware simples para leitura de um canal ECG (simulando EMG) e um canal EMG.
// As amostras são transmitidas pela porta serial em formato legível e podem ser
// consumidas pelo script Python localizado em software/data_capture/serial_plotter.py.

#define ECG_PIN 35   // GPIO35 para ECG
#define EMG_PIN 34   // GPIO34 para EMG

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("--- Leitura de 1 ECG e 1 EMG ---");
  
  pinMode(ECG_PIN, INPUT);
  pinMode(EMG_PIN, INPUT);
}

void loop() {
  int valor_ecg = analogRead(ECG_PIN);
  int valor_emg = analogRead(EMG_PIN);

  // Envia os 2 sinais pela serial
  Serial.print("ECG: ");
  Serial.print(valor_ecg);
  Serial.print(", EMG: ");
  Serial.println(valor_emg);

  delay(10); // Atraso para evitar sobrecarga no serial
}
