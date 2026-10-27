# Open-sEMG-16 — comprehensive electrical design audit

Review date: 27 October 2026. Scope: diagnostic review only. No schematic, PCB, component, wiring, library, or project-setting changes were made.

## Part A — Executive summary

**Readiness: not ready for initial power-up, fabrication release, or human-worn testing.** The supplied schematic contains fundamental supply and clock connectivity faults. Earlier ADS1298/EVM experiments do not validate these connections.

The most important confirmed findings are:

1. **Both ADS1298 analog supply spans are zero.** U1/U2 AVDD pins 19/21/22/56/59 and AVDD1 pin 54 connect to `AGND`, together with AVSS/AVSS1. The analog core therefore has 0 V rather than the required 2.7–5.25 V. [D1, pp.10–12]
2. **The digital supply and ground network is invalid.** U1/U2 DVDD pins 48/50 connect to the net named `DGND`, while their actual DGND pins 33/49/51 connect to `AGND`. U3's grounds connect to `DGND`; battery negative connects to `AGND`. Those nets have no DC bond. The ADC digital supply and MCU battery return are consequently undefined. This is an electrical connectivity failure, not a choice of analog/digital ground layout.
3. **A powered 3.3 V rail would overstress six auxiliary analog pins.** U1/U2 pins 17, 18 and 62 connect directly to `+3.3V` while actual AVDD is at `AGND`. If that rail reaches 3.3 V, the pins exceed their AVDD + 0.3 V absolute limit by about 3.0 V. Clamp conduction, back-powering, and damage are possible. [D1, §7.1, p.12]
4. **U4 and U5 are both fixed 3.3 V LDOs and their outputs are directly paralleled.** They are not separate analog/digital supplies. Their ratings cannot be added to obtain a 650 mA supply. Their common `/EN` net has only the two enable inputs and no driver or bias.
5. **U2 has no master clock.** U1's CLK pin 37 is electrically unconnected; U2's pin 37 has a singleton `ADC_CLK` net. U2 is selected for an external clock. Shared START cannot produce simultaneous 16-channel acquisition without a common clock.
6. **No body-bias/RLD electrode or deliberate DC body-bias path is implemented.** Both RLD outputs and feedback/reference terminals are explicitly disconnected. The acquisition inputs have capacitive AC returns, which do not establish the wearer's DC common mode.

Major additional risks include undefined ADC controls during MCU reset, unresolved USB/DevKit power interactions, unspecified electrode protection and wearer fault-current control, electrode-impedance-induced CMRR loss, DC-offset/PGA saturation, LDO battery headroom and thermal limits, and unspecified capacitor ratings/derating. A nominal 222.4 µF is connected directly across the LDO output/AGND network; actual effective capacitance and stability need qualification against the regulators' documented output-capacitance ranges.

Features verified as correctly connected within their limited scope include all 16 differential electrode mappings, the independent reference capacitor networks, the nominal VCAP values and returns, and a supported **cascade SPI** arrangement with separate chip selects. U3's 44-pad DevKitC symbol/assigned footprint mapping agrees with official DevKit headers. These observations do not make the overall circuit operational.

The development schematic and `.kicad_pro` are **byte-identical to the supplied read-only earlier revision**. Normalized net connectivity and ERC results also match. Demonstrated faults therefore **persist** in this comparison; there are **no substantiated Fixed or New findings**. The historical annotated Amberflow report was not supplied, so this establishes presence in both artifacts, not which faults Amberflow previously identified.

Static analysis establishes connectivity, nominal transfer functions, component identities as specified, and conditional operating margins. It cannot establish real rail transients, oscillation, temperature, achieved CMRR/noise, RF interference, firmware timing, or wearer safety. No PCB, firmware, battery specification, complete passive-component BOM, or new-board measurements were available.

## Part B — Design inventory and diagnostic results

### Project, evidence, and inspection method

Active project: `open-semg-16-v1.kicad_pro` / `open-semg-16-v1.kicad_sch` in the authorized development workspace. There is **one root schematic sheet `/`**, no hierarchical sub-sheets, and no `.kicad_pcb` in either supplied design directory. The title block says Version 1.2. The schematic has 111 non-power components: 57 capacitors, 32 resistors, 16 two-terminal electrode connectors, five IC/assembly symbols, and one battery. KiCad exports 134 nets, including deliberately unconnected-pin nets; this is not a count of 134 functional signals.

The configured `kicad` MCP server was queried and confirmed this development directory. Its exposed build-profile tools lacked schematic-reading, netlist-export, and standalone ERC operations. No `kicad_reference` tools were exposed. Read-only inspection therefore used the local **KiCad CLI 10.0.7**, embedded symbol definitions, and native XML netlists. The original design was read and copied into an internal diagnostic snapshot before its CLI diagnostics, so all requested exports/reports stayed inside this workspace. No write-capable design-edit tool was used.

Evidence files:

- [Current native netlist](diagnostics/current-netlist.xml), [derived pin/net map](diagnostics/current-connectivity.json), [readable pin/net map](diagnostics/current-connectivity.txt).
- [Current ERC](diagnostics/current-erc.json), [reference netlist](diagnostics/reference-netlist.xml), [reference ERC](diagnostics/reference-erc.json).
- [Schematic inventory](diagnostics/current-schematic-inventory.json), [schematic SVG](diagnostics/schematic-svg/open-semg-16-v1.svg), and [independent-review checkpoint](diagnostics/independent-review-checkpoint.md).
- Source file hashes and comparison results are in `diagnostics/`; final verification checks original design files against their pre-audit hashes.

Netlist connectivity takes precedence over visible label text. Embedded power-symbol values include `GND`, `AGND`, `DGND`, and several voltage names; sharing a graphical ground symbol shape does not join differently named nets. Conversely `GND` and `AGND` are actually joined in this schematic. Some supply pins have passive rather than power-input types, reducing ERC's ability to detect a bad supply connection. Hidden/stacked DevKit power pins are included in the exported netlist.

### ICs and major blocks

| Reference | Actual schematic identity | Package / footprint and qualification |
|---|---|---|
| U1, U2 | `ADS1298xPAG`, eight differential channels each | `Package_QFP:TQFP-64_10x10mm_P0.5mm`; PAG/TQFP pin map matches D1. Full procurement suffix/grade unspecified. |
| U3 | `ESP32-S3-DevKitC` assembly | `PCM_Espressif:ESP32-S3-DevKitC`, 44 pads; not a bare 40-pad WROOM module. Exact installed DevKit/module SKU and revision unspecified. |
| U4 | `LP2985-3.3`, fixed **3.3 V**, **150 mA** | `Package_TO_SOT_SMD:SOT-23-5`; full orderable MPN, accuracy grade, and legacy/new silicon not specified. |
| U5 | `TLV75533PDBV`, fixed **3.3 V**, **500 mA** | `Package_TO_SOT_SMD:SOT-23-5`, **DBV**, without an exposed thermal pad. Reel suffix unspecified. |
| BT1 | Generic `Battery` | No cell MPN, capacity, protection, current rating, connector or footprint. The user's intended single-cell Li-Po is an operating assumption, not a component specification. |
| E1–E16 | Generic two-pin connectors with value `Electrodes` | 32 acquisition contacts, no instantiated bias contact, no assigned footprints. Gold finish, geometry and mechanical polarity are not established. |

All R1–R32, C1–C57, BT1 and E1–E16 lack footprints: **106 of 111 non-power components**. Their electrical ratings, tolerances and manufacturer parts are also unspecified. The unused `dry_electrode.kicad_sym` and `ref_electrode.kicad_sym` do not instantiate a bias circuit. The active electrode symbols are generic connectors, so flaws in unused custom symbols must not be mistaken for current input shorts.

### Actual power-rail inventory

| Net | Actual source and connected loads | Electrical conclusion |
|---|---|---|
| `+3.7V` | BT1.1; U4 VIN1 and U5 IN1; C53/C56, each 1 µF to AGND | Battery label only; actual range and droop unknown. |
| `AGND` / merged `GND` | BT1.2, U4/U5 GND2, analog filter/ref/VCAP returns; **all ADC AVDD, AVSS and physical DGND pins** | Defined battery-negative net, but ADC supply pins are incorrectly on it. |
| `DGND` | U3 GND22/23/24/44; **ADC DVDD48/50**; RESV1, DAISY_IN, ADC GPIOs; U2 CLKSEL52; C8/C9/C34/C35 returns | Separate DC island without battery return. Its name is not proof it is the ADC's physical ground. |
| `+3.3V` | U4 VOUT5 **and** U5 OUT5; U3 3V3 pins1/2; ADC aux17/18/62, U1 CLKSEL52; rail capacitors | Two direct LDO sources; startup undefined because EN floats. No actual ADC AVDD/DVDD supply pin is connected to this rail. |
| `/EN` | U4 ON/OFF3 and U5 EN3 only | Undriven. No GPIO, resistor, switch or power source. |
| `+5V` | U3 header pin21 only | No carrier source. Not required if an intact DevKit is intentionally powered via 3V3; external USB/5V states require separate power review. |
| VREFP, separately per ADC | U1.24 → C19 0.1 µF || C20 10 µF → AGND; U2.24 → C45/C46 equivalents | No external reference. Internal reference must be enabled by firmware after valid power. VREFN25 is AGND. |
| VCAP1–4, separately per ADC | U1 pins28/30/55/26 → C23 22 µF/C24 1 µF/C25 1 µF/C26 1 µF to AGND; U2 C49–C52 | Nominal pin-table values/returns correct. Ratings and physical implementation unknown. |

Regulator pins are verified directly against D2/D3 p.3: both pin1 input, pin2 ground, pin3 enable, pin5 output; U4 pin4 BP has C55 10 nF to its ground, whereas U5 pin4 is intentionally NC. C53/C56 are 1 µF input bypass; C54 is 2.2 µF and C57 is **200 µF**, not 200 nF. No voltage setting was inferred from family names.

