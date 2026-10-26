//
// Created by Oscar Tesniere on 05/06/2026.
// This scripts turns off all channels except channel 1, which it connects to the test signal generator through the internal MUX, then transfers the digitalized value to the ESP through SPI
//
#include <Arduino.h>
#include <SPI.h>

// ESP32-S3 pins
constexpr int PIN_SCLK  = 18;
constexpr int PIN_MISO  = 19;  // ADS1298 DOUT
constexpr int PIN_MOSI  = 17;  // ADS1298 DIN
constexpr int PIN_CS    = 16;

constexpr int PIN_START = 12;
constexpr int PIN_PWDN  = 7;
constexpr int PIN_RST   = 6;
constexpr int PIN_DRDY  = 15;

// ADS1298 frame size: 24-bit status + 8 x 24-bit channels
constexpr int ADS_CHANNELS = 8;
constexpr int ADS_FRAME_BYTES = 3 + ADS_CHANNELS * 3;

// SPI mode from ADS1298 datasheet: CPOL = 0, CPHA = 1
SPISettings adsSpi(500000, MSBFIRST, SPI_MODE1);

volatile bool adsDataReady = false;
uint8_t frame[ADS_FRAME_BYTES];

// ADS1298 commands
constexpr uint8_t CMD_WAKEUP = 0x02;
constexpr uint8_t CMD_STANDBY = 0x04;
constexpr uint8_t CMD_RESET = 0x06;
constexpr uint8_t CMD_START = 0x08;
constexpr uint8_t CMD_STOP = 0x0A;
constexpr uint8_t CMD_RDATAC = 0x10;
constexpr uint8_t CMD_SDATAC = 0x11;
constexpr uint8_t CMD_RDATA = 0x12;
constexpr uint8_t CMD_RREG = 0x20;
constexpr uint8_t CMD_WREG = 0x40;

// ADS1298 registers
constexpr uint8_t REG_ID      = 0x00;
constexpr uint8_t REG_CONFIG1 = 0x01;
constexpr uint8_t REG_CONFIG2 = 0x02;
constexpr uint8_t REG_CONFIG3 = 0x03;
constexpr uint8_t REG_CH1SET  = 0x05; // for channel 1
constexpr uint8_t REG_CH2SET  = 0x06;
constexpr uint8_t REG_CH8SET  = 0x0C;
constexpr uint8_t REG_CONFIG4 = 0x17;

// Register values used here
//
// CONFIG1:
// 0x06 = reset default: high-resolution mode, daisy-chain enabled,
//       CLK output disabled, 500 SPS with internal 2.048 MHz clock.
// This is fine for first testing.
//
// CONFIG2:
// bit 4 INT_TEST = 1
// bit 2 TEST_AMP = 0 => ±1 mV nominal
// bits 1:0 TEST_FREQ = 01 => fCLK / 2^20
// bit 7 should remain like reset value; CONFIG2 reset is 0x40.
// 0x40 | 0x10 | 0x01 = 0x51
constexpr uint8_t CONFIG2_INTERNAL_TEST_1MV_2HZ = 0x51;

// CONFIG3:
// reset is 0x40.
// bit 7 PD_REFBUF = 1 => internal reference buffer powered up
// bit 6 must be 1
// bit 5 VREF_4V = 0 => 2.4 V reference, correct for 3.3 V AVDD
// So 0xC0 enables internal reference buffer.
constexpr uint8_t CONFIG3_INTERNAL_REF_2V4 = 0xC0;

// CHnSET:
// bit 7 PDn = power down
// bits 6:4 gain: 000 = gain 6
// bit 3 reserved = 0
// bits 2:0 mux
//
// CH1: normal operation, gain 6, mux = 101 test signal => 0x05
constexpr uint8_t CH_TEST_SIGNAL_GAIN6 = 0x05;

// Unused channels: power down + mux shorted.
// bit 7 = 1, mux = 001 => 0x81
constexpr uint8_t CH_POWERDOWN_SHORTED = 0x81;

void IRAM_ATTR adsDrdyISR() {
  adsDataReady = true;
}

void adsSelect() {
  digitalWrite(PIN_CS, LOW);
  // pull CS low to select the ADS1298 then let a small delay to settle.
  delayMicroseconds(2);
}

void adsDeselect() {
  delayMicroseconds(2);
  digitalWrite(PIN_CS, HIGH);
  delayMicroseconds(2);
}

uint8_t adsXfer(uint8_t b) {
  return SPI.transfer(b);
}

void adsCommand(uint8_t cmd) {
 // check that this correctly starts the SCLK clock
  SPI.beginTransaction(adsSpi);
  adsSelect();
 //TODO might need to swap beginTransaction and adsSelect if timing issue
  adsXfer(cmd);
  adsDeselect();
  SPI.endTransaction();

  delayMicroseconds(10);
}

