# Electrode Testing Protocol (dry sEMG electrodes)

Purpose: compare dry electrode candidates in a way that is **repeatable**. Background, CMRR budget
and design decisions are in `afe.md`; this file is only the test procedure. Run the same test on
different electrodes, people or days and get comparable numbers.

Targets we are testing against:

| Property | Target | Notes |
|---|---|---|
| Skin–electrode impedance \|Z\| | < 100 kΩ at 100 Hz, after 5 min settling | Also report 10 Hz and 1 kHz, magnitude and phase. sEMG is 20–500 Hz, so 10 Hz alone is misleading |
| DC offset between an electrode pair | < 100 mV at rest, rest drift < ~1 mV/min | The 100 mV limit comes from the gel ECG electrode standard (ANSI/AAMI EC12) and is borrowed as a goal. Motion jumps are recorded and compared; no hard limit yet |
| Impedance mismatch within a pair | As low as possible; aim for ΔZ < 20 kΩ | Sets how much mains hum leaks in (CMRR), see §6 |

Front-end context (from `docs/datasheets/processed/components/ADS1298_llamaparse.md` and the firmware):
ADS1298 at gain 6, VREF 2.4 V gives an input range of about ±400 mV. The DC input impedance is
1000 MΩ with no lead-off, 500 MΩ with current-source lead-off and 10 MΩ with pull-up lead-off.
According to `audits/ambrflow-v0-v1-20261028/EVIDENCE/adc_findings.md`, every electrode input has
2 kΩ in series and 620 pF to AGND, with no series blocking capacitor. The input is therefore
DC-coupled, so electrode DC offset reaches the ADC directly. Re-check this if the input network changes.

> **Safety:** whenever a person is connected, use battery-powered or isolated instruments (LCR meter,
> function generator, scope, laptop on battery). Never connect a person to mains-powered, non-isolated
> equipment. Keep test currents ≤ 10 µA.

---

## 0. Before touching skin: validate the measurement setup

Do this first, every session. If the rig can't measure a known part correctly, skin numbers mean
nothing.

### 0.1 Build a "skin phantom"
Solder a known network that behaves roughly like an electrode on skin:

```
 lead A ──[ R_s = 1 kΩ ]──┬──[ R_p = 100 kΩ ]──┬── lead B
                          └──[ C_p = 47 nF  ]──┘
```

- R_s stands for the body tissue, and R_p ∥ C_p for the skin contact.
- Use 1 % resistors and a C0G/NP0 or film capacitor (not X7R ceramic, whose value drifts with voltage).
- Calculate the expected |Z| and phase at each test frequency, using Z = R_s + R_p / (1 + j·2π·f·R_p·C_p):

| f | Expected \|Z\| | Expected phase |
|---|---|---|
| 10 Hz | ≈ 96.9 kΩ | ≈ −16.3° |
| 100 Hz | ≈ 32.4 kΩ | ≈ −69.6° |
| 1 kHz | ≈ 3.6 kΩ | ≈ −71.8° |

(Recompute these if you use other part values. A short Python one-liner with `complex()` works.)

### 0.2 Pass criteria for the setup
- |Z| within ±5 % of expected, and phase within ±3°, at every test frequency.
- **The phase of an electrode or phantom must always lie between 0° and −90°**. A real
  resistor–capacitor system can't be inductive (positive phase) or below −90°. Seeing a phase outside that
  range means the setup is wrong, not the electrode.

### 0.3 LCR-meter checklist (common causes of "impossible" phase)
1. **Run open/short compensation** at each test frequency with the exact cables and clips you
   will use. High-impedance readings (100 kΩ – 1 MΩ) are dominated by cable capacitance otherwise.
2. **Use a low test level.** Many LCR meters default to 1 V rms. Set it to **≤ 50 mV rms**, or
   use constant-current mode with ≤ 10 µA. High levels polarize the electrode and make the result
   non-linear.
3. **Turn DC bias OFF.** Any DC through the electrode polarizes it.
4. **Use low frequencies.** The defaults are often 1 kHz or higher, but sEMG lives at 20–500 Hz. Test at
   **10 Hz, 100 Hz and 1 kHz** (and lower if your meter supports it). Note your meter's lowest frequency.
5. **Mains pickup.** The body is an antenna for 50/60 Hz, and it corrupts readings, especially near
   50/60 Hz. Avoid test frequencies within ±5 Hz of mains and its harmonics, move away from power
   supplies, and use short twisted or shielded leads. Running the meter on battery helps if possible.
6. **Electrode DC voltage.** The pair has its own DC voltage (tens of mV), which can upset some
   meters. Check that the meter tolerates it, or add a large DC-blocking capacitor (≥ 10 µF film) in series and
   include it in the open/short compensation.
7. **Choose the right equivalent-circuit mode.** Record raw |Z| and θ (not Cs/Rs/Cp/Rp derived values),
   so the meter's circuit-model choice doesn't confuse things.
