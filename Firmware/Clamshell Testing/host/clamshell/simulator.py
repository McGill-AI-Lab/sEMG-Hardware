"""
==============================================================================
 simulator.py  —  a fake ESP32 + ADS1298 that speaks the same protocol
==============================================================================

WHY A SIMULATOR?
----------------
`python run_suite.py --simulate` runs the complete suite (live window,
analysis, report) with no hardware attached. Uses:
  - learning what every experiment does before touching the board,
  - checking a change to the analysis code quickly,
  - `--simulate faulty` shows what FAILs look like: interleaved zero frames,
    missed samples, a noisy channel, strong mains, a gain/scaling error on the
    test signal, a register that does not read back.

HOW IT PRETENDS TO BE A SERIAL PORT
-----------------------------------
`Board` (device.py) only ever calls `.write()`, `.read()`, `.in_waiting`,
`.reset_input_buffer()` and `.close()` on its port. `SimulatedPort` provides
exactly those:
  - `write()` receives command lines; text replies are queued immediately.
  - On "CAP", frames are generated in blocks as (simulated) time passes, so
    data trickles in at the real sample rate (times `speed`).

THE SIGNAL MODEL (numbers chosen to look like a healthy ADS1298)
----------------------------------------------------------------
Input-referred noise of a shorted channel is the RSS of
  - PGA noise:  35 nV/sqrt(Hz)                          (independent of gain)
  - ADC noise:  0.10 uV/sqrt(Hz) at the modulator, divided by the gain
  - a "1/f-like" low-frequency rise below ~1 Hz
  - a small component shared by all channels (reference/supply) + 60 Hz
Every number is in `PROFILES` below so it can be changed in one place.
NOTHING here is measured data: it only exists to exercise the code.
==============================================================================
"""

from __future__ import annotations

import time                                              # wall clock for pacing the fake data stream

import numpy as np                                       # random numbers and vector maths
from scipy.signal import lfilter                         # 1-pole low-pass filter for the slow-noise component

from . import ads1298 as ads                             # register decoding and scaling helpers

# ---------------------------------------------------------------------------
# Simulation parameters. "clean" = a good board, "faulty" = several problems.
# ---------------------------------------------------------------------------
PROFILES = {
    "clean": {
        "pga_density_uV": 0.035,        # PGA input noise density, uV/sqrt(Hz)
        "adc_density_uV": 0.10,         # ADC noise density at the modulator input, uV/sqrt(Hz)
        "slow_plateau_uV": 0.15,        # density of the slow (<1 Hz) noise, uV/sqrt(Hz)
        "shared_fraction": 0.08,        # shared noise as a fraction of each channel's noise
        "mains_uV": (0.08, 0.04),       # 50 Hz and 150 Hz amplitudes (input-referred), uV
        "clock_error": 0.003,           # internal oscillator 0.3 % fast
        "zero_frames": 0.0,             # fraction of frames returned as all zeros
        "missed_at_4k": 0.0,            # fraction of conversions missed at >= 4 kSPS
        "bad_channel": None,            # channel number with 3x noise, or None
        "test_gain_bug": False,         # True = test signal scaled as if gain were 1
        "readback_bug": False,          # True = CH8SET reads back with a flipped bit
        "wifi_scan_burst_uV": 1.5,      # extra noise during WiFi TX bursts
        "wifi_ap_spike_uV": 0.5,        # spike at each beacon (every 102.4 ms)
    },
}
PROFILES["faulty"] = dict(PROFILES["clean"], **{   # start from "clean", override some entries
    "mains_uV": (2.0, 0.6),
    "zero_frames": 0.5,
    "missed_at_4k": 0.004,
    "bad_channel": 5,
    "test_gain_bug": True,
    "readback_bug": True,
    "wifi_scan_burst_uV": 6.0,
    "wifi_ap_spike_uV": 3.0,
})


