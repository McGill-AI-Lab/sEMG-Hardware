# Open-sEMG-16 V1.2 — implementation record

27 October 2026. Sources of truth: the [original F01–F21 engineering review](../reviews_v1/full_review.md) and [V1.1 implementation report](../reviews_v1.1/updates_from_v1.md). The older report uses the name “V2”; here its migrated V1.1 files and native final netlist are the historical reference. This record addresses remaining findings and does not repeat the original audit.

## A. Executive summary

**V1.2 remains unsuitable for initial power-up or human-worn testing.** The original Critical wiring repairs F01–F03 remain intact. Power-source conflicts, usable power control, body bias, protection and sequencing still block release.

Implemented in `open-semg-16-v1.2.kicad_sch`:

- **F05, partial:** added fitted removable **R38 = 0 Ω from EN to AGND**. The formerly floating shared enable now has an explicit OFF connection. Both regulators are deliberately disabled; this is a development inhibit, not a functional power-enable solution. Their outputs remain paralleled under F04. USB or another external source can still energize that rail.
- **F09, partial:** added **R36/R37 = 10 kΩ, 1%** from MOSI/DIN and SCLK respectively to AGND, establishing low biases while the controller is high impedance. CS defaults and complete supply/reset sequencing remain unresolved.
- **F12/F14, partial:** specified C0G/NP0, 1% for the 32 existing 620 pF input capacitors and 0.1%, ≥0.1 W for R1–R32, with derating/fault-pulse qualification still required. Nominal values and topology are unchanged.
- **F14, partial:** specified ≥10 V for C25/C51, with capacitance qualification at VCAP3 bias; added C55 leakage <100 nA at operating bias/temperature. These are procurement requirements, not claims about selected or installed parts.
- Updated the obsolete V2/floating-enable annotation and added visible notes identifying the new requirements and remaining blockers.

No operating power architecture, body-connected circuit, sample rate, gain, ADC reference modification, component MPN or PCB footprint was selected. **3 findings remain fixed for their original wiring diagnoses; 6 are partial; 12 remain otherwise open.** No additional finding receives a complete operational signoff.

Initial ERC: **35 errors + 26 warnings = 61**. Final ERC: **34 errors + 26 warnings = 60**. The removed error is U4's undriven enable; fewer ERC findings do not establish electrical readiness. Final verification passes **1,043 static assertions**. Every original pin-to-net assignment and all 16 acquisition mappings remain unchanged.

## B. Complete findings tracker

“Fixed” applies to the original diagnosed mechanism. “Partial” includes specified requirements that still need actual parts and physical qualification. Original Unverified findings remain unverified risks rather than demonstrated failures.