8. **Use 2-terminal vs 4-terminal (Kelvin) leads consistently.** Kelvin clips on two electrode
   leads is fine. Keep the clip arrangement the same between runs.
9. Let the meter settle and **average** (slow mode or high averaging), since dry contacts are noisy.

Only move on once the phantom passes §0.2.

### 0.4 Alternative method: function generator + series resistor
Use this if the LCR meter can't go low enough in frequency or test level, or keeps giving
impossible phase.

```
 generator ──[ R_ref = 1 MΩ ]──●── electrode A ~~ skin ~~ electrode B ──● ── generator GND
                               └── V_e measured across A–B ─────────────┘
```

1. Set the generator to a sine wave, **no DC offset**, at 10 Hz, then 100 Hz, then 1 kHz. Choose its amplitude so the
   current I = V_gen / R_ref is ≤ 10 µA (e.g. 1 V amplitude with 1 MΩ gives ≤ 1 µA).
2. Measure V_e (across the electrodes) and V_R (across R_ref) with a two-channel scope or
   the ADS1298 (differential, gain 1). Use a battery-powered or isolated scope, or measure both channels
   differentially, so the scope's ground doesn't short anything.
3. Then |Z| = |V_e| / (|V_R| / R_ref), and the phase = phase(V_e) − phase(V_R).
4. **Validate it on the §0.1 phantom first.** It must pass §0.2 before it's used on skin.

A 1 MΩ R_ref makes the current nearly independent of the electrode impedance, so the
generator acts like a current source.

---

## 1. Fixed test conditions (keep identical every run)

| Condition | Setting |
|---|---|
| Site | Volar forearm, about 1/3 of the way from elbow to wrist (mark it with a skin pen) |
| Electrode spacing | Same spacing as the bracelet (center-to-center, measure and record in mm) |
| Skin prep | Wipe with 70 % isopropyl alcohol, let dry 60 s. **No** abrasion or gel |
| Contact pressure | Fixed and known: same strap with marked hole, or a weight or spring force; record in N (or in kPa if contact area is known) |
| Room | Record temperature and humidity |
| Subject state | Seated, arm resting on table, relaxed. No exercise in the previous 15 min |
| Leads | Same cables, same routing, every time |

Record electrode **contact area** (diameter or dimensions) for every candidate. Impedance scales
roughly as 1/area, so compare candidates normalized to area too (kΩ·cm²).

---

## 2. Impedance vs. time (main test)

1. Place the electrode pair at the marked site with the fixed pressure. Start a timer.
2. Measure |Z| and phase at 10 Hz, 100 Hz and 1 kHz at **t = 0, 1, 2, 5, 10 and 15 min**.
3. Do not move the arm or strap between readings.
4. Remove, wait 5 min, re-prep the skin, and repeat (placements 2 and 3).

Report: the **5-minute value** as the headline number, plus the full curve (dry electrodes drop
as sweat builds up).

> This two-electrode measurement gives Z_electrode1 + Z_tissue + Z_electrode2. Halve it as an
> estimate for one electrode. To measure one electrode alone, use a three-electrode setup (an
> extra large gel reference electrode as the current return) — optional, only if needed.

---

## 3. DC offset and drift

1. Same placement as §2 (can run right after the 15-min impedance reading).
2. Measure the DC voltage between the two electrodes with a **high input-impedance** meter
   (≥ 1 GΩ, e.g. the ADS1298 itself at gain 1, which works because the input is DC-coupled,
   or an electrometer-grade DMM). A normal 10 MΩ DMM loads the electrode and gives wrong values.
3. Log for **5 min at rest**. Record the mean, minimum, maximum and drift (mV per minute).
4. **Motion test**: for 60 s, gently tap the electrodes and flex the wrist every 5 s. Record the
   peak-to-peak offset change. This approximates the motion artifact.

Pass: |mean| < 100 mV and rest drift < ~1 mV/min (a starting goal). Record the motion jumps
and compare candidates; there is no hard limit yet.

---

## 4. Mismatch within a bracelet

For candidates that pass §2–3, measure **several electrodes of the same type** (ideally all
positions on one bracelet) and record the spread of |Z| at 10 Hz and 100 Hz. Report the mean, the standard
deviation, and the worst-case difference between paired electrodes (ΔZ).

For CMRR, the mismatch that matters is at **60 Hz**. Mains pickup corrupts readings at exactly
60 Hz, so measure each pair at **40 Hz and 80 Hz** and interpolate. Use the decision rule in
`afe.md` §10.2 to choose the active-electrode design from the median ΔZ.

---

## 5. Repeat matrix

- **Subjects:** at least 3 people (different skin types or hair if possible).
- **Placements:** 3 per subject per electrode type.
- **Baselines every session:** (a) the current Mill-Max gold pogo pins, (b) a standard disposable gel
  Ag/AgCl electrode. Gel should read clearly lower and settle faster than any dry electrode. It's
  a comparison point, not a rig check; the phantom in §0 is the only rig pass/fail.
