/*
 * =============================================================================
 *  ads1298.cpp  —  Low-level driver for the TI ADS1298 (the "how")
 * =============================================================================
 *
 *  This file contains the actual code for every function declared in
 *  ads1298.h. Read the header first for the wiring diagram and the big picture.
 *
 *  LIBRARIES USED
 *  --------------
 *  - Arduino.h : pinMode(), digitalWrite(), delay(), delayMicroseconds(),
 *                attachInterrupt(). These are thin wrappers around the ESP32's
 *                own GPIO and timer drivers.
 *  - SPI.h     : the global object "SPI" of type SPIClass. It drives one of
 *                the ESP32-S3's hardware SPI peripherals. Key methods:
 *                  SPI.begin(sck, miso, mosi, ss)   choose pins, switch hardware on
 *                  SPI.beginTransaction(settings)   lock the bus + apply speed/mode
 *                  SPI.transfer(byte)               send one byte, return the byte received
 *                  SPI.transferBytes(out, in, n)    same for n bytes at once (faster)
 *                  SPI.endTransaction()             release the bus
 *  - esp_timer.h : esp_timer_get_time() returns microseconds since boot as a
 *                64-bit number. It is safe to call inside an interrupt.
 *
 *  SPI SETTINGS FOR THE ADS1298
 *  ----------------------------
 *  An SPISettings object bundles three things:
 *     1. clock speed in Hz,
 *     2. bit order (MSBFIRST = most significant bit first),
 *     3. SPI "mode" = clock polarity (CPOL) and phase (CPHA).
 *  The ADS1298 needs CPOL = 0, CPHA = 1, which is SPI_MODE1 (datasheet,
 *  "Serial Interface"): the clock idles LOW and data is sampled on the
 *  falling edge.
 *
 *  We use TWO speeds:
 *    - g_regSpi  (500 kHz) for commands and registers. Slow and safe, because
 *      multi-byte commands need >= 4 tCLK (~2 us) between bytes ("t_SDECODE").
 *    - g_dataSpi (default 4 MHz, changeable by the PC) for reading frames.
 *      Fast so a frame is read well inside one sample period (250 us at 4 kSPS).
 * =============================================================================
 */
#include "ads1298.h"               // our own declarations (pins, commands, function names)
#include <esp_timer.h>             // esp_timer_get_time(): microsecond timestamp, ISR-safe
#include <driver/gpio.h>           // gpio_intr_disable()/gpio_intr_enable(): pause one pin's interrupt (DOUT mode)
#include <soc/gpio_struct.h>       // GPIO.status_w1tc: clear an interrupt that is already waiting (DOUT mode)

/*
 * -----------------------------------------------------------------------------
 *  MODULE-LEVEL ("global to this file") VARIABLES
 * -----------------------------------------------------------------------------
 *  "static" in front of a global variable means it is private to this .cpp
 *  file: main.cpp cannot see or change it directly, only through functions.
 *
 *  "volatile" tells the compiler: this variable can change at any moment
 *  behind your back (here: inside the DRDY interrupt). Without it, the
 *  compiler might keep a stale copy in a CPU register and a waiting loop
 *  would never see the new value.
 *
 *  portMUX_TYPE is an ESP32 "spinlock". The ESP32 CPU is 32-bit, so writing a
 *  64-bit timestamp takes two steps. If the interrupt fired between those
 *  two steps while loop() was reading, loop() would see half old/half new
 *  garbage ("torn read"). Taking the lock around both the write (ISR) and
 *  the read (adsDrdySnapshot) makes each access all-or-nothing.
 * -----------------------------------------------------------------------------
 */
static SPISettings g_regSpi(500000, MSBFIRST, SPI_MODE1);     // 500 kHz, MSB first, CPOL=0/CPHA=1 for commands/registers
static SPISettings g_dataSpi(4000000, MSBFIRST, SPI_MODE1);   // 4 MHz for frame reads (PC can change it with "SCLK")
static uint32_t    g_dataClockHz = 4000000;                   // remember the frame-read clock so we can report it

static volatile uint32_t g_drdyCount  = 0;                    // how many DRDY falling edges since boot
static volatile int64_t  g_drdyTimeUs = 0;                    // time (us since boot) of the most recent DRDY edge
static portMUX_TYPE      g_drdyLock   = portMUX_INITIALIZER_UNLOCKED;  // spinlock protecting the two variables above

