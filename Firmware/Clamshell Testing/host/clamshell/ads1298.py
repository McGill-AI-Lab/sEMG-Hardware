"""
==============================================================================
 ads1298.py  —  everything the PC needs to know about ADS1298 registers
==============================================================================

WHY THIS LIVES ON THE PC
------------------------
The firmware only writes the bytes it is given. Deciding WHICH bytes to write
(data rate, gain, input multiplexer, test signal) happens here, in one place,
so the rest of the suite can say "500 SPS, gain 6, inputs shorted" instead of
"0x86 ... 0x01".

The register bit layouts come from the TI datasheet SBAS459 ("Register Map").
The values are also explained in clamshell_validation.md.

THE 12 BYTES SENT WITH "CFG"
----------------------------
    CONFIG1, CONFIG2, CONFIG3, CONFIG4, CH1SET, CH2SET, ..., CH8SET

    CONFIG1  bit 7      HR        1 = high-resolution mode (we always use it)
             bit 6      DAISY_EN  0 = daisy-chain mode (fine with one chip)
             bit 5      CLK_EN    0 = do not output the clock on the CLK pin
             bits 2:0   DR        data rate, see RATE_CODES below

    CONFIG2  bit 4      INT_TEST  1 = test signal generated internally
             bit 2      TEST_AMP  0 = 1 x (VREFP-VREFN)/2.4 mV, 1 = 2 x
             bits 1:0   TEST_FREQ 00 = fCLK/2^21, 01 = fCLK/2^20, 11 = DC
             (bits 7, 6, 5, 3 kept 0, as recommended in todo.md: 0x51 -> 0x11)

    CONFIG3  0xC0 = internal reference buffer on (bit 7), bit 6 must be 1,
                    VREF_4V = 0 -> 2.4 V reference (right for a 3.3 V AVDD)

    CONFIG4  0x00 = continuous conversion, lead-off comparators off

    CHnSET   bit 7      PDn       1 = channel powered down
             bits 6:4   GAIN      PGA gain, see GAIN_CODES below
             bits 2:0   MUX       input selection, see MUX_* below
==============================================================================
"""

from __future__ import annotations          # lets us write type hints like "list[int]" on older Pythons too

# ---------------------------------------------------------------------------
# Fixed facts about the chip and the board
# ---------------------------------------------------------------------------
EXPECTED_ID = 0x92                          # ID register value of an ADS1298 (8 channels, ADS129x family)
F_CLK_HZ = 2.048e6                          # internal oscillator frequency (datasheet: 2.048 MHz)
FULL_SCALE_CODES = 2**23 - 1                # largest positive 24-bit code, 0x7FFFFF = 8 388 607
BANDWIDTH_FACTOR = 0.262                    # -3 dB bandwidth = 0.262 x data rate (sinc3 filter, datasheet "Digital Filter")
N_CHANNELS = 8                              # ADS1298 channel count

# ---------------------------------------------------------------------------
# CONFIG1 data-rate codes in high-resolution mode (DR[2:0])
# ---------------------------------------------------------------------------
RATE_CODES = {                              # samples per second -> DR bits
    32000: 0b000,
    16000: 0b001,
    8000: 0b010,
    4000: 0b011,
    2000: 0b100,
    1000: 0b101,
    500: 0b110,
}

# ---------------------------------------------------------------------------
# CHnSET gain codes (GAIN[2:0]). Note the odd order: 000 means gain 6.
# ---------------------------------------------------------------------------
GAIN_CODES = {6: 0b000, 1: 0b001, 2: 0b010, 3: 0b011, 4: 0b100, 8: 0b101, 12: 0b110}

