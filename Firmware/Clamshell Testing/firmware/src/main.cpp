/*
 * =============================================================================
 *  main.cpp  —  ADS1298 clamshell validation firmware ("command server")
 * =============================================================================
 *
 *  THE IDEA
 *  --------
 *  This firmware does not contain any experiment. It is a small "server"
 *  that waits for one-line text commands from the PC, performs them, and
 *  replies. The PC program (host/run_suite.py) decides which registers to
 *  write, how long to capture, which aggressor to switch on, and does all
 *  of the analysis. Benefits:
 *    - you flash the ESP32 once; changing or limiting experiments only means
 *      editing host/test_plan.toml,
 *    - the firmware stays small enough to read in one sitting,
 *    - the raw 24-bit codes reach the PC untouched (no float printing, no
 *      rounding: clamshell_validation.md, section 1.1, last row).
 *
 *  DATA FLOW
 *  ---------
 *
 *     PC (Python)                         ESP32-S3 (this file)                 ADS1298
 *     -----------                         --------------------                 -------
 *     "CFG 86 00 C0 00 01 ..."  ───────►  adsApplyConfig()  ── SPI WREG ────►  registers
 *                               ◄───────  "OK CFG <readback>" ◄── SPI RREG ──
 *     "CAP 5000 32 S"           ───────►  start conversions ── START pin ──►  converting
 *                                         wait for DRDY count to change ◄──── DRDY falls
 *                                         adsReadFrame() ◄──── SPI 27 bytes ── frame
 *                               ◄───────  binary packet (34 bytes) x 5000
 *                               ◄───────  "END sent=5000 missed=0 ..."
 *
 *  THE SERIAL LINK
 *  ---------------
 *  "Serial" on this board is UART0, which reaches the PC through the
 *  USB-to-UART bridge chip on the DevKitC (the USB port labelled "UART").
 *  At 2,000,000 baud a byte takes 10 bits (start + 8 data + stop) = 5 us, so
 *  the link carries ~200,000 bytes/s. The worst case here, 4 kSPS x 34
 *  bytes = 136,000 bytes/s, fits with margin. If your bridge cannot do
 *  2 Mbaud, lower SERIAL_BAUD here AND "baud" in host/test_plan.toml; the
 *  4 kSPS captures will then report missed frames (they are never hidden).
 *
 *  COMMANDS (one per line, terminated by '\n'; replies start with OK or ERR)
 *  ------------------------------------------------------------------------
 *    PING                      -> OK PONG fw=<version> heap=<bytes> maxalloc=<bytes> baud=<baud>
 *    ID                        -> OK ID <hex>
 *    REGS                      -> OK REGS <26 hex bytes: register 0x00..0x19>
 *    CFG c1 c2 c3 c4 s1..s8    -> OK CFG <12 hex readback bytes>   (ERR CFG ... if any byte differs)
 *    RESET                     -> OK RESET id=<hex>                (PWDN power cycle + reset)
 *    SCLK <hz>                 -> OK SCLK <hz>                     (frame-read SPI clock)
 *    WIFI OFF|AP|SCAN          -> OK WIFI <mode>
 *    LOAD IDLE|BUSY            -> OK LOAD <mode>
 *    CAP <n> <discard> <S|B>   -> OK CAP n=<n> bytes=34, then n binary packets, then END line
 *                                 S = stream each packet immediately
 *                                 B = buffer all packets in RAM first, send after the
 *                                     capture (USB idle during the capture)
 *
 *  BINARY PACKET (34 bytes, one per conversion)
 *  --------------------------------------------
 *    [0]      0xA5           sync byte 1   } lets the PC find packet boundaries
 *    [1]      0x5A           sync byte 2   } even if a byte gets lost
 *    [2..5]   seq            DRDY number of this frame, little-endian uint32,
 *                            counted from the start of the capture. A jump of
 *                            more than 1 between packets = missed conversions.
 *    [6..32]  frame          the 27 raw bytes from the ADS1298, untouched
 *                            (3 status bytes, then CH1..CH8, 3 bytes each,
 *                            big-endian two's complement)
 *    [33]     checksum       XOR of bytes [2..32]; the PC drops any packet
 *                            whose checksum does not match
 * =============================================================================
 */
