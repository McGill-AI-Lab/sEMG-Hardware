"""
==============================================================================
 experiments.py  —  every experiment of clamshell_validation.md, as code
==============================================================================

THE THREE OBJECTS
-----------------
CaptureSpec : a recipe for ONE capture (rate, which channels, gain, input
              MUX, test signal, aggressors, duration). The runner turns it
              into register values, sends them, and records the data.
Capture     : what came back: raw codes, sequence numbers, status words,
              firmware counters, register readback, plus integrity checks.
Experiment  : one section of the validation plan. It knows:
                - specs()    which captures it needs,
                - quick()    a one-line verdict shown live after each capture,
                - analyze()  the full analysis: tables, findings, figures.
              Experiments B, D and E capture nothing themselves: they
              re-analyse Experiment A's data (that is what the plan says).

DATA FLOW
---------
  test_plan.toml ──► Experiment.specs() ──► runner sends CFG + CAP ──► Capture
                                                                         │
  report.py  ◄── Result (tables, findings, figures) ◄── Experiment.analyze(ctx)

VERDICTS
--------
PASS / WARN / FAIL compare a number against a threshold in test_plan.toml.
INFO means "measured, nothing to compare against". SKIP means "not run".

PYTHON FEATURES YOU WILL SEE A LOT HERE
---------------------------------------
- @dataclass: writes __init__ for classes that mostly hold data.
- List comprehensions: [f(x) for x in items if cond] builds a list in one line.
- Dict/set comprehensions: {k: v for ...}, {x for ...}.
- Classes and inheritance: `class ShortedNoise(Experiment)` reuses everything
  the base class Experiment defines and overrides specs()/analyze().
- lambda: a tiny unnamed function, e.g. `lambda th: self._fig(th, rows)` is a
  function of one argument `th` that calls self._fig. We hand it to
  plots.save_both, which calls it once per colour theme.
==============================================================================
"""

from __future__ import annotations          # allow "list[int]"-style hints everywhere

import json                                 # save capture metadata as text
from dataclasses import asdict, dataclass, field   # dataclass helpers
from pathlib import Path                    # file paths that work on every OS

import numpy as np                          # arrays and statistics

from . import ads1298 as ads                # register encoding + unit conversion
from . import analysis as an                # the maths
from . import plots                         # chart styling and saving
from .analysis import FAIL, INFO, PASS, SKIP, WARN   # verdict words


# ===========================================================================
# Settings shared by all experiments ([suite] and [reference] in the TOML)
# ===========================================================================
@dataclass
class Suite:
    """
    Global settings. Field names match the keys of [suite] in test_plan.toml,
    so run_suite.py can build this object straight from the TOML table.
    `field(default_factory=...)` is needed for list/dict defaults: each Suite
    gets its own fresh list instead of all sharing one.
    """
    rates: list = field(default_factory=lambda: [500, 2000, 4000])     # data rates to iterate over
    channels: list = field(default_factory=lambda: list(range(1, 9)))  # channels visited by the "each" plan
    channel_plan: list = field(default_factory=lambda: ["each", "all"])  # "each" = one at a time, "all" = together
    capture_seconds: float = 10.0          # default capture length
    discard_frames: int = 32               # frames thrown away after START (filter settling)
    vref: float = 2.4                      # reference voltage in volts
    sclk_hz: int = 4000000                 # default SPI clock for frame reads
    mains_hz: float = 50.0                 # local mains frequency (50 Hz Europe, 60 Hz North America)
    expected_id: int = 0x92                # ADS1298 ID register value
    rate_tol_warn_pct: float = 1.0         # sample-rate error that triggers WARN
    rate_tol_fail_pct: float = 3.0         # sample-rate error that triggers FAIL
    reference_noise_uVrms: dict = field(default_factory=dict)   # datasheet table values, key "G6_500"

    def reference_rms(self, gain: int, rate: int) -> tuple[float | None, str]:
        """
        Expected input-referred noise (uVrms) for a gain and data rate, and
        where the number came from.

        1. If you typed a datasheet value into [reference] in test_plan.toml
           (key "G<gain>_<rate>"), use it.
        2. Otherwise, at gain 6 only, scale the datasheet front-page figure
           (4 uVpp in 150 Hz bandwidth at G = 6) by sqrt(bandwidth / 150 Hz)
           and divide by 6.6 to turn peak-to-peak into RMS. This is an
           ESTIMATE that assumes white noise; replace it with table values.
        3. Otherwise there is no reference (returns None).
        """
        key = f"G{gain}_{rate}"                                      # e.g. "G6_500"
        if key in self.reference_noise_uVrms:                        # user-supplied datasheet value?
            return float(self.reference_noise_uVrms[key]), "datasheet table (test_plan.toml)"
        if gain == 6:                                                # headline-based estimate
            return 4.0 / 6.6 * np.sqrt(ads.bandwidth_hz(rate) / 150.0), "estimate from 4 uVpp @150 Hz headline"
        return None, "no reference"                                  # nothing to compare against


def expand_channel_plan(plan: list, channels: list) -> list[tuple[str, list[int]]]:
    """
    Turn ["each", "all"] into concrete channel sets:
        "each" -> ("each", [1]), ("each", [2]), ... one per listed channel
        "all"  -> ("all",  [1, 2, ..., 8]) all listed channels together
    This is how the suite does "channel 1 through 8 one at a time, then all 8".
    """
    sets = []                                                        # result list
    for item in plan:                                                # in the order given in the TOML
        if item == "each":                                           # one channel at a time
            sets += [("each", [c]) for c in channels]                # one tuple per channel
        elif item == "all":                                          # all together
            sets.append(("all", list(channels)))                     # one tuple with every channel
        else:                                                        # a typo in the TOML
            raise ValueError(f"channel_plan entries must be 'each' or 'all', not {item!r}")
    return sets


# ===========================================================================
# CaptureSpec and Capture
# ===========================================================================
@dataclass
class CaptureSpec:
    """The recipe for one capture. Everything needed to reproduce it."""
    key: str                                 # unique name, also the file name, e.g. "A_r500_ch3"
    exp: str                                 # experiment letter
    title: str                               # human label, e.g. "500 SPS · CH3 · G6 · shorted"
    rate: int                                # samples per second
    channels: list                           # enabled channel numbers
    gains: list                              # 8 gains (index 0 = CH1)
    muxes: list                              # 8 MUX codes (index 0 = CH1)
    int_test: bool = False                   # internal test signal generator on?
    test_amp: int = 0                        # CONFIG2 TEST_AMP
    test_freq: int = ads.TEST_FREQ_FAST      # CONFIG2 TEST_FREQ
    seconds: float = 10.0                    # capture length
    discard: int = 32                        # settling frames to throw away
    sclk: int = 4000000                      # frame-read SPI clock
    buffered: bool = False                   # True = capture into ESP32 RAM, send afterwards
    wifi: str = "off"                        # off / ap / scan
    load: str = "idle"                       # idle / busy
    vref: float = 2.4                        # reference voltage (for scaling)
    prompt: str | None = None                # message to show and wait for Enter before this capture
    power_cycle_first: bool = False          # send RESET before configuring
    tags: dict = field(default_factory=dict) # extra labels used by the analysis (plan, variant, ...)

    def registers(self) -> list[int]:
        """The 12 CFG register values for this capture (see ads1298.build_registers)."""
        return ads.build_registers(self.rate, self.gains, self.muxes, self.channels,
                                   self.int_test, self.test_amp, self.test_freq)

    def n_frames(self) -> int:
        """How many frames to capture: seconds x rate, at least 1."""
        return max(1, int(round(self.seconds * self.rate)))


@dataclass
class Capture:
    """One finished capture: spec + data + checks."""
    spec: CaptureSpec                        # the recipe it came from
    seq: np.ndarray                          # (N,) DRDY numbers
    status: np.ndarray                       # (N,) 24-bit status words
    codes: np.ndarray                        # (N, 8) signed 24-bit codes
    fw: dict                                 # firmware END-line counters
    host: dict                               # PC-side counters
    written: list                            # register values sent
    readback: list                           # register values read back
    started: str = ""                        # timestamp text
    error: str | None = None                 # set if the capture failed
    integrity: dict = field(default_factory=dict)   # result of check_integrity()

    @property
    def valid(self) -> np.ndarray:
        """
        Boolean mask of frames whose status word starts with 1100 (datasheet
        "Data Output Protocol"). `>> 20` shifts the 24-bit word right so only
        its top 4 bits remain; 0xC is binary 1100. A @property is used like
        an attribute: cap.valid (no brackets).
        """
        return (self.status >> 20) == 0xC

    @property
    def fs(self) -> float:
        """Measured sample rate if available, else the nominal one."""
        return self.integrity.get("rate_measured") or float(self.spec.rate)

    def uV(self, ch: int) -> np.ndarray:
        """Input-referred microvolts of channel `ch`, valid frames only."""
        g = self.spec.gains[ch - 1]                                  # that channel's gain
        return ads.codes_to_uV(self.codes[self.valid, ch - 1].astype(float), g, self.spec.vref)   # select + scale

    # ---- saving / loading -------------------------------------------------
    def save(self, folder: Path):
        """
        Write <key>.npz (the arrays, compressed NumPy format) and <key>.json
        (everything else, human-readable). --reanalyze reads them back.
        """
        folder.mkdir(parents=True, exist_ok=True)                    # make the folder if needed
        np.savez_compressed(folder / f"{self.spec.key}.npz", seq=self.seq, status=self.status, codes=self.codes)
        meta = {"spec": asdict(self.spec), "fw": self.fw, "host": self.host, "written": self.written,
                "readback": self.readback, "started": self.started, "error": self.error,
                "integrity": self.integrity}                         # dataclass -> dict with asdict()
        (folder / f"{self.spec.key}.json").write_text(json.dumps(meta, indent=1, default=_json_default))

    @classmethod
    def load(cls, folder: Path, key: str) -> "Capture":
        """Read a capture saved by save(). @classmethod: called as Capture.load(...), returns a new Capture."""
        meta = json.loads((folder / f"{key}.json").read_text())      # the metadata
        arr = np.load(folder / f"{key}.npz")                         # the arrays
        return cls(spec=CaptureSpec(**meta["spec"]), seq=arr["seq"], status=arr["status"], codes=arr["codes"],
                   fw=meta["fw"], host=meta["host"], written=meta["written"], readback=meta["readback"],
                   started=meta.get("started", ""), error=meta.get("error"))


def _json_default(o):
    """json.dumps cannot write NumPy numbers/arrays by itself; convert them to plain Python."""
    if isinstance(o, np.integer):                                    # e.g. np.int64
        return int(o)
    if isinstance(o, np.floating):                                   # e.g. np.float64
        return float(o)
    if isinstance(o, np.ndarray):                                    # arrays -> lists
        return o.tolist()
    return str(o)                                                    # anything else as text


