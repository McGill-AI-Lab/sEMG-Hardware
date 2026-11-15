"""
==============================================================================
 device.py  —  talk to the firmware over the serial port
==============================================================================

WHAT THIS MODULE DOES
---------------------
1. Opens the serial port (or the simulator, which behaves like one).
2. Sends one-line text commands ("PING", "CFG ...", "CAP ...") and waits for
   the "OK ..." / "ERR ..." reply.
3. During a capture, receives the stream of 34-byte binary packets, checks
   every one (sync bytes + checksum) and turns them into NumPy arrays.

LIBRARIES USED
--------------
- pyserial (`import serial`): `serial.Serial(port, baud)` opens a serial port.
  Its key methods are `.write(bytes)`, `.read(n)` (returns up to n bytes,
  waiting at most `.timeout` seconds) and `.in_waiting` (bytes ready now).
- NumPy (`import numpy as np`): fast arrays. We decode thousands of packets at
  once with array operations instead of a slow Python loop per byte.
- dataclasses: `@dataclass` auto-writes the boring `__init__` for classes that
  mostly hold data.

THE PACKET (must match firmware/src/main.cpp)
---------------------------------------------
    byte  0      0xA5          sync 1
    byte  1      0x5A          sync 2
    bytes 2..5   seq           uint32, little-endian (lowest byte first)
    bytes 6..8   status        24-bit status word, big-endian
    bytes 9..32  CH1..CH8      3 bytes each, big-endian two's complement
    byte  33     checksum      XOR of bytes 2..32
==============================================================================
"""

from __future__ import annotations

import glob                                   # find files/devices matching a pattern, e.g. /dev/cu.usbserial*
import re                                     # regular expressions, used to pick numbers out of reply text
import time                                   # time.monotonic() for timeouts, time.sleep() for short waits
from dataclasses import dataclass, field      # @dataclass decorator, field(default_factory=...) for mutable defaults

import numpy as np                            # array maths

PACKET_BYTES = 34                             # size of one packet (sync 2 + seq 4 + frame 27 + checksum 1)
SYNC = b"\xA5\x5A"                            # the two sync bytes as a Python bytes object


class DeviceError(RuntimeError):
    """Raised when the board replies ERR, or does not reply in time."""


# ---------------------------------------------------------------------------
# Finding the serial port
# ---------------------------------------------------------------------------
def find_port() -> str:
    """
    Guess the serial port of the ESP32 on macOS / Linux / Windows.

    USB-to-UART bridges show up under different names depending on the chip
    and the operating system. We try the common patterns and take the first.
    On Windows, pyserial's list_ports gives names like COM5.
    """
    patterns = ["/dev/cu.usbserial*", "/dev/cu.SLAB_USBtoUART*", "/dev/cu.wchusbserial*",   # macOS bridge names
                "/dev/cu.usbmodem*", "/dev/ttyUSB*", "/dev/ttyACM*"]                        # macOS native USB, Linux
    for pattern in patterns:                                  # try each pattern in order
        found = sorted(glob.glob(pattern))                    # all devices that match it
        if found:                                             # at least one?
            return found[0]                                   # use the first
    try:                                                      # Windows (or anything else): ask pyserial
        from serial.tools import list_ports                   # imported here because only this path needs it
        ports = [p.device for p in list_ports.comports()]     # e.g. ["COM3", "COM5"]
        if ports:                                             # found something?
            return ports[0]                                   # use the first
    except Exception:                                         # list_ports can fail on unusual systems
        pass                                                  # fall through to the error below
    raise DeviceError("No serial port found. Plug the board into the USB port labelled UART, "
                      "or pass --port explicitly.")


