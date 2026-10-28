# Open-sEMG-16 — Ambrflow electrical feedback audit

**Audit date:** 28 October 2026. **Scope:** only the 48 supplied Ambrflow conditions, applied to the two active schematics. Both complete files and embedded pin definitions were parsed and reviewed; each is a single sheet with no hierarchical sheets. `.history` and backup snapshots were not used as active designs. No source project or circuit was modified; proposed changes below are instructions only.

## Overall result and counting

There are **six confirmed V0 wiring/control problems** within scope: **zero fully fixed, one partially fixed, five still present**. V1 adds **two distinct supply/return wiring problems**. Thus **eight distinct problems need a correction or completion in V1**. This is a count of the specific arrangements in Findings 1–8 below, not of hypothetical failure modes or duplicated checklist entries. The new AVDD ground tie worsens the existing analog-power problem; it is not counted again as a separate V1 problem. The V1 DVDD error and disconnected controller return require different corrections and are counted separately, even though they touch the same DGND net.

**25 condition comparisons are CANNOT VERIFY.** A1 and F1 are special: V1’s zero analog supply is confirmed, but V0’s actual floating voltage cannot be calculated. Their before/after *voltage* comparison is uncertain; the underlying missing valid analog supply is already a confirmed V0 problem under H2. None of these uncertain entries is credited as a fix.

| Count basis | Fixed | Partially fixed | Still present | New in V1 | Cannot verify | Not found | Not applicable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Distinct wiring/control problems |0|1|5|2|Not counted as confirmed problems|—|—|
|48 checklist rows |0|1|4|2|25|6|10|

The checklist-row counts differ because several rows describe the same wiring problem, and J3 covers several control arrangements. A valid local improvement is recorded without claiming the entire condition was cleared. Passing ERC would not prove functionality; its counts are not issue counts or completion percentages.

## Evidence and limits

V0 source: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/Archive/electronics-archive/open-semg-16-electronics-v0/open-semg-16.kicad_sch`.

V1 source: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/open-semg-16-v1/open-semg-16-v1.kicad_sch`.

KiCad CLI 10.0.7 exported XML netlists, SVG schematics and all-severity ERC JSON into `EVIDENCE/`. Reports: [V0 connectivity](EVIDENCE/v0.connectivity.txt), [V1 connectivity](EVIDENCE/v1.connectivity.txt), [V0 ERC](EVIDENCE/v0.erc_summary.txt), [V1 ERC](EVIDENCE/v1.erc_summary.txt). Complete parsed inventories retain component properties, embedded pin types, positions, wires, labels, junctions, notes and no-connect markers. [Source manifest](EVIDENCE/source_manifest.json) records source hashes and sheet counts.

ERC produced 62 V0 and 65 V1 messages, including unused/unconnected pins and electrical-type/model warnings. Both runs completed. V0 netlist export warned of annotation errors: two placed reference-electrode symbols are both J1. This limits unambiguous connector-instance naming in the optional RLD path; it does not affect the traced ADC/LDO supply nets. No connector-count or footprint review was performed. Fontconfig printed a missing-default-config warning; netlist/ERC/SVG files were generated successfully.

Relevant ERC corroboration: both revisions flag undriven U4 enable and parallel LDO outputs. V1 flags U1 CLK37 unconnected and ADC_CLK label dangling. V1 shared MISO output-type warning is not proof of contention; the ADS output can tri-state. Likewise, DevKit external CHIP_PU warning does not model its internal reset network. Generic ground labels can hide serious errors that ERC does not diagnose as intended-voltage failures.

No battery operating range, complete power/voltage-rated passive BOM, firmware, source/electrode model or measured/simulated transient response was supplied with these schematic sources. A brownout is a supply drop that triggers controller reset. The nominal `+3.7V` label does not specify battery chemistry, cell count, charging voltage or cutoff. V0’s represented controller is a **WROOM-1 module**, not a DevKit. V1 represents **ESP32-S3-DevKitC**; its precise board revision and module suffix are unspecified. Official DevKitC-1 v1.1 is used as the documented internal-circuit reference; confirm the installed board matches before relying on board-specific details.

## Circuit understanding and equivalent parts

Each revision has two TI ADS1298 ADCs, each with eight differential electrode inputs, internal programmable-gain amplifiers (PGAs), delta-sigma converters, optional RLD circuitry, reference pins and digital control/SPI pins. `ADS1298xPAG` specifies the PAG 64-pin TQFP family; the `x` is not a complete orderable grade/packing suffix. Both embedded ADS pin definitions agree with the manufacturer’s PAG supply/input/digital pin numbers. Pin 18 is labelled TESTP_PACE_OUT2 in the symbol but is TESTN_PACE_OUT2 in TI’s table; analysis follows pin number 18.

| Function | V0 reference/value | V1 reference/value | Electrical comparison |
|---|---|---|---|
| ADCs | U1/U2 ADS1298xPAG | U1/U2 same | Same acquisition devices; supply wiring changed substantially |
| Analog-intended LDO | U4 LP2985-3.3 | U4 same | Exact LP orderable/chip generation absent; output still wrongly shared |
| Digital-intended LDO | U7 TLV75533PDBV | U5 same | TI fixed 3.3 V, DBV5-pin; rename is not a fix |
| Controller | U6 ESP32-S3-WROOM-1 | U3 ESP32-S3-DevKitC | Module→board; account for board’s existing EN/reset/LDO circuitry |
| Battery | BT1, generic Battery | BT1 same | Both labelled +3.7V; actual range unspecified |
| U1 eight input pairs | E17–E24; R3,R21–R35 | E1–E8; R1–R16 | Resistor sequence maps in pin order; all 2 kΩ |
| U2 eight input pairs | E1–E8; R4–R19 | E9–E16; R17–R32 | All 2 kΩ, same input topology |
| U1 input capacitors | C13,C14,C15,C50–C62 | C1–C5,C10–C18,C21,C22 | Per-lead 620 pF to AGND, unchanged electrically |
| U2 input capacitors | C26–C41 | C27–C31,C36–C44,C47,C48 | Per-lead 620 pF to AGND; match by ADS pin, not consecutive cap number |
| U1 VCAP1/2/3/4 | C63/C64/C65/C66 | C23/C24/C25/C26 |22 µF/1 µF/1 µF/1 µF retained |
| U2 VCAP1/2/3/4 | C2/C3/C4/C5 | C49/C50/C51/C52 | Same values retained |
| U1 VREFP bypass | C67/C68 | C19/C20 |0.1 µF/10 µF retained |
| U2 VREFP bypass | C17/C11 | C45/C46 |0.1 µF/10 µF retained |
| U1 analog/digital bypass | C69/C70; C71/C72 | C6/C7; C8/C9 |0.1 µF/10 µF per rail; V1 pins wired to return rows |
| U2 analog/digital bypass | C18/C19; C20/C21 | C32/C33; C34/C35 | Same values, same V1 wiring error |
| LP input/output/bypass | C43/C44/C42 | C53/C54/C55 |1 µF/2.2 µF/10 nF retained |
| TLV input/output | C45/C46 | C56/C57 |1 µF/200 µF retained |
| Module supply/EN | C47=22 µF,C48=0.1 µF; R20=10 kΩ,C49=1 µF | Inside U3 reference board | External network removal is not evidence of lost EN pull-up |
| Optional RLD feedback | U1 R36/C73; U2 R1/C1; two J1 instances | Removed |1 MΩ∥1.5 nF; no independent bias/safety redesign investigated |

Reference changes were matched by device pins, net membership, values and circuit role. See the complete inventories for every passive component and the digital evidence file for the full GPIO remap.

| Digital function | V0 module pin / GPIO | V1 board symbol pin / GPIO | ADC pins |
|---|---|---|---|
| Chip select | U6.5/GPIO5, shared /CS | U3.16/GPIO10→/CS_ADC1; U3.20/GPIO14→/CS_ADC2 |39 each |
| Power down | U6.6/GPIO6 | U3.7/GPIO7 |35 each |
| Reset | U6.7/GPIO7 | U3.6/GPIO6 |36 each |
| START | U6.23/GPIO21 | U3.12/GPIO8 |38 each |
| MOSI | U6.19/GPIO11 | U3.17/GPIO11 |34 each |
| SCLK | U6.21/GPIO13 | U3.18/GPIO12 |40 each |
| MISO | U6.20/GPIO12 from U1; U2 DOUT→U1 DAISY_IN | U3.19/GPIO13 from both DOUTs |43; V0 chain input U1.41 |
| DRDY | U6.12/GPIO8 | U3.15/GPIO9 |U1.47; U2.47 unused in both |