### All 16 differential paths

Electrode terminal1 consistently feeds P through the odd resistor; terminal2 feeds N through the even resistor. Each resistor is 2 kΩ. Every listed capacitor is 620 pF from the ADC-side node to AGND. There are no cross-channel shorts or P/N swaps in these 32 input nets.

| System channel | Contact | ADC/channel | P / N pins | P / N resistors | P / N shunt capacitors |
|---|---|---|---|---|---|
| 1 | E1 | U1/1 | 16 / 15 | R1 / R2 | C1 / C2 |
| 2 | E2 | U1/2 | 14 / 13 | R3 / R4 | C3 / C4 |
| 3 | E3 | U1/3 | 12 / 11 | R5 / R6 | C5 / C10 |
| 4 | E4 | U1/4 | 10 / 9 | R7 / R8 | C11 / C12 |
| 5 | E5 | U1/5 | 8 / 7 | R9 / R10 | C13 / C14 |
| 6 | E6 | U1/6 | 6 / 5 | R11 / R12 | C15 / C16 |
| 7 | E7 | U1/7 | 4 / 3 | R13 / R14 | C17 / C18 |
| 8 | E8 | U1/8 | 2 / 1 | R15 / R16 | C21 / C22 |
| 9 | E9 | U2/1 | 16 / 15 | R17 / R18 | C27 / C28 |
| 10 | E10 | U2/2 | 14 / 13 | R19 / R20 | C29 / C30 |
| 11 | E11 | U2/3 | 12 / 11 | R21 / R22 | C31 / C36 |
| 12 | E12 | U2/4 | 10 / 9 | R23 / R24 | C37 / C38 |
| 13 | E13 | U2/5 | 8 / 7 | R25 / R26 | C39 / C40 |
| 14 | E14 | U2/6 | 6 / 5 | R27 / R28 | C41 / C42 |
| 15 | E15 | U2/7 | 4 / 3 | R29 / R30 | C43 / C44 |
| 16 | E16 | U2/8 | 2 / 1 | R31 / R32 | C47 / C48 |

No analog high-pass, differential bridge capacitor, external input clamp, or input bias resistor network is present. The RC transfer is one matched pole for differential signals, not two cascaded poles.

### RLD/bias path

U1/U2 RLDREF60, RLDINV61, RLDOUT63, and WCT64 have explicit no-connect markers. RLDIN62 is tied to `+3.3V`. There is no RLD feedback R/C, series drive resistor, passive midpoint bias, or bias-electrode connector. Thus there are no connected dual RLD drivers and no implemented feedback loop whose capacitive loading or phase margin could be assessed. Optional WCT output disconnection is reasonable for differential sEMG. Both RLD amplifiers must remain off in this topology. [D1, pp.41–42,69]

### Digital control and actual SPI topology

| Signal | U1 / U2 pin(s) | U3 carrier pin / ESP GPIO |
|---|---|---|
| `/MOSI` | DIN34, both | 17 / GPIO11 |
| `/MISO` | DOUT43, both | 19 / GPIO13 |
| `/SCLK` | SCLK40, both | 18 / GPIO12 |
| `/CS_ADC1` | U1 CS39 | 16 / GPIO10 |
| `/CS_ADC2` | U2 CS39 | 20 / GPIO14 |
| `/START` | START38, both | 12 / GPIO8 |
| `/RESET` | RESET36, both | 6 / GPIO6 |
| `/PWDN` | PWDN35, both | 7 / GPIO7 |
| `/DRDY_ADC1` | U1 DRDY47 | 15 / GPIO9 |
| U2 DRDY | U2.47 explicitly NC | None |
| Master clock | U1.37 unconnected; U2.37 singleton `ADC_CLK` | None |

U1 CLKSEL52 is `+3.3V`, U2 CLKSEL52 is `DGND`. Both DAISY_IN41 and RESV1 31 connect to `DGND`; ADC GPIO42/44/45/46 do too. **This is TI cascade mode**: shared DIN/SCLK/DOUT with independent CS, not a serial DOUT→DAISY_IN chain. DOUT is high impedance when deselected. It is valid only when the devices are properly powered and CS signals never overlap. [D1, §9.4.2.1 p.57, §9.5.1.4 p.60]

### ERC results and interpretation

Configured all-severity ERC: **65 violations = 38 errors + 27 warnings**, identically in both revisions. No reported violation was marked excluded. Four check types are disabled in project settings: `single_global_label`, `four_way_junction`, `simulation_model_issue`, `footprint_filter`. “All severity” does not override these disabled checks. Project settings were not changed.

| Type | Errors | Warnings | Interpretation |
|---|---:|---:|---|
| `pin_not_connected` | 29 | 0 | U1 CLK plus U3 CHIP_PU and 27 unused GPIOs. CLK is a real defect; unused GPIOs need documentation. DevKit CHIP_PU has onboard circuitry if an intact specified DevKit is fitted. |
| `power_pin_not_driven` | 4 | 0 | Ground/source power-pin typing, battery source, and U3 +5V. Passive battery pins need source declaration for ERC, but adding PWR_FLAG would not correct actual ADC or ground faults. +5V may intentionally be unused. |
| `pin_not_driven` | 2 | 0 | U4 enable is genuinely undriven; U3 CHIP_PU needs assembly-aware interpretation. |
| `pin_to_pin` | 2 | 4 | Errors: parallel LDO outputs (real issue), shared DOUT (supported with exclusive CS). Warnings: four TEST/PACE pins tied to rail; only acceptable as unused AVDD ties after supply correction and with output modes disabled. |
| `label_dangling` | 1 | 0 | Global `ADC_CLK` near U1 is not attached. Together with U1 CLK disconnection and U2 singleton this proves the missing link. |
| `unconnected_wire_endpoint` | 0 | 20 | 16 electrode-area dangling stubs, two ADC-area stubs, the U1 clock stub, and a U3-side stub. Netlist still confirms every acquisition pair and CS connection; a dangling stub is not automatically a missing electrode connection. Clock is the material fault. |
| `multiple_net_names` | 0 | 2 | `+3.3V`/`AVDD` and `AGND`/`GND` aliases. Naming a signal AVDD does not connect the chip's actual AVDD pins to it. |
| `lib_symbol_mismatch` | 0 | 1 | BT1 differs from installed Device library. No reversed battery polarity is supported by the exported pins; procurement/library reconciliation remains necessary. |

There are nine explicit NC markers: four optional RLD/WCT terminals per ADC and U2 DRDY. ADS pins27/29 and U5 pin4 are intrinsically NC pins; their intentional disconnection does not require a missing-input diagnosis. U1 CLK has no NC marker and is required by the intended clock arrangement. An ERC pass after cosmetic fixes would not establish electrical performance.

### Manufacturer sources

Page numbers below refer to the original local PDF pages, generally matching printed pages. PDFs were extracted directly using macOS PDFKit with page markers. Converted Markdown was used only for navigation; original PDF text/pin tables were checked. Relevant support notes were reviewed without importing ECG-specific bandwidth or safety assumptions into sEMG.