static bool     g_doutActive = false;                         // true while a capture runs in DOUT-as-DRDY mode (CS held LOW)
static uint32_t g_periodUs   = 2000;                          // sample period of the configured data rate (default 500 SPS)

/*
 * -----------------------------------------------------------------------------
 *  adsDrdyIsr()  —  the DRDY interrupt service routine (ISR)
 * -----------------------------------------------------------------------------
 *  WHAT AN INTERRUPT IS
 *  An interrupt makes the CPU pause whatever it is doing, run a short
 *  function (the ISR), then resume exactly where it was. We ask the ESP32
 *  to call this ISR on every FALLING edge of the DRDY pin, i.e. every time
 *  the ADS1298 finishes a conversion.
 *
 *  WHY A COUNTER AND NOT A TRUE/FALSE FLAG
 *  The old sketch used "volatile bool adsDataReady". A bool cannot tell
 *  whether ONE or FIVE conversions happened while loop() was busy (for
 *  example printing). A counter can: if it jumped by more than 1 since we
 *  last looked, we know exactly how many samples were missed. Every capture
 *  reports this number to the PC, so no sample is ever lost silently.
 *
 *  RULES FOR ISRs ON THE ESP32
 *  - Keep them very short (no Serial.print, no delay).
 *  - Mark them IRAM_ATTR so the code is placed in internal RAM. Code in
 *    external flash may be unreachable at the moment the interrupt fires.
 *  - Use the "_ISR" variants of FreeRTOS lock functions inside them.
 * -----------------------------------------------------------------------------
 */
static void IRAM_ATTR adsDrdyIsr() {
  portENTER_CRITICAL_ISR(&g_drdyLock);          // take the spinlock (ISR version)
  g_drdyCount = g_drdyCount + 1;                // one more conversion finished (written out because "++" on volatile is deprecated in C++20)
  g_drdyTimeUs = esp_timer_get_time();          // remember when it happened (microseconds since boot)
  portEXIT_CRITICAL_ISR(&g_drdyLock);           // release the spinlock
}

/*
 * -----------------------------------------------------------------------------
 *  adsDrdySnapshot()  —  read the DRDY counter and timestamp consistently
 * -----------------------------------------------------------------------------
 *  Parameters are passed "by reference" (the & in uint32_t &count): the
 *  function writes directly into the caller's variables, which is how C++
 *  returns more than one value without building a struct.
 * -----------------------------------------------------------------------------
 */
void adsDrdySnapshot(uint32_t &count, int64_t &timeUs) {
  portENTER_CRITICAL(&g_drdyLock);              // block the ISR for a few CPU cycles
  count  = g_drdyCount;                         // copy the counter
  timeUs = g_drdyTimeUs;                        // copy the 64-bit timestamp (cannot be torn now)
  portEXIT_CRITICAL(&g_drdyLock);               // let the ISR run again
}

/*
 * -----------------------------------------------------------------------------
 *  csLow() / csHigh()  —  select and deselect the ADS1298
 * -----------------------------------------------------------------------------
 *  CS ("chip select") LOW tells the ADS1298 that the following SPI clock
 *  pulses are meant for it. Timing rules (datasheet, "Timing Requirements"):
 *    - a few ns between CS falling and the first SCLK edge (t_CSSC),
 *    - at least 4 tCLK (~2 us at 2.048 MHz) after the last SCLK edge before
 *      CS may go HIGH again (t_SCCS).
 *  The microsecond delays below are generous versions of those rules.
 * -----------------------------------------------------------------------------
 */
static inline void csLow() {
  digitalWrite(PIN_CS, LOW);                    // select the chip
  delayMicroseconds(1);                         // > t_CSSC setup time before clocking
}

static inline void csHigh() {
  delayMicroseconds(2);                         // >= 4 tCLK after the last bit (t_SCCS)
  digitalWrite(PIN_CS, HIGH);                   // deselect the chip
  delayMicroseconds(2);                         // minimum CS-high time before the next access
}