## Remaining findings and exact proposed KiCad corrections

These are eight distinct arrangements, grouped here to avoid counting repeated checklist consequences. No changes have been implemented. P0 means a verified operating blocker or damage risk; P1 means verified potential unreliability. Unmeasured timing/analogue behavior remains UNKNOWN even when the responsible wiring omission is certain.

### Finding 1 — Analog positive supply has no valid source (STILL PRESENT, P0; H2, with A1/F1 consequences)

**What is wrong / why it matters:** V0’s `+3.3VA` is a source-free island; its exact voltage is unknown. V1 instead connects every ADC analog positive supply to the battery-negative net. Thus `AVDD−AVSS=0V` by connectivity, below the minimum operating span. The PGAs and converters cannot perform valid acquisition with this supply connection. In V1, unused analog pins 17/18/62 are tied to `+3.3V` while AVDD is grounded; when the intended 3.3 V rail is on, those pins exceed `AVDD+0.3V`. This creates a potential damage path; its current is not known.

**Where:** both U1/U2 AVDD19/21/22/56/59 and AVDD1.54; negative AVSS20/23/32/57/58 and AVSS1.53. V0 positives→`+3.3VA`; V1 positives and negatives→`AGND`. U1 V1 supply endpoints around(172.72/177.8,101.6)mm run to y93.98 capacitor-return bus, not y86.36 positive bus. U2 repeats the error. A nearby AVDD label on the capacitor top does not power the IC pin connected to its bottom.

**Exactly change in KiCad:** remove these positive-supply connections from the ground rows. With Finding 3’s rail split, connect them to U4.5’s dedicated `+3.3VA`. Put the supply side(pin 1) of C6/C7/C32/C33 on that same analog rail. Keep AVSS and those capacitors’ pin 2 on valid ground. Connect unused TEST/PACE17/18 and RLDIN62 to this corrected analog rail, following TI’s unused-analog-pin instruction; do not leave them on a separately sequenced digital rail. Keep U1 CLKSEL on the digital logic rail.

**Verify:** netlist must separate all analog positives from AVSS and include U4.5 as their source. Measure span at both ADCs before acquisition; check unused analog-pin voltages against the restored AVDD. No new regulator, buffer or capacitor is justified by this fault.

### Finding 2 — LDO enable net has no driver (STILL PRESENT, P1; E6/J3)

**What/why:** `/EN` consists only of two input pins. Joining two inputs does not create a high or low level, so regulator startup is not guaranteed. A particular off or latched state is not proven.

**Where:** V0 U4.3/U7.3; V1 U4.3/U5.3. These are separate from the ESP’s own EN/CHIP_PU.

**Exactly change:** for always-on operation, connect both pin 3 enables directly to their shared pin 1 input supply `+3.7V`, after specifying its allowed voltage range. This needs no added resistor. If shutdown is required, define its actual controller and reset default before selecting that alternative.

**Verify:** netlist includes the intended input supply/driver; measure enable and outputs during startup. Do not count a speculative E3 latch fault separately.

### Finding 3 — Two LDO outputs are tied together (STILL PRESENT, P1; E5)

**What/why:** independent 3.3 V regulators have slightly different setpoints. Directly joining them does not guarantee current sharing and does not provide an additive 650 mA supply rating. This topology is verified; a particular overload/oscillation is not.

**Where:** V0 U4.5 and U7.5; V1 U4.5 and U5.5, all on `+3.3V`.

**Exactly change:** keep the existing parts and split their loads: U4.5/C54.1 to `+3.3VA` for the corrected analog supply; U5.5/C57.1 to `+3.3V` for ADC digital and controller supply. Each capacitor return stays at valid common ground. Preserve U4 bypass C55 and input capacitors. No ballast network or power mux is needed to separate these intended loads.

**Verify:** distinct output nets, correct capacitor/load allocation and per-regulator load budget; targeted ERC power-output conflict should disappear. U3’s documented internal LDO also reaches its 3V3 header: establish one DevKit supply method. USB/header dual powering is an unresolved operating-mode question, not an assumed additional active source.

### Finding 4 — “DGND” control ties are not actually grounded (STILL PRESENT, P1; J3)

**What/why:** a ground symbol’s name matters. Both revisions have a `DGND` net separate from battery-negative `AGND/GND`. V0’s actual IC ground pins are correctly on AGND, but inputs meant to be low sit on the isolated DGND island. Their low state is not guaranteed. V1 expands this island into supply/return faults in Findings 7/8.

**Where:** V0 U1/U2 RESV1.31 and GPIO42/44/45/46 plus U2 DAISY_IN41. V1 additionally U1 DAISY_IN41 and U2 CLKSEL52, as well as misplaced DVDD and MCU returns. True ADC DGND33/49/51 stays AGND in both.

**Exactly change:** after removing misplaced DVDD pins from this net, connect the intended low-level/control ground ties to valid battery/regulator ground. No resistor or isolation device is needed to establish that reference. Keep unused ADS GPIOs configured as inputs or low outputs; an actual firmware high-drive conflict has not been established.

**Verify:** all intended low straps share the ADC’s real DGND33/49/51 and BT1.2 net. Check actual control levels while reset is held. Do not merely rename a supply bus “ground.”

### Finding 5 — ADC controls lack hardware reset defaults (STILL PRESENT, P1; J2/J3)

**What/why:** before firmware runs, the selected ESP GPIOs provide no guaranteed drive/pull for shared `/PWDN`, `/RESET` and `/START`. The ADS inputs have no specified internal bias that can be relied on. The omission is confirmed; a specific startup glitch or brownout is not.

**Where:** both ADCs PWDN35, RESET36, START38; V0 U6 GPIO6/7/21 and V1 U3 GPIO7/6/8. Separate/shared CS also needs a deliberate startup policy; its actual contention state is unknown.

**Exactly change:** add one 10 kΩ pulldown from shared `/PWDN` to valid ADC ground and one from shared `/RESET` to that ground. A 10 kΩ `/START` pulldown defines conversion-off default. These are justified bias components on demonstrated undriven controls. At 3.3 V a high-driven 10 kΩ draws 0.33 mA; two 10 µA input leakage bounds produce at most 0.20 V, below the 0.66 V low threshold. Recheck for the selected actual supply/leakage bounds.

**Verify/firmware:** hold inputs low until both supplies are valid, then establish both CS high before releasing shared PWDN/RESET. Initialize U1 on its internal clock and enable U1 CLK_EN before assuming U2 has a clock. For U2, TI’s power-up wait starts only once its external CLK is valid: wait at least 2^18 clock periods (128 ms at 2.048 MHz), or until VCAP1 exceeds 1.1 V, whichever is later, then reset/configure U2 using its separate CS and RESET opcode. Observe specified reset-completion and command timing. Do not pulse shared RESET at this stage: that would clear U1 CLK_EN and remove U2’s clock. Repeat this master-first validation after a common reset. This is a proposed sequence to verify, not a claim that existing firmware implements it.

Scope all relevant nets during held reset/cold start. Do not blindly add CS pull-ups: they can rise with DVDD before AVDD. Final CS/MOSI/SCLK passive defaults require the selected sequence; do not assume DOUT is tri-stated merely by PWDN. The official DevKit already has its EN pull-up/RC; no extra external EN resistor is justified from the unconnected U3.3 marker.

### Finding 6 — Clock selection improved but clock delivery is incomplete (PARTIALLY FIXED, P0; J3)

**What/why:** V0 ties CLK37 only to CLKSEL52 on each ADC. At reset CLK_EN=0, so CLK is input/tri-state and cannot define CLKSEL. V1 adds an explicit U1 CLKSEL high strap and intends U2 external-clock selection; this is a local wiring improvement, usable only after supply repairs. However, U1 CLK37 does not reach the nearby ADC_CLK label. U2 CLK37 is the only component on ADC_CLK, so its selected external clock has no source. U2’s low strap also needs Finding 4’s valid ground.

**Exactly change:** connect U1.37 to the existing `ADC_CLK` label/net reaching U2.37. Keep U1.52 on valid digital 3.3 V and U2.52 on valid ground after supply repairs. Firmware must set U1 CONFIG1.CLK_EN=1 to deliver the clock before ADC2 is expected to operate. No new oscillator is needed for the already chosen master/slave arrangement.