# ===========================================================================
# Integrity checks (clamshell_validation.md section 1), run on EVERY capture
# ===========================================================================
def check_integrity(cap: Capture, suite: Suite) -> dict:
    """
    Decide whether a capture's data can be trusted. Checks:
      - register readback equals what was written (ignoring read-only bits),
      - every requested frame arrived, none corrupted on the wire,
      - no conversions were missed (firmware counter AND gaps in seq),
      - every status word starts with 1100,
      - no "suspicious exact zeros" (the interleaved-zeros bug of the old sketch),
      - measured sample rate is close to nominal.
    Returns a dict with the verdict, human-readable messages and the counts.
    """
    s = cap.spec                                                     # shorthand
    msgs, verdicts = [], []                                          # findings and their verdicts
    n_exp = s.n_frames()                                             # frames requested
    n = len(cap.seq)                                                 # frames received
    if cap.error:                                                    # the capture itself failed
        return {"verdict": FAIL, "messages": [f"capture error: {cap.error}"], "frames": n, "frames_expected": n_exp}

    mism = ads.readback_mismatches(cap.written, cap.readback) if cap.readback else ["no readback"]
    if mism:                                                         # registers did not stick
        verdicts.append(FAIL)
        msgs.append("register readback mismatch: " + "; ".join(mism))

    if n < n_exp:                                                    # frames missing at the PC
        verdicts.append(FAIL)
        msgs.append(f"received {n} of {n_exp} frames")
    if cap.host.get("bad_packets", 0):                               # checksum failures on the wire
        verdicts.append(FAIL)
        msgs.append(f"{cap.host['bad_packets']} corrupted packets (checksum)")
    if cap.fw.get("timeouts", 0):                                    # DRDY stopped toggling
        verdicts.append(FAIL)
        msgs.append("DRDY timeout: conversions stopped (check DRDY wire, clock, PWDN)")

    gaps = np.diff(cap.seq.astype(np.int64)) if n > 1 else np.zeros(0, np.int64)   # seq steps (1 = no gap)
    missed_seq = int(np.sum(gaps[gaps > 1] - 1))                     # conversions skipped between packets
    missed_fw = int(cap.fw.get("missed", 0))                         # the firmware's own count
    missed = max(missed_seq, missed_fw)                              # trust the larger
    if missed:
        verdicts.append(FAIL)
        msgs.append(f"{missed} conversions missed (SPI/UART could not keep up)")

    bad_status = int(np.sum(~cap.valid))                             # frames without the 1100 prefix (~ = NOT)
    if bad_status:
        verdicts.append(FAIL)
        msgs.append(f"{bad_status} frames with an invalid status word (misaligned / zero frames)")

    zero_frames = int(np.sum((cap.status == 0) & np.all(cap.codes == 0, axis=1)))   # completely empty frames

    zero_flags = []                                                  # channels with suspicious zeros
    for ch in s.channels:                                            # only enabled channels carry data
        col = cap.codes[cap.valid, ch - 1]                           # that channel's valid codes
        if len(col) == 0:                                            # nothing to look at
            continue
        if len(col) < 3:                                             # need a left and right neighbour
            continue
        # A zero is only suspicious when BOTH neighbours are far from zero
        # (e.g. 5400, 0, 5400: the interleaved-zeros bug). A signal that
        # simply sits near zero (28, 3, 0, 14, -6) hits 0 now and then by
        # chance; looking at the whole-capture median would wrongly flag it
        # whenever the other half of a square wave is far from zero.
        prev, mid, nxt = col[:-2], col[1:-1], col[2:]                # each sample with its left and right neighbour
        susp = (mid == 0) & (np.abs(prev) > 50) & (np.abs(nxt) > 50) # zero surrounded by clearly non-zero values
        frac = float(np.mean(susp))                                  # fraction of samples that are suspicious zeros
        if frac > 0.01:                                              # more than 1 % -> the old bug is back
            zero_flags.append(f"CH{ch} {frac:.0%}")
    if zero_flags:
        verdicts.append(FAIL)
        msgs.append("suspicious exact-zero samples: " + ", ".join(zero_flags))

    rate = None                                                      # measured sample rate
    fu, lu = cap.fw.get("first_us"), cap.fw.get("last_us")           # DRDY times from the firmware (µs)
    fs_, ls_ = cap.fw.get("first_seq"), cap.fw.get("last_seq")       # matching DRDY numbers
    if all(isinstance(v, int) for v in (fu, lu, fs_, ls_)) and lu > fu and ls_ > fs_:
        rate = (ls_ - fs_) / ((lu - fu) / 1e6)                       # DRDY pulses per second, timed by the ESP32 crystal
    rate_err = (rate / s.rate - 1) * 100 if rate else None           # percent error vs nominal
    if rate_err is not None:
        if abs(rate_err) > suite.rate_tol_fail_pct:                  # far off
            verdicts.append(FAIL)
            msgs.append(f"sample rate {rate:.2f} SPS is {rate_err:+.2f} % off nominal")
        elif abs(rate_err) > suite.rate_tol_warn_pct:                # a bit off
            verdicts.append(WARN)
            msgs.append(f"sample rate {rate:.2f} SPS is {rate_err:+.2f} % off nominal")
    if cap.host.get("skipped_bytes", 0) > 64:                        # junk on the line (not fatal)
        verdicts.append(WARN)
        msgs.append(f"{cap.host['skipped_bytes']} stray bytes between packets")

    return {"verdict": an.worst(verdicts) if verdicts else PASS, "messages": msgs, "frames": n,
            "frames_expected": n_exp, "missed": missed, "bad_status": bad_status, "zero_frames": zero_frames,
            "bad_packets": int(cap.host.get("bad_packets", 0)), "rate_measured": rate, "rate_error_pct": rate_err,
            "readback_ok": not mism}


# ===========================================================================
# Results containers
# ===========================================================================
@dataclass
class Table:
    """A table for the report. `verdict_col` = index of the column holding PASS/WARN/FAIL (or None)."""
    title: str                    # heading above the table
    columns: list                 # column names
    rows: list                    # list of rows, each a list of cell values
    verdict_col: int | None = None   # which column to draw as verdict badges
    note: str = ""                # small explanatory text under the table


@dataclass
class Result:
    """Everything the report needs about one experiment."""
    id: str                       # letter
    name: str                     # title
    section: str                  # section of clamshell_validation.md
    goal: str                     # what it is for
    method: str                   # how it was measured
    verdict: str = SKIP           # overall verdict
    headline: str = ""            # one-line summary for the report tile
    findings: list = field(default_factory=list)       # list of (verdict, text)
    tables: list = field(default_factory=list)         # list of Table
    figures: list = field(default_factory=list)        # list of dict(title, light, dark, caption)
    log_rows: list = field(default_factory=list)       # rows for the section-13 results log


class Context:
    """Shared state during analysis: all captures, settings, figure folder, earlier results."""

    def __init__(self, suite: Suite, captures: dict, fig_dir: Path, device: dict):
        self.suite = suite                    # global settings
        self.captures = captures              # key -> Capture
        self.fig_dir = fig_dir                # where PNGs go
        self.device = device                  # ID, firmware info, register dump
        self.results: dict = {}               # experiment id -> Result

    def caps(self, exp_id: str) -> list[Capture]:
        """All successful captures of one experiment, in capture order."""
        return [c for c in self.captures.values() if c.spec.exp == exp_id and not c.error and len(c.seq)]


def fmt(v, digits=3, unit=""):
    """Format a number for tables with `digits` significant digits; '—' for missing values."""
    if v is None or (isinstance(v, float) and not np.isfinite(v)):  # None, NaN or infinity
        return "—"
    return f"{v:.{digits}g}{unit}" if abs(v) < 1e5 else f"{v:.3e}{unit}"   # "g" = compact, "e" = scientific


def ratio_verdict(ratio, warn, fail):
    """PASS if ratio <= warn, WARN if <= fail, else FAIL (None -> INFO)."""
    if ratio is None or not np.isfinite(ratio):                      # nothing to judge
        return INFO
    return PASS if ratio <= warn else WARN if ratio <= fail else FAIL   # chained conditional expression


# ===========================================================================
# Base class
# ===========================================================================
class Experiment:
    """
    Base class. A subclass sets the class attributes and overrides specs(),
    analyze() and optionally quick(). `self.cfg` is this experiment's table
    from test_plan.toml (a dict); `self.suite` the global settings.
    """
    id = "?"                     # letter used on the command line (--only A,G)
    name = ""                    # short title
    section = ""                 # section of clamshell_validation.md
    goal = ""                    # one or two sentences shown live and in the report
    method = ""                  # how it is measured
    requires: tuple = ()         # experiments whose captures this one analyses

    def __init__(self, cfg: dict, suite: Suite):
        self.cfg = cfg or {}                                         # [X] table from the TOML ({} if missing)
        self.suite = suite                                           # [suite] settings

    # ---- helpers for subclasses ----------------------------------------------
    @property
    def enabled(self) -> bool:
        """`enabled = true/false` in the TOML table; on by default."""
        return bool(self.cfg.get("enabled", True))

    def rates(self) -> list[int]:
        """This experiment's `rates`, or the suite's if not set."""
        return list(self.cfg.get("rates") or self.suite.rates)

    def channel_sets(self, default=None):
        """Channel sets from this experiment's `channel_plan` (or `default`, or the suite's)."""
        plan = self.cfg.get("channel_plan") or default or self.suite.channel_plan
        return expand_channel_plan(plan, self.cfg.get("channels") or self.suite.channels)

    def seconds(self) -> float:
        """This experiment's capture length, or the suite's."""
        return float(self.cfg.get("seconds", self.suite.capture_seconds))

    def base_spec(self, key, title, rate, channels, gain, mux, **kw) -> CaptureSpec:
        """
        A CaptureSpec with the same gain and MUX on every enabled channel.
        `**kw` collects any extra keyword arguments (seconds=..., wifi=...) and
        passes them on; setdefault fills in suite defaults for ones not given.
        """
        kw.setdefault("seconds", self.seconds())                     # default capture length
        kw.setdefault("discard", self.suite.discard_frames)          # default settling discard
        kw.setdefault("sclk", self.suite.sclk_hz)                    # default SPI clock
        kw.setdefault("vref", self.suite.vref)                       # reference voltage
        return CaptureSpec(key=key, exp=self.id, title=title, rate=rate, channels=list(channels),
                           gains=[gain] * 8, muxes=[mux] * 8, **kw)  # same gain/MUX in all 8 slots

    def new_result(self) -> Result:
        """An empty Result pre-filled with this experiment's descriptive fields."""
        return Result(self.id, self.name, self.section, self.goal, self.method)

    # ---- to override -------------------------------------------------------
    def specs(self) -> list[CaptureSpec]:
        """The captures this experiment needs (none by default)."""
        return []

    def quick(self, cap: Capture) -> tuple[str, str]:
        """
        Default live summary, shown right after each capture: the verdict is
        the data-integrity verdict (PASS = the data can be trusted), the text
        gives the median noise. Experiments with an expected value override
        this to judge the measurement itself.
        """
        st = [an.noise_stats(cap.uV(ch)) for ch in cap.spec.channels]   # statistics per enabled channel
        rms = np.median([s["rms_uV"] for s in st])                     # typical noise
        ppr = max(s["pp_rms"] for s in st)                             # worst peak-to-peak / rms
        return cap.integrity.get("verdict", INFO), f"data OK · median {rms:.3g} µVrms, max pp/rms {ppr:.1f}"

    def analyze(self, ctx: Context) -> Result:
        """The full analysis (nothing by default)."""
        return self.new_result()


def _plan_label(channels: list[int], plan: str) -> str:
    """'CH3' for a single channel, 'all 8' for the all-channel plan."""
    return f"CH{channels[0]}" if plan == "each" else f"all {len(channels)}"


def _set_key(prefix: str, rate: int, plan: str, chs: list[int]) -> str:
    """Capture key such as 'A_r500_ch3' or 'A_r500_all'."""
    return f"{prefix}_r{rate}_" + (f"ch{chs[0]}" if plan == "each" else "all")