- **Durability (for a commercial product):** re-test the same electrodes after 500 wipe-and-wear cycles
  and after a sweat or saline soak (e.g. 24 h in artificial sweat). Look for impedance rising,
  offset growing or visible corrosion. Plated parts can wear through to the base metal.

---

## 6. How to interpret mismatch → CMRR

Mains hum appears on both electrodes equally (common-mode). Each electrode's impedance and the
amplifier's common-mode input impedance Z_cm form a voltage divider, so a mismatch ΔZ turns part of the hum into a
fake differential signal:

```
 leaked fraction ≈ ΔZ / Z_cm        effective CMRR ≈ 20·log10(Z_cm / ΔZ)
```

| ΔZ | Z_cm = 1 GΩ | Z_cm = 10 MΩ (pull-up lead-off or bias resistor) |
|---|---|---|
| 10 kΩ | ~100 dB | ~60 dB |
| 50 kΩ | ~86 dB | ~46 dB |
| 200 kΩ | ~74 dB | ~34 dB |

Use current-source lead-off (not pull-up) and right-leg drive to keep this small.

**Our board's actual Z_cm is set by the input filter, not the chip.** The 620 pF to AGND on each
input is about **4.3 MΩ at 60 Hz** (5.1 MΩ at 50 Hz), far below the ADS1298's 1 GΩ. So in practice the
right-hand column (~10 MΩ) is closer to reality than the 1 GΩ column, and ΔZ = 50 kΩ gives roughly
40 dB. The tolerance mismatch of the 620 pF capacitors also converts common-mode hum on its own.

The electrode impedance is in series with the 2 kΩ, so the real RC corner per lead is
f ≈ 1 / (2π·(|Ze| + 2 kΩ)·C), not the 128 kHz you get from 2 kΩ alone. This is the same mechanism as
ADS1298 datasheet Equation 8 (§10.1.3), with the electrode included in R. The formula treats Ze as a
pure resistor, which is the worst case. A real electrode's impedance falls with frequency, so the true
loss is somewhat smaller.

**Proposal (to validate with a common-mode injection test; not decided):** cut the per-lead
capacitor from 620 pF to about **22 pF C0G (≤ 5 %)**, and raise the series R from 2 kΩ to about
**7.5 kΩ (1 %)**. Including the ADS1298's own ~20 pF, that puts the zero-source corner at about
500 kHz, just under the 512 kHz HR-mode modulator rate. (The datasheet line after Eq. 8 says to keep
the bandwidth wide for CMR, with the modulator rate as the upper limit.) The added thermal noise is
about 0.35 µVrms differential over 500 Hz, small next to a dry electrode's own noise. With real
electrodes connected, the electrode impedance pushes the corner down anyway.

Datasheet Eq. 8 also matters on the bench. With the current 2 kΩ / 620 pF, the board's CMR at 60 Hz
is about 100 dB if R and C are 1 %, but about 91 dB with 5 % caps and about 86 dB with 10 % caps. The
schematic doesn't state the 620 pF tolerance.

**Right-leg drive (RLD) is required** for a ≥ 95 dB system target. Its loop gain at 60 Hz is about
N·|Z_f| / 220 kΩ, where N is the number of channel inputs summed (internal 220 kΩ each, datasheet
Fig. 43) and Z_f is the external feedback. With 1 MΩ ∥ 1.5 nF this gives ≈ 24 dB for N = 4 and
≈ 36 dB for N = 16. The rejection of mains interference is roughly the front-end CMRR plus the RLD
loop gain. The design budget conservatively assumes only 20 dB of RLD, so the front end must give
≥ 75 dB for a 95 dB system target. That isn't reachable passively with dry electrodes; see `afe.md`
§7–§9 (active electrodes).

Do **not** add a large differential capacitor across the pair. With dry electrodes its corner,
1/(2π·2|Ze|·C_diff), lands inside the sEMG band. If capacitance has to stay large, the alternative is a
buffer at each electrode (active electrodes).

---

## 7. Data sheet (copy per run)

```
Date / time:            Operator:
Subject ID:             Placement # (1-3):
Electrode type / lot:   Contact area:          Spacing (mm):
Pressure / strap hole:  Temp / RH:
Phantom check passed?   (Y/N, values)
LCR settings:           level ____ mV rms, DC bias OFF, averaging ____, compensation done (Y/N)

t (min) | |Z| 10 Hz | θ 10 Hz | |Z| 100 Hz | θ 100 Hz | |Z| 1 kHz | θ 1 kHz
0       |           |         |            |          |           |
1       |           |         |            |          |           |
2       |           |         |            |          |           |
5       |           |         |            |          |           |
10      |           |         |            |          |           |
15      |           |         |            |          |           |

DC offset rest: mean ____ mV, min ____, max ____, drift ____ mV/min
DC offset motion: peak-to-peak change ____ mV
Notes (sweat, skin redness, slipping, etc.):
```

Save results as CSV next to the run (one row per reading) so they can be plotted and compared.
