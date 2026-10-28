# Focused regulator implementation check

27 October 2026. Analysis only; no schematic changes. This check addresses the proposed converter/post-regulator blocker, rather than reopening the whole architecture.

## Decision

**Permit schematic implementation of a controlled bench prototype with the small MAIN-setpoint correction below. Do not describe the original 3.40 V / 2.98 V pair as a qualified regulation design.** Its positive 9.8 mV calculation excludes resistor drift and is almost entirely consumed by plausible selected-part drift. This is a narrow design margin, not evidence that a built circuit has failed or that ADC absolute limits would be violated. Bench power-up and release remain separate decisions.

**Recommended smallest correction:** retain TPS63802 and LT3042, keep AFE at 2.98 V nominal, and change MAIN to **3.440 V nominal**. Use converter FB top = **56.0 kΩ + 2.80 kΩ**, bottom = **10.0 kΩ**, each **0.1%, ≤10 ppm/°C**. Keep LT3042 RSET = **29.8 kΩ, 0.1%, ≤10 ppm/°C**. This preserves the planned ADC voltage and interface architecture. It increases the main set point by 1.18% compared with 3.40 V; it does not demand another converter or reduced AFE voltage.

The correction gives a useful but still bounded prototype envelope. It does **not** make RF transients, noise, layout, full-temperature operation or safety pass without measurements.

## Primary-source checks

[ADI LT3042 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/3042fb.pdf), pp.3–4,12–15,22: full-temperature SET current is 98–102 µA, offset ±2 mV, at its stated load/input/output conditions. Low-load dropout is 300 mV maximum at the 1/50 mA test points; dropout is defined at **1% output regulation error**, not perfect regulation. Use its bound as a conservative screen for the ≤20 mA allocation, not a guaranteed PSRR number. Pin mappings and reverse-input protection in the architecture report are correct. PGFB tied to IN disables fast start; PG may float when unused. CIN/COUT must meet the effective-capacitance/ESR/ESL and Kelvin-routing requirements. Normal-data operation below its measured dropout cannot inherit the full regulated-output tolerance interval. The 0.8-µVrms claim is typical under stated capacitors/conditions; high-headroom PSRR curves do not guarantee the proposed operating point.