class SimulatedPort:
    """A stand-in for `serial.Serial` that answers like the firmware."""

    def __init__(self, profile: str = "clean", speed: float = 5.0, seed: int = 1):
        if profile not in PROFILES:                                  # unknown profile name?
            raise ValueError(f"unknown simulation profile {profile!r}; use one of {list(PROFILES)}")
        self.p = PROFILES[profile]                                   # the parameter set in use
        self.speed = max(0.1, float(speed))                          # how many times faster than real time
        self.rng = np.random.default_rng(seed)                       # reproducible random numbers
        self.timeout = 0.05                                          # like pyserial: read() waits at most this long
        self._out = bytearray()                                      # bytes waiting to be "received" by the PC
        self._regs = [0x86, 0x00, 0x40, 0x00] + [0x61] * 8           # power-on register defaults (approximate)
        self._sclk, self._wifi, self._load = 4000000, "OFF", "IDLE"  # aggressor state
        self._cap = None                                             # state of a running capture (dict) or None
        self._clock_s = 0.0                                          # simulated seconds since "power on" (for warm-up)
        self._offsets = self.rng.uniform(-30, 30, 8)                 # fixed offset per channel, uV
        self._drift = self.rng.uniform(-0.3, 0.3, 8)                 # offset drift per channel, uV/degC
        self._out += b"READY fw=simulator id=92\n"                   # boot banner, like the real firmware

    # ------------------------------------------------------------------ port API
    @property
    def in_waiting(self) -> int:
        """Bytes ready to read (pyserial has the same property)."""
        self._produce()                                              # generate any data that is now "due"
        return len(self._out)                                        # how many bytes are queued

    def reset_input_buffer(self):
        """Throw away queued input (pyserial has the same method)."""
        self._out.clear()                                            # forget everything queued

    def close(self):
        """Nothing to release for a fake port."""

    def read(self, size: int = 1) -> bytes:
        """Return up to `size` bytes, waiting at most `self.timeout` for some to appear."""
        deadline = time.monotonic() + self.timeout                   # pyserial-style timeout
        while True:
            self._produce()                                          # generate due data
            if self._out or time.monotonic() >= deadline:            # have data, or gave up waiting
                break
            time.sleep(0.005)                                        # short nap, then look again
        chunk = bytes(self._out[:size])                              # take at most `size` bytes
        del self._out[:size]                                         # remove them from the queue
        return chunk

    def write(self, data: bytes) -> int:
        """Receive command text from the PC; queue the reply."""
        for line in data.decode("ascii", errors="replace").splitlines():   # usually exactly one line
            self._handle(line.strip())                               # act on it
        return len(data)                                             # pyserial returns the byte count

    # ------------------------------------------------------------- command handling
    def _reply(self, text: str):
        """Queue one reply line."""
        self._out += (text + "\n").encode("ascii")                   # text -> bytes with newline

    def _handle(self, line: str):
        """Same command set as firmware/src/main.cpp."""
        words = line.split()                                         # split at spaces
        if not words:                                                # empty line
            return
        cmd, args = words[0], words[1:]                              # command name and its arguments
        if cmd == "PING":
            self._reply("OK PONG fw=simulator heap=300000 maxalloc=200000 baud=2000000")
        elif cmd == "ID":
            self._reply("OK ID 92")
        elif cmd == "REGS":
            regs = [0x92] + self._regs[:4] + [0x00] + self._regs[4:] + [0] * 13   # rough 26-register image
            regs = regs[:26]                                         # exactly 26 values
            self._reply("OK REGS " + " ".join(f"{r:02X}" for r in regs))
        elif cmd == "CFG":
            values = [int(a, 16) for a in args]                      # the 12 requested values
            self._regs = list(values)                                # "write" them
            readback = list(values)                                  # perfect readback ...
            if self.p["readback_bug"]:                               # ... unless the fault is enabled
                readback[11] ^= 0x08                                 # flip a reserved bit of CH8SET
            ok = readback == values                                  # compare
            self._reply(("OK CFG " if ok else "ERR CFG mismatch ") + " ".join(f"{r:02X}" for r in readback))
            self._clock_s += 0.3                                     # configuring takes a little time
        elif cmd == "RESET":
            self._regs = [0x86, 0x00, 0x40, 0x00] + [0x61] * 8       # defaults again
            self._clock_s += 1.2                                     # power cycle time
            self._reply("OK RESET id=92")
        elif cmd == "SCLK":
            self._sclk = int(args[0])                                # remember
            self._reply(f"OK SCLK {self._sclk}")
        elif cmd == "WIFI":
            self._wifi = (args[0] if args else "OFF").upper()        # remember
            self._reply(f"OK WIFI {self._wifi}")
        elif cmd == "LOAD":
            self._load = (args[0] if args else "IDLE").upper()       # remember
            self._reply(f"OK LOAD {self._load}")
        elif cmd == "CAP":
            self._start_capture(int(args[0]), int(args[1]), args[2].upper() == "B")
        else:
            self._reply(f"ERR unknown command '{cmd}'")

    # ------------------------------------------------------------------- capture
    def _start_capture(self, n: int, discard: int, buffered: bool):
        """Set up the state of a capture; frames are generated later in _produce()."""
        cfg = ads.decode_registers(self._regs)                       # what the "chip" is set to
        rate = cfg["rate"] or 500                                    # nominal samples/s
        if buffered and n * 34 > 200000:                             # same memory limit as the real board
            self._reply("ERR CAP nomem maxalloc=200000")
            return
        self._reply(f"OK CAP n={n} bytes=34")                        # header line
        self._cap = {
            "n": n, "made": 0, "buffered": buffered, "cfg": cfg,     # totals and settings
            "rate_true": rate * (1 + self.p["clock_error"]),         # actual rate (oscillator error)
            "t0": time.monotonic(), "seq": 0, "missed": 0,           # pacing start, seq counter, missed counter
            "lp_state": np.zeros(8), "pending": bytearray(),         # slow-noise filter state, B-mode buffer
            "clock0": self._clock_s + discard / rate,                # simulated time of the first kept frame
        }

    def _produce(self):
        """Generate every frame that is due by now and queue its packet bytes."""
        c = self._cap                                                # running capture, if any
        if c is None:                                                # none
            return
        elapsed = (time.monotonic() - c["t0"]) * self.speed          # simulated seconds since CAP
        due = min(c["n"], int(elapsed * c["rate_true"]))             # frames that should exist by now
        if c["buffered"] and due < c["n"]:                           # B mode: nothing is sent until the end
            due_send = 0
        else:
            due_send = due
        while c["made"] < due:                                       # generate in blocks of <= 2000 frames
            k = min(2000, due - c["made"])                           # block size
            c["pending"] += self._make_packets(c, k)                 # build them
            c["made"] += k                                           # count them
        if due_send:                                                 # something may be sent
            self._out += c["pending"]                                # move to the output queue
            c["pending"] = bytearray()                               # empty the staging buffer
        if c["made"] >= c["n"] and not c["pending"]:                 # finished and flushed
            r = c["rate_true"]                                       # true rate
            first_us = int(c["clock0"] * 1e6)                        # time of first frame, us
            last_us = int(first_us + (c["seq"] - c["first_seq"]) / r * 1e6)   # time of the last frame
            self._out += (f"\nEND sent={c['n']} missed={c['missed']} timeouts=0 first_seq={c['first_seq']} "
                          f"last_seq={c['seq']} first_us={first_us} last_us={last_us} sclk={self._sclk} "
                          f"wifi={self._wifi} load={self._load}\n").encode("ascii")
            self._clock_s += (c["seq"] + 1) / r                      # advance the simulated clock
            self._cap = None                                         # capture done

    def _make_packets(self, c: dict, k: int) -> bytes:
        """Build k packets (34 bytes each) for the current configuration."""
        cfg, p, rng = c["cfg"], self.p, self.rng                     # shorthand names
        fs = cfg["rate"] or 500                                      # nominal rate (the noise model uses it)
        # ---- sequence numbers, with optional missed conversions ----------------
        step = np.ones(k, dtype=np.int64)                            # normally each frame is the next DRDY
        if fs >= 4000 and p["missed_at_4k"] and not c["buffered"]:   # simulate the UART not keeping up
            step[rng.random(k) < p["missed_at_4k"]] = 2              # sometimes skip one
        if c["seq"] == 0:                                            # first block of this capture
            step[0] = 1                                              # starts at seq 1
            c["first_seq"] = 1
        seqs = c["seq"] + np.cumsum(step)                            # running DRDY count
        c["missed"] += int((step - 1)[1:].sum() + (step[0] - 1 if c["made"] else 0))   # count skips
        c["seq"] = int(seqs[-1])                                     # remember where we are
        t = c["clock0"] + (seqs - 1) / c["rate_true"]                # simulated time of each frame, s
        # ---- per-channel input-referred microvolts --------------------------------
        uV = np.zeros((k, 8))                                        # signal at the input pins
        gains = np.ones(8)                                           # gain per channel
        shared = rng.normal(0, 1, k)                                 # one shared noise sequence
        mains = p["mains_uV"][0] * np.sin(2 * np.pi * 50 * t) + p["mains_uV"][1] * np.sin(2 * np.pi * 150 * t + 1)
        temp_c = 26 + 4 * (1 - np.exp(-t / 90.0))                    # board warming up from 26 to 30 degC
        for ch in cfg["channels"]:                                   # each channel
            i = ch["channel"] - 1                                    # column index
            if not ch["powered"]:                                    # powered down: outputs ~0
                continue
            g = ch["gain"] or 6                                      # its gain
            gains[i] = g
            sig_pga = p["pga_density_uV"] * np.sqrt(fs / 2)          # PGA noise per sample, uV
            sig_adc = p["adc_density_uV"] * np.sqrt(fs / 2) / g      # ADC noise referred to input, uV
            sigma = np.hypot(sig_pga, sig_adc)                       # RSS
            if p["bad_channel"] == ch["channel"]:                    # the deliberately bad channel
                sigma *= 3
            if self._sclk >= 8000000:                                # fast SPI edges couple a little
                sigma *= 1.05
            if c["buffered"]:                                        # USB idle during the capture
                sigma *= 0.97
            noise = rng.normal(0, sigma, k)                          # independent noise
            w = rng.normal(0, p["slow_plateau_uV"] * np.sqrt(fs / 2), k)   # input of the slow-noise filter
            a = np.exp(-2 * np.pi * 1.0 / fs)                        # 1-pole low-pass at 1 Hz
            slow, zf = lfilter([1 - a], [1, -a], w, zi=[c["lp_state"][i] * a])   # filter, continuing previous state
            c["lp_state"][i] = slow[-1]                              # keep the state for the next block
            common = p["shared_fraction"] * sigma * shared + mains   # shared part
            mux = ch["mux"]                                          # input selection
            if mux == ads.MUX_SHORTED:                               # shorted input
                v = self._offsets[i] + self._drift[i] * (temp_c - 26) + noise + slow + common
            elif mux == ads.MUX_NORMAL:                              # external inputs shorted at the connector
                johnson = 0.0129 * np.sqrt(2) * np.sqrt(fs / 2)      # two 10 kOhm resistors
                v = self._offsets[i] + noise + slow + rng.normal(0, johnson, k) + common + 3 * mains
            elif mux == ads.MUX_TEST:                                # internal test signal
                amp_uV = ads.test_signal_half_amplitude_mV(cfg["test_amp"], 2.4) * 1000   # +/- amplitude
                if cfg["test_freq"] == ads.TEST_FREQ_DC:             # DC level
                    sq = np.full(k, amp_uV)
                else:                                                # square wave from the (fast) clock
                    f = ads.test_signal_frequency(cfg["test_freq"]) * (1 + p["clock_error"])
                    sq = np.where(np.sin(2 * np.pi * f * t) >= 0, amp_uV, -amp_uV)
                if p["test_gain_bug"]:                               # reproduce the "1/6 amplitude" symptom
                    sq = sq / g
                v = self._offsets[i] + sq + noise + slow + common
            elif mux == ads.MUX_MVDD:                                # supply measurement
                volts = 0.825 if ch["channel"] in (3, 4) else 1.65 * 0.998   # DVDD/4 or (AVDD+AVSS)/2
                v = volts * 1e6 + rng.normal(0, 40, k) + 30 * np.sin(2 * np.pi * 50 * t)
            elif mux == ads.MUX_TEMP:                                # temperature sensor
                v = 145300 + 490 * (temp_c - 25) + noise
            else:                                                    # anything else: just noise
                v = noise
            if self._wifi == "SCAN":                                 # radio transmitting in bursts
                burst = rng.random(k) < 0.03
                v = v + burst * rng.normal(0, p["wifi_scan_burst_uV"], k)
            elif self._wifi == "AP":                                 # beacon every 102.4 ms
                v = v + p["wifi_ap_spike_uV"] * ((t % 0.1024) < (1.0 / fs))
            uV[:, i] = v                                             # store
        # ---- input uV -> 24-bit codes ---------------------------------------------
        codes = np.round(uV * 1e-6 * gains / 2.4 * ads.FULL_SCALE_CODES)   # volts * gain / VREF * full scale
        codes = np.clip(codes, -2**23, 2**23 - 1).astype(np.int64)   # the converter saturates at full scale
        raw = codes & 0xFFFFFF                                       # two's complement 24-bit pattern
        status = np.full(k, 0xC00000, dtype=np.int64)                # status word: top nibble 1100
        # ---- assemble packets --------------------------------------------------------
        pk = np.zeros((k, 34), dtype=np.uint8)                       # one row per packet
        pk[:, 0], pk[:, 1] = 0xA5, 0x5A                              # sync bytes
        for b in range(4):                                           # seq, little-endian
            pk[:, 2 + b] = (seqs >> (8 * b)) & 0xFF
        for b in range(3):                                           # status, big-endian
            pk[:, 6 + b] = (status >> (8 * (2 - b))) & 0xFF
        for i in range(8):                                           # channels, big-endian
            for b in range(3):
                pk[:, 9 + 3 * i + b] = (raw[:, i] >> (8 * (2 - b))) & 0xFF
        if p["zero_frames"]:                                         # the "interleaved zeros" fault
            bad = rng.random(k) < p["zero_frames"]
            pk[bad, 6:33] = 0                                        # whole frame (status + data) reads 0
        pk[:, 33] = np.bitwise_xor.reduce(pk[:, 2:33], axis=1)       # checksum
        return pk.tobytes()                                          # rows -> one bytes object