**Verify:** corrected netlist contains U1.37 and U2.37 together; the dangling-label/unconnected-clock ERC findings disappear. With valid supplies and configured master, measure the selected nominal 2.048 MHz clock at both chips. Validate the master-first reset sequence in Finding 5: common RESET clears U1’s clock-output setting. This is completion of the control arrangement within J3, not a separate general timing redesign.

### Finding 7 — ADC digital positive supplies moved to the ground island (NEW IN V1, P0; H2/A1)

**What/why:** V0 DVDD48/50 is correctly on `+3.3V`. V1 puts those positive pins on `DGND`, while actual ADC DGND33/49/51 remains `AGND`. There is no valid positive digital supply; simply merging the ground names would ground DVDD. This is distinct from the controller’s missing return in Finding 8.

**Exactly change:** remove U1/U2 pins 48/50 from the capacitor-return/DGND rows; connect them to the U5 digital `+3.3V` rail, at the supply side of C8/C9/C34/C35. Retain those capacitors’ returns on corrected common ground.

**Verify:** positive DVDD pins share U5.5 and capacitor pin 1, never the actual chip-ground net. Measure DVDD relative to ADC DGND against its operating range. Remove these mistaken connections before joining ground nets.

### Finding 8 — Controller and digital bypass returns lack battery ground (NEW IN V1, P0; H1/C3)

**What/why:** V0 MCU ground has a valid battery return. V1 U3’s four GND pins and digital decoupler returns join isolated DGND, separate from battery negative and LDO ground. The intended board supply lacks its return reference. A parasitic path through signals or an attached USB cable is not a valid schematic ground connection and is not assumed here.

**Exactly change:** once Finding 7 is repaired, join U3 GND22/23/24/44 and C8/C9/C34/C35 pin 2 to common battery/LDO/ADC ground. Keeping meaningful net names is fine only if the actual connection is explicit. No new ground-isolation component is supported.

**Verify:** netlist includes U3 grounds, capacitor returns, BT1.2, U4.2/U5.2 and actual ADC grounds on the same return net; DVDD/AVDD remain separate positives. Check board 3V3-to-GND voltage directly after corrections.

## Calculations and checks that constrain the conclusions

### Dropout and missing battery limits (E2)

The labels give only 0.400 V nominal headroom. The following use maximum listed dropout at stated loads/temperature, added to the nominal 3.3 V target; they are **not full minimum-battery specifications**, because output tolerance and actual load/range remain to be included.

| Regulator/chip | Load | Maximum dropout over full stated temperature range |3.3 V+dropout |
|---|---:|---:|---:|
| TLV75533P |500 mA|0.238 V|3.538 V|
| LP2985 legacy |150 mA|0.575 V|3.875 V|
| LP2985 new chip |150 mA|0.254 V|3.554 V|
| LP2985 legacy |50 mA|0.225 V|3.525 V|
| LP2985 new chip |50 mA|0.184 V|3.484 V|

Actual signoff uses `VIN(min under load) ≥ VOUT(max tolerance) + VDO(max at selected load/temperature)` and the selected part’s recommended-input conditions. Do not assume U4 supplies 150 mA, a particular battery chemistry/cutoff, or fixed current sharing in the present parallel circuit. No added boost/buck architecture is justified until those requirements show a need.

### Nominal digital levels (I1)

For V0’s intended 3.3 V digital interface and common actual AGND, the stated static limits are compatible. Zero guaranteed margin on one comparison calls for realistic validation; it is not a demonstrated fault.

| Direction | Transmitter guarantee | Receiver requirement | Result at 3.3 V |
|---|---|---|---|
| ESP→ADS high |VOH≥0.8VDD=2.64 V|VIH≥0.8DVDD=2.64 V|Meets boundary; no extra guaranteed high margin |
| ESP→ADS low |VOL≤0.1VDD=0.33 V|VIL≤0.2DVDD=0.66 V|Compatible |
| ADS→ESP high |VOH≥DVDD−0.4=2.90 V|VIH≥0.75VDD=2.475 V|Compatible |
| ADS→ESP low |VOL≤0.4 V|VIL≤0.25VDD=0.825 V|Compatible |

Use each datasheet’s stated output test conditions/drive settings; these figures do not bound arbitrary firmware settings or transients. V1’s floating/incorrect supply-reference network prevents the same valid-domain calculation until repaired. No level shifter is supported merely because different chip families are used.

### ADS1298 input architecture (I4)

Each lead’s external network has `R×C=2000×620pF=1.24µs`, giving a simple external one-pole corner of about 128.4 kHz. A 1.2 nA input-bias bound through the drawn 2 kΩ alone produces 2.4 µV. These calculations neither describe the total electrode source impedance nor prove 24-bit accuracy. ADS1298 has CMOS PGA inputs followed by delta-sigma modulators/digital filters; generic SAR sample-and-hold settling assumptions do not establish a fault here. Actual electrode/source impedance, gain, lead-off settings, data rate and allowed settling error are needed. No added buffer follows from the existing resistor value alone.

### Optional RLD change and limits of the evidence

V0 U1 has 1 MΩ R36 parallel 1.5 nF C73 between RLDOUT63 and RLDINV61, with one J1 reference electrode at output. U2 has the analogous R1/C1 toward the other J1 instance, but U2 RLDOUT63 is unconnected in the actual schematic. Text saying “RLDIN -> RLDOUT on PCB” is not a schematic connection. Both RLDREF60 and RLDIN62 are unconnected in V0; their chosen operating modes are undocumented. V1 removes the feedback networks and reference-electrode symbols, leaves RLDOUT/RLDINV/RLDREF unconnected and ties unused RLDIN to the positive-named rail. This does not prove measured common-mode failure, instability or clipping, particularly while optional circuits may be disabled. No independent RLD/electrode-safety/layout/performance review was conducted.

## Condition-by-condition audit

Classification is the comparison result. **CANNOT VERIFY with P0 at A1/F1 means the V0 numerical comparison is unresolved but a V1 fault is already confirmed.** A dash priority means no demonstrated remaining problem under that condition; UNKNOWN means insufficient evidence to rank an alleged failure. Exact proposed corrections above are shared by overlapping rows.

## A. Analog — supply pins

### A1 — An IC supply pin operates above its rating or below its minimum operating voltage.

**Status:** CANNOT VERIFY. **Priority:** P0.

**V0 — U1/U2 ADS1298; U6 ESP32; U4/U7 LDOs:** ADC AVDD/AVDD1 pins 19/21/22/54/56/59 are on source-free +3.3VA. This confirms missing power under H2, but the floating voltage cannot be assigned a number. DVDD48/50 and U6.2 are on +3.3V relative to AGND.

**V1 — U1/U2 ADS1298; U3 DevKit; U4/U5 LDOs:** CONFIRMED V1 failure: AVDD/AVDD1 and AVSS are AGND, so analog span is 0 V. DVDD48/50 instead joins isolated DGND; U3 grounds are on that island. A valid digital supply span is also not established.

**Exact evidence:** v0/v1.net.xml: +3.3VA, +3.3V, AGND, DGND; embedded PAG pin tables; see Findings 1/4/7/8 above.

**Difference / conclusion:** V0 missing analog source became a V1 ground connection. CANNOT VERIFY applies to the strict before/after voltage comparison, not to the proven V1 fault. Do not call this fixed or assume V0 was 0 V.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §§6,7.1,7.3: analog span 2.7–5.25 V; digital span 1.65–3.6 V. No valid span exists with the V1 analog pins on one net.

**Simplest correction:** Implement the connection-only corrections in Findings 1/7/8: separate positive supplies from ground; use valid analog/digital 3.3 V sources.

**Verification:** Re-export corrected netlist; then measure each supply relative to its actual ground at U1/U2/U3. Specify battery limits before rating signoff.

## B. Analog — resistors

### B1 — A resistor dissipates more power than its footprint or component rating allows.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — R3–R19/R21–R35=2 kΩ; R1/R36=1 MΩ; R20=10 kΩ:** No resistor power ratings, manufacturer parts or footprints specified; electrode voltages are unspecified. No demonstrated excessive resistor dissipation.

**V1 — R1–R32=2 kΩ:** Same input resistance; power ratings/parts still absent. Feedback and module-EN resistors removed with their circuits.

**Exact evidence:** Complete symbol properties and both connectivity exports; resistor values are explicit, ratings are not.

**Difference / conclusion:** Renumbering the input resistors does not prove a power-rating improvement.

