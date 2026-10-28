# Regulator architecture evidence — V1.3, 27 October 2026

Analysis/proposal only. No schematic or historical revision was changed. The original F04/F05/F13–F17 findings and later corrections were read first. V1.2 already isolated U4.5/C54.1; F04 must not be reported as a still-present direct U4/U5 output short. R38 still disables both regulators. The main nominal bank is now 240.4 µF, before DevKit capacitance.

## Preferred proposal

Protected conventional 1S cell, assumed 4.2 V maximum pending actual cell specification → input protection/manual OFF and defined undervoltage enable → TPS63802 at 3.400 V → ESP32 assembly and digital interface; separately LT3042 at approximately 3.0 V (2.980 V set point) → **both** ADS1298 analog and digital supplies, with appropriate level translation. Sharing the quiet ADC supply avoids ADC AVDD/DVDD sequencing differences. Preserve all 16 acquisition channels. The quiet rail remains a power proposal; protection/body bias, layout and signal-range qualification remain separate gates.

Raising the principal rail from 3.3 to 3.4 V costs about 3% in power at equal current, and reduces positive transient margin to the ESP32/ADS digital upper limit. It provides useful headroom for a real post-LDO rather than assuming a 3.3-V LDO regulates from 3.3 V. It is permissible only with level translation and exact module/assembly limits verified. Neither converter should ever be tied to a USB-fed regulator output.

## TPS63802 verified source facts

