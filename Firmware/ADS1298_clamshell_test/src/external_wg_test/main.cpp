//
// External function generator test for ADS1298 CH1
//

#include <Arduino.h>
#include <SPI.h>

// control pins
constexpr int RST   = 6;
constexpr int PWDN  = 7;
constexpr int START = 12;
constexpr int DRDY  = 15;

// SPI pins
constexpr int PIN_CS   = 16;
constexpr int PIN_COPI = 17;  // ESP MOSI -> ADS DIN
constexpr int PIN_SCLK = 18;
constexpr int PIN_CIPO = 19;  // ESP MISO <- ADS DOUT

// ADS1298 registers
constexpr byte REG_ID      = 0x00;
constexpr byte CONFIG1     = 0x01;
constexpr byte CONFIG2     = 0x02;
constexpr byte CONFIG3     = 0x03;
constexpr byte CH1SET      = 0x05;
constexpr byte CH2SET      = 0x06;
constexpr byte CH8SET      = 0x0C;

// ADS1298 commands
constexpr byte SDATAC_CMD  = 0x11;
constexpr byte RREG_CMD    = 0x20;
constexpr byte WREG_CMD    = 0x40;
constexpr byte START_CMD   = 0x08;
constexpr byte RDATAC_CMD  = 0x10;
constexpr byte STOP_CMD    = 0x0A;

// SPI mode from ADS1298 datasheet: CPOL = 0, CPHA = 1
SPISettings adsSpi(1000000, MSBFIRST, SPI_MODE1);

volatile bool drdy = false;

constexpr int ADS_CHANNELS = 8;
constexpr int ADS_FRAME_BYTES = 3 + ADS_CHANNELS * 3;

uint8_t frame[ADS_FRAME_BYTES];

void IRAM_ATTR data_ready() {
    drdy = true;
}

void sendCommand(uint8_t cmd) {
    SPI.beginTransaction(adsSpi);
    digitalWrite(PIN_CS, LOW);
    delayMicroseconds(2);

    SPI.transfer(cmd);

    delayMicroseconds(2);
    digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(2);
    SPI.endTransaction();

    delayMicroseconds(10);
}

void writeRegister(uint8_t address, uint8_t payload) {
    uint8_t bytes[] = {
        uint8_t(WREG_CMD | address),
        0x00,
        payload
    };

    SPI.beginTransaction(adsSpi);
    digitalWrite(PIN_CS, LOW);
    delayMicroseconds(2);

    for (uint8_t i = 0; i < sizeof(bytes); i++) {
        SPI.transfer(bytes[i]);
    }

    delayMicroseconds(2);
    digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(2);
    SPI.endTransaction();

    delayMicroseconds(10);
}

uint8_t readRegister(uint8_t address) {
    SPI.beginTransaction(adsSpi);
    digitalWrite(PIN_CS, LOW);
    delayMicroseconds(2);

    SPI.transfer(uint8_t(RREG_CMD | address));
    SPI.transfer(0x00);
    uint8_t readback = SPI.transfer(0x00);

    delayMicroseconds(2);
    digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(2);
    SPI.endTransaction();

    delayMicroseconds(10);

    return readback;
}

int32_t signExtend24(uint32_t raw) {
    raw &= 0xFFFFFFUL;

    if (raw & 0x800000UL) {
        raw |= 0xFF000000UL;
    }

    return (int32_t)raw;
}

int32_t read_24bit(const uint8_t* payload) {
    uint32_t raw =
        ((uint32_t)payload[0] << 16) |
        ((uint32_t)payload[1] << 8)  |
        ((uint32_t)payload[2]);

    return signExtend24(raw);
}

void readFrame(uint8_t *buf) {
    SPI.beginTransaction(adsSpi);
    digitalWrite(PIN_CS, LOW);
    delayMicroseconds(2);

    for (uint8_t i = 0; i < ADS_FRAME_BYTES; i++) {
        buf[i] = SPI.transfer(0x00);
    }

    delayMicroseconds(2);
    digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(2);
    SPI.endTransaction();
}

float codeToVolts(int32_t code, float vref, float gain) {
    return ((float)code * vref) / (gain * (float)((1U << 23) - 1));
}

void printRegister(const char* name, uint8_t reg) {
    Serial.print(name);
    Serial.print(" = 0x");
    Serial.println(readRegister(reg), HEX);
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(RST, OUTPUT);
    pinMode(PWDN, OUTPUT);
    pinMode(DRDY, INPUT);
    pinMode(START, OUTPUT);
    pinMode(PIN_CS, OUTPUT);

    digitalWrite(PIN_CS, HIGH);
    digitalWrite(START, LOW);
    digitalWrite(PWDN, HIGH);
    digitalWrite(RST, HIGH);

    // Keep ADS DIN low before SPI takes over
    pinMode(PIN_COPI, OUTPUT);
    digitalWrite(PIN_COPI, LOW);

    SPI.begin(PIN_SCLK, PIN_CIPO, PIN_COPI, PIN_CS);

    // Hardware reset pulse
    digitalWrite(RST, LOW);
    delay(10);
    digitalWrite(RST, HIGH);
    delay(200);

    // Stop continuous read mode before register writes
    sendCommand(SDATAC_CMD);
    sendCommand(STOP_CMD);
    digitalWrite(START, LOW);

    // CONFIG1:
    // 0x85 = high-resolution mode, 1 kSPS
    // HR=1, DR[2:0]=101
    writeRegister(CONFIG1, 0x85);

    // CONFIG2:
    // 0x40 = reset/default-style value with internal test generator disabled.
    // Important: INT_TEST = 0 here.
    writeRegister(CONFIG2, 0x40);

    // CONFIG3:
    // 0xC0 = internal reference buffer enabled, 2.4 V reference
    writeRegister(CONFIG3, 0xC0);

    delay(200);  // internal reference startup

    // CH1SET:
    // 0x00 = channel on, gain 6, normal electrode input.
    // This means CH1 reads IN1P - IN1N.
    writeRegister(CH1SET, 0x00);

    // CH2-CH8 powered down and shorted
    for (uint8_t ch_reg = CH2SET; ch_reg <= CH8SET; ch_reg++) {
        writeRegister(ch_reg, 0x81);
    }

    Serial.println("======= ADS REGISTER CHECK =======");
    printRegister("ID     ", REG_ID);
    printRegister("CONFIG1", CONFIG1);
    printRegister("CONFIG2", CONFIG2);
    printRegister("CONFIG3", CONFIG3);
    printRegister("CH1SET ", CH1SET);
    Serial.println("==================================");

    // Enter continuous read mode
    sendCommand(RDATAC_CMD);

    // Start conversions
    digitalWrite(START, HIGH);
    delayMicroseconds(10);
    sendCommand(START_CMD);

    drdy = false;
    attachInterrupt(digitalPinToInterrupt(DRDY), data_ready, FALLING);

    Serial.println("Streaming external function generator signal on CH1...");
}

void loop() {
    if (!drdy) {
        return;
    }

    drdy = false;

    readFrame(frame);

    int32_t ch1_code = read_24bit(&frame[3]);
    float ch1_volts = codeToVolts(ch1_code, 2.4f, 3.0f);

    // Print millivolts for Python plotting
    Serial.println(ch1_volts * 1000.0f, 6);
}