| ID / original severity | V1.1 status | V1.2 action | Current status | Verification evidence |
|---|---|---|---|---|
| F01 / Critical | Fixed: AVDD/AVDD1 wiring | Rechecked both ADCs; preserved | **Fixed — wiring** | [Final checks](diagnostics/final-validation.json): U1/U2 19/21/22/54/56/59 = +3.3V; AVSS/AVSS1 = AGND. Source qualification remains open. |
| F02 / Critical | Fixed: DVDD and common return | Rechecked actual pins; preserved | **Fixed — wiring** | DVDD48/50 = +3.3V; DGND33/49/51, MCU grounds and BT1 negative = AGND. |
| F03 / Critical | Fixed: auxiliary relative overvoltage | Rechecked pins 17/18/62; preserved | **Fixed — diagnosed exposure** | Aux pins remain identical to actual AVDD. Optional output/rerouting firmware restrictions remain F18. |
| F04 / High | Requires power decision | Investigated alternatives; no architecture selected | **Requires design decision** | U4.5/U5.5 still share +3.3V. R38 disables regulation but provides no output isolation. See C1/E1. |
| F05 / High | Floating shared EN; requires decision | Added fitted 0 Ω OFF strap R38 | **Partially corrected** | EN = U4.3/U5.3/R38.1; R38.2 = AGND. Floating condition removed; usable startup control unresolved. |
| F06 / High | Shared clock wired; startup unverified | Preserved and checked | **Partially corrected** | ADC_CLK contains only U1.37/U2.37/TP1; U1 CLKSEL tied to DVDD/U2 to AGND. Powered logic and observed synchronization remain unverified. |
| F07 / High | Requires bias decision | Compared protected passive bias and one compensated RLD; no body path added | **Requires design decision** | RLDREF60/RLDINV61/RLDOUT63/WCT64 NCs intact on both ADCs. See E2. |
| F08 / Unverified | Safety/protection not established | Preserved safety gate; no assumed fault-current target | **Requires safety design, simulation and verification** | No protection/isolation/cell qualification evidence supplied. Input resistor power rating is not wearer protection. |
| F09 / High | START/RESET/PWDN pulls only | Added DIN/SCLK pulls; investigated CS boot behavior | **Partially corrected** | Exact R36/R37 nets and leakage/load calculations in C2; CS nets unchanged. |
| F10 / Medium | Offset/gain/common mode unbounded | Preserved direct-coupled inputs; gain policy remains undefined | **Requires measurement and firmware** | All 32 input nets/values preserved; contact offset/motion/common-mode data absent. |
| F11 / Medium | Passband/rate decision pending | No sampling change | **Requires passband decision and firmware** | Original 2/4 kSPS analysis remains applicable; no register configuration supplied. |
| F12 / Unverified | RC matching/contacts unqualified | Added explicit component tolerance/dielectric requirements | **Partially addressed; performance unverified** | Fields exported in final XML; nominal 2 kΩ/620 pF unchanged. See C3. |
| F13 / Unverified | Effective output C/ESR and LP silicon unknown | Recomputed/checked bank; no unsupported capacitor substitution | **Requires power/BOM decision and qualification** | Common-rail nominal capacitance remains 242.6 µF before DevKit. No oscillation is asserted. |
| F14 / Unverified | Passive ratings/derating absent | Added input RC, VCAP3 voltage/bias and BP leakage requirements | **Partially specified** | C3/C4 and exported fields; selected parts, effective C, leakage, pulses and remaining passive ratings still pending. |
| F15 / Medium | Battery window/cutoff undefined | Retained source pending cell specification | **Requires design decision** | BT1/source net unchanged; +3.7V label is not a cell specification. |
| F16 / Unverified | RF transient/DBV thermal margin unknown | Recorded pull loading and OFF-state consequences | **Requires PCB/load/thermal measurements** | U5 DBV unchanged; no copper, RF duty or enclosure specification. |
| F17 / Medium | USB/5V/backfeed unresolved | Explicitly documented that R38 is not isolation | **Requires power-interface decision** | DevKit 3V3 interface and both LDO outputs unchanged; external-source/reverse-current scenarios remain. |
| F18 / Medium | Firmware absent | Preserved clock/reference/mode requirements in revised note | **Requires firmware** | No firmware created; CLK_EN, 2.4V reference, gain/rate, GPIO and optional modes require implementation/readback. |
| F19 / Medium | 125 unassigned footprints; unspecified MPNs/assembly | Added requirements without inventing procurement identities | **Requires PCB/manufacturing work** | Original footprints unchanged; three new resistors are unassigned: 128 of 133 components now lack footprints. |
| F20 / Unverified | PCB/RF/returns unreviewed | No layout changes or performance claims | **Requires PCB review and measurement** | No PCB supplied; schematic connectivity does not establish RF/noise/thermal behavior. |
| F21 / Low | TP1–TP16 added; physical access pending | Preserved all probe nodes | **Partially corrected** | All 16 test-point assignments unchanged; pad footprints, placement/loading and assembled access pending. |

## C. Detailed change log

### C1. F05 — defined development OFF state

**Before:** `/EN` contained only U4 ON/OFF3 and U5 EN3, with no driver or bias. U4.5/U5.5 already shared +3.3V. The V1.1 supply/ground repairs were independently confirmed before relying on AGND.