/*
 * -----------------------------------------------------------------------------
 *  adsBegin()  —  configure pins and SPI, then power up and reset the ADS1298
 * -----------------------------------------------------------------------------
 *  This copies the conservative sequence of the working ADS1298_diagnostic
 *  sketch (todo.md: "Reuse the conservative PWDN/reset timing"):
 *
 *    1. Set each output's level BEFORE making it an output ("preload"), so
 *       no pin glitches to the wrong level for a moment.
 *    2. PWDN LOW (chip off) -> 20 ms -> PWDN HIGH (chip on) -> wait 1 s for
 *       the supplies, reference and internal oscillator to settle.
 *    3. Pulse RESET LOW for 10 ms: every register returns to its default.
 *    4. After reset the chip is in RDATAC mode, where it ignores register
 *       commands. Send SDATAC so we can configure it.
 *    5. Attach the DRDY interrupt (only when the real DRDY pin is used; in
 *       DOUT mode adsStartConversions() attaches it to MISO instead).
 * -----------------------------------------------------------------------------
 */
void adsBegin() {
  digitalWrite(PIN_CS, HIGH);                   // preload: CS idle HIGH (chip not selected)
  digitalWrite(PIN_START, LOW);                 // preload: START LOW (no conversions yet)
  digitalWrite(PIN_RST, HIGH);                  // preload: RESET idle HIGH (not in reset)
  digitalWrite(PIN_PWDN, LOW);                  // preload: PWDN LOW (chip held powered down for now)

  pinMode(PIN_CS, OUTPUT);                      // CS is driven by the ESP32
  pinMode(PIN_START, OUTPUT);                   // START is driven by the ESP32
  pinMode(PIN_RST, OUTPUT);                     // RESET is driven by the ESP32
  pinMode(PIN_PWDN, OUTPUT);                    // PWDN is driven by the ESP32
  pinMode(PIN_DRDY, INPUT);                     // DRDY is driven by the ADS1298 (push-pull output)

  SPI.begin(PIN_SCLK, PIN_MISO, PIN_MOSI, -1);  // route the SPI peripheral to our pins; -1 = we drive CS ourselves

  delay(20);                                    // keep the chip powered down briefly
  digitalWrite(PIN_PWDN, HIGH);                 // power the chip up
  delay(1000);                                  // conservative wake-up wait (supplies, oscillator, reference)

  digitalWrite(PIN_RST, LOW);                   // start the reset pulse
  delay(10);                                    // hold reset (datasheet needs only 2 tCLK; 10 ms is very safe)
  digitalWrite(PIN_RST, HIGH);                  // release reset: all registers now hold defaults
  delay(50);                                    // let the chip finish its internal reset (>= 18 tCLK)

  adsCommand(CMD_SDATAC);                       // leave RDATAC so register reads/writes are accepted
  adsCommand(CMD_STOP);                         // make sure no conversions run (START pin is LOW too)

  if (!DRDY_VIA_DOUT) {                         // real DRDY pin in use (see ads1298.h)?
    attachInterrupt(digitalPinToInterrupt(PIN_DRDY), adsDrdyIsr, FALLING);  // call adsDrdyIsr on each DRDY falling edge
  }                                             // DOUT mode: the interrupt goes on MISO, only during captures
}

/*
 * -----------------------------------------------------------------------------
 *  adsPowerCycle()  —  power the chip down and back up through the PWDN pin
 * -----------------------------------------------------------------------------
 *  Used by the PC's "RESET" command for the repeated power-cycle check in the
 *  prerequisite experiment. All registers return to their defaults, so the
 *  PC sends a fresh CFG afterwards. This is not a removal of the supply
 *  voltage, but it exercises the same wake-up and reset path.
 * -----------------------------------------------------------------------------
 */
void adsPowerCycle() {
  digitalWrite(PIN_START, LOW);                 // stop conversions first
  digitalWrite(PIN_PWDN, LOW);                  // power the chip down
  delay(100);                                   // stay off long enough for internal nodes to discharge
  digitalWrite(PIN_PWDN, HIGH);                 // power back up
  delay(1000);                                  // same conservative wake-up wait as adsBegin()
  digitalWrite(PIN_RST, LOW);                   // reset pulse ...
  delay(10);                                    // ... held for 10 ms ...
  digitalWrite(PIN_RST, HIGH);                  // ... released
  delay(50);                                    // internal reset time
  adsCommand(CMD_SDATAC);                       // register access mode again
  adsCommand(CMD_STOP);                         // no conversions
}