# ---------------------------------------------------------------------------
# CHnSET input multiplexer codes (MUX[2:0])
# ---------------------------------------------------------------------------
MUX_NORMAL = 0b000                          # normal electrode input (IN+ / IN- pins)
MUX_SHORTED = 0b001                         # both inputs tied internally to (AVDD+AVSS)/2: noise / offset test
MUX_RLD_MEAS = 0b010                        # RLD measurement (not used here)
MUX_MVDD = 0b011                            # supply measurement
MUX_TEMP = 0b100                            # temperature sensor
MUX_TEST = 0b101                            # internal test signal
MUX_NAMES = {0: "normal", 1: "shorted", 2: "rld", 3: "mvdd", 4: "temp", 5: "test"}   # for printing

CH_POWERED_DOWN = 0x81                      # PDn = 1 and MUX = shorted: the recommended "off" state

# ---------------------------------------------------------------------------
# CONFIG2 test-signal frequency codes
# ---------------------------------------------------------------------------
TEST_FREQ_SLOW = 0b00                       # f_CLK / 2^21 ~ 0.98 Hz
TEST_FREQ_FAST = 0b01                       # f_CLK / 2^20 ~ 1.95 Hz
TEST_FREQ_DC = 0b11                         # constant (DC) level

# Bits of CONFIG registers that are read-only status bits and may legitimately
# read back differently from what was written. Index = position in the 12-byte
# CFG list. CONFIG3 bit 0 is RLD_STAT (read-only), so ignore it when comparing.
READBACK_MASKS = [0xFF, 0xFF, 0xFE, 0xFF] + [0xFF] * 8


def test_signal_frequency(test_freq: int) -> float:
    """
    Frequency in Hz of the internal square-wave test signal.

    The test signal is made by dividing the 2.048 MHz master clock:
        TEST_FREQ = 00 -> f_CLK / 2**21 = 0.977 Hz
        TEST_FREQ = 01 -> f_CLK / 2**20 = 1.953 Hz
        TEST_FREQ = 11 -> DC (returns 0.0)
    """
    if test_freq == TEST_FREQ_DC:               # DC level: no frequency
        return 0.0                              # signal it with 0
    divider = 2**21 if test_freq == TEST_FREQ_SLOW else 2**20   # choose the divider
    return F_CLK_HZ / divider                   # clock / divider = Hz


def test_signal_half_amplitude_mV(test_amp: int, vref: float) -> float:
    """
    Height of the test signal ABOVE its midpoint, in mV (datasheet, CONFIG2):
        TEST_AMP = 0 -> 1 x (VREFP - VREFN) / 2.4 mV  ->  1 mV for VREF = 2.4 V
        TEST_AMP = 1 -> 2 x (VREFP - VREFN) / 2.4 mV  ->  2 mV
    So the square wave swings +/- this value, i.e. high-minus-low is twice it.
    """
    return (2.0 if test_amp else 1.0) * vref / 2.4   # mV


def build_registers(rate: int, gains: list[int], muxes: list[int], enabled: list[int],
                    int_test: bool = False, test_amp: int = 0, test_freq: int = TEST_FREQ_FAST) -> list[int]:
    """
    Build the 12 register values for a "CFG" command.

    Parameters
    ----------
    rate      : data rate in samples/s (must be a key of RATE_CODES)
    gains     : 8 PGA gains, index 0 = CH1 (ignored for disabled channels)
    muxes     : 8 MUX codes, index 0 = CH1 (ignored for disabled channels)
    enabled   : list of channel NUMBERS (1..8) to power up; all others are powered down
    int_test  : True to switch the internal test-signal generator on (CONFIG2 bit 4)
    test_amp  : 0 or 1 (CONFIG2 bit 2)
    test_freq : 0, 1 or 3 (CONFIG2 bits 1:0)

    Returns a list of 12 ints in the CFG order.
    """
    if rate not in RATE_CODES:                                   # unsupported rate?
        raise ValueError(f"unsupported data rate {rate}; choose from {sorted(RATE_CODES)}")
    config1 = 0x80 | RATE_CODES[rate]                            # HR mode bit + data-rate bits
    config2 = (0x10 if int_test else 0x00) | ((test_amp & 1) << 2) | (test_freq & 0b11)   # test-signal bits
    config3 = 0xC0                                               # internal reference buffer on, 2.4 V
    config4 = 0x00                                               # continuous conversions
    chset = []                                                   # will hold CH1SET..CH8SET
    for ch in range(1, N_CHANNELS + 1):                          # channel numbers 1..8
        if ch in enabled:                                        # this channel should run
            g = gains[ch - 1]                                    # its gain
            if g not in GAIN_CODES:                              # invalid gain?
                raise ValueError(f"unsupported gain {g}; choose from {sorted(GAIN_CODES)}")
            chset.append((GAIN_CODES[g] << 4) | (muxes[ch - 1] & 0b111))   # PDn=0, gain bits, mux bits
        else:                                                    # channel not used
            chset.append(CH_POWERED_DOWN)                        # power it down, inputs shorted
    return [config1, config2, config3, config4] + chset          # the 12 values in order


