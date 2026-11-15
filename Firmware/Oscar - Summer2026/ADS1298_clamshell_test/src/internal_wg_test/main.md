# ADS1298 internal waveform test: beginner's guide to `main.cpp`

This document explains [`main.cpp`](./main.cpp) for someone with no previous C++ or embedded-development experience. It covers what the program is trying to do, how the ESP32-S3 and ADS1298 communicate, what the important C++ constructs mean, what each function does, and what should be fixed next.

## What this program is trying to prove

The program performs a self-test without using the external function generator or the physical channel inputs. The ADS1298 contains its own small calibration signal generator. The program:

1. starts the ESP32-S3 serial and SPI peripherals;
2. resets the ADS1298;
3. enables the ADS1298 internal reference and internal test generator;
4. connects that test generator to channel 1 through the ADS1298's internal multiplexer;
5. powers down channels 2 through 8;
6. starts repeated analog-to-digital conversions;
7. waits for the ADS1298 to announce that each result is ready;
8. reads the complete 27-byte result frame over SPI;
9. extracts channel 1's signed 24-bit number;
10. converts that number to volts; and
11. prints millivolts to the laptop over USB-to-UART.

This test covers much of the digital path and the internal channel-1 signal path. It does **not** test the external function generator, the IN1P/IN1N pins, electrode wiring, or the external analog front end.

## The two data paths

There are two different processes: uploading the program and running the measurement.

### Uploading firmware

```text
main.cpp
   │ compiled on laptop
   ▼
ESP32 machine-code binary
   │ USB cable / CP2102N USB-to-UART bridge
   ▼
ESP32-S3 flash memory
```

The laptop compiles the C++ source into machine code. The upload tool sends that binary through the USB-to-UART bridge. The ESP32 bootloader writes it into flash memory. After reset, the ESP32 executes the program from its own memory. The ADS1298 does not execute any of this C++ code.

### Running the internal-signal test

```text
                 control/configuration
ESP32-S3  ─────────────────────────────────► ADS1298
           CS, SCLK, DIN, RESET, START, PWDN

Inside ADS1298:
internal test generator → CH1 MUX → gain-6 PGA → ADC → digital filter
                                                        │
                                                        ▼
ESP32-S3 ◄──── DOUT/SPI frame ─── ADS1298 signals DRDY low
   │
   │ UART text through CP2102N and USB
   ▼
laptop Serial Monitor
```

SPI is used between the ESP32 and ADS1298. UART is used between the ESP32 and laptop. They are separate communication links with different pins and speeds.

## Power is separate from firmware

The program cannot create power on an ordinary GPIO. In this setup, the ESP32 DevKit's physical `3V3` power pin supplies the breadboard rail. That rail supplies ADS1298 AVDD/AVDD1 and DVDD. ESP32 GND and the ADS1298 grounds must share a common ground.

The earlier `0x00` register readings occurred while the ADS1298 power rail was not connected. After connecting 3.3 V, the diagnostic returned `ID=0x92` and passed a register write/read test. That proves the ADS1298 is now powered and SPI register communication works.

## Small C++ and Arduino primer

### Header files

```cpp
#include <Arduino.h>
#include <SPI.h>
```

`Arduino.h` provides Arduino functions such as `pinMode`, `digitalWrite`, `delay`, `Serial`, `setup`, and `loop`. `SPI.h` provides the ESP32 SPI interface.

### Constants and types

```cpp
constexpr int PIN_SCLK = 18;
constexpr uint8_t CMD_START = 0x08;
```

`constexpr` means a value is fixed at compile time. Giving values names makes the code easier to understand and prevents accidental changes.

Common types in this program are:

| Type | Meaning |
|---|---|
| `bool` | `true` or `false` |
| `uint8_t` | an unsigned 8-bit integer, 0 through 255; one byte |
| `uint32_t` | an unsigned 32-bit integer |
| `int32_t` | a signed 32-bit integer |
| `int` | a normal signed integer used for pins and loop counters |
| `float` | a number with a fractional part |

### Decimal, hexadecimal, and binary

The same value can be written in several ways:

```text
decimal  17
hex      0x11
binary   0b00010001
```

Hexadecimal is convenient for registers because one hex digit represents four bits. ADS1298 registers are eight bits, so they are usually shown using two hex digits.

### Functions

```cpp
uint8_t adsReadRegister(uint8_t reg) {
    // work performed by the function
    return value;
}
```