# ===========================================================================
# P — prerequisites: make the data trustworthy (section 1)
# ===========================================================================
class Prereq(Experiment):
    id = "P"
    name = "Prerequisites & data integrity"
    section = "1"
    goal = ("Prove the data path is trustworthy before measuring noise: device ID, register readback, "
            "exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.")
    method = ("All channels on the internal test signal (far from zero, so a stuck or zeroed sample is obvious). "
              "One capture per data rate, then repeated PWDN power cycles with a fresh configuration each time.")

    def specs(self):
        """One test-signal capture per rate, then `power_cycles` short captures each preceded by RESET."""
        out = []                                                     # list of specs
        ch = self.cfg.get("channels") or self.suite.channels         # all listed channels
        for r in self.rates():                                       # one capture per rate
            out.append(self.base_spec(f"P_r{r}", f"{r} SPS · all {len(ch)} · test signal", r, ch, 6,
                                      ads.MUX_TEST, int_test=True, tags={"kind": "rate"}))
        r0 = self.rates()[0]                                         # power cycles at the first rate
        for i in range(int(self.cfg.get("power_cycles", 3))):        # repeated power cycles
            out.append(self.base_spec(f"P_cycle{i + 1}", f"power cycle {i + 1} · {r0} SPS", r0, ch, 6,
                                      ads.MUX_TEST, int_test=True, seconds=float(self.cfg.get("cycle_seconds", 2)),
                                      power_cycle_first=True, tags={"kind": "cycle", "n": i + 1}))
        return out

    def quick(self, cap):
        """Live line: frame counts, missed, bad status and measured rate."""
        i = cap.integrity                                            # integrity results
        rate = f"{i['rate_measured']:.2f} SPS" if i.get("rate_measured") else "rate n/a"
        return i["verdict"], (f"{i['frames']}/{i['frames_expected']} frames, missed {i.get('missed', 0)}, "
                              f"bad status {i.get('bad_status', 0)}, {rate}")

    def analyze(self, ctx):
        """ID check, a table of P's captures, and the integrity of every capture in the run."""
        res = self.new_result()                                      # empty result
        dev_id = ctx.device.get("id")                                # read once at the start of the run
        if dev_id is not None:                                       # (missing when re-analysing very old runs)
            ok = dev_id == self.suite.expected_id                    # right chip answering?
            res.findings.append((PASS if ok else FAIL,
                                 f"ID register = 0x{dev_id:02X} (expected 0x{self.suite.expected_id:02X})"))
        rows = []                                                    # P's own captures
        for c in ctx.caps("P"):
            i = c.integrity
            rows.append([c.spec.title, f"{i['frames']}/{i['frames_expected']}", i.get("missed", "—"),
                         i.get("bad_status", "—"), i.get("zero_frames", "—"),
                         fmt(i.get("rate_measured"), 6), fmt(i.get("rate_error_pct"), 2, " %"),
                         "yes" if i.get("readback_ok") else "NO", i["verdict"]])
        res.tables.append(Table("Integrity of the prerequisite captures",
                                ["Capture", "Frames", "Missed", "Bad status", "Zero frames", "Rate (SPS)",
                                 "Rate error", "Readback OK", "Verdict"], rows, verdict_col=8))
        all_rows, bad = [], 0                                        # integrity of EVERY capture of the run
        for c in ctx.captures.values():
            i = c.integrity or {"verdict": FAIL, "messages": ["not analysed"]}
            if i["verdict"] == FAIL:                                 # count untrustworthy captures
                bad += 1
            all_rows.append([c.spec.exp, c.spec.title, f"{i.get('frames', 0)}/{i.get('frames_expected', '?')}",
                             i.get("missed", "—"), i.get("bad_status", "—"), fmt(i.get("rate_error_pct"), 2, " %"),
                             "; ".join(i.get("messages", [])) or "—", i["verdict"]])
        res.tables.append(Table("Integrity of every capture in this run",
                                ["Exp", "Capture", "Frames", "Missed", "Bad status", "Rate error", "Problems",
                                 "Verdict"], all_rows, verdict_col=7,
                                note="A capture that fails here is still analysed, but its numbers are suspect."))
        for c in ctx.caps("P"):                                      # each problem of P's captures as a finding
            for m in c.integrity.get("messages", []):
                res.findings.append((c.integrity["verdict"], f"{c.spec.title}: {m}"))
        if bad:
            res.findings.append((FAIL, f"{bad} of {len(ctx.captures)} captures in this run failed integrity checks."))
        elif ctx.captures:
            res.findings.append((PASS, f"All {len(ctx.captures)} captures passed the integrity checks."))
        res.verdict = an.worst([v for v, _ in res.findings] + [r[-1] for r in rows])   # worst of everything
        n_ok = sum(1 for r in all_rows if r[-1] != FAIL)             # trustworthy captures
        res.headline = f"{n_ok}/{len(all_rows)} captures trustworthy"
        return res


# ===========================================================================
# A — shorted-input noise floor (section 2)
# ===========================================================================
class ShortedNoise(Experiment):
    id = "A"
    name = "Shorted-input noise floor"
    section = "2"
    goal = ("Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted "
            "inside the chip. Every other experiment is compared against this baseline.")
    method = ("CHnSET MUX = 001 (input shorted), internal 2.4 V reference, HR mode. Input-referred µVrms, µVpp, "
              "pp/rms and offset per channel, compared with the datasheet noise level.")

    def gain(self):
        """PGA gain used for this experiment."""
        return int(self.cfg.get("gain", 6))

    def specs(self):
        """For every rate and channel set (each CH1..CH8, then all 8): one shorted-input capture."""
        out = []
        for r in self.rates():                                       # every data rate ...
            for plan, chs in self.channel_sets():                    # ... every channel set
                out.append(self.base_spec(_set_key("A", r, plan, chs),
                                          f"{r} SPS · {_plan_label(chs, plan)} · G{self.gain()} · shorted", r, chs,
                                          self.gain(), ads.MUX_SHORTED, tags={"plan": plan}))
        return out

    def quick(self, cap):
        """Live verdict: worst channel's noise vs the expected level, and spikiness."""
        ref, _ = self.suite.reference_rms(self.gain(), cap.spec.rate)   # expected µVrms (or None)
        st = [an.noise_stats(cap.uV(ch)) for ch in cap.spec.channels]   # per-channel statistics
        rms = [s["rms_uV"] for s in st]                                 # noise of each channel
        warn, fail = float(self.cfg.get("warn_ratio", 1.5)), float(self.cfg.get("fail_ratio", 3.0))
        ratio = max(rms) / ref if ref else None                         # worst channel vs expected
        v = ratio_verdict(ratio, warn, fail)                            # PASS / WARN / FAIL / INFO
        if any(an.is_spiky(x, float(self.cfg.get("pp_rms_margin", 1.3))) for x in st) and v == PASS:
            v = WARN                                                    # spikes on some channel
        txt = f"median {np.median(rms):.3g} µVrms"                      # build the text
        if ratio:
            txt += f", worst {ratio:.2f}× expected"
        return v, txt + f", max pp/rms {max(x['pp_rms'] for x in st):.1f}"

    def channel_rows(self, ctx):
        """One dict per (capture, channel) with the noise statistics and verdict."""
        rows = []
        warn, fail = float(self.cfg.get("warn_ratio", 1.5)), float(self.cfg.get("fail_ratio", 3.0))
        margin = float(self.cfg.get("pp_rms_margin", 1.3))            # allowed excess over Gaussian pp/rms
        for c in ctx.caps("A"):                                       # every A capture
            ref, src = self.suite.reference_rms(self.gain(), c.spec.rate)   # expected level and its source
            for ch in c.spec.channels:                                # every enabled channel
                st = an.noise_stats(c.uV(ch))                         # offset, rms, pp, pp/rms
                ratio = st["rms_uV"] / ref if ref else None           # measured ÷ expected
                v = ratio_verdict(ratio, warn, fail)                  # judge the level
                if an.is_spiky(st, margin) and v == PASS:             # spikier than Gaussian noise would be
                    v = WARN
                if c.integrity.get("verdict") == FAIL:                # untrustworthy data
                    v = FAIL
                rows.append(dict(cap=c, rate=c.spec.rate, plan=c.spec.tags.get("plan"), ch=ch, ref=ref,
                                 ref_src=src, ratio=ratio, verdict=v, **st))   # **st merges the stats dict in
        return rows

    def analyze(self, ctx):
        """Noise table, alone-vs-all comparison, per-rate findings, ratio chart and results-log rows."""
        res = self.new_result()
        rows = self.channel_rows(ctx)                                 # all channel measurements
        if not rows:                                                  # no data at all
            res.headline = "no data"
            return res
        res.tables.append(Table(
            "Noise per channel (input-referred)",
            ["Rate", "Plan", "Ch", "Offset (µV)", "Noise (µVrms)", "Noise (µVpp)", "pp/rms", "Expected (µVrms)",
             "Measured ÷ expected", "Verdict"],
            [[r["rate"], r["plan"], r["ch"], fmt(r["offset_uV"]), fmt(r["rms_uV"]), fmt(r["pp_uV"]),
              fmt(r["pp_rms"], 2), fmt(r["ref"]), fmt(r["ratio"], 2), r["verdict"]] for r in rows],
            verdict_col=9, note="Expected value: " + rows[0]["ref_src"] + ". Thresholds: [A] warn_ratio / "
                                "fail_ratio / pp_rms_margin in test_plan.toml. pp/rms is compared with what pure "
                                "Gaussian noise gives for the same number of samples (≈6.4 at 1 500, ≈8.1 at 40 000)."))
        # ---- single channel vs all channels on --------------------------------------
        cmp_rows = []
        for r in sorted({x["rate"] for x in rows}):                   # each rate
            for ch in sorted({x["ch"] for x in rows}):                # each channel
                e = [x for x in rows if x["rate"] == r and x["ch"] == ch and x["plan"] == "each"]   # alone
                a = [x for x in rows if x["rate"] == r and x["ch"] == ch and x["plan"] == "all"]    # all on
                if e and a:                                           # both measured
                    q = a[0]["rms_uV"] / e[0]["rms_uV"]               # ratio all ÷ alone
                    cmp_rows.append([r, ch, fmt(e[0]["rms_uV"]), fmt(a[0]["rms_uV"]), fmt(q, 3),
                                     ratio_verdict(abs(q - 1) + 1, 1.2, 1.5)])   # 20 % / 50 % difference limits
        if cmp_rows:
            res.tables.append(Table("Does turning all channels on change the noise?",
                                    ["Rate", "Ch", "Alone (µVrms)", "All on (µVrms)", "All ÷ alone", "Verdict"],
                                    cmp_rows, verdict_col=5,
                                    note="Should be ~1.0. More than 20 % different points to shared supply/reference "
                                         "loading."))
        # ---- findings ----------------------------------------------------------------
        for r in sorted({x["rate"] for x in rows}):                   # one finding per rate
            sub = [x for x in rows if x["rate"] == r]                 # rows at that rate
            med = np.median([x["rms_uV"] for x in sub])               # typical noise
            ratios = [x["ratio"] for x in sub if x["ratio"]]          # ratios vs expected
            txt = f"{r} SPS: median {med:.3g} µVrms"
            if ratios:
                txt += f", {np.median(ratios):.2f}× expected (worst {max(ratios):.2f}×)"
            worst_ch = max(sub, key=lambda x: x["rms_uV"])            # noisiest channel
            if worst_ch["verdict"] in (WARN, FAIL):
                txt += f"; noisiest CH{worst_ch['ch']} at {worst_ch['rms_uV']:.3g} µVrms"
            res.findings.append((an.worst([x["verdict"] for x in sub]), txt))
        spiky = [x for x in rows if an.is_spiky(x, float(self.cfg.get("pp_rms_margin", 1.3)))]
        if spiky:
            res.findings.append((WARN, f"{len(spiky)} channel captures have a pp/rms well above what Gaussian noise "
                                       "gives: spikes or bursts, not pure random noise. See Experiment F (aggressors)."))
        res.verdict = an.worst([x["verdict"] for x in rows])          # overall verdict
        res.headline = "; ".join(t.split(",")[0] for _, t in res.findings[:3])   # "500 SPS: median ..." parts
        # ---- figure --------------------------------------------------------------------
        if any(x["ratio"] for x in rows):                             # only if there is an expected value
            res.figures.append(dict(title="Measured noise ÷ expected, per channel", caption=(
                "Each dot is one channel in one capture (filled = channel alone, ring = all channels on). "
                "1.0 means exactly the datasheet level; the dashed line is the WARN limit."),
                **plots.save_both(lambda th: self._fig_ratio(th, rows), ctx.fig_dir, "A_ratio")))
        for x in rows:                                                # rows for the section-13 results log
            res.log_rows.append(dict(exp="A", condition=f"shorted, {x['plan']}", gain=self.gain(),
                                     rate=f"HR {x['rate']}", ch=x["ch"], offset_uV=x["offset_uV"],
                                     rms_uV=x["rms_uV"], pp_uV=x["pp_uV"], pp_rms=x["pp_rms"], notes=x["verdict"]))
        return res

    def _fig_ratio(self, th, rows):
        """Dot chart: measured ÷ expected per channel, one colour per rate, filled = alone, ring = all on."""
        rates = sorted({x["rate"] for x in rows})                     # rates present
        fig, (ax,) = plots.new_figure(th, height=3.0)                 # one panel
        offsets = {r: (i - (len(rates) - 1) / 2) * 0.22 for i, r in enumerate(rates)}   # side-by-side per rate
        for r in rates:
            for plan, filled in (("each", True), ("all", False)):
                sub = [x for x in rows if x["rate"] == r and x["plan"] == plan and x["ratio"]]
                if not sub:
                    continue
                col = plots.rate_color(th, r)                         # fixed colour of this rate
                ax.scatter([x["ch"] + offsets[r] for x in sub], [x["ratio"] for x in sub], s=36,
                           color=col if filled else th.surface, edgecolors=col, linewidths=1.4, zorder=3,
                           label=f"{r} SPS" + ("" if filled else " (all on)"))
        ax.axhline(1.0, color=th.ink2, linewidth=1.0)                 # "exactly as expected"
        ax.axhline(float(self.cfg.get("warn_ratio", 1.5)), color=th.muted, linewidth=1.0, linestyle="--")   # WARN limit
        ax.set_xticks(range(1, 9), [f"CH{i}" for i in range(1, 9)])   # channel labels
        ax.set_ylabel("measured ÷ expected")
        ax.set_ylim(bottom=0)                                         # ratios start at 0
        plots.legend(ax, th, ncols=min(6, 2 * len(rates)), loc="upper center", bbox_to_anchor=(0.5, 1.18))
        return fig


