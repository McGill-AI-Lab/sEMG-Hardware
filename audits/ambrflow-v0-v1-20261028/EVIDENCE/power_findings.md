# Power, passive-component and ground evidence

Read-only review of the complete active V0/V1 schematic files and their KiCad 10.0.7 XML exports. Both active designs contain one sheet and no hierarchical sheets. Parsed full source trees are saved as `v0.parsed.json` and `v1.parsed.json`. These are audit artifacts, not modified KiCad files.

## Confirmed electrical findings

### E5 — STILL PRESENT; P1

- V0 U4 = TI LP2985-3.3, U7 = TI TLV75533PDBV. V1 U4 unchanged; U7 becomes U5.
- In **both** designs, both regulators' output pins **5** are on the same net `+3.3V`. Both input pins **1** are on `+3.7V`. Both ground pins **2** are on the battery-negative net exported as `AGND`.
- The two fixed 3.3-V outputs are directly paralleled; they are not isolated analog/digital supplies. The schematic's ADC/MCU box titles do not change this connection.
- The parts' independent tolerances mean that sharing is not defined; their 150-mA and 500-mA ratings must not simply be added. Actual current sharing, oscillation, damage or a specific transient is **not** established by this schematic.
- Simple correction: use U4 pin5 to supply a distinct analog rail, e.g. `+3.3VA`, and U5 pin5 to supply the digital/MCU rail. Correct the ADS supply connections described below. Keep each regulator's existing output capacitor connected to its own output and ground. This uses the two existing regulators; no added regulator or mux is justified.
- Verification: re-export the proposed netlist; U4.5 and U5.5 must have different net names with the intended loads. Confirm individual load budgets. The specific KiCad ERC power-output-to-power-output violation should disappear. Coordinate V1 DevKit USB/3V3 supply arrangements with the ESP agent before externally powering its 3V3 header.

### E6 — STILL PRESENT; P1

- V0 `/EN` contains **only U4.3 and U7.3**. V1 `/EN` contains **only U4.3 and U5.3**.
- There is no pull-up, pull-down, switch, GPIO or valid logic source on that net. Labels named EN are wires' names; they are not an enable source. V0 MCU U6.3 has a separate RC network and is not this net.
- Both LDOs require a high enable level. The LP2985 datasheet explicitly requires ON/OFF to be terminated. An actual low/off state or latched-off sequence cannot be proven from an undriven node, so E3 should not repeat this as a confirmed off/latch fault.
- Simple correction if always-on operation is intended: connect the two existing enable pin3 inputs to their common input supply `+3.7V` (both pin1 inputs). No resistor is needed for this fixed always-on connection. If shutdown is required, its intended control source and default state must first be specified.
- Verification: netlist should show U4.3 and U5.3 on the battery-input net. Measure enable voltage and both outputs during startup once supply and ground faults are corrected.

### H2 — STILL PRESENT / worsened analog supply fault; P0

- V0 `+3.3VA` contains U1/U2 AVDD pins **19,21,22,54,56,59**, and C18/C19/C69/C70. It contains **no battery or regulator output**. U4.5 was named `+3.3V`, not `+3.3VA`.
- V1 those same AVDD pins of **both** ADCs are on `AGND`, the same net as their AVSS pins **20,23,32,53,57,58** and battery negative. Thus **AVDD−AVSS = 0 V** exactly in the schematic. They were not connected to a valid analog source by the revision.
- V1 AVDD local labels occur on the +3.3-V upper terminals of C6/C7 and C32/C33 and on U1/U2 RLDIN pins62, while the ADC AVDD supply pins are physically connected to the lower capacitor/AGND buses. Renaming the ground bus is not a fix: disconnect the AVDD supply pins from ground and connect them to the intended valid analog supply, keeping AVSS grounded.
- Simplest correction: route the dedicated U4.5 analog rail to all listed AVDD/AVDD1 supply pins and the supply side of their existing analog decoupling capacitors. Preserve the ground side of the capacitors and AVSS connections. ADS agent should resolve other AVDD-labelled signals under the ADS-specific checks.
- Verification: ADS analog positive pins and negative pins must land on different nets; calculate their supply difference against the ADS recommended 2.7–5.25-V analog span. Confirm by powered measurement after the netlist is corrected. V0 lacked a defined analog operating supply; do not invent a precise floating voltage for it.

