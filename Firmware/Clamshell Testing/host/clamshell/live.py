"""
==============================================================================
 live.py  —  what you see WHILE the suite runs
==============================================================================

Two displays, both fed by the runner:

1. ConsoleProgress — always on. Prints the plan, one progress bar per
   capture (redrawn in place with "\\r"), and a one-line verdict when each
   capture finishes.

2. LiveDashboard — an optional matplotlib window that shows:
     - which experiment is running, its goal, and overall progress,
     - the last second of signal on every enabled channel,
     - the spectrum of the current capture so far,
     - a scoreboard of finished captures with PASS / WARN / FAIL.

WHY THE WINDOW RUNS IN A SEPARATE PROCESS
-----------------------------------------
Data arrives at up to 136 kB/s. If the same program that reads the serial port
also redraws a plot (tens of milliseconds each time), incoming bytes pile up
and can be lost in the USB-UART bridge. So the window lives in a second
Python PROCESS (library: `multiprocessing`). The two processes share nothing
but a Queue:
    runner  ──put(message)──►  multiprocessing.Queue  ──get()──►  window process
Messages are small dicts ("start", "data", "done", "finish"). If the window is
slow or was closed, messages are simply dropped (put_nowait + queue.Full), so
the capture never waits for the display.
==============================================================================
"""

from __future__ import annotations

import multiprocessing as mp                   # separate process + inter-process queue
import queue                                   # only for the queue.Full / queue.Empty exception types
import sys                                     # sys.stdout.write for in-place progress bars
import textwrap                                # wrap the experiment goal onto several lines
import time                                    # throttle how often we send data to the window

import numpy as np
from scipy.signal import welch                 # averaged spectrum (several overlapping FFTs) for a steadier display

from . import ads1298 as ads
from .palette import LIGHT, VERDICT_ICON, channel_color, verdict_color


# ===========================================================================
# 1. Console output
# ===========================================================================
class ConsoleProgress:
    """Text progress in the terminal. Works everywhere, even over SSH."""

    def __init__(self, total: int):
        self.total = total                      # number of captures in the run
        self.t0 = time.monotonic()              # start of the run
        self._last = 0.0                        # time of the last progress redraw

    def start(self, i: int, spec, exp):
        """Print the header line of capture i (0-based)."""
        print(f"\n[{i + 1:>3}/{self.total}] {exp.id} · {exp.name} — {spec.title}")   # e.g. "[ 12/57] A · ..."

    def progress(self, got: int, n: int):
        """Redraw the bar for the current capture, at most 10 times a second."""
        now = time.monotonic()                  # current time
        if now - self._last < 0.1 and got < n:  # too soon since the last redraw
            return
        self._last = now
        frac = got / n if n else 1.0            # fraction done
        bar = "█" * int(frac * 30) + "░" * (30 - int(frac * 30))   # 30-character bar
        sys.stdout.write(f"\r        {bar} {frac:5.1%}  {got}/{n} frames")   # \r = back to line start
        sys.stdout.flush()                      # show it now

    def done(self, verdict: str, text: str):
        """Finish the bar line and print the capture's verdict."""
        elapsed = time.monotonic() - self.t0    # total time so far
        print(f"\n        {VERDICT_ICON.get(verdict, '?')} {verdict:<4}  {text}   (run time {elapsed / 60:.1f} min)")


