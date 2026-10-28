# Focused check of simplified power circuit

27 October2026. Analysis only; no schematic edits by this agent. The current user direction supersedes the earlier independent preconverter/LT3042 proposal.

**The simplified architecture is electrically feasible as a bench prototype:** one TPS63802 at nominal3.3V powers the stock DevKit and a controlled ADC supply branch. One TPS22919 switches both ADCs. Their DVDD uses its output directly; one10Ω resistor feeds the combined AVDD/AVDD1 branch and its existing20.2µF nominal bypass. There is no need for a second converter, a post-LDO, an adjustable2.98-V rail or level translation merely because of supply-voltage differences. Maintain the separate USB-exclusion/unseated-service contract and existing shared ground.

## TPS22919 connections and small supporting parts

Verified against [TI SLVSEN5B,pp.3–6,13–17](https://www.ti.com/lit/ds/symlink/tps22919.pdf) and installed `Power_Management:TPS22919DCK`:

|Pin|Required connection|
|---|---|
|1 IN|MAIN3V3; local1µF input bypass to AGND|
|2 GND|Common AGND|
|3 ON|ESP32GPIO4 plus an external pulldown, initially10kΩ; verify GPIO4 reset/boot behavior|
|4 NC|Leave unconnected|
|5 QOD|Tie directly to pin6 for the internal24Ω typical discharge path|
|6 OUT|ADC_DVDD/switched3.3V, digital bypass banks and the input of the analog10Ω resistor|

Orderable candidateTPS22919DCKR, footprint`Package_TO_SOT_SMD:SOT-363_SC-70-6`. Input range1.6–5.5V, maximum continuous current1.5A. ON high≥1.0V and low≤0.35V; ON-high leakage100nA maximum. Internal smart pulldown is530kΩ typical; use an external bias for the system default. The output rise is deliberately slow: at3.6V, typical turn-on1.75ms,10–90% rise1.1ms and slope2.7mV/µs. These are typical values, not guaranteed timing maxima. QOD becomes weaker during input collapse; it is not reverse-current isolation or a guaranteed zero-voltage deadline. The switch does not isolate ADC signal pins.

A10kΩ pulldown gives1mV from100nA ON leakage alone. GPIO leakage/boot pulls must be included; no weak resistor can override an actively driven boot-high pulse. GPIO4 must actually be high impedance/low until firmware takes control. If a documented reset pull-up makes10kΩ insufficient, lower that resistor after calculating its divider against the pull-up rather than adding another power-control IC.

The small-parts minimum is one local1µF input capacitor, one ON pulldown, the switch, and the10Ω analog resistor, beyond the existing converter and ADC capacitors. Preserve each ADC's10µF+100nF analog and digital banks. Follow [ADS1298§11.1](../../../../docs/datasheets/originals/components/ADS1298.pdf) for short AVDD1/AVSS1 star connections and pin-local bypassing; add dedicated1µF+100nF per ADC at that charge-pump branch if absent. Count those extra capacitors in the RC transient model. Do not add a ferrite based on an assumed impedance curve.

## Voltage and RC budget

Retaining main feedback56.0kΩ/10.0kΩ gives3.3V nominal. The earlier conservative full-temperature resistor/reference screen givesMAIN approximately**3.2503–3.3499V** (0.1% resistors,≤10ppm/K,100°C excursion,±1% reference,±100nA FB bias). These are DC calculations; RF/startup extrema remain measurements.

Two ADS analog cores have the prior3V high-resolution typical benchmark5.5mA combined. The10Ω resistor therefore drops about**55mV typical**. At a planning10mA analog load and1% high resistor, drop is**101mV**. Allowing10mV for the ADC switch/path at a planning20mA total branch load gives approximately:

- ADC_DVDD≥3.240V;
- ADC_AVDD≥**3.139V**, rather than exactly3.15V once switch loss is included;
- AVDD−DVDD≈−0.101V, comfortably within the ADS operating-relative range−2.1…+3.6V;
- analog margin above2.7V≈439mV before dynamic droop.

The10mV switch/path allowance is conservative engineering allocation, not a guaranteed exact3.3-V RON row. The datasheet maximum RON rows vary with supply and temperature; verify it at the actual load. The voltage span has ample margin for this tiny steady load compared with the earlier tight post-LDO solution. The analog resistor dissipates only about1mW at10mA, but its pulse rating must also handle capacitor charging/discharge events. An0805 resistor with a documented short-pulse capability is a practical selection; do not infer pulse capability solely from its DC wattage.

For the existing analog bank only:

`τ=10Ω×20.2µF=202µs; fc≈788Hz`.

A five-time-constant settling interval is about1.01ms;20ms is ample nominal RC settling allowance after the switch has risen. During a2.7mV/µs linear supply ramp, the simple ramp-tracking lag is approximately`τ×slope=0.545V`, not a20µs turn-on. This typical model is compatible with the ADS relative supply limit; verify actual AVDD/DVDD ramps and include capacitor tolerance/new bypassing. Holding RESET/PWDN low prevents attempted conversion while supplies establish themselves. RC filtering does not substantially suppress slow RF-current envelopes or ground/radiated interference; it is a reasonable simple filter, not proof of sEMG noise performance.

For shutdown, direct QOD discharges the digital bank and the analog bank through its10Ω feed. A two-node, equal20.2µF-bank/24Ω-QOD model gives a slow time constant around1.1ms, hence roughly2–3ms fall intervals.20ms off-time is a reasonable initial firmware dead-time target, not a guaranteed full-system discharge time; internal VCAP/reference networks and loss of QOD strength during main-input collapse require measurement.

## Minimal operating contract and budget

At reset/boot keep ADC power OFF. Firmware first sets ADC-bound outputs LOW and disables any opposing pull-ups, then turns on GPIO4, allows switch/RC settling, and performs the full ADS power-up/reset/clock/reference sequence. The20ms RC wait does **not** replace the ADS2¹⁸-clock POR interval(128ms at2.048MHz), VCAP1>1.1V requirement or the slave's clock-dependent initialization. Before turning ADC power off, drive every MCU-to-ADC output LOW again; pull-ups on ADC-side nets must use switched DVDD, never MAIN. Verify main-powered return receivers add no pull-up/back-power path. The retained DOUT selection arrangement and exclusive-CS protocol remain required; a power switch does not itself prevent DOUT contention.

Current allocation can remain simple:500mA module source capability+25mA provisional DevKit overhead+20mA ADC/control branch+5mA remaining logic≈**550mA**, rounded to0.56A design load with0.75A short-step reserve. These are provision targets, not measured averages. At3.3V/0.56A, power1.848W; assumed85% efficiency gives0.679A from3.2V. At0.75A the corresponding current is0.910A. Initial ADC-bank inrush, VCAP/reference charging and radio peaks need measured waveforms; the converter's headline current rating alone does not qualify them.

The only focused checks still needed before accepting this simplified implementation are actual pin/net routing, GPIO4 boot-OFF behavior, main/ADC ramp and discharge captures, absence of powered-signal injection, actual RF load steps and noise spectra. These checks do not justify rebuilding the larger power tree unless they reveal a concrete unmet requirement.

## Further simplification: common rail without ADC power switch

The latest proposed common-rail arrangement is also acceptable as a standard **bench prototype**. A separate ADC load switch is not structurally necessary: power MCU, forward244 buffer and ADC DVDD from the same regulated3.3V source; feed AVDD/AVDD1 through2.2Ω and the analog bypass banks. Hold all ADC-bound inputs LOW, including RESET/PWDN, during supply startup, then perform the full stabilized-supply/VCAP1/clock/POR initialization. Firmware must not start conversions merely because the MCU has booted. The buffer's boot biases and the retained return interface must be checked as their own small interface circuit.

Exact constraint distinction: ADS1298§7.1 lists absolute limits for AVDD−AVSS, DVDD−DGND, AVSS−DGND and individual inputs relative to their own supplies. It does **not** list AVDD−DVDD as an absolute maximum. The−2.1…+3.6V AVDD−DVDD range is in§7.3 recommended operating conditions. A hypothetical startup excursion outside that recommended range while supplies are still rising does not by itself establish a damage mechanism or a mandatory load-switch requirement. Do not claim normal ADC operation during the ramp. Supply/input relative absolute limits still apply throughout.

With20.2µF existing analog bulk plus2.2–4.4µF added local charge-pump bypass, the2.2Ω filter time constant is approximately49–54µs. A purely illustrative linear3.3-V/224-µs rise gives0.73–0.80V tracking lag, below2.1V. However the converter's224µs characterization concerns startup/current-limit behavior: it is **not** a guaranteed main-output maximum slew rate. Actual capacitor tolerances, startup load, source and converter response must be measured; this illustration must not be promoted to a guaranteed inter-rail waveform. No unverified maximum slew has been invented.

At10mA combined analog current, the resistor loses only22mV nominal(22.22mV at1% high resistance). The main low DC corner3.2503V therefore gives roughly3.228V analog supply before trace loss; at the5.5mA typical benchmark, loss is12.1mV. This provides ample steady supply headroom. On shutdown the filtered analog rail may outlast DVDD; an analog level no higher than approximately3.35V relative to falling DVDD remains below the recommended positive3.6-V difference. Auxiliary pins17/18/62 must follow the filtered **actual AVDD**; CLKSEL follows DVDD. Preserve common AGND and existing local bypasses.

Use the2.2Ω filter, existing bypass banks and necessary pin-local charge-pump bypass; omit the ADC power-switch/ON/QOD support when adopting this version. This removes a control domain and its software ON/OFF contract. RF-noise, startup and brownout captures remain ordinary prototype verification, without requiring the earlier larger power tree in advance.