A function groups a reusable operation. The type before the name is the returned result. Values inside parentheses are inputs. `void` means the function returns no value.

### Arrays and pointers

```cpp
uint8_t frame[ADS_FRAME_BYTES];
int32_t readInt24(const uint8_t *p);
```

`frame` is a sequence of bytes stored in ESP32 RAM. `p` is a pointer: it holds the location of a byte in memory. Calling `readInt24(&frame[3])` passes the address of byte 3, which is where channel 1 begins.

### Bit operations

```cpp
CMD_WREG | reg
((uint32_t)p[0] << 16)
```

`|` combines bit fields. It is used to combine the WREG command bits with a register address. `<<` shifts bits left and is used to rebuild a 24-bit ADC value from three separate bytes.

### Arduino `setup()` and `loop()`

Arduino calls `setup()` once after boot or reset. It then calls `loop()` repeatedly for as long as the board runs.

## Pin definitions

```cpp
constexpr int PIN_SCLK  = 18;
constexpr int PIN_MISO  = 19;
constexpr int PIN_MOSI  = 17;
constexpr int PIN_CS    = 16;
constexpr int PIN_START = 12;
constexpr int PIN_PWDN  = 7;
constexpr int PIN_RST   = 6;
constexpr int PIN_DRDY  = 15;
```

These names map ESP32 GPIO numbers to ADS1298 signals:

| Code name | ESP32 pin | ADS1298 direction | Purpose |
|---|---:|---|---|
| `PIN_SCLK` | 18 | ESP → ADS | SPI clock; the ESP creates clock pulses during communication |
| `PIN_MOSI` | 17 | ESP → ADS DIN | commands and register values sent to the ADS |
| `PIN_MISO` | 19 | ADS DOUT → ESP | register values and sample data returned by the ADS |
| `PIN_CS` | 16 | ESP → ADS | chip select; low means the ESP is talking to the ADS |
| `PIN_START` | 12 | ESP → ADS | starts or stops ADC conversions |
| `PIN_PWDN` | 7 | ESP → ADS | active-low hardware power-down control |
| `PIN_RST` | 6 | ESP → ADS | active-low hardware reset |
| `PIN_DRDY` | 15 | ADS → ESP | falls low when a new conversion frame is ready |

`MOSI` and `MISO` are generic SPI names. In the ADS1298 datasheet they are called DIN and DOUT.

SCLK is only the serial communication clock. It is not the ADS1298 master conversion clock. This design ties CLKSEL high so the ADS1298 uses its internal master oscillator.

## SPI configuration

```cpp
SPISettings adsSpi(500000, MSBFIRST, SPI_MODE1);
```

This requests:

- a 500 kHz SPI clock;
- most-significant bit first; and
- SPI mode 1, which means clock polarity 0 and clock phase 1.

The ADS1298 requires SPI mode 1. The 500 kHz speed is deliberately conservative.

## The ADS frame buffer

```cpp
constexpr int ADS_CHANNELS = 8;
constexpr int ADS_FRAME_BYTES = 3 + ADS_CHANNELS * 3;
uint8_t frame[ADS_FRAME_BYTES];
```

Each ADS1298 result contains:

```text
3 status bytes + 8 channels × 3 bytes/channel = 27 bytes
```

The layout is:

| Byte indexes | Contents |
|---|---|
| 0–2 | 24-bit status word |
| 3–5 | channel 1 |
| 6–8 | channel 2 |
| 9–11 | channel 3 |
| 12–14 | channel 4 |
| 15–17 | channel 5 |
| 18–20 | channel 6 |
| 21–23 | channel 7 |
| 24–26 | channel 8 |

Powered-down channels still occupy their three-byte positions. The ESP must clock out all 27 bytes to keep the frame aligned.

## Commands versus registers

Commands and registers are related but different:

- A **command** tells the ADS1298 to perform an action, such as start conversions.
- A **register** stores configuration bits, such as a channel's gain and input selection.

The command constants are the byte values defined by the ADS1298 protocol:

| Constant | Value | Action |
|---|---:|---|
| `CMD_WAKEUP` | `0x02` | leave standby |
| `CMD_STANDBY` | `0x04` | enter standby |
| `CMD_RESET` | `0x06` | software reset |
| `CMD_START` | `0x08` | start conversions |
| `CMD_STOP` | `0x0A` | stop conversions |
| `CMD_RDATAC` | `0x10` | enter continuous-data-read mode |
| `CMD_SDATAC` | `0x11` | stop continuous-data-read mode |
| `CMD_RDATA` | `0x12` | request one data frame |
| `CMD_RREG` | `0x20` | base bits for reading registers |
| `CMD_WREG` | `0x40` | base bits for writing registers |

The program defines addresses for registers it uses:

| Register | Address | Purpose |
|---|---:|---|
| `REG_ID` | `0x00` | identifies the device and number of channels |
| `REG_CONFIG1` | `0x01` | operating mode and sample rate |
| `REG_CONFIG2` | `0x02` | internal test-signal configuration |
| `REG_CONFIG3` | `0x03` | internal reference and RLD configuration |
| `REG_CH1SET` | `0x05` | channel 1 power, gain, and input MUX |
| `REG_CH2SET` | `0x06` | channel 2 settings |
| `REG_CH8SET` | `0x0C` | channel 8 settings |
| `REG_CONFIG4` | `0x17` | continuous/single-shot and lead-off options |

Register access is not allowed while the ADS1298 is in RDATAC mode. That is why the code sends SDATAC before reading or writing registers.

## Important register values

### `CONFIG1 = 0x06`

The source comments are wrong here. `0x06` means:

```text
bit 7 HR       = 0  → low-power mode
bit 6 DAISY_EN = 0  → daisy-chain mode
bit 5 CLK_EN   = 0  → do not output the internal clock on CLK
bits 2:0 DR    = 110
```

With the nominal 2.048 MHz internal oscillator, `DR=110` in low-power mode gives **250 samples per second**, not high-resolution mode at 500 samples per second.

### `CONFIG2_INTERNAL_TEST_1MV_2HZ = 0x51`

The intent is to enable the internal test source with its lower amplitude and approximately 1.95 Hz frequency. The current value is problematic:

```text
0x51 = 0101 0001
       │││  │└─ TEST_FREQ = 01 → fCLK / 2^20 ≈ 1.953 Hz
       ││└──── INT_TEST = 1 → internally generated test source
       └└───── reserved field contains 01
```

TI says CONFIG2 bits 7–6 must always be written as zero. The corrected value should therefore be:

```cpp
constexpr uint8_t CONFIG2_INTERNAL_TEST_1MV_2HZ = 0x11;
```

With a 2.4 V reference, the lower test amplitude is nominally `2.4 V / 2400 = 1 mV`.

### `CONFIG3_INTERNAL_REF_2V4 = 0xC0`

```text
0xC0 = 1100 0000
       ││
       │└─ reserved bit 6 remains 1 as required
       └── PD_REFBUF = 1, which enables the reference buffer
```

Bit 5 is zero, selecting the 2.4 V reference. The 4 V reference option must not be used with the present 3.3 V analog supply.

### `CH_TEST_SIGNAL_GAIN6 = 0x05`

```text
0x05 = 0000 0101
       │││  └── MUX = 101 → internal test signal
       │└────── gain bits 000 → gain 6
       └─────── PD = 0 → channel powered on
```

This setting connects the internal test generator to the selected channel. It does not read the channel's external INP/INN pins.

### `CH_POWERDOWN_SHORTED = 0x81`

```text
0x81 = 1000 0001
       │      └─ MUX = 001 → inputs shorted internally
       └──────── PD = 1 → channel powered down
```

TI recommends selecting the internal short when powering down a channel. The loop writes this value to channel registers 2 through 8.

## What each helper function does

### `adsDrdyISR()`

```cpp
void IRAM_ATTR adsDrdyISR() {
  adsDataReady = true;
}
```

This is an interrupt service routine. When DRDY falls, the ESP32 temporarily pauses normal execution, runs this very short function, and sets a flag. `IRAM_ATTR` asks the ESP32 toolchain to put the function in instruction RAM so it is safe and quick to call during an interrupt.

The variable is declared `volatile`:

```cpp
volatile bool adsDataReady = false;
```

`volatile` tells the compiler that the value can change unexpectedly outside the normal flow of `loop()`. Without it, compiler optimization could incorrectly reuse an old value.

### `adsSelect()` and `adsDeselect()`

These functions pull CS low before a transaction and return it high afterward. Only while CS is low should the ADS1298 treat SPI clock pulses as communication intended for it.

### `adsXfer()`