void adsWriteRegister(uint8_t reg, uint8_t value) {
  SPI.beginTransaction(adsSpi);
  adsSelect();

  adsXfer(CMD_WREG | reg);
  // From the datasheet : upper 3 bits are for command (CMD_REG) and lower 5 bits are for the register address (reg)
  // 010r rrrr where 010 is WREG, and the r's make up the 5-bit address of the register to write to.
  adsXfer(0x00);      // write one register: number of registers - 1
  adsXfer(value);

  adsDeselect();
  SPI.endTransaction();

  delayMicroseconds(10);
}

uint8_t adsReadRegister(uint8_t reg) {
  uint8_t value;

  SPI.beginTransaction(adsSpi);
  adsSelect();

  adsXfer(CMD_RREG | reg);
  adsXfer(0x00);      // read one register: number of registers - 1
  value = adsXfer(0x00);

  adsDeselect();
  SPI.endTransaction();

  return value;
}

int32_t signExtend24(uint32_t x) {
  if (x & 0x800000UL) {
    x |= 0xFF000000UL;
  }
  return (int32_t)x;
}

int32_t readInt24(const uint8_t *p) {
  uint32_t raw =
    ((uint32_t)p[0] << 16) |
    ((uint32_t)p[1] << 8)  |
    ((uint32_t)p[2]);

  return signExtend24(raw);
}

float codeToVolts(int32_t code, float vref, float gain) {
  return ((float)code * vref) / (gain * 8388607.0f);
}

void readAdsFrame(uint8_t *buf) {
  SPI.beginTransaction(adsSpi);
  adsSelect();

  // During ADS1298 data read, keep DIN low: transmit dummy 0x00 bytes.
  for (int i = 0; i < ADS_FRAME_BYTES; i++) {
    buf[i] = adsXfer(0x00);
  }

  adsDeselect();
  SPI.endTransaction();
}

void setupAdsInternalTestMode() {
  // Stop continuous read mode before register writes.
  // ADS1298 starts in RDATAC after reset, and RREG/WREG are not usable there.
  adsCommand(CMD_SDATAC);

  // Stop conversions while configuring.
  adsCommand(CMD_STOP);
  digitalWrite(PIN_START, LOW);
  delay(10);

  // Basic config
  adsWriteRegister(REG_CONFIG1, 0x06);  // HR mode, 500 SPS
  adsWriteRegister(REG_CONFIG2, CONFIG2_INTERNAL_TEST_1MV_2HZ); // connect the internal test signal to CH1 through the MUX
  adsWriteRegister(REG_CONFIG3, CONFIG3_INTERNAL_REF_2V4); // enable the internal reference. VREFN is tied to AGND, while VREFP is bypassed by capacitors
  adsWriteRegister(REG_CONFIG4, 0x00);  // continuous conversion mode

  // Wait for internal reference startup. Datasheet gives 150 ms typical.
  delay(200);

  // CH1 reads internal test signal. CH2-CH8 powered down.
  adsWriteRegister(REG_CH1SET, CH_TEST_SIGNAL_GAIN6);

  for (uint8_t reg = REG_CH2SET; reg <= REG_CH8SET; reg++) {
    adsWriteRegister(reg, CH_POWERDOWN_SHORTED);
  }

  // Enter continuous data read mode.
  adsCommand(CMD_RDATAC);

  // Start conversions.
  digitalWrite(PIN_START, HIGH);
  delayMicroseconds(10);
  adsCommand(CMD_START);
}

void printRegisters() {
  Serial.print("ID      = 0x"); Serial.println(adsReadRegister(REG_ID), HEX);
  Serial.print("CONFIG1 = 0x"); Serial.println(adsReadRegister(REG_CONFIG1), HEX);
  Serial.print("CONFIG2 = 0x"); Serial.println(adsReadRegister(REG_CONFIG2), HEX);
  Serial.print("CONFIG3 = 0x"); Serial.println(adsReadRegister(REG_CONFIG3), HEX);
  Serial.print("CH1SET  = 0x"); Serial.println(adsReadRegister(REG_CH1SET), HEX);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PIN_CS, OUTPUT);
  pinMode(PIN_RST, OUTPUT);
  pinMode(PIN_PWDN, OUTPUT);
  pinMode(PIN_START, OUTPUT);
  pinMode(PIN_DRDY, INPUT);

  digitalWrite(PIN_CS, HIGH);
  digitalWrite(PIN_START, LOW);
  digitalWrite(PIN_PWDN, HIGH);

  // Hold MOSI low before SPI takes over, useful for ADS1298 DIN.
  pinMode(PIN_MOSI, OUTPUT);
  digitalWrite(PIN_MOSI, LOW);

  SPI.begin(PIN_SCLK, PIN_MISO, PIN_MOSI, PIN_CS);

  // Hardware reset
  digitalWrite(PIN_RST, LOW);
  delay(10);
  digitalWrite(PIN_RST, HIGH);
  delay(200);

  // First put the ADS in register-access mode so we can print sanity registers.
  adsCommand(CMD_SDATAC);

  Serial.println();
  Serial.println("ADS1298 internal test signal demo");
  Serial.println("Before setup:");
  printRegisters();

  setupAdsInternalTestMode();

  // Do not read registers while in RDATAC unless you first SDATAC.
  // So we only print this once before RDATAC, or temporarily stop RDATAC if needed.
  adsCommand(CMD_SDATAC);
  Serial.println("After setup:");
  printRegisters();
  adsCommand(CMD_RDATAC);

  attachInterrupt(digitalPinToInterrupt(PIN_DRDY), adsDrdyISR, FALLING);

  Serial.println("Streaming CH1 internal test signal...");
}