def decode_registers(values: list[int]) -> dict:
    """
    Turn 12 register bytes back into readable settings. Used by the simulator
    (to know what to generate) and for printing in the report.
    """
    c1, c2 = values[0], values[1]                                # first two CONFIG registers
    rate_by_code = {v: k for k, v in RATE_CODES.items()}         # invert the rate table
    gain_by_code = {v: k for k, v in GAIN_CODES.items()}         # invert the gain table
    chans = []                                                   # per-channel settings
    for i, b in enumerate(values[4:12]):                         # CH1SET..CH8SET
        chans.append({
            "channel": i + 1,                                    # channel number
            "powered": not (b & 0x80),                           # PDn bit clear = powered
            "gain": gain_by_code.get((b >> 4) & 0b111, None),    # gain from bits 6:4
            "mux": b & 0b111,                                    # mux from bits 2:0
        })
    return {
        "hr": bool(c1 & 0x80),                                   # high-resolution mode?
        "rate": rate_by_code.get(c1 & 0b111),                    # samples/s (HR mode)
        "int_test": bool(c2 & 0x10),                             # internal test signal on?
        "test_amp": (c2 >> 2) & 1,                               # amplitude bit
        "test_freq": c2 & 0b11,                                  # frequency bits
        "channels": chans,                                       # list of 8 dicts
    }


def readback_mismatches(written: list[int], readback: list[int]) -> list[str]:
    """
    Compare written vs read-back register values, ignoring read-only bits.
    Returns a list of human-readable problems (empty list = all good).
    """
    names = ["CONFIG1", "CONFIG2", "CONFIG3", "CONFIG4"] + [f"CH{i}SET" for i in range(1, 9)]   # labels
    problems = []                                                # collected messages
    for name, w, r, m in zip(names, written, readback, READBACK_MASKS):   # walk all 12 in parallel
        if (w & m) != (r & m):                                   # differ in a writable bit?
            problems.append(f"{name}: wrote 0x{w:02X}, read 0x{r:02X}")   # describe it
    return problems


def lsb_input_referred_uV(gain: int, vref: float) -> float:
    """
    Size of one code step referred to the INPUT pins, in microvolts:
        LSB_in = VREF / (G * (2**23 - 1))
    e.g. 2.4 V / (6 * 8 388 607) = 0.0477 uV = 47.7 nV at gain 6.
    """
    return vref / (gain * FULL_SCALE_CODES) * 1e6                # volts -> microvolts


def codes_to_uV(codes, gain, vref: float):
    """
    Convert raw signed 24-bit codes to INPUT-referred microvolts.

    `codes` can be a NumPy array; `gain` can be a number or an array that
    broadcasts against it (e.g. one gain per channel column). Dividing by the
    gain moves the noise back to the electrodes, which is the number you
    compare to an sEMG signal (clamshell_validation.md, section 0).
    """
    return codes * (vref / FULL_SCALE_CODES) / gain * 1e6        # code -> volts at modulator -> volts at input -> uV


def bandwidth_hz(rate: float) -> float:
    """-3 dB bandwidth of the sinc3 digital filter: 0.262 x data rate."""
    return BANDWIDTH_FACTOR * rate                               # e.g. 131 Hz at 500 SPS