```cpp
uint8_t adsXfer(uint8_t b) {
  return SPI.transfer(b);
}
```

SPI is full duplex: sending one byte also receives one byte. This wrapper sends `b` on MOSI/DIN and returns the byte simultaneously received on MISO/DOUT.

### `adsCommand()`

This starts an SPI transaction, selects the ADS, sends one command byte, deselects the ADS, and ends the transaction. The final delay gives the ADS time to decode the command.

### `adsWriteRegister()`

Writing one register takes three bytes:

```text
byte 1: WREG base command OR register address
byte 2: number of registers minus one; 0 means one register
byte 3: new register value
```

For example, writing `0xC0` to CONFIG3 address `0x03` sends a first byte of `0x40 | 0x03 = 0x43`.

### `adsReadRegister()`

Reading one register also uses three transfers:

```text
byte 1: RREG base command OR register address
byte 2: number of registers minus one
byte 3: dummy 0x00 sent by ESP while ADS shifts the result out
```

The successful diagnostic result `ID=0x92` came through this same basic mechanism.

### `readInt24()` and `signExtend24()`

Each ADC result arrives as three bytes. `readInt24()` reconstructs them:

```text
byte 0 becomes bits 23–16
byte 1 becomes bits 15–8
byte 2 becomes bits 7–0
```

ADS results use 24-bit two's-complement signed numbers. C++ has convenient 32-bit integers but no standard 24-bit integer. `signExtend24()` copies the 24-bit sign into the upper eight bits so negative values remain negative when stored in `int32_t`.

Examples:

```text
0x000001 → +1
0x7FFFFF → largest positive code
0xFFFFFF → -1 after sign extension
0x800000 → most negative code
```

### `codeToVolts()`

```cpp
return ((float)code * vref) / (gain * 8388607.0f);
```

`8388607` is `2^23 - 1`, the largest positive 24-bit signed code. Dividing by the PGA gain converts the ADC result back to an input-referred voltage. For this program, `vref=2.4` and `gain=6`, so the nominal differential full-scale input range is approximately ±0.4 V.

### `readAdsFrame()`

This function selects the ADS and performs 27 SPI transfers. It sends `0x00` each time so DIN remains low while DOUT shifts the status and channel bytes into `frame`.

### `setupAdsInternalTestMode()`

This is the main ADS configuration sequence:

1. send SDATAC so registers can be accessed;
2. stop conversions and set START low;
3. write CONFIG1, CONFIG2, CONFIG3, and CONFIG4;
4. wait for the internal reference to settle;
5. route the internal test signal to channel 1;
6. power down and short channels 2 through 8;
7. re-enter RDATAC continuous-read mode; and
8. raise START and also send the START command.

Using both the START pin and START command is redundant. One consistent start/stop method would be clearer.

### `printRegisters()`

This reads several registers and prints them in hexadecimal. Expected values after corrected configuration are approximately:

```text
ID      = 0x92
CONFIG1 = 0x06
CONFIG2 = 0x11
CONFIG3 = 0xC0
CH1SET  = 0x05
```

### `setup()`

`setup()` runs once. It starts the laptop serial connection at 115200 baud, configures GPIO directions, starts SPI, resets the ADS1298, prints registers before configuration, configures internal-test mode, prints registers afterward, and attaches the DRDY interrupt.

### `loop()`

`loop()` repeatedly checks `adsDataReady`. If no sample is ready, it returns immediately. When a sample is ready, it:

1. clears the flag;
2. reads all 27 frame bytes;
3. constructs the status word;
4. decodes channel 1 from `frame[3]`, `frame[4]`, and `frame[5]`;
5. converts the code to input-referred volts; and
6. multiplies by 1000 and prints millivolts.

The variable `status` is calculated but never used. The counter `n` is incremented but also not currently used because the conditional printing block is commented out.

## What happens in time

```text
ESP32 reset
  ↓
setup() starts UART and GPIO
  ↓
ADS hardware reset
  ↓
read default registers
  ↓
write internal-test configuration
  ↓
start continuous conversion
  ↓
ADS finishes one conversion and pulls DRDY low
  ↓
interrupt sets adsDataReady=true
  ↓
loop() reads 27 bytes over SPI
  ↓
decode CH1 → convert to mV → print to laptop
  ↓
repeat at the configured sample rate
```

## Known issues and confusing parts

These should be addressed before using the file as a trusted test tool:

1. **CONFIG2 should be `0x11`, not `0x51`.** The current code writes a nonzero value into reserved bits that TI says must be zero.
2. **The CONFIG1 comments are incorrect.** `0x06` selects low-power mode at 250 SPS, not high-resolution mode at 500 SPS.
3. **Power-up timing is less conservative than the working diagnostic.** The diagnostic holds PWDN low, then raises it and waits one second before resetting. This file raises PWDN and resets almost immediately. The longer sequence should be adopted for repeatable cold starts.
4. **The comment says samples are decimated, but every sample is printed.** The `if ((n % 25) == 0)` block is commented out.
5. **A Boolean DRDY flag cannot count missed samples.** If another DRDY edge occurs while the flag is already true, the program cannot tell that a frame was missed. A counter and overrun reporting would be better.
6. **The status word is ignored.** Validating its fixed high bits helps detect lost byte alignment and SPI corruption.
7. **START is asserted twice.** The code raises the START pin and sends the START command. This is unnecessary and makes state harder to reason about.
8. **The example output is suspicious.** Frequent exact zeros and levels around 0.29 mV do not resemble a clean nominal ±1 mV internal calibration waveform. It may have been recorded before power and communication were corrected.
9. **The PlatformIO environments are confusing.** `internal-wg-test` includes both `main.cpp` and `manual.cpp`, which both define `setup()` and `loop()` and can cause duplicate-definition errors. `manual-wg-test` actually selects `main.cpp` by excluding `manual.cpp`.
10. **Only channel 1 is parsed.** The ADS already sends all eight channel slots, so channel iteration and simultaneous multichannel parsing are logical extensions.

## Recommended repair and test sequence

### Step 1: Make channel 1 deterministic

- Change CONFIG2 from `0x51` to `0x11`.
- Correct the CONFIG1 comments to say low-power mode, 250 SPS.
- Reuse the conservative PWDN/reset sequence from the working diagnostic.
- Use either the START pin or START command consistently.
- Verify all important register readbacks before starting acquisition. Stop with an explicit error if ID is not `0x92` or a written register does not match.
- Print the raw status word, raw channel code, and converted millivolts at a reduced rate while debugging.

Expected result: a stable approximately 1.953 Hz internal square wave on channel 1 at the nominal internal-test amplitude.

### Step 2: Validate the frame itself

- Check that the status word begins with the ADS1298's expected fixed status bits.
- Replace the Boolean DRDY flag with a sample-ready counter.
- Count received frames, missed-ready events, and invalid status words.
- Measure the actual number of frames per second and compare it with 250 SPS.

This separates analog-value problems from SPI-frame alignment problems.

### Step 3: Test channels 1 through 8 individually

For each channel:

1. stop continuous reading and conversions;
2. write `0x81` to all eight CHnSET registers;
3. write `0x05` only to the channel under test;
4. read the channel registers back;
5. restart conversion;
6. discard at least the first three samples for digital-filter settling; and
7. capture several complete test-signal cycles.

Channel `n` begins in the frame at:

```cpp
int offset = 3 + 3 * (n - 1);
```

### Step 4: Test all channels simultaneously

Write `0x05` to CH1SET through CH8SET. Parse all eight 24-bit results from every 27-byte frame. At 250 SPS, print one CSV row containing a sample number and eight channel values. Increase UART to 921600 baud to provide comfortable bandwidth.

All eight channels should show the same internally generated signal at nearly the same phase and amplitude. Compare frequency, mean, peak-to-peak amplitude, and correlation across channels.

### Step 5: Return to the external function generator

Only after internal single-channel, channel-sweep, and simultaneous multichannel tests pass should CONFIG2 disable the internal source and CHnSET select normal electrode input. At that stage, test common-mode bias, differential amplitude, input protection, and the external analog signal path separately.

## Current confidence boundary

The successful diagnostic proves:

- the ADS1298 has power;
- the ESP32 can select the ADS over SPI;
- ADS DOUT can return a correct `0x92` ID;
- CONFIG1 can be written, read back, and restored reliably.

It does not yet prove:

- the internal reference reaches its correct voltage;
- conversions run at the expected sample rate;
- DRDY produces reliable edges during conversion;
- the 27-byte frame is aligned correctly;
- channel 1 contains the expected internal waveform; or
- all eight ADC channels behave similarly.

Those are exactly the questions the staged internal-test pipeline should answer next.
