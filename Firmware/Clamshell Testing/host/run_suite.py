#!/usr/bin/env python3
"""
==============================================================================
 run_suite.py  —  THE file you run. Runs every enabled experiment, shows it
                  live, and writes the final report.
==============================================================================

USAGE (from the host/ folder)
-----------------------------
    python run_suite.py                     everything enabled in test_plan.toml
    python run_suite.py --list              print the plan and time estimate only
    python run_suite.py --only A,G          just these experiments (dependencies added)
    python run_suite.py --skip F,I          everything except these
    python run_suite.py --rates 500,4000    override the data rates
    python run_suite.py --channels 1,3 --plan each
    python run_suite.py --seconds 3         shorter captures
    python run_suite.py --quick             fast smoke test (3 s captures, short drift run)
    python run_suite.py --simulate          no hardware: the built-in simulator
    python run_suite.py --simulate faulty   simulator with deliberate faults
    python run_suite.py --reanalyze ../runs/2026-11-15_143000
                                            redo analysis + report from saved data
    python run_suite.py --no-live           terminal only, no window

WHAT HAPPENS, IN ORDER
----------------------
  1. Read test_plan.toml, apply command-line overrides.
  2. Build the experiment objects and ask each one for its CaptureSpecs.
  3. Print the plan with a time estimate.
  4. Open the board (or simulator), check the ADS1298 ID.
  5. For every spec: (wait for you if it needs a manual step) → set aggressors
     → CFG (write + verify registers) → CAP (stream frames) → integrity check
     → quick verdict → save raw data to runs/<run>/captures/.
  6. Analyse every experiment, draw figures, write report.html, summary.md,
     results_log.csv and results.json into the run folder.
  7. Open the report in your browser.

Ctrl+C during the captures stops early; everything captured so far is still
analysed and reported.
==============================================================================
"""

from __future__ import annotations

import argparse                                     # command-line options
import json                                         # save/load the resolved plan and device info
import os                                           # environment variable for the live-window test snapshot
import shutil                                       # copy the plan file into the run folder
import sys                                          # sys.exit, sys.path, stdout redirection for the console log
import time                                         # timing
import tomllib                                      # read TOML files (built into Python >= 3.11)
import traceback                                    # print full errors if an experiment's analysis crashes
import webbrowser                                   # open the report at the end
from datetime import datetime                       # timestamps for the run-folder name
from pathlib import Path                            # file paths

import numpy as np                                  # empty arrays for failed captures

HERE = Path(__file__).resolve().parent              # the host/ folder, whatever the current directory is
sys.path.insert(0, str(HERE))                       # make "import clamshell" work from anywhere

from clamshell.analysis import FAIL, INFO, WARN, worst   # noqa: E402  (imports after the sys.path change)
from clamshell.device import Board, DeviceError, find_port   # noqa: E402
from clamshell.experiments import ALL_EXPERIMENTS, Capture, Context, Suite, check_integrity   # noqa: E402
from clamshell.live import ConsoleProgress, LiveDashboard   # noqa: E402
from clamshell.report import write_all              # noqa: E402


# ===========================================================================
# Command line
# ===========================================================================
def parse_args():
    """
    Define and read the command-line options (library: argparse).
    `action="store_true"` makes a flag that is False unless given.
    `nargs="?"` with `const` lets "--simulate" be used alone (= "clean") or
    with a value ("--simulate faulty").
    """
    p = argparse.ArgumentParser(description="ADS1298 clamshell validation suite")
    p.add_argument("--plan-file", default=str(HERE / "test_plan.toml"), help="test plan (TOML)")
    p.add_argument("--only", help="comma-separated experiment letters to run, e.g. A,G")
    p.add_argument("--skip", help="comma-separated experiment letters to leave out")
    p.add_argument("--rates", help="comma-separated data rates, e.g. 500,2000")
    p.add_argument("--channels", help="comma-separated channel numbers, e.g. 1,2,3")
    p.add_argument("--plan", help="channel plan: each, all, or each,all")
    p.add_argument("--seconds", type=float, help="capture length in seconds")
    p.add_argument("--quick", action="store_true", help="fast smoke test")
    p.add_argument("--port", help="serial port (overrides test_plan.toml)")
    p.add_argument("--simulate", nargs="?", const="clean", choices=["clean", "faulty"],
                   help="use the simulator instead of hardware")
    p.add_argument("--sim-speed", type=float, default=5.0, help="simulator speed vs real time")
    p.add_argument("--reanalyze", metavar="RUN_DIR", help="analyse a previous run's saved data again")
    p.add_argument("--list", action="store_true", help="print the plan and exit")
    p.add_argument("--no-live", action="store_true", help="no live window")
    p.add_argument("--no-open", action="store_true", help="do not open the report in a browser")
    p.add_argument("--force", action="store_true", help="continue even if the device ID is wrong")
    return p.parse_args()