### H1 — NEW IN V1; P0; C3 shares this root cause

- V0 KiCad export merges battery negative, ADC true ground pins, MCU ground and all capacitor return grounds as `AGND`. Its AGND/GND connection in the grounding box is a wire from **(242.57,161.29) to (254,161.29) mm**. V0's separately named DGND control-pin island is **not** tied to that ground; it does not contain the V0 MCU or ADC true ground pins. See the digital/control audit for consequences of that control island.
- V1 `AGND`/`GND` remain tied through the grounding-box wire **(36.83,267.97) to (48.26,267.97) mm**. But the separately named **DGND does not connect to that ground**.
- V1 MCU U3 ground pins **22,23,24,44** are on isolated `DGND`; regulator pins2 and BT1.2 are `AGND`. Capacitors C8 (100 nF), C9 (10 uF), C34 (100 nF), C35 (10 uF) have pin1 on `+3.3V` and pin2 on this isolated DGND. They are not returned to a valid supply ground.
- Additionally U1/U2 **DVDD pins48/50 are on DGND**, but their true DGND pins **33/49/51 are on AGND**. Simply tying ground names together before removing the misplaced DVDD connections would ground the ADC positive digital supply.
- Simple correction sequence: (1) remove DVDD48/50 from the ground bus and connect them to the intended digital 3.3-V rail; (2) connect the genuine MCU/ADC digital grounds and digital capacitor returns to common battery/regulator ground. One electrical ground with sensible physical routing is enough for this schematic correction; no new isolation or ground architecture is justified.
- Verification: netlist must show a continuous DC return from U3 ground to BT1.2 and regulator ground; ADS DVDD must remain separate from that return. Scope supply-to-ground differences during startup after correction.

## Condition decisions without a confirmed new fault

