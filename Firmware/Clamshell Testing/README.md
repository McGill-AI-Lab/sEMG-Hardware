# ADS1298 clamshell test suite

This suite runs every experiment in [clamshell_validation.md](clamshell_validation.md) in one go. While it runs, a
window shows what is happening. At the end it writes a report with a PASS / WARN / FAIL verdict per experiment.

```
Clamshell Testing/
├── clamshell_validation.md   the plan (what and why)
├── firmware/                 ESP32-S3 firmware: flash once, never changes per test
│   ├── platformio.ini
│   └── src/  main.cpp        command server (CFG, CAP, WIFI, ...)
│             ads1298.h/.cpp  SPI driver for the ADS1298
│             aggressors.h/.cpp  WiFi / CPU-load noise sources for Experiment F
├── host/                     PC side (Python)
│   ├── run_suite.py          ← THE file you run
│   ├── test_plan.toml        ← the file you edit to choose / limit experiments
│   ├── requirements.txt
│   └── clamshell/            the package (read the files in the order listed in __init__.py)
└── runs/                     one folder per run: report.html, summary.md, CSV, raw captures
```

## How it works

```
 test_plan.toml ─► run_suite.py ──"CFG 84 00 C0 00 01 81 …"──► ESP32 firmware ──SPI WREG──► ADS1298
                        ▲        ◄──"OK CFG <readback>"──────                 ◄─SPI RREG──
                        │        ──"CAP 20000 32 S"─────────►  waits for DRDY, reads 27-byte frames
                        │        ◄──34-byte binary packets ──  (sync, sequence no., raw frame, checksum)
                        │        ◄──"END sent=… missed=…"───
                        ▼
   live window + terminal  →  analysis (numpy/scipy)  →  runs/<date>/report.html
```

The firmware contains no experiments. It writes the registers the PC asks for, streams raw 24-bit frames
untouched, and reports exactly how many conversions it saw and missed. Everything else happens on the PC: which
rate, which channels, which gain, which input MUX, and all the analysis. So you only change `test_plan.toml`,
never the firmware.

## One-time setup

1. **Flash the firmware.** Open `firmware/` in VS Code with PlatformIO and press *Upload*, or run:
   ```
   cd "Clamshell Testing/firmware"
   pio run -t upload
   ```
   Use the board's **UART** USB port. Wiring is the same as for the earlier sketches (pins at the top of
   `src/ads1298.h`).
