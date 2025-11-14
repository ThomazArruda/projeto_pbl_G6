/*
 * FIRMWARE CORRIGIDO PARA A FIAÇÃO DA FOTO
 *
 * Esta versão corresponde ao seu diagrama:
 * 1. EMG: D34
 * 2. ECG: D35
 * 3. IMU 1 (IMU_C): Barramento I2C Padrão (D21=SDA, D22=SCL)
 * 4. IMU 2 (IMU_P): Barramento I2C Customizado (D32=SDA, D33=SCL)
 *
 * Requer as bibliotecas "Adafruit MPU6050" e "Adafruit Unified Sensor".
 */

#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// --- Pinos Analógicos (Corrigidos) ---
#define EMG_PIN 34   // GPIO34 para EMG (Quadríceps)
#define ECG_PIN 35   // GPIO35 para ECG (Isquiotibial)

// --- Barramento I2C nº 1 (Padrão, para IMU_C) ---
// D21 (SDA), D22 (SCL)
Adafruit_MPU6050 mpu1;

// --- Barramento I2C nº 2 (Customizado, para IMU_P) ---
// <<< CORREÇÃO AQUI: A linha 'TwoWire Wire1 = TwoWire(1);' foi REMOVIDA.
// A biblioteca Wire do ESP32 já define 'Wire1' automaticamente.
Adafruit_MPU6050 mpu2;
#define I2C_BUS1_SDA 32 // D32 (SDA)
#define I2C_BUS1_SCL 33 // D33 (SCL)

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }
  Serial.println("--- Firmware Corrigido (V3 - 2x I2C) ---");

  // Configura os pinos analógicos
  pinMode(EMG_PIN, INPUT);
  pinMode(ECG_PIN, INPUT);

  // Inicializa o I2C Padrão (Wire) para IMU_C
  Wire.begin(); 
  if (!mpu1.begin(0x68, &Wire)) { 
    Serial.println("Falha ao encontrar MPU-6050 (IMU 1) no barramento 0 (Padrão D21/D22)");
    while (1) {
      delay(10);
    }
  }
  Serial.println("IMU 1 (IMU_C) conectado!");
  mpu1.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu1.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu1.setFilterBandwidth(MPU6050_BAND_21_HZ);

  // Inicializa o I2C Customizado (Wire1) para IMU_P
  // 'Wire1' já existe, então podemos apenas usá-lo.
  Wire1.begin(I2C_BUS1_SDA, I2C_BUS1_SCL);
  if (!mpu2.begin(0x68, &Wire1)) {
    Serial.println("Falha ao encontrar MPU-6050 (IMU 2) no barramento 1 (D32/D33)");
    while (1) {
      delay(10);
    }
  }
  Serial.println("IMU 2 (IMU_P) conectado!");
  mpu2.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu2.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu2.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  delay(100);
}

void loop() {
  // 1. Ler Sensores Analógicos
  int valor_emg = analogRead(EMG_PIN);
  int valor_ecg = analogRead(ECG_PIN);

  // 2. Ler Sensores IMU
  sensors_event_t a1, g1, temp1;
  mpu1.getEvent(&a1, &g1, &temp1);
  
  sensors_event_t a2, g2, temp2;
  mpu2.getEvent(&a2, &g2, &temp2);

  // 3. Enviar todos os 14 dados em uma única linha CSV
  // Formato: EMG,ECG,A1x,A1y,A1z,G1x,G1y,G1z,A2x,A2y,A2z,G2x,G2y,G2z
  Serial.print(valor_emg); Serial.print(",");
  Serial.print(valor_ecg); Serial.print(",");
  Serial.print(a1.acceleration.x, 4); Serial.print(",");
  Serial.print(a1.acceleration.y, 4); Serial.print(",");
  Serial.print(a1.acceleration.z, 4); Serial.print(",");
  Serial.print(g1.gyro.x, 4); Serial.print(",");
  Serial.print(g1.gyro.y, 4); Serial.print(",");
  Serial.print(g1.gyro.z, 4); Serial.print(",");
  Serial.print(a2.acceleration.x, 4); Serial.print(",");
  Serial.print(a2.acceleration.y, 4); Serial.print(",");
  Serial.print(a2.acceleration.z, 4); Serial.print(",");
  Serial.print(g2.gyro.x, 4); Serial.print(",");
  Serial.print(g2.gyro.y, 4); Serial.print(",");
  Serial.println(g2.gyro.z, 4);

  delay(10);
}