#include <Arduino.h>                       // Arduino core API
#include "ads1298.h"                       // our ADS1298 driver
#include "aggressors.h"                    // WiFi / CPU-load aggressors

/*
 * -----------------------------------------------------------------------------
 *  CONSTANTS
 * -----------------------------------------------------------------------------
 */
static const char    *FW_VERSION       = "clamshell-suite-1.0";   // reported by PING so the PC can log it
constexpr uint32_t    SERIAL_BAUD      = 2000000;   // UART speed; must equal "baud" in host/test_plan.toml
constexpr size_t      SERIAL_TX_BUFFER = 16384;     // bytes the UART driver can queue before Serial.write() blocks
constexpr size_t      CMD_LINE_MAX         = 160;       // longest command line we accept
constexpr uint32_t    DRDY_TIMEOUT_US  = 500000;    // give up a capture if no DRDY arrives for 0.5 s
constexpr uint32_t    MAX_CAPTURE      = 20000000;  // sanity limit on frames per capture (~83 min at 4 kSPS)

/*
 * -----------------------------------------------------------------------------
 *  setup()  —  runs once after power-on or reset
 * -----------------------------------------------------------------------------
 *  setTxBufferSize() must be called BEFORE Serial.begin(): it decides how
 *  much RAM the UART driver reserves for outgoing bytes. A large buffer
 *  absorbs short hiccups on the USB side without stalling the capture loop.
 * -----------------------------------------------------------------------------
 */
void setup() {
  Serial.setTxBufferSize(SERIAL_TX_BUFFER);   // big transmit queue (must come before begin)
  Serial.setRxBufferSize(1024);               // receive queue for commands from the PC
  Serial.begin(SERIAL_BAUD);                  // open UART0 at 2 Mbaud (8 data bits, no parity, 1 stop bit)
  delay(200);                                 // give the USB-UART bridge a moment

  adsBegin();                                 // pins, SPI, power-up, reset, SDATAC, DRDY interrupt

  Serial.printf("READY fw=%s id=%02X\n",      // announce we are alive; the PC waits for this or a PONG
                FW_VERSION, adsReadRegister(REG_ID));
}

/*
 * -----------------------------------------------------------------------------
 *  parseHexByte()  —  turn text like "C0" into the number 0xC0
 * -----------------------------------------------------------------------------
 *  strtoul(text, &end, 16) converts base-16 text to a number and makes "end"
 *  point just after the last digit it used. If "end" did not move, or the
 *  value does not fit in a byte, the text was not a valid hex byte.
 * -----------------------------------------------------------------------------
 */
static bool parseHexByte(const char *text, uint8_t &out) {
  if (text == nullptr) {                       // no token at all
    return false;                              // -> invalid
  }
  char *end = nullptr;                         // will point after the parsed digits
  unsigned long v = strtoul(text, &end, 16);   // parse as hexadecimal
  if (end == text || *end != '\0' || v > 0xFF) {   // nothing parsed, trailing junk, or too big
    return false;                              // -> invalid
  }
  out = uint8_t(v);                            // store the result in the caller's variable
  return true;                                 // success
}

/*
 * -----------------------------------------------------------------------------
 *  cmdCfg()  —  handle "CFG c1 c2 c3 c4 s1 s2 s3 s4 s5 s6 s7 s8"
 * -----------------------------------------------------------------------------
 *  strtok(nullptr, " ") returns the next space-separated word of the line
 *  that handleLine() started splitting. We expect exactly 12 hex bytes.
 * -----------------------------------------------------------------------------
 */