/*
 * -----------------------------------------------------------------------------
 *  adsCommand()  —  send one opcode byte
 * -----------------------------------------------------------------------------
 *  beginTransaction() locks the SPI bus and applies the speed/mode, then we
 *  select the chip, send the byte, deselect and release the bus.
 *  The 10 us pause afterwards gives the ADS1298 time to execute the command
 *  before anything else arrives (some commands need 4 tCLK to decode).
 * -----------------------------------------------------------------------------
 */
void adsCommand(uint8_t cmd) {
  SPI.beginTransaction(g_regSpi);               // lock bus, 500 kHz, SPI mode 1
  csLow();                                      // select the ADS1298
  SPI.transfer(cmd);                            // shift the opcode out (the byte coming back is ignored)
  csHigh();                                     // deselect
  SPI.endTransaction();                         // unlock bus
  delayMicroseconds(10);                        // let the command take effect
}

/*
 * -----------------------------------------------------------------------------
 *  adsWriteRegister()  —  write one 8-bit value into one register
 * -----------------------------------------------------------------------------
 *  The WREG command is three bytes (datasheet, "WREG"):
 *     byte 1: 010r rrrr  = 0x40 | address        (which register)
 *     byte 2: 000n nnnn  = number of registers - 1 (0 means "just one")
 *     byte 3: the value
 *  Between bytes the chip needs t_SDECODE = 4 tCLK ~ 2 us to decode. At
 *  500 kHz one byte already takes 16 us, and we add 5 us on top, so we are
 *  far from the limit.
 * -----------------------------------------------------------------------------
 */
void adsWriteRegister(uint8_t reg, uint8_t value) {
  SPI.beginTransaction(g_regSpi);               // slow, safe register-access speed
  csLow();                                      // select
  SPI.transfer(uint8_t(CMD_WREG | reg));        // opcode + 5-bit register address
  delayMicroseconds(5);                         // t_SDECODE spacing
  SPI.transfer(0x00);                           // "write 1 register" (count - 1 = 0)
  delayMicroseconds(5);                         // t_SDECODE spacing
  SPI.transfer(value);                          // the new register value
  csHigh();                                     // deselect
  SPI.endTransaction();                         // release bus
  delayMicroseconds(10);                        // let the write settle before the next access
}

/*
 * -----------------------------------------------------------------------------
 *  adsReadRegisters()  —  read "count" consecutive registers into "out"
 * -----------------------------------------------------------------------------
 *  The RREG command (datasheet, "RREG"):
 *     byte 1: 001r rrrr = 0x20 | first address
 *     byte 2: 000n nnnn = count - 1
 *  then the chip shifts out one byte per register while we send dummy 0x00.
 *  "out" is a pointer: the address of the first element of the caller's
 *  array. out[i] = ... writes into that array.
 * -----------------------------------------------------------------------------
 */
void adsReadRegisters(uint8_t first, uint8_t count, uint8_t *out) {
  SPI.beginTransaction(g_regSpi);               // slow, safe register-access speed
  csLow();                                      // select
  SPI.transfer(uint8_t(CMD_RREG | first));      // opcode + starting address
  delayMicroseconds(5);                         // t_SDECODE spacing
  SPI.transfer(uint8_t(count - 1));             // how many registers, minus one
  delayMicroseconds(5);                         // t_SDECODE spacing
  for (uint8_t i = 0; i < count; i++) {         // for each requested register ...
    out[i] = SPI.transfer(0x00);                // ... send a dummy byte and store what comes back
  }
  csHigh();                                     // deselect
  SPI.endTransaction();                         // release bus
}

/*
 * -----------------------------------------------------------------------------
 *  adsReadRegister()  —  convenience wrapper: read just one register
 * -----------------------------------------------------------------------------
 */
uint8_t adsReadRegister(uint8_t reg) {
  uint8_t value = 0;                            // where the result will be stored
  adsReadRegisters(reg, 1, &value);             // &value = "address of value", so the function can fill it
  return value;                                 // hand the byte back to the caller
}

