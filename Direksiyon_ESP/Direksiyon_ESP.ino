#include <ESPNowProtocol.h>
#include <WiFi.h>
#include <ESP_FlexyStepper.h>

uint8_t anaMac[] = {0x68, 0xFE, 0x71, 0x87, 0x3D, 0xE8};

ESPNowProtocol protocol;

// !! DM860H pinleri - degistirilecek
#define STEP_PIN 18
#define DIR_PIN  19

ESP_FlexyStepper stepper;

float mevcutAci = 0.0;
float hedefAci  = 0.0;

void komutGeldi(uint8_t src, uint8_t id, const uint8_t *data, uint8_t len, int8_t rssi) {
  memcpy(&hedefAci, data, sizeof(hedefAci));
  Serial.printf("KOMUT ALINDI <- Direksiyon: %.1f derece\n", hedefAci);

  // Gercek donanim baglaninca aktif et:
  // stepper.setTargetPositionInDegrees(hedefAci);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Gercek donanim baglaninca aktif et:
  // stepper.connectToPins(STEP_PIN, DIR_PIN);
  // stepper.setSpeedInStepsPerSecond(1000);
  // stepper.setAccelerationInStepsPerSecondPerSecond(500);
  // stepper.startAsService(1);

  protocol.begin();
  protocol.setNodeId(4);
  protocol.addPeer(1, anaMac);
  protocol.onReceive(komutGeldi);

  Serial.print("Direksiyon ESP32 MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.println("Direksiyon hazir, fake sinyal gonderiliyor...");
}

void loop() {
  protocol.loop();

  // Fake sinyal (-32 ile +32 derece arasi)
  // Gercek donanim baglaninca:
  // int ham = analogRead(32);
  // mevcutAci = map(ham, 0, 4095, -32, 32);
  float zaman = millis() / 1000.0;
  mevcutAci = sin(zaman) * 32.0;

  protocol.sendReliable(1, 1, (uint8_t*)&mevcutAci, sizeof(mevcutAci));
  Serial.printf("Gonderildi -> Direksiyon: %.1f derece\n", mevcutAci);

  delay(500);
}