| ID | Original document and key locations | Availability |
|---|---|---|
| D1 | [TI ADS1298, SBAS459K, Aug 2015](../../docs/datasheets/originals/components/ADS1298.pdf): pp.10–12 pin/voltage limits; pp.13–17 performance/timing; p.22 noise; p.32 Eq.2/3; p.49 Eq.5; pp.50–63 clock/SPI; pp.67–81 registers; pp.96–98 power/layout | Local original, 113 pages; [official PDF](https://www.ti.com/lit/ds/symlink/ads1298.pdf) also consulted. |
| D2 | [TI LP2985, SLVS522S, May 2025](../../docs/datasheets/originals/components/LP2985.pdf): pp.3–7 pinout/limits; p.16 enable; pp.20–21 capacitors/reverse current; p.30 silicon identification | Local original, 43 pages; [official PDF](https://www.ti.com/lit/ds/symlink/lp2985.pdf). |
| D3 | [TI TLV755P, SBVS320D, Sep 2024](../../docs/datasheets/originals/components/TLV755P.pdf): pp.3–6 pinout/limits/thermal; pp.12–15 enable/capacitors; pp.17–18 reverse current/thermal | Local original, 51 pages; [official PDF](https://www.ti.com/lit/ds/symlink/tlv755p.pdf). |
| D4 | [Espressif ESP32-S3-WROOM-1/-1U v1.8](../../docs/datasheets/originals/components/ESP32-S3-WROOM-1.pdf): pp.11–16 pins/straps; p.27 electrical tables; p.28 RF current | Local original, 53 pages; applies to module inside DevKit, not its carrier pin numbering. |
| D5 | [TI SBAA188B, Oct 2026, Improving Common-Mode Rejection Using the RLD Amplifier](../../docs/datasheets/originals/ti-app-notes/SBAA188.pdf): p.3 mismatch; pp.4–6 bias, safety example, loop stability/disconnection | Local original, 11 pages. Its illustrative fault-current example is not a product compliance determination. |
| D6 | [TI SBAA185, May 2011, Thermal Noise Analysis in ECG Applications](../../docs/datasheets/originals/ti-app-notes/SBAA185.pdf): p.3 thermal-noise equation; pp.4–5 bandwidth/noise | Local original, 6 pages. Single-pole ENBW shortcut not used for sinc³. |
| D7 | [TI SBAA196A, Jan 2015, Understanding Lead-Off Detection in ECG](../../docs/datasheets/originals/ti-app-notes/SBAA196.pdf): p.2 DC-bias/common-mode need; pp.3–5 offset/noise; p.11 band overlap | Local original, 16 pages. |
| D8 | [TI SBAA230A, Digital Filter Types in Delta-Sigma ADCs](../../docs/datasheets/originals/ti-app-notes/SBAA230.pdf) | Local original, 9 pages; contextual filter guidance; actual response from D1. |
| D9 | [TI SLAA412B, LDO Noise Demystified](../../docs/datasheets/originals/ti-app-notes/SLAA412.pdf) | Local original, 10 pages; distinction between output noise and PSRR. |
| D10 | [TI SLAA414A, LDO PSRR Measurement Simplified](../../docs/datasheets/originals/ti-app-notes/SLAA414.pdf): load/headroom and measurement guidance | Local original, 7 pages. |
| D11 | [TI SBAA160A, Analog Front-End Design for ECG Systems Using Delta-Sigma ADCs](../../docs/datasheets/originals/ti-app-notes/SBAA160.pdf): pp.5–6 architecture/filtering | Local original, 11 pages. |
| D12 | [TI SLYY192, Fundamentals of Precision ADC Noise Analysis](../../docs/datasheets/originals/ti-app-notes/SLYY192.pdf) | Local original, 83 pages; contextual noise/dynamic-range guidance. |
| D13 | [TI ADS1298ECG-FE/ADS1198ECG-FE EVM, SBAU171D, Jan 2016](../../docs/datasheets/originals/reference-designs/ADS1298-EVM.pdf): power/input/RLD sections and schematics | Local original, 57 pages; reference implementation, not proof this design works. |
| D14 | [Official ESP32-S3-DevKitC-1 v1.1 guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html), header and power-supply sections | Official web reference inspected. |
| D15 | [Official DevKitC-1 v1.1 schematic, 2022-11-30](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf), p.2 | Official web PDF inspected; installed revision is not specified. |

The ESP32-S3 Technical Reference Manual was unnecessary for the pin/boot/interface conclusions and was not used. No firmware claims rely on it. CLI diagnostics emitted a fontconfig warning; netlist/ERC outputs were successfully generated. An initial Swift/PDF extraction path failed because of SDK/toolchain mismatch; the successful original-PDF extraction used Objective-C/PDFKit with the available compatible SDK. No electrical finding depends on failed extraction or unavailable tools.

## Part C — Prioritized findings

Severity describes consequence; **Unverified** explicitly means a plausible issue whose occurrence/size cannot be determined. Conditional examples below are calculated, not measured.

| ID | Severity | Subsystem | Finding | Component / net | Evidence | Recommended correction |
|---|---|---|---|---|---|---|
| F01 | Critical | ADC power | Analog supply span is 0 V | U1/U2 AVDD19/21/22/56/59, AVDD1 54, AVSS/AVSS1 → AGND | Native netlist; D1 p.12 operating min2.7 V | Reconnect actual supply/return pins deliberately; verify pin spans and netlist before energizing. |
| F02 | Critical | Supply/grounds | Invalid ADC digital supply and no MCU battery return | U1/U2 DVDD48/50→DGND; actual DGND33/49/51→AGND; U3 GND→DGND | Separate native nets; no DC bond | Correct DVDD and all grounds, with a deliberate common return; decouple the actual supply pins. |
| F03 | Critical | Analog stress | Rail-tied aux pins exceed analog absolute bounds if +3.3V starts | U1/U2 pins17/18/62 | Actual AVDD=AGND; D1 §7.1 | Make unused ties follow actual AVDD; disable optional output/rerouting modes. |
| F04 | High | Regulation | Two LDO outputs directly paralleled | U4.5/U5.5→+3.3V | ERC and netlist; D2/D3 reverse-current sections | Select one adequately rated source or separate rails with appropriate isolation. |
| F05 | High | Startup | Both LDO enables float | U4.3/U5.3 `/EN` | Net contains only enable inputs; D2 p.16, D3 §6.3.2 | Provide a defined hardware control/default, compatible with battery startup. |
| F06 | High | Synchronization | Slave clock has no source | U1.37 NC; U2.37 `ADC_CLK`; U2.52 external select | ERC dangling clock; D1 Table11 p.50 | Route one common valid clock; implement and verify master-clock startup and shared START. |
| F07 | High | Body bias | No deliberate DC body-bias/RLD path | All RLD60/61/63 NC; no bias contact | Netlist; D1 §10.1.2; D7 p.2 | Add a protected bias strategy, or one compensated RLD driver, with a dedicated contact. |
| F08 | Unverified | Wearer safety | Wearer current limits, ESD, charging/isolation and single faults are not established | E1–E16, R1–R32, BT1, U3 USB path | Only2 kΩ input series elements; unspecified cell/protection; no safety evidence | Complete protection and single-fault review before human testing; simulator tests first. |
| F09 | High | Digital startup | CS/RESET/PWDN/START lack defined external reset states | U1/U2 CS39/RESET36/PWDN35/START38; U3 GPIO6/7/8/10/14 | MCU-to-input-only nets; no bias resistors | Define hardware defaults; initialize outputs safely and guarantee non-overlap CS. |
| F10 | Medium | Input headroom | DC offsets and common mode are not bounded by a gain policy | R1–R32; CHnSET/reference firmware absent | No analog HP; D1 p.32 Eq.2/3 | Budget offsets/artifacts and CM together; select gain/attachment handling from measured extremes. |
| F11 | Medium | Bandwidth | 2 kSPS does not preserve a flat band to850 Hz | ADC sinc³ filter | D1 p.22/49: −8.26dB at850 Hz | Specify passband tolerance; evaluate4 kSPS HR or another justified rate/processing policy. |
| F12 | Unverified | CMRR/loading | 620 pF shunts interact with dry-electrode impedance and mismatch | All32 RC legs | Impedance model in Part F; D5 p.3 | Specify matching/dielectric; model and measure contacts/CMRR; reassess shunt capacitance and bias. |
| F13 | Unverified | LDO capacitors | Nominal aggregate output capacitance exceeds documented200 µF range; ESR/effective C unknown | C57/C54/C6/C7/C32/C33 plus digital bank |222.4 µF direct,242.6 µF after ground correction; D2/D3 | Select full capacitor network and LDO silicon; qualify limits, startup, ESR and transients. |
| F14 | Unverified | Component stress | Capacitor voltage/derating and resistor ratings cannot be signed off | All R/C; notably VCAP3 C25/C51 | No ratings/parts; VCAP3≈5.2 V after power correction | Complete BOM with voltage, dielectric, tolerance, leakage, effective C and power ratings. |
| F15 | Medium | Battery supply | 3.3 V LDO operation has insufficient full-discharge headroom without a cutoff policy | BT1/U4/U5 | Conditional dropout calculations in Part F | Specify cell and usable voltage window; budget dropout/droop or choose a suitable architecture. |
| F16 | Unverified | Current/thermal | DBV LDO thermal and RF-load transients may govern usable current | U5 TLV75533PDBV, U3 | D3 DBV231.1°C/W; D4 RF currents; no PCB/duty data | Budget sustained/burst currents; assess real copper/enclosure, thermal and brownout measurements. |
| F17 | Medium | Power interfaces | External DevKit USB/5V can introduce another3.3 V source and backfeed | U3 3V3/header21, U4/U5 | D14 exclusive supply options, D15 onboard LDO | Define and enforce supply modes; provide source/reverse-current isolation where needed. |
| F18 | Medium | Firmware | Reference, gain, optional outputs, grounded GPIOs and lead-off require deliberate setup | CONFIG1/3, CHnSET, PACE, GPIO, LOFF | D1 register defaults; no firmware | Enable/settle2.4 V ref, choose rate/gain, keep unused modes off; read back configuration. |
| F19 | Medium | Manufacturing | Most footprints and procurement identities are absent |106 components; U4 full MPN; U3 SKU | Schematic fields and absent PCB | Complete physical/BOM definitions and library portability before layout/fabrication release. |
| F20 | Unverified | Layout/system | Return paths, decoupling proximity, antenna keepout, SPI ringing and RF coupling unreviewed | Entire future PCB/assembly | No PCB or hardware data | Review routed PCB and actual DevKit antenna geometry; measure with radios/clocks active. |
| F21 | Low | Debugging | Slave DRDY and useful rail/reference nodes lack dedicated test access | U2.47 NC; no TP symbols | Netlist | Provide diagnostic access to both DRDYs/CLK, supplies, reference/VCAP and grounds. |

### F01–F03: supply faults and absolute maximum exposure

For each ADC, AVDD pins19/21/22/56/59 and AVDD1 54, AVSS20/23/32/57/58 and AVSS1 53, VREFN25 and actual DGND33/49/51 are all on `AGND`. This directly proves AVDD−AVSS=0 V. The required digital supply is measured from DVDD to the IC's **physical** DGND, so it is `V(net DGND)−V(net AGND)`, which is undefined with the current separated nets. Do not describe it as a measured 0 V. If only the ground islands were bonded, DVDD would then be 0 V; that partial change would still fail.

D1 §7.3 allows analog2.7–5.25 V and digital1.65–3.6 V. Its stress ratings are different: analog span−0.3…5.5 V, digital span−0.3…3.9 V, AVSS relative DGND−3…+0.2 V. The 0 V analog span is an operating violation; the auxiliary-pin connection additionally creates a conditional **absolute maximum** violation. If `+3.3V` turns on, aux17/18/62 are3.3 V above AVDD, versus the permitted+0.3 V. There is no external current-limiting resistor on these ties.

The manufacturer explicitly permits tying unused17/18/62 to AVDD (D1 p.10 footnote). A connection to a rail merely labeled AVDD elsewhere does not satisfy this when the actual supply pins are grounded. Pin18 is named TESTN_PACE_OUT2 by TI; the library's TESTP spelling on pin18 is a naming discrepancy, not a pin-number reassignment.

C6/C7 and C32/C33 are across+3.3V–AGND, while C8/C9 and C34/C35 are across+3.3V–DGND. None is correctly across an ADS supply pin pair as presently connected. The digital-bank return also has no battery DC return. Required verification: corrected native netlist, unpowered continuity/resistance at every actual IC supply/return pin, then current-limited dummy-load startup and direct pin-voltage measurements. No person should be connected during bring-up.

### F04–F05, F13, F15–F17: regulation, startup, and power-source interactions

U4 and U5 have independent control loops. Equal nominal3.3 V settings do not ensure equal actual voltages or load sharing. The higher setpoint can supply nearly the whole load, exposing U4's150 mA limit to MCU demand. U5 has a typical120 Ω **output discharge** when disabled; this is not an EN-input pulldown. One source on while U5 is off can therefore add roughly27.5 mA discharge load, and output bias/reverse current must be assessed. Simultaneous shared EN does not guarantee identical thresholds, ramps, UVLO or thermal states. Actual damage is not established by static inspection. [D2 §7.1.4; D3 §§6.3.2,7.1.4]

The `/EN` label has no connection to U3 or a source. D2 requires active termination and recommends ON/OFF→VIN if unused; D3 likewise recommends EN→IN when shutdown is unused. No guaranteed EN pulldown is specified for U5. The present state is **undefined**, not demonstrably latched off. Legacy LP2985 additionally specifies an ON/OFF slew condition; identify silicon before choosing a slow RC enable ramp.

The LP2985 value does not establish legacy versus new silicon. D2 p.30 Table8-1 distinguishes legacy CSO DLN/GF8 from new RFB, with M3 relevant to new orderables. The variants differ in dropout, capacitance/ESR, noise and reverse-current limits. Legacy parts can use ceramic output capacitors within the documented effective-C/ESR region; a blanket “ceramic-only is unstable” diagnosis is unsupported. C57's technology is not even specified. Select actual parts and assess the parallel network's impedance, not only C54 in isolation.

D14's supported USB,5 V-header and3V3-header supply choices are mutually exclusive. D15's v1.1 DevKit includes an SGM2212-3.3 regulator and reset/programming circuits. Accordingly, a complete DevKit can introduce another regulator via USB/5 V even though only two LDOs appear as carrier symbols. The actual fitted board revision is unknown. A source-free carrier+5V pin is acceptable for a deliberately direct3V3-powered DevKit; USB plus battery requires a documented isolation/sequencing solution. Large output capacitance can retain voltage as battery VIN collapses, creating a second reverse-current scenario. Neither backfeed current nor rail overshoot has been measured.

Corrective decision to make before implementation: choose whether the product uses a complete DevKit or a bare module, define valid power sources and return nets, then assign adequately rated separate or single regulated rails. Demonstrate startup/shutdown/hot-plug and full battery-window behavior. Headroom/thermal/transient screens are in Part F.

### F06, F09, F18: timing, reset, and firmware contracts

D1 Table11 p.50 specifies external CLK when CLKSEL=0; with CLKSEL=1 the internal oscillator reaches CLK only if CONFIG1.CLK_EN=1. CLK_EN resets0. The visible `ADC_CLK` near U1 is dangling, so enabling firmware alone cannot repair the missing electrical route. U2 requires the clock before clock-dependent POR/reset/configuration can complete. A valid correction could distribute U1's enabled clock or a shared external oscillator, followed by matched data-rate settings and a shared START edge. Shared RESET alone is not a synchronization clock.

U2 DRDY is intentionally NC. This can be acceptable after common-clock synchronization is demonstrated; as wired it conceals a nonconverting slave. During bring-up observe both DRDY signals and prove sample alignment. The clock's actual frequency also sets the actual sample rate; nominal2.048 MHz internal-clock operation is not an absolute timebase guarantee.

ADC CS, RESET, PWDN and START connect directly to ESP GPIOs without external bias. Thus no deterministic state is established while the controller is reset/high impedance or unpowered. A low pair of chip selects permits both DOUTs to drive different data. Add inactive CS defaults and a deliberate startup/reset policy, and guarantee signal state before enabling MCU outputs. The grounded ADC GPIOs must remain inputs or output-low; output-high would contend directly with ground. Keep PACE/RLD/WCT output modes and RLD rerouting disabled for unused hard-tied terminals.

The current MCU assignments GPIO6–14 avoid straps0/3/45/46, input-only GPIO46, USB19/20, and module-specific flash/PSRAM constraints on35–37. U3 CHIP_PU's external disconnection is not proof of a floating bare-chip enable: D15 supplies onboard reset/boot circuitry on an intact DevKit. That benefit is conditional on the actual assembly and revision. [D4 §§3.2,4; D14/D15]

Firmware requirements after correcting hardware include: bounded supply/clock startup, SDATAC before configuration, individual ID/register verification, internal reference enable and settling, matched rate/gain settings, valid clock-output setup, shared START, exclusive CS, proper SPI mode/timing and update keepout, frame length/status parsing, overflow/drop detection, and valid lead-off state labeling. No supplied firmware establishes these guarantees. Holding RESET or PWDN low does not make an ADC input tolerant of an absent supply; D1 §11.1 requires controlled signals during power-up.

### F07–F08: DC body bias and wearable operation

Without a body-bias contact or deliberate input DC-return network, input bias/leakage currents and accumulated charge can move the body's potential until another uncontrolled leakage/clamp path limits it. The620 pF capacitors provide AC coupling to AGND but are open at DC. A disconnected bias electrode would have the same absence of deliberate DC control; it would not be equivalent to a grounded body. D7 p.2 and D1 §10.1.2 p.86 explain the need for establishing common mode.

Choose either a protected passive bias or **one** compensated RLD loop with an appropriate bias contact and sensing configuration. Keep the other RLD amplifier off. A future RLD design must include output current limiting, adequate output swing, expected electrode/body/cable capacitance, lead disconnection, loop gain/phase margin and recovery. There is currently no pair of active RLD outputs tied together and no implemented RLD loop to call unstable. Its absence cannot establish the stability of a proposed replacement.

The only explicit acquisition input series elements are2 kΩ. There are no specified external low-leakage clamps, ESD protection network, isolated external-power interface, or protected-cell/charging design. This does not prove a particular regulatory leakage limit is exceeded; it does mean the design lacks evidence for safe human use. An internal pin-to-rail fault, a shorted shunt capacitor, multiple simultaneous contact paths, charging equipment and USB/debug connections need explicit analysis. ADS ±2 kV HBM/±500 V CDM component ratings and10 mA continuous input-current stress rating are **not wearer-safety or system-level ESD certifications**. [D1 §7.1/7.2; D5 pp.4–6]

Before human connection, use a simulator to validate fault-current limiting and normal acquisition, and obtain a safety review appropriate to the intended research use and external connections. Battery-only operation with USB/charging/debug disconnected must be an enforced test condition until those interfaces are separately qualified.

### F10–F12, F18: DC offsets, bandwidth, CMRR, and lead-off

No analog HP means electrode offsets and motion artifacts reach the PGA. That preserves DC and avoids another mismatched high-pass network, but does not prevent clipping. With a2.4 V reference and gain6, the nominal differential endpoints are±400 mV. An illustrative300 mV electrode offset leaves100 mV toward the nearer endpoint; gain12 would already clip. Common-mode headroom must be checked simultaneously using D1 Eq.2. Digital offset removal cannot recover clipped analog data.

Internal reference buffering resets **off**, while CHnSET resets to **gain6**. Each VREFP has only capacitors and requires firmware to enable the internal2.4 V reference and allow settling. The4 V reference is specified for a5 V analog supply and is unsuitable for the intended corrected3.3 V supply. This is a firmware contract, not proof that an external reference chip is missing. [D1 pp.33,69,71]

The input RC filters are nearly transparent at850 Hz for zero source impedance. Their128 kHz pole is not a specification for a flat850 Hz system. At2 kSPS the actual sinc³ filter has524 Hz−3dB bandwidth and−8.26 dB gain at850 Hz;4 kSPS improves this to1048 Hz and−1.97 dB. Neither gives an ideally flat passband. Equalization trades extra noise for amplitude correction and cannot remove aliases. ADS1298 is a continuous delta-sigma/PGA architecture, so a generic SAR “acquisition capacitor must settle in one aperture” diagnosis is inappropriate. Input loading, modulator-frequency aliases and RF rectification still matter. [D1 pp.26,32,49; D8/D11]

CMRR is especially sensitive to electrode impedance interacting with the shunt capacitors. An illustrative100 kΩ real impedance imbalance can convert about2.34% of a60 Hz common-mode voltage into differential voltage in the simple model, only about32.6 dB rejection before considering the ADC. These are not measured dry-electrode impedances or an actual system CMRR result. The model shows why the IC's115 dB typical intrinsic CMRR cannot be assigned to this assembly. Matching components alone does not eliminate electrode mismatch.

Internal lead-off detection exists but resets disabled per channel. DC excitation changes loading, offset and noise; it needs a return path. AC excitation is fDR/4: **500 Hz at2 kSPS is inside the requested EMG band**. At4 kSPS it is1 kHz, outside850 Hz but still requires rejection/leakage assessment. Choose diagnostic timing/excitation and invalid-sample labeling deliberately. A disconnected electrode can drift, rail or collect plausible-looking interference. Status bits are meaningful only after configuring the corresponding detection function. [D1 pp.39–40,74–75; D7]

### F14, F19–F21: component and physical limits

The VCAP3 pin is internally generated at AVDD+1.9 V relative AVSS; at corrected3.3 V operation C25/C51 therefore see about5.2 V. A4 V capacitor would be overstressed; a6.3 V MLCC might satisfy voltage rating yet lose substantial effective capacitance. Neither type is specified, so no actual capacitor rating failure can be asserted. Select a documented part with margin and effective1 µF at operating bias, for example an appropriately evaluated10 V or higher option. Similar specification work is required for every input, reference, supply and regulator capacitor.

The assigned U3 library footprint was available:44 pads in two22-position rows,2.54 mm pitch and22.86 mm row spacing. Pins1–22 map J1.1–22; pins23–44 map J3.22–1. Power pins1/2 and ground pins22/23/24/44 are intentionally stacked in the symbol. No connector-count mismatch was found. The local symbol-library table contains an unrelated absolute download path, however; portable library provisioning needs cleanup after review. No edits were made. The PAG and SOT23 footprint families agree with their specified IC packages, but no placed PCB is available to verify pad geometry/orientation or physical fit.

No layout claim is possible for ground returns, decoupling proximity, electrode routing, guard/leakage control, antenna clearance, SPI impedance/ringing, RF rectification, or enclosure/thermal behavior. Reference D1 §12.1 and D14 antenna requirements when reviewing a routed PCB. Wi-Fi/BLE burst currents, clock harmonics and digital-ground motion may contaminate low-amplitude EMG through supply, capacitive or radiated coupling; their actual size is unverified. No dedicated TP symbols exist. DevKit USB/UART/programming access is internal to a fitted assembly, not evidence that a future bare-module implementation is complete.

## Part D — Confirmed correct design elements

These positives are limited to the named connections and do not override the blockers above.

| Inspected feature | Confirmed evidence / qualification |
|---|---|
| Sixteen independent differential mappings | E1–E8→U1 channels1–8, E9–E16→U2 channels1–8; terminal1→P and2→N throughout, through the listed separate2 kΩ resistors. D1 pp.10–11 pin map. |
| Symmetric nominal input topology | Both legs of every pair have2 kΩ and620 pF to the same AGND; no accidental cross-channel/differential short found. Tolerance and physical matching remain unknown. |
| Reference bypass networks | U1 VREFP24→C19(.1 µF)||C20(10 µF)→VREFN25/AVSS; U2 C45/C46 equivalent. Independent references are not shorted together. D1 p.33 Fig31, p.96 Fig106. |
| VCAP values and returns |22 µF atVCAP1,1 µF atVCAP2/3/4 for both devices, all to actual AVSS net. These match D1 pp.10–11. Voltage/derating/placement need specification. |
| Regulator pin mappings and setpoints | U4 LP2985-3.3 and U5 TLV75533PDBV both3.3 V, correct five-pin SOT23 maps; U5NC4 intentionally disconnected. D2/D3 p.3. Their shared output remains a defect. |
| U4 noise bypass | BP4→C55 10 nF→actual GND2 net, consistent with D2 §7.1.3. Leakage/technology unknown. |
| Nominal input bypass exists | C53/C56 1 µF from each LDO input to its actual ground. Effective C/physical placement unverified. |
| Cascade SPI arrangement | Shared DIN/SCLK/DOUT plus distinct CS is explicitly supported by D1 §9.4.2.1. It is not invalid merely because ERC sees two outputs. Supplies, clock and nonoverlap CS must be corrected/guaranteed. |
| Suitable intended synchronization routes | Shared START38 and RESET36 reach both ADCs. This supports synchronization only with a valid common CLK and matched configuration. |
| Unused digital-pin treatment | RESV1,DAISY_IN and GPIOs are tied to intended digital-low net, as recommended in D1 pp.10,48. The entire power/ground topology must first be corrected; grounded GPIOs must not be programmed output-high. |
| DevKit carrier interface | U3 44-pad symbol/available footprint agrees with official header numbering; used GPIO6–14 avoid strapping/input-only/USB/flash constraints. D4/D14/D15. Actual fitted SKU and layout fit remain unverified. |
| No shared RLD-output contention | RLDOUT63 is explicitly NC on each ADC; no two active drivers are tied. No RLD function is provided. |
| Capacitor terminal connectivity | All57 caps have both pins represented in nets. There is no literally unconnected capacitor terminal; digital return-island and wrong-supply decoupling faults remain. |

## Part E — Amberflow issue tracking

The earlier and current columns refer to the supplied artifacts, which are identical. **Persists** means a defect is directly demonstrable in both; it does not establish that the historical Amberflow reviewer identified it. **No Fixed or New issue is established.** Unspecified parts, firmware states and measurements cannot receive a positive signoff merely because the files match.

| Amberflow category | Specific failure mode | Earlier revision | Current revision | Status | Evidence / explanation |
|---|---|---|---|---|---|
| Supply pins | Supply below operating minimum | ADC analog span is 0 V; invalid digital supply domain and MCU return | Same | **Persists** | F01/F02; D1 p.12. |
| Supply pins | Supply above rating | Actual operating rail voltages are not established | Same | **Unverified** | No demonstrated supply-rail overvoltage. F03 separately establishes conditional absolute maximum exposure at auxiliary inputs. |
| Resistors | Dissipation above component or footprint rating | Ratings and footprints absent | Same | **Unverified** | Fault screens in Part F; no basis for an actual resistor overrating claim. |
| Capacitors | Voltage at or above rating | Ratings absent; VCAP3 can reach 5.2 V after power repair | Same | **Unverified** | F14; no assumption that 6.3 V parts were selected. |
| Capacitors | Pin unconnected | Both terminals of all 57 capacitors appear in the netlist | Same | **No issue found** | No isolated capacitor pin. |
| Capacitors | Decoupling with floating ground or wrong return | C8/C9/C34/C35 return to isolated DGND; ADS supply decoupling is misconnected | Same | **Persists** | F01/F02; other capacitor AGND returns connect to battery negative. |
| Capacitors | Insufficient regulator output capacitance | Nominal bypass present; effective capacitance unknown | Same | **Unverified** | No evidence of nominal shortage; effective minimum capacitance and ESR require selected parts. Excess-capacitance concern is F13. |
| Capacitors | Ceramic-only output on an ESR-sensitive regulator | Capacitor technology and LP2985 silicon unspecified | Same | **Unverified** | D2 permits suitable ceramics; no blanket ceramic prohibition is justified. |
| Capacitors | Missing decoupling causes a rail dip greater than 5% | ADC decoupling is wrong; no waveform available | Same | **Persists** for wiring; **Unverified** for the dip | A static connectivity defect does not establish a transient magnitude. |
| Capacitors / amplifiers | Capacitive loading destabilizes an amplifier | RLD/PACE outputs unused; no external amplifier feedback loop | Same | **Not applicable** to an implemented feedback loop | No connected RLD loop. Regulator load stability remains unverified separately. |
| LEDs | Missing current limiting; direct open-collector sink without limiting | No discrete carrier LED or open-collector LED sink; U3 represents a complete DevKit | Same | **No issue found** in the official DevKit reference; actual assembly **Unverified** | D15 p.2 shows power LED D5 with R11 = 5.1 kΩ and addressable RGB LED D6, rather than a bare LED driven by a GPIO. Installed board revision and components are unspecified; see qualification below. |
| Regulators | Input above maximum rating | Exact battery unspecified | Same | **Unverified** for the actual cell | An assumed conventional 4.2 V full-charge cell is below both input maxima; the rail label alone is insufficient evidence. |
| Regulators | Dropout | 3.3 V regulators on the intended single-cell source | Same | **Unverified** operating occurrence | Conditional voltage, load and temperature screens in Part F establish the headroom and cutoff that must be designed. |
| Regulators | Disabled by own enable network or latched off | EN net undriven; no latch circuit | Same | **Persists** for undefined enable | F05; no reconstructed self-latching mechanism is claimed. |
| Regulators | Output inconsistent with rail label | Both selected variants have fixed 3.3 V outputs; rail labeled +3.3V | Same | **No issue found** for setpoints | Actual energized output remains unestablished with the current wiring. |
| Regulators | Two regulators drive the same rail | U4.5 and U5.5 directly share +3.3V | Same | **Persists** | F04; a powered DevKit may add a third source. |
| Regulators | Floating enable or incorrect power-good dependence | EN contains only U4.3/U5.3; no power-good circuit | Same | **Persists** for floating enable | No inappropriate power-good dependency exists. |
| Regulators | Switching regulator directly feeds a noise-sensitive analog supply | No carrier switching converter | Same | **Not applicable** | Supply and RF noise remain unverified; absence of a switching converter does not establish low noise. |
| Regulators | Cannot sink current when setpoint moves | Fixed-output regulators; no moving-setpoint circuit | Same | **Not applicable** to this setpoint condition | Parallel sourcing, active discharge and reverse-current concerns are F04/F17. |
| Regulators / sequencing | Signals active before receiving supply is available | ADC supply domain invalid; direct controller links | Same | **Unverified** actual sequence | The exposure topology is present in both revisions (F02/F03/F09); no transient waveform or firmware sequence proves when signals become active. |
| Amplifiers | Supply span outside operating range | ADS internal PGA analog supply span is 0 V | Same | **Persists** | F01; optional RLD output function is disabled and unconnected. |
| Amplifiers | Supply pins reversed | AVDD and AVSS share ground; no reversed bipolar rails | Same | **No issue found** for reversal | The zero supply span is separately a critical defect. |
| Amplifiers | Input common-mode voltage outside operating range | No controlled body DC operating point; offsets unknown | Same | **Unverified** actual voltage violation | Missing bias persists (F07); actual common-mode voltage and excursions require measurement. |
| Amplifiers | Oscillation, ringing or inadequate phase margin | No implemented RLD loop; no waveforms | Same | **Unverified** system behavior | RLD-loop fault is inapplicable; regulator and SPI ringing require measurement. |
| Amplifiers | Output clipping or overloading | Gain, offsets and common mode unknown; PACE pins tied to a rail | Same | **Unverified** actual clipping | F10 evaluates DC headroom. Enabling a hard-tied PACE output could create contention. |
| Power multiplexers | Disabled output; unused priority; rejected input or failed failover; floating controls; unconnected input; wrong output voltage | No carrier power multiplexer | Same | **Not applicable** | Each listed condition lacks a corresponding multiplexer. USB power-source policy still requires F17 review. |
| Wiring | IC missing a required ground | MCU ground lacks a battery DC return; ADC grounds and supplies misassigned | Same | **Persists** | F01/F02; this is not merely a missing PWR_FLAG. |
| Wiring | Rail without a valid source | ADC supplies invalid; carrier +5V is a singleton net | Same | **Persists** for ADC power | +5V need not be sourced when an intact DevKit is powered through its 3V3 header. |
| Mixed signal | Incorrect logic levels | Invalid physical supply and ground references | Same | **Persists** | The actual design does not establish valid logic operating conditions. Part F evaluates nominal compatibility after correcting the 3.3 V supplies and returns. |
| Mixed signal | Inadequate bus rise or fall time | No PCB, load model or waveforms | Same | **Unverified** | Nominal timing capability does not prove actual edge quality. |
| Mixed signal | Open-drain output missing a pull-up | Used ADS DOUT/DRDY outputs are not open-drain | Same | **No issue found** | DOUT enters high impedance under CS control; no generic I²C-style pull-up is required. |
| Mixed signal | Pull-up exceeds output sink-current capability | No external carrier pull-ups; fitted DevKit variant unspecified | Same | **Not applicable** to the carrier; assembly **Unverified** | GPIO capacitive current remains unverified. An installed DevKit's internal circuits require its actual board specification. |
| Mixed signal | ADC source impedance prevents acquisition settling | ADS uses a PGA and delta-sigma converter, rather than a generic SAR acquisition aperture | Same | **Not applicable** to the generic SAR rule | Electrode RC loading, modulator aliases and filter settling are evaluated explicitly. |
| Mixed signal | Slow threshold crossing without suitable hysteresis | ADS SCLK has a Schmitt input; other control waveforms unknown | Same | **Unverified** actual edge behavior | No missing external SCLK Schmitt buffer is demonstrated. D1 §9.5.1.2. |
| Mixed signal | Multiple threshold crossings from ringing or noise | No PCB or oscilloscope evidence | Same | **Unverified** | F20. |
| Firmware at reset | Incorrect or floating boot straps | ADC GPIO assignments avoid straps; installed U3 board and eFuses unknown | Same | **No issue found** in assignment; boot configuration **Unverified** | Verify the installed board and eFuse configuration. Arbitrary additional straps are not justified by this carrier schematic. |
| Firmware at reset | Switch or enable incorrectly depends on controller reset pulls | Regulator EN has no MCU connection | Same | **No issue found** for this dependency | The independent floating-EN fault persists. |
| Firmware at reset | Transistor gate, regulator enable or control input floating | No carrier transistor; regulator EN and ADC controls lack hardware bias | Same | **Persists** | F05/F09. An intact DevKit has its own transistor and reset circuits, qualified below. |
| Firmware at reset | Controller pin input rating exceeded | No higher-voltage carrier signal intentionally drives a GPIO; ground references invalid | Same | **Unverified** actual MCU stress | The supply-reference defect persists; no nonexistent 5 V logic route is assumed. |
| Firmware during normal operation | GPIO exceeds output current limits | No firmware or current data; ADC inputs have high impedance | Same | **Unverified** | No demonstrated overload. Grounded ADS GPIOs must never be configured to drive high. |
| Firmware during normal operation | Two outputs drive against each other | Shared MISO; grounded ADS GPIOs and tied auxiliary pins have firmware-dependent output modes | Same | **Unverified** actual firmware conflict | Shared MISO is supported when only one CS is active. Simultaneous selection or conflicting output configuration is unverified. The confirmed parallel-LDO fault belongs to F04, not this firmware condition. |
| Firmware during normal operation | GPIO drives a peripheral while its supply is off | Direct ADC inputs; invalid ADC supply domain | Same | **Unverified** actual GPIO state | The exposure topology is present in both revisions. Reset does not confer off-state input tolerance; actual firmware states and supply waveforms are unavailable. |
| Firmware during transitions | Supply dip or brownout reset | No transient data | Same | **Unverified** | F13/F15/F16; a dip greater than 5% is not demonstrated. |
| Firmware during transitions | Input driven high before receiving device is powered | No fail-safe control or isolation; invalid supply network | Same | **Unverified** actual sequence | Existing topology permits exposure; F02/F03/F09 require correction and sequencing verification. |
| Additional | Capacitor tolerance and DC-bias derating | All capacitor parts unspecified | Same | **Unverified** | F12–F14; VCAP3 and effective regulator output capacitance need particular attention. |
| Additional | Footprint and package correctness | Five IC or assembly footprints assigned; 106 other components lack footprints | Same | **Persists** for incomplete physical definition | Known IC package families and pin mappings are consistent; no PCB signoff is possible. |
| Additional | Connector pin counts | E1–E16 each have two pins; U3 has 44 pads matching the header map | Same | **No issue found** electrically | Physical electrodes and connectors remain unspecified; the intended bias contact is absent (F07). |
| Additional | Signal integrity and RF interference | No PCB or measurements | Same | **Unverified** | F20. |
| Additional | Thermal behavior | Loads, duty cycle, copper and enclosure unknown | Same | **Unverified** | Conditional DBV calculation in Part F; no measured temperature. |
| Additional | Excessively strong open-drain pull-ups | No carrier open-drain bus or pull-up network | Same | **Not applicable** to the carrier | Do not add pull-ups merely to suppress ERC warnings. Installed DevKit circuitry remains subject to its actual board specification. |

For the **official DevKitC-1 v1.1 reference**, D15 p.2 shows red power LED **D5 with R11 = 5.1 kΩ (1%)** and addressable RGB LED **D6 (SK68XXMINI-HS)**. D6 has separate supply and logic pins; its DIN is reached from GPIO38 through **R17 = 0 Ω**. R17 is a logic connection, not a bare-LED current limiter. The board also supplies the CHIP_PU reset network **R5 = 10 kΩ / C6 = 1 µF**, reset and boot buttons, and automatic programming transistors Q1/Q2 with base resistors R10/R12. Thus an unused carrier CHIP_PU header is not evidence that an intact DevKit's module enable floats. These reference-board observations do not establish the fitted SKU, revision, modifications or component population.

Rows with multiple statuses distinguish a confirmed topology defect from an unmeasured consequence. Supply dips, oscillation, clipping events, firmware output conflicts and sequencing events remain **Unverified** unless behavior is supported directly. Their relevant exposure topology can still persist in both revisions. Historical Amberflow annotations remain unavailable; identical supplied files cannot demonstrate a historical repair.

## Part F — Quantitative engineering calculations

All operational examples in this part assume **corrected valid supplies and common returns**. The present circuit cannot produce valid acquisition. Assumed battery voltages, electrode impedances, offsets and RF duty are examples, not measured or procured component specifications.

### F.1 Supply margins, LDO dropout, current and temperature

For a3.3 V fixed LDO, available nominal headroom is `H = Vcell − 3.3 V`:

| Assumed Vcell | H |
|---:|---:|
|4.2 V full-charge example|0.9 V|
|3.7 V nominal label|0.4 V|
|3.3 V low-cell example|0 V|

The exact cell minimum/maximum, temperature, ESR, protection cutoff and wiring loss require its datasheet. At4.2 V the input is1.3 V below U5's5.5 V recommended maximum and1.8 V below its6 V absolute maximum. LP2985 recommended input maximum is16 V. These are different from output regulation requirements. [D2/D3 §§5.1,5.3]

| Part / load | Datasheet maximum dropout used | Approximate3.3 V + dropout screen | Margin at3.7 V |
|---|---:|---:|---:|
| U5 **DBV**,500 mA,≤85°C |215 mV|3.515 V|185 mV|
| U5 **DBV**,500 mA,≤125°C |238 mV|3.538 V|162 mV|
| U4 legacy,150 mA,full temperature |575 mV|3.875 V|−175 mV|
| U4 new,150 mA,full temperature |254 mV|3.554 V|146 mV|
| U4 legacy,50 mA,full temperature |225 mV|3.525 V|175 mV|
| U4 new,50 mA,full temperature |184 mV|3.484 V|216 mV|

Sources: D2 pp.6–7 and D3 p.6 electrical tables. LP2985 dropout is defined at100 mV output loss; these additions are headroom screens, not guaranteed nominal-output accuracy at that boundary. Include output tolerance, load/cell droop and PSRR degradation near dropout. Do not substitute the TLV DYD dropout or thermal row for the selectedDBV package. A3.3 V LDO cannot maintain regulated3.3 V through a cell falling to3.3 V or below; usable battery window or supply architecture must reflect this.

D1 p.16, RLD/WCT/PACE off, gives typical per-device HR analog2.75 mA at3 V plus digital0.5 mA at3 V, about3.25 mA/device or6.5 mA for two. LP is about2.3 mA/device. These are reference-condition estimates, not guaranteed3.3 V/4 kSPS currents. D4 p.27 requires a module source capable of at least0.5 A; p.28 lists Wi-Fi TX peak355 mA for802.11b1 Mbps20.5 dBm, BLE344 mA at20 dBm/187 mA at0 dBm and Wi-Fi RX95–97 mA. DevKit overhead and actual duty are additional. A150 mA LP2985 is insufficient as the sole assumed RF-module source; two unsanctioned parallel regulators do not solve it.

Illustrative sustained load `I = 355 + 6.5 = 361.5 mA`, excluding DevKit overhead:

`P_LDO ≈ (VIN − VOUT) I = (4.2 − 3.3) × 0.3615 = 0.325 W`.

For U5 DBV, D3 p.5 gives JEDEC `RθJA = 231.1°C/W`, so `ΔTJ ≈ 75.2°C`. This gives about100°C at25°C ambient or125°C at50°C ambient. At500 mA:0.45 W and104°C rise, about129°C at25°C. At3.7 V/361.5 mA:0.145 W and33.4°C rise. These are conditional steady-state screens using reference-board thermal impedance; RF bursts, copper and enclosure can change results substantially. The headline60.3°C/W refers to another package/EVM condition and does not qualifyDBV. No actual overheating is established.

If an independent U4 supplied only6.5 mA of AFE load at4.2 V, its pass loss would be about5.85 mW plus quiescent loss, a modest current/thermal load. The present wiring does not provide that separation.

Ideal LDO efficiency ignoring quiescent current is approximately `VOUT/VIN`:89.2% at3.7 V,78.6% at4.2 V. Battery current approximately equals regulated load current plus quiescent/assembly overhead. Runtime is `usable Ah / average A`; at the illustrative continuous0.3615 A it is2.77 h per usableAh before overhead and cutoff. No actual battery capacity/runtime or discharge capability can be inferred.

### F.2 Output capacitance, transients, startup and reverse current

Direct+3.3V–AGND nominal capacitance:

`C6 + C7 + C32 + C33 + C54 + C57 = 0.1 + 10 + 0.1 + 10 + 2.2 + 200 = 222.4 µF`.

The+3.3V–DGND bank adds `C8+C9+C34+C35=20.2 µF` after valid ground bonding, giving242.6 µF before DevKit capacitors. D3 §5.3 and §7.1.1 specify up to200 µF; D2 new-chip recommended range also ends at200 µF. Nominal totals exceed that range, but actual effective capacitance depends on tolerance/bias/technology. Distributed parasitics also affect stability. A proven oscillation or exact effective-C violation cannot be asserted without parts and measurements.

Legacy LP2985 needs effective output≥2.2 µF and permitted ESR; new silicon permits≥1 µF with its specified ESR range. U5 permits suitable1 µF ceramics. [D2 §§7.1.1–7.1.3, Figs5-36–38; D3 §7.1.1] There is no basis to reject ceramic-only output solely from the family name.

Capacitor-only step screen:

`ΔV ≈ ΔI Δt / Ceff + ΔI·ESR`.

AtCeff200 µF andΔI0.3 A, a5%3.3 V allowance=165 mV gives unsupported time `CΔV/ΔI ≈110 µs`, before ESR and regulator response. At100 µF it is55 µs. This is neither a prediction nor a measurement of a>5% dip.

For200 µF at3.3 V: `Q=CV=660 µC`; `E=CV²/2=1.089 mJ`. Charging in550 µs would require1.2 A average before load. U5's typical startup measured with a small capacitor cannot be transferred unchanged to this bank; current limit and soft start alter timing. Scope actual startup.

U5's typical output discharge gives `I≈3.3/120=27.5 mA` if externally held high while disabled, conditional on that resistance remaining applicable. D3's absolute OUT limit is `min(VIN+0.3 V,6 V)`; the LP new-chip output limit and reverse-current guidance differ. Battery removal with a charged output bank or USB-fed DevKit must therefore be assessed for output-above-input stress; no reverse-current waveform is available. [D2 §7.1.4; D3 §§5.1,7.1.4]

### F.3 ADC differential range, offset and common-mode headroom

Using correctedAVDD3.3 V,AVSS0 V and enabledVREF2.4 V:

`VD,FS = ±VREF/G`; total span=`2VREF/G`. [D1 p.32 Eq.3]

| Gain | Nominal differential endpoints |
|---:|---:|
|1|±2.4 V|
|2|±1.2 V|
|3|±0.8 V|
|4|±0.6 V|
|6 (reset gain)|±0.4 V|
|8|±0.3 V|
|12|±0.2 V|

Each input must also remain within its individual voltage limits and satisfy PGA headroom. D1 Eq.2:

`AVSS + 0.2 V + G|VD,max|/2 < VCM < AVDD − 0.2 V − G|VD,max|/2`.

Atgain6:

| Maximum differential magnitude | Allowed VCM for3.3 V supply |
|---:|---:|
|300 mV|1.10–2.20 V|
|350 mV|1.25–2.05 V|
|400 mV|1.40–1.90 V|

Endpoints in this table are strict headroom boundaries, not recommended operation exactly at the edges. A300 mV DC offset atgain6 leaves100 mV toward the nearer ADC endpoint; actual EMG, motion and gain/reference tolerance must fit. Gain12 fails for that example. A digital high-pass or DC subtraction cannot restore data clipped in the PGA/modulator.

Atgain6,24-bit code weight=`(2×2.4/6)/2²⁴=47.68 nV`. This does not mean47.68 nV effective sensitivity or24 noise-free bits. D1 Table1's typical7.3 µVpp at2 kSPS/gain6 corresponds to about`log2(0.8 V/7.3 µV)=16.74` noise-free bits under that test convention, before electrodes or interference. It is a benchmark at the table's3 V/shorted-input conditions.

### F.4 External filtering, input loading, and CMRR

For negligible source impedance and high ADC impedance, each branch is:

`H(s)=1/(1+sRC)`, `τ=2000Ω×620pF=1.24 µs`, `fc=1/(2πRC)=128.35 kHz`.

With equal components the differential transfer is the sameH, notH². Odd-mode equivalent2R andC/2 also givesRC. No differential capacitor bridgesP/N.

| Frequency | Ideal external RC gain |
|---:|---:|
|850 Hz|−0.000190 dB|
|256 kHz (LP fMOD)|about−6.97 dB|
|512 kHz (HR fMOD)|about−12.28 dB|

D1 p.32 givesfMOD=fCLK/8 LP orfCLK/4 HR, with nominalfCLK2.048 MHz. D1 p.49 states digital passbands repeat at multiples offMOD; the modest external suppression there requires an interference/alias budget. Do not extrapolate an ideal lumpedRC to claim2.4 GHz attenuation; parasitics and rectification dominate at RF.

Per620 pF shunt, `|ZC|=1/(2πfC)` gives5.13 MΩ at50 Hz,4.28 MΩ at60 Hz,302 kΩ at850 Hz. D1's20 pF typical input capacitance and1 GΩ DC input impedance do not remove this external AC loading. With an illustrative100 kΩ real electrode source, `(R+Ze)C` lowersfc to2.52 kHz and gives about−0.47 dB at850 Hz;1 MΩ gives approximately256 Hz and−10.8 dB. Real electrodes are complex, frequency dependent, and unmeasured.

For a simple independent-branch model:

`HP=1/[1+jωCP(RP+ZP)]`, `HN=1/[1+jωCN(RN+ZN)]`.

`Ad=(HP+HN)/2`, common-to-differential gain=`HP−HN`; hence `CMRRext=20log10(|Ad|/|HP−HN|)`.

Atlowfrequency with matchedC, imbalance dominated by realΔZ gives approximately `CMRRext≈−20log10(2πfC|ΔZ|)`. At60 Hz:ΔZ10 kΩ→52.6 dB;100 kΩ→32.6 dB. For the latter case,1 V common mode produces about23.4 mV differential in this illustrative model. Body/electrode capacitance and shared-channel interactions are omitted; this is a sensitivity calculation, not actual wristCMRR.

Component-only example with ideal electrodes: a2% leg-to-leg time-constant mismatch gives about100.6 dB at60 Hz;4% gives94.6 dB;12% gives85.0 dB. ±1% resistors on opposing extremes create2%R mismatch; ±5% capacitors create10%C mismatch, potentially about12% total. **Those tolerances are examples; none are specified.** D5 p.3 supports this common-to-differential mechanism. Intrinsic ADC typical115 dB CMRR (D1 p.14, specified test conditions) cannot cancel a differential voltage already generated by external mismatch.

### F.5 Actual sample-rate bandwidth and noise

D1 p.49 Eq.5:

`|HADC(f)| = |sin(Nπf/fMOD) / [N sin(πf/fMOD)]|³`, `N=fMOD/fDR`.

For largeN this approaches`|sin(πf/fDR)/(πf/fDR)|³`. The approximate gains below differ negligibly from the exactHR expression at nominal2.048 MHz.

| Per-channel fDR | D1−3 dB bandwidth | At100 Hz | At500 Hz | At850 Hz |
|---:|---:|---:|---:|---:|
|2 kSPS|524 Hz|−0.107 dB|−2.736 dB|−8.262 dB|
|4 kSPS|1048 Hz|−0.0268 dB|−0.673 dB|−1.965 dB|

Nyquist alone is insufficient to define useful EMG bandwidth. The sinc³ also does not provide a50/60 Hz notch at either rate; those frequencies are in the passband. Digital filtering may reduce residual interference but cannot repair PGA saturation or recreate aliased signal.

For two uncorrelated2 kΩ resistors at300 K:

`en = √[4kT(RP+RN)] = √[4×1.380649e−23×300×4000] = 8.14 nV/√Hz`.

Integrated over an ideal rectangular20–850 Hz band: `vn=en√830=0.235 µVrms`. This is a density-to-band integral, not8.14 nV RMS. Including the sinc³ weighting within20–850 Hz gives approximately0.183 µVrms at2 kSPS or0.218 µVrms at4 kSPS, by numerical integration of`en²|HRC|²|HADC|²`. It excludes noise that aliases from other bands and does not model electrode noise. D6 p.3 gives the resistor-noise relation; the actual digital filter fromD1 is used rather than a single-poleπ/2 ENBW shortcut.

If both electrode real impedances were100 kΩ throughout the same rectangular band, their pair's thermal noise would be about1.66 µVrms **before frequency-dependent loading/filter weighting**. This is an illustrative resistive model; contact/excess noise and complex impedances are unknown. A200 pA input bias through100 kΩ develops20 µV DC; actual differential bias error depends on both currents and impedances. D1 p.13 lists±200 pA at25°C, up to±1.2 nA over industrial temperature under its specified conditions. DC lead-off adds further offset/noise.

D1 p.22 typical shorted-input noise,3 V analog/2.4 V reference:

| Gain | HR2 kSPS | HR4 kSPS |
|---:|---:|---:|
|1|4.1 µVrms|6.1 µVrms|
|4|1.3 µVrms|1.9 µVrms|
|6|1.1 µVrms|1.5 µVrms|
|12|0.9 µVrms|1.2 µVrms|

LP/gain6 is1.4 µVrms at2 kSPS and2.4 µVrms at4 kSPS. These are integrated converter-output-band values, not densities or identically post-filtered20–850 Hz values. They must not simply be RSS-added to the830 Hz resistor calculation as a “system noise” result. A valid budget needs all sources under the same transfer function and alias assumptions. LDO output noise is not automatically input-referred ADC noise: use frequency-dependentPSRR/reference coupling and actual rail measurements. [D9/D10]

### F.6 SPI throughput, timing, synchronization and logic levels

At2/4 kSPS each ADC frame is `24 status + 8×24 channel =216 bits=27 bytes`; two devices require432 bits/54 bytes per sample interval. Powered-down channels still occupy their slots. [D1 §9.4.1.3.2 p.53]

| Rate | Period |16-channel payload |Two complete frames | Bare SCLK lower bound |
|---:|---:|---:|---:|---:|
|2 kSPS|500 µs|768 kbit/s=96 kB/s|864 kbit/s=108 kB/s|>0.864 MHz|
|4 kSPS|250 µs|1.536 Mbit/s=192 kB/s|1.728 Mbit/s=216 kB/s|>1.728 MHz|

`tpair=432/fSCLK`:1 MHz→432 µs;2 MHz→216 µs;4 MHz→108 µs;8 MHz→54 µs. These omit GPIO/CS gaps, MCU latency and ADC update requirements. Atnominal2.048 MHz,4tCLK=1.953 µs. Illustratively adding one update interval and two final-CS hold intervals to a4 MHz payload gives at least113.86 µs before other software/setup gaps, leaving about136 µs of the250 µs4 kSPS period. This is a schedule budget, not proof of firmware operation. RDATA mode adds8 command clocks per device:448 clocks/pair and bare1.792 MHz at4 kSPS. Wireless packets, metadata and retransmissions add traffic beyond the table.

D1 p.17, atDVDD2.7–3.6 V: minimumSCLK period50 ns (20 MHz by period), high/low≥15 ns, DINsetup/hold10 ns, CSsetup6 ns, CS-high≥2tCLK, finalbyte fallingedge-to-CS-high≥4tCLK, and CS-high-to-DOUT-high-Z≤10 ns under the specified test load. UseCPOL0/CPHA1 and non-overlap selects. At faster command rates, honor4tCLK command-decode spacing; at4 MHz a byte is2 µs, only marginally above nominal1.953 µs and slightly shorter than4tCLK at a−2.5% industrial internal-clock extreme. Add deliberate command spacing/slow command speed rather than assuming the nominal example covers all clocks. Conversion frame speed is a separate timing question. [D1 §§9.5.1,9.5.2.9]

SharedSCLK can clear either device'sDRDY irrespective ofCS (D1 pp.52–53); it is not a wired-OR status bus. With valid synchronization oneDRDY may pace paired reads; while diagnosing or using other SPI traffic, account for TI's clock-gating/event guidance. Do not leave free-runningSCLK on the bus.

Nominal configuration options atfCLK2.048 MHz: HR DR100→2 kSPS; HR DR011→4 kSPS; LP DR011→2 kSPS; LP DR010→4 kSPS. [D1 p.67] Match both chips. POR wait is at least2¹⁸/fCLK≈128 ms nominal and untilVCAP1 passes1.1 V per D1 §11.1; RESET low≥2tCLK≈0.977 µs, then18tCLK≈8.79 µs. The slave's clock must be valid for its clock-dependent initialization. HR first settled output is4616tCLK≈2.254 ms at2 kSPS or2312tCLK≈1.129 ms at4 kSPS. After an input step, settled data are available on the fourthDRDY. [D1 pp.48,51–52,96]

Conditional logic budget with **corrected common3.3 V rails/grounds**:

- ADSVIH≥0.8DVDD=2.64 V; VIL≤0.66 V; VOH≥2.9 V andVOL≤0.4 V at500 µA. [D1 p.16]
- ESPVIH≥0.75VDD=2.475 V; VIL≤0.825 V; VOH≥0.8VDD=2.64 V andVOL≤0.33 V under the table's high-impedance condition. [D4 p.27]
- ADS→ESP high/low margins each0.425 V. ESP→ADS guaranteed table-bound high margin is **0 V**, low margin0.33 V. Same-voltage operation does not inherently require level translation, but these tables alone do not prove robust positive worst-case high noise margin in that direction. Check actual lightly loadedVOH/edges and rail tolerances. ESP40 mA/28 mA figures are typical drive characterization, not blanket safe per-pin current limits.

These are not margins for the presently invalid supply network. D1 digital absolute input range is physicalDGND−0.3…DVDD+0.3 V; recommended operation is tighter. Powered MCU signals into an unsupplied ADC can inject current regardless ofRESET/PWDN state.

### F.7 Resistor stress and wearer-fault screens

For a2 kΩ resistor with an assumed3.3 V entirely across it: `I=V/R=1.65 mA`, `P=V²/R=5.45 mW`. At4.2 V:2.10 mA and8.82 mW; at5 V:2.50 mA and12.5 mW. These are illustrative single-path electrical screens. The actual component power/pulse rating is absent; normal input bias currents imply much lower dissipation, but no rating signoff follows.

They also do not prove a specific single fault creates that wearer current or that it is acceptable. Patient/body impedance, number of parallel contacts, capacitor/resistor faults, clamps and external-power return paths must be included. D5 p.5 discusses a protection-resistor example for a stated fault-current target; it cannot replace classification and formal evaluation of this product's complete normal/single-fault paths. Increasing protection resistance also changes thermal noise, input loading andCMRR, so protection and signal quality must be engineered together.

## Part G — Recommended next actions

### 1. Required before initial hardware power-up

1. Correct and review every ADS supply and return connection: AVDD/AVDD1, AVSS/AVSS1, DVDD, DGND and VREFN. Define valid battery, MCU and ADC returns, and connect decoupling across the actual supply pins. Recheck auxiliary pins 17/18/62 against the actual AVDD rail.
2. Resolve the two directly paralleled 3.3 V sources. Decide whether U3 will remain a complete DevKit or become a bare module, and define allowed external power sources. Specify exact regulators and capacitors, establish current and headroom budgets, and define EN in hardware.
3. Provide a real common ADC clock and a workable master/slave power-on reset and configuration sequence. Define CS, RESET, PWDN and START defaults so controller reset cannot leave controls floating or select conflicting outputs.
4. Specify capacitor ratings and effective capacitance, particularly for VCAP3 and the combined regulator output bank. Check startup, ESR and reverse-current requirements for the selected LP2985 silicon and TLV755P DBV package.
5. Re-export the netlist, rerun ERC and examine every substantive violation. PWR_FLAG and no-connect markers must reflect the circuit, rather than hide supply or clock faults. Verify unpowered continuity at physical IC pins before energizing.
6. Bring up the board from a current-limited supply with dummy inputs and no wearer. Measure rails, pin voltages, current and temperature before enabling ADC conversions or radio transmissions.

### 2. Required before human-worn testing

1. Implement and verify a deliberate protected DC body-bias strategy and dedicated contact. If RLD is chosen, use one compensated driver and validate disconnection, stability and recovery.
2. Complete electrode fault-current, protection, leakage, ESD and single-fault analyses. Include all 32 contacts, shorted filter capacitors, pin-to-rail faults and parallel paths. Specify a protected cell and physical battery connection.
3. Enforce battery-only operation with USB, charger and debugging connections disconnected until isolation and all external power states are qualified. Document the test configuration and prevent accidental reconnection while worn.
4. Demonstrate safe operation first with an electrode/body simulator. Obtain an appropriate wearer-safety review before proceeding to human testing.

### 3. Improvements for EMG signal integrity

1. Define allowed passband attenuation and choose 2 or 4 kSPS HR operation accordingly. At 4 kSPS the filter better preserves 850 Hz content; budget the associated noise and data transport.
2. Measure dry-contact impedance, imbalance, offsets and motion excursions. Use those results to select gain, bias, protection and input RC values. Specify resistor matching and suitable input-capacitor dielectric and tolerances.
3. Establish an offset and headroom policy, saturation detection and recovery, and valid-sample flags. Choose an EMG-compatible lead-off policy; account for in-band contamination before enabling continuous 500 Hz excitation at 2 kSPS.
4. Plan analog supply and return currents, reference noise and coupling from RF bursts. Use short local decoupling loops and balanced input routing on the PCB, then measure the result.

### 4. Bench, simulation, firmware and PCB evidence still required

- **Power:** test the full battery window; startup and shutdown; USB insertion and removal; regulator output-to-input reverse bias; load-step dips and overshoot near each IC; noise with RF on and off; and enclosure temperatures.
- **Timing and firmware:** capture both CLK and DRDY waveforms; verify sample alignment, register readback, reference settling, CS dead time, SPI edge quality, worst-case DMA and interrupt latency, lost-frame accounting, and wireless throughput with realistic packet overhead.
- **Analog:** measure shorted-input noise with a specified common post-filter; sweep differential signal and common-mode voltage; measure 50/60 Hz CMRR with representative impedance imbalance; and test offset/artifact clipping, recovery, contact disconnection and lead-off behavior.
- **Simulation:** analyze the proposed RLD loop with body, electrode and cable models and fault conditions; evaluate the revised RC/protection network; and examine regulator startup and stability where selected conditions fall outside guaranteed specifications.
- **PCB and assembly:** check routed-board DRC and schematic/netlist parity, power-pin pads and orientation, electrode connector pinout, ground returns, decoupling placement, antenna keepout, leakage and ESD paths, thermal copper, and DevKit fit and SKU.

### 5. Lower-priority improvements

- Add accessible test points for both DRDY signals, shared CLK, rails, grounds, reference and VCAP nodes.
- Complete portable library and BOM definitions, and document intentional no-connect pins. Repair dangling stubs only after explicit implementation instructions.
- Document allowed operating modes, gain/reference/rate/lead-off registers, power connections and wearer-test conditions alongside the final design.
- Consider the additional VCAP3 100 nF shown in D1 Fig.106 during layout and decoupling review. The existing 1 µF matches the pin-table minimum; omission of the extra capacitor alone does not demonstrate failure.

**Implementation remains pending explicit user instruction.** All corrections above are recommendations; this audit implements no automatic fixes.