**Requirement / calculation:** P=V²/R or I²R; compare with actual specified resistor rating. Illustratively 3.3 V across 2 kΩ gives 5.445 mW; across 10 kΩ gives 1.089 mW. These are conditional, not measured operating losses.

**Simplest correction:** No value/component change justified. Obtain power-rated BOM parts and actual applied-voltage bounds.

**Verification:** Calculate worst-case loss from actual inputs/states and compare to selected part ratings.

## C. Analog — capacitors

### C1 — Voltage across a capacitor reaches or exceeds its rating.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — All capacitors; especially C65/C4 VCAP3:** Capacitances are given, but voltage ratings and orderable parts are absent.

**V1 — All capacitors; especially C25/C51 VCAP3:** Ratings remain absent. VCAP3 is an important check after supply correction; it is not simply a 3.3 V node.

**Exact evidence:** All capacitor properties lack voltage-rating fields. V0 U1.55→C65.1, U2.55→C4.1; V1 U1.55→C25.1, U2.55→C51.1; returns AGND.

**Difference / conclusion:** VCAP capacitors retained with changed references; no demonstrated voltage-rating fix.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) PAG pin 55 description: VCAP3 is internally AVDD+1.9 V, referenced to AVSS. At a corrected 3.3 V analog span this is approximately 5.2 V; actual capacitor rating must exceed its maximum applied voltage.

**Simplest correction:** Get capacitor voltage ratings, actual analog/battery limits and relevant node maxima; do not change capacitance or add capacitors from this check alone.

**Verification:** Compare maximum pin-to-pin voltage with each selected capacitor rating. No tolerance/DC-bias-derating review performed.

### C2 — A capacitor has a pin connected to nothing.

**Status:** NOT FOUND. **Priority:** —.

**V0 — C1–C73 as populated:** Every drawn capacitor pin joins a net containing another component connection.

**V1 — C1–C57:** Every drawn capacitor pin likewise joins another component connection.

**Exact evidence:** Both complete XML netlists: each capacitor has both pins present, with another connected component. Floating supply networks are covered separately, not mistaken for a physically unconnected pin.

**Difference / conclusion:** No open capacitor terminal established in either revision.

**Requirement / calculation:** A connected resistor/IC terminal is a connection even if the larger network is floating.

**Simplest correction:** None under C2.

**Verification:** Connectivity check completed; inspect C3/H2 separately for invalid returns/sources.

### C3 — A decoupling capacitor has a floating ground connection.

**Status:** NEW IN V1. **Priority:** P0.

**V0 — C20/C21/C71/C72 and other return capacitors:** All capacitor returns that are drawn as ground connect to the battery-negative AGND/GND net.

**V1 — C8=0.1 µF, C9=10 µF, C34=0.1 µF, C35=10 µF:** Each pin 1 is +3.3V; pin 2 is isolated DGND. That net has no valid battery/regulator ground connection. This is the same return-network defect as H1, not four separate faults.

**Exact evidence:** v1.net.xml: DGND includes these four pin 2 terminals and U3 grounds, but excludes BT1.2/U4.2/U5.2; V0 counterparts return to AGND.

**Difference / conclusion:** The return symbols changed electrically: V0 returns were valid; V1 returns land on a separate net.

**Requirement / calculation:** Decoupling must connect between the supplied rail and its receiving circuit’s valid return; ADS actual DGND33/49/51 is AGND here.

**Simplest correction:** First remove ADC DVDD48/50 from DGND and connect them to digital 3.3 V. Then join genuine DGND returns to battery/regulator ground; retain these capacitor values.

**Verification:** Netlist must place capacitor pin 2, MCU ground and BT1.2 on one return net, with ADC DVDD separate; measure rail across each capacitor after correction.

### C4 — A voltage regulator has insufficient output capacitance.

**Status:** NOT FOUND. **Priority:** —.

**V0 — U4/C44=2.2 µF; U7/C46=200 µF:** Both regulators have nominal output capacitance meeting their stated minimums.

**V1 — U4/C54=2.2 µF; U5/C57=200 µF:** Same nominal values; no minimum-capacitance shortfall demonstrated.

**Exact evidence:** C44/C54 pin 1→U4.5; C46/C57 pin 1→U7.5/U5.5; all pin 2→AGND. Presently both outputs share +3.3V.

**Difference / conclusion:** Capacitance unchanged; this is NOT FOUND, not FIXED. No excluded tolerance/DC-bias investigation undertaken.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) §6.3/§7.1.2: legacy minimum 2.2 µF (new-chip requirements differ); [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) pin table/§7.1.1:1 µF nominal recommended, with at least 0.47 µF effective for stability. Drawn nominal values do not show a minimum shortfall.

**Simplest correction:** Preserve each existing output capacitor on its own LDO output when separating E5; no increase justified by this check.

**Verification:** Connectivity/value check completed. Actual part selection/ESR remains C5; no performance certification implied.

### C5 — A regulator requires output-capacitor ESR but uses only unsuitable ceramic capacitors.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U4/C44; U7/C46:** Capacitor technology/ESR and exact LP2985 orderable chip identity are absent.

**V1 — U4/C54; U5/C57:** Same limitation; a generic unpolarized capacitor symbol does not establish ceramic technology or ESR.

**Exact evidence:** No capacitor manufacturer, technology or ESR properties. U4 is only LP2985-3.3, without complete orderable suffix.

**Difference / conclusion:** No evidence either revision used only unsuitable ceramics; do not infer an ESR fix from renumbering.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) §§7.1.1–7.1.2 distinguish legacy stability/ESR requirements and a new ceramic-stable chip; [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) supports ceramic output capacitors. ESR is the small effective resistance in series with a real capacitor.

**Simplest correction:** Identify U4 generation and capacitor parts; compare the complete output network to that chip’s stability requirements. Add resistance/change parts only if this demonstrates a mismatch.

**Verification:** BOM/part-marking check and ESR-versus-temperature/frequency specifications; stability measurement only if still uncertain.

### C6 — Missing or insufficient decoupling causes a rail dip greater than 5%.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — ADC decoupling; C44/C46/C47/C48; U6:** Capacitors exist; missing analog source is H2. No transient evidence establishes a greater-than 5% dip.

**V1 — ADC decoupling; C54/C57; U3:** Four invalid capacitor returns are confirmed under C3. No rail waveform establishes dip magnitude.

**Exact evidence:** Supply capacitors in both exports; no load-step waveform, supply impedance or validated transient model supplied.

**Difference / conclusion:** V1 return error worsens supply integrity, but a numerical droop cannot be fabricated.

**Requirement / calculation:** 5% of 3.3 V=0.165 V. A static wiring defect does not specify a time-varying voltage dip.

**Simplest correction:** Correct C3/H1/H2/E5/E6 first; do not add bulk capacitance without a demonstrated transient need.

**Verification:** Measure rail-to-local-ground during startup and intended peak loads, with actual battery/source impedance; compare droop with 165 mV.

### C7 — A capacitive load makes an amplifier unstable.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1 RLDOUT63; R36=1 MΩ/C73=1.5 nF; J1:** Output electrode/cable load and enabled RLD settings are unknown. Feedback capacitance is not proof of an unstable load.

**V1 — U1/U2 internal RLD/PGA/PACE:** External RLD feedback/electrode output networks removed; no external amplifier output load is drawn. No instability demonstrated.

**Exact evidence:** V0 U1.63→R36/C73/J1; V1 RLDOUT63 NC. V0 U2.63 also NC, despite a schematic note about a PCB connection.

**Difference / conclusion:** Removing an optional circuit does not prove that a demonstrated instability was corrected.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) RLD/optional-output sections apply only to the enabled configuration and actual load.

**Simplest correction:** No compensation component change justified; obtain actual enabled-loop and load information.

**Verification:** After valid supplies, simulate the actual enabled loop with cable/electrode model or measure step/ringing response; V1 external-load case is absent.

## D. Analog — LEDs

### D1 — An LED has no suitable current limitation.

**Status:** NOT FOUND. **Priority:** —.

**V0 — No LED in V0 schematic:** No relevant LED circuit in the module carrier.

**V1 — U3 reference-board D5/R11 and D6:** Official DevKit reference power LED D5 has R11=5.1 kΩ; RGB D6 is a smart LED with internal driver. No missing external current limiter found.

**Exact evidence:** V0 complete symbol inventory; official DevKitC v1.1 sheet 2 shows D5/R11 and SK68XXMINI-HS D6. Exact fitted board revision is unspecified.

