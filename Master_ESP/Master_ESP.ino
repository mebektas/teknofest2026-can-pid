#include <ESPNowProtocol.h>
#include <WiFi.h>

uint8_t gazMac[]        = {0xD4, 0xE9, 0xF4, 0xE3, 0x56, 0xD0};
uint8_t frenMac[]       = {0x94, 0xB9, 0x7E, 0xD9, 0xE4, 0x48};
uint8_t direksiyonMac[] = {0x70, 0x4B, 0xCA, 0x49, 0xE5, 0xD8};
uint8_t roleMac[]       = {0x88, 0x57, 0x21, 0x59, 0x6C, 0xC8};

ESPNowProtocol protocol;

float gaz        = 0.0;
float fren       = 0.0;
float direksiyon = 0.0;
bool  role       = false;

void veriGeldi(uint8_t src, uint8_t id, const uint8_t *data, uint8_t len, int8_t rssi) {
  switch (src) {
    case 2:
      memcpy(&gaz, data, sizeof(gaz));
      Serial.printf("GAZ <- %.1f%%  (RSSI: %d)\n", gaz, rssi);
      break;
    case 3:
      memcpy(&fren, data, sizeof(fren));
      Serial.printf("FREN <- %.1f%%  (RSSI: %d)\n", fren, rssi);
      break;
    case 4:
      memcpy(&direksiyon, data, sizeof(direksiyon));
      Serial.printf("DIREKSIYON <- %.1f derece  (RSSI: %d)\n", direksiyon, rssi);
      break;
    case 5:
      memcpy(&role, data, sizeof(role));
      Serial.printf("ROLE <- %s  (RSSI: %d)\n", role ? "ACIK" : "KAPALI", rssi);
      break;
    default:
      Serial.printf("BILINMEYEN NODE: %d\n", src);
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  protocol.begin();
  protocol.setNodeId(1);
  protocol.addPeer(2, gazMac);
  protocol.addPeer(3, frenMac);
  protocol.addPeer(4, direksiyonMac);
  protocol.addPeer(5, roleMac);
  protocol.onReceive(veriGeldi);

  Serial.print("Master MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.println("Master hazir, slave'ler bekleniyor...");
}

unsigned long sonKomutZamani = 0;

void loop() {
  protocol.loop();

  if (millis() - sonKomutZamani > 2000) {
    sonKomutZamani = millis();

    float gazKomut = 0.0;
    protocol.sendReliable(2, 1, (uint8_t*)&gazKomut, sizeof(gazKomut));
    Serial.printf("GAZ KOMUT -> %.1f%%\n", gazKomut);

    float frenKomut = 0.0;
    protocol.sendReliable(3, 1, (uint8_t*)&frenKomut, sizeof(frenKomut));
    Serial.printf("FREN KOMUT -> %.1f%%\n", frenKomut);

    float direksiyonKomut = 0.0;
    protocol.sendReliable(4, 1, (uint8_t*)&direksiyonKomut, sizeof(direksiyonKomut));
    Serial.printf("DIREKSIYON KOMUT -> %.1f derece\n", direksiyonKomut);

    bool roleKomut = true;
    protocol.sendReliable(5, 1, (uint8_t*)&roleKomut, sizeof(roleKomut));
    Serial.printf("ROLE KOMUT -> %s\n", roleKomut ? "ACIK" : "KAPALI");
  }
}