**After:** R38 pin 1 connects to the existing local `EN` net; pin 2 connects to actual AGND. Value `0`, `dnp no`, in BOM and on board. Its Purpose field identifies a fitted removable development OFF strap. No enable source was added. The resistor has a ≥0.1 W procurement requirement; exact MPN/footprint remain pending.

The [LP2985 datasheet](../../docs/datasheets/originals/components/LP2985.pdf), pp.3/7/16, specifies active termination and low-level OFF operation; its full-temperature low threshold is 0.15 V. The [TLV755P datasheet](../../docs/datasheets/originals/components/TLV755P.pdf), pp.3/6/12, specifies OFF below 0.3 V. A fitted zero-ohm connection establishes a deliberate low in the static schematic without relying on U5's unspecified maximum EN leakage to justify a weak pulldown. These are intended static states, not measured strap/ground voltages or a qualified startup waveform. LP silicon remains unspecified.

**Electrical consequence:** the two regulators are disabled rather than enabled in parallel. A battery-fed operational rail is intentionally not established by this revision. R38 must remain fitted until the power architecture is redesigned; do not apply a high EN driver against it. It does not prevent external voltage at the outputs. U5's disabled output discharge can load an externally held 3.3 V rail; its typical 120 Ω gives the conditional screen 3.3/120 ≈27.5 mA, not a guaranteed current. Output-above-input and USB backfeed stress remain unresolved. [Official TLV755P](https://www.ti.com/lit/ds/symlink/tlv755p.pdf), §§6.3.2/7.1.4.

**Method/evidence:** explicit [modification plan](diagnostics/modification-plan.json), controlled symbol/wire/label addition, [hardware edit log](diagnostics/hardware-edit-log.json), [ground-label scope correction](diagnostics/ground-scope-edit-log.json), [after-hardware netlist](diagnostics/after-hardware-netlist.xml) and [independent power review](diagnostics/independent-final-power-review.md). Native ERC no longer reports the original U4.3 undriven error. F05 remains partial because usable enable control and power delivery are still unresolved.

### C2. F09 — DIN and SCLK reset biases

| New part | Value / requirement | Pin 1 net and original terminals | Pin 2 |
|---|---|---|---|
| R36 | 10 kΩ, 1%, ≥0.1 W | `/MOSI`: U1.34, U2.34, U3.17 / GPIO11 | AGND |
| R37 | 10 kΩ, 1%, ≥0.1 W | `/SCLK`: U1.40, U2.40, U3.18 / GPIO12 | AGND |

**Before:** these two MCU-to-ADC input nets had no external bias. **After:** only the stated passive terminals are added. Existing R33/R34/R35 and START/RESET/PWDN wiring remain unchanged. MISO and both CS nets retain exact original membership.

