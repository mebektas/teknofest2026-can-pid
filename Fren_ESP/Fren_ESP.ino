#include <ESPNowProtocol.h>
#include <WiFi.h>
#include <BTS7960.h>

uint8_t anaMac[] = {0x68, 0xFE, 0x71, 0x87, 0x3D, 0xE8};

ESPNowProtocol protocol;

// !! BTS7960 pinleri - degistirilecek
const uint8_t EN    = 26;
const uint8_t L_PWM = 27;
const uint8_t R_PWM = 14;

BTS7960 motorController(EN, L_PWM, R_PWM);

void komutGeldi(uint8_t src, uint8_t id, const uint8_t *data, uint8_t len, int8_t rssi) {
  float komut;
  memcpy(&komut, data, sizeof(komut));
  Serial.printf("KOMUT ALINDI <- Fren: %.1f%%\n", komut);

  // Gercek donanim baglaninca aktif et:
  // motorController.Enable();
  // motorController.TurnRight((int)map(komut, 0, 100, 0, 255));
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  protocol.begin();
  protocol.setNodeId(3);
  protocol.addPeer(1, anaMac);
  protocol.onReceive(komutGeldi);

  Serial.print("Fren ESP32 MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.println("Fren hazir, fake sinyal gonderiliyor...");
}

void loop() {
  protocol.loop();

  // Fake sinyal
  // Gercek donanim baglaninca:
  // int ham = analogRead(35);
  // float fren = (ham / 4095.0) * 100.0;
  float zaman = millis() / 1000.0;
  float fren = (sin(zaman) + 1.0) * 50.0;

  protocol.sendReliable(1, 1, (uint8_t*)&fren, sizeof(fren));
  Serial.printf("Gonderildi -> Fren: %.1f%%\n", fren);

  delay(500);
}