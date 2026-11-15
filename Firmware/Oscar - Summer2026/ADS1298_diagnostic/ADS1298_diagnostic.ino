// Standalone Arduino diagnostic for ESP32-S3 -> ADS1298 SPI.
// USB-to-UART connector; Serial Monitor at 115200 baud.
// Keep the function generator output OFF. No ADC conversions are started.
#include <Arduino.h>
#include <SPI.h>

constexpr int ADS_RST = 6, ADS_PWDN = 7, ADS_START = 12;
constexpr int ADS_DRDY = 15, ADS_CS = 16;
constexpr int ADS_MOSI = 17, ADS_SCLK = 18, ADS_MISO = 19;
SPISettings adsSPI(250000, MSBFIRST, SPI_MODE1);

void selectADS() {
  SPI.beginTransaction(adsSPI);
  digitalWrite(ADS_CS, LOW);
  delayMicroseconds(10);
}

void deselectADS() {
  delayMicroseconds(10);
  digitalWrite(ADS_CS, HIGH);
  SPI.endTransaction();
  delayMicroseconds(10);
}

void commandADS(uint8_t command) {
  selectADS();
  SPI.transfer(command);
  deselectADS();
}

uint8_t readADS(uint8_t address) {
  selectADS();
  SPI.transfer(uint8_t(0x20 | address));
  delayMicroseconds(5);
  SPI.transfer(0x00);
  delayMicroseconds(5);
  uint8_t value = SPI.transfer(0x00);
  deselectADS();
  return value;
}

void writeADS(uint8_t address, uint8_t value) {
  selectADS();
  SPI.transfer(uint8_t(0x40 | address));
  delayMicroseconds(5);
  SPI.transfer(0x00);
  delayMicroseconds(5);
  SPI.transfer(value);
  deselectADS();
}

void setup() {
  Serial0.begin(115200); // Explicit UART0, regardless of USB CDC setting.
  delay(2000);
  Serial0.println("ADS1298 REGISTER DIAGNOSTIC - no waveform acquisition");

  // Preload output levels before enabling output drivers.
  digitalWrite(ADS_CS, HIGH);
  digitalWrite(ADS_START, LOW);
  digitalWrite(ADS_RST, HIGH);
  digitalWrite(ADS_PWDN, LOW);
  pinMode(ADS_CS, OUTPUT);
  pinMode(ADS_START, OUTPUT);
  pinMode(ADS_RST, OUTPUT);
  pinMode(ADS_PWDN, OUTPUT);
  pinMode(ADS_DRDY, INPUT);
  SPI.begin(ADS_SCLK, ADS_MISO, ADS_MOSI, ADS_CS);

  delay(20);
  digitalWrite(ADS_PWDN, HIGH);
  delay(1000); // Conservative wake-up wait before issuing reset.
  digitalWrite(ADS_RST, LOW);
  delay(10);
  digitalWrite(ADS_RST, HIGH);
  delay(50);
  commandADS(0x11); // SDATAC: enable register access.
  commandADS(0x0A); // STOP; START pin also remains low.
  Serial0.println("Readbacks repeat every second. CONFIG1 write/read is tested only with nonzero/non-FF ID.");
}

void loop() {
  uint8_t id = readADS(0x00);
  uint8_t before = readADS(0x01);
  uint8_t config2 = readADS(0x02);
  uint8_t config3 = readADS(0x03);
  Serial0.printf("ID=0x%02X CONFIG1=0x%02X CONFIG2=0x%02X CONFIG3=0x%02X DRDY=%d\n",
                 id, before, config2, config3, digitalRead(ADS_DRDY));
  if (id == 0x00 || id == 0xFF) {
    Serial0.println("FAIL: invalid ID readback; register writes skipped.");
  } else {
    // A nonzero/non-FF ID alone does not establish correct device identity.
    writeADS(0x01, 0x85);
    uint8_t written = readADS(0x01);
    writeADS(0x01, before);
    uint8_t restored = readADS(0x01);
    Serial0.printf("CONFIG1 wrote 0x85 -> read 0x%02X; restored 0x%02X -> read 0x%02X: %s\n",
                   written, before, restored,
                   written == 0x85 && restored == before ? "PASS" : "FAIL");
  }
  delay(1000);
}