/*
 * -----------------------------------------------------------------------------
 *  adsApplyConfig()  —  write the 12 settings chosen by the PC, read them back
 * -----------------------------------------------------------------------------
 *  values[]   = { CONFIG1, CONFIG2, CONFIG3, CONFIG4, CH1SET ... CH8SET }
 *  readback[] = what the chip reports afterwards, same order.
 *
 *  Order of operations matters:
 *    1. Stop conversions and leave RDATAC (registers are read-only otherwise).
 *    2. Write CONFIG3 first: it powers the internal reference buffer.
 *    3. Wait 200 ms: the internal reference needs ~150 ms to settle
 *       (datasheet, "Internal Reference").
 *    4. Write the rest.
 *    5. Read everything back. The PC compares and refuses to trust a capture
 *       whose registers do not match (todo.md: "Stop acquisition with an
 *       explicit error if ... configuration readback is wrong").
 *
 *  Returns true if every byte read back equals what was written. The PC
 *  applies its own masks for read-only bits (e.g. CONFIG3 bit 0 RLD_STAT).
 * -----------------------------------------------------------------------------
 */
bool adsApplyConfig(const uint8_t values[CFG_VALUE_COUNT], uint8_t readback[CFG_VALUE_COUNT]) {
  adsStopConversions();                         // START LOW + SDATAC: chip idle and accepting register writes

  adsWriteRegister(REG_CONFIG3, values[2]);     // reference buffer first
  delay(200);                                   // internal reference start-up (150 ms typ.) with margin
  adsWriteRegister(REG_CONFIG1, values[0]);     // mode + data rate
  uint32_t baseSps = (values[0] & 0x80) ? 32000 : 16000;     // bit 7 HR: high-resolution mode runs twice as fast
  uint32_t sps     = baseSps >> (values[0] & 0x07);          // DR bits 2:0 halve the rate per step (0 -> 32k/16k ... 6 -> 500/250)
  g_periodUs       = 1000000UL / sps;                        // microseconds between conversions, used by DOUT mode
  adsWriteRegister(REG_CONFIG2, values[1]);     // test-signal settings
  adsWriteRegister(REG_CONFIG4, values[3]);     // continuous mode, lead-off comparators
  for (int ch = 0; ch < ADS_CHANNELS; ch++) {   // for channel index 0..7 ...
    adsWriteRegister(REG_CH1SET + ch, values[4 + ch]);  // ... CHnSET lives at 0x05 + index
  }

  readback[0] = adsReadRegister(REG_CONFIG1);   // read CONFIG1 back
  readback[1] = adsReadRegister(REG_CONFIG2);   // read CONFIG2 back
  readback[2] = adsReadRegister(REG_CONFIG3);   // read CONFIG3 back
  readback[3] = adsReadRegister(REG_CONFIG4);   // read CONFIG4 back
  for (int ch = 0; ch < ADS_CHANNELS; ch++) {   // for each channel ...
    readback[4 + ch] = adsReadRegister(REG_CH1SET + ch);  // ... read its CHnSET back
  }

  bool allMatch = true;                         // assume success ...
  for (int i = 0; i < CFG_VALUE_COUNT; i++) {   // ... then check every value
    if (readback[i] != values[i]) {             // a difference means the write failed or a bit is read-only
      allMatch = false;                         // remember the mismatch (the PC gets the full details)
    }
  }
  return allMatch;                              // true = every byte matched
}

/*
 * -----------------------------------------------------------------------------
 *  adsStartConversions() / adsStopConversions()
 * -----------------------------------------------------------------------------
 *  We start and stop with the START *pin* only, never also the START
 *  command (todo.md: "Use either the START pin or START command consistently
 *  instead of both"). Sending the START opcode while the pin is already HIGH
 *  restarts the conversion and is one possible source of the odd samples
 *  seen with the old sketch.
 *
 *  RDATAC must be sent BEFORE starting, so that each new frame is placed on
 *  DOUT automatically. SDATAC after stopping brings back register access.
 *  After START goes HIGH, the first DRDY arrives after the digital filter
 *  has settled (datasheet, "Settling Time"); the PC also asks us to throw
 *  away a few frames to be safe.
 *
 *  DOUT mode (DRDY_VIA_DOUT, see ads1298.h): CS is pulled LOW once and kept
 *  LOW for the whole capture, so DOUT mirrors DRDY. The SPI bus is locked
 *  (beginTransaction) for the same time, and the "DRDY" interrupt is put on
 *  the MISO pin. adsStopConversions() undoes all three.
 * -----------------------------------------------------------------------------
 */