# ===========================================================================
# B — noise spectrum (section 3)
# ===========================================================================
def source_caps(ctx: Context) -> dict:
    """
    For analyses that re-use Experiment A (B and D): per rate, A's
    all-channel capture if it exists, otherwise its single-channel captures.
    Returns {rate: [Capture, ...]}.
    """
    out = {}
    for c in ctx.caps("A"):                                           # every A capture
        r = c.spec.rate
        if c.spec.tags.get("plan") == "all":                          # an all-channel capture wins
            out[r] = [c]
        elif r not in out or out[r][0].spec.tags.get("plan") != "all":   # no all-channel one (yet)
            out.setdefault(r, []).append(c)                           # collect the single-channel ones
    return out


class Spectrum(Experiment):
    id = "B"
    name = "Noise spectrum (PSD)"
    section = "3"
    goal = "Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines."
    method = ("Welch PSD (Hann window, ≥ 8 averaged segments) of Experiment A's captures, shown as amplitude "
              "spectral density. Lines more than 10 dB above the local floor are listed with a likely cause.")
    requires = ("A",)

    def analyze(self, ctx):
        """Per channel: white floor, 1/f corner and spectral lines; findings about mains/other lines; ASD chart."""
        res = self.new_result()
        src = source_caps(ctx)                                        # A's data per rate
        if not src:
            res.findings.append((SKIP, "No Experiment A data."))
            return res
        thr = float(self.cfg.get("line_threshold_db", 10.0))          # line detection threshold
        rows, spectra = [], {}                                        # table rows, (rate, ch) -> (f, asd)
        for r, caps in sorted(src.items()):                           # each rate
            for c in caps:
                for ch in c.spec.channels:                            # each channel
                    f, asd = an.welch_asd(c.uV(ch), c.fs)             # spectrum
                    spectra[(r, ch)] = (f, asd)                       # keep for the chart
                    floor = an.white_floor(f, asd, c.fs)              # flat level
                    corner = an.one_over_f_corner(f, asd, floor)      # where 1/f noise takes over
                    lines = an.find_lines(f, asd, thr)                # narrow peaks
                    labels = [f"{l['f_hz']:.1f} Hz ({an.label_line(l['f_hz'], self.suite.mains_hz, c.fs)}, "
                              f"+{l['excess_db']:.0f} dB)" for l in lines[:4]]   # up to 4, with likely cause
                    rows.append([r, ch, fmt(floor * 1000, 3), fmt(corner, 2), "; ".join(labels) or "none",
                                 WARN if lines else PASS])
        res.tables.append(Table("Spectrum summary", ["Rate", "Ch", "White floor (nV/√Hz)", "1/f corner (Hz)",
                                                     "Spectral lines", "Verdict"], rows, verdict_col=5,
                                note=f"Lines = local maxima ≥ {thr:.0f} dB above a running-median floor. "
                                     "With the inputs shorted INSIDE the chip, any mains line must enter via the "
                                     "supply, ground or reference."))
        mains = [r for r in rows if "mains" in r[4]]                  # spectra containing a mains line
        if mains:
            res.findings.append((WARN, f"Mains lines on {len(mains)} channel spectra although the inputs are shorted "
                                       "internally: coupling via supply/ground/reference."))
        other = [r for r in rows if r[4] != "none" and "mains" not in r[4]]   # other lines
        if other:
            res.findings.append((WARN, f"Other spectral lines on {len(other)} channel spectra; check them against "
                                       "Experiments D (alias?) and F (aggressor?)."))
        if not mains and not other:
            res.findings.append((PASS, "No spectral lines above the threshold: the floor is clean."))
        res.verdict = an.worst([r[-1] for r in rows])
        floors = [float(r[2]) for r in rows if r[2] != "—"]           # numeric floors
        res.headline = (f"floor ≈ {np.median(floors):.0f} nV/√Hz, {len(mains) + len(other)} spectra with lines"
                        if floors else "")
        res.figures.append(dict(title="Amplitude spectral density, inputs shorted", caption=(
            "One panel per data rate, one line per channel. Flat = white noise; rising at the left = 1/f noise; "
            "spikes = interference lines."), **plots.save_both(lambda th: self._fig(th, spectra), ctx.fig_dir, "B_asd")))
        return res

    def _fig(self, th, spectra):
        """One log-log ASD panel per rate, one line per channel (fixed channel colours)."""
        rates = sorted({r for r, _ in spectra})                       # panels
        fig, axes = plots.new_figure(th, nrows=len(rates), height=2.4)
        for ax, r in zip(axes, rates):
            chans = sorted(ch for rr, ch in spectra if rr == r)       # channels at this rate
            for ch in chans:
                f, asd = spectra[(r, ch)]
                ax.loglog(f[1:], asd[1:] * 1000, color=plots.channel_color(th, ch), linewidth=0.9,
                          label=f"CH{ch}")                            # skip DC bin, µV -> nV
            ax.set_title(f"{r} SPS", loc="left")
            ax.set_ylabel("nV/√Hz")
            if len(chans) > 1 and ax is axes[0]:                      # one legend at the top
                plots.legend(ax, th, ncols=8, loc="upper center", bbox_to_anchor=(0.5, 1.32))
        axes[-1].set_xlabel("frequency (Hz)")
        return fig


# ===========================================================================
# C — gain sweep (section 4)
# ===========================================================================
class GainSweep(Experiment):
    id = "C"
    name = "Gain sweep (PGA vs ADC noise)"
    section = "4"
    goal = ("Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: "
            "the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.")
    method = "Shorted inputs at every gain; fit v_in² = e_PGA² + (e_ADC/G)² per channel."

    def gains(self):
        """Gains to sweep."""
        return [int(g) for g in self.cfg.get("gains", [1, 2, 3, 4, 6, 8, 12])]

    def specs(self):
        """For every rate and channel set (default: all channels together): one capture per gain."""
        out = []
        for r in self.rates():
            for plan, chs in self.channel_sets(default=["all"]):
                for g in self.gains():
                    out.append(self.base_spec(_set_key("C", r, plan, chs) + f"_g{g}",
                                              f"{r} SPS · {_plan_label(chs, plan)} · G{g} · shorted", r, chs, g,
                                              ads.MUX_SHORTED, tags={"plan": plan, "gain": g}))
        return out

    def analyze(self, ctx):
        """Noise vs gain table with the model fit, suggested gain, findings and chart."""
        res = self.new_result()
        data = {}                                          # (rate, ch) -> {gain: (rms_in µV, rms in LSB)}
        for c in ctx.caps("C"):
            g = c.spec.tags["gain"]                        # this capture's gain
            for ch in c.spec.channels:
                st = an.noise_stats(c.uV(ch))              # input-referred statistics
                lsb = st["rms_uV"] / ads.lsb_input_referred_uV(g, c.spec.vref)   # same noise in output codes
                data.setdefault((c.spec.rate, ch), {})[g] = (st["rms_uV"], lsb)
        rows, fits = [], {}
        gains = self.gains()
        for (r, ch), d in sorted(data.items()):            # each rate/channel
            gs = sorted(d)                                 # gains measured
            if len(gs) < 2:                                # cannot fit one point
                continue
            rms = [d[g][0] for g in gs]                    # input-referred noise per gain
            fit = an.fit_gain_model(gs, rms)               # e_PGA, e_ADC
            fits[(r, ch)] = (gs, rms, fit)                 # keep for the chart
            rec = next(g for g in gs if d[g][0] <= 1.2 * min(rms))   # lowest gain within 20 % of the floor
            falls = rms[0] / rms[-1]                       # lowest-gain ÷ highest-gain noise
            lsb = [d[g][1] for g in gs]                    # output-referred noise per gain
            rows.append([r, ch] + [fmt(d[g][0]) if g in d else "—" for g in gains] +
                        [fmt(fit["e_pga_uV"]), fmt(fit["e_adc_uV"]), f"G{rec}", fmt(max(lsb) / min(lsb), 3),
                         PASS if falls >= 1.3 else WARN])
        if not rows:
            res.findings.append((SKIP, "Not enough gain-sweep data."))
            return res
        res.tables.append(Table("Input-referred noise (µVrms) vs gain, and model fit",
                                ["Rate", "Ch"] + [f"G{g}" for g in gains] +
                                ["e_PGA (µV)", "e_ADC (µV)", "Suggested gain", "LSB-noise spread", "Verdict"],
                                rows, verdict_col=len(gains) + 6,
                                note="e_PGA: input-referred PGA noise (the high-gain floor). e_ADC: ADC + reference "
                                     "noise at the modulator input. Suggested gain: lowest gain within 20 % of the "
                                     "floor, which keeps the most headroom (±VREF/G) for electrode offset. "
                                     "LSB-noise spread ≈ 1 would mean noise after the PGA dominates."))
        for r in sorted({k[0] for k in fits}):             # one finding per rate
            e_p = np.median([fits[k][2]["e_pga_uV"] for k in fits if k[0] == r])
            e_a = np.median([fits[k][2]["e_adc_uV"] for k in fits if k[0] == r])
            recs = [row[-3] for row in rows if row[0] == r]   # suggested gains at this rate
            res.findings.append((INFO, f"{r} SPS: e_PGA ≈ {e_p:.3g} µVrms, e_ADC ≈ {e_a:.3g} µVrms; "
                                       f"suggested gain {max(set(recs), key=recs.count)}"))   # most common suggestion
        flat = [row for row in rows if row[-1] == WARN]
        if flat:
            res.findings.append((WARN, f"{len(flat)} channel sweeps barely fall with gain: noise enters at or before "
                                       "the PGA, or is common to all channels via the supply."))
        res.verdict = an.worst([row[-1] for row in rows])
        res.headline = res.findings[0][1]
        res.figures.append(dict(title="Input-referred noise vs gain", caption=(
            "Dots = measurement per channel, dashed = model fit of the channel median. The curve should fall "
            "and level off; where it levels off is the PGA noise floor."),
            **plots.save_both(lambda th: self._fig(th, fits), ctx.fig_dir, "C_gain")))
        for (r, ch), (gs, rms, _) in fits.items():         # results-log rows
            for g, v in zip(gs, rms):
                res.log_rows.append(dict(exp="C", condition="shorted, gain sweep", gain=g, rate=f"HR {r}", ch=ch,
                                         rms_uV=v, notes=""))
        return res

    def _fig(self, th, fits):
        """One panel per rate: dots per channel, dashed fit of the channel median."""
        rates = sorted({k[0] for k in fits})
        fig, axes = plots.new_figure(th, ncols=len(rates), width=7.6, height=3.0, sharey=True)
        for ax, r in zip(axes, rates):
            keys = sorted(k for k in fits if k[0] == r)    # channels at this rate
            for k in keys:
                gs, rms, _ = fits[k]
                ax.plot(gs, rms, "o", markersize=4.5, color=plots.channel_color(th, k[1]), label=f"CH{k[1]}")
            gs = fits[keys[0]][0]                          # gain list
            med = np.median([fits[k][1] for k in keys if fits[k][0] == gs], axis=0)   # channel median per gain
            fit = an.fit_gain_model(gs, med)
            gg = np.geomspace(min(gs), max(gs), 50)        # smooth curve points
            ax.plot(gg, np.sqrt(fit["e_pga_uV"] ** 2 + (fit["e_adc_uV"] / gg) ** 2), "--", color=th.ink2,
                    linewidth=1.2)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xticks(gs, [str(g) for g in gs])        # label the actual gains
            ax.minorticks_off()
            ax.set_title(f"{r} SPS", loc="left")
            ax.set_xlabel("PGA gain")
        axes[0].set_ylabel("µVrms (input-referred)")
        if len(fits) > 1:
            plots.legend(axes[-1], th, fontsize=7)
        return fig