void loop() {
  if (!adsDataReady) {
    return;
  }

  adsDataReady = false;

  readAdsFrame(frame);

  uint32_t status =
    ((uint32_t)frame[0] << 16) |
    ((uint32_t)frame[1] << 8)  |
    ((uint32_t)frame[2]);

  int32_t ch1_code = readInt24(&frame[3]);  // CH1 starts at byte 3
  float ch1_volts = codeToVolts(ch1_code, 2.4f, 6.0f);

  static uint32_t n = 0;
  n++;

  // Print every sample at 500 SPS can be too much.
  // Print every 25th sample.
  Serial.println(ch1_volts * 1000.0f, 6);
  //if ((n % 25) == 0) {
    //Serial.print("status=0x");
    //Serial.print(status, HEX);

    //Serial.print("  ch1_code=");
    //Serial.print(ch1_code);

    //Serial.print("  ch1_mV : ");
    //Serial.println(ch1_volts * 1000.0f, 6);
  //}
}
/* example output
ch1_mV : -0.052595
ch1_mV : 0.000000
ch1_mV : -0.052071
ch1_mV : 0.000000
ch1_mV : -0.053358
ch1_mV : 0.287676
ch1_mV : 0.000000
ch1_mV : 0.293350
ch1_mV : 0.000000
ch1_mV : 0.293541
ch1_mV : 0.000000
ch1_mV : -0.055027
ch1_mV : 0.000000
ch1_mV : 0.000000
ch1_mV : -0.054121
ch1_mV : 0.000000
ch1_mV : 0.293112
ch1_mV : 0.000000
ch1_mV : 0.292826
ch1_mV : 0.292921
ch1_mV : 0.000000
ch1_mV : -0.054884
ch1_mV : 0.000000
ch1_mV : 0.000000
ch1_mV : -0.055504
ch1_mV : 0.000000
ch1_mV : 0.292587
ch1_mV : 0.000000
ch1_mV : 0.292778
ch1_mV : 0.000000
ch1_mV : 0.293112
ch1_mV : 0.000000
ch1_mV : -0.055933
ch1_mV : 0.000000
ch1_mV : -0.055504
ch1_mV : 0.000000
ch1_mV : 0.292349
ch1_mV : 0.000000
ch1_mV : 0.291824
ch1_mV : 0.000000
ch1_mV : 0.292492
ch1_mV : 0.000000
ch1_mV : -0.055027
ch1_mV : 0.000000
ch1_mV : -0.054550
ch1_mV : 0.000000
ch1_mV : 0.292349
ch1_mV : 0.000000
ch1_mV : 0.292492
ch1_mV : 0.000000
ch1_mV : 0.292587
ch1_mV : 0.000000
ch1_mV : -0.055122
ch1_mV : 0.000000
ch1_mV : -0.055695
ch1_mV : 0.000000
ch1_mV : 0.292015
ch1_mV : 0.000000
ch1_mV : 0.292635
ch1_mV : 0.000000
ch1_mV : 0.292492
ch1_mV : 0.000000
ch1_mV : -0.055838
ch1_mV : -0.055552
ch1_mV : 0.000000
ch1_mV : -0.055742
ch1_mV : 0.000000
ch1_mV : 0.000000
ch1_mV : 0.293160
ch1_mV : 0.000000
ch1_mV : 0.292873
ch1_mV : 0.120163
ch1_mV : 0.000000
ch1_mV : -0.055265
ch1_mV : 0.000000
ch1_mV : -0.055647
ch1_mV : 0.000000
ch1_mV : 0.292826
ch1_mV : 0.000000
ch1_mV : 0.292015
*/