def csv_list(text, cast=int):
    """'1, 2,3' -> [1, 2, 3] (or strings with cast=str)."""
    return [cast(x.strip()) for x in text.split(",") if x.strip()]


# ===========================================================================
# Plan → Suite + experiments → capture list
# ===========================================================================
def apply_overrides(plan: dict, args) -> dict:
    """
    Apply command-line options to the plan dictionary. A command-line
    override wins over BOTH [suite] and the per-experiment settings, so
    '--rates 500' really means "only 500 SPS everywhere".
    """
    suite = plan.setdefault("suite", {})                         # the [suite] table (created if missing)
    exp_tables = [plan.setdefault(cls.id, {}) for cls in ALL_EXPERIMENTS]   # every experiment table
    if args.rates:                                               # --rates
        suite["rates"] = csv_list(args.rates)
        for t in exp_tables:
            t.pop("rates", None)                                 # remove per-experiment overrides
    if args.channels:                                            # --channels
        suite["channels"] = csv_list(args.channels)
        for t in exp_tables:
            t.pop("channels", None)
    if args.plan:                                                # --plan
        suite["channel_plan"] = csv_list(args.plan, str)
        for t in exp_tables:
            t.pop("channel_plan", None)
    if args.seconds:                                             # --seconds
        suite["capture_seconds"] = args.seconds
        for t in exp_tables:
            t.pop("seconds", None)
    if args.quick:                                               # small, fast versions of everything
        suite["capture_seconds"] = min(float(suite.get("capture_seconds", 10)), 3.0)
        plan["G"]["periods"] = 6                                 # 6 periods of the test signal
        plan["I"]["duration_s"] = 20                             # 20 s drift run
        plan["P"]["power_cycles"] = 1                            # one power cycle
    if args.port:                                                # --port
        suite["port"] = args.port
    return plan


def build_suite(plan: dict) -> Suite:
    """Create the Suite settings object from [suite] and [reference]."""
    s = plan.get("suite", {})                                    # the [suite] table
    known = Suite.__dataclass_fields__                           # field names the Suite class has
    suite = Suite(**{k: v for k, v in s.items() if k in known})  # pass only fields it knows (port, baud are not)
    suite.reference_noise_uVrms = dict(plan.get("reference", {}).get("noise_uVrms", {}))   # datasheet values
    return suite


def build_experiments(plan: dict, suite: Suite, args) -> list:
    """
    Instantiate experiments, keep the enabled/selected ones, and add the
    ones they depend on (B, D and E need A's captures).
    """
    exps = {cls.id: cls(plan.get(cls.id, {}), suite) for cls in ALL_EXPERIMENTS}   # one object per letter
    if args.only:                                                # explicit selection beats "enabled"
        chosen = {x.strip().upper() for x in args.only.split(",")}
    else:                                                        # otherwise: what the TOML enables
        chosen = {k for k, e in exps.items() if e.enabled}
    if args.skip:                                                # --skip removes letters
        chosen -= {x.strip().upper() for x in args.skip.split(",")}
    unknown = chosen - set(exps)                                 # typos like --only Z
    if unknown:
        sys.exit(f"Unknown experiment letter(s): {', '.join(sorted(unknown))}. Valid: {', '.join(exps)}")
    for k in list(chosen):                                       # add dependencies
        for dep in exps[k].requires:
            if dep not in chosen:
                print(f"  note: {k} analyses {dep}'s data, so {dep}'s captures are added")
                chosen.add(dep)
    return [e for k, e in exps.items() if k in chosen]          # keep the registry order


def collect_specs(exps: list) -> list:
    """All CaptureSpecs of the selected experiments, in order, with unique keys."""
    specs, seen = [], set()                                      # result, keys already used
    for e in exps:
        for s in e.specs():
            if s.key not in seen:                                # guard against duplicates
                seen.add(s.key)
                specs.append(s)
    return specs


