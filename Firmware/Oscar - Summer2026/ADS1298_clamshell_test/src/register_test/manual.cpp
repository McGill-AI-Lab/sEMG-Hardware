//
// Created by Oscar Tesniere on 19/06/2026.
//

// TRY TO ABSTRACT the ADS select / deselect code as much as possible. For this reason i created the sendCommand so that the CS toggling and SPI start/end transaction logic is encapsulated and the user doesn't have to worry about that
#include <Arduino.h>
#include <SPI.h>

// control pins
constexpr int RST = 6;
constexpr int PWDN = 7;
constexpr int START = 12;
constexpr int DRDY = 15;

// SPI pins (are these default pins?)
constexpr int PIN_CS = 16;
constexpr int PIN_COPI = 17;
constexpr int PIN_SCLK = 18;
constexpr int PIN_CIPO = 19;

constexpr byte CONFIG3 = 0x03;
constexpr byte CONFIG2 = 0x02;
constexpr byte CONFIG1 = 0x01;
constexpr byte  SDATAC_CMD = 0x11;
constexpr byte RREG_CMD   = 0x20;
constexpr byte WREG_CMD   = 0x40;

// SPI mode from ADS1298 datasheet: CPOL = 0, CPHA = 1
SPISettings adsSpi(500000, MSBFIRST, SPI_MODE1); //500kHz to start with

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
void writeRegister(uint8_t address, uint8_t payload){
    // 8 bit payload
    // To write to the register we need to send two bytes
    uint8_t bytes[] = {
        uint8_t(WREG_CMD | address),  // command byte: 010r rrrr
        0x00,                         // number of registers - 1, so 0x00 = one register
        payload                         // register payload
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

uint8_t readRegister(uint8_t address){
    // 8 bit payload
    // To write to the register we need to send two bytes
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

void setup(){

Serial.begin(115200);

pinMode(RST,OUTPUT);
pinMode(PWDN,OUTPUT);
pinMode(DRDY,INPUT);
pinMode(START,OUTPUT);
pinMode(PIN_CS, OUTPUT);

digitalWrite(PIN_CS, HIGH);

SPI.begin(PIN_SCLK, PIN_CIPO, PIN_COPI, PIN_CS);


delay(500); // startup time for the oscillator
digitalWrite(PWDN,HIGH);
digitalWrite(RST,HIGH);
delay(500); // wait for t_POR

//TODO :  Send RST pulse, wait for 18 t_CLKs

sendCommand(SDATAC_CMD);
// disable continuous data read by sending SDATAC (stop continuous mode)
// set internal reference :
writeRegister(CONFIG3,0xC0); // WREG CONFIG3 0xC0

for(uint8_t ch_reg = 0x06; ch_reg <= 0x0C;ch_reg++){
// set channel 2-8 to input short then power them down
    writeRegister(ch_reg,0b10000001); // 0x81
    // this simultaneously sets the channel to input short and powers it down
}
// finally enable channel 1
 writeRegister(0x05, 0b00000000); // 0x00
delayMicroseconds(2);
/*
    // Set Device in HR Mode and DR = fMOD/1024 WREG CONFIG1 0x86
    WREG CONFIG2 0x00
*/

    Serial.println("======= BEGIN READING FROM ID REGISTER FIELDS =======");
// Now read the configuration register (ID register at address 0x00) to ensure we get proper readbacks
uint8_t id_reg = readRegister(0x00);
uint8_t dev_id = (id_reg & 0b11100000) >> 5;
Serial.print("Device ID : ");
Serial.println(dev_id,HEX);
if(dev_id==4){
Serial.println("Detected ADC is `ADS129x device family`. This checks out !");
}
//uint8_t rsvd = (id_reg & 0b00011000) >> 3;
//Serial.print("Reserved field : ");
//Serial.println(rsvd,HEX);
uint8_t ch_id = id_reg & 0b00000111;
Serial.print("Channel ID : ");
Serial.println(ch_id,HEX);
 if(ch_id==2){
        Serial.println("Detected ADC is `8-channel ADS1298`. This checks out !");
  }

Serial.println("======= END READING FROM ID REGISTER FIELDS =======");
delay(1000);
Serial.println("======= BEGIN READING FROM REGISTER1 FIELDS =======");
uint8_t reg_1 = readRegister(CONFIG1);
uint8_t highRes = (reg_1 & 0b10000000) >> 7;
Serial.print("High resolution mode bit : ");
Serial.println(highRes,HEX);
uint8_t daisy_en = (reg_1 & 0b01000000) >> 6;
Serial.print("Daisy chain mode bit : ");
Serial.println(daisy_en,HEX);
// skipped reserved bit field
uint8_t data_r = reg_1 & 0b00000111;
Serial.print("Output data rate field : ");
Serial.println(data_r,HEX);
Serial.println("======= END READING FROM REGISTER1 FIELDS =======");
}
void loop(){
// do nothing for now
}