**Difference / conclusion:** V1 introduces a board with documented LED circuits, not a demonstrated LED fault.

**Requirement / calculation:** [Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) sheet 2: passive LED series resistance is present. At 3.3 V, even zero LED forward voltage gives 3.3/5100=0.647 mA through R11. D6 is not a bare LED requiring a GPIO series-current resistor.

**Simplest correction:** None supported. Confirm fitted board if it differs from the official reference.

**Verification:** Reference-board schematic check completed; inspect actual board documentation if variant differs.

### D2 — An LED is driven directly into an open-collector sink causing incorrect operation/excessive current.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No LED/open-collector arrangement.

**V1 — U3 reference-board LEDs:** No such direct LED/open-collector arrangement is shown in the carrier or reference board.

**Exact evidence:** Complete carrier inventories and official board schematic.

**Difference / conclusion:** No relevant arrangement introduced.

**Requirement / calculation:** No applicable LED sink arrangement.

**Simplest correction:** None.

**Verification:** No further check under this condition.

## E. Analog — regulators

### E1 — Regulator input voltage exceeds the maximum rating.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — BT1; U4.1/U7.1:** Both inputs are labelled +3.7V, below their limits nominally; actual BT1 maximum is unspecified.

**V1 — BT1; U4.1/U5.1; U3 onboard LDO:** Same external source; fitted board and its USB/header use are unspecified.

**Exact evidence:** BT1 has only generic Battery value; no chemistry, cell count, charger, cutoff or min/max specification.

**Difference / conclusion:** No nominal overvoltage shown and no demonstrated input-rating fix.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) input recommended maximum 16 V; [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) recommended maximum 5.5 V, absolute maximum 6 V. The rail name alone cannot establish worst-case voltage.

**Simplest correction:** Specify maximum source/charger voltage; change parts only if actual range exceeds limits.

**Verification:** Compare maximum loaded/unloaded source voltage, including charging if applicable, against actual fitted regulator ratings.

### E2 — A regulator enters dropout during expected operation.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U4 LP2985-3.3; U7 TLV75533PDBV:** Battery minimum under load and actual regulator current sharing unknown.

**V1 — U4; U5 TLV75533PDBV:** Same nominal voltages, same missing operating-range data; current-sharing error remains E5.

**Exact evidence:** Both inputs +3.7V, both nominal outputs 3.3 V: labelled headroom 3.7−3.3=0.400 V. See the dropout calculation above.

**Difference / conclusion:** Neither voltage label nor reference change demonstrates adequate headroom across battery discharge.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) electrical table and [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) §5.5 specify load/temperature-dependent dropout. Dropout is the extra input voltage required above the output to maintain regulation.

**Simplest correction:** Get minimum battery voltage, cutoff, load and chip identity; check headroom before selecting any replacement regulator or converter.

**Verification:** Use VIN(min,loaded)≥VOUT(max)+VDO(max at actual load/temperature), then measure near battery cutoff.

### E3 — A regulator is disabled by its own enable arrangement or remains latched off.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U4.3/U7.3 /EN:** Undriven shared enable is confirmed under E6; its actual voltage/off state is not known. No self-output dependency is drawn.

**V1 — U4.3/U5.3 /EN:** Same; no proven latch-off sequence or self-powered enable arrangement.

**Exact evidence:** /EN contains only the two enable inputs in each revision. It does not connect to either output rail, MCU EN or a power-good output.

**Difference / conclusion:** E6 persists; do not count an imagined latched-off waveform as another verified fault.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) and [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) enable requirements apply. An undriven input does not establish a specific measured low state or latch behavior.

**Simplest correction:** Correct E6 with a defined always-on connection or specified shutdown controller.

**Verification:** Measure EN and both outputs through cold start/power cycling after wiring corrections; no latch claim without a waveform.

### E4 — Regulator output voltage does not match the voltage indicated by its rail name.

**Status:** NOT FOUND. **Priority:** —.

**V0 — U4.5/U7.5:** Both 3.3 V fixed-output types drive +3.3V.

**V1 — U4.5/U5.5:** Both 3.3 V fixed-output types still drive +3.3V.

**Exact evidence:** Exact component values LP2985-3.3 and TLV75533PDBV; exported output net +3.3V.

**Difference / conclusion:** Missing V0 +3.3VA source and grounded V1 AVDD are supply wiring faults, not mismatched LDO setpoints.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf)/[TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) fixed-output part identities.

**Simplest correction:** None under E4; fix H2/A1 separately.

**Verification:** Part-identity/net-name check completed.

### E5 — Two regulator outputs drive the same rail.

**Status:** STILL PRESENT. **Priority:** P1.

**V0 — U4.5 LP2985; U7.5 TLV75533:** Both output pins directly share +3.3V.

**V1 — U4.5 LP2985; U5.5 TLV75533:** Same direct parallel outputs. Reference DevKit onboard LDO can additionally drive the header rail if USB/5 V powers it; that use is unverified.

**Exact evidence:** Both netlists +3.3V; both ERC reports explicitly flag the two LDO power outputs. V1 U3.1/.2 also +3.3V.

**Difference / conclusion:** U7→U5 is renumbering; topology did not change. No measured oscillation, damage or particular overload is claimed.

**Requirement / calculation:** [TI parallel-LDO reference, §2.2.1.1](https://www.ti.com/lit/pdf/tiducs7): independent regulator references require a deliberate sharing arrangement. Directly tying these outputs provides no specified current sharing; do not add 150 mA+500 mA as an available rating.

**Simplest correction:** Separate existing outputs: U4.5 plus C54 to analog +3.3VA; U5.5 plus C57 to digital/MCU +3.3V. Use one approved DevKit supply mode; no added mux or sharing circuit needed.

**Verification:** Corrected netlist must separate U4.5/U5.5 and assign intended loads/caps; check each load budget and board supply mode; repeat targeted ERC.

### E6 — Regulator enable input floats or depends incorrectly on another rail’s power-good.

**Status:** STILL PRESENT. **Priority:** P1.

**V0 — U4.3/U7.3 /EN:** Only these two input pins occupy /EN; there is no driver, pull or switch.

**V1 — U4.3/U5.3 /EN:** Exactly the same omission; no power-good output is present.

**Exact evidence:** Netlists /EN pin memberships; ERC undriven U4.3. Module U6.3 EN is a different net.

**Difference / conclusion:** Moving and renumbering regulators did not add an enable source.

**Requirement / calculation:** [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf) ON/OFF must be terminated; [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf) EN needs a valid level. Neither diagram provides one.

**Simplest correction:** For always-on operation, connect both enable pin 3 inputs directly to their common input +3.7V (pin 1 supply), subject to specified source range. No resistor needed. If shutdown is required, define its source/default first.

**Verification:** Netlist /EN must include the intended driver/input supply; measure enables and outputs at startup.

### E7 — A switching regulator directly supplies an analog IC with potentially unacceptable noise.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — U4/U7:** Both explicit regulators are linear LDOs.

**V1 — U4/U5/U3 reference onboard regulator:** Linear LDO supply path; no switching regulator shown.

**Exact evidence:** Complete power-component inventory; manufacturer identities and official DevKit schematic.

**Difference / conclusion:** No applicable switching regulator introduced.

**Requirement / calculation:** No switching-regulator arrangement to evaluate.

**Simplest correction:** None; no independent analog-noise/layout investigation.

**Verification:** No additional check under E7.

### E8 — A regulator cannot sink current when a required output-setpoint change occurs.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — U4/U7:** Fixed 3.3 V parts; no output-setpoint switching.

**V1 — U4/U5:** Same fixed outputs; no required setpoint-lowering transition.

**Exact evidence:** No feedback-programming circuit or switched setpoint in either full schematic.

**Difference / conclusion:** No applicable arrangement.

**Requirement / calculation:** No required setpoint transition to evaluate. TLV active discharge is not evidence of such a system requirement.

**Simplest correction:** None.

**Verification:** No additional check under E8.

### E9 — A control/signal voltage rises before the receiver supply is valid.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6→U1/U2 control nets:** No ramp or pre-firmware waveform; analog rail is source-free.

**V1 — U3→U1/U2 controls; TEST/PACE17/18 and RLDIN62:** No measured ordering. Separately, V1 hard-ties unused analog pins to +3.3V while AVDD is grounded: a confirmed static overvoltage if 3.3 V is on, described in Finding 1. It is not an invented ramp.

**Exact evidence:** /PWDN,/RESET,/START,/CS*,MOSI,SCLK; v1 analog pins 17/18/62 on +3.3V vs AVDD on AGND.

**Difference / conclusion:** Supply/control wiring changed, but actual event order is not supplied. Static analog-pin hazard uses the same AVDD repair, not another independent count.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §11.1: keep digital inputs low until supplies stabilize. Analog input bound §7.1 is AVDD+0.3 V; with grounded AVDD, intended 3.3 V exceeds 0.3 V.

**Simplest correction:** Correct supply wiring and move unused analog pin ties to the corrected analog rail; define reset defaults and firmware release order.

**Verification:** Scope AVDD/DVDD/controls through cold start, MCU reset and intended external-board power modes; inspect firmware initialization.

## F. Analog — amplifiers

### F1 — Amplifier supply span exceeds or falls below its allowed limits.

**Status:** CANNOT VERIFY. **Priority:** P0.

**V0 — U1/U2 internal PGA/RLD:** Analog supply has no valid source; numeric voltage on +3.3VA unknown.

**V1 — U1/U2 internal PGA/RLD:** CONFIRMED V1: amplifier analog supply span 0 V because AVDD and AVSS share AGND.

**Exact evidence:** Same exact supply pins as A1/H2; no separate external op-amp exists.

**Difference / conclusion:** Strict comparison cannot assign V0 a voltage; V1 failure is confirmed. Same root as H2, not an additional amplifier defect.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) supply ratings apply to its internal analog circuits.