2. **Python packages** (Python ≥ 3.11):
   ```
   cd "Clamshell Testing/host"
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
3. **Try it without hardware first**, so you can see what each experiment does:
   ```
   .venv/bin/python run_suite.py --simulate --quick
   .venv/bin/python run_suite.py --simulate faulty --quick   # what failures look like
   ```

## Running the real thing

```
.venv/bin/python run_suite.py --list     # plan + time estimate (≈ 22 min for the default plan)
.venv/bin/python run_suite.py            # run everything enabled in test_plan.toml
```

By default every applicable experiment runs at **500, 2000 and 4000 SPS**, first on **CH1 … CH8 one at a time**
(the other channels powered down), then with **all 8 channels together**.

### Running only part of it

| You want | Command line | Or permanently in `test_plan.toml` |
|---|---|---|
| Only some experiments | `--only A,G` | `enabled = false` in the others |
| Everything except some | `--skip F,I` | |
| One data rate | `--rates 500` | `[suite] rates = [500]` |
| Some channels | `--channels 1,2` | `[suite] channels = [1, 2]` |
| Single-channel runs only / all-channel only | `--plan each` / `--plan all` | `[suite] channel_plan = ["each"]` |
| Shorter captures | `--seconds 3` | `[suite] capture_seconds = 3` |
| Quick smoke test | `--quick` | |
| Redo the analysis of an old run | `--reanalyze ../runs/<folder>` | |

B, D and E capture nothing. They re-analyse A's data, so `--only E` automatically adds A's captures.

### What you see while it runs

- **Terminal:** the plan, a progress bar per capture, and a verdict line as each capture finishes.
  Everything is also saved to `console.log` in the run folder.
- **Live window:**
  - which experiment is running and why, plus run and capture progress bars;
  - the last second of signal (channels stacked) and its spectrum;
  - a scoreboard of finished captures.

  Close it at the end to exit, or use `--no-live` for terminal only.
- **Manual steps** (the J connector-short test, and battery or other F variants you add) pause and ask you to
  press Enter.

### What you get

`runs/<date_time>/`:

| File | Contents |
|---|---|
| `report.html` | Opens automatically. One tile per experiment, a "things to look at" list, then charts, tables and an explanation per experiment |
| `summary.md` | Verdicts, findings, and the results log in the format of section 13 of the plan |
| `results_log.csv` | The same results log as a spreadsheet |
| `results.json` | Everything, for your own scripts |
| `captures/*.npz/.json` | Raw codes and settings of every capture (used by `--reanalyze`) |

## How the problems in section 1.1 are handled

| Problem in the plan | What this suite does |
|---|---|
| Interleaved exact `0.000000` samples | The DRDY interrupt now counts conversions instead of setting a flag. The capture loop reads each frame right after DRDY and never prints while capturing. START is used through the pin only. Every frame's status word is checked (`1100…`), and "exact zeros while the signal is far from zero" is flagged. P runs this check at every rate, using the test signal on all channels. |
| Test-signal amplitude ≈ 1/6 of expected | Every CFG is read back and compared. CONFIG2 is `0x10 \| amp \| freq` (bit 6 cleared, as todo.md suggests). G's **gain cross-check** measures the same test signal at gains 1–12: a correct chain gives a flat line, while the bug gives an amplitude falling as 1/G, and the report says so. |
| `CONFIG1 = 0x06` is LP 250 SPS | CONFIG1 is built from the rate: `0x86` (500), `0x84` (2 k), `0x83` (4 k), always HR mode. |
| Printing floats per sample | Raw 24-bit codes go out as binary packets with a checksum. Conversion to µV happens on the PC. |
| SPI budget (1.2) | Frames are read at 4 MHz (54 µs per frame). Register access stays at 500 kHz with gaps between bytes for t_SDECODE. F's SPI-clock variants that are too slow for a rate are skipped automatically. |
| Sanity checks (1.3) | ID check before anything else (the run stops if it is wrong), readback of every write, sample rate measured from DRDY timestamps, status-word check, 32 settling frames discarded, 200 ms reference start-up wait. |
| No silent sample loss (todo.md) | Each packet carries its DRDY sequence number. Gaps and the firmware's missed-conversion counter are both reported, per capture. |

## Things to know

- **Serial speed.** The link runs at 2 Mbaud (4 kSPS × 34 bytes needs 1.36 Mbaud). The DevKitC's CP2102N or CH343
  bridge handles this. If yours cannot, lower `SERIAL_BAUD` in `firmware/src/main.cpp` **and** `baud` in
  `test_plan.toml`. The 4 kSPS captures will then show missed frames rather than hiding them.
- **Expected noise.** Unless you type datasheet values into `[reference.noise_uVrms]`, A compares against an
  estimate scaled from the "4 µVpp in 150 Hz at G = 6" headline. Copy the real numbers from the *Noise
  Measurements* table of your datasheet revision to make A's verdicts meaningful.
- **Mains frequency.** Set `mains_hz` (50 or 60) so spectral lines are labelled correctly.
- **Supplies.** Set `avdd`, `avss` and `dvdd` in `[H]` to your board's actual rails.
- **Long drift run.** For the 30–60 min warm-up the plan recommends, set `[I] duration_s = 1800` and run
  `--only I` from a cold board.
- **Power cycles.** P's power cycles use the PWDN pin. todo.md also asks for 10 real supply power cycles; do
  those by hand and run `--only P` after each.
- **What the simulator is.** All numbers from `--simulate` are synthetic. They exist only to exercise the code.

## Reading order for the code

1. `firmware/src/main.cpp`: the command server and capture loop (start here)
2. `firmware/src/ads1298.cpp`: SPI, registers, DRDY interrupt
3. `host/run_suite.py`: the overall flow
4. `host/clamshell/device.py`: the serial protocol and packet decoding
5. `host/clamshell/experiments.py`: what each experiment captures and how it is judged
6. `host/clamshell/analysis.py`: the maths
