# Analog Front End (AFE): Electrodes, Input Network and CMRR

**Status:** working design notes, 2026-11-16. Nothing in this document has been measured on skin
yet. Numbers marked *(model)* are calculations, *(est.)* are engineering estimates, and anything
with a link comes from that source.

**Scope:** everything between the skin and the ADS1298's digital output. That covers the dry
electrodes, the electrode–skin interface, the passive input network, right-leg drive (RLD), common-mode
rejection (CMRR) and the proposed active electrodes.

---

## Contents
1. [Summary: decisions and open items](#1-summary-decisions-and-open-items)
2. [The system as it is today](#2-the-system-as-it-is-today)
3. [Requirements](#3-requirements)
4. [Background concepts (read this first if new to AFEs)](#4-background-concepts)
5. [Electrodes: materials, comparison and decision](#5-electrodes-materials-comparison-and-decision)
6. [The input filter problem](#6-the-input-filter-problem)
7. [CMRR: where it goes and the budget](#7-cmrr-where-it-goes-and-the-budget)
8. [Solutions](#8-solutions)
9. [Active electrodes with a driven guard (detailed)](#9-active-electrodes-with-a-driven-guard-detailed)
10. [Test procedures](#10-test-procedures)
11. [Step-by-step plan](#11-step-by-step-plan)
12. [Corrections made along the way](#12-corrections-made-along-the-way)
13. [Open questions](#13-open-questions)
14. [Related files](#14-related-files)
15. [References](#15-references)

---

## 1. Summary: decisions and open items

**Decisions so far**

| Topic | Decision | Why (details in section) |
|---|---|---|
| Electrode material for the product | **316L stainless steel, CNC-turned** dome | Proven in a cleared reusable EMG product. Cheapest at our volume. No material-cost problem (§5) |
| Lab reference electrode | Sintered Ag/AgCl discs (a few, bought retail) | Best-behaved electrochemically. A known baseline to compare against (§5) |
| Rejected for now | Solid silver (metal alone > $1/electrode); MIM (tooling cost); sintered Ag/AgCl for production (10–40× over budget) | §5.4 |
| Right-leg drive (RLD) | **Will be connected.** Designed assuming only 20 dB of loop gain | §7.3 |
| CMRR target | **≥ 95 dB at 60 Hz, system level (with RLD)** → the front end must give ≥ 75 dB on its own | §7 |
| Leading CMRR solution | **Active electrodes (buffer per electrode) with a driven guard** | Only option that passes with dry electrodes (§8, §9) |
| ADS1298 mode | High-resolution (HR) mode, 512 kHz modulator, gain 6, VREF 2.4 V (from firmware) | §2 |

**What is still open:** the real electrode-to-electrode mismatch on skin. It decides between a simple
buffer and a harder bootstrapped one. Also open: the electrode size versus the existing sleeve modules,
and the questions in §13.

---

## 2. The system as it is today

```
 skin ─┬─ electrode P ── cable ── R 2 kΩ ──┬── INxP ─┐
       │                                   C 620 pF   │  ADS1298 (×2 chips = 16 channels)
       │                                   │ AGND     ├─ PGA (gain 6) ─ ΔΣ modulator ─ digital filter ─ 24-bit data ─ ESP32-S3
       └─ electrode N ── cable ── R 2 kΩ ──┬── INxN ─┘
                                           C 620 pF
                                           │ AGND
 RLD / reference electrode ── (V1: not connected)
```

- **Board:** `open-semg-16-v1`, two ADS1298 ADCs giving 16 differential channels.
- **Electrode connectors:** E1–E16, one two-pin connector per channel: P and N. Each 3D-printed
  "sleeve sensor module" holds one channel's electrode pair. 33 electrodes per bracelet =
  16 pairs + (presumably) one RLD/reference electrode. *(See §13.)*
- **Input network per lead:** 2 kΩ series resistor (R1–R32), then 620 pF from the ADC pin to
  analog ground (C1–C32). Tolerance and dielectric of the 620 pF are not stated in the schematic.
  There is no series blocking capacitor, so the input is **DC-coupled**: the electrode's DC offset
  reaches the ADC.
- **RLD:** in V1 the RLD pins (RLDOUT, RLDINV, RLDREF) are **unconnected**
  (`v1.connectivity.txt`), and the firmware writes `CONFIG3 = 0xC0`, which leaves the RLD
  amplifier powered down. V0 had RLD feedback of 1 MΩ ∥ 1.5 nF.
- **Firmware settings** (`Firmware/Clamshell Testing/host/clamshell/ads1298.py`): gain 6,
  HR mode (bit 7 of CONFIG1), internal reference 2.4 V (CONFIG3 = 0xC0).
- **Current electrodes:** Mill-Max gold-over-nickel spring pins 0859-0-15-20-82-14-11-0 and
  0871-0-57-20-82-14-11-0, held in sleeve bores of 3.2 mm and 4.8 mm
  (`3D-prints/README.md`).
- **Unrelated but blocking:** the Ambrflow audit found supply-wiring errors on both board revisions
  (e.g. V1 AVDD tied to AGND). These must be fixed before any AFE measurement means anything.
  See `audits/ambrflow-v0-v1-20261028/`.

---

## 3. Requirements

| Requirement | Value | How it must be specified to be testable |
|---|---|---|
| Skin–electrode impedance | < 100 kΩ | At **100 Hz** (and report 10 Hz, 500 Hz, 1 kHz), after **5 min** on skin, at a stated pressure and contact area. sEMG lives at 20–500 Hz, so 10 Hz alone is misleading |
| DC offset between a pair | < 100 mV | At rest after 5 min. Borrowed from the gel ECG electrode standard ANSI/AAMI EC12. There is no dry-electrode standard |
| CMRR | ≥ 95 dB at 60 Hz | System level, **with RLD**, with a stated electrode imbalance (e.g. 51 kΩ ∥ 47 nF, see §10.3). Add 50 Hz if selling outside North America |
| Electrodes per bracelet | 33 | |
| Electrode cost | ≤ $1 each | Clarify whether this includes the spring/mount (§13) |
| Life | Reusable, ~2 years in a commercial product | Needs a wear and sweat-soak test (§10.2) |
| "Medical grade" | Means signal quality is not compromised | Not regulatory clearance. Skin safety still matters (§5.6) |

---

## 4. Background concepts

This section explains the terms used in the rest of the document. Skip what you already know.

### 4.1 Impedance, magnitude and phase
**Impedance (Z)** is "resistance for AC signals". A resistor has the same impedance at every
frequency. A **capacitor's impedance falls as frequency rises**: Z_C = 1 / (2π·f·C). For example,
620 pF is 4.3 MΩ at 60 Hz but only 2 kΩ at 128 kHz.

Impedance is a complex number, with a **magnitude |Z|** (in ohms) and a **phase θ** (in degrees):
- A pure resistor has θ = 0°.
- A pure capacitor has θ = −90°.
- Anything built from resistors and capacitors only, like an electrode on skin, **must have a
  phase between 0° and −90°**. A phase outside that range means the measurement is wrong. This is how we
  knew the earlier LCR readings were bad.

### 4.2 The electrode–skin interface
Where a metal touches skin, the electrical behaviour is modelled as:

```
 metal ──[ R_s ]──┬──[ R_p ]──┬── body
                  └──[ C_p ]──┘
```
- **R_p** (parallel resistance): how hard it is for DC current to cross the interface. It's high
  for dry contacts (hundreds of kΩ to many MΩ) and low with gel.
- **C_p** (parallel capacitance): the interface stores charge like a capacitor, in the "double layer"
  at the metal surface and in the skin's outer dead layer, the stratum corneum. Larger contact area
  means more C_p.
- **R_s** (series resistance): the body tissue and sweat, small (hundreds of Ω to a few kΩ).

So the impedance is **high at low frequency** (dominated by R_p) and **falls at higher
frequency** (C_p bypasses R_p). Dry electrodes start high and fall over 5–20 minutes as sweat
builds up under them. Impedance scales roughly with **1/contact area**.

### 4.3 Half-cell potential, DC offset and polarization
Any metal in contact with an electrolyte (sweat) develops a small built-in voltage, the
**half-cell potential**. Two electrodes of the *same* material mostly cancel each other. Small differences
between them show up as a **DC offset** between the pair (tens of mV is common).

- **Non-polarizable electrodes** (Ag/AgCl): the chemistry lets charge cross the interface
  freely, so the half-cell potential is stable. Low drift, low motion artifact.
- **Polarizable electrodes** (gold, platinum, stainless steel): charge mostly piles up at the
  surface instead of crossing it. When the electrode moves, that charge layer is disturbed and the
  voltage jumps. That jump is the **motion artifact**.

The DC offset matters because our input is DC-coupled. At gain 6 with VREF 2.4 V, the ADS1298
accepts a differential input of **±VREF/gain = ±400 mV**, so a 100 mV offset fits comfortably. Drift and
jumps still show up as baseline wander.

### 4.4 Differential and common-mode signals
Each channel measures two electrodes, P and N.
- The **differential signal** is V_P − V_N. That's the EMG we want (µV to a few mV).
- The **common-mode signal** is (V_P + V_N)/2, the part both electrodes share. The main source is
  **mains hum**: the body acts as an antenna and picks up 50/60 Hz from wiring, often at
  volts-level relative to the circuit.

An ideal differential amplifier ignores common-mode completely. A real one converts a tiny
fraction of it into a fake differential signal.

### 4.5 CMRR and decibels
**CMRR** (common-mode rejection ratio) is how strongly the system suppresses common-mode
relative to differential signals:

```
 CMRR = 20 · log10( V_common-mode / V_fake-differential )   [dB]
```

Every 20 dB is a factor of 10. **95 dB ≈ a factor of 56,000.** So 1 V of hum on the body would
appear as about 18 µV of fake EMG. 75 dB is a factor of 5,600, and 40 dB is a factor of 100.

**System CMRR is limited by its weakest contributor, not its best.** The ADS1298 chip alone has
105 dB minimum, but the electrodes and input network in front of it usually dominate (§7).

### 4.6 Input impedance, input capacitance and input bias current
These three describe how an amplifier input "loads" whatever drives it:

- **Input impedance:** how much the input draws from the source. Higher is better. The ADS1298 lists
  1000 MΩ at DC with no lead-off, 500 MΩ with current-source lead-off, and **10 MΩ with
  pull-up lead-off** (lead-off is explained in §4.8).
- **Input capacitance:** every input pin has some capacitance to its surroundings. The ADS1298
  datasheet lists **20 pF** per input. There are two kinds:
  - **Common-mode (CM) capacitance:** from each input to ground or the supplies. This is what
    hurts CMRR, because each electrode's impedance forms a voltage divider with it (§7.1).
  - **Differential capacitance:** between the two inputs of a pair. It filters the wanted signal.
  - The ADS1298 datasheet doesn't say which kind its 20 pF is. This matters, and it can be
    measured (§10.3).
- **Input bias current:** a tiny DC current that flows into or out of an amplifier input pin,
  from transistor gates, leakage and protection diodes. It has to flow through the electrode, so it
  creates an extra DC voltage: **V = I_bias × Z_electrode**.
  - ADS1298: ±200 pA typical at 25 °C, ±1 nA max over 0–70 °C. Through 1 MΩ, 200 pA gives
    0.2 mV, which is harmless.
  - Lead-off detection injects a deliberate 6–24 nA. Through 1 MΩ, that's 6–24 mV of offset.
  - For active-electrode op-amps we want **picoamps**, because dry electrodes can be 10 MΩ+ at DC.

### 4.7 Noise from resistors
Every resistor generates thermal noise: e_n = √(4·k·T·R), in nV/√Hz. Multiply by √(bandwidth) for
the rms value. Over a 500 Hz sEMG band:

| Resistance | Noise density | rms over 500 Hz |
|---|---|---|
| 2 kΩ | 5.8 nV/√Hz | 0.13 µV |
| 7.5 kΩ | 11.1 nV/√Hz | 0.25 µV |
| 100 kΩ | 40.7 nV/√Hz | 0.91 µV |
| 1 MΩ | 129 nV/√Hz | 2.9 µV |

For comparison, the ADS1298 itself is 4 µV peak-to-peak (roughly 0.6–0.7 µV rms) over 150 Hz at
gain 6. Small series resistors on the board don't matter. The electrode's own resistance and the
electrode–skin interface usually dominate (Huigen et al. 2002 found most electrode noise comes
from the interface).

### 4.8 ADS1298 essentials
- **PGA:** programmable-gain amplifier, gain 1–12. We use 6.
- **ΔΣ modulator:** samples the input very fast, at the **modulator rate**: 512 kHz in HR mode,
  256 kHz in low-power (LP) mode. A digital filter then produces our 1–2 kSPS output. Because of
  this, the analog anti-aliasing filter only has to remove signals near the modulator rate. A single
  RC is enough (datasheet §10.1.3).
- **Lead-off detection:** the chip pushes a small DC current (6–24 nA, "current source") or a
  10 MΩ pull resistor into each input. If the electrode is off, the input drifts to a rail and the chip
  flags it. Pull-up mode drops input impedance to 10 MΩ, so it's bad for CMRR.
- **RLD (right-leg drive):** an on-chip amplifier that senses the common-mode voltage of selected
  inputs and drives the body (through one extra electrode) with the inverted version. This pushes the hum
  on the body down by the **loop gain**. Details in §7.3.

---

## 5. Electrodes: materials, comparison and decision

### 5.1 Why the current pogo-pin measurements were unreliable
- **Setup:** the LCR readings (100 kΩ–1 MΩ) came with phases outside 0° to −90°, which is
  physically impossible. The setup was wrong. Common causes: a 1 V default test level (it polarizes the
  electrode), DC bias left on, no open/short compensation, test frequency too high or too close to mains,
  and the electrodes' own DC voltage upsetting the meter. The checklist is in the protocol, §0.3.
- **Small contact:** the pins are 3.2–4.8 mm across, so contact area is small. Small changes in
  angle or pressure cause large swings.
- **Gold is polarizable** (§4.3), so its offset drifts with pressure and movement.
- **Gold over nickel:** nickel plating is porous. Sweat can corrode through pores, and worn gold
  exposes nickel, an allergen.

### 5.2 What the research says
*(Summary. The paper-by-paper table with sizes, offsets, impedances and drift is in §5.10.)*
- **Material differences on dry skin are modest, and studies disagree.**
  - A 2019 study rated dry Ag/AgCl about 3× better than the stainless steel common in wearables.
  - A 2024 *Scientific Reports* ECG study found stainless steel had the highest SNR at rest
    (platinum was best during movement).
  - Neither was an sEMG study.
- **sEMG specifically:** Rodrigues et al. 2020 compared 16 mm 316 stainless discs with gel
  Ag/AgCl on the biceps. Stainless impedance was "of the same order of magnitude" as Ag/AgCl, and signal
  quality was close (median SNR at 20 % effort: Ag/AgCl 19.2 dB vs 18.3 dB for Ti-coated
  stainless). Recordings were short (10 s), and DC offset was not reported.
- **Area matters more than metal.** Huigen et al. 2002 found electrode noise ∝ 1/√area. That was
  with gel; applying it to dry electrodes is our extrapolation.
- **Pressure and settling time** strongly affect dry-electrode impedance (Kusche et al.,
  bioimpedance).
- **No study runs longer than days.** The 2-year question can only be answered by our own
  durability test.

### 5.3 Comparison of candidate materials

| | 316L stainless | Sintered Ag/AgCl | Fine silver (99.9 %) | Gold-plated (current) |
|---|---|---|---|---|
| Signal quality, dry | Close to gel Ag/AgCl in one sEMG study | Best in theory (non-polarizable) | Good: used by Delsys Trigno research sensors | OK, but polarizable |
| Offset / motion stability | Worse (polarizable) | Best | Middle *(est.)* | Worse |
| 2-year durability | Strong precedent (Coapt FDA-cleared reusable 316L dome) | Unknown. Brittle, porous, AgCl depletes *(est.)* | Unknown. Soft, tarnishes | Plating wears; nickel pores corrode |
| Skin safety | Very low nickel release if low-sulfur (316L/304/430 all < 0.03 µg/cm²/week vs the EU limit of 0.5) | Fine | Silver allergy exists (Delsys warns) | Nickel exposure if worn |
| Cost per electrode | Material ≈ $0.03; machining needs a quote | $11–42 retail; volume needs a quote | Metal alone $1.9–2.4 at spot | — |
| Verdict | **Product** | **Lab reference** | Too expensive solid | Replace |

### 5.4 Cost arithmetic (why silver and MIM are out)
- **Silver** at ≈ $49.5/troy oz ≈ $1.59/g (Nov 2026):
  - A Ø6 × 4 mm part is 113 mm³ × 10.49 g/cm³ ≈ 1.19 g ≈ **$1.89 of metal**.
  - A 6 × 6 × 4 mm part is ≈ 1.51 g ≈ **$2.40**.
  - Retail stock is about $3.95/g (Otto Frei rod).
  - This fails the $1 budget before any machining.
- **MIM (metal injection molding):** one vendor quotes **$50k–100k tooling**. Over 1,000 bracelets
  (33,000 parts), that's **$1.50–3.00 per part for tooling alone**. Worth revisiting only at several
  thousand bracelets per year.
- **316L turned from rod:** 1/4" 316 rod costs $5.57 per 48" (Speedy Metals). At about 6 mm used per
  part, that's ≈ **$0.03 of material**. Machining dominates the cost and needs a quote.
- **Sintered Ag/AgCl:** I found no stock to machine. It's pressed from powder into finished shapes.
  Retail discs cost $10.93 (Neurospec) up to about $42.

**Stock forms:**
- Round domes are **turned from rod** on a lathe.
- **Sheet** is for flat discs (laser-cut or punched) or **stamped** domes, which need a die.
- **MIM** uses powder.
- If a shop makes the parts, it supplies certified material. Buy rod yourself only for hand-made
  prototypes.

### 5.5 Why not sintered Ag/AgCl for the product?
It isn't ruled out. In order of how solid the evidence is:
1. **Price** is the only barrier we've verified: 10–40× over budget at retail. A Wuhan Greentek
   volume quote could change this.
2. **Its advantage on dry skin is thin.** Its strength is a stable interface with *gel*. On dry
   skin, the skin itself dominates, and the head-to-head evidence is mixed (§5.2).
3. **Durability is unknown** (brittle, porous, AgCl gets used up) *(est.)*.
4. **Precedent:** commercial reusable dry EMG products use 316L (Coapt) or silver (Delsys).

If a quote comes in near budget **and** our tests show clearly less motion artifact than 316L, choose
Ag/AgCl.

### 5.6 Other commercial considerations
- **Use one material everywhere.** All 33 electrodes, including RLD, should be the same material.
  Different metals give a fixed DC offset between electrodes and corrode where they touch in sweat
  (galvanic corrosion). Keep the spring or stud behind the electrode sealed from sweat.
- **Biocompatibility:** expect cytotoxicity (ISO 10993-5), sensitization (ISO 10993-10) and
  irritation testing. ISO 10993-1:2025 counts each calendar day of wear as a "contact day", so a
  daily-worn bracelet is long-term contact. EU skin-contact metals must pass **EN 1811** nickel
  release.
- **Material certificates** for every lot. Specify 316L in writing. **Never accept 303**, the
  free-machining grade with high sulfur and worse corrosion and nickel behaviour.
- **Surface finish:** passivated or electropolished. Finish changes nickel release even for the
  same alloy.
- **Pogo-pin mechanism life:** sweat getting into the barrel and the spring's cycle rating can
  limit life as much as the contact surface does.

### 5.7 The chosen electrode design (draft)
Files are in `electrode-characteristics/316L-dome-electrode/`.

| Feature | Value | Reason |
|---|---|---|
| Head | Ø6.0 × 4.0 mm | Round is cheaper to turn than square and has no corners |
| Top | Spherical dome, radius 9 mm (center rises 0.51 mm) | Pushes into the skin with even pressure |
| Edge | 0.5 mm round | Comfort |
| Back | M2 × 0.4 stud, 4 mm, thread runout ≤ 0.8 mm allowed | Stainless doesn't solder with normal flux, so it mounts mechanically |
| Material | 316L with mill certificate; implant-grade (ASTM F138) optional | §5.6 |
| Finish | Passivated or electropolished, skin face Ra ≤ 0.8 µm | §5.6 |
| Tolerance | ±0.1 mm general | Tighter costs more |

**Size limits:**
- **SENIAM** (the European sEMG guideline) says ≤ 10 mm along the muscle fibers and ≤ 20 mm
  between the two electrodes of a pair.
- **Pitch limits width:** pitch = circumference ÷ electrodes per ring. On a 160 mm wrist, 16 per
  ring gives a 10 mm pitch (Ø8 fits); 32 per ring gives 5 mm (only about Ø4 fits).
- **Bigger is quieter:** if Huigen's √area rule carries over to dry electrodes, Ø8 would be about
  25 % quieter than Ø6.
- **Fit problem:** a Ø6 head **does not fit** the existing sleeve bores (3.2 / 4.8 mm). The head
  diameter and stud are one-line changes in `make_electrode.py` (§13).

### 5.8 Expected mismatch between two 316L electrodes
I found no published measurement of dry-electrode mismatch. This is reasoning only:
- **From area:** 16 mm stainless discs are about 10 kΩ at higher frequency (Rodrigues 2020). Our
  Ø6 dome has ≥ 7× less face area, and less still in actual contact, so expect **tens to hundreds of kΩ
  per electrode at 60 Hz**, highest in the first minutes.
- **Mismatch** is driven mostly by skin and pressure, not metal. Plan for **ΔZ ≈ 20–50 % of |Z|**,
  and worse if an electrode sits poorly *(est.)*.
- **Planning range:** ΔZ ≈ 20 kΩ to a few hundred kΩ at 60 Hz. **This must be measured** (§10.2).
- **What reduces it:** equal spring force, more contact area, a few minutes of settling, and a
  consistent surface finish.

### 5.9 Making electrodes in-house: cost and time (2026-11-18)
Rough estimates for building electrodes ourselves in Montreal, using North American suppliers.
*(est.)* marks my estimates; everything else comes from a listing in §15. Prices are USD.

**Summary**

| Route | Material per electrode | Hands-on time | All-in at 3,300 (excluding labour) |
|---|---|---|---|
| 316L from sheet, DIY | $0.01–0.05 | 3–5 min *(est.)* | **$0.20–0.50** |
| 316L blanks, etched or stamped (outsourced) | cents | ≈ 0 | quote needed; probably lowest at volume |
| Sintered Ag/AgCl, homemade | $0.85–2.00 | 3–5 min *(est.)* | **$1.50–3.20** |

At 3–5 minutes each, labour dominates both routes: at $20/h it adds $1.00–1.70 per electrode.
**316L sheet is the only homemade route that can stay near $1 all-in.**

#### 316L from sheet
Sheet gives a different part from the turned dome in §5.7: a **0.5–0.6 mm flat or pressed-dome
disc with a welded lead or tab**. A dome pressed from sheet is a hollow cap.

*Route 1, do it yourself (70–500 pieces):*
1. **Buy sheet:** 316, 0.018–0.036" (0.46–0.91 mm), 12" × 12": $15.59 (Zoro) or $16.07 (Speedy
   Metals). McMaster-Carr sells 0.02" 316 with a material certificate (2317K303), and Metal Supermarkets
   lists 24 ga 316 (priced per store). One sheet gives over 1,000 Ø6–8 mm discs, so material is
   ≈ $0.01–0.05 each.
2. **Cut discs** with a jewelry disc cutter (6 and 8 mm sizes exist). Cutters are rated for soft
   metals up to about 18–20 ga, so **stainless is at or past their limit**: test before buying many.
3. **Press the dome** in a dapping block with a small shop press.
4. **Attach the lead** by spot-welding a 316 wire or tab to the back *(est.)*. A capacitor-discharge
   stud welder can put M3 studs on thin sheet but costs $2,700–5,800.
5. **Deburr**, then **passivate** in a citric-acid batch.

Tools, one-time: ≈ $500–1,500 (disc cutter, dapping block, small press, spot welder) *(est.)*.
Labour: about 3–5 min per electrode → 165–275 h for 3,300.

*Route 2, outsource the blanks (3,300 and up):*
- **Photochemical etching** is priced per sheet area, with cheap optical tooling. An older figure is
  about $0.15–0.20 per in² for steel up to 0.020", roughly cents per Ø8 mm disc. Suppliers:
  Fotofab, Tech-Etch.
- **SendCutSend** laser-cuts 316, but only 0.060" (1.5 mm) and thicker, with a minimum part of
  0.25" × 0.375". Too thick to dome, but usable for a flat Ø10 mm disc.
- **Forming domes at volume:** Montreal-area stampers include Tripar Inc., Laval Poinçon et Matrice
  and Hyperforme. Stamping typically pays off only at about 10,000+ parts.

#### Sintered Ag/AgCl, homemade
**Recipe** (RSC Advances 2017): Ag and AgCl powder mixed 1:1, pressed into 2 mm pellets at 10 MPa with a
silver wire embedded, sintered at **400 ± 10 °C under nitrogen**. A thesis used 380–430 °C for
1–3 h in vacuum. Stay well below 455 °C, where AgCl melts.
- **Force is small:** 10 MPa on a Ø6 mm die is about 283 N (29 kg). A proper pellet die matters
  more than press size.

**Materials per pellet.** Assumes a 50/50 mix by weight sintered to 80 % density (5.8 g/cm³), with
Ag powder at $4.75/g (Thermo, 50 g) and AgCl at $7.31/g (Sigma, 100 g, 99 %):

| Pellet | Mass | Ag | AgCl | Total |
|---|---|---|---|---|
| Ø6 × 2 mm | 0.33 g | $0.78 | $1.20 | ≈ $2.00 plus silver wire |
| Ø4.5 × 1.5 mm | 0.14 g | $0.33 | $0.50 | ≈ $0.85 plus silver wire |

Bulk silver powder (about $2/g wholesale) would roughly halve the silver part. Canadian Fisher prices
are about 2× the US ones.

**Equipment, one-time (≈ $2,000–4,000):**
- muffle furnace: MTI KSL-1100X-S, $1,288;
- 12-ton pellet press: MSE, $1,825. A cheaper arbor press would also work *(est.)*;
- pellet die, 0.001 g scale and nitrogen: ≈ $300–800 *(est.)*.

**Time:** about 3–5 min hands-on per pellet to weigh, fill, press, eject and fit the wire *(est.)*.
Sintering runs in unattended batches of about 4–6 hours.

| Quantity | Equipment share | + Materials | ≈ Total (excluding labour) |
|---|---|---|---|
| 70 | $29–57 | $0.85–2 | $30–60. Buying retail ($11–19) is cheaper |
| 500 | $4–8 | $0.85–2 | $5–10 |
| 3,300 | $0.60–1.20 | $0.85–2 | $1.50–3.20, plus 165–275 h |

**Risks:**
- batch-to-batch consistency of DC offset and drift: test every batch with the protocol;
- breathing silver powder: wear a mask;
- AgCl's sensitivity to light.

**North American commercial makers for comparison:** BioMed Products (Fair Oaks, CA; offers custom
shapes), In Vivo Metric (Healdsburg, CA), and Cortech Solutions (distributor). BESDATA and Greentek are in China.
Quote status is tracked in `electrode-characteristics/quote_requests.md`.

**When homemade Ag/AgCl makes sense:** only if our tests show clearly less motion artifact than 316L
**and** the Greentek or BioMed quotes come back expensive.

### 5.10 Literature review: stainless/316L, dry Ag/AgCl and sintered Ag/AgCl (2026-11-18)

**How to read this table**
- **NR** = not reported in what we could read.
- **Evidence:** *Full text* = we read the paper's text. *Abstract* = abstract or a search summary of it only.
  *Vendor* = a manufacturer's own specification.
- **"Offset" and "drift" mean two different things** (see §4.3):
  - **Offset** is the DC voltage between two electrodes of a pair.
  - **Drift (polarization over time)** is how that voltage changes over minutes or hours.
- **Impedance numbers are only comparable at the same frequency and settling time.** Most papers
  report neither drift nor offset for dry electrodes on skin.

#### A. Stainless steel (including 316 / 316L)

| Material | Paper | Size | DC offset | Skin–electrode impedance | Polarization / drift over time | Other notes | Evidence |
|---|---|---|---|---|---|---|---|
| 316 stainless, bare and Ti-film-coated; vs gel Ag/AgCl | Rodrigues et al. 2020, *Materials* 13:2135 | Ø16 mm discs, 1.0 mm thick | NR | "Same order of magnitude" as the gel Ag/AgCl reference, which tended to about 10 kΩ at higher frequency (measured 10–1000 Hz) | NR (recordings only 10 s) | **sEMG**, biceps. Median SNR at 20 % effort: Ag/AgCl 19.2 dB vs Ti-coated stainless 18.3 dB (from a summary of the table; verify). The authors note stainless is common in consumer dry electrodes | Full text (partly) |
| Stainless steel (plus platinum, silver, conductive polymer, fabrics) | *Sci. Rep.* 2024, "ECG signal quality in intermittent long-term dry electrode recordings with controlled motion artifacts" | NR | NR | Stainless had the **lowest impedance of the solid materials after 10 min** | NR | ECG. Stainless gave the **best SNR at rest**; platinum was best during movement, stainless second | Abstract |
| Stainless steel (vs disposable wet electrodes) | "The electrical characteristics of some commercial ECG electrodes" (PubMed 621452) | NR | Wet electrodes: median 0.5–4 mV | Wet electrodes: median 1.5–3.25 kΩ | **100 nA DC through stainless → about 0.5 V of polarization in about 25 min** | Classic evidence that stainless polarizes badly under DC current | Abstract |
| Stainless steel, silver, dry AgCl, polyurethane | EMBC 2017, "Performance assessment of dry electrodes for wearable long term cardiac rhythm monitoring: skin-electrode impedance spectroscopy" | NR | NR | **500 kΩ – 1 MΩ** across 1–100 Hz for all four dry types | NR | ECG. Conclusions favoured dry AgCl for trace quality | Abstract |
| Stainless steel vs Ag/AgCl-plated polymer and others (6 dry types, 1 gel) | Popović Maneski et al. 2020, *Biomed. Eng./Biomed. Tech.* 65:405 | NR | Analysed ("junction potentials"); values NR | NR | NR | ECG, 30 s real-life recordings. Overall, dry Ag/AgCl about **3× better than stainless**, the material typical in wearables | Abstract |
| Stainless steel (plus gold, carbon rubber, metallized textile) vs Ag/AgCl hydrogel | Kusche et al. 2019, arXiv 1910.05033 | Same contact area for all types (value NR) | NR | Dry impedance can reach hydrogel levels **or lower** with the right frequency, pressure and contact time; abstract gives no values | NR | Bioimpedance, not biopotential | Abstract |
| Stainless-steel spring probes (with Au, Cu, BeCu) | Liao et al. 2011, *Sensors* 11:5819 (via Fu et al. 2020 review) | 17 spring probes | NR | NR (the review's table cell for this row repeats another paper's text) | NR | EEG. Correlation with wet electrodes 95.26 % (forehead), 91.47 % (top of head) | Review table |

#### B. Dry Ag/AgCl (coated, plated, printed or chlorided; not sintered)

| Material | Paper | Size | DC offset | Skin–electrode impedance | Polarization / drift over time | Other notes | Evidence |
|---|---|---|---|---|---|---|---|
| Ag/AgCl on 99.99 % Ag made three ways: bleach, electroplating, cured ink | Lee et al. 2022, *Front. Electron.* 2:700363 | Bullet shape on 10-gauge Ag wire; contact area NR | NR | Forearm, 3-electrode EIS (time after application NR). **~10 Hz:** bleach 6.2 MΩ, electroplated 6.5 MΩ, ink 4.0 MΩ (gel 0.15 MΩ). **~100 Hz:** 1.7 / 1.9 / 0.89 MΩ (gel 0.033 MΩ) | NR | ECG and EEG (ASSR). Correlation with wet ECG: 75.5 / 84.5 / 90.7 %. Ink performed best. 3 subjects. In 1 M saline the same electrodes were tens to hundreds of Ω, so skin dominates | Full text |
| Dry Ag foil, partly chlorided; dry Ag/AgCl; vs gel Ag/AgCl | Gruetzmann et al. 2007, *Physiol. Meas.* 28:1375 | Ø2 cm, 0.3 mm silver foil | NR. The authors built a passive filter network to suppress slow offset fluctuations | Values only in a figure (axis up to 1,200 kΩ). **Dry Ag/AgCl had the highest impedance of all**: "the chloride isolates in dry condition." In 0.9 % NaCl, Ag/AgCl was lower than gel | NR numerically | ECG. Dry silver showed **less motion artifact** than gel electrodes, consistent with Searle & Kirkup 2000 | Full text |
| One dry electrode (material NR in abstract) vs wet Ag/AgCl vs insulating | Searle & Kirkup 2000, *Physiol. Meas.* 21:271 | NR | NR | NR in abstract | Motion artifact: dry worse at the start of trials; by the end, dry was **8.2 dB lower than wet** | Interference on dry electrodes 40 dB lower than wet | Abstract |
| *Reference, wet Ag/AgCl:* gel electrodes | Chi et al. 2010, *IEEE Rev. Biomed. Eng.* 3:106 | NR | — | Values in a table image (not extractable) | **1/f-like low-frequency drift of the Ag/AgCl offset** (half-cell mismatch) confirmed in 1-hour recordings | Wet Ag/AgCl was the only type noisier than its thermal-noise prediction at low frequency | Full text |

#### C. Sintered Ag/AgCl

| Material | Paper / source | Size | DC offset | Skin–electrode impedance | Polarization / drift over time | Other notes | Evidence |
|---|---|---|---|---|---|---|---|
| Reusable sintered Ag/AgCl (vs 5 other reusable types, 6 disposable Ag/AgCl, 9 gels) | Tallgren et al. 2005, *Clin. Neurophysiol.* 116:799 | NR | Values NR in abstract | NR | **Best DC stability** of all reusable types; others showed polarization, baseline drift and low-frequency noise | Slow-EEG (DC) recording, **with gel**. 7 of 9 gels contained enough chloride, "a prerequisite for DC stability" of Ag/AgCl. So the advantage depends on an electrolyte | Abstract |
| Sintered Ag/AgCl discs EC-DC-AGD8 / AGD24 | Cortech Solutions product page; same figures in a Harvard Apparatus pellet datasheet | Ø8 × 1 mm and Ø24 × 1 mm | **180 µV** between a matched pair | NR | **25 µV/h** | Measured **in 0.9 % saline**, not on skin. Noise 1 µVpp (0.1–1 kHz) | Vendor |
| BESDATA pre-wired sintered AgCl | Shenzhen Besdata Technology (MedicalExpo listing) | Disc or pillar (sizes NR) | **≤ 150 µV** | ≤ 25 Ω·cm² at 10 Hz (in electrolyte, not skin) | **≤ 25 µV/h** | Vendor, test conditions not stated | Vendor |
| Sintered Ag/AgCl **used dry on skin** | — | — | — | — | — | **No published measurement found** of offset, drift or impedance | — |

#### What this means for us
1. **Nobody we found has measured DC offset or drift for 316L or sintered Ag/AgCl used dry on skin.**
   Our protocol (§10, `electrode_testing_protocol.md` §3) would produce exactly that data. That is a
   real gap, and could be part of the paper's contribution.
2. **Sintered Ag/AgCl's famous figures (≈ 150–180 µV offset, 25 µV/h drift) are measured in saline.**
   On dry skin the skin itself dominates (Lee 2022; Gruetzmann 2007), and Tallgren ties the DC stability
   to a chloride electrolyte. Expect the dry advantage over 316L to be **smaller than the datasheets
   suggest**, which is consistent with the mixed head-to-head results in §5.2.
3. **Thin Ag/AgCl coatings used dry can be worse than bare metal.** The chloride layer insulates when
   dry (Gruetzmann), and coated dry Ag/AgCl measured 4–6.5 MΩ at 10 Hz (Lee). Avoid coated or plated
   Ag/AgCl for a dry, two-year product.
4. **Stainless steel polarizes under DC current** (about 0.5 V after 25 min at 100 nA). Design
   implications:
   - **don't use DC lead-off current injection** (6–24 nA) on 316L electrodes;
   - keep any DC current through them to picoamps (buffer bias current is fine, §9.4);
   - prefer AC or firmware-based lead-off detection.
5. **Dry impedance on skin is typically 0.5–6 MΩ at 10 Hz and falls with frequency, area and settling
   time.** Large stainless discs (16 mm) can approach gel levels. This supports the 100 Hz impedance
   spec in §3 and the active-electrode plan in §9.

---

## 6. The input filter problem

### 6.1 What the filter was meant to do
The 2 kΩ + 620 pF on each lead is an **anti-aliasing low-pass filter**: it should remove signals near
the ADS1298's modulator rate before they get sampled. The design intent was a corner at
**256 kHz**, the LP-mode modulator rate. Three issues with that:
1. The values actually give 1/(2π·2 kΩ·620 pF) = **128.4 kHz**, not 256 kHz (the audit agrees).
2. A corner placed *at* the modulator rate only attenuates by 3 dB there.
3. The firmware runs **HR mode**, where the modulator rate is **512 kHz**.

### 6.2 What was missing from the calculation
f = 1/(2π·R·C) is correct, but **R must be everything between the signal source and the
capacitor**:
- With a signal generator (≈ 0 Ω output), R = 2 kΩ.
- With an electrode on skin, **R = Z_electrode + 2 kΩ**, and Z_electrode is 50–500× larger than
  2 kΩ.

```
 skin ──[ Z_electrode ]──[ 2 kΩ ]──┬── ADS1298 input
                                   = 620 pF
                                   │ AGND
```

| Source impedance (treated as a resistor) | Corner frequency |
|---|---|
| 0 Ω (signal generator) | **128.4 kHz**: the design value |
| 100 kΩ | **2.5 kHz** (kilohertz) |
| 1 MΩ | **256 Hz**: inside the 20–500 Hz sEMG band |

This is the worst case. A real electrode's impedance falls with frequency (§4.2), so the actual
loss is smaller. Using an R ∥ C electrode model *(illustrative values)*:

| Electrode model | Signal kept at 250 Hz, 620 pF | Signal kept at 250 Hz, 47 pF |
|---|---|---|
| Gel-like (R_p 20 kΩ ∥ C_p 50 nF) | 99 % | 100 % |
| Good dry (200 kΩ ∥ 10 nF) | 95 % | 100 % |
| Poor dry (1 MΩ ∥ 1 nF) | **68 %** | 97 % |

### 6.3 Why it also damages CMRR
If the two electrodes of a pair have different impedances, each lead gets a **different filter
corner**. Mains hum, which is identical on both leads, then comes out slightly different on P and N,
and that difference looks like EMG. The ADS1298 datasheet describes exactly this in §10.1.3,
Equation 8:

```
 CMR ≈ 20·log10( δR/R + δC/C ) + 20·log10( f / f_C )
```

δR/R and δC/C are the relative mismatches between the two leads, and f_C is the filter corner. With
electrodes connected, the electrode itself is part of R. Its mismatch is large (tens of %), and it
drags f_C down. Both terms get worse.

### 6.4 Bench-only CMRR of the current filter (no electrodes)
Applying Eq. 8 to 2 kΩ / 620 pF at 60 Hz, with 1 % resistors:

| 620 pF tolerance | Board CMR at 60 Hz |
|---|---|
| 1 % | 100.6 dB |
| 5 % | 91.0 dB |
| 10 % (typical X7R ceramic) | 85.8 dB |

The schematic only says "620pF". **If these are 5–10 % X7R parts, the board fails 95 dB even on the
bench.** Use **C0G/NP0** capacitors: they're stable, low-tolerance and don't change value with voltage
the way X7R does.

### 6.5 What to do about the filter
- **If staying passive (no active electrodes):** reduce each per-lead capacitor to about **22 pF C0G
  (≤ 5 %)** and raise R to about **7.5 kΩ (1 %)**.
  - With the chip's own 20 pF, the generator-source corner is 1/(2π·7.5 kΩ·42 pF) ≈ **505 kHz**,
    just under the 512 kHz HR modulator rate. The datasheet says to keep this bandwidth wide for CMR,
    with the modulator rate as the upper limit.
  - The added noise is about 0.35 µV rms differential, which is negligible.
  - **This helps but is not enough on its own** (§7.4).
- **If using active electrodes (recommended):** the buffers drive the filter from a low
  impedance, so the filter behaves as designed. It can stay at 2 kΩ / 620 pF, **but with C0G
  1–5 %** parts.
- **Never add a large capacitor across the pair** (a "differential capacitor") with passive dry
  electrodes. Its corner is 1/(2π·2·Z_electrode·C), which lands in the sEMG band.

---

## 7. CMRR: where it goes and the budget

### 7.1 The mechanism: two voltage dividers
Each lead sees its electrode impedance (Z_e) in series with the CM input impedance (Z_cm, mostly
capacitance to ground: the 620 pF plus the chip's 20 pF). Hum on the body is divided down by each
lead's divider:

```
 body hum ──[ Z_e,P ]──┬── INxP        body hum ──[ Z_e,N ]──┬── INxN
                      Z_cm                                  Z_cm
                       │                                     │
                      GND                                   GND
```

If Z_e,P ≠ Z_e,N, the two inputs get slightly different amounts of hum. The fake differential signal
is roughly:

```
 V_fake / V_cm ≈ ΔZ / Z_cm         →    front-end CMRR ≈ 20·log10( Z_cm / ΔZ )
```

where ΔZ = |Z_e,P − Z_e,N| at 60 Hz, and Z_cm = 1/(2π·60 Hz·C_cm). **More Z_cm (less
capacitance) and less ΔZ both help.**

Z_cm at 60 Hz for the capacitances discussed:

| C_cm per lead | What it is | Z_cm at 60 Hz |
|---|---|---|
| 640 pF | Current 620 pF filter cap + 20 pF chip input | 4.1 MΩ |
| 42 pF | Proposed 22 pF + 20 pF chip | 63 MΩ |
| 20 pF | Chip input alone, no external cap | 133 MΩ |
| 3–5 pF | Op-amp buffer input (active electrode) | 0.53–0.88 GΩ |
| ~1 pF | Buffer + driven guard / bootstrapping | 2.7 GΩ |

### 7.2 Where the "51 kΩ ∥ 47 nF" comes from
ECG standards and the ADS1298 datasheet model a **bad electrode** as 51 kΩ in parallel with 47 nF,
placed in **one** lead to create a known imbalance. At 60 Hz that network is |Z| ≈ **37.8 kΩ**. It
represents a gel-electrode-level mismatch. Dry electrodes are likely worse, so we also evaluate
100 kΩ and 200 kΩ.

### 7.3 Right-leg drive (RLD)
RLD senses the hum and drives the body with the opposite signal through the RLD electrode, shrinking
the hum itself. **Hum reaching the inputs is reduced by (1 + loop gain).** To first order:

```
 system CMRR [dB] ≈ front-end CMRR [dB] + RLD loop gain [dB]
```

**Loop gain at 60 Hz** ≈ N · |Z_f| / 220 kΩ:
- N is the number of channel inputs summed (each through an internal 220 kΩ, datasheet Fig. 43).
- Z_f is the external feedback network between RLDOUT and RLDINV.

| Feedback Z_f | N = 4 | N = 16 |
|---|---|---|
| 1 MΩ ∥ 1.5 nF (V0 values, |Z_f| ≈ 0.87 MΩ) | 24.5 dB | 36.2 dB |
| 10 MΩ ∥ 150 pF (same pole, 10× gain; untested) | 44 dB | 56 dB |

**Design assumption: 20 dB.** We plan with this conservative figure, taken from the datasheet. More
gain is possible with more inputs or more feedback, but loop stability must then be verified. RLD
also needs:
- one dedicated electrode (the 33rd);
- a current-limiting resistor in its output for patient safety (check the IEC 60601-1 patient
  current limits);
- `PD_RLD` enabled in CONFIG3.

With two ADS1298s, the datasheet says to **power down all but one RLD amplifier**. Our reading is that
the sum nodes (RLDINV) of both chips are tied together so one amplifier sums all inputs. Confirm
against TI's EVM before relying on it.

### 7.4 The budget with 20 dB of RLD
95 dB − 20 dB means the **front end must give ≥ 75 dB on its own**. That caps the CM capacitance
per lead:

| Electrode mismatch ΔZ at 60 Hz | Required Z_cm | Max C_cm per lead |
|---|---|---|
| 37.8 kΩ (gel-level test) | ≥ 213 MΩ | **≤ 12.5 pF** |
| 100 kΩ | ≥ 562 MΩ | **≤ 4.7 pF** |
| 200 kΩ (realistic dry) | ≥ 1.1 GΩ | **≤ 2.4 pF** |

The chip alone is 20 pF, so **no passive version of the input can pass with dry electrodes**.
System CMRR *(model)*, 20 dB of RLD included:

| Front end | ΔZ 38 kΩ | 100 kΩ | 200 kΩ |
|---|---|---|---|
| Current 620 pF | 61 ✗ | 52 ✗ | 46 ✗ |
| 22 pF external | 84 ✗ | 76 ✗ | 70 ✗ |
| No external cap (chip's 20 pF) | 91 ✗ | 83 ✗ | 76 ✗ |
| No external cap, *if* chip CM is only 5 pF | 103 ✓ | 94.5 ✗ | 89 ✗ |
| Active electrode, 3 pF | **107 ✓** | **99 ✓** | 93 ✗ |
| Active electrode, 4 pF (OPA2333) | **105 ✓** | **96 ✓** | 90 ✗ |
| Active electrode + guard/bootstrap, 1 pF | **117 ✓** | **109 ✓** | **103 ✓** |

Model assumptions: one electrode carries the whole mismatch, RLD adds directly in dB, the chip's
20 pF is matched between inputs, and the RLD electrode's own impedance is ignored. The largest
mismatch a passive, cap-free input tolerates is **≈ 24 kΩ**.

---

## 8. Solutions

In order of importance:

1. **Connect RLD.** Required in every scenario. It gives 20 dB in our budget, and more is possible.
   With active electrodes it's also what holds the electrode inputs at a defined voltage (§9.4).
2. **Fix the input capacitors.** Use C0G at 1–5 %. If staying passive, also switch to
   7.5 kΩ / 22 pF (§6.5). Necessary, but not sufficient with dry electrodes.
3. **Active electrodes with a driven guard.** The only route that passes 95 dB at realistic dry
   mismatch (§9).
4. **Supply bootstrapping.** Only if measured ΔZ is ≥ ~150–200 kΩ. It brings buffer capacitance
   below 1 pF (an IEEE Access 2023 design reached 191 fF) but adds parts and design risk.
5. **Reduce the mismatch at the source:** equal pressure, larger contact, settling time (§5.8).
6. **Avoid pull-up lead-off.** It drops input impedance to 10 MΩ. Use current-source lead-off, or
   none.

A digital 60 Hz notch filter can clean up the data afterwards, but it doesn't improve CMRR. It also
removes real EMG energy at 60 Hz.

---

## 9. Active electrodes with a driven guard (detailed)

### 9.1 The idea
Put a **unity-gain buffer** (an op-amp voltage follower) directly behind each signal electrode.
A follower outputs exactly its input voltage, but it can drive cables and filters without drawing
current from the electrode. It's an **impedance converter**, not an amplifier.

**The ADS1298 still sees a bipolar, differential signal.** Each module buffers P and N separately,
and the chip still measures P − N. Nothing changes in firmware gain or channel setup.

### 9.2 Circuit per sensor module (one channel = two electrodes)
```
                      guard ring (copper around input pad, both layers)
                      ┌───────────────────────────────┐
 electrode P ── R_prot ──┤+ \                           │
                       │   >── U1A ──┬── R_iso ── cable ── E-connector ── 2 kΩ ── INxP
                    ┌──┤- /          │
                    └────────────────┘ (output tied to − input, and to the guard)

 electrode N ──  same with U1B  ──────────────────────── cable ───────── 2 kΩ ── INxN

 +3.3 VA ── 100 nF ── GND   (op-amp supply decoupling, at the op-amp)
```

| Part | Value (starting point) | Purpose |
|---|---|---|
| U1 | Dual op-amp (see §9.3) | Two followers, one per electrode |
| R_prot | 10–47 kΩ, inside the guard | Limits ESD and fault current into the op-amp input. Its noise (13–28 nV/√Hz) is similar to the op-amp's |
| R_iso | 100–470 Ω | Isolates the cable's capacitance from the op-amp output so it doesn't oscillate |
| Decoupling | 100 nF C0G/X7R at the supply pin | Local energy for the op-amp |
| Guard | Copper ring around the input pad and trace, on both layers, connected to the output | Removes stray capacitance (§9.5) |
| ESD diode (optional) | Low-capacitance TVS | Adds 0.5–1 pF, which counts against the budget |

### 9.3 Choosing the op-amp
Requirements: low CM input capacitance (≤ 3–5 pF), bias current in picoamps, rail-to-rail input
on a single 3.3 V supply, low noise in 20–500 Hz, and low supply current (32 of them).

| Op-amp (dual) | CM input capacitance | Bias current | Supply current per ch | Notes |
|---|---|---|---|---|
| **OPA2333** | 4 pF (2 pF differential) | very low (CMOS) | **17 µA** | Zero-drift. Lowest power. Check chopper noise in band |
| TLV9002 | ~5 pF (from a TI design example, not the spec table) | 5 pA typ | 60 µA | Cheap and common. Marginal on capacitance |
| LTC6241 | ~3 pF (ambiguous table; 0.5 pF differential) | very low | higher (not checked) | Used for active electrodes in the literature. $0.90–3.16 depending on quantity |

Prices for OPA2333 and TLV9002 weren't found. Get quotes. **Verify every value against the current
datasheet before committing.**

### 9.4 The DC path ("bias") for the inputs
An op-amp input needs a defined DC voltage. In this design, **RLD holds the body at mid-supply**
(about 1.65 V on a 3.3 V supply). Each electrode input then sits at body voltage ± its half-cell offset.
The op-amp's bias current (pA) flows through the electrode's R_p: 5 pA × 10 MΩ = 50 µV, which is
harmless.

- **Without RLD, the inputs float and drift to a rail**, so RLD is mandatory here.
- **Don't add a normal bias resistor** to ground or mid-supply. A 10 MΩ resistor would wreck the
  Z_cm we just built. If one is needed for recovery after lift-off, it must be ≥ 1 GΩ or bootstrapped.

### 9.5 The driven guard and bootstrapping, explained
Any copper near the input trace forms a small capacitor with it. Capacitance only draws current
when there is **voltage across it**. The guard ring is connected to the buffer output, which carries
the same voltage as the input, so the voltage across that stray capacitance is ≈ 0 and it draws
≈ no current. Effectively the capacitance disappears. This is **bootstrapping**: making the
"other side" of a capacitor follow the signal.

- **The guard removes PCB stray capacitance**, but not the op-amp's own CM input capacitance (from
  the input pin to its supply rails and substrate). That's the 3–5 pF floor.
- **Supply bootstrapping** also makes the op-amp's supply rails follow the signal (AC-wise), which
  takes the floor below 1 pF (191 fF in IEEE Access 2023). It costs more parts and more design effort.
  A simpler two-wire bootstrapped design reported 32 % less input capacitance (PMC6833060).
- In a follower, the differential capacitance between the + and − inputs is automatically
  bootstrapped, because both inputs carry the same voltage. Only the CM part matters.

### 9.6 What else changes
- **Wiring:** each module goes from 2 wires (P, N) to 4 (P, N, +3.3 VA, GND). The E1–E16
  connectors become 4-pin, and the main board supplies the analog rail to the modules.
- **Mechanics:** a small PCB (about 8 × 12 mm) inside each sleeve module. The electrode stud or pin
  mounts directly to it, so the input trace is millimetres long. The module needs sealing against
  sweat.
- **Lead-off detection:** the ADS1298's lead-off currents can't reach the electrodes through the
  buffers. Detect a lifted electrode in firmware instead: the buffer output drifts toward a rail.
- **The input filter** on the main board can stay as is, but switch to C0G 1–5 % (§6.5).
- **Cleanliness:** at picoamp currents, flux residue leaks. Use no-clean flux plus a wash, or a
  conformal coat that keeps the electrode face clear.

### 9.7 Cost and power *(est.)*
| Item | Per module (2 electrodes) |
|---|---|
| Dual op-amp | $0.30–3 |
| PCB + assembly at volume | $0.20–1 |
| Passives | a few cents |
| Extra connector and wires | $0.20–0.50 |
| **Total** | **≈ $1–3 → ≈ $15–50 per bracelet (16 modules)** |

Supply current for 32 buffers: about 0.5 mA (OPA2333) to about 2 mA (TLV9002).

**Verdict:** cheap in parts and simple in circuit. Most of the work is the module PCB, sleeve CAD
changes and wiring. It passes 95 dB up to about **100 kΩ mismatch**. Beyond that, supply
bootstrapping or more RLD gain is needed.

---

## 10. Test procedures

### 10.1 Electrode impedance and offset
The full procedure is in **`electrode_testing_protocol.md`**. In short:
1. **Validate the rig** on a resistor–capacitor "skin phantom" (1 kΩ + 100 kΩ ∥ 47 nF). Expected
   values: 96.9 kΩ / −16.3° at 10 Hz, 32.4 kΩ / −69.6° at 100 Hz, 3.6 kΩ / −71.8° at 1 kHz.
   Pass: within ±5 % and ±3°, with phase always between 0° and −90°.
2. **LCR settings:** ≤ 50 mV test level, DC bias off, open/short compensation with the real cables,
   low frequencies, average readings. If the meter can't do this, use the function-generator +
   1 MΩ series-resistor method (protocol §0.4).
3. **Impedance on skin:** readings at 0, 1, 2, 5, 10 and 15 min, at 10 Hz / 100 Hz / 1 kHz, with
   fixed site, pressure and skin prep.
4. **DC offset:** a ≥ 1 GΩ meter, or the ADS1298 at gain 1 (DC-coupled). 5 min at rest, then a
   60 s tap-and-flex motion test.
5. **Repeat matrix:** ≥ 3 people × 3 placements. Baselines every session: current gold pins and a gel
   Ag/AgCl electrode.
6. **Safety:** battery-powered or isolated instruments only when a person is connected, and test
   currents ≤ 10 µA.

### 10.2 Electrode mismatch (decides the active-electrode design)
1. Same setup as §10.1, at the 5-minute mark.
2. Measure each electrode pair at **40 Hz and 80 Hz** and interpolate to 60 Hz. Don't measure *at*
   60 Hz, because mains pickup corrupts it.
3. Record |Z| and ΔZ = |Z_P − Z_N| for every pair, across ≥ 3 people.
4. **Decision rule:**
   - median ΔZ < 50 kΩ → simple buffer (§9);
   - 50–100 kΩ → buffer with a ≤ 3–4 pF op-amp and a careful guard;
   - > 100 kΩ → plan supply bootstrapping or more RLD gain.
5. **Durability:** repeat after about 500 wear-and-wipe cycles and a 24 h artificial-sweat soak.

### 10.3 Bench CMRR test (no person; follows TI app note SBAA188)
Purpose: measure the board's real common-mode rejection, and find out whether the ADS1298's 20 pF
behaves as CM capacitance.

1. Power the board from battery. Use a function generator whose ground connects to the board's AGND.
2. Generator: **60 Hz sine, about 1 V peak-to-peak, with a DC offset at mid-supply** (≈ 1.65 V).
   This keeps the inputs within the chip's common-mode range.
3. At the channel's electrode connector (so the board's 2 kΩ / 620 pF network is included), connect the
   generator to **both** pins: directly to one pin, and through **51 kΩ ∥ 47 nF** to the other
   (the imbalance).
4. Record the channel and read the 60 Hz amplitude in an FFT. Divide by the gain to get it
   input-referred.
5. **CMRR = 20·log10(V_generator / V_60Hz,input-referred).**
6. Repeat with the imbalance in the other lead, with no imbalance (board only, which checks Eq. 8 and
   the cap tolerance), and on one channel with its 620 pF caps removed. That last one shows how much
   CM capacitance the chip itself contributes.
7. **With RLD:** build a "body" node, connect the RLD output to it through an electrode-like network,
   connect the inputs to it through the electrode/imbalance networks, and couple the generator in
   through a small capacitor (a few hundred pF). Measure the 60 Hz amplitude on the body node with RLD
   off and on. Their ratio is the RLD loop gain. Then measure the channel output as in step 4.
   (ECG standards define a similar test; follow the specific one you'll claim compliance with.)

---

## 11. Step-by-step plan

1. **Fix the board-level supply errors** found in the Ambrflow audit. Nothing analog is meaningful
   until AVDD/DVDD are correct.
2. **Reconnect RLD** in the schematic: feedback network, RLD electrode output with a
   current-limiting resistor, both chips' sum nodes, and firmware `PD_RLD` on.
3. **Change the input capacitors** to C0G, 1–5 %.
4. **Run the bench CMRR test** (§10.3) with and without the caps on one channel, and with RLD.
5. **Fix the impedance rig** and validate it on the phantom (§10.1).
6. **Prototype electrodes:**
   - 316 stainless snap studs for quick tests;
   - a few sintered Ag/AgCl discs as reference;
   - get CNC quotes for `electrode_316L_dome.step` (Xometry, Hubs) once the size is settled (§13).
7. **Measure impedance, offset and mismatch on skin** (§10.1, §10.2).
8. **Choose the active-electrode variant** using the §10.2 decision rule. Hand-build 2–3 modules
   (OPA2333 or LTC6241, guard ring) and repeat the CMRR test with them.
9. **Durability and skin-safety** tests on the final electrode (§5.6, §10.2).
10. **Volume decisions:** a Greentek quote for Ag/AgCl if motion artifact is a problem; MIM only at
    several thousand bracelets per year.

---

## 12. Corrections made along the way
Recorded so earlier statements in the chat don't cause confusion:

| Earlier statement | Correction |
|---|---|
| Tip "0.5 cm radius", so area isn't the issue | The pins are 3.2–4.8 mm across (`3D-prints/README.md`). Area *is* a lever |
| 304 stainless releases more nickel than 316L | Low-sulfur 304, 316L and 430 all release very little. Sulfur (e.g. 303) is the problem |
| Machined 316L is "realistically ≤ $1" | Unverified until quoted |
| Add a large capacitor across the pair | Wrong for dry electrodes: it creates an in-band low-pass (§6.5) |
| Raise R to 12–26 kΩ with 47–100 pF | Superseded by 7.5 kΩ / 22 pF (passive), or keep 2 kΩ / 620 pF C0G (active) |
| "2.5 kHz" was read as 2.5 Hz | The corner is 2.5 kHz at 100 kΩ (§6.2) |
| Silver as a "credible second option" | Fails $1 on metal cost alone |

---

## 13. Open questions
1. **Bracelet layout:** wrist or forearm circumference, electrodes per ring, the spacing between the
   two electrodes of a pair, and whether the 33rd electrode is the RLD electrode.
2. **Electrode mounting:** how should the electrode attach to the sleeve module (and to the
   active-electrode PCB)? The Ø6 head doesn't fit the 3.2 / 4.8 mm bores.
3. **Budget scope:** does "$1 per electrode" include the spring or mount, or only the contact?
4. **Volume:** expected bracelets per year (CNC vs MIM, quote quantities).
5. **The 620 pF capacitors:** tolerance and dielectric on the BOM.
6. **RLD 20 dB:** confirm which datasheet section it comes from. With the V0 parts and 16 inputs
   we calculated about 36 dB, which would loosen every budget by 16 dB.
7. **95 dB definition:** with RLD? With which imbalance? 50 Hz as well?
8. **ADS1298 20 pF:** common-mode or differential? Answered by the §10.3 test.

---

## 14. Related files

| File | What it is |
|---|---|
| `electrode_testing_protocol.md` | Step-by-step electrode impedance, offset and mismatch test |
| `electrode-characteristics/316L-dome-electrode/make_electrode.py` | Parametric CAD script. Run: `uv run --python 3.11 --with cadquery --with matplotlib python make_electrode.py` |
| `electrode-characteristics/316L-dome-electrode/electrode_316L_dome.step` | 3D model for CNC quotes |
| `electrode-characteristics/316L-dome-electrode/electrode_316L_dome.stl` | Mesh for 3D-printed fit checks |
| `electrode-characteristics/316L-dome-electrode/electrode_316L_dome_drawing.pdf` / `.png` | Dimensioned drawing with material and finish notes |
| `electrode-characteristics/0859-…`, `0871-…` | Placeholders for the current Mill-Max pins |
| `electrode-characteristics/quote_requests.md` | Supplier quote tracker: who was contacted, how, status, and the request templates |
| `3D-prints/README.md` and Fusion files | Sleeve sensor modules (bores for the current pins) |
| `audits/ambrflow-v0-v1-20261028/AMBRFLOW_DETAILED_AUDIT.md` | Board audit: input filter values, RLD state, supply errors |
| `audits/ambrflow-v0-v1-20261028/EVIDENCE/v1.connectivity.txt` | Netlist: RLD pins unconnected, E1–E16 connectors |
| `audits/ambrflow-v0-v1-20261028/EVIDENCE/adc_findings.md` | 2 kΩ / 620 pF networks, supply findings |
| `docs/datasheets/processed/components/ADS1298_llamaparse.md` | ADS1298 datasheet (input specs, Eq. 8 in §10.1.3, RLD Fig. 43) |
| `Firmware/Clamshell Testing/host/clamshell/ads1298.py` | Register settings (gain 6, HR mode, CONFIG3) |
| `Firmware/Clamshell Testing/firmware/src/ads1298.h` | Register map |

---

## 15. References

**Electrode science**
- Rodrigues et al. 2020, dry titanium / stainless sEMG electrodes — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7254203/
- Huigen, Peper, Grimbergen 2002, origin of surface-electrode noise — https://link.springer.com/doi/10.1007/BF02344216
- Properties of different types of dry electrodes (2019) — https://www.degruyterbrill.com/document/doi/10.1515/bmt-2019-0167
- ECG signal quality in long-term dry electrode recordings (2024) — https://www.nature.com/articles/s41598-024-56595-0
- Kusche et al., dry electrodes for bioimpedance — https://arxiv.org/abs/1910.05033
- Ag/AgCl dry electrodes for wearables — https://www.frontiersin.org/journals/electronics/articles/10.3389/felec.2021.700363/epub

**Products and precedents**
- Coapt Dome Electrode, FDA 510(k) K190416 (316L) — https://www.accessdata.fda.gov/cdrh_docs/pdf19/K190416.pdf
- Delsys Trigno manual (99.9 % silver contacts) — https://www.manualslib.com/manual/1552575/Delsys-Trigno.html?page=16
- BIOPAC reusable sintered Ag/AgCl — https://biopac.com/product-category/research/electrodes/ag-agcl-reusable
- Neurospec sintered Ag/AgCl disk — https://shop.neurospec.com/sintered-disk-electrode
- Wuhan Greentek (sintered Ag/AgCl, quote) — https://greenteksensor.en.alibaba.com/productgrouplist-807422043/Sintered_Ag_AgCl_Electrodes.html
- Speedy Metals 1/4" 316 rod — https://www.speedymetals.com/p-2614-14-rd-316-stainless-steel-cold-finished-annealed.aspx
- OnlineMetals 316/316L rod — https://www.onlinemetals.com/en/buy/stainless-steel/0-25-stainless-round-bar-precision-ground-316-316l/pid/27640
- Xometry stainless CNC — https://www.xometry.com/material-cnc-machining-metal-stainless-steel
- Hubs stainless CNC — https://www.hubs.com/cnc-machining/metal/stainless-steel/
- Sailrite DOT 316 stainless snap stud — https://www.sailrite.com/Sailrite-Snap-Fastener-Cloth-to-Cloth-Stud-Stainless-Steel
- Otto Frei fine silver wire — https://www.ottofrei.com/products/fine-silver-round-wire-half-hard-999-6-30-gauge-12in-harmony
- Silver price (JM Bullion) — https://www.jmbullion.com/charts/silver-prices/
- MIM tooling cost (vendor claim) — https://milwaukeeprec.com/metal-injection-molding-alternative.html

**Literature review (§5.10)**
- Lee et al. 2022, Characterization of Ag/AgCl dry electrodes, *Front. Electron.* — https://www.frontiersin.org/journals/electronics/articles/10.3389/felec.2021.700363/full
- Gruetzmann et al. 2007, Novel dry electrodes for ECG monitoring, *Physiol. Meas.* — https://people.ece.cornell.edu/land/courses/ece5030/labs/s2014/Gruetzmann_PhysMea_2007.pdf
- Chi, Jung, Cauwenberghs 2010, Dry-contact and noncontact biopotential electrodes, *IEEE RBME* — https://isn.ucsd.edu/pub/papers/rbme10.pdf
- Searle & Kirkup 2000, Direct comparison of wet, dry and insulating electrodes — https://data.zhenzhi.com/details/1/906648898
- Tallgren et al. 2005, Electrodes and gels for slow EEG potentials — https://data.zhenzhi.com/details/1/890708853
- Popović Maneski et al. 2020, Properties of different types of dry electrodes — https://www.degruyterbrill.com/document/doi/10.1515/bmt-2019-0167
- EMBC 2017, Dry electrodes for long-term cardiac rhythm monitoring, impedance spectroscopy — https://doi.org/10.1109/embc.2017.8037209
- The electrical characteristics of some commercial ECG electrodes (PubMed 621452) — https://pubmed.ncbi.nlm.nih.gov/621452/
- Fu et al. 2020, Dry electrodes for human bioelectrical signal monitoring (review) — https://pmc.ncbi.nlm.nih.gov/articles/PMC7374322/
- Harvard Apparatus Ag-AgCl electrode datasheet (180 µV, 25 µV/h in saline) — https://www.harvardapparatus.com/media/harvard/pdf/W3_7_313.pdf
- Cortech EC-DC-AGD24 sintered disc — https://cortechsolutions.com/product/ec-dc-agd24/
- BESDATA sintered AgCl (MedicalExpo) — https://www.medicalexpo.com/prod/shenzhen-besdata-technology/product-301554-1024332.html

**In-house manufacturing (§5.9)**
- Sintered Ag/AgCl recipe, 1:1, 10 MPa, 400 °C under N₂ (RSC Advances 2017) — https://pubs.rsc.org/en/content/articlehtml/2017/ra/c7ra05532c
- Powder processing of sintered Ag/AgCl neural electrodes (SDSU thesis) — https://digitallibrary.sdsu.edu/islandora/object/sdsu:1507
- Thermo Scientific silver powder, 50 g — https://thermofisher.com/order/catalog/product/041598.18
- Sigma-Aldrich silver chloride 99 %, 227927 — https://sigmaaldrich.com/NZ/en/product/sigald/227927
- Bulk silver powder price indicator — https://www.metal.com/en/prices/202112230002
- MTI KSL-1100X-S muffle furnace — https://mtixtl.com/products/ksl-1100x-s-ul-ld
- MSE 12-ton manual pellet press — https://www.msesupplies.com/products/lab-scale-12-ton-manual-hydraulic-pellet-press
- Zoro 316 sheet, 0.018", 12" × 12" — https://www.zoro.com/zoro-select-ss-sheet-316-12-in-overall-w-78641212/i/G305848663/
- Speedy Metals 20 ga 316 sheet — https://speedymetals.com/p-942-20ga-0036-316-stainless-steel-cold-rolled-annealed-2b-finish.aspx
- McMaster-Carr stainless sheet — https://mcmaster.com/products/stainless-steel-sheet-stock
- Metal Supermarkets 316 sheet — https://www.metalsupermarkets.com/product/stainless-steel-sheet-316/
- Disc cutter ratings (Ganoksin) — https://www.ganoksin.com/best-disc-cutter-reviews/
- IWT LYNX4 CD stud welder — https://weldingmart.com/products/iwt-lynx4-modular-5-16-capacity-capacitor-discharge-stud-welding-system-1-iwt500054m4
- Pro Weld CD-212 stud welder — https://www.zoro.com/pro-weld-cd-212-stud-welder-capacitor-discharge-single-phase-14-ga-14-in-range-cd-212/i/G9986986
- SendCutSend 316 limits — https://sendcutsend.com/stainless-steel-316
- Photochemical machining costs — https://en.wikipedia.org/wiki/Photochemical_machining
- Fotofab precision etching — https://fotofab.com/services/etching/precision-chemical-etching/
- Stamping volume threshold (The Fabricator) — https://www.thefabricator.com/stampingjournal/article/stamping/ask-the-stamping-expert-how-do-metal-formers-stamp-the-unstampable
- Tripar Inc. (Montreal) — https://axya.co/suppliers_directory/company/tripar-inc
- Laval Poinçon et Matrice — https://axya.co/suppliers_directory/company/laval-poincon-et-matrice
- Hyperforme — https://www.groupehyperforme.com/en/industrial-subcontracting/metal/metal-stamping-services/
- In Vivo Metric — https://medicregister.com/In_Vivo_Metric/Supplier/sid12626.htm

**Standards and safety**
- Nickel release from stainless steels — https://pubmed.ncbi.nlm.nih.gov/9330816
- ANSI/AAMI EC12 limits table — https://pmc.ncbi.nlm.nih.gov/articles/PMC6556171/table/Tab2
- ISO 10993-1:2025 changes — https://advisera.com/articles/iso-10993-1-2025-what-has-changed/
- FDA biocompatibility basics — https://www.fda.gov/medical-devices/biocompatibility-assessment-resource-center/basics-biocompatibility-information-needed-assessment-fda
- SENIAM recommendations summary — https://pmc.ncbi.nlm.nih.gov/articles/PMC8587451
- Gold-plating porosity — https://www.electronicsonline.net.au/content/components/news/porosity-real-world-concerns-1380085348

**Circuits and active electrodes**
- TI ADS1298 datasheet (SBAS459) — https://www.ti.com/lit/ds/symlink/ads1298.pdf (local copy in `docs/`)
- TI SBAA188, improving CMR with the right-leg drive amplifier (referenced by the ADS1298 datasheet)
- Ultra-high input impedance buffer for dry electrodes (IEEE Access 2023) — https://doaj.org/article/fc58c2828c7248ef8a842930220bdc63
- Bootstrapped two-wire dry electrode — https://pmc.ncbi.nlm.nih.gov/articles/PMC6833060
- Low-bias LTC624x active electrode — https://pmc.ncbi.nlm.nih.gov/articles/PMC5371775
- OPA2333 datasheet — https://www.ti.com/document-viewer/OPA2333/datasheet/specifications
- TLV9002 datasheet — https://www.ti.com/lit/gpn/TLV9002
- LTC6241 (Analog Devices article) — https://www.analog.com/en/resources/technical-articles/fast-cmos-op-amp-challenges-bipolar-amps-on-all-key-specs.html