ADS1298 SBAS459K §11.1 p.96 requires input-low conditions through supply stabilization. Low DIN also agrees with ordinary frame-read requirements. These pulls advance that requirement when MCU outputs are high impedance. [Official ADS1298 datasheet](https://www.ti.com/lit/ds/symlink/ads1298.pdf).

Using p.16's ±10 µA/ADC input, 50 nA controller input leakage and 1% maximum resistance: `VLOW = (2×10 µA + 50 nA)×10.1 kΩ = 0.202505 V`. Against `VIL=0.2×3.3=0.66 V`, illustrative static margin is 0.457495 V. This model assumes valid rails and high-impedance MCU pins with no opposing pull/drive; it does not validate the supply ramp or powered-off interfaces. At 3.3 V each nominal pull draws 0.33 mA and dissipates 1.089 mW while high; the two add up to 0.66 mA nominal static load. Worst 1% low resistance gives about 0.667 mA combined at the same assumed voltage. Timing, lightly loaded MCU VOH, ringing and actual rail tolerances still need measurement; the original table-bound ESP-to-ADS high-margin concern is not claimed solved.

Plain CS pullups were not adopted as a complete solution. They rise with DVDD during startup, and the [ESP32-S3 SoC datasheet v2.2](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf), Tables 2-1/2-2 pp.16–18, documents GPIO6–14 reset states and low-output startup glitches. A pullup cannot guarantee overriding a driven low glitch. A deliberate power/startup contract or suitable gating is still needed. No generic CS resistor was added merely to silence a shared-DOUT ERC error.

**Method/evidence:** same controlled addition as C1; [digital design evidence](diagnostics/digital-decision-evidence.md), [final netlist](diagnostics/final-netlist.xml), [digital independent review](diagnostics/independent-final-digital-review.md), and [rendered new block](diagnostics/new-controls-view.png). These are incremental default-state improvements, not a complete F09 correction.

### C3. F12/F14 — define input passive requirements

**Before:** R1–R32 were 2 kΩ and the 32 input capacitors were 620 pF without tolerance, dielectric or resistor rating requirements. **After:** every nominal value, terminal and input architecture remains unchanged; hidden procurement fields and a visible summary specify:

- R1–R32: **0.1%, ≥0.1 W**, subject to temperature derating and fault-pulse review.
- C1–C5, C10–C18, C21/C22, C27–C31, C36–C44, C47/C48: **C0G/NP0, 1%**.

These are engineering selections implementing the original review's matching/dielectric recommendation, not asserted manufacturer mandates or installed parts. The opposing tolerance extremes give `τHIGH=1.001×1.01×(2k×620pF)` and `τLOW=0.999×0.99×(2k×620pF)`, about 2.2% leg-to-leg time-constant spread. In the review's ideal-source independent-branch model this gives approximately 99.76 dB component-only rejection at 60 Hz. It is a conditional calculation, not achieved system CMRR; electrode impedance, contact imbalance, layout and protection can dominate. See the [original review §5.4](../reviews_v1/full_review.md) and [TI SBAA188](../../docs/datasheets/originals/ti-app-notes/SBAA188.pdf), p.3.

The review's 5 V-across-2 kΩ screen gives 12.5 mW; 0.1 W is an explicit part-selection floor rather than a safety-current limit. Fault voltage, duration, parallel contact paths, resistor pulses and derating still require a complete assessment. No wearer-current requirement is inferred from this rating.

**Method/evidence:** source-span property additions recorded per reference in [specifications-edit-log.json](diagnostics/specifications-edit-log.json). Final native XML includes the requirements; all 32 ADC-side nets and all electrode P/N mappings remain exact. [Analog evidence](diagnostics/analog-decision-evidence.md) gives the calculation and manufacturer dielectric references; [independent analog review](diagnostics/independent-final-analog-review.md) found no regression.

### C4. F14 — VCAP3 voltage and U4 bypass leakage requirements

| Parts / pins | V1.1 configuration | V1.2 requirement; electrical reasoning |
|---|---|---|
| C25.1 → U1 VCAP3.55/TP10; C25.2 → AGND | 1 µF, no voltage rating | **≥10 V**; selected-part capacitance must be qualified at operating DC bias, tolerance and temperature. |
| C51.1 → U2 VCAP3.55/TP15; C51.2 → AGND | Same independent second-ADC network | Same requirement; no shared VCAP node or capacitance change. |
| C55.1 → U4 BP4; C55.2 → AGND | 10 nF, no leakage specification | **<100 nA at operating bias and temperature**, retaining 10 nF. |

ADS1298 p.11 defines VCAP3 as internally generated AVDD+1.9 V. Relative to AVSS, at intended 3.3 V analog supply this is approximately 5.2 V. A ≥10 V requirement provides nominal voltage margin and follows the original review's suggested evaluation range. It does not establish adequate effective capacitance from a voltage marking alone. No original capacitor is declared overstressed because no part had been specified. A different analog rail would require reassessing actual bypass voltages and parts. Independent reference C19/C20 and C45/C46 and all VCAP values/returns remain unchanged.

LP2985 §7.1.3 p.21 requires bypass leakage not to exceed 100 nA and identifies 10 nF ceramic/film options. The schematic selects a stricter `<100 nA` procurement requirement without pretending a particular capacitor has met it. [Official LP2985 datasheet](https://www.ti.com/lit/ds/symlink/lp2985.pdf).

**Method/evidence:** controlled field additions in the specifications log; final XML and 1,043 assertions verify exported requirements and preserved terminals. Exact MPNs, capacitance at bias and temperature, leakage and physical placement remain open under F14/F19.

### C5. Editing method, annotations and recovery

Live read-only MCP queries confirmed the V1.2 project/schematic, build profile and write mode. Recovery schematic/project copies and pre-edit hashes were saved before electrical edits. The exposed transaction implementation supports label insertion but does not instantiate the components shown in its preview; component/property edits therefore require a controlled fallback even with a working transport.

The first `sch_plan_from_spec` call was rejected before plan creation: **“MCP tool call requires approval, but approval policy is never.”** The [exact spec and rejection](diagnostics/mcp-operation-log.json) are retained. No repeated write attempt, preview/apply or rollback was issued against a nonexistent plan. No MCP design mutation succeeded.

The user-authorized fallback [edit_v1_2.py](diagnostics/edit_v1_2.py) restricts the target to V1.2, applies explicit source-span changes, checks balanced KiCad S-expressions and unique UUIDs/references, validates candidates with native KiCad export, and atomically replaces the active schematic. It preserves all original embedded symbols, wires, junctions and NC markers. Three signal labels and one global AGND label connect the new passive block to existing nets. The revised summary note corrects the stale “V2”/floating-EN text; a separate note visibly lists procurement requirements and readiness limits. No ERC severity, exclusion, pin type, power flag, project setting or sampling configuration changed.

Installed `sch_verify_plan` would also initialize a symbol cache under `~/.cache/kicad-sch-api`, outside the authorized write roots, and only reports ERC availability rather than running ERC. Native KiCad CLI plus explicit pin/net comparisons provided verification instead. The preserved baseline is the recovery point for these controlled edits.

## D. ERC, netlist and regression results

### D1. Baseline and final results

The pre-existing root `initial-erc.json` and `initial-netlist.xml` were preserved. Fresh initial exports under `diagnostics/` reproduce the supplied V1.2 state. Native initial net partitions exactly match V1.1's final partitions: 130 components, 132 nets. Live active project paths were confirmed separately.

| Stage | Errors | Warnings | Total | Static validation |
|---|---:|---:|---:|---|
| [Initial](diagnostics/initial-erc.json) / [netlist](diagnostics/initial-netlist.xml) | 35 | 26 | 61 | Reproduces V1.1 final connectivity |
| [After passive additions and label scope correction](diagnostics/after-hardware-erc.json) / [netlist](diagnostics/after-hardware-netlist.xml) | 34 | 26 | 60 | [976 assertions pass](diagnostics/after-hardware-validation.json) |
| [Final](diagnostics/final-erc.json) / [netlist](diagnostics/final-netlist.xml) | 34 | 26 | 60 | [1,043 assertions pass](diagnostics/final-validation.json) |

Final components: **133**, comprising the original 130 plus R36–R38. Nets: **132**. Important exact deltas:

| Net | Only added terminals |
|---|---|
| `/MOSI` | R36.1 |
| `/SCLK` | R37.1 |
| `/EN` | R38.1 |
| `AGND` | R36.2, R37.2, R38.2 |

All 416 original represented pin assignments, original values, footprints and library identities are preserved. Every original net's membership equals its baseline membership plus only the listed terminals. No unintended short/open or reassignment is found. Every capacitor retains both endpoints; both references, all eight VCAP nodes, CLK/CLKSEL, DRDY/test access, acquisition polarity and original control connections remain intact.

### D2. Remaining ERC inventory

| Type | Errors | Warnings | Interpretation |
|---|---:|---:|---|
| pin_not_connected | 28 | 0 | Existing DevKit header/unused GPIO reports; no blanket NC markers added. |
| power_pin_not_driven | 3 | 0 | Existing AGND/battery/+5V power-model issues; no flags used to conceal unresolved source design. |
| pin_not_driven | 1 | 0 | Existing U3 CHIP_PU assembly-aware report. U4 EN error removed by real low connection. |
| pin_to_pin | 2 | 4 | Parallel regulator outputs and shared cascade DOUT errors; auxiliary TEST/PACE tie warnings. Source design and firmware restrictions still apply. |
| unconnected_wire_endpoint | 0 | 19 | Existing stubs, unchanged. |
| multiple_net_names | 0 | 2 | Existing +3.3V/AVDD and AGND/GND aliases, unchanged electrically. |
| lib_symbol_mismatch | 0 | 1 | Existing BT1 cache/library mismatch. |

The initial passive block used a local AGND label beside pre-existing global AGND labels. Native checks caught one new label-scope warning; its scope was corrected to global without changing any net membership. The first failed checks and native reports are retained under `after-hardware-first-*`. The first final verification also rejected an ERC identity comparison because KiCad chose a different pre-existing AVDD label UUID to represent the same alias warning. The checker now compares alias diagnoses while independently requiring all original label bytes and net memberships to be preserved. That earlier result is retained in `final-first-validation.json`; the delivered final result passes. No warning was disabled or severity reduced.

The four inherited disabled checks remain unchanged: single_global_label, four_way_junction, simulation_model_issue and footprint_filter. All configured severities were requested. Native exports emitted the existing fontconfig warning and completed successfully.

### D3. Visual and independent review

The [final schematic PDF](diagnostics/final-schematic.pdf), [new passive block](diagnostics/new-controls-view.png) and [requirement notes](diagnostics/requirements-view.png) were visually inspected. Native SVG is also retained. PDF rasterization used the installed macOS 15.4 SDK after the default 27.0 SDK failed to link with the available compiler; this affected only rendering, not KiCad validation.

Independent [power](diagnostics/independent-final-power-review.md), [digital](diagnostics/independent-final-digital-review.md) and [analog](diagnostics/independent-final-analog-review.md) reviews checked the final native netlist and source. None found an unintended connectivity regression. Their conclusions are limited to the static scopes stated in those documents.

No PCB/DRC, firmware execution, circuit simulation, startup capture, rail/current/thermal/RF measurement or wearer testing was performed. ERC and static assertions do not establish powered operation, analog performance, complete fault-current protection or safety.

## E. Remaining issues and decisions

### E1. Operating power architecture — F04/F05/F13/F15/F16/F17

The supplied datasheets do not supply the missing battery, USB mode, current-duty or layout requirements. The alternatives remain materially different:

| Alternative | Benefit | Requirements still needed |
|---|---|---|
| One qualified 3.3 V source | Eliminates output sharing; one common supply | Source transient/thermal/noise capability, source removal/isolation, battery window and USB policy. |
| U4 analog / U5 digital, retaining DevKit | Keeps RF demand off the 150 mA AFE source; follows V1.1's preferred investigation direction | Exact LP silicon, separated capacitors, controlled analog/digital sequencing, U5 DBV qualification and DevKit source isolation. |
| DevKit digital regulation with independent AFE source | Uses the fitted board's existing supply circuitry | Actual board/SKU and valid input window, source selection, battery/USB interaction and AFE sequencing. A single cell cannot be assumed to provide a 5 V header supply. |

Even a rail split alone would leave nominal U5 capacitance **220.2 µF plus DevKit capacitance** (C57 200 µF plus C8/C9/C34/C35 20.2 µF), while U4 would see 22.4 µF. Thus it would not independently resolve the documented 200 µF qualification concern. Reducing C57 without a transient/ESR/startup budget would replace one unknown with another. The actual common output remains 242.6 µF nominal before DevKit; no oscillation is claimed.

**Decisions needed:** choose the rail/source architecture and allowed USB/5V/3V3 modes; identify the battery and usable voltage/cutoff window; identify the fitted DevKit and LP2985 silicon; then design isolation, reverse-current protection, functional EN control and startup/shutdown behavior. Qualify full-window steady/burst loads, capacitance/ESR and thermal behavior. Keep R38 fitted until that redesign is implemented; OFF is not a safe external-power mode. Espressif documents the DevKit [power options as mutually exclusive](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html).

### E2. Body bias and protection — F07/F08

Protected passive bias and one compensated RLD driver remain viable alternatives. A dedicated contact, representative electrode/body/cable impedance and capacitance, sensing configuration, disconnection recovery and applicable normal/single-fault current requirements are not specified. No body-connected values can be defended from the ADC datasheet alone. Choose the approach and operating/safety requirements, model the complete paths and loop where applicable, and validate on a simulator before considering a wearer. The second RLD must not be connected as a competing active driver. No added input-resistor rating qualifies these paths.

### E3. Controls, firmware and signal performance — F06/F09/F10/F11/F12/F18

Define the complete power/reset/CS contract, including MCU boot glitches, unpowered receivers and exclusive selects. Suitable gating or sequenced defaults must be evaluated with the chosen supply architecture. Implement U1 CLK_EN startup/restoration, valid U2 clock/POR/reset timing, reference enable/settling, register readback, matched gains/rates, shared START and complete frame/data-validity handling. Keep grounded ADS GPIOs inputs/output-low, optional PACE/RLD/WCT modes off, and RLD rerouting disabled. Verify both DRDY signals and alignment on a bench.

Choose acceptable passband attenuation before selecting 2/4 kSPS HR operation. Measure contact impedance, DC offsets, common mode and motion extremes before gain/protection/RC changes. The new component requirements reduce unspecified procurement choices; they do not close electrode loading, achieved CMRR, clipping, lead-off contamination or RF noise.

### E4. Physical qualification — F14/F16/F19/F20/F21

Select actual MPNs and footprints, verify effective capacitance/leakage/tolerance/voltage and resistor derating/pulses, and identify exact IC/DevKit variants. Remaining passive ratings and R33–R35 physical specifications still need completion. Design a PCB and examine physical pin mapping, return currents, local decoupling, reference/VCAP leakage, antenna keepout, thermal copper, balanced electrodes and probe loading. Perform schematic/PCB parity, DRC and appropriate measurement. Existing TP1–TP16 remain schematic access only.

## F. Modified and created files; historical integrity

**Only modified pre-existing design file:** [open-semg-16-v1.2.kicad_sch](../v1.2/open-semg-16-v1.2.kicad_sch).

**Unchanged:** V1.2 `.kicad_pro`, `.kicad_prl`, local symbol/library files and `.codex/config.toml`; all V1/V1.1 designs and prior review documents; manufacturer datasheets and other protected project files. The [pre-edit hash record](diagnostics/pre-edit-hashes.json) covers 181 protected files, all seven original active-revision files and both pre-existing V1.2 diagnostics. Final verification confirms every protected file and every pre-existing file except the authorized schematic is hash-identical. No historical revision or shared library was edited.

All retained new diagnostics and this report are inside `reviews_v1.2/`. Recovery copies, candidate schematics/exports, per-edit logs, baseline/final diagnostics, validation scripts/results, independent reviews, render source and images are enumerated in the exact manifest below. Candidate/first-pass files are diagnostic history; the active V1.2 file and `final-*` results are the delivered design/evidence. An unused temporary MCP artifact-directory symlink was created and removed after the blocked call; no such active-project artifact remains. The temporary renderer binary was removed after generating images.

The machine-readable [file-integrity result](diagnostics/final-file-integrity.json) and [retained file manifest](diagnostics/created-file-manifest.txt) provide final accounting. The report's exact file list is generated after all artifacts are saved.

### Exact retained new file list

- [diagnostics/after-hardware-cli-log.json](diagnostics/after-hardware-cli-log.json)
- [diagnostics/after-hardware-connectivity.json](diagnostics/after-hardware-connectivity.json)
- [diagnostics/after-hardware-erc.json](diagnostics/after-hardware-erc.json)
- [diagnostics/after-hardware-first-cli-log.json](diagnostics/after-hardware-first-cli-log.json)
- [diagnostics/after-hardware-first-connectivity.json](diagnostics/after-hardware-first-connectivity.json)
- [diagnostics/after-hardware-first-erc.json](diagnostics/after-hardware-first-erc.json)
- [diagnostics/after-hardware-first-netlist.xml](diagnostics/after-hardware-first-netlist.xml)
- [diagnostics/after-hardware-first-validation.json](diagnostics/after-hardware-first-validation.json)
- [diagnostics/after-hardware-netlist.xml](diagnostics/after-hardware-netlist.xml)
- [diagnostics/after-hardware-validation.json](diagnostics/after-hardware-validation.json)
- [diagnostics/analog-decision-evidence.md](diagnostics/analog-decision-evidence.md)
- [diagnostics/baseline/open-semg-16-v1.2.kicad_pro](diagnostics/baseline/open-semg-16-v1.2.kicad_pro)
- [diagnostics/baseline/open-semg-16-v1.2.kicad_sch](diagnostics/baseline/open-semg-16-v1.2.kicad_sch)
- [diagnostics/configuration-check.json](diagnostics/configuration-check.json)
- [diagnostics/created-file-manifest.txt](diagnostics/created-file-manifest.txt)
- [diagnostics/digital-decision-evidence.md](diagnostics/digital-decision-evidence.md)
- [diagnostics/edit_v1_2.py](diagnostics/edit_v1_2.py)
- [diagnostics/final-cli-log.json](diagnostics/final-cli-log.json)
- [diagnostics/final-connectivity.json](diagnostics/final-connectivity.json)
- [diagnostics/final-erc.json](diagnostics/final-erc.json)
- [diagnostics/final-file-integrity.json](diagnostics/final-file-integrity.json)
- [diagnostics/final-first-validation.json](diagnostics/final-first-validation.json)
- [diagnostics/final-netlist.xml](diagnostics/final-netlist.xml)
- [diagnostics/final-schematic.pdf](diagnostics/final-schematic.pdf)
- [diagnostics/final-svg/open-semg-16-v1.2.svg](diagnostics/final-svg/open-semg-16-v1.2.svg)
- [diagnostics/final-validation.json](diagnostics/final-validation.json)
- [diagnostics/ground-scope-candidate-netlist.xml](diagnostics/ground-scope-candidate-netlist.xml)
- [diagnostics/ground-scope-candidate.kicad_sch](diagnostics/ground-scope-candidate.kicad_sch)
- [diagnostics/ground-scope-edit-log.json](diagnostics/ground-scope-edit-log.json)
- [diagnostics/hardware-candidate-netlist.xml](diagnostics/hardware-candidate-netlist.xml)
- [diagnostics/hardware-candidate.kicad_sch](diagnostics/hardware-candidate.kicad_sch)
- [diagnostics/hardware-edit-log.json](diagnostics/hardware-edit-log.json)
- [diagnostics/independent-final-analog-review.md](diagnostics/independent-final-analog-review.md)
- [diagnostics/independent-final-digital-review.md](diagnostics/independent-final-digital-review.md)
- [diagnostics/independent-final-power-review.md](diagnostics/independent-final-power-review.md)
- [diagnostics/initial-cli-log.json](diagnostics/initial-cli-log.json)
- [diagnostics/initial-erc.json](diagnostics/initial-erc.json)
- [diagnostics/initial-netlist.xml](diagnostics/initial-netlist.xml)
- [diagnostics/mcp-operation-log.json](diagnostics/mcp-operation-log.json)
- [diagnostics/modification-plan.json](diagnostics/modification-plan.json)
- [diagnostics/new-controls-view.png](diagnostics/new-controls-view.png)
- [diagnostics/pre-edit-hashes.json](diagnostics/pre-edit-hashes.json)
- [diagnostics/render-log.json](diagnostics/render-log.json)
- [diagnostics/render-pdf.m](diagnostics/render-pdf.m)
- [diagnostics/requirements-view.png](diagnostics/requirements-view.png)
- [diagnostics/specifications-candidate-netlist.xml](diagnostics/specifications-candidate-netlist.xml)
- [diagnostics/specifications-candidate.kicad_sch](diagnostics/specifications-candidate.kicad_sch)
- [diagnostics/specifications-edit-log.json](diagnostics/specifications-edit-log.json)
- [diagnostics/validate_v1_2.py](diagnostics/validate_v1_2.py)
- [updates_from_v1.1.md](updates_from_v1.1.md)