def print_plan(specs: list, exps: list):
    """Show how many captures each experiment needs and roughly how long it takes."""
    print("\nPlan")
    print("────")
    total = 0.0                                                  # total seconds
    for e in exps:
        mine = [s for s in specs if s.exp == e.id]               # this experiment's captures
        secs = sum(s.seconds + s.discard / s.rate + 0.6 for s in mine)   # capture + settling + ~0.6 s overhead
        total += secs
        what = f"{len(mine):>3} captures, ~{secs / 60:4.1f} min" if mine else "analysis of earlier data"
        manual = " (has manual steps)" if any(s.prompt for s in mine) else ""
        print(f"  {e.id}  {e.name:<42} {what}{manual}")
    print(f"  {'':2} {'TOTAL':<42} {len(specs):>3} captures, ~{total / 60:4.1f} min\n")


# ===========================================================================
# Hardware / simulator
# ===========================================================================
def open_board(args, suite_cfg: dict) -> tuple[Board, str]:
    """Open the simulator or the real serial port. Returns (board, description)."""
    if args.simulate:                                            # no hardware
        board = Board.open_simulator(args.simulate, args.sim_speed)
        return board, f"simulator ({args.simulate}, {args.sim_speed:g}× speed)"
    port = suite_cfg.get("port", "auto")                         # from the TOML (or --port)
    if port == "auto":
        port = find_port()                                       # guess the USB-UART device
    baud = int(suite_cfg.get("baud", 2000000))
    print(f"Opening {port} at {baud} baud …")
    return Board.open_serial(port, baud), f"hardware on {port}"


def run_captures(board: Board, specs: list, exps: dict, suite: Suite, cap_dir: Path,
                 console: ConsoleProgress, live: LiveDashboard) -> dict:
    """
    The capture loop: one CaptureSpec after another.
    Returns {key: Capture}. Errors in one capture are recorded, not fatal,
    unless three in a row fail (the board is probably gone).
    """
    captures, errors_in_row = {}, 0
    maxalloc = int(board.info.get("maxalloc", 0) or 0)           # largest RAM block on the ESP32 (buffered mode)
    for i, spec in enumerate(specs):                             # enumerate gives (index, item)
        exp = exps[spec.exp]                                     # the experiment this spec belongs to
        if spec.buffered and maxalloc:                           # keep buffered captures inside free RAM
            n_max = int(maxalloc * 0.9) // 34                    # packets that fit, with 10 % margin
            if spec.n_frames() > n_max:
                spec.seconds = n_max / spec.rate                 # shorten the capture
                spec.tags["clamped_to_ram"] = True               # note it for the record
        console.start(i, spec, exp)                              # terminal header line
        live.start(i, spec, exp)                                 # live window: new capture
        if spec.prompt:                                          # a manual step
            live.wait(spec.prompt)
            input(f"\n  >>> {spec.prompt}\n  (press Enter to continue) ")   # blocks until Enter
        started = datetime.now().isoformat(timespec="seconds")   # timestamp text
        written = spec.registers()                               # the 12 CFG bytes
        try:
            if spec.power_cycle_first:                           # P's power-cycle captures
                pid = board.power_cycle()
                spec.tags["id_after_cycle"] = f"0x{pid:02X}"
            board.set_aggressors(spec.sclk, spec.wifi, spec.load)   # SPI clock / WiFi / CPU load
            readback = board.configure(written)                  # write + read back registers
            n = spec.n_frames()

            def on_data(got, codes, n=n):                        # called by Board.capture as data arrives
                console.progress(got, n)                         # terminal progress bar
                live.data(got, codes)                            # live window update

            raw = board.capture(n, spec.discard, spec.buffered, spec.rate, on_data=on_data)
            cap = Capture(spec, raw.seq, raw.status, raw.codes, raw.fw, raw.host, written, readback, started)
        except DeviceError as err:                               # the board refused or did not answer
            cap = Capture(spec, np.zeros(0, np.uint32), np.zeros(0, np.uint32), np.zeros((0, 8), np.int32),
                          {}, {}, written, [], started, error=str(err))   # an empty capture carrying the error
        cap.integrity = check_integrity(cap, suite)              # can the data be trusted?
        if cap.error or not len(cap.seq):                        # nothing usable (board error OR zero frames)
            errors_in_row += 1                                   # count it: several in a row = stop the run
            reasons = "; ".join(cap.integrity.get("messages", []))   # e.g. "DRDY timeout: conversions stopped ..."
            verdict, text = FAIL, cap.error or reasons or "no data"  # show WHY, not just "no data"
        else:
            errors_in_row = 0                                    # real data arrived: reset the counter
            try:
                verdict, text = exp.quick(cap)                   # the experiment's one-line verdict
            except Exception as err:                             # a quick-look bug must not stop the run
                verdict, text = INFO, f"(quick look failed: {err})"
            if cap.integrity["verdict"] in (WARN, FAIL):         # data problems override / add to the verdict
                verdict = worst([verdict, cap.integrity["verdict"]])
                text = "; ".join(cap.integrity["messages"])[:160] + " | " + text
        console.done(verdict, text)                              # terminal verdict line
        live.done(i, spec.exp, spec.title, verdict, text)        # live scoreboard
        cap.save(cap_dir)                                        # raw data to disk right away
        captures[spec.key] = cap
        if errors_in_row >= 3:                                   # the board is unplugged or the ADC is not converting
            print("\nThree captures in a row returned no data; stopping the capture loop "
                  "(see the FAIL reasons above).")
            break
    return captures