# ===========================================================================
# D — data-rate sweep (section 5)
# ===========================================================================
class RateSweep(Experiment):
    id = "D"
    name = "Data-rate sweep"
    section = "5"
    goal = ("Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and "
            "separate real in-band lines (fixed frequency) from aliases (move when the rate changes).")
    method = "Re-uses Experiment A's captures at every data rate."
    requires = ("A",)

    def analyze(self, ctx):
        """RMS-vs-rate exponent and floor overlap per channel, fixed-vs-moving lines, overlay chart."""
        res = self.new_result()
        src = source_caps(ctx)                             # A's data per rate
        rates = sorted(src)
        if len(rates) < 2:
            res.findings.append((SKIP, "Needs Experiment A at two or more data rates."))
            return res
        thr = float(self.cfg.get("line_threshold_db", 10))
        per, mean_asd = {}, {}                             # ch -> {rate: (rms, floor, lines)}; rate -> (f, asd)
        for r in rates:
            asds = []                                      # spectra at this rate
            for c in src[r]:
                for ch in c.spec.channels:
                    x = c.uV(ch)
                    f, asd = an.welch_asd(x, c.fs)
                    asds.append((f, asd))
                    per.setdefault(ch, {})[r] = (an.noise_stats(x)["rms_uV"], an.white_floor(f, asd, c.fs),
                                                 an.find_lines(f, asd, thr))
            f0 = asds[0][0]                                # common frequency axis
            mean_asd[r] = (f0, np.sqrt(np.mean([np.interp(f0, f, a) ** 2 for f, a in asds], axis=0)))   # power average
        rows = []
        for ch, d in sorted(per.items()):
            rs = sorted(d)
            if len(rs) < 2:
                continue
            expo = an.rate_exponent(rs, [d[r][0] for r in rs])   # slope of log(rms) vs log(rate)
            floors = [d[r][1] for r in rs]
            spread = max(floors) / min(floors)             # do the µV/√Hz floors overlap?
            v = an.worst([PASS if 0.35 <= expo <= 0.65 else WARN if expo <= 0.8 else FAIL,
                          PASS if spread <= 1.3 else WARN])
            rows.append([ch] + [fmt(d[r][0]) if r in d else "—" for r in rates] + [fmt(expo, 2), fmt(spread, 3), v])
        res.tables.append(Table("Noise vs data rate", ["Ch"] + [f"{r} SPS (µVrms)" for r in rates] +
                                ["Exponent (0.5 = white)", "Floor spread (max÷min)", "Verdict"], rows,
                                verdict_col=len(rates) + 3,
                                note="Exponent = slope of log(rms) vs log(rate). > 0.65: noise rises faster than "
                                     "white, interference at high frequency. Floor spread compares the µV/√Hz "
                                     "floors, which should overlap between rates."))
        # ---- fixed vs moving lines ---------------------------------------------------
        all_lines = [(r, l["f_hz"]) for d in per.values() for r, (_, _, ls) in d.items() for l in ls]   # (rate, f)
        line_rows, seen = [], set()
        for r, fl in sorted(all_lines):
            if (r, round(fl)) in seen:                     # same line already listed for this rate
                continue
            seen.add((r, round(fl)))
            others = [rr for rr in rates if rr != r and any(r2 == rr and abs(f2 - fl) < 1.0 for r2, f2 in all_lines)]
            kind = "fixed → real in-band interference" if others else "only at this rate → possible alias"
            line_rows.append([r, f"{fl:.1f}", an.label_line(fl, self.suite.mains_hz, r), kind])
        if line_rows:
            res.tables.append(Table("Spectral lines across data rates",
                                    ["Rate", "Line (Hz)", "Likely cause", "Behaviour"], line_rows[:40]))
            if any("alias" in r[3] for r in line_rows):
                res.findings.append((WARN, "Some lines appear at one data rate only: likely aliases of interference "
                                           "above Nyquist (the sinc³ filter rejects only partially between its nulls)."))
        exps = [float(r[len(rates) + 1]) for r in rows if r[len(rates) + 1] != "—"]   # all exponents
        if exps:
            res.findings.insert(0, (an.worst([r[-1] for r in rows]),
                                    f"RMS grows with rate^{np.median(exps):.2f} (white noise = 0.50)."))
        res.verdict = an.worst([r[-1] for r in rows] + [v for v, _ in res.findings])
        res.headline = res.findings[0][1] if res.findings else ""
        res.figures.append(dict(title="Channel-averaged spectrum at each data rate", caption=(
            "If the noise is white, the curves overlap on their common frequency range. A line present in only "
            "one curve is an alias."), **plots.save_both(lambda th: self._fig(th, mean_asd), ctx.fig_dir, "D_rates")))
        return res

    def _fig(self, th, mean_asd):
        """Overlay of channel-averaged ASD, one colour per rate."""
        fig, (ax,) = plots.new_figure(th, height=3.2)
        for r, (f, a) in sorted(mean_asd.items()):
            ax.loglog(f[1:], a[1:] * 1000, color=plots.rate_color(th, r), linewidth=1.3, label=f"{r} SPS")
        ax.set_xlabel("frequency (Hz)")
        ax.set_ylabel("nV/√Hz")
        plots.legend(ax, th)
        return fig


# ===========================================================================
# E — multichannel correlation (section 6)
# ===========================================================================
class Correlation(Experiment):
    id = "E"
    name = "Multichannel correlation"
    section = "6"
    goal = ("Separate noise that belongs to each channel from noise that all channels share (reference, supply, "
            "ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.")
    method = ("Experiment A's all-channel capture, high-pass filtered at 1 Hz: Pearson correlation matrix, RMS of "
              "the channel average vs σ/√N, and the mean coherence spectrum over all channel pairs.")
    requires = ("A",)

    def analyze(self, ctx):
        """Correlation summary per rate, verdict on max |r|, heatmap chart."""
        res = self.new_result()
        caps = [c for c in ctx.caps("A") if c.spec.tags.get("plan") == "all" and len(c.spec.channels) > 1]
        if not caps:
            res.findings.append((SKIP, "Needs an Experiment A capture with channel_plan 'all'."))
            return res
        warn_cfg, fail = float(self.cfg.get("warn_abs_r", 0.05)), float(self.cfg.get("fail_abs_r", 0.2))
        rows, mats = [], {}
        for c in caps:
            n = min(len(c.uV(ch)) for ch in c.spec.channels)           # common length of all channels
            X = np.column_stack([c.uV(ch)[:n] for ch in c.spec.channels])   # (n, channels) matrix
            # Two independent noise records still show |r| ~ 1/sqrt(n) by pure chance, and the
            # largest of 28 pairs reaches ~3-4 times that. So never warn below 4/sqrt(n).
            warn = max(warn_cfg, 4 / np.sqrt(n))
            s = an.correlation_summary(X, c.fs, float(self.cfg.get("highpass_hz", 1.0)))   # high-pass, then correlate
            mats[c.spec.rate] = (c.spec.channels, s)                   # keep for the chart
            v = PASS if s["max_abs_r"] < warn else WARN if s["max_abs_r"] < fail else FAIL
            peak = ""                                                  # frequencies with high coherence
            if s["coh"] is not None:
                hi = s["f"][s["coh"] > 0.5]
                peak = ", ".join(f"{x:.1f}" for x in hi[:6]) if len(hi) else "none"
            rows.append([c.spec.rate, fmt(s["max_abs_r"], 2), fmt(s["avg_ratio"], 3),
                         fmt(np.sqrt(len(c.spec.channels)), 3), peak, v])
        res.tables.append(Table("Correlation between channels", ["Rate", "Max |r|", "RMS(avg) ÷ (σ/√N)",
                                                                 "Fully shared would be", "Coherence > 0.5 at (Hz)",
                                                                 "Verdict"], rows, verdict_col=5,
                                note=f"|r| < {warn_cfg} (or 4/√samples for short captures): independent, the ideal "
                                     "case. RMS(avg) ÷ (σ/√N) ≈ 1 confirms independence; ≈ √N means the noise is "
                                     "shared. Data are high-pass filtered at highpass_hz first."))
        for row in rows:
            res.findings.append((row[-1], f"{row[0]} SPS: max |r| = {row[1]}, channel-average ratio {row[2]} "
                                          f"(1 = independent, {row[3]} = fully shared)"))
        res.verdict = an.worst([r[-1] for r in rows])
        res.headline = res.findings[0][1]
        res.figures.append(dict(title="Correlation matrices", caption=(
            "Blue = negative, grey = none, red = positive correlation. Off-diagonal cells should be grey."),
            **plots.save_both(lambda th: self._fig(th, mats), ctx.fig_dir, "E_corr")))
        return res

    def _fig(self, th, mats):
        """One correlation heatmap per rate, colour scale fixed to [-1, 1]."""
        rates = sorted(mats)
        fig, axes = plots.new_figure(th, ncols=len(rates), width=2.6 * len(rates) + 0.8, height=2.7)
        im = None
        for ax, r in zip(axes, rates):
            chans, s = mats[r]
            m = s["corr"].copy()
            np.fill_diagonal(m, np.nan)                               # hide the trivial diagonal (r = 1)
            im = ax.imshow(m, vmin=-1, vmax=1, cmap=plots.diverging_cmap(th))
            ax.set_xticks(range(len(chans)), [str(c) for c in chans])
            ax.set_yticks(range(len(chans)), [str(c) for c in chans])
            ax.grid(False)
            ax.set_title(f"{r} SPS", loc="left")
            ax.set_xlabel("channel")
        cb = fig.colorbar(im, ax=axes, shrink=0.85)                    # shared colour bar
        cb.ax.tick_params(colors=th.muted, labelsize=8)
        cb.outline.set_visible(False)
        return fig