static void cmdCfg() {
  uint8_t values[CFG_VALUE_COUNT];                    // what the PC wants written
  uint8_t readback[CFG_VALUE_COUNT];                  // what the chip reports afterwards
  for (int i = 0; i < CFG_VALUE_COUNT; i++) {         // read the 12 arguments ...
    if (!parseHexByte(strtok(nullptr, " "), values[i])) {   // ... each must be a valid hex byte
      Serial.printf("ERR CFG bad argument %d\n", i + 1);    // tell the PC which one was wrong
      return;                                         // do not touch the chip with bad data
    }
  }
  bool ok = adsApplyConfig(values, readback);         // write + read back
  Serial.print(ok ? "OK CFG" : "ERR CFG mismatch");   // first part of the reply
  for (int i = 0; i < CFG_VALUE_COUNT; i++) {         // then every readback byte ...
    Serial.printf(" %02X", readback[i]);              // ... as two hex digits
  }
  Serial.print('\n');                                 // end of the reply line
}

/*
 * -----------------------------------------------------------------------------
 *  cmdRegs()  —  handle "REGS": dump all 26 registers (0x00..0x19)
 * -----------------------------------------------------------------------------
 *  Used for the report appendix. Conversions must be stopped first because
 *  register reads are ignored in RDATAC mode.
 * -----------------------------------------------------------------------------
 */
static void cmdRegs() {
  uint8_t regs[REG_COUNT];                            // space for all registers
  adsStopConversions();                               // make sure registers are readable
  adsReadRegisters(0x00, REG_COUNT, regs);            // one multi-register RREG
  Serial.print("OK REGS");                            // reply prefix
  for (int i = 0; i < REG_COUNT; i++) {               // each register ...
    Serial.printf(" %02X", regs[i]);                  // ... as hex
  }
  Serial.print('\n');                                 // end of line
}

/*
 * -----------------------------------------------------------------------------
 *  cmdCapture()  —  handle "CAP <n> <discard> <S|B>"
 * -----------------------------------------------------------------------------
 *  This is the heart of the firmware. Step by step:
 *
 *   1. Validate arguments; in buffer mode reserve RAM for n packets with
 *      malloc() (returns nullptr if there is not enough memory).
 *   2. Reply "OK CAP ..." and Serial.flush() (wait until it has left the
 *      UART) so the reply is not mixed into the binary data.
 *   3. Start conversions and remember the DRDY count at the start.
 *   4. Loop until n packets are done:
 *        a. Busy-wait until the DRDY counter changes (or time out).
 *        b. If it moved by more than 1, conversions were missed: count them.
 *        c. Read the 27-byte frame over SPI.
 *        d. The first "discard" frames are thrown away (filter settling).
 *        e. Build the 34-byte packet and send it (S) or store it (B).
 *   5. Stop conversions, send buffered packets (B), and print the END line
 *      with all the counters the PC needs for the integrity checks.
 *
 *  WHY BUSY-WAIT INSTEAD OF RETURNING TO loop()?
 *  Polling a counter in a tight loop gives the lowest and most predictable
 *  delay between DRDY falling and the SPI read starting. The frame must be
 *  read completely before the next DRDY, or it may be overwritten mid-read
 *  (datasheet, "RDATAC"). That race is one candidate for the interleaved
 *  zeros seen with the old sketch.
 * -----------------------------------------------------------------------------
 */