# ===========================================================================
# Analysis
# ===========================================================================
def analyze_all(exps: list, ctx: Context) -> list:
    """
    Run every experiment's analysis. P goes last because it summarises the
    integrity of all captures, but it is shown first in the report.
    """
    order = [e for e in exps if e.id != "P"] + [e for e in exps if e.id == "P"]   # P last
    for e in order:
        print(f"  analysing {e.id} · {e.name} …")
        try:
            ctx.results[e.id] = e.analyze(ctx)
        except Exception:                                        # one broken analysis must not lose the others
            res = e.new_result()
            res.verdict = FAIL
            res.findings.append((FAIL, "analysis crashed:\n" + traceback.format_exc(limit=3)))
            ctx.results[e.id] = res
            traceback.print_exc()                                # show the full error in the terminal
    return [ctx.results[e.id] for e in exps if e.id in ctx.results]   # report order = registry order


class Tee:
    """Write everything printed to the terminal also into a log file (like the Unix `tee` command)."""

    def __init__(self, stream, path: Path):
        self.stream = stream                                     # the real terminal
        self.fh = path.open("a", encoding="utf-8")               # the log file, appended to

    def write(self, s):
        self.stream.write(s)                                     # to the terminal
        self.fh.write(s)                                         # and to the file

    def flush(self):
        self.stream.flush()
        self.fh.flush()