# ---------------------------------------------------------------------------
# Decoding packets
# ---------------------------------------------------------------------------
class PacketParser:
    """
    Turns an unstructured stream of bytes into validated packets.

    HOW IT WORKS
    Bytes arrive in random-sized chunks (whatever the OS hands us). We append
    them to `self.buf`, then:
      1. Find the next sync pair 0xA5 0x5A. Bytes before it are junk
         (counted in `skipped_bytes`).
      2. Look at every complete 34-byte slot from there as a 2-D NumPy array
         (one row per packet) and check, for ALL rows at once, that the sync
         bytes are right and the XOR checksum matches.
      3. Keep the leading run of good rows. At the first bad row, drop one
         byte and search for the next sync pair (this "resynchronises" after a
         lost or corrupted byte).
    Anything left over (an incomplete packet) waits in `self.buf` for the
    next chunk.
    """

    def __init__(self):
        self.buf = bytearray()                    # bytes received but not yet turned into packets
        self.skipped_bytes = 0                    # junk bytes thrown away while searching for sync
        self.bad_packets = 0                      # slots with valid sync but wrong checksum

    def feed(self, data: bytes, max_packets: int | None = None) -> np.ndarray:
        """
        Add `data` and return all complete, valid packets as an (k, 34) uint8
        array. `max_packets` stops early so bytes after the last expected
        packet (the END line) stay in `self.buf`.
        """
        self.buf += data                                          # append the new bytes
        good_blocks = []                                          # list of (k_i, 34) arrays to join at the end
        taken = 0                                                 # how many packets we already return
        while max_packets is None or taken < max_packets:         # until we have enough (or no limit)
            i = self.buf.find(SYNC)                               # position of the next sync pair
            if i < 0:                                             # none in the buffer
                keep = 1 if self.buf.endswith(SYNC[:1]) else 0    # a lone trailing 0xA5 may be half a sync
                self.skipped_bytes += len(self.buf) - keep        # everything else is junk
                del self.buf[:len(self.buf) - keep]               # drop it
                break                                             # wait for more data
            if i > 0:                                             # junk before the sync
                self.skipped_bytes += i                           # count it
                del self.buf[:i]                                  # drop it
            n_full = len(self.buf) // PACKET_BYTES                # complete 34-byte slots available
            if max_packets is not None:                           # respect the limit
                n_full = min(n_full, max_packets - taken)         # do not take more than needed
            if n_full == 0:                                       # not even one complete packet yet
                break                                             # wait for more data
            block = np.frombuffer(bytes(self.buf[:n_full * PACKET_BYTES]), dtype=np.uint8)   # raw bytes -> array
            block = block.reshape(n_full, PACKET_BYTES)           # one row per packet
            sync_ok = (block[:, 0] == 0xA5) & (block[:, 1] == 0x5A)                 # sync check for every row
            sum_ok = np.bitwise_xor.reduce(block[:, 2:33], axis=1) == block[:, 33]  # XOR of bytes 2..32 vs byte 33
            ok = sync_ok & sum_ok                                 # a row is good only if both checks pass
            n_good = n_full if ok.all() else int(np.argmin(ok))   # length of the leading run of good rows
            if n_good:                                            # some good rows?
                good_blocks.append(block[:n_good].copy())         # keep them (copy: the buffer is about to change)
                taken += n_good                                   # count them
                del self.buf[:n_good * PACKET_BYTES]              # remove them from the buffer
            if n_good < n_full:                                   # we hit a bad row
                if sync_ok[n_good]:                               # sync was fine -> checksum failed
                    self.bad_packets += 1                         # count a corrupted packet
                self.skipped_bytes += 1                           # we drop one byte ...
                del self.buf[:1]                                  # ... and search for sync again
            elif len(self.buf) < PACKET_BYTES:                    # all good and nothing complete left
                break                                             # wait for more data
        if good_blocks:                                           # anything found?
            return np.concatenate(good_blocks)                    # one (k, 34) array
        return np.zeros((0, PACKET_BYTES), dtype=np.uint8)        # empty array with the right shape


def decode_packets(block: np.ndarray):
    """
    Split validated packets into seq numbers, status words and channel codes.

    Returns (seq, status, codes):
        seq    : (k,)   uint32   DRDY number of each frame
        status : (k,)   uint32   24-bit status word
        codes  : (k, 8) int32    signed 24-bit samples, column 0 = CH1

    Bit tricks used:
      - `a << 16` shifts bits left by 16 places (multiplies by 65536);
        OR-ing three shifted bytes rebuilds a 24-bit number.
      - Two's complement: if bit 23 is set the number is negative, and its
        value is (raw - 2**24). np.where applies that rule to every element.
    """
    b = block.astype(np.uint32)                                        # widen so shifts do not overflow
    seq = b[:, 2] | (b[:, 3] << 8) | (b[:, 4] << 16) | (b[:, 5] << 24) # little-endian uint32
    status = (b[:, 6] << 16) | (b[:, 7] << 8) | b[:, 8]                # big-endian 24-bit status word
    ch = b[:, 9:33].reshape(-1, 8, 3)                                  # (k, 8 channels, 3 bytes)
    raw = (ch[:, :, 0] << 16) | (ch[:, :, 1] << 8) | ch[:, :, 2]       # big-endian 24-bit unsigned
    codes = np.where(raw & 0x800000, raw.astype(np.int64) - (1 << 24), raw).astype(np.int32)   # sign-extend
    return seq.astype(np.uint32), status.astype(np.uint32), codes