**Simplest correction:** Fix the analog supply in Finding 1; no amplifier replacement.

**Verification:** Check corrected span/netlist, then measure AVDD−AVSS against the 2.7–5.25 V operating range.

### F2 — Amplifier positive/negative supply pins are reversed.

**Status:** NOT FOUND. **Priority:** —.

**V0 — U1/U2 internal analog circuits:** AVSS is grounded; AVDD is source-free, not shown connected to a negative source.

**V1 — U1/U2 internal analog circuits:** AVDD and AVSS are the same net. This is zero span, not reversed polarity.

**Exact evidence:** PAG supply pin definitions and both netlists.

**Difference / conclusion:** Do not relabel A1/H2 as reversed supplies.

**Requirement / calculation:** A reversed supply requires positive supply below negative supply; no such deliberate connection established.

**Simplest correction:** None under F2; correct A1/H2.

**Verification:** Pin polarity check completed; power fault remains independently verified.

### F3 — Amplifier input is outside its common-mode range.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1/U2 input pairs and optional RLD:** Electrode common-mode/DC offsets and enabled bias configuration unknown.

**V1 — U1/U2 input pairs; RLD circuit removed:** No external bias source shown, but this alone does not prove the electrodes’ actual common-mode voltage is invalid.

**Exact evidence:** Input pin pairs 16/15,14/13,12/11,10/9,8/7,6/5,4/3,2/1;2 kΩ/620 pF networks unchanged. See the RLD mapping above.

**Difference / conclusion:** Removing RLD is an electrical change, but is not proof that a measured common-mode fault exists or was fixed. Invalid supplies must be corrected first.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §9.3.1.5.1 equation 2 gives PGA common-mode limits; §9.3.1.5.2 equation 3 gives differential range. Common-mode means the average (INP+INN)/2; it differs from the small differential EMG signal.

**Simplest correction:** No independent bias/RLD redesign justified. Obtain actual source model, offsets, gain/reference/lead-off/RLD settings.

**Verification:** Measure input average and difference relative to actual chip ground; compare to the programmed gain/reference and datasheet limits after supply repair.

### F4 — Amplifier oscillates/rings because of inadequate stability or phase margin.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1 RLD loop; internal amplifiers:** No loop model or measured response;1 MΩ∥1.5 nF feedback does not certify or disprove stability.

**V1 — U1/U2 optional internal amplifiers:** External RLD loop removed; enabled states unknown. Unconnected feedback on a disabled optional amplifier is not proof of oscillation.

**Exact evidence:** V0 R36/C73 and R1/C1; V1 RLDINV61/RLDOUT63 NC. No simulation or waveform supplied.

**Difference / conclusion:** No demonstrated oscillation in either revision; do not call deletion a verified fix.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) RLD sections apply to actual enabled loop/load; phase margin is the stability reserve of a feedback loop.

**Simplest correction:** No compensation change without actual loop/load evidence.

**Verification:** For an enabled loop, simulate its real load or measure ringing/oscillation after correcting supplies; V1 drawn external RLD loop is absent.

### F5 — Amplifier output is clipped, saturated or overloaded.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1/U2 PGA and RLD:** Actual input magnitude/DC offset, gain/reference, RLD enable and load unknown.

**V1 — U1/U2 PGA and optional outputs:** Same missing acquisition configuration/source data. The confirmed supply fault already prevents valid operation; it does not specify an output waveform.

**Exact evidence:** Input/output netlists and absence of firmware/source/load data.

**Difference / conclusion:** No separate clipping or overload fault proven; no fix credited.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §7.3 differential full scale±VREF/gain and §9.3.1.5.1 PGA headroom apply to validly powered operation.

**Simplest correction:** Repair supply wiring, obtain configuration and inputs; change gain/bias/load only if limits are exceeded.

**Verification:** Measure or calculate PGA input/output headroom with actual DC offsets and configured gain/reference; measure any enabled external output load.

## G. Analog — power multiplexers

### G1 — Power multiplexer output remains off.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G2 — Priority input is never used.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G3 — A power-multiplexer input is rejected incorrectly.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G4 — Expected power-multiplexer failover does not work.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G5 — A power-multiplexer control pin floats.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G6 — A power-multiplexer input is disconnected.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

### G7 — Power-multiplexer output rail specifies a voltage no input can provide.

**Status:** NOT APPLICABLE. **Priority:** —.

**V0 — None:** No power multiplexer.

**V1 — None:** No power multiplexer.

**Exact evidence:** Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.

**Difference / conclusion:** No mux introduced.

**Requirement / calculation:** No relevant multiplexer requirement.

**Simplest correction:** None; no additional mux architecture is justified.

**Verification:** Not applicable.

## H. Analog — wiring

### H1 — An IC has no valid ground connection.

**Status:** NEW IN V1. **Priority:** P0.

**V0 — U1/U2; U6; U4/U7:** Actual ADC DGND33/49/51, AVSS, MCU GND1/40/41 and LDO GND2 all connect to BT1.2 on AGND/GND. The separately named DGND control island is not an actual V0 IC supply-ground connection.

**V1 — U3 GND22/23/24/44; U1/U2 ground pins:** U3 grounds connect only to isolated DGND, while BT1.2/LDO grounds and actual ADC grounds remain AGND. No valid controller DC return.

**Exact evidence:** Both netlists AGND/DGND memberships; raw V1 ground-box tie(36.83,267.97)→(48.26,267.97)mm joins AGND and GND only, not DGND.

**Difference / conclusion:** V1 moves the controller return onto a previously isolated control-reference net. It also moves four decoupler returns there (C3).

**Requirement / calculation:** [Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf)/[Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf): supply must be referenced to actual board/module ground. A symbol named DGND does not automatically join AGND.

**Simplest correction:** After moving misplaced ADC DVDD pins off DGND, connect genuine MCU/digital returns to BT1.2/U4.2/U5.2 common ground. No isolated-ground architecture needed.

**Verification:** Netlist continuity from every genuine IC ground to BT1.2, excluding positive supplies; measure U3 supply between its 3V3 and GND headers after correction.

### H2 — A power rail is disconnected from all valid sources.

**Status:** STILL PRESENT. **Priority:** P0.

**V0 — U1/U2 +3.3VA:** Analog rail contains only ADC positive-supply pins and decouplers; no battery/regulator output.

**V1 — U1/U2 AVDD/AVDD1 and DVDD:** Analog positive supply now grounded instead of reaching a positive source; digital positive supplies also moved off +3.3V to isolated DGND.

**Exact evidence:** v0.net.xml +3.3VA members; v1.net.xml AGND/DGND. ADC AVDD19/21/22/54/56/59; DVDD48/50.

**Difference / conclusion:** Analog power remains invalid and is worsened by a direct ground tie; separate V1 digital-supply error is Finding 7.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) requires valid positive analog/digital supplies, not merely similarly named capacitor buses.

**Simplest correction:** Connect ADC analog positives to the separated U4 analog output, digital positives to U5 digital output; preserve actual ground pins.