[TI SLVSEU9D](https://www.ti.com/lit/ds/symlink/tps63802.pdf), §§7–10, 12: input 1.3–5.5 V (>1.8 V startup); 2-A rating is explicitly at 3.3-V output and input ≥2.3 V. Pins: EN1, MODE2, AGND3, FB4, PG5, VOUT6, L2=7, GND8, L1=9, VIN10. Use 0.47 µH; 10 µF nominal input (≥4 µF effective), 22 µF nominal output (≥7 µF effective). Output capacitance has no upper limit. FB is 500 mV, ±1% in PWM, input bias ≤100 nA; bottom resistor ≤100 kΩ. EN rising 1.07–1.13 V, falling 0.97–1.03 V; input leakage ≤0.2 µA. Forced PWM permits reverse energy flow. Shutdown load disconnect does not isolate sources during operation. RθJA reference value 81°C/W.

Suggested values: feedback top 58.0 kΩ (56.0 kΩ + 2.00 kΩ), bottom 10.0 kΩ, all 0.1%; 100 kΩ PG pull-up to the main rail; MODE tied high for acquisition initially. TI lists Coilcraft XFL4015-471ME (0.47 µH) in its example. Validate current derating and inductance under startup/current limit, and source the exact part. Do not move the existing 200-µF bank to the quiet LDO by accident. It can remain on the main converter provisionally because there is no output-capacitance upper limit; effective value, startup and placement still need qualification.

Calculated conservative main DC bounds, using ±1% reference, opposing 0.1% resistor tolerances and ±100-nA feedback bias:

- Nominal: 0.5 × (1 + 58/10) = **3.400 V**.
- Minimum: 0.495 × (1 + 57.942/10.010) − 100 nA × 58.058 kΩ = **3.35446 V**.
- Maximum: 0.505 × (1 + 58.058/9.990) + 100 nA × 58.058 kΩ = **3.44567 V**.
- Static positive margin to 3.6 V: **154.3 mV**, before transient overshoot and local wiring effects. The 2-A/3.3-V headline does not constitute a guaranteed 3.4-V/temperature/enclosure load specification: validate the proposed ≤0.75-A load envelope.

Provisional enable divider: top 22.0 kΩ, bottom 10.0 kΩ, 0.1%; manual OFF clamps EN low or disconnects the source. Derived typical falling/rising thresholds are **3.20/3.52 V**. With threshold, resistor and ±0.2-µA leakage bounds, falling **3.095–3.305 V**, rising **3.415–3.625 V**. These wide intervals are not a precision 3.2-V battery cutoff. Choose a separate supervisor/latch if actual cell minimum, droop/rebound or restart requirements demand tighter limits. Converter intrinsic UVLO near 1.25 V is unsuitable as Li-Po discharge protection. Pack protection remains a separate function.

## LT3042 verified source facts

[ADI LT3042 revision B](https://www.analog.com/media/en/technical-documentation/data-sheets/3042fb.pdf), pp.2–4,12–15,18,22: choose LT3042IDD#PBF/IMSE#PBF. IN1/2; EN3; PG4; ILIM5; PGFB6; SET7; GND8/pad11; OUTS9; OUT10. ISET=98–102 µA across stated operating bounds, offset ±2 mV. Low-load dropout maximum is 300 mV full temperature at 1/50-mA test currents (1%-regulation definition). Use ≥4.7 µF effective output, ESR<50 mΩ, ESL<2 nH, Kelvin OUTS connection; input bypass typically 4.7 µF. Typical ground current is approximately 2 mA at 1-mA load; 50-mA table row maximum is 5 mA. Protection blocks output-to-input flow with input grounded, intermediate or open. Output can still discharge to ground through SET/clamp circuitry. Typical 0.8-µVrms noise requires stated capacitance/conditions; it does not predict this board's ADC noise.

Proposed LT3042 connections/values:

- IN1/2 → main3.4, local nominal 10 µF selected for ≥4.7 µF effective.
- EN3 → defined main-power-good qualified enable; do not float. A 100-kΩ pull-up to main with open-drain PG clamping low is a candidate, accounting for EN input current and PG drive.
- SET7 → **29.8 kΩ, 0.1%, low drift**, and 4.7 µF to the local quiet return.
- OUT10 → quiet ADC rail; OUTS9 Kelvin-senses this node at the output capacitor. Local nominal10 µF selected for ≥4.7 µF effective, plus existing distributed ADC decoupling. GND8 and exposed pad11 → continuous common return; join capacitor/SET grounds locally as manufacturer directs.
- ILIM5 → **2.49 kΩ, 1%**, locally Kelvin to ground: about 50 mA typical current limit. The 2.5-kΩ data row is 45–55 mA; this is a rail fault/current limit, not wearer protection.
- PG4 is open collector. PGFB6 → a qualified divider if used to sequence/reset logic; otherwise tie PGFB to IN and leave PG open, per manufacturer. External precision rail monitoring is preferable where guaranteed thresholds matter. Do not assign a guaranteed cutoff using only PGFB's typical input leakage.

Calculated quiet supply bounds: 100 µA ×29.8 kΩ = **2.980 V nominal**; low=98 µA×29.7702 kΩ−2 mV=**2.91548 V**; high=102 µA×29.8298 kΩ+2 mV=**3.04464 V**. Main minimum minus quiet maximum gives **309.8 mV** of static headroom. The source specifies dropout at 1/50-mA points; use 300 mV as a conservative screening value for the proposed ≤20-mA load, and confirm operation across temperature/load and RF steps. Static headroom is close to that conservative bound, so no assertion of guaranteed high PSRR under transients follows. CSET=4.7 µF creates a deliberate slow startup when fast start is disabled (roughly 0.5 s in manufacturer examples). Use qualified rail-good detection, then reset/configure ADCs; do not copy an unrelated startup timer.

With an allocated 20-mA quiet load, pass loss ≈(3.4−2.98)×0.020=8.4 mW; allow another 3.4×0.005=17 mW for a conservative 5-mA ground-current allocation. Total screen≈25.4 mW; DFN34°C/W gives <1°C rise on its reference thermal board. Actual copper and enclosure still govern temperature. This is considerably less thermally demanding than feeding the radio through a SOT23 LDO.

## Alternatives and conditional budgets

| Alternative | Feasibility and tradeoff |
|---|---|
| A: single 3.3-V LDO feeding ESP32 and both ADCs, RC/ferrite analog branches | Few parts and no converter switching, but cannot cover cell discharge below rail+dropout. At 4.2 V, ideal efficiency78.6%; at 3.7 V89.2%. TLV755 DBV500-mA/fulltemperature dropout238 mV implies3.538-V input before tolerances/droop. Existing nominal240.4-µF output bank remains beyond TLV's200-µF stated range until effective C/BOM is qualified. |
| B: independent raw-cell digital and analog LDOs | Improved load isolation and modest analog pass loss; still loses3.3-V regulation near low cell. LP2985 alone cannot supply RF load; new/legacy silicon, ESR and reverse-current rules differ. A1S-cell dual-LDO design needs explicit early cutoff/runtime sacrifice or lower analog supply. |
| C1: single3.3-V buck-boost with damped analog filtering | Full useful discharge window subject to cutoff; simplest converter solution. RF envelope and PFM content couple to ADC supply. RC example2.2Ω with20.2µF givesfc≈3.58kHz and22mVDCdrop at10mA, but does not remove lowfrequencyRF-current envelope. A ferrite needs actual impedance/current/damping modeling. This is a valid lower-component-count fallback requiring ADC-noise measurement. |
| C2: main3.4-V buck-boost and quiet≈3.0-V reverse-protected LDO | Recommended balanced proposal. Most high-current load avoids pass loss; ADC supply/logic isolation and reset qualification add parts. Lower AVDD narrows common-mode range; verify gain/electrode-offset requirements. Higher main setpoint offers postregulator headroom while remaining below3.6V with explicit overshoot budget. |
| Preserve3.3-V analog exactly | Separate low-current buck-boost to3.7/3.8V plus3.3-V analog LDO is feasible and preserves signal headroom, but adds a second switching converter/inductor. Raising the entire RF source then postregulating to3.3 adds avoidable heat/parts. |

Reference existing-regulator facts: local [TLV755P](../../../../docs/datasheets/originals/components/TLV755P.pdf) and [LP2985](../../../../docs/datasheets/originals/components/LP2985.pdf), plus prior review4.5–4.7. TLV755P DBV RθJA231.1°C/W gives104°C rise at(4.2−3.3)×0.5=0.45W. This is a reference-board screen, not measured overheating. USB-fed voltage on its disabled output can cause discharge loading and output-above-input stress; R38 does not isolate it.

Own budget examples, **85% efficiency assumed for conservative calculation**, not a guaranteed converter minimum:

| Main output current | Main power at3.4V | Battery current at3.0V | Converter total loss | 81°C/W all-loss-in-IC screen |
|---:|---:|---:|---:|---:|
|150mA|0.510W|0.200A|0.090W|7.3°C|
|250mA|0.850W|0.333A|0.150W|12.2°C|
|400mA|1.360W|0.533A|0.240W|19.4°C|
|550mA|1.870W|0.733A|0.330W|26.7°C|
|750mA reserve|2.550W|1.000A|0.450W|36.5°C|

At90% efficiency and250mA average: main0.85W, battery3.7V current0.255A, loss0.094W. Runtime remains usable batteryWh / measured battery-averageW. Firmware sampling/radio duty, moduleSKU, DevKit loads, cell capacity/ESR/temperature and enclosure are unspecified. Bulk-capacitor step estimate is ΔV≈ΔIΔt/Ceff+ΔI×ESR; 300mA for50µs with100µF means150mV before ESR and converter response. This shows why a capacitor label alone cannot establish a5% transient result. Converter, capacitor and load-path measurements must set final values.

TPS7A2030 is attractive for7-µV typical noise and low IQ, but it has VIN+0.3-V output absolute bound and limited reverse current; abrupt main collapse can leave charged analog output above input. TPS7A37 similarly requires EN low before input removal for reverse blocking and needs VOUT+0.5V for its accuracy table. LT3042 is preferred here because its documented intrinsic reverse-input behavior avoids that normal power-removal weakness, with a small radio-relative current overhead. These are design tradeoffs, not measured failures of the earlier circuit.