# ===========================================================================
# main
# ===========================================================================
def main():
    """Glue everything together in the order described at the top of this file."""
    args = parse_args()
    if args.reanalyze:                                           # ---- re-analysis of a saved run ----
        run_dir = Path(args.reanalyze).resolve()
        saved = json.loads((run_dir / "plan_resolved.json").read_text())   # the exact plan that was run
        plan = saved["plan"]
        device_file = run_dir / "device.json"
        device = json.loads(device_file.read_text()) if device_file.exists() else {}
        source = saved.get("source", "?") + " (re-analysed)"
    else:                                                        # ---- normal run ----
        plan = apply_overrides(tomllib.loads(Path(args.plan_file).read_text()), args)
        device, source = {}, ""
    suite = build_suite(plan)
    exps = build_experiments(plan, suite, args)
    specs = collect_specs(exps)
    print_plan(specs, exps)
    if args.list:                                                # --list: show every capture and stop
        for s in specs:
            print(f"  {s.key:<22} {s.title}")
        return

    live = None                                                  # live window (normal runs only)
    if args.reanalyze:
        cap_dir = run_dir / "captures"
        captures = {}
        for s in specs:                                          # load every capture that exists
            if (cap_dir / f"{s.key}.json").exists():
                c = Capture.load(cap_dir, s.key)
                c.integrity = check_integrity(c, suite)          # recompute with the current thresholds
                captures[s.key] = c
        print(f"Loaded {len(captures)} of {len(specs)} captures from {cap_dir}")
    else:
        out_root = (Path(args.plan_file).resolve().parent / plan["suite"].get("output_dir", "../runs")).resolve()
        run_dir = out_root / (datetime.now().strftime("%Y-%m-%d_%H%M%S") + ("_sim" if args.simulate else ""))
        cap_dir = run_dir / "captures"
        cap_dir.mkdir(parents=True)                              # creates runs/<timestamp>/captures
        sys.stdout = Tee(sys.stdout, run_dir / "console.log")    # keep a copy of all terminal output
        shutil.copy(args.plan_file, run_dir / "test_plan_used.toml")   # record which plan was used
        print(f"Run folder: {run_dir}")

        board, source = open_board(args, plan["suite"])
        dev_id = board.read_id()                                 # first sanity check (section 1.3)
        device = {"id": dev_id, "firmware": board.info, "source": source}
        print(f"Connected: {source}; firmware {board.info.get('fw', '?')}; ADS1298 ID = 0x{dev_id:02X}")
        if board.info.get("drdy") == "dout":                     # firmware uses the DRDY-wire workaround (ads1298.h)
            print("Data ready: taken from DOUT (DRDY_VIA_DOUT workaround: the DRDY wire is not connected)")
        if dev_id != suite.expected_id and not args.force:       # wrong/no chip: nothing else is meaningful
            board.close()
            sys.exit(f"\nThe ID register reads 0x{dev_id:02X}, expected 0x{suite.expected_id:02X}. SPI wiring, "
                     "power or the PWDN/RESET pins are wrong, so every measurement would be meaningless. "
                     "Fix that first (or pass --force).")
        (run_dir / "plan_resolved.json").write_text(json.dumps({"plan": plan, "source": source}, indent=1))

        live_on = bool(plan["suite"].get("live", True)) and not args.no_live
        live = LiveDashboard(enabled=live_on, snapshot=os.environ.get("CLAMSHELL_LIVE_SNAPSHOT"))
        live.plan(specs, exps)
        console = ConsoleProgress(len(specs))
        t0 = time.monotonic()
        try:
            captures = run_captures(board, specs, {e.id: e for e in exps}, suite, cap_dir, console, live)
        except KeyboardInterrupt:                                # Ctrl+C: keep what we have
            print("\n\nStopped by Ctrl+C — analysing the captures taken so far.")
            captures = {p.stem: Capture.load(cap_dir, p.stem) for p in cap_dir.glob("*.json")}
            for c in captures.values():
                c.integrity = check_integrity(c, suite)
        try:
            board.set_aggressors(suite.sclk_hz, "off", "idle")   # leave the board in a quiet state
            device["registers_after_run"] = board.read_all_registers()   # for the report appendix
        except DeviceError:
            pass
        board.close()
        (run_dir / "device.json").write_text(json.dumps(device, indent=1, default=str))
        print(f"\nCaptures finished in {(time.monotonic() - t0) / 60:.1f} min.")

    print("\nAnalysis")
    print("────────")
    ctx = Context(suite, captures, run_dir / "figures", device)
    results = analyze_all(exps, ctx)
    meta = {"Run": run_dir.name, "Source": source, "Captures": len(captures),
            "Device ID": f"0x{device['id']:02X}" if isinstance(device.get("id"), int) else "?",
            "Firmware": device.get("firmware", {}).get("fw", "?"),
            "Rates": ", ".join(map(str, suite.rates)), "Channels": ", ".join(map(str, suite.channels)),
            "Channel plan": ", ".join(suite.channel_plan), "Capture length (s)": suite.capture_seconds,
            "Mains (Hz)": suite.mains_hz, "Experiments": ", ".join(e.id for e in exps),
            "Registers after run": " ".join(f"{r:02X}" for r in device.get("registers_after_run", [])) or "—"}
    report = write_all(run_dir, results, meta)                   # report.html, summary.md, CSV, JSON

    print("\nResults")
    print("───────")
    for r in results:
        print(f"  {r.id}  {r.verdict:<4}  {r.name:<42} {r.headline[:70]}")
    print(f"\n  Overall: {worst([r.verdict for r in results])}")
    print(f"  Report:  {report}")
    print(f"  Summary: {run_dir / 'summary.md'}")
    if not args.no_open and not os.environ.get("CLAMSHELL_LIVE_SNAPSHOT"):
        webbrowser.open(report.as_uri())                         # file:///... URL in the default browser
    if live is not None:
        live.finish(report, {r.id: r.verdict for r in results})  # final scoreboard in the window
        if live.enabled and not os.environ.get("CLAMSHELL_LIVE_SNAPSHOT"):
            print("\nClose the live window to exit.")
        live.close(wait=True)                                    # wait until the window is closed


if __name__ == "__main__":                                       # only when run as a script, not when imported
    main()