**Verification:** Re-export pin-to-net membership; ensure each positive supply has exactly the intended source, then verify DC rail spans.

## I. Mixed-signal

### I1 — Logic voltage is too low/high for the receiving component.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6↔U1/U2; floating DGND straps:** At nominal common 3.3 V, normal SPI/DRDY thresholds are compatible. DGND control island has no guaranteed logic-low reference (J3).

**V1 — U3↔U1/U2:** No valid digital supply/reference due to DVDD and ground errors. Actual voltages on that island cannot be calculated from its name.

**Exact evidence:** V0 valid interface nets +3.3V/AGND; V1 DVDD→DGND, actual ADC DGND→AGND and U3 GND→DGND. See the logic comparison table above.

**Difference / conclusion:** 3.3 V digital interfaces were not inherently incompatible; V1 introduces supply/reference faults, already counted separately.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) digital thresholds; [Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) DC levels. Compatibility at limits is not proof of a measured voltage violation or adequate dynamic margin.

**Simplest correction:** Correct supplies/grounds and low-level straps first. No level shifter justified by nominal 3.3 V interfaces alone.

**Verification:** Measure actual transmitter VOH/VOL at receiver pins versus local supply/ground and VIH/VIL; verify configured direction/drive.

### I2 — A digital signal edge is too slow for its interface.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — SPI/START/RESET/DRDY:** No measured edge rate or total load supplied; no large external RC on SPI nets.

**V1 — Same; shared MISO:** Changed pin mapping/bus loads do not establish an edge-rate violation.

**Exact evidence:** Digital netlists; no timing waveform, trace/cable load or firmware clock-rate specification.

**Difference / conclusion:** No demonstrated slow edge fixed or introduced. A missing clock is not a slow edge.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) serial timing requirements apply; SCLK has a Schmitt input (§9.5.1.2).

**Simplest correction:** No series/parallel component change supported.

**Verification:** Scope actual edges at receiver under selected SPI speed/load; compare to datasheet timing. No separate general signal-integrity review.

### I3 — An open-drain signal lacks a pull-up or has an excessively strong pull-up.

**Status:** NOT FOUND. **Priority:** —.

**V0 — U1/U2 DOUT43 and DRDY47:** These are driven outputs, not open-drain lines needing generic pull-ups. No power-good line exists.

**V1 — U1/U2 DOUT/DRDY; U3 reference reset circuitry:** ADC signals remain driven outputs. Official board reset/autoprogram sinks have a documented 10 kΩ CHIP_PU pull-up; no missing relevant pull-up found.

**Exact evidence:** ADS pin/interface definitions; reference-board R5=10 kΩ on CHIP_PU. No carrier open-drain interface appears.

**Difference / conclusion:** No demonstrated open-drain pull fault. Do not add a DRDY pull-up by habit.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) digital-output definitions and [Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) reset circuit.

**Simplest correction:** None supported. Excluded general sink-capability review not undertaken.

**Verification:** Interface-type and reference-board pull-up check completed; fitted board variant still to confirm.

### I4 — ADC source impedance/settling prevents valid acquisition.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1/U2 input 2 kΩ/620 pF networks:** Actual electrode impedance versus frequency and data-rate/gain/settling requirements absent.

**V1 — U1/U2 R1–R32 and input 620 pF caps:** Same electrical filter values; no demonstrated acquisition fault from the drawn series resistors.

**Exact evidence:** All 16 differential pairs have 2 kΩ on each lead and 620 pF to AGND at ADC side. See filter calculation and mapping above.

**Difference / conclusion:** Filter renumbering is not a fix. Source/load and selected digital-filter settling remain unknown.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) CMOS PGA inputs precede delta-sigma conversion; do not apply a generic SAR sample-capacitor acquisition model.

**Simplest correction:** No added buffer or resistor/capacitor change justified.

**Verification:** Obtain actual electrode source model, gain/data-rate and valid-settling criterion; apply a representative input step and check settled output after supplies/clocks are repaired.

### I5 — A slow signal enters a non-hysteretic input or crosses threshold repeatedly.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — Control inputs; U6 EN RC:** No signal waveform demonstrating a slow/chattering crossing. Module EN has its RC network.

**V1 — Control inputs; U3 internal reset RC:** Reference board has built-in EN/reset network; no measured repeated crossings. ADC clock omission is not proof of chatter.

**Exact evidence:** No threshold-crossing waveform or noise amplitude supplied; SCLK explicitly has hysteresis in ADS documentation.

**Difference / conclusion:** Moving the EN RC inside the development board does not show its removal.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §9.5.1.2 identifies SCLK Schmitt hysteresis (different rising/falling thresholds). Other control waveforms must be checked individually.

**Simplest correction:** No Schmitt buffer or RC change justified without waveform evidence.

**Verification:** Measure relevant slow control/enable ramps and compare input hysteresis/threshold requirements for the actual component.

## J. Firmware — reset conditions

### J1 — A boot-strapping pin floats or is held at the wrong level.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6 GPIO0 pin 27; GPIO3 pin 15; GPIO45 pin 26; GPIO46 pin 16:** GPIO0/45/46 have defined internal default pulls. GPIO3 has no pull, but its effect depends on eFuse-selected JTAG policy; normal boot failure is unproven.

**V1 — U3 GPIO0 pin 31; GPIO3 pin 13; GPIO45 pin 30; GPIO46 pin 14:** Same strap issue; board adds normal boot/reset hardware. Required GPIO3/JTAG setting is unspecified.

**Exact evidence:** Both inventories, ESP strapping table, module §4.4. GPIO3 is physically floating; that observation is not proof that the application requires either level.

**Difference / conclusion:** No demonstrated boot fix or new boot fault.

**Requirement / calculation:** [Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) boot/JTAG strapping tables: GPIO3 affects JTAG source only under relevant nondefault eFuse selection.

**Simplest correction:** Do not add a GPIO3 resistor without selecting a required debug/JTAG state. If required by eFuse policy, bias it to that chosen state.

**Verification:** Read eFuses and required boot/debug configuration; confirm normal cold boot. Do not mistake all unconnected GPIOs for floating boot straps.

### J2 — A switch/enable relies only on an uncertain controller reset pull state.

**Status:** STILL PRESENT. **Priority:** P1.

**V0 — U6 GPIO6→U1/U2 PWDN35:** ADC power-down/enable depends on a GPIO with no guaranteed reset bias; no external pull.

**V1 — U3 GPIO7→U1/U2 PWDN35:** Same omission after GPIO remap.

**Exact evidence:** /PWDN net contains only GPIO and both ADC inputs; ESP reset table gives no WPU/WPD/drive on used GPIO6/7.

**Difference / conclusion:** Controller pin changed, hardware default did not. This overlaps the reset-bias root under J3.

**Requirement / calculation:** [Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) Table 2-1 reset states; [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) control input definitions/§11.1.

**Simplest correction:** Add one 10 kΩ pulldown on shared /PWDN to valid ADC ground, as part of the reset-default correction in Finding 5.

**Verification:** Hold controller reset and measure /PWDN before firmware; calculate leakage versus pull strength and verify startup sequence.

### J3 — A transistor gate/regulator enable/control input floats during controller idle/reset.

**Status:** PARTIALLY FIXED. **Priority:** P0.

**V0 — U4/U7 EN; U1/U2 controls, CLKSEL and DGND straps:** Floating LDO enable, unreferenced DGND strap island, ADC reset/start/enable GPIO nets, and CLK37 tied only to CLKSEL52.

**V1 — U4/U5 EN; U1/U2 controls/CLKSEL; U3:** Several controls remain undefined. U1 CLKSEL now has a deliberate +3.3V tie; U2 selects external clock via isolated DGND, and its ADC_CLK has no source because U1 CLK37 is disconnected.

**Exact evidence:** V0 CLK/CLKSEL two-pin-only nets; V1 U1.37 NC, dangling ADC_CLK label, U2.37 sole ADC_CLK member. /EN and reset nets as above. Board U3 CHIP_PU has internal R5/C6 and is not a missing external pull fault.

**Difference / conclusion:** A local clock-selection wiring improvement earns PARTIALLY FIXED, not FIXED; its logic level is usable only after supply repair. Other floating-control faults persist, and slave clock routing remains incomplete. Row spans Findings 2/4/5/6; do not count it as one independent extra fault.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) Table 11 and CONFIG1: reset CLK_EN=0 makes CLK either input or tri-state, so V0 self-tie cannot bias CLKSEL. [Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) reset defaults do not drive used ADC controls. [Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) provides its own EN pull/RC.