# ---------------------------------------------------------------------------
# Result of one capture, straight from the wire
# ---------------------------------------------------------------------------
@dataclass
class RawCapture:
    """Everything one CAP command produced, before any analysis."""
    seq: np.ndarray                                   # (N,) DRDY numbers
    status: np.ndarray                                # (N,) status words
    codes: np.ndarray                                 # (N, 8) signed codes
    fw: dict = field(default_factory=dict)            # counters from the firmware END line
    host: dict = field(default_factory=dict)          # counters measured on the PC (bad packets, timing)


# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------
class Board:
    """
    A connection to the clamshell firmware.

    `port` is anything with pyserial's interface: a real `serial.Serial` or
    the `SimulatedPort` from simulator.py. All methods below work the same
    with either, which is what lets `--simulate` exercise the whole suite.
    """

    def __init__(self, port, log=print):
        self.port = port                       # the serial port object
        self.log = log                         # function used for status messages
        self._rx = bytearray()                 # received bytes not yet consumed as text lines
        self.info: dict = {}                   # facts from PING (fw version, heap, ...)
        self.state = {"sclk": None, "wifi": None, "load": None}   # last aggressor settings we sent

    # -------- opening -----------------------------------------------------
    @classmethod
    def open_serial(cls, port_name: str, baud: int, log=print) -> "Board":
        """
        Open a real serial port and make sure the firmware answers.

        About DTR/RTS: on ESP32 dev boards these two USB-UART control lines are
        wired to the chip's EN (reset) and BOOT pins. Opening a port can toggle
        them and reset the ESP32. We set both "off" before opening, which on
        most systems avoids the reset. If the board does not answer PING we
        pulse reset ourselves and wait for its READY line.
        """
        import serial                                         # pyserial; imported here so --simulate works without it
        ser = serial.Serial()                                 # create the object WITHOUT opening yet
        ser.port = port_name                                  # e.g. /dev/cu.usbserial-1140
        ser.baudrate = baud                                   # must equal SERIAL_BAUD in the firmware
        ser.timeout = 0.05                                    # read() returns after at most 50 ms
        ser.dtr = False                                       # do not assert DTR on open
        ser.rts = False                                       # do not assert RTS on open
        ser.open()                                            # now open it
        board = cls(ser, log)                                 # wrap it
        if not board._try_ping(attempts=3):                   # no answer: reset the ESP32 and retry
            log("  no reply to PING, resetting the ESP32 ...")
            ser.rts = True                                    # RTS asserted -> EN low -> ESP32 held in reset
            time.sleep(0.1)                                   # hold reset for 100 ms
            ser.rts = False                                   # release reset -> firmware boots
            time.sleep(2.5)                                   # adsBegin() takes ~1.3 s; wait a bit longer
            board._rx.clear()                                 # forget boot-ROM garbage
            ser.reset_input_buffer()                          # and anything still queued in the OS
            if not board._try_ping(attempts=5):               # still nothing?
                raise DeviceError(f"No answer from the firmware on {port_name} at {baud} baud. "
                                  "Is firmware/ flashed, and does 'baud' in test_plan.toml match SERIAL_BAUD?")
        return board

    @classmethod
    def open_simulator(cls, profile: str, speed: float, log=print) -> "Board":
        """Create a Board connected to the built-in simulator instead of hardware."""
        from .simulator import SimulatedPort                  # imported here to keep the dependency optional
        board = cls(SimulatedPort(profile=profile, speed=speed), log)   # wrap the fake port
        if not board._try_ping(attempts=2):                   # the simulator always answers; check anyway
            raise DeviceError("simulator did not answer")
        return board

    def close(self):
        """Close the port (safe to call twice)."""
        try:
            self.port.close()                                 # release the device
        except Exception:                                     # already closed / unplugged
            pass

    # -------- low-level text I/O -------------------------------------------
    def _read_line(self, timeout: float) -> str | None:
        """
        Return the next complete text line (without the newline), or None if
        no full line arrives within `timeout` seconds.
        """
        deadline = time.monotonic() + timeout                 # absolute time limit
        while True:
            nl = self._rx.find(b"\n")                         # is a full line already buffered?
            if nl >= 0:                                       # yes
                line = bytes(self._rx[:nl])                   # take it ...
                del self._rx[:nl + 1]                         # ... and remove it plus the newline
                return line.decode("ascii", errors="replace").strip()   # bytes -> text, drop \r and spaces
            if time.monotonic() > deadline:                   # out of time
                return None                                   # signal "nothing"
            chunk = self.port.read(max(1, getattr(self.port, "in_waiting", 0) or 1))   # read what is there (waits <= timeout)
            if chunk:                                         # got something
                self._rx += chunk                             # append to our buffer

    def command(self, text: str, timeout: float = 3.0) -> str:
        """
        Send one command line and return its reply (the text after "OK ").

        Lines that are not replies (boot messages, garbage at the wrong baud
        rate) are skipped. An "ERR ..." reply raises DeviceError.
        """
        self.port.write((text + "\n").encode("ascii"))        # text -> bytes, add newline, send
        word = text.split()[0]                                # command name, e.g. "CFG"
        deadline = time.monotonic() + timeout                 # overall time limit
        while time.monotonic() < deadline:                    # keep reading lines until a reply arrives
            line = self._read_line(deadline - time.monotonic())   # next line (or None)
            if line is None:                                  # timed out
                break                                         # -> error below
            if line.startswith("ERR"):                        # the firmware refused
                raise DeviceError(f"{text!r} -> {line}")      # report the exact reply
            if line.startswith("OK"):                         # a reply
                return line[3:]                               # strip the "OK " prefix
            # anything else (READY banner, boot text) is ignored
        raise DeviceError(f"no reply to {word} within {timeout:.0f} s")

    def _try_ping(self, attempts: int) -> bool:
        """Send PING up to `attempts` times; store the reply info; True on success."""
        for _ in range(attempts):                             # a few tries
            try:
                reply = self.command("PING", timeout=1.0)     # e.g. "PONG fw=... heap=..."
                self.info = dict(kv.split("=", 1) for kv in reply.split()[1:] if "=" in kv)   # parse key=value pairs
                return True                                   # it answered
            except DeviceError:                               # no answer this time
                time.sleep(0.3)                               # wait a little and retry
        return False                                          # never answered

    # -------- commands -------------------------------------------------------
    def read_id(self) -> int:
        """Read the ADS1298 ID register (expect 0x92)."""
        return int(self.command("ID").split()[1], 16)         # "ID 92" -> 0x92

    def read_all_registers(self) -> list[int]:
        """Dump registers 0x00..0x19."""
        return [int(x, 16) for x in self.command("REGS").split()[1:]]   # "REGS 92 86 ..." -> [0x92, 0x86, ...]

    def power_cycle(self) -> int:
        """Power-cycle the ADS1298 via PWDN; returns the ID read afterwards."""
        reply = self.command("RESET", timeout=5.0)            # takes ~1.2 s on the board
        return int(reply.split("id=")[1], 16)                 # "RESET id=92" -> 0x92

    def configure(self, values: list[int]) -> list[int]:
        """
        Write the 12 register values and return what the chip read back.
        Unlike other commands, a mismatch is NOT raised here: the caller
        compares with masks (read-only bits) and records the result.
        """
        text = "CFG " + " ".join(f"{v:02X}" for v in values)  # e.g. "CFG 86 00 C0 00 01 81 ..."
        self.port.write((text + "\n").encode("ascii"))        # send it
        deadline = time.monotonic() + 3.0                     # writing + 200 ms reference wait
        while time.monotonic() < deadline:                    # wait for the reply line
            line = self._read_line(deadline - time.monotonic())
            if line is None:                                  # nothing in time
                break
            if line.startswith("OK CFG") or line.startswith("ERR CFG mismatch"):   # normal replies
                return [int(x, 16) for x in line.split()[-12:]]   # last 12 words = readback bytes
            if line.startswith("ERR"):                        # any other error (bad argument)
                raise DeviceError(line)
        raise DeviceError("no reply to CFG")

    def set_aggressors(self, sclk: int, wifi: str, load: str):
        """Apply SPI clock / WiFi / CPU-load settings, skipping ones already set."""
        if self.state["sclk"] != sclk:                        # SPI clock changed?
            self.command(f"SCLK {int(sclk)}")                 # apply
            self.state["sclk"] = sclk                         # remember
        if self.state["wifi"] != wifi:                        # WiFi mode changed?
            self.command(f"WIFI {wifi.upper()}", timeout=8.0) # starting/stopping a scan can take a few seconds
            self.state["wifi"] = wifi
        if self.state["load"] != load:                        # CPU load changed?
            self.command(f"LOAD {load.upper()}")
            self.state["load"] = load

    def capture(self, n: int, discard: int, buffered: bool, rate: float, on_data=None) -> RawCapture:
        """
        Run one capture of `n` frames and return a RawCapture.

        `on_data(codes_so_far_count, new_codes)` is called as packets arrive so
        the live display can update. Steps:
          1. send "CAP n discard S|B" and wait for "OK CAP ...",
          2. read bytes and feed them to a PacketParser until n packets are in
             (or a time limit passes: frames can be lost, and the firmware
             aborts if DRDY stops),
          3. read the "END ..." line and parse its key=value counters.
        """
        mode = "B" if buffered else "S"                       # buffer or stream
        reply = self.command(f"CAP {n} {discard} {mode}", timeout=3.0)   # "CAP n=... bytes=34"
        if f"bytes={PACKET_BYTES}" not in reply:              # protocol mismatch between PC and firmware
            raise DeviceError(f"firmware packet size differs: {reply}")
        parser = PacketParser()                               # fresh parser
        blocks = []                                           # list of packet arrays
        received = 0                                          # packets so far
        t_start = time.monotonic()                            # wall-clock start
        duration = (n + discard) / rate                       # expected capture time in seconds
        limit = t_start + duration * 1.5 + 5.0                # generous deadline (50 % + 5 s)
        if buffered:                                          # B mode sends everything at the end
            limit += n * PACKET_BYTES * 10 / 2e6 + 5.0        # plus transfer time at 2 Mbaud
        pending = bytes(self._rx)                             # bytes already read past the OK line belong to the stream
        self._rx.clear()                                      # (they are binary, not text)
        end_text = None                                       # the END line, once found
        tail = b""                                            # last bytes seen, to spot "END" split across chunks
        while received < n and time.monotonic() < limit:      # until done or out of time
            chunk = pending or self.port.read(max(PACKET_BYTES, getattr(self.port, "in_waiting", 0) or 0))   # next bytes
            pending = b""                                     # only use the leftover once
            if not chunk:                                     # nothing this time
                continue                                      # try again
            window = tail + chunk                             # include the previous tail
            if b"\nEND " in window and received + len(parser.buf) // PACKET_BYTES < n:   # early END = firmware aborted
                pos = window.index(b"\nEND ")                 # where the END line starts
                end_text = window[pos + 1:]                   # keep it for parsing below
            tail = chunk[-8:]                                 # remember the tail
            pk = parser.feed(chunk, max_packets=n - received) # validate + split packets
            if len(pk):                                       # some new packets
                blocks.append(pk)                             # keep them
                received += len(pk)                           # count them
                if on_data is not None:                       # live display wants to know
                    _, _, codes = decode_packets(pk)          # decode just the new ones
                    on_data(received, codes)                  # hand them over
            if end_text is not None:                          # firmware stopped early
                break                                         # stop waiting for packets
        # ---- collect the END line --------------------------------------------
        rest = bytes(parser.buf) if end_text is None else end_text   # bytes after the last packet
        self._rx = bytearray(rest)                            # put them back as text input
        fw = {}                                               # parsed END counters
        line = None                                           # the END line text
        deadline = time.monotonic() + 3.0                     # it should follow immediately
        while time.monotonic() < deadline:                    # look for it
            line = self._read_line(deadline - time.monotonic())
            if line is None:                                  # nothing came
                break
            if line.startswith("END"):                        # found it
                fw = {k: v for k, v in (kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)}   # key=value
                break
        for k in list(fw):                                    # convert numeric values to int
            if re.fullmatch(r"-?\d+", fw[k]):                 # looks like an integer?
                fw[k] = int(fw[k])                            # convert
        block = np.concatenate(blocks) if blocks else np.zeros((0, PACKET_BYTES), np.uint8)   # all packets
        seq, status, codes = decode_packets(block)            # decode everything
        host = {
            "packets_received": int(received),                # what reached the PC intact
            "bad_packets": parser.bad_packets,                # corrupted packets (checksum)
            "skipped_bytes": parser.skipped_bytes,            # junk bytes between packets
            "end_line_seen": bool(fw),                        # did we get the END line?
            "wall_time_s": time.monotonic() - t_start,        # how long it took on the PC
        }
        return RawCapture(seq=seq, status=status, codes=codes, fw=fw, host=host)