| ID | Suggested result | Evidence and limitation |
|---|---|---|
| A1 | ADS agent final classification | V1 analog span is confirmed 0 V, below 2.7 V. V0 has no defined analog operating supply; do not assign a precise floating voltage. Regulator inputs are only nominally named +3.7V, with no specified actual range. |
| B1 | CANNOT VERIFY | Resistors have values but no manufacturer, power rating or footprint. Input resistors: 2 kohm; V0 enable pull-up R20: 10 kohm; V0 feedback R1/R36: 1 Mohm. No demonstrated high-dissipation connection. Conditional examples: 3.3 V across 2 kohm dissipates 5.445 mW; across 10 kohm 1.089 mW. External electrode voltages are unspecified. These calculations do not establish actual operating currents. |
| C1 | CANNOT VERIFY | All capacitors lack voltage ratings/orderable parts. Battery minimum/maximum and external input limits are absent. Values alone cannot establish voltage overstress. No capacitor derating review was performed. |
| C2 | NOT FOUND | Every capacitor in the XML export has both pins on a net with another actual component connection. There is no capacitor pin attached only to an unconnected wire or power symbol. |
| C3 | NEW IN V1 | C8/C9/C34/C35 pin2 on isolated DGND; see H1. V0 capacitor return grounds all merged with battery negative. |
| C4 | NOT FOUND | V0 U4 C44=2.2 uF, U7 C46=200 uF. V1 U4 C54=2.2 uF, U5 C57=200 uF. Nominal output capacitors meet the respective minimums (LP2985 legacy 2.2 uF; TLV755P 1 uF). They currently share one output net, so fix E5 without abandoning each local capacitor. Physical proximity and effective capacitance are not demonstrated and are outside the excluded derating review. |
| C5 | CANNOT VERIFY | Capacitor technology/ESR unspecified; LP2985 exact orderable suffix/chip identity unspecified. Legacy LP2985 allows ceramics but requires its stable ESR window; new chip is ceramic-stable. TLV755P is ceramic-stable. No basis for declaring 'ceramic capacitors are unsuitable' in either revision. ESR means capacitor series resistance. |
| C6 | CANNOT VERIFY | No measured/simulated load waveform or supply impedance. Existing decoupling does not prove <5% droop, and static faults do not prove a time-domain dip. Resolve C3/H1/H2 before measuring; 5% of 3.3 V = 165 mV. |
| E1 | CANNOT VERIFY actual range; no nominal fault found | Both LDO input pins1 are nominal +3.7V. LP2985 recommended max16 V (legacy abs max16 V/new18 V), TLV755P recommended max5.5 V/abs max6.0 V. BT1 has no chemistry, cell count, min/max voltage, protection or charger specification; a rail name is not a worst-case input specification. |
| E2 | CANNOT VERIFY | See dropout calculation below. Battery operating range/cutoff and actual regulator load allocation are missing. |
| E3 | CANNOT VERIFY | E6 is confirmed. No feedback dependency on the LDO's own output or proven latch-off sequence exists; an undriven enable is not proof of a particular off voltage. |
| E4 | NOT FOUND | Both fixed-output regulators are 3.3-V types and each output pin5 is labelled +3.3V in both revisions. The missing V0 +3.3VA source and V1 grounded supply are H2/A1, not a regulator setpoint mismatch. |
| E7 | NOT APPLICABLE | Explicit supply regulators are linear LDOs, not switching regulators; DevKit onboard supply uses an LDO per ESP agent confirmation. |
| E8 | NOT APPLICABLE | Fixed 3.3-V parts; no adjustable output setpoint or required voltage-lowering transition shown. |
| G1–G7 | NOT APPLICABLE | No power multiplexer present in either complete schematic. |

## Dropout calculation for E2

Dropout is the extra input voltage an LDO needs above its intended output to maintain regulation.

- Nominal labelled headroom: **3.7−3.3 = 0.400 V**. This is not the battery's minimum headroom.
- TLV75533PDBV worst-case dropout at 500 mA over −40 to125°C is **238 mV**, so a nominal-target estimate is **VIN >= 3.3+0.238 = 3.538 V**.
- LP2985 at 150 mA over −40 to125°C: legacy maximum **575 mV**, new-chip maximum **254 mV**; corresponding nominal-target inputs **3.875 V** and **3.554 V**. At50 mA the respective maxima are225 mV and184 mV; nominal-target inputs3.525 V and3.484 V.
- A battery named +3.7V therefore does not establish dropout throughout expected operation. Full worst-case signoff also uses the positive output tolerance, actual load, temperature and minimum battery voltage under load. The paralleled connection currently prevents assuming intended current sharing. Do not add a converter until the missing battery/load requirements demonstrate one is needed.

## Manufacturer evidence

- [TI LP2985 datasheet SLVS522S, May2025](https://www.ti.com/lit/ds/symlink/lp2985.pdf): pin table p3; recommended operation p4; output tolerance p5; dropout p6; enable p16 and24; legacy/new capacitor requirements p20–21. Exact physical LP2985 orderable device is absent from both schematics; latest datasheet covers two chip generations.
- [TI TLV755P datasheet SBVS320D, September2024](https://www.ti.com/lit/ds/symlink/tlv755p.pdf): DBV pins p3; ratings p4; dropout p6; enable and output discharge p12–13; capacitor requirements p15 onward.

Both ERC reports flag U4 enable pin3 as undriven and the two regulator output pins5 as power-output-to-power-output. These reports corroborate the traced connections; ERC passing/failing is not a complete functional test.