**Simplest correction:** Complete existing master clock connection U1.37→ADC_CLK→U2.37, keep U1 CLKSEL at digital high and U2 at valid ground, set U1 CLK_EN in firmware; define ADC reset defaults and fix /EN/DGND in Findings 2/4.

**Verification:** Netlist must show both CLK37 pins on ADC_CLK. Hold MCU reset to check defaults. Initialize U1 first and enable CLK_EN; after U2 clock-valid tPOR and VCAP1 settling, reset/configure U2 through its separate CS. Shared reset would clear U1 CLK_EN. Confirm clock at both ADCs and validate the timed sequence.

### J4 — A controller input exceeds its maximum input voltage.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6 MISO20/DRDY12:** Nominal 3.3 V ADC outputs do not show overvoltage; actual fault-state waveforms absent.

**V1 — U3 MISO19/DRDY15:** No explicit 5 V GPIO connection, but controller ground is disconnected. Its input voltages relative to local ground cannot be assigned.

**Exact evidence:** Only U3.21 is on +5V; it is the board 5 V supply header, not a GPIO. ADC DOUT/DRDY nets use nominal 3.3 V domain.

**Difference / conclusion:** No demonstrated controller input-overvoltage waveform; ground fault remains confirmed under H1.

**Requirement / calculation:** [Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)/[Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) DC input limits apply relative to valid local ground; a labelled 5 V supply pin is not a 5 V GPIO drive.

**Simplest correction:** Correct supplies/grounds; no level shifter supported from nominal net names alone.

**Verification:** Measure MISO/DRDY versus local MCU ground through intended startup/power modes and compare absolute/DC limits.

## K. Firmware — operating states

### K1 — A GPIO exceeds its permitted current.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6 ADC-control GPIOs; ADS GPIO pins 42/44/45/46:** No heavy DC GPIO load shown; actual directions, drive and fault-state currents unspecified.

**V1 — U3 ADC-control GPIOs; ADS GPIO pins 42/44/45/46:** Same input loads; supply errors and firmware states prevent a reliable current bound.

**Exact evidence:** Controller outputs drive ADC inputs; no carrier LED/resistive power load on them. ADS GPIO pins are tied to the DGND island and could contend only in an incompatible programmed state.

**Difference / conclusion:** No confirmed excess GPIO-current event, and no current fix credited.

**Requirement / calculation:** [Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)/[TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) output-current/leakage specifications require known direction/loading.

**Simplest correction:** No series resistors or driver added without demonstrated current path. Correct supply wiring and inspect configuration.

**Verification:** Inspect firmware GPIO/ADS direction registers; calculate DC loads and measure current only for actual driven states.

### K2 — Two output pins drive incompatible levels onto the same net.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U1.43 MISO; U2.43→U1.41:** Daisy path keeps ADC DOUT pins on different nets. No hard two-DOUT short.

**V1 — U1.43/U2.43→MISO→U3.19:** Shared data bus is valid with separate mutually exclusive CS. Both selected together could conflict, but that firmware/reset state is not established.

**Exact evidence:** V1 ERC flags output-output on MISO; U1.39=/CS_ADC1 and U2.39=/CS_ADC2 are separate. ADS GPIO strap behavior also depends on direction/configuration.

**Difference / conclusion:** Bus architecture changed from daisy chain to shared SPI with separate selects. This is not automatically a new contention fault.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §9.4.2.1: deselected DOUT becomes high impedance. ERC pin types cannot represent this chip-select behavior.

**Simplest correction:** Keep separate selects; firmware must deselect both before releasing ADC reset/power-down and select one for readback. No extra bus switch justified.

**Verification:** Inspect firmware and scope both CS/MISO through cold start/reset/reads. Do not assume DOUT high impedance in power-down without a specified guarantee.

### K3 — The controller drives a component whose supply is off.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6→U1/U2:** Analog supply has no source, but digital supply is nominally present; no actual GPIO-high/off-state timing supplied.

**V1 — U3→U1/U2:** Invalid ADC supply wiring is confirmed; actual controller drive states with those supplies are unknown.

**Exact evidence:** No firmware/state table supplied. Digital input limits reference DVDD, so do not equate missing AVDD alone with a proven digital-input clamp current.

**Difference / conclusion:** No fabricated off-state GPIO drive or current magnitude counted.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §7.1 digital input range and §11.1 supply sequencing.

**Simplest correction:** Correct supply wiring and define valid power/control sequence; add isolation only if an unavoidable actual state demonstrates need.

**Verification:** Inspect firmware and capture receiver DVDD/AVDD plus control voltages during power-down/startup/reset.

## L. Firmware — state transitions

### L1 — A state change causes a supply dip or brownout reset.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — BT1/LDOs/U6:** No state-transition/current/supply waveform or source-impedance model.

**V1 — BT1/LDOs/U3:** Same missing evidence; static supply faults do not establish a brownout event.

**Exact evidence:** No firmware transition states or measured rail/reset trace supplied.

**Difference / conclusion:** No demonstrated state-transition brownout fixed or introduced.

**Requirement / calculation:** A brownout is a reset caused by supply voltage dropping below the controller’s operating/reset threshold. Actual threshold/configuration and waveform are required.

**Simplest correction:** Correct confirmed wiring first; no bulk-capacitance or architecture change solely from this condition.

**Verification:** Measure local rail and reset reason during actual peak-load/state transitions with specified battery impedance and cutoff.

### L2 — Controller drives an input high before receiver supply is valid.

**Status:** CANNOT VERIFY. **Priority:** UNKNOWN.

**V0 — U6 controls→ADS1298:** Reset GPIO default levels are not guaranteed; no timing capture proves a high-before-valid event.

**V1 — U3 controls→ADS1298:** Same sequence uncertainty; supply topology itself must first be repaired.

**Exact evidence:** Reset-state omission is confirmed under J2/J3; it does not specify a particular transient level or timing.

**Difference / conclusion:** No timing fix credited without firmware and waveform evidence.

**Requirement / calculation:** [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf) §11.1 requires digital inputs low until supplies settle.

**Simplest correction:** Use defined low reset/power-down defaults, then release controls only after corrected supplies are valid.

**Verification:** Scope controls, AVDD/DVDD and MCU reset during cold start/restart/power cycling; inspect initialization code.

## Manufacturer sources and supporting evidence

- [TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf): pin functions pp 10–11, ratings p 12, input characteristics p 13, PGA pp 31–32, RLD p 41, clock p 50, multiple-device SPI pp 56–58, configuration/reset registers pp 66–70, power-up p 96.
- [TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf): pinout p 3, recommended conditions p 4, dropout/electrical tables pp 5–6, ON/OFF and capacitor requirements in §§6–7. Covers legacy/new chips; exact fitted suffix is still required.
- [TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf): DBV pinout p 3, ratings p 4, dropout p 6, enable/discharge and capacitor requirements §§6–7.
- [Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) and [Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf): GPIO reset/strap/DC tables. V0 is a module representation; unspecified eFuses matter for GPIO3 interpretation.
- [Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) sheet 2, saved as [reference PDF](EVIDENCE/esp32-devkitc-v11.pdf); [Espressif DevKitC power guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html) describes mutually exclusive board power methods. This reference does not establish the exact installed board revision.
- [TI parallel-LDO reference, §2.2.1.1](https://www.ti.com/lit/pdf/tiducs7): why parallel independent regulator references require a deliberate current-sharing arrangement; no such arrangement is shown here.
- [Power evidence](EVIDENCE/power_findings.md), [ADC evidence](EVIDENCE/adc_findings.md), [digital evidence](EVIDENCE/digital_findings.md), netlist/ERC/SVG exports and full parsed inventories in `EVIDENCE/`. Raw analyst notes are supporting material; this report and the CSV contain the final classifications, including the stricter A1/F1 comparison treatment.

## Verification still outstanding

No physical voltage, dip, brownout, ringing, oscillation, clipping, clamp current or signal-edge measurement was performed. No loop/transient simulation or firmware execution was possible from the supplied source material. Missing inputs: rated passive BOM, LP2985 chip identity, battery minimum/maximum/cutoff and load budgets, exact DevKit revision/powering modes, GPIO/ADC register/eFuse configuration, electrode/source/load models, and relevant startup/transition captures. These gaps do not weaken the direct pin-to-net wiring findings; they limit claims about actual physical behavior and the 25 uncertain condition comparisons.