static void cmdCapture() {
  const char *nText = strtok(nullptr, " ");           // 1st argument: number of packets
  const char *dText = strtok(nullptr, " ");           // 2nd argument: frames to discard first
  const char *mText = strtok(nullptr, " ");           // 3rd argument: S or B
  if (!nText || !dText || !mText) {                   // any argument missing?
    Serial.print("ERR CAP usage: CAP <n> <discard> <S|B>\n");   // explain the format
    return;                                           // abort
  }
  uint32_t n       = strtoul(nText, nullptr, 10);     // decimal text -> number
  uint32_t discard = strtoul(dText, nullptr, 10);     // decimal text -> number
  bool buffered    = (mText[0] == 'B');               // 'B' = buffer in RAM, anything else = stream
  if (n == 0 || n > MAX_CAPTURE) {                    // nonsense request?
    Serial.print("ERR CAP n out of range\n");         // refuse it
    return;                                           // abort
  }

  uint8_t *ram = nullptr;                             // RAM buffer (only used in B mode)
  if (buffered) {                                     // buffer mode requested
    ram = (uint8_t *)malloc(size_t(n) * PACKET_BYTES);   // try to reserve n x 34 bytes
    if (ram == nullptr) {                             // not enough free memory
      Serial.printf("ERR CAP nomem maxalloc=%u\n", (unsigned)ESP.getMaxAllocHeap());   // tell the PC the limit
      return;                                         // abort
    }
  }

  Serial.printf("OK CAP n=%lu bytes=%d\n", (unsigned long)n, PACKET_BYTES);   // header line for the PC
  Serial.flush();                                     // wait until it has been fully transmitted

  uint8_t  frame[ADS_FRAME_BYTES];                    // one raw frame from the ADS1298
  uint8_t  packet[PACKET_BYTES];                      // one packet to the PC
  uint32_t sent = 0, missed = 0, timeouts = 0;        // counters reported in the END line
  uint32_t discarded = 0;                             // frames thrown away so far
  uint32_t firstSeq = 0, lastSeq = 0;                 // seq of first/last packet kept
  int64_t  firstUs = 0, lastUs = 0;                   // DRDY time of first/last packet kept

  adsStartConversions();                              // RDATAC + START pin HIGH
  uint32_t startCount, lastCount;                     // DRDY counter at the start / last handled
  int64_t  tNow;                                      // DRDY timestamp from the snapshot
  adsDrdySnapshot(startCount, tNow);                  // remember where the counter was
  lastCount = startCount;                             // nothing handled yet
  int64_t  prevEdgeUs = 0;                            // DOUT mode: time of the previous handled edge (0 = none yet)
  uint32_t seqExtra   = 0;                            // DOUT mode: conversions found by the clock check below
  uint32_t periodUs   = adsNominalPeriodUs();         // expected time between conversions at this data rate

  while (sent < n) {                                  // until we have n packets
    uint32_t count;                                   // current DRDY counter
    uint32_t waitStart = micros();                    // when we started waiting
    adsDrdySnapshot(count, tNow);                     // look at the counter
    while (count == lastCount) {                      // no new conversion yet ...
      if (micros() - waitStart > DRDY_TIMEOUT_US) {   // ... for too long?
        break;                                        // stop waiting
      }
      adsDrdySnapshot(count, tNow);                   // look again
    }
    if (count == lastCount) {                         // we gave up: DRDY stopped toggling
      timeouts++;                                     // record it
      break;                                          // end the capture early (the PC sees sent < n)
    }

    uint32_t newEvents = count - lastCount;           // conversions since the last one we handled
    lastCount = count;                                // this one is now handled
    // DOUT mode cross-check: the "DRDY" interrupt is paused while a frame is
    // read, so if this loop ever fell almost a whole period behind, one edge
    // could hide inside that pause. The clock cannot be fooled: the time since
    // the previous edge, divided by the sample period, says how many
    // conversions really happened. If that is more than the counter says, the
    // difference is added to seq, so the PC sees an honest gap (= missed).
    if (DRDY_VIA_DOUT && prevEdgeUs != 0) {           // only in DOUT mode, and only once we have a previous edge
      uint32_t byClock = uint32_t((tNow - prevEdgeUs + periodUs / 2) / periodUs);   // rounded number of periods elapsed
      if (byClock > newEvents) {                      // the clock saw more conversions than the counter
        seqExtra  += byClock - newEvents;             // shift all later seq numbers by the hidden ones
        newEvents  = byClock;                         // and count them as skipped below
      }
    }
    prevEdgeUs = tNow;                                // this edge is the reference for the next check
    adsReadFrame(frame);                              // clock the 27 bytes out of the ADS1298

    if (discarded < discard) {                        // still in the settling period?
      discarded++;                                    // count it
      continue;                                       // and drop this frame
    }
    if (sent > 0 && newEvents > 1) {                  // we skipped one or more conversions
      missed += newEvents - 1;                        // (only counted after the first kept packet)
    }

    uint32_t seq = count - startCount + seqExtra;     // 1, 2, 3, ... counted in DRDY pulses (+ any found by the clock check)
    packet[0] = PACKET_SYNC0;                         // sync byte 1
    packet[1] = PACKET_SYNC1;                         // sync byte 2
    packet[2] = uint8_t(seq);                         // seq bits 0-7   (little-endian: lowest byte first)
    packet[3] = uint8_t(seq >> 8);                    // seq bits 8-15
    packet[4] = uint8_t(seq >> 16);                   // seq bits 16-23
    packet[5] = uint8_t(seq >> 24);                   // seq bits 24-31
    memcpy(&packet[6], frame, ADS_FRAME_BYTES);       // copy the untouched 27-byte frame
    uint8_t x = 0;                                    // checksum accumulator
    for (int i = 2; i < PACKET_BYTES - 1; i++) {      // over seq + frame bytes ...
      x ^= packet[i];                                 // ... XOR them all together
    }
    packet[PACKET_BYTES - 1] = x;                     // last byte = checksum

    if (buffered) {                                   // buffer mode
      memcpy(ram + size_t(sent) * PACKET_BYTES, packet, PACKET_BYTES);   // store at position "sent"
    } else {                                          // stream mode
      Serial.write(packet, PACKET_BYTES);             // queue for transmission (blocks only if the queue is full)
    }

    if (sent == 0) {                                  // first kept packet?
      firstSeq = seq;                                 // remember its seq ...
      firstUs = tNow;                                 // ... and DRDY time
    }
    lastSeq = seq;                                    // always update the latest seq
    lastUs = tNow;                                    // and the latest DRDY time
    sent++;                                           // one more packet done
  }

  adsStopConversions();                               // START LOW + SDATAC

  if (buffered) {                                     // buffer mode: now send everything
    Serial.write(ram, size_t(sent) * PACKET_BYTES);   // the whole buffer in one call
    free(ram);                                        // give the memory back
  }

  Serial.printf("\nEND sent=%lu missed=%lu timeouts=%lu first_seq=%lu last_seq=%lu "
                "first_us=%lld last_us=%lld sclk=%lu wifi=%s load=%s\n",   // all counters in one line
                (unsigned long)sent, (unsigned long)missed, (unsigned long)timeouts,
                (unsigned long)firstSeq, (unsigned long)lastSeq,
                (long long)firstUs, (long long)lastUs,
                (unsigned long)adsGetDataClock(), aggressorWifiName(), aggressorLoadName());
}

