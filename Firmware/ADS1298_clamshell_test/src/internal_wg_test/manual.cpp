//
// Created by Oscar Tesniere on 20/06/2026.
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
constexpr byte SDATAC_CMD = 0x11;
constexpr byte RREG_CMD   = 0x20;
constexpr byte WREG_CMD   = 0x40;
constexpr byte START_CMD = 0x08;
constexpr byte RDATAC_CMD = 0x10;
constexpr byte STOP_CMD = 0x0A;
// SPI mode from ADS1298 datasheet: CPOL = 0, CPHA = 1
SPISettings adsSpi(500000, MSBFIRST, SPI_MODE1); //500kHz to start with

volatile bool drdy = false; // a flag to monitor data readiness

constexpr int ADS_CHANNELS = 8;
constexpr int ADS_FRAME_BYTES = 3 + ADS_CHANNELS*3; // 3 bytes for S.W, then 3 bytes per channel
// NOTA : we need to clock out every channel even though some are unpowered.
uint8_t frame[ADS_FRAME_BYTES];

// on the falling edge of DRDY, the data can be clocked out of the ADS1298
void IRAM_ATTR data_ready() {
    drdy = true;   // Keep ISR short
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
    SPI.transfer(uint8_t(RREG_CMD | address)); // send the 16 bit payload (byte1+byte0). SPI transfers byte by byte so here ONLY the first byte is clocked out on COPI
    SPI.transfer(0x00); // send dummy byte to clock out the second payload byte on COPI
    uint8_t readback = SPI.transfer(0x00); // send dummy byte to read register byte on CIPO
    // ADS needs 8 clock pulses to shift the register value back to us.
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
digitalWrite(START, LOW);
digitalWrite(PWDN,HIGH);
digitalWrite(RST,HIGH);

    // reset-pulse the chip
    digitalWrite(RST, LOW);
    delay(10);
    digitalWrite(RST, HIGH);
    delay(200);

SPI.begin(PIN_SCLK, PIN_CIPO, PIN_COPI, PIN_CS);


delay(500); // wait for t_POR

//TODO :  Send RST pulse, wait for 18 t_CLKs

sendCommand(SDATAC_CMD);
// disable continuous data read by sending SDATAC_CMD (stop continuous mode)
// set internal reference :
writeRegister(CONFIG3,0xC0); // WREG_CMD CONFIG3 0xC0

for(uint8_t ch_reg = 0x06; ch_reg <= 0x0C;ch_reg++){
// set channel 2-8 to input short then power them down
    writeRegister(ch_reg,0b10000001); // 0x81
    // this simultaneously sets the channel to input short and powers it down
}
// finally enable channel 1
 writeRegister(0x05, 0b00000101); // 0x00
    delay(200);  // internal reference startup
/*
    // Set Device in HR Mode and DR = fMOD/1024 WREG_CMD CONFIG1 0x86
    WREG_CMD CONFIG2 0x00
*/
Serial.println("======= BEGIN READING FROM ID REGISTER FIELDS =======");
// Now read the configuration register (ID register at address 0x00) to ensure we get proper readbacks
uint8_t id_reg = readRegister(0x00);
uint8_t dev_id = (id_reg & 0b11100000) >> 5;
Serial.print("Device ID : ");
Serial.println(dev_id,HEX);
uint8_t rsvd = (id_reg & 0b00011000) >> 3;
Serial.print("Reserved field : ");
Serial.println(rsvd,HEX);
uint8_t ch_id = id_reg & 0b00000111;
Serial.print("Channel ID : ");
Serial.println(ch_id,HEX);

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
Serial.print("Output data rate field");
Serial.println(data_r,HEX);
Serial.println("======= END READING FROM REGISTER1 FIELDS =======");

delay(1000);
Serial.print("sending STOP command");
//Send start command to start conversion
sendCommand(STOP_CMD);
Serial.println("Sending command to initialize internal routing");
writeRegister(CONFIG2, 0x54);
Serial.println("Sending RDATAC command to start reading continuously");
    sendCommand(RDATAC_CMD);
    digitalWrite(START, HIGH);
    delayMicroseconds(10);
    sendCommand(START_CMD);

Serial.println("Attaching interrupt pin for DRDY");
    attachInterrupt(
          digitalPinToInterrupt(DRDY),
          data_ready,
          FALLING
        );
}
// ADS1298 always outputs 24 status bits + 8 x 24-bit channels = 27 bytes.
// Powered-down channels output zero, but still occupy their slots.

// Helper functions to convert the ADC code to voltage (signed)

// [byte 0][byte 1][byte 2] = need to shift everything
int32_t signExtend24(uint32_t raw){
// look at the MSB, if its 0 then simply dupplicate 0 to make a
raw &= 0xFFFFFFUL;
// as a safety mask out the bit past bit 23

if(raw & 0x800000UL){ // i.e if bit 23 is 1
// fill remaining bits with 1s
raw |= 0xFF000000UL;
}
// else the remaining bits will be padded with 0s
return (int32_t)raw;
}

int32_t read_24bit(const uint8_t* payload) {
    uint32_t raw =
        ((uint32_t)payload[0] << 16) |
        ((uint32_t)payload[1] << 8)  |
        ((uint32_t)payload[2]);

    return signExtend24(raw);
}
 // this will update the variable raw by taking a pointer to an array of bytes read from CIPO


void readFrame(uint8_t *buf){
// reads a frame and parses it into an array of bytes (not bounded to any size for flexibility)
    SPI.beginTransaction(adsSpi);
    digitalWrite(PIN_CS, LOW);
    delayMicroseconds(2);
    for(uint8_t i = 0; i<ADS_FRAME_BYTES;i++){
    // clock out the bytes by sending dummy zeros
    buf[i] = SPI.transfer(0x00);
    }

    delayMicroseconds(2);
    digitalWrite(PIN_CS, HIGH);
    delayMicroseconds(2);
    SPI.endTransaction();
    delayMicroseconds(10);
}

float codeToVolts(int32_t code, float vref, float gain) {
    return ((float)code * vref) / (gain * 8388607.0f);
}


/*
SDATAC
WREG CONFIG2 0b 000|1|0|1|00
WREG CHnSET 0x05
RDATAC
Look for DRDY and Issue 24 + n * 24 SCLKs

for TST_FREQ = 00 ; the frequency is 0.97Hz
for TST_FREQ = 01 ; the frequency is 1.95Hz
*/


void loop(){
    if (!drdy) {
        return;
    }
    drdy = false;
    // we dont care about teh status word
    readFrame(frame);
    int32_t ch1_code = read_24bit(&frame[3]);  // CH1 starts at byte 3
    float ch1_volts = codeToVolts(ch1_code, 2.4f, 6.0f);
    Serial.println(ch1_volts * 1000.0f, 6);
     // gain is 6

}