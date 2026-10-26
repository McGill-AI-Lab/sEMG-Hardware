//
// Created by Oscar Tesniere on 05/06/2026.
// This script will attempt to read / write registers to check correct SPI communication with the chip
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

volatile bool adsDataReady = false;

// ADS1298 commands
constexpr uint8_t CMD_SDATAC = 0x11;
constexpr uint8_t CMD_RREG   = 0x20;
constexpr uint8_t CMD_WREG   = 0x40;

// ADS1298 registers
constexpr uint8_t REG_ID      = 0x00;
constexpr uint8_t REG_CONFIG1 = 0x01;

byte buf[8];
int32_t ch[8];

SPISettings adsSpi(500000, MSBFIRST, SPI_MODE1); // ADS1298: CPOL=0, CPHA=1

void adsSelect() {
    digitalWrite(PIN_CS, LOW);
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
    SPI.beginTransaction(adsSpi);
    adsSelect();
    adsXfer(cmd);
    adsDeselect();
    SPI.endTransaction();

    delayMicroseconds(10);
}

uint8_t adsReadRegister(uint8_t reg) {
    uint8_t value;

    SPI.beginTransaction(adsSpi);
    adsSelect();

    adsXfer(CMD_RREG | reg);  // first byte: 001r rrrr
    adsXfer(0x00);            // second byte: read 1 register => n-1 = 0
    value = adsXfer(0x00);    // dummy byte clocks out register value

    adsDeselect();
    SPI.endTransaction();

    return value;
}

void adsWriteRegister(uint8_t reg, uint8_t value) {
    SPI.beginTransaction(adsSpi);
    adsSelect();

    adsXfer(CMD_WREG | reg);  // first byte: 010r rrrr
    adsXfer(0x00);            // second byte: write 1 register => n-1 = 0
    adsXfer(value);

    adsDeselect();
    SPI.endTransaction();

    delayMicroseconds(10);
}

// interrupt routine to set ready flag and start clocking out the 256 bits
void IRAM_ATTR adsDrdyISR() {
    adsDataReady = true;
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(PIN_CS, OUTPUT);
    pinMode(PIN_RST, OUTPUT);
    pinMode(PIN_PWDN, OUTPUT);
    pinMode(PIN_DRDY, INPUT);

    // Hardware reset pulse
    digitalWrite(PIN_RST, LOW);
    delay(10);
    digitalWrite(PIN_RST, HIGH);
    delay(200);


    attachInterrupt(digitalPinToInterrupt(PIN_DRDY), adsDrdyISR, FALLING);

    // turn on these active low pins for now
    digitalWrite(PIN_CS, HIGH);
    digitalWrite(PIN_PWDN, HIGH);

    digitalWrite(PIN_START, LOW); // keep conversions stopped for this test

    SPI.begin(PIN_SCLK, PIN_MISO, PIN_MOSI, PIN_CS);

    // After reset, ADS1298 defaults to RDATAC mode.
    // Stop continuous data mode before using RREG/WREG.
    adsCommand(CMD_SDATAC);

    Serial.println("ADS1298 SPI register test started");
}


void loop() {
    uint8_t id = adsReadRegister(REG_ID);
    uint8_t config1_before = adsReadRegister(REG_CONFIG1);

    // CONFIG1 reset default is typically 0x06.
    // Write a harmless nearby value, read it back, then restore.
    adsWriteRegister(REG_CONFIG1, 0x86);
    uint8_t config1_written = adsReadRegister(REG_CONFIG1);

    adsWriteRegister(REG_CONFIG1, 0x06);
    uint8_t config1_restored = adsReadRegister(REG_CONFIG1);
/*
So for CONFIG1, 0x86 means:

Bit 7  HR        = 1
Bit 6  DAISY_EN  = 0
Bit 5  CLK_EN    = 0
Bit 4  reserved  = 0
Bit 3  reserved  = 0
Bit 2  DR2       = 1
Bit 1  DR1       = 1
Bit 0  DR0       = 0
*/

    Serial.print("ID = 0x");
    Serial.print(id, HEX);

    Serial.print(" | CONFIG1 before = 0x");
    Serial.print(config1_before, HEX);

    Serial.print(" | after write 0x86 = 0x");
    Serial.print(config1_written, HEX);

    Serial.print(" | restored = 0x");
    Serial.println(config1_restored, HEX);

    delay(1000);
}

// To test the internal test source and read it on channel 8

/*
 *The datasheet says: do not run SCLK continuously while CS is high. TI says free-running SCLK operation is not supported; SCLK should only be active during actual SPI transfers with CS low
 **/

// RDATA "001 0010"

/*
 Datasheet says to keep DIN low during the entire READ operation
 So to ensure DIN stays low, transmit dummy 0x00 bytes on MOSI : SPI.transfer(0x00);
*/
/*
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
ID = 0x92 | CONFIG1 before = 0x6 | after write 0x86 = 0x86 | restored = 0x6
*/