# ===========================================================================
# F — aggressor toggling (section 7)
# ===========================================================================
class Aggressors(Experiment):
    id = "F"
    name = "Aggressor toggling (ESP32, USB, SPI)"
    section = "7"
    goal = "Find which system activity couples into the ADC by changing one thing at a time against a baseline."
    method = ("All channels shorted; each variant changes one of SPI clock, CPU load, WiFi mode, or USB activity "
              "(buffering in RAM). The first variant is the baseline.")

    def variants(self):
        """The list of variants from the TOML (each a dict)."""
        return list(self.cfg.get("variants") or [{"name": "baseline"}])

    def specs(self):
        """One shorted capture per (rate, variant), skipping SPI clocks too slow for the rate."""
        out = []
        chs = self.cfg.get("channels") or self.suite.channels
        g = int(self.cfg.get("gain", 6))
        for r in self.rates():
            for i, var in enumerate(self.variants()):
                sclk = int(var.get("sclk", self.suite.sclk_hz))
                if sclk < 216 * r * 1.5:                             # 216-bit frame must fit in a sample period
                    continue                                         # (with 50 % margin) -> skip this combination
                out.append(self.base_spec(
                    f"F_r{r}_v{i}", f"{r} SPS · {var['name']}", r, chs, g, ads.MUX_SHORTED, sclk=sclk,
                    wifi=var.get("wifi", "off"), load=var.get("load", "idle"),
                    buffered=bool(var.get("buffered", False)),
                    seconds=float(var.get("seconds", self.seconds())), prompt=var.get("prompt"),
                    tags={"variant": var["name"], "vi": i}))
        return out

    def analyze(self, ctx):
        """Per rate, compare every variant with the first (baseline): noise change, spikiness, new lines."""
        res = self.new_result()
        caps = ctx.caps("F")
        if not caps:
            res.findings.append((SKIP, "No captures."))
            return res
        warn, fail = float(self.cfg.get("warn_increase_pct", 20)), float(self.cfg.get("fail_increase_pct", 50))
        margin = float(self.cfg.get("pp_rms_margin", 1.3))
        rows, bars = [], {}                                           # table rows; rate -> [(variant, % change)]
        for r in sorted({c.spec.rate for c in caps}):
            sub = sorted([c for c in caps if c.spec.rate == r], key=lambda c: c.spec.tags["vi"])   # in TOML order
            base = None                                               # (rms, lines) of the baseline
            for c in sub:
                st = [an.noise_stats(c.uV(ch)) for ch in c.spec.channels]
                rms = float(np.mean([s["rms_uV"] for s in st]))       # mean noise over channels
                ppr = float(max(s["pp_rms"] for s in st))             # worst pp/rms
                spiky = any(an.is_spiky(s, margin) for s in st)
                f, asd = an.welch_asd(c.uV(c.spec.channels[0]), c.fs)
                lines = {round(l["f_hz"]) for l in an.find_lines(f, asd)}   # line frequencies (rounded)
                if base is None:                                      # first variant = baseline
                    base = (rms, lines)
                inc = (rms / base[0] - 1) * 100                       # % change vs baseline
                new = sorted(lines - base[1])                         # lines not in the baseline
                v = PASS if inc <= warn else WARN if inc <= fail else FAIL
                if spiky and v == PASS:
                    v = WARN
                if c.integrity.get("missed"):                         # lost samples under this aggressor
                    v = an.worst([v, WARN])
                rows.append([r, c.spec.tags["variant"], fmt(rms), f"{inc:+.1f} %", fmt(ppr, 2),
                             ", ".join(f"{x} Hz" for x in new[:5]) or "none", c.integrity.get("missed", 0), v])
                bars.setdefault(r, []).append((c.spec.tags["variant"], inc))
                for ch, s in zip(c.spec.channels, st):                # results-log rows
                    res.log_rows.append(dict(exp="F", condition=c.spec.tags["variant"], gain=c.spec.gains[0],
                                             rate=f"HR {r}", ch=ch, offset_uV=s["offset_uV"], rms_uV=s["rms_uV"],
                                             pp_uV=s["pp_uV"], pp_rms=s["pp_rms"], notes=v))
        res.tables.append(Table("Noise under each aggressor", ["Rate", "Variant", "Mean noise (µVrms)",
                                                               "Change vs baseline", "Max pp/rms",
                                                               "New lines (CH1)", "Missed frames", "Verdict"],
                                rows, verdict_col=7,
                                note=f"WARN above +{warn:.0f} %, FAIL above +{fail:.0f} % (test_plan.toml [F]). "
                                     "Variants whose SPI clock is too slow for the data rate are skipped."))
        for row in rows:
            if row[-1] in (WARN, FAIL):
                res.findings.append((row[-1], f"{row[0]} SPS, {row[1]}: noise {row[3]}, pp/rms {row[4]}"
                                              + (f", new lines {row[5]}" if row[5] != "none" else "")))
        if not res.findings:
            res.findings.append((PASS, "No aggressor changed the noise beyond the thresholds."))
        res.verdict = an.worst([r[-1] for r in rows])
        res.headline = f"{sum(r[-1] != PASS for r in rows)} of {len(rows)} variants affect the noise"
        res.figures.append(dict(title="Noise change vs baseline", caption=(
            "Mean input-referred noise of all channels, relative to the first variant at the same rate. "
            "The dashed line is the WARN limit."),
            **plots.save_both(lambda th: self._fig(th, bars, warn), ctx.fig_dir, "F_aggr")))
        return res

    def _fig(self, th, bars, warn):
        """Horizontal bars: % noise change per variant, grouped by rate (rate colour)."""
        rates = sorted(bars)
        n_bars = sum(len(bars[r]) for r in rates)
        fig, (ax,) = plots.new_figure(th, height=0.32 * n_bars + 1.0)
        y, ticks = 0, []                                              # bar position, (position, label)
        for r in rates:
            for n, inc in bars[r]:
                ax.barh(y, inc, height=0.7, color=plots.rate_color(th, r), edgecolor=th.surface, linewidth=1)
                ticks.append((y, f"{n} · {r}"))
                y += 1
            y += 0.6                                                  # gap between rate groups
        ax.set_yticks([t for t, _ in ticks], [l for _, l in ticks], fontsize=8)
        ax.invert_yaxis()                                             # first variant at the top
        ax.axvline(0, color=th.base, linewidth=1)                     # zero change
        ax.axvline(warn, color=th.muted, linewidth=1, linestyle="--")  # WARN limit
        ax.set_xlabel("noise change vs baseline (%)")
        return fig