/*
 * -----------------------------------------------------------------------------
 *  handleLine()  —  decide which command a received line is and run it
 * -----------------------------------------------------------------------------
 *  strtok(line, " ") splits the text at spaces. The first call returns the
 *  first word (the command name); each later strtok(nullptr, " ") returns
 *  the next word. strtok modifies the line in place, which is fine here.
 * -----------------------------------------------------------------------------
 */
static void handleLine(char *line) {
  const char *cmd = strtok(line, " ");                // first word = command name
  if (cmd == nullptr) {                               // empty line
    return;                                           // ignore it
  }

  if (strcmp(cmd, "PING") == 0) {                     // ---- PING ----
    Serial.printf("OK PONG fw=%s heap=%u maxalloc=%u baud=%lu drdy=%s\n",
                  FW_VERSION, (unsigned)ESP.getFreeHeap(),        // free RAM in bytes
                  (unsigned)ESP.getMaxAllocHeap(),                // biggest single block malloc can give
                  (unsigned long)SERIAL_BAUD,                     // the baud rate we are using
                  DRDY_VIA_DOUT ? "dout" : "pin");                // where "data ready" comes from (see ads1298.h)
  } else if (strcmp(cmd, "ID") == 0) {                // ---- ID ----
    adsStopConversions();                             // registers are only readable when stopped
    Serial.printf("OK ID %02X\n", adsReadRegister(REG_ID));   // read and report the ID register
  } else if (strcmp(cmd, "REGS") == 0) {              // ---- REGS ----
    cmdRegs();                                        // dump all registers
  } else if (strcmp(cmd, "CFG") == 0) {               // ---- CFG ----
    cmdCfg();                                         // write + verify 12 registers
  } else if (strcmp(cmd, "RESET") == 0) {             // ---- RESET ----
    adsPowerCycle();                                  // PWDN cycle + reset pulse
    Serial.printf("OK RESET id=%02X\n", adsReadRegister(REG_ID));   // confirm the chip answers again
  } else if (strcmp(cmd, "SCLK") == 0) {              // ---- SCLK <hz> ----
    const char *a = strtok(nullptr, " ");             // the frequency argument
    uint32_t hz = a ? strtoul(a, nullptr, 10) : 0;    // convert (0 if missing)
    if (hz < 100000 || hz > 20000000) {               // ADS1298 limit is 20 MHz; below 100 kHz makes no sense
      Serial.print("ERR SCLK range 100000..20000000\n");   // refuse
    } else {
      adsSetDataClock(hz);                            // apply
      Serial.printf("OK SCLK %lu\n", (unsigned long)hz);   // confirm
    }
  } else if (strcmp(cmd, "WIFI") == 0) {              // ---- WIFI OFF|AP|SCAN ----
    const char *a = strtok(nullptr, " ");             // the mode argument
    aggressorSetWifi(a ? a : "OFF");                  // apply (missing -> OFF)
    Serial.printf("OK WIFI %s\n", aggressorWifiName());   // confirm the mode actually set
  } else if (strcmp(cmd, "LOAD") == 0) {              // ---- LOAD IDLE|BUSY ----
    const char *a = strtok(nullptr, " ");             // the mode argument
    aggressorSetLoad(a ? a : "IDLE");                 // apply (missing -> IDLE)
    Serial.printf("OK LOAD %s\n", aggressorLoadName());   // confirm
  } else if (strcmp(cmd, "CAP") == 0) {               // ---- CAP n discard S|B ----
    cmdCapture();                                     // run a capture
  } else {                                            // anything else
    Serial.printf("ERR unknown command '%s'\n", cmd); // tell the PC
  }
}

/*
 * -----------------------------------------------------------------------------
 *  loop()  —  runs over and over: collect characters into a line
 * -----------------------------------------------------------------------------
 *  Serial.available() says how many received bytes are waiting.
 *  Serial.read() takes one. We collect bytes until '\n', then hand the
 *  complete line to handleLine(). '\r' is ignored so the commands also work
 *  from terminals that send "\r\n". "static" local variables keep their
 *  value between calls of loop().
 * -----------------------------------------------------------------------------
 */
void loop() {
  static char   line[CMD_LINE_MAX];                       // the line being collected
  static size_t len = 0;                              // how many characters are in it

  while (Serial.available() > 0) {                    // for every byte that has arrived ...
    char c = char(Serial.read());                     // ... take it
    if (c == '\r') {                                  // carriage return
      continue;                                       // ignore
    }
    if (c == '\n') {                                  // end of line
      line[len] = '\0';                               // terminate the C string
      handleLine(line);                               // run the command
      len = 0;                                        // start a new line
    } else if (len < CMD_LINE_MAX - 1) {                  // room left (keep 1 byte for '\0')
      line[len++] = c;                                // append the character
    }                                                 // (characters beyond CMD_LINE_MAX are dropped)
  }
}