# ===========================================================================
# 2. Live window: main-process side
# ===========================================================================
class LiveDashboard:
    """
    Main-process handle of the live window. Methods only put messages on the
    queue, so they return immediately.
    """

    def __init__(self, enabled: bool = True, snapshot: str | None = None):
        self.enabled = enabled                  # False -> every method does nothing
        self._q = None                          # the queue (created below)
        self._proc = None                       # the window process
        self._buf = {}                          # recent samples of the current capture, per channel
        self._last_send = 0.0                   # throttle timer
        if not enabled:                         # nothing more to do
            return
        ctx = mp.get_context("spawn")           # "spawn" = start a fresh Python, the only safe choice on macOS
        self._q = ctx.Queue(maxsize=64)         # small queue: old messages are dropped when it is full
        self._proc = ctx.Process(target=_window_main, args=(self._q, snapshot), daemon=False)   # the window process
        self._proc.start()                      # launch it

    def _send(self, msg: dict):
        """Put a message on the queue without ever blocking."""
        if not self.enabled or self._q is None:
            return
        try:
            self._q.put_nowait(msg)             # returns at once
        except queue.Full:                      # window busy or closed
            pass                                # drop the message

    # ---- events from the runner ------------------------------------------------
    def plan(self, specs, experiments):
        """Tell the window the full list of captures."""
        self._send({"type": "plan", "n": len(specs),
                    "items": [(s.exp, s.title) for s in specs]})

    def start(self, i, spec, exp):
        """A new capture begins: reset the buffers and tell the window what it is."""
        self._buf = {ch: np.zeros(0) for ch in spec.channels}   # empty buffer per enabled channel
        self._spec = spec                                       # remember for scaling
        self._send({"type": "start", "i": i, "exp": exp.id, "name": exp.name, "goal": exp.goal,
                    "title": spec.title, "channels": spec.channels, "n": spec.n_frames(), "rate": spec.rate})

    def wait(self, text):
        """The runner is waiting for you (a manual step)."""
        self._send({"type": "wait", "text": text})

    def data(self, got: int, codes: np.ndarray):
        """
        New frames arrived (called from Board.capture). Keep the last 4 s per
        channel, and 4 times a second send the window the last 1 s of signal
        plus the spectrum of those 4 s.
        """
        if not self.enabled:
            return
        s = self._spec
        keep = int(4 * s.rate)                                  # samples kept for the spectrum
        for ch in s.channels:                                   # convert and append
            x = ads.codes_to_uV(codes[:, ch - 1].astype(float), s.gains[ch - 1], s.vref)
            self._buf[ch] = np.concatenate([self._buf[ch], x])[-keep:]
        now = time.monotonic()
        if now - self._last_send < 0.25:                        # at most 4 updates per second
            return
        self._last_send = now
        show = int(1.0 * s.rate)                                # 1 s of signal on screen
        step = max(1, show // 1000)                             # at most ~1000 points per line
        y, asd, f = {}, {}, None
        for ch, x in self._buf.items():
            if len(x) < 64:                                     # too little data yet
                continue
            seg = x[-show:]                                     # the newest second
            y[ch] = (seg - seg.mean())[::step].astype(np.float32)   # mean removed, decimated
            nper = 2 ** int(np.log2(max(32, min(len(x) // 4, int(s.rate) // 2))))   # Welch segment: >= 4 segments
            ff, psd = welch(x - x.mean(), fs=s.rate, nperseg=nper)  # averaged spectrum of up to 4 s
            asd[ch] = np.sqrt(psd[1:]).astype(np.float32)        # ASD in µV/√Hz, skip DC
            f = ff[1:].astype(np.float32)                       # matching frequencies
        self._send({"type": "data", "got": got, "y": y, "dt": step / s.rate, "f": f, "asd": asd})

    def done(self, i, exp_id, title, verdict, text):
        """A capture finished."""
        self._send({"type": "done", "i": i, "exp": exp_id, "title": title, "verdict": verdict, "text": text})

    def finish(self, report_path, verdicts: dict):
        """The whole run finished; show the final scoreboard."""
        self._send({"type": "finish", "report": str(report_path), "verdicts": verdicts})

    def close(self, wait: bool = True):
        """Wait for the window to be closed by the user (or stop it)."""
        if self._proc is None:
            return
        if wait:
            self._proc.join()                   # returns when the window is closed
        elif self._proc.is_alive():
            self._proc.terminate()              # stop it now


# ===========================================================================
# 3. Live window: the separate process
# ===========================================================================
def _window_main(q, snapshot: str | None):
    """
    Entry point of the window process. Runs its own little event loop:
    read all waiting messages, update the drawing, let matplotlib process
    window events for 0.1 s (plt.pause), repeat. Exits when the window is
    closed. `snapshot` (testing only) renders off-screen and saves a PNG at
    the end instead of opening a window.
    """
    import matplotlib                                           # imported here: this runs in the new process
    if snapshot:                                                # off-screen for tests
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if not snapshot:                                            # a real window is wanted
        # "spawn" re-imports run_suite.py in this process, which imports plots.py,
        # which forces the file-only "Agg" backend. Switch to a window backend here.
        for name in ("macosx", "QtAgg", "TkAgg"):               # macOS native first, then common fallbacks
            try:
                plt.switch_backend(name)                        # change the backend even after pyplot was imported
                break                                           # the first one that works is enough
            except Exception:                                   # not installed / not supported on this OS
                continue                                        # try the next one
    w = _Window(plt)                                            # build the figure
    finished = False
    while True:
        try:
            for _ in range(200):                                # handle up to 200 waiting messages
                msg = q.get_nowait()
                w.handle(msg)
                finished |= msg["type"] == "finish"
        except queue.Empty:                                     # nothing more waiting
            pass
        except (EOFError, OSError):                             # the main process went away
            break
        w.redraw()                                              # update artists if something changed
        if snapshot:                                            # test mode
            if finished:
                w.fig.savefig(snapshot, dpi=110)
                break
            time.sleep(0.05)
            continue
        if not plt.fignum_exists(w.fig.number):                 # the user closed the window
            break
        plt.pause(0.1)                                          # process GUI events, sleep 0.1 s


class _Window:
    """The figure and all its parts. Lives only in the window process."""

    def __init__(self, plt):
        import matplotlib.ticker as mticker                     # tick locators/formatters (axis number placement)
        th = self.th = LIGHT                                    # light theme colours
        self.plt = plt                                          # keep pyplot for drawing rectangles etc.
        self.mticker = mticker                                  # keep the ticker module for later
        self.fig = plt.figure(figsize=(12.5, 7.6), facecolor=th.surface)   # the window
        try:
            self.fig.canvas.manager.set_window_title("ADS1298 clamshell validation — live")
        except Exception:                                       # some backends have no title
            pass
        gs = self.fig.add_gridspec(3, 2, height_ratios=[1.05, 3, 1.7], hspace=0.45, wspace=0.18,
                                   left=0.06, right=0.98, top=0.97, bottom=0.04)   # layout grid
        self.ax_head = self.fig.add_subplot(gs[0, :])           # header (text + progress bars)
        self.ax_wave = self.fig.add_subplot(gs[1, 0])           # waveform
        self.ax_asd = self.fig.add_subplot(gs[1, 1])            # spectrum
        self.ax_score = self.fig.add_subplot(gs[2, :])          # scoreboard
        for ax in (self.ax_head, self.ax_score):                # text-only areas: no axes
            ax.axis("off")
        for ax in (self.ax_wave, self.ax_asd):                  # plot areas: recessive styling
            self._style(ax)
        self.ax_wave.set_xlabel("time (ms)")
        self.ax_wave.set_ylabel("µV (input-referred, mean removed)")
        self.ax_asd.set_xlabel("frequency (Hz)")
        self.ax_asd.set_ylabel("µV/√Hz")
        self.ax_asd.set_xscale("log")
        self.ax_asd.set_yscale("log")
        self.t_exp = self.ax_head.text(0, 1.0, "Waiting for the board …", fontsize=15, weight="bold",
                                       color=th.ink, va="top", transform=self.ax_head.transAxes)
        self.t_goal = self.ax_head.text(0, 0.62, "", fontsize=9.5, color=th.ink2, va="top",
                                        transform=self.ax_head.transAxes)
        self.t_cap = self.ax_head.text(0, 0.05, "", fontsize=10, color=th.ink, va="bottom",
                                       transform=self.ax_head.transAxes)
        self.t_score = self.ax_score.text(0, 1.0, "", fontsize=9, color=th.ink, va="top", family="monospace",
                                          transform=self.ax_score.transAxes)
        self.t_tally = self.ax_score.text(1.0, 1.0, "", fontsize=10, color=th.ink, va="top", ha="right",
                                          family="monospace", transform=self.ax_score.transAxes)
        # progress bars drawn as rectangles in header-axes coordinates
        self.bar_run_bg = self.ax_head.add_patch(self.plt.Rectangle((0.62, 0.30), 0.38, 0.10, color=th.grid,
                                                                    transform=self.ax_head.transAxes))
        self.bar_run = self.ax_head.add_patch(self.plt.Rectangle((0.62, 0.30), 0.0, 0.10, color=th.series[0],
                                                                 transform=self.ax_head.transAxes))
        self.bar_cap_bg = self.ax_head.add_patch(self.plt.Rectangle((0.62, 0.05), 0.38, 0.10, color=th.grid,
                                                                    transform=self.ax_head.transAxes))
        self.bar_cap = self.ax_head.add_patch(self.plt.Rectangle((0.62, 0.05), 0.0, 0.10, color=th.series[2],
                                                                 transform=self.ax_head.transAxes))
        self.t_run = self.ax_head.text(0.62, 0.44, "run", fontsize=8, color=th.muted, transform=self.ax_head.transAxes)
        self.t_capbar = self.ax_head.text(0.62, 0.19, "capture", fontsize=8, color=th.muted,
                                          transform=self.ax_head.transAxes)
        self.lines_w, self.lines_a = {}, {}                     # one line per channel in each plot
        self.n_total, self.i, self.n_frames = 0, 0, 1           # progress state
        self.spacing = 0.0                                      # vertical gap between stacked traces, µV
        self.history = []                                       # finished captures (verdict, exp, title, text)
        self.dirty = True                                       # something changed -> redraw

    def _style(self, ax):
        """Same recessive look as the report charts."""
        th = self.th
        ax.set_facecolor(th.surface)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(th.base)
        ax.tick_params(colors=th.muted, labelsize=8)
        ax.grid(True, color=th.grid, linewidth=0.6)
        ax.xaxis.label.set_color(th.ink2)
        ax.yaxis.label.set_color(th.ink2)

    def handle(self, m: dict):
        """
        Update the window from one message. Each message is a dict whose
        "type" says what happened; the other keys carry the details.
        Matplotlib "artists" (lines, texts, rectangles) are updated in place
        with set_data / set_text / set_width, which is much faster than
        clearing and redrawing the plots.
        """
        t = m["type"]                                           # which kind of message
        if t == "plan":                                         # whole-run information
            self.n_total = m["n"]                               # number of captures in the run
        elif t == "start":                                      # a new capture
            self.i, self.n_frames = m["i"], m["n"]              # capture index and its length in frames
            self.t_exp.set_text(f"Experiment {m['exp']} · {m['name']}")   # big title
            self.t_goal.set_text("\n".join(textwrap.wrap(m["goal"], 120)[:3]))   # goal, max 3 lines of 120 chars
            self.t_cap.set_text(f"Capture {m['i'] + 1}/{self.n_total}:  {m['title']}")   # what is being captured
            for ln in list(self.lines_w.values()) + list(self.lines_a.values()):   # remove old lines
                ln.remove()                                     # take the line off its plot
            self.lines_w, self.lines_a = {}, {}                 # start with no lines
            for ch in m["channels"]:                            # new lines in each channel's fixed colour
                c = channel_color(self.th, ch)                  # CH1 always blue, CH2 orange, ...
                self.lines_w[ch], = self.ax_wave.plot([], [], color=c, linewidth=1.0, label=f"CH{ch}")   # empty for now
                self.lines_a[ch], = self.ax_asd.plot([], [], color=c, linewidth=0.9)   # "x, = list" unpacks a 1-item list
            if len(m["channels"]) > 1:                          # legend only for >= 2 series (identifies the spectrum lines)
                self.ax_asd.legend(frameon=False, fontsize=7, ncols=8, loc="upper center",
                                   bbox_to_anchor=(0.5, 1.13), labelcolor=self.th.ink2,
                                   handles=list(self.lines_w.values()))
            elif self.ax_asd.get_legend():                      # single channel: drop the old legend
                self.ax_asd.get_legend().remove()
            self.ax_wave.set_title(f"last 1 s, {m['rate']} SPS", fontsize=9, color=self.th.ink2, loc="left")
            self.bar_cap.set_width(0)                           # empty capture progress bar
        elif t == "wait":                                       # manual step
            self.t_cap.set_text("WAITING FOR YOU — see the terminal:  " + m["text"][:110])
        elif t == "data":                                       # new signal
            chans = [ch for ch in self.lines_w if ch in m["y"]] # channels with data, in order
            if len(chans) > 1:                                  # several channels: stack them vertically
                spread = max(np.percentile(m["y"][ch], 99.5) - np.percentile(m["y"][ch], 0.5) for ch in chans)
                self.spacing = max(spread * 1.15, 1e-3)         # gap between traces, µV
            else:
                self.spacing = 0.0                              # one channel: no offset
            for k, ch in enumerate(chans):                      # k-th channel drawn k gaps lower
                y = m["y"][ch]                                  # mean-removed, decimated samples
                self.lines_w[ch].set_data(np.arange(len(y)) * m["dt"] * 1000, y - k * self.spacing)
            if len(chans) > 1:                                  # label each trace on the y axis
                self.ax_wave.set_yticks([-k * self.spacing for k in range(len(chans))], [f"CH{c}" for c in chans])
                self.ax_wave.set_ylabel(f"channels stacked, {self.spacing:.3g} µV apart")
            else:
                self.ax_wave.yaxis.set_major_locator(self.mticker.AutoLocator())   # normal numeric ticks again
                self.ax_wave.yaxis.set_major_formatter(self.mticker.ScalarFormatter())
                self.ax_wave.set_ylabel("µV (input-referred, mean removed)")
            if m["f"] is not None:                              # a spectrum came with the message
                for ch, a in m["asd"].items():
                    if ch in self.lines_a:
                        self.lines_a[ch].set_data(m["f"], a)    # frequency vs ASD
            self.bar_cap.set_width(0.38 * min(1.0, m["got"] / max(1, self.n_frames)))   # capture progress
            for ax in (self.ax_wave, self.ax_asd):              # rescale axes to the new data
                ax.relim()                                      # recompute the data limits
                ax.autoscale_view()                             # and fit the axes to them
        elif t == "done":                                       # a capture finished
            self.history.append((m["verdict"], m["exp"], m["title"], m["text"]))   # remember for the scoreboard
            self.bar_run.set_width(0.38 * len(self.history) / max(1, self.n_total))   # overall progress
            self.bar_cap.set_width(0.38)                        # this capture: full
        elif t == "finish":                                     # the run finished
            self.t_exp.set_text("Run complete")                 # final title
            short = "/".join(m["report"].replace("\\", "/").split("/")[-2:])   # "<run folder>/report.html"
            self.t_goal.set_text("Report: runs/" + short + " (opened in your browser)\nClose this window to exit.")
            self.t_cap.set_text("Experiments:  " + "   ".join(
                f"{k} {VERDICT_ICON.get(v, '?')} {v}" for k, v in m["verdicts"].items()))   # one verdict per experiment
            self.bar_run.set_width(0.38)                        # run progress: full
        self._update_score()                                    # refresh the scoreboard text
        self.dirty = True                                       # ask for a redraw

    def _update_score(self):
        """Scoreboard: the last 8 captures, and a count of each verdict."""
        lines = [f"{VERDICT_ICON.get(v, '?')} {v:<4} {e}  {ti[:46]:<46}  {tx[:70]}"   # icon, verdict, exp, title, text
                 for v, e, ti, tx in self.history[-8:]]                  # only the newest 8
        self.t_score.set_text("Finished captures (latest last)\n" + "\n".join(lines))
        counts = {k: sum(1 for h in self.history if h[0] == k) for k in ("PASS", "INFO", "WARN", "FAIL")}   # tallies
        self.t_tally.set_text("\n".join(f"{VERDICT_ICON[k]} {k:<4} {n:>3}" for k, n in counts.items()))
        worst = "FAIL" if counts["FAIL"] else "WARN" if counts["WARN"] else "PASS"   # worst verdict so far
        self.t_tally.set_color(verdict_color(self.th, worst) if self.history else self.th.ink)   # tally colour = worst

    def redraw(self):
        """Ask matplotlib to redraw if anything changed."""
        if self.dirty:
            self.fig.canvas.draw_idle()                         # schedule a redraw (cheap if nothing changed)
            self.dirty = False