[TI TPS63802 datasheet](https://www.ti.com/lit/ds/symlink/tps63802.pdf), §§7–10: FB accuracy is ±1% in PWM with ≤100 nA feedback bias. Pin mappings and EN-divider calculations in the report are correct. Its 2-A output statement is specifically for 3.3 V output, VI≥2.3 V; 3.44 V current capability still needs verification. Inductor saturation must cover current-limit/ripple conditions, not only the intended output load. Startup-delay/current-ramp figures are typical characterization, not a guaranteed maximum startup time for the complete capacitor/load bank. Output capacitance has no upper limit in its guidance; this does not qualify the existing 200-µF part or its inrush. Forced PWM can return energy upstream; no second source may drive MAIN. Intrinsic UVLO is not a Li-Po cutoff.

## Tolerance calculation including drift

Assume a maximum resistor-temperature excursion of 100°C from the 25°C resistance specification (covering −40°C…+125°C component temperatures). For each 0.1%, 10-ppm/°C resistor, conservatively combine initial tolerance and drift linearly: **±0.2%**. The FB reference and LT3042 SET-current/offset bounds already include their specified semiconductor-temperature ranges. This calculation does not double-count them as resistor drift.

Use:

`MAINmin = 0.495 × [1 + RTOPmin/RBOTTOMmax] − 100 nA × RTOPmax`

`MAINmax = 0.505 × [1 + RTOPmax/RBOTTOMmin] + 100 nA × RTOPmax`

`AFEmin = 98 µA × RSETmin − 2 mV`

`AFEmax = 102 µA × RSETmax + 2 mV`

| Main setting | MAIN min/max with initial tolerance only | MAIN min/max including stated drift | AFE min/max including stated drift | Minimum static headroom | Residual above 300 mV dropout screen |
|---|---|---|---|---:|---:|
| Original3.400V, top58.0kΩ |3.35446…3.44567V|3.34873…3.45155V|2.91256…3.04768V|301.05mV|**1.05mV**|
| Revised3.440V, top58.8kΩ |3.39390…3.48623V|3.38809…3.49219V|2.91256…3.04768V|340.41mV|**40.41mV**|

The original 3.40-V screen therefore cannot be called a useful full-temperature dropout margin. There is no contradiction with the earlier report: that report explicitly left temperature coefficients and transient effects for qualification.

For the revised prototype, make the following explicit acceptance envelope:

- At the LT3042 input, budget at most **30 mV downward main excursion** beyond the worst DC corner, and at most **5 mV additional distribution loss** at the allocated 20 mA AFE load. Remaining conservative dropout-screen reserve is approximately 5.4 mV. No added series resistor or ferrite may consume this budget without recalculation; 2.2 Ω at 20 mA would already lose44mV.
- At every main-powered IC, budget at most **80 mV total positive excursion** beyond the worst DC corner: 3.49219+0.080=**3.57219 V**, below the ESP32's3.6-V recommended maximum with27.8mV remaining. This includes ringing, startup overshoot and load-release events; it is a design limit to measure, not a simulated or guaranteed waveform.
- Track local MAIN/AFE extrema and compare their simultaneous difference, rather than subtracting two unrelated scope readings taken at different loads/times. If these limits are not met, do not declare regulation/noise qualified; increase local energy storage/control response or choose the higher-headroom analog alternative.
- The stated AFE interval is a regulated DC screen. The dropout specification admits1% output error at its defined boundary. Neither this interval nor the9.8/40.4mV calculation promises1% total accuracy under arbitrary ripple. Current ADC/logic minimum-voltage and monitor-delay analyses must include actual observed minima.

Retain a **2.70 kΩ,1% AFE bleeder**: at2.91256V and2.727kΩ it draws≥1.068mA, placing even the powered-down stable rail above the LT3042 electrical-table1mA load condition. Nominal current is1.10mA and loss3.29mW; include it in the20mA allocation. During ramps and faults the rail naturally passes outside its regulated operating interval. Select bypass leakage and resistor drift explicitly; the interval is not a complete PCB leakage/noise error budget.

## Alternatives considered only for this blocker

Changing to a regulator based on headline dropout alone would not remove a guarantee gap. The [MAX38903A–D datasheet,pp.4–5,13](https://www.analog.com/media/en/technical-documentation/data-sheets/max38903a-max38903d.pdf) offers intrinsic output-to-input reverse protection and a low-dropout pass device, but its ±1% accuracy condition still needs input ≥output+0.3V. Its headline100mV/1A dropout is measured at95% of nominal output, not full accuracy. It is a feasible alternate prototype part, not proof that arbitrary100mV headroom preserves precision. TPS7A20 requires separately engineered reverse handling; TPS7A37 requires EN low before input removal and a different accuracy headroom. Those swaps add unresolved work without needing to preserve their supposed benefits.

Lowering AFE to2.8/2.9V changes the electrode-offset/common-mode envelope, and should not be done merely to make a regulator calculation comfortable. Raising MAIN to3.6V would remove recommended-limit tolerance room. A separate low-current converter feeding the existing quiet regulator at higher voltage remains the larger fallback if measured rejection at the proposed lower-headroom point is inadequate.

## What can be implemented without a specified pack

The converter, quiet regulator, translation and rail-monitor schematic can be implemented against an explicit **bench input envelope**, with a fitted development OFF/inhibit and no human connection. Use a current-limited battery emulator for first tests. A named battery connector/input net is not a cell specification.

At the revised3.44V setting,0.56A MAIN means1.9264W; with assumed85% efficiency and3.2V battery input, current≈0.708A. The0.75-A reserve means2.58W and≈0.949A at the same input. At3.0V it is≈1.012A. These are planning calculations, not a guarantee of the cell or converter. Output-bank charging and converter current limit can require higher instantaneous input current than the operating load calculation.

Pack identity/protection thresholds, fuse/precharge/current-limiter behavior, connector polarity and allowed temperature/current still prevent selecting a final battery-protection/cutoff assembly or claiming an operational worn battery design. The provisional22kΩ/10kΩ EN divider turns off over approximately3.095–3.305V and restarts3.415–3.625V; actual pack limits and rebound must accept those intervals or replace them with a qualified supervisor/latch. Retain the development inhibit until the pack-facing circuit and startup behavior are verified. Do not claim a precise3.2-V cutoff or that the RF-current budget bounds inrush/short-circuit current.

The focused result supports **schematic progress with the stated correction and explicit test targets**. It does not authorize hardware power, remove the actual-board3V3-load verification, or close wearer protection/body-bias findings.

## Final implementation correction: independent AFE preconverter

The later confirmed stock-DevKit/USB-exclusion requirement supersedes the earlier3.44-V prototype adjustment. The generated implementation helper now uses **MAIN3.3V TPS63802**, **independent AFE_PRE4.0V TPS63802**, and **LT3042AFE2.98V**. Both converters draw from the protected/switched battery; their outputs are separate. This retains the official nominal DevKit3V3 supply mode while removing the quiet regulator's marginal headroom.

With0.1% feedback resistors,≤10ppm/K and100°C maximum excursion (±0.2% combined resistance bound), plus the same FB/bias corners:

| Rail | Divider | Calculated DC interval |
|---|---|---|
|MAIN|56.0kΩ/10.0kΩ|3.250323…3.349946V|
|AFE_PRE|69.8kΩ+200Ω top,10.0kΩ bottom|3.939154…4.061182V|
|AFE|29.8kΩ RSET|2.912559…3.047679V|

Minimum AFE_PRE−AFE is**891.47mV**, leaving approximately**591mV** above the300-mV dropout screen. Headroom no longer needs to consume nearly all main-rail transient allowance. Noise/PSRR and board transients still require measurement; no achieved ADC-noise claim follows.

Use TPS63802's recommended**two22µF nominal output capacitors** on4.0V PRE, because its guidance changes above3.6V. Main3.3V uses22µF nominal plus the retained main bulk. Every converter input must have≥4µF effective; every converter output≥7µF effective; the LT3042 input/output local bypasses retain≥4.7µF effective. Generated candidate capacitors are MurataGRM21BR61C106KE15L(10µF16V0805),GRM21BR61C226ME44L(22µF16V0805),andGRM21BR71A475KA73L(4.7µF10VX7RSET). Manufacturer part identities/nominal ratings are verified; the helper explicitly retains DC-bias/ESR/temperature/leakage qualification requirements. X5R candidates limit capacitor operating temperature to85°C unless replaced/requalified; the125°C semiconductor calculations are conservative screens, not a whole-BOM125°C rating.

Both converter inductors use the TI-reference candidateCoilcraftXFL4015-471MEC(0.47µH). Manufacturer data gives3.5A/5.4A/6.6A for10%/20%/30% inductance loss at25°C; it is not a sharp5.4-A current limit. Current/temperature/initial-tolerance derating still applies. Exact TPS63802DLA0010A HotRod and XFL4015 footprints are deliberately unassigned pending verified local land patterns; genericWSON10+EP footprints would be incorrect. LT3042IMSE#PBF uses the installed verifiedMSOP10+EP symbol/footprint mapping.

MAIN_PG has a10kΩ pull-up toMAIN and100kΩ pulldown, feeding both U7 and U8 enables. TI explicitly permits PG-to-EN rail sequencing. WithMAINmin3.250V, conservative15.2µA combined enable leakage and the pulldown, the high level is approximately2.82V—above both enable-high requirements. PG low sinks well under its1-mA rating. A disappearing input can make PG undefined; separate rail monitors/READY gating handle interface isolation during abrupt removal. PG sequencing does not replace those monitors.

At20mA AFE load plus5mA conservative LDO ground-current allowance, PRE output is0.100W. At an assumed85% preconverter efficiency, input current is36.8mA at3.2V and conversion loss17.6mW. LDO dissipation is approximately40.4mW, around1.3°C using its referenceMSOP thermal metric. The main current budget now excludes the separately supplied25mA AFE/LDO branch:500mA module capability+25mA DevKit allowance+5mA main-interface allowance=530mA planning load. At85% conversion assumptions for both branches, total battery current is approximately0.680A at3.2V, or0.725A at3.0V. For0.75A MAIN reserve plus0.100W PRE, the corresponding battery figures are0.947A at3.2V and1.010A at3.0V. Actual forced-PWM light-load efficiency must be measured;85% is a sensitivity assumption, not a guaranteed PRE minimum.

The new block generator only writes review-directory artifacts and has73 native pin/net assertions passing. Root integration supplies the battery connector/fuse/reverse-polarity element, physical OFF/service arrangement, supervised readiness controls and existing-rail reassignment. The cell, source-inrush and hardware-power release gates remain as stated above.