void adsStartConversions() {
  adsCommand(CMD_RDATAC);                       // continuous read mode: frames come out after every DRDY
  if (DRDY_VIA_DOUT) {                          // DRDY wire not usable: let DOUT signal "data ready"
    SPI.beginTransaction(g_dataSpi);            // lock the bus at the frame-read clock for the whole capture
    csLow();                                    // CS LOW and kept LOW: DOUT now follows DRDY between reads
    GPIO.status_w1tc = BIT(PIN_MISO);           // forget any edge left over from the RDATAC command
    attachInterrupt(digitalPinToInterrupt(PIN_MISO), adsDrdyIsr, FALLING);  // count DOUT falling edges as DRDY
    g_doutActive = true;                        // remember: adsReadFrame/adsStopConversions must act differently
  }
  digitalWrite(PIN_START, HIGH);                // START HIGH: conversions begin and continue
}

void adsStopConversions() {
  digitalWrite(PIN_START, LOW);                 // START LOW: the current conversion finishes, then it stops
  delay(2);                                     // allow the last conversion (max 2 ms at 500 SPS) to complete
  if (g_doutActive) {                           // a DOUT-mode capture was running?
    detachInterrupt(digitalPinToInterrupt(PIN_MISO));   // stop counting MISO edges (register reads would trigger it)
    csHigh();                                   // release the chip
    SPI.endTransaction();                       // release the SPI bus
    g_doutActive = false;                       // back to normal operation
  }
  adsCommand(CMD_SDATAC);                       // leave continuous mode -> registers accessible again
}

uint32_t adsNominalPeriodUs() {
  return g_periodUs;                            // set by adsApplyConfig() from the CONFIG1 data-rate bits
}

/*
 * -----------------------------------------------------------------------------
 *  adsReadFrame()  —  clock out one 27-byte frame after DRDY fell
 * -----------------------------------------------------------------------------
 *  In RDATAC mode the frame is simply shifted out when we provide clock
 *  pulses. DIN must stay LOW while we read (datasheet, "RDATAC"), otherwise
 *  the chip could interpret the bits as a command. So we send 27 zero bytes.
 *
 *  SPI.transferBytes(out, in, n) sends n bytes from "out" and simultaneously
 *  stores the n received bytes into "in". One call is much faster than 27
 *  separate SPI.transfer() calls.
 *
 *  Timing budget: 27 bytes x 8 bits = 216 clocks. At 4 MHz that is 54 us,
 *  well inside the 250 us between samples at 4 kSPS (see
 *  clamshell_validation.md, section 1.2).
 * -----------------------------------------------------------------------------
 */
void adsReadFrame(uint8_t *frame) {
  static const uint8_t zeros[ADS_FRAME_BYTES] = {0};   // 27 zero bytes kept in memory once ("static")
  if (g_doutActive) {                           // DOUT mode: bus already locked and CS already LOW
    gpio_intr_disable((gpio_num_t)PIN_MISO);    // our own clocking toggles DOUT: do not count those edges
    SPI.transferBytes(zeros, frame, ADS_FRAME_BYTES);  // send zeros, receive the 27-byte frame
    GPIO.status_w1tc = BIT(PIN_MISO);           // throw away the edge our read left pending
    gpio_intr_enable((gpio_num_t)PIN_MISO);     // count the next real "data ready" again
    return;                                     // done (CS stays LOW for the next frame)
  }
  SPI.beginTransaction(g_dataSpi);              // lock bus at the (fast) data clock
  csLow();                                      // select
  SPI.transferBytes(zeros, frame, ADS_FRAME_BYTES);    // send zeros, receive the 27-byte frame
  csHigh();                                     // deselect (with the required 4 tCLK wait)
  SPI.endTransaction();                         // release bus
}

/*
 * -----------------------------------------------------------------------------
 *  adsSetDataClock() / adsGetDataClock()
 * -----------------------------------------------------------------------------
 *  Lets the PC try different SPI clock speeds for Experiment F ("does a
 *  faster SCLK couple noise into the analog side?"). The ADS1298 allows up
 *  to 20 MHz at DVDD 2.7-3.6 V (datasheet, t_SCLK).
 * -----------------------------------------------------------------------------
 */
void adsSetDataClock(uint32_t hz) {
  g_dataClockHz = hz;                                   // remember the value
  g_dataSpi = SPISettings(hz, MSBFIRST, SPI_MODE1);     // build new settings with the same mode/bit order
}

uint32_t adsGetDataClock() {
  return g_dataClockHz;                                 // report the current frame-read clock
}