# ===========================================================================
# G — internal test signal (section 8)
# ===========================================================================
class TestSignal(Experiment):
    id = "G"
    name = "Internal test signal"
    section = "8"
    goal = ("Check gain, scaling, offset, timing and reference noise with the chip's own square wave. "
            "Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.")
    method = ("MUX = 101 (test signal), INT_TEST = 1. Square wave: amplitude, midpoint, plateau noise, period. "
              "Gain cross-check: input-referred amplitude must not depend on gain. DC levels at both amplitudes: "
              "plateau noise vs shorted noise reveals reference noise.")

    def gain(self):
        """PGA gain for the main square-wave captures."""
        return int(self.cfg.get("gain", 6))

    def expected_amp_mV(self, amp):
        """Expected high-minus-low amplitude in mV for TEST_AMP = amp (override in the TOML if needed)."""
        key = "expected_amplitude_mV" if amp == 0 else "expected_amplitude_mV_amp1"
        default = 2 * ads.test_signal_half_amplitude_mV(amp, self.suite.vref)   # twice the ± amplitude
        return float(self.cfg.get(key, default))

    def specs(self):
        """Square wave per rate and channel set; gain cross-check at the first rate; DC levels per rate."""
        out = []
        f_test = ads.test_signal_frequency(ads.TEST_FREQ_FAST)        # ~1.953 Hz
        sec = max(self.seconds(), float(self.cfg.get("periods", 20)) / f_test + 0.5)   # long enough for N periods
        amp = int(self.cfg.get("test_amp", 0))
        for r in self.rates():
            for plan, chs in self.channel_sets():
                out.append(self.base_spec(_set_key("G", r, plan, chs),
                                          f"{r} SPS · {_plan_label(chs, plan)} · G{self.gain()} · test 2 Hz", r, chs,
                                          self.gain(), ads.MUX_TEST, int_test=True, test_amp=amp, seconds=sec,
                                          tags={"kind": "square", "plan": plan, "amp": amp}))
        chs = self.cfg.get("channels") or self.suite.channels
        r0 = self.rates()[0]
        for g in self.cfg.get("gain_check", [1, 2, 4, 6, 12]):        # same signal at several gains
            out.append(self.base_spec(f"G_gaincheck_g{g}", f"{r0} SPS · all · G{g} · test 2 Hz", r0, chs, int(g),
                                      ads.MUX_TEST, int_test=True, test_amp=amp, seconds=sec,
                                      tags={"kind": "gaincheck", "gain": int(g), "amp": amp}))
        if self.cfg.get("dc_levels", True):                           # DC test level at both amplitudes
            for r in self.rates():
                for a in (0, 1):
                    out.append(self.base_spec(f"G_r{r}_dc_amp{a}", f"{r} SPS · all · G{self.gain()} · DC amp{a}", r,
                                              chs, self.gain(), ads.MUX_TEST, int_test=True, test_amp=a,
                                              test_freq=ads.TEST_FREQ_DC, tags={"kind": "dc", "amp": a}))
        return out

    def quick(self, cap):
        """Live verdict on the first channel's square-wave amplitude (DC captures: default summary)."""
        if cap.spec.tags.get("kind") == "dc":
            return super().quick(cap)                                 # super() = the base-class version
        st = an.square_wave_stats(cap.uV(cap.spec.channels[0]), cap.fs)
        if st is None:
            return WARN, "no square wave found"
        exp = self.expected_amp_mV(cap.spec.tags.get("amp", 0))       # expected high-minus-low, mV
        err = (st["amplitude_uV"] / 1000 / exp - 1) * 100             # percent error
        tw, tf = float(self.cfg.get("amp_warn_pct", 5)), float(self.cfg.get("amp_fail_pct", 15))
        v = PASS if abs(err) <= tw else WARN if abs(err) <= tf else FAIL   # judge the amplitude
        return v, (f"CH{cap.spec.channels[0]}: {st['amplitude_uV'] / 1000:.3f} mV (expect {exp:.3f}, {err:+.1f} %), "
                   f"period {st['period_s'] * 1000:.1f} ms")

    def analyze(self, ctx):
        """Square-wave table, 1/G diagnosis, gain cross-check, reference-noise table, charts."""
        res = self.new_result()
        caps = ctx.caps("G")
        tol_w, tol_f = float(self.cfg.get("amp_warn_pct", 5)), float(self.cfg.get("amp_fail_pct", 15))
        per_w, per_f = float(self.cfg.get("period_warn_pct", 1)), float(self.cfg.get("period_fail_pct", 3))
        f_test = ads.test_signal_frequency(ads.TEST_FREQ_FAST)
        rows, example = [], None                                      # table rows; (capture, ch) to plot
        for c in [c for c in caps if c.spec.tags.get("kind") == "square"]:
            exp = self.expected_amp_mV(c.spec.tags["amp"])
            for ch in c.spec.channels:
                st = an.square_wave_stats(c.uV(ch), c.fs)
                if st is None:                                        # no square wave at all
                    rows.append([c.spec.rate, c.spec.tags["plan"], ch] + ["—"] * 7 + [FAIL])
                    continue
                amp = st["amplitude_uV"] / 1000                       # mV
                err = (amp / exp - 1) * 100                           # amplitude error %
                per_err = (st["period_s"] * f_test - 1) * 100         # period error %
                jit = st["period_jitter_s"] * c.fs                    # period jitter in samples
                v = an.worst([PASS if abs(err) <= tol_w else WARN if abs(err) <= tol_f else FAIL,
                              PASS if abs(per_err) <= per_w else WARN if abs(per_err) <= per_f else FAIL,
                              PASS if jit < 1 else WARN])
                if c.integrity.get("verdict") == FAIL:
                    v = FAIL
                rows.append([c.spec.rate, c.spec.tags["plan"], ch, f"{amp:.4f}", f"{exp:.3f}", f"{err:+.1f} %",
                             fmt(st["midpoint_uV"]), fmt((st["std_high_uV"] + st["std_low_uV"]) / 2),
                             f"{st['period_s'] * 1000:.2f}", fmt(jit, 2), v])
                if example is None or (c.spec.tags["plan"] == "all" and example[0].spec.tags["plan"] != "all"):
                    example = (c, ch)                                 # prefer an all-channel capture for the chart
                res.log_rows.append(dict(exp="G", condition=f"test 2 Hz, {c.spec.tags['plan']}", gain=self.gain(),
                                         rate=f"HR {c.spec.rate}", ch=ch, offset_uV=st["midpoint_uV"],
                                         rms_uV=(st["std_high_uV"] + st["std_low_uV"]) / 2,
                                         notes=f"amplitude {amp:.4f} mV ({err:+.1f} %)"))
        if rows:
            res.tables.append(Table("Square-wave measurements", [
                "Rate", "Plan", "Ch", "Amplitude (mV)", "Expected (mV)", "Error", "Midpoint (µV)",
                "Plateau noise (µVrms)", "Period (ms)", "Period jitter (samples)", "Verdict"], rows, verdict_col=10,
                note=f"Expected period {1000 / f_test:.1f} ms (f_CLK/2²⁰). The test-signal amplitude is not a "
                     "precision reference: treat a few % as normal (clamshell_validation.md, section 8)."))
            amps = [float(r[3]) for r in rows if r[3] != "—"]
            exp0 = self.expected_amp_mV(int(self.cfg.get("test_amp", 0)))
            med = np.median(amps) if amps else float("nan")           # typical measured amplitude
            msg = f"median amplitude {med:.4f} mV vs {exp0:.3f} mV expected ({(med / exp0 - 1) * 100:+.1f} %)"
            for g in (2, 3, 4, 6, 8, 12):                             # explain a gain-shaped error
                if abs(med * g / exp0 - 1) < 0.08:                    # within 8 % of exactly 1/g
                    msg += f" — almost exactly 1/{g} of expected: the PGA gain and the scaling do not match"
                    break
            res.findings.append((an.worst([r[-1] for r in rows]), msg))
        # ---- gain cross-check ----------------------------------------------------------------
        gc = sorted([c for c in caps if c.spec.tags.get("kind") == "gaincheck"], key=lambda c: c.spec.tags["gain"])
        gc_pts = []                                                   # (gain, median amplitude mV)
        for c in gc:
            stats = [an.square_wave_stats(c.uV(ch), c.fs) for ch in c.spec.channels]
            amps = [s["amplitude_uV"] / 1000 for s in stats if s]
            if amps:
                gc_pts.append((c.spec.tags["gain"], float(np.median(amps))))
        if len(gc_pts) >= 2:
            gs, am = zip(*gc_pts)                                     # unzip into two tuples
            spread = max(am) / min(am)                                # 1.00 = independent of gain
            slope = an.rate_exponent(gs, am)                          # log-log slope vs gain (-1 = falls as 1/G)
            v = PASS if spread <= 1.05 else WARN if spread <= 1.15 else FAIL
            txt = f"amplitude spread across gains {spread:.3f}× (1.00 ideal); log-log slope vs gain {slope:+.2f}"
            if slope < -0.8:
                txt += (" — amplitude falls as 1/G: the PGA gain is not applied to the signal, or codeToVolts "
                        "divides by a gain the channel is not set to")
            res.findings.append((v, "Gain cross-check: " + txt))
            res.tables.append(Table("Gain cross-check (input-referred amplitude must not depend on gain)",
                                    ["Gain", "Median amplitude (mV)"], [[g, f"{a:.4f}"] for g, a in gc_pts]))
            res.figures.append(dict(title="Gain cross-check", caption=(
                "Input-referred test-signal amplitude at each PGA gain. A flat line is correct; a line falling as "
                "1/G reproduces the 'amplitude ≈ 1/6' problem."),
                **plots.save_both(lambda th: self._fig_gain(th, gc_pts), ctx.fig_dir, "G_gaincheck")))
        # ---- DC levels: reference noise -------------------------------------------------------
        dc_rows = []
        short = {c.spec.rate: c for c in ctx.caps("A") if c.spec.tags.get("plan") == "all"}   # shorted baseline
        for c in sorted([c for c in caps if c.spec.tags.get("kind") == "dc"],
                        key=lambda c: (c.spec.rate, c.spec.tags["amp"])):
            sig = np.mean([an.noise_stats(c.uV(ch))["rms_uV"] for ch in c.spec.channels])   # noise on the DC level
            ref = None
            if c.spec.rate in short:                                  # shorted noise at the same rate
                sc = short[c.spec.rate]
                ref = np.mean([an.noise_stats(sc.uV(ch))["rms_uV"] for ch in c.spec.channels if ch in sc.spec.channels])
            excess = np.sqrt(max(0.0, sig ** 2 - ref ** 2)) if ref else None   # RSS difference
            dc_rows.append([c.spec.rate, c.spec.tags["amp"], fmt(sig), fmt(ref), fmt(excess),
                            ratio_verdict(sig / ref, 1.2, 2.0) if ref else INFO])
        if dc_rows:
            res.tables.append(Table("Reference noise: noise on a DC test level vs shorted noise",
                                    ["Rate", "TEST_AMP", "Noise on DC level (µVrms)", "Shorted noise (µVrms)",
                                     "Excess (µVrms)", "Verdict"], dc_rows, verdict_col=5,
                                    note="Reference noise scales with the signal and vanishes at 0 V, so it shows up "
                                         "only here. Growing with TEST_AMP = reference noise: improve VREFP decoupling."))
            bad = [r for r in dc_rows if r[-1] in (WARN, FAIL)]
            res.findings.append((an.worst([r[-1] for r in dc_rows]),
                                 "Noise on DC test levels is close to the shorted noise: reference noise negligible."
                                 if not bad else f"Noise on DC test levels exceeds shorted noise in {len(bad)} cases: "
                                                 "reference noise."))
        if example:                                                   # waveform chart first
            res.figures.insert(0, dict(title="Test signal, example channel", caption=(
                f"{example[0].spec.title}, CH{example[1]}: the first ~2.5 periods."),
                **plots.save_both(lambda th: self._fig_wave(th, *example), ctx.fig_dir, "G_wave")))
        res.verdict = an.worst([v for v, _ in res.findings]) if res.findings else SKIP
        res.headline = res.findings[0][1].split(" — ")[0] if res.findings else ""
        return res

    def _fig_wave(self, th, cap, ch):
        """About 2.5 periods of the square wave on one channel."""
        x = cap.uV(ch) / 1000                                         # mV
        n = int(2.5 / ads.test_signal_frequency(ads.TEST_FREQ_FAST) * cap.fs)   # samples in 2.5 periods
        t = np.arange(min(n, len(x))) / cap.fs * 1000                 # time axis, ms
        fig, (ax,) = plots.new_figure(th, height=2.6)
        ax.plot(t, x[:len(t)], color=plots.channel_color(th, ch), linewidth=1.4)
        ax.set_xlabel("time (ms)")
        ax.set_ylabel("mV (input-referred)")
        return fig

    def _fig_gain(self, th, pts):
        """Measured amplitude vs gain, with the expected value as a dashed line."""
        gs, am = zip(*pts)
        exp = self.expected_amp_mV(int(self.cfg.get("test_amp", 0)))
        fig, (ax,) = plots.new_figure(th, height=2.6)
        ax.plot(gs, am, "o-", color=th.series[0], linewidth=1.4, markersize=6)
        ax.axhline(exp, color=th.muted, linestyle="--", linewidth=1)  # expected amplitude
        ax.set_xscale("log")
        ax.set_xticks(gs, [str(g) for g in gs])
        ax.minorticks_off()
        ax.set_xlabel("PGA gain")
        ax.set_ylabel("amplitude (mV)")
        ax.set_ylim(0, max(max(am), exp) * 1.25)                     # headroom above the data and the expected line
        return fig


# ===========================================================================
# H — supply measurement (section 9)
# ===========================================================================
class Supply(Experiment):
    id = "H"
    name = "Supply measurement (MVDD)"
    section = "9"
    goal = "Measure the ADS1298's own supply rails and their ripple using the chip itself."
    method = ("MUX = 011 (MVDD), gain 1. Channels 1, 2, 5–8 measure (AVDD + AVSS)/2; channels 3 and 4 measure "
              "DVDD/4. Repeated under each listed variant (e.g. WiFi transmitting).")

    def expected_V(self, ch):
        """Expected reading in volts for channel `ch` (from avdd/avss/dvdd in the TOML)."""
        avdd, avss = float(self.cfg.get("avdd", 3.3)), float(self.cfg.get("avss", 0.0))
        dvdd = float(self.cfg.get("dvdd", 3.3))
        return dvdd / 4 if ch in (3, 4) else (avdd + avss) / 2

    def specs(self):
        """One MVDD capture per variant, at the experiment's rates (default: the first suite rate)."""
        out = []
        chs = self.cfg.get("channels") or self.suite.channels
        for r in self.rates() if self.cfg.get("rates") else [self.suite.rates[0]]:
            for i, var in enumerate(self.cfg.get("variants") or [{"name": "default"}]):
                out.append(self.base_spec(f"H_r{r}_v{i}", f"{r} SPS · MVDD · {var['name']}", r, chs, 1, ads.MUX_MVDD,
                                          wifi=var.get("wifi", "off"), load=var.get("load", "idle"),
                                          prompt=var.get("prompt"), tags={"variant": var["name"], "vi": i}))
        return out

    def quick(self, cap):
        """Live verdict on the worst rail error."""
        m = [np.mean(cap.uV(ch)) / 1e6 for ch in cap.spec.channels]       # mean volts per channel
        errs = [abs(v / self.expected_V(c) - 1) * 100 for c, v in zip(cap.spec.channels, m)]   # % errors
        tw, tf = float(self.cfg.get("warn_pct", 3)), float(self.cfg.get("fail_pct", 10))
        v = PASS if max(errs) <= tw else WARN if max(errs) <= tf else FAIL  # judge the worst rail
        return v, "rails: " + ", ".join(f"CH{c} {x:.3f} V" for c, x in zip(cap.spec.channels, m))

    def analyze(self, ctx):
        """Rail table (mean, error, ripple, ripple lines), per-variant findings, ripple spectrum chart."""
        res = self.new_result()
        tw, tf = float(self.cfg.get("warn_pct", 3)), float(self.cfg.get("fail_pct", 10))
        rows, spectra = [], {}
        for c in ctx.caps("H"):
            for ch in c.spec.channels:
                x = c.uV(ch)                                          # µV
                mean_v = float(np.mean(x)) / 1e6                      # V
                exp = self.expected_V(ch)
                err = (mean_v / exp - 1) * 100
                ripple = float(np.std(x))                             # µVrms
                f, asd = an.welch_asd(x, c.fs)
                lines = an.find_lines(f, asd)
                if ch == c.spec.channels[0]:                          # chart uses the first channel
                    spectra[c.spec.tags["variant"]] = (f, asd)
                v = PASS if abs(err) <= tw else WARN if abs(err) <= tf else FAIL
                what = "DVDD/4" if ch in (3, 4) else "(AVDD+AVSS)/2"
                rows.append([c.spec.rate, c.spec.tags["variant"], ch, what, f"{mean_v:.4f}", f"{exp:.4f}",
                             f"{err:+.2f} %", fmt(ripple), ", ".join(f"{l['f_hz']:.1f} Hz" for l in lines[:3]) or "none",
                             v])
                res.log_rows.append(dict(exp="H", condition=f"MVDD {c.spec.tags['variant']}", gain=1,
                                         rate=f"HR {c.spec.rate}", ch=ch, offset_uV=mean_v * 1e6, rms_uV=ripple,
                                         notes=f"{what} {err:+.2f} %"))
        if not rows:
            res.findings.append((SKIP, "No captures."))
            return res
        res.tables.append(Table("Supply rails", ["Rate", "Variant", "Ch", "Measures", "Mean (V)", "Expected (V)",
                                                 "Error", "Ripple (µVrms)", "Ripple lines", "Verdict"], rows,
                                verdict_col=9, note="Expected values from avdd/avss/dvdd in test_plan.toml [H]. "
                                                    "Lines that also appear in Experiment B point to the supply as "
                                                    "the coupling path."))
        for var in dict.fromkeys(r[1] for r in rows):                 # each variant, in order, once
            sub = [r for r in rows if r[1] == var]
            a = [r for r in sub if r[3].startswith("(")]              # analog rail channels
            d = [r for r in sub if r[3] == "DVDD/4"]                  # digital rail channels
            txt = f"{var}: "
            if a:
                txt += f"(AVDD+AVSS)/2 = {np.mean([float(r[4]) for r in a]):.3f} V"
            if d:
                txt += f", DVDD/4 = {np.mean([float(r[4]) for r in d]):.3f} V"
            txt += f", ripple ≈ {np.median([float(r[7]) for r in sub]):.3g} µVrms"
            res.findings.append((an.worst([r[-1] for r in sub]), txt))
        res.verdict = an.worst([r[-1] for r in rows])
        res.headline = res.findings[0][1]
        if spectra:
            res.figures.append(dict(title="Supply ripple spectrum (first channel)", caption=(
                "Ripple on the measured rail under each variant."),
                **plots.save_both(lambda th: self._fig(th, spectra), ctx.fig_dir, "H_ripple")))
        return res

    def _fig(self, th, spectra):
        """Ripple ASD per variant."""
        fig, (ax,) = plots.new_figure(th, height=2.8)
        for i, (name, (f, asd)) in enumerate(spectra.items()):
            ax.loglog(f[1:], asd[1:], color=th.series[i % 8], linewidth=1.2, label=name)
        ax.set_xlabel("frequency (Hz)")
        ax.set_ylabel("µV/√Hz")
        if len(spectra) > 1:
            plots.legend(ax, th)
        return fig


# ===========================================================================
# I — temperature and long-term drift (section 10)
# ===========================================================================
class Drift(Experiment):
    id = "I"
    name = "Temperature & long-term drift"
    section = "10"
    goal = "See how offset and noise change during warm-up and over minutes; find the longest useful averaging time."
    method = ("One channel on the temperature sensor (MUX = 100, gain 1), the others shorted. Offset per second "
              "vs temperature, and the Allan deviation of each shorted channel.")

    def specs(self):
        """One long capture: temperature channel at gain 1, the rest shorted."""
        r = int(self.cfg.get("rate", 500))
        tch = int(self.cfg.get("temp_channel", 1))
        chs = sorted(set(self.cfg.get("channels") or self.suite.channels) | {tch})   # always include the temp channel
        spec = self.base_spec("I_drift", f"{r} SPS · CH{tch} temperature + shorted · "
                                         f"{float(self.cfg.get('duration_s', 120)):.0f} s",
                              r, chs, int(self.cfg.get("gain", 6)), ads.MUX_SHORTED,
                              seconds=float(self.cfg.get("duration_s", 120)), tags={"temp_channel": tch})
        spec.gains[tch - 1] = 1                                      # ~145 mV sensor needs the ±2.4 V range of gain 1
        spec.muxes[tch - 1] = ads.MUX_TEMP                           # temperature sensor input
        return [spec]

    @staticmethod
    def temperature_C(v_uV):
        """Datasheet "Temperature Sensor": T = (V(µV) − 145 300) / 490 + 25. @staticmethod: needs no self."""
        return (v_uV - 145300.0) / 490.0 + 25.0

    def quick(self, cap):
        """Live line: mean temperature."""
        t = self.temperature_C(np.mean(cap.uV(cap.spec.tags["temp_channel"])))
        return INFO, f"temperature ≈ {t:.2f} °C"

    def analyze(self, ctx):
        """Temperature trace, offset drift per channel (µV/°C), Allan deviation, two charts."""
        res = self.new_result()
        caps = ctx.caps("I")
        if not caps:
            res.findings.append((SKIP, "No capture."))
            return res
        c = caps[0]
        tch = c.spec.tags["temp_channel"]
        fs = c.fs
        blk = max(1, int(round(fs)))                                  # one-second blocks
        temp = self.temperature_C(an.block_means(c.uV(tch), blk))     # °C per second
        t_s = np.arange(len(temp))                                    # time axis, s
        tv = PASS if 10 <= np.median(temp) <= 70 else WARN            # plausibility check
        res.findings.append((tv, f"temperature {temp[0]:.2f} → {temp[-1]:.2f} °C over {len(temp)} s "
                                 f"(range {temp.min():.2f}–{temp.max():.2f} °C)"))
        rows, offs, adevs = [], {}, {}
        for ch in [x for x in c.spec.channels if x != tch]:           # shorted channels
            x = c.uV(ch)
            o = an.block_means(x, blk)                                # offset per second
            offs[ch] = o
            n = min(len(o), len(temp))
            drift = None
            if np.ptp(temp[:n]) >= float(self.cfg.get("min_temp_span_C", 0.5)):   # enough temperature change?
                drift = float(np.polyfit(temp[:n], o[:n], 1)[0])       # slope = µV per °C
            taus, ad = an.allan_deviation(x, fs)
            adevs[ch] = (taus, ad)
            k = int(np.argmin(ad)) if len(ad) else 0                  # index of the minimum
            rows.append([ch, fmt(o[0]), fmt(o[-1]), fmt(o[-1] - o[0]), fmt(drift, 3),
                         fmt(ad[k] if len(ad) else None), fmt(taus[k] if len(ad) else None, 3), INFO])
        res.tables.append(Table("Offset drift and Allan deviation", [
            "Ch", "Offset start (µV)", "Offset end (µV)", "Change (µV)", "Drift (µV/°C)", "Min Allan dev. (µV)",
            "at τ (s)", "Verdict"], rows, verdict_col=7,
            note="Drift is fitted only when the temperature changes by at least min_temp_span_C. Allan deviation: "
                 "slope −½ = white noise (averaging helps), flat = flicker, rising = drift. Its minimum is the "
                 "longest useful averaging time. Compare drift with the datasheet 'Offset drift'."))
        taus_min = [float(r[6]) for r in rows if r[6] != "—"]
        if taus_min:
            res.findings.append((INFO, f"longest useful averaging time ≈ {np.median(taus_min):.3g} s "
                                       "(median over channels)"))
        res.verdict = an.worst([v for v, _ in res.findings])
        res.headline = res.findings[0][1]
        res.figures.append(dict(title="Temperature and offset over time", caption=(
            "Top: die temperature from the on-chip sensor. Bottom: per-channel offset change from its first second."),
            **plots.save_both(lambda th: self._fig_time(th, t_s, temp, offs), ctx.fig_dir, "I_time")))
        res.figures.append(dict(title="Allan deviation", caption="Shorted channels. Dashed: slope −½ reference.",
                                **plots.save_both(lambda th: self._fig_adev(th, adevs), ctx.fig_dir, "I_adev")))
        return res

    def _fig_time(self, th, t, temp, offs):
        """Two stacked panels sharing the time axis: temperature, offset change per channel."""
        fig, (a1, a2) = plots.new_figure(th, nrows=2, height=2.0, sharex=True)
        a1.plot(t, temp, color=th.series[3], linewidth=1.4)
        a1.set_ylabel("°C")
        for ch, o in offs.items():
            a2.plot(np.arange(len(o)), o - o[0], color=plots.channel_color(th, ch), linewidth=1.1, label=f"CH{ch}")
        a2.set_ylabel("Δ offset (µV)")
        a2.set_xlabel("time (s)")
        if len(offs) > 1:
            plots.legend(a2, th, ncols=7, fontsize=7)
        return fig

    def _fig_adev(self, th, adevs):
        """Allan deviation per channel with a slope −½ reference line."""
        fig, (ax,) = plots.new_figure(th, height=2.8)
        for ch, (t, a) in adevs.items():
            ax.loglog(t, a, color=plots.channel_color(th, ch), linewidth=1.2, label=f"CH{ch}")
        t0, a0 = next(iter(adevs.values()))                           # any channel, for the reference line
        if len(t0):
            ax.loglog(t0, a0[0] * np.sqrt(t0[0] / t0), "--", color=th.muted, linewidth=1)
        ax.set_xlabel("averaging time τ (s)")
        ax.set_ylabel("Allan deviation (µV)")
        if len(adevs) > 1:
            plots.legend(ax, th, ncols=4, fontsize=7)
        return fig


# ===========================================================================
# J — shorting at the connector (section 11)
# ===========================================================================
class Connector(Experiment):
    id = "J"
    name = "Shorting at the connector (front end)"
    section = "11"
    goal = "Measure the noise added by YOUR front end (RC filters, protection resistors, connector, traces)."
    method = ("MUX = 000 (normal input) with IN+ and IN− shorted together at the electrode connector and tied to the "
              "bias/RLD reference. Compared with Experiment A and with the resistors' thermal noise.")

    def specs(self):
        """One all-channel capture per rate; the first one waits for you to do the wiring."""
        out = []
        chs = self.cfg.get("channels") or self.suite.channels
        g = int(self.cfg.get("gain", 6))
        prompt = self.cfg.get("prompt", "Short IN+ to IN- of every channel at the connector, tie them to the "
                                        "bias/RLD reference, then press Enter.")
        for i, r in enumerate(self.rates()):
            out.append(self.base_spec(f"J_r{r}", f"{r} SPS · all · G{g} · shorted at connector", r, chs, g,
                                      ads.MUX_NORMAL, prompt=prompt if i == 0 else None, tags={"plan": "all"}))
        return out

    def analyze(self, ctx):
        """Front-end excess noise vs internal short and vs resistor thermal noise; mains presence."""
        res = self.new_result()
        caps = ctx.caps("J")
        if not caps:
            res.findings.append((SKIP, "No captures (J needs manual wiring and is off by default)."))
            return res
        r_ohm = float(self.cfg.get("series_resistance_ohm", 10000))
        factor = float(self.cfg.get("excess_factor", 2.0))
        internal = {c.spec.rate: c for c in ctx.caps("A") if c.spec.tags.get("plan") == "all"}   # A baseline
        rows = []
        for c in caps:
            jn = np.sqrt(2) * an.johnson_noise_uV(r_ohm, ads.bandwidth_hz(c.spec.rate))   # two resistors, RSS
            base = internal.get(c.spec.rate)
            for ch in c.spec.channels:
                st = an.noise_stats(c.uV(ch))
                v_int = an.noise_stats(base.uV(ch))["rms_uV"] if base and ch in base.spec.channels else None
                fe = np.sqrt(max(0.0, st["rms_uV"] ** 2 - v_int ** 2)) if v_int else None   # front-end excess
                f, asd = an.welch_asd(c.uV(ch), c.fs)
                mains = [l for l in an.find_lines(f, asd)
                         if "mains" in an.label_line(l["f_hz"], self.suite.mains_hz, c.fs)]
                v = INFO if fe is None else PASS if fe <= factor * jn else WARN
                if mains:
                    v = an.worst([v, WARN])
                rows.append([c.spec.rate, ch, fmt(st["rms_uV"]), fmt(v_int), fmt(fe), fmt(jn),
                             "yes" if mains else "no", v])
                res.log_rows.append(dict(exp="J", condition="shorted at connector", gain=c.spec.gains[0],
                                         rate=f"HR {c.spec.rate}", ch=ch, offset_uV=st["offset_uV"],
                                         rms_uV=st["rms_uV"], pp_uV=st["pp_uV"], pp_rms=st["pp_rms"], notes=v))
        res.tables.append(Table("Front-end noise", ["Rate", "Ch", "At connector (µVrms)", "Internal short (µVrms)",
                                                    "Front-end excess (µVrms)", "Resistor thermal (µVrms)",
                                                    "Mains present", "Verdict"], rows, verdict_col=7,
                                note=f"Excess = √(connector² − internal²). Thermal noise of two {r_ohm:.0f} Ω "
                                     f"resistors over the −3 dB bandwidth. WARN above {factor}× thermal, or if mains "
                                     "appears (coupling into the input wiring; RLD loop and CMRR deal with it)."))
        res.verdict = an.worst([r[-1] for r in rows])
        fe_vals = [float(r[4]) for r in rows if r[4] != "—"]
        res.findings.append((res.verdict, f"median front-end excess {np.median(fe_vals):.3g} µVrms" if fe_vals
                             else "no internal-short baseline to compare with (run A with the 'all' plan)"))
        res.headline = res.findings[0][1]
        return res


# ===========================================================================
# Registry: the order here is the order of capture and of the report
# ===========================================================================
ALL_EXPERIMENTS = [Prereq, ShortedNoise, Spectrum, GainSweep, RateSweep, Correlation, Aggressors, TestSignal,
                   Supply, Drift, Connector]
