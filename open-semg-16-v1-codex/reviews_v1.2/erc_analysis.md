# Open-sEMG-16 V1.2 — individual ERC analysis

27 October 2026. Analysis only: no schematic, project, library, ERC configuration, existing diagnostic or historical review was modified. The only created file is this report.

## 1. Result and evidence

The comparison uses the requested [initial-erc.json](initial-erc.json) and [final-erc.json](final-erc.json) in the review-directory root, rather than substituting the similarly named files under diagnostics. Both identify open-semg-16-v1.2.kicad_sch, one root sheet, KiCad 10.0.7 and the same included severities/check exclusions. Their recorded times are 2026-10-27T19:16:31 and 2026-10-27T19:43:15 respectively; these strings carry no timezone offset.

- **One substantive error disappeared:** the undriven U4 enable input, after R38 established a development OFF connection.
- **No new substantive ERC violation was introduced.**
- **All 60 final diagnoses persist from the initial report:** 59 have exactly matching parsed violation records; one existing supply-alias warning selected a different pre-existing label as its representative.
- The remaining 60 comprise **34 errors and 26 warnings**, not 60 independently demonstrated electrical faults. U3 CHIP_PU alone produces two separate reports.

Physical interpretation was checked against the [final native netlist](diagnostics/final-netlist.xml), the current [V1.2 schematic](../v1.2/open-semg-16-v1.2.kicad_sch), its cached symbol definitions and the [original review](../reviews_v1/full_review.md), [V1.1 report](../reviews_v1.1/updates_from_v1.md) and [V1.2 report](updates_from_v1.1.md). The original F01–F21 identifiers retain their meanings and severities. No new comprehensive audit or powered test was performed.

Input SHA-256 values:

- Initial ERC: `fefa240d16e97ccbb3a8a293a55f2b8227400c07dd5f56e8461357ff06eb61a4`
- Final ERC: `6490939e7eb49cb94f69a032d685d037580666108617a840b11b8e7ac8d54276`
- Current schematic: `7efd6a06e2ac45a553e7731665950c98c9a680dd36da6db584a826dc016e9494`

### Comparison method and numbering

For each parsed violation, compare type, severity, diagnosis text and every reported item's UUID, description and coordinates. Ignore JSON object-key order and the violation's position in the array; do not match solely by total or by diagnosis text. This produces 59 exact matches, two initial-only records and one final-only record. Examination of the alias records shows that one raw removal/addition pair represents the same continuing issue.

**Vnn** means the one-based position in final-erc.json's root-sheet violations array; **Inn** means the corresponding initial position. These are traceability indices, not replacement finding IDs. Sections 3 and 7 identify every final record individually. All records except V47 are exact parsed-record matches to the listed initial entry.

## 2. Exactly what changed

### Removed electrical error — I03

- ERC type/severity: pin_not_driven / error; diagnosis: “Input pin not driven by any Output pins.”
- Item: U4 pin 3, ON/~{OFF}; at (107.95, 271.78) mm.
- Pin UUID: `aba29000-5afc-44b8-8a0b-a932ea750275`.
- Initial /EN contained only U4.3 and U5.3. Final /EN contains those inputs plus R38.1; R38.2 is AGND. R38 has value 0 and is fitted in the schematic (dnp no).
- This removes **F05's floating-enable condition**. It deliberately holds both regulators OFF; it does not implement a working power-enable circuit, remove their parallel outputs, prevent USB backfeed or qualify a usable rail. F05 remains partial in the V1.2 report.

This is the only removed electrical diagnosis. U5.3 shared the same undriven net but was not a second separate initial ERC record.

### Changed representative — I45 becomes V47

The warning “Both +3.3V and AVDD are attached to the same items; +3.3V will be used in the netlist” persists.

| Item | Initial report | Final report |
|---|---|---|
| Global +3.3V | UUID 8b21c772-a7e2-49e8-be88-8f0bc106d537; (565.15,187.96) mm | Same UUID, position and description |
| Representative AVDD label | UUID 066ca9c8-7bd4-4f0b-92e4-56350bd7253c; (160.02,85.09) mm | UUID 3589528b-9c95-40c8-a912-f86516f6c24c; (201.93,116.84) mm |

Both AVDD labels still exist in the schematic; all four local AVDD labels are on the common +3.3V supply. The chosen representative and array ordering changed. This is **not a repaired warning followed by a new fault**. The AGND/GND alias warning is an exact match, I54 → V53.

Consequently the strict record delta is **2 removed / 1 added / 59 exact matches**, while the engineering delta is **1 resolved / 0 introduced / 60 continuing diagnoses**. The other 59 exact-match identities are fully listed in section 7.

## 3. Classification of all 60 remaining records

Each record receives one primary category. Conditional operation and missing evidence are stated separately; a valid static topology is not proof of valid firmware, supplies or safety.

| Code | Requested classification | Count |
|---|---|---:|
| CE | Confirmed electrical error requiring correction | 1 |
| UI | Unused pin or intentionally unconnected circuit element | 27 |
| SD | Schematic cleanup or documentation issue | 22 |
| VT | ERC false positive / valid circuit topology | 7 |
| AE | Requires additional evidence | 3 |
| **Total** | | **60** |

| ERC type | Errors | Warnings | Affected component/net groups | Primary categories |
|---|---|---|---|---|
| pin_not_connected | 28 | 0 | U3: 27 unused GPIO/header terminals plus CHIP_PU | 27 UI; 1 AE |
| power_pin_not_driven | 3 | 0 | AGND, +3.7V, +5V | 2 VT; 1 AE |
| pin_not_driven | 1 | 0 | U3.3 CHIP_PU | 1 AE |
| pin_to_pin | 2 | 4 | U4/U5 outputs; U1/U2 DOUT; four TEST/PACE ties | 1 CE; 5 VT |
| unconnected_wire_endpoint | 0 | 19 | 16 input-node stubs, two RLDOUT stubs, one CS_ADC2 tail | 19 SD |
| multiple_net_names | 0 | 2 | +3.3V/AVDD and AGND/GND | 2 SD |
| lib_symbol_mismatch | 0 | 1 | BT1 Device:Battery cache | 1 SD |
| **Total** | **34** | **26** | **60 individual reports** | **1 CE + 27 UI + 22 SD + 7 VT + 3 AE** |


### 3.1 Power-input source reports — three errors

| Final / initial | Affected item and actual net | Class | Finding references and interpretation |
|---|---|---|---|
| V01 / I01 | #PWR01.1, displayed GND; actual net AGND | VT | F02 repaired; F19 model documentation. BT1.2, ADC physical grounds, MCU grounds and regulator grounds already share one return. The marker does not demonstrate a floating physical ground. |
| V02 / I02 | #PWR068.1; +3.7V | VT | F15/F16/F19 qualification remains. Intended source BT1.1 is passive in the symbol; net also contains U4.1/U5.1, C53.1/C56.1 and TP5.1. ERC lacks a power-output declaration, not evidence that the battery wiring is open. |
| V13 / I14 | #PWR063.1; +5V, containing only U3.21 | AE | F17/F19. An unused DevKit 5V header can be legitimate with direct-3V3 supply, but actual board and permitted power modes remain unspecified. Do not invent a 5V source or connect this to the battery to clear ERC. |


KiCad explains why passive source connections and regulator ground pins produce these source-model reports. A later, truthful power-source declaration can resolve the first two without an architecture change; it would not qualify the battery or make the intentionally disabled +3.3V rail functional. Do not add a flag to +5V before defining its actual role. [KiCad 10.0: power pins and power flags](https://docs.kicad.org/10.0/en/eeschema/eeschema.html#_power_pins_and_power_flags).

### 3.2 Unconnected U3 terminals — 28 errors

All entries below are singleton carrier nets in the native netlist, named unconnected-(U3-function-PadN); the complete function/pin and UUID make each distinct. “Unused” means unused on this carrier. It does not mean the corresponding node lacks circuitry inside the complete DevKit. No additional connection is required merely because ERC calls it an error.

| Final / initial | U3 terminal and function | Class / disposition | Findings |
|---|---|---|---|
| V05 / I06 | U3.3 — CHIP_PU | AE: verify installed DevKit reset network; see section 3.3. | F19; F09 reset context |
| V07 / I08 | U3.8 — GPIO15/ADC2_CH4/32K_P | UI: unused GPIO/optional 32k-clock header. | F19; no demonstrated missing required carrier connection |
| V08 / I09 | U3.9 — GPIO16/ADC2_CH5/32K_N | UI: unused GPIO/optional 32k-clock header. | F19; no demonstrated missing required carrier connection |
| V09 / I10 | U3.36 — GPIO39/MTCK | UI: unused carrier JTAG-related header. | F19; no demonstrated missing required carrier connection |
| V10 / I11 | U3.37 — GPIO40/MTDO | UI: unused carrier JTAG-related header. | F19; no demonstrated missing required carrier connection |
| V11 / I12 | U3.38 — GPIO41/MTDI | UI: unused carrier JTAG-related header. | F19; no demonstrated missing required carrier connection |
| V12 / I13 | U3.39 — GPIO42/MTMS | UI: unused carrier JTAG-related header. | F19; no demonstrated missing required carrier connection |
| V14 / I15 | U3.43 — GPIO43/U0TXD | UI: unused carrier UART header; DevKit has onboard UART circuitry. | F19; no demonstrated missing required carrier connection |
| V15 / I16 | U3.42 — GPIO44/U0RXD | UI: unused carrier UART header; DevKit has onboard UART circuitry. | F19; no demonstrated missing required carrier connection |
| V16 / I17 | U3.26 — GPIO20/USB_D+ | UI: unused carrier USB header; DevKit has onboard USB wiring. | F19; no demonstrated missing required carrier connection |
| V17 / I18 | U3.25 — GPIO19/USB_D- | UI: unused carrier USB header; DevKit has onboard USB wiring. | F19; no demonstrated missing required carrier connection |
| V18 / I19 | U3.31 — GPIO0 | UI: unused carrier header; preserve DevKit boot/strap circuitry. | F19; no demonstrated missing required carrier connection |
| V19 / I20 | U3.41 — GPIO1/ADC1_CH0 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V20 / I21 | U3.40 — GPIO2/ADC1_CH1 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V21 / I22 | U3.13 — GPIO3/ADC1_CH2 | UI: unused carrier header; strap/eFuse behavior needs assembly/firmware awareness. | F19; no demonstrated missing required carrier connection |
| V22 / I23 | U3.4 — GPIO4/ADC1_CH3 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V23 / I24 | U3.5 — GPIO5/ADC1_CH4 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V24 / I25 | U3.10 — GPIO17/ADC2_CH6 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V25 / I26 | U3.11 — GPIO18/ADC2_CH7 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V26 / I27 | U3.27 — GPIO21 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V27 / I28 | U3.32 — GPIO35 | UI: do not route blindly; octal-memory module variants reserve this GPIO. | F19; no demonstrated missing required carrier connection |
| V28 / I29 | U3.33 — GPIO36 | UI: do not route blindly; octal-memory module variants reserve this GPIO. | F19; no demonstrated missing required carrier connection |
| V29 / I30 | U3.34 — GPIO37 | UI: do not route blindly; octal-memory module variants reserve this GPIO. | F19; no demonstrated missing required carrier connection |
| V30 / I31 | U3.35 — GPIO38 | UI: carrier-unused; GPIO38 drives RGB on the official v1.1 DevKit. | F19; no demonstrated missing required carrier connection |
| V31 / I32 | U3.30 — GPIO45 | UI: unused carrier header; preserve boot/strap conditions. | F19; no demonstrated missing required carrier connection |
| V32 / I33 | U3.14 — GPIO46 | UI: unused carrier header; preserve boot/strap conditions. | F19; no demonstrated missing required carrier connection |
| V33 / I34 | U3.28 — GPIO47 | UI: unused carrier GPIO header; retain existing wiring. | F19; no demonstrated missing required carrier connection |
| V34 / I35 | U3.29 — GPIO48 | UI: carrier-unused; GPIO48 drives RGB on the original DevKit. | F19; no demonstrated missing required carrier connection |

An intact, matching DevKit supplies USB/UART, reset and boot circuitry that the carrier symbol does not expand. The official guide also distinguishes module-memory reservations and RGB GPIO changes by board revision. Before later adding a per-pin NC annotation, confirm the header is intentionally unused and document any board-internal role. Never add arbitrary pull resistors or tie these pins together to reduce the error count. [Official DevKitC-1 v1.1 guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html).

### 3.3 Undriven U3 CHIP_PU — one additional error

| Final / initial | Type / affected net | Class | Evidence and action |
|---|---|---|---|
| V06 / I07 | pin_not_driven, U3.3 CHIP_PU; same unconnected-(U3-CHIP_PU-Pad3) singleton as V05 | AE | F19 and reset context F09. V05 and V06 concern one physical terminal, not two independently confirmed failures. |

The [official DevKit schematic, p.2](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) includes CHIP_PU reset bias R5 = 10 kΩ, C6 = 1 µF, buttons and automatic-programming circuitry. The fitted SKU/revision and any assembly modifications have not been established. Thus neither “bare ESP32 enable floats” nor “the installed reset network is verified” follows from this report. Confirm the actual assembly; if it matches the intact reference, both CHIP_PU entries become assembly-model/documentation false positives. Do not ground CHIP_PU, add a competing reset circuit or alter its pin type merely to clear these entries.

### 3.4 Pin-to-pin conflicts — two errors and four warnings

| Final / initial | Severity / affected pins and net | Class | Finding references and electrical interpretation |
|---|---|---|---|
| V03 / I04 | Error: U4.5 VOUT ↔ U5.5 OUT, +3.3V | CE | F04 confirmed: independent LDO outputs directly share a rail without an approved sharing/isolation architecture. R38's OFF connection does not remove the topology or isolate externally biased outputs. F05/F13/F16/F17 remain dependencies; actual contention/damage is unmeasured. |
| V04 / I05 | Error: U1.43 DOUT ↔ U2.43 DOUT, /MISO; also U3.19 | VT | Valid manufacturer-supported cascade topology with separate /CS_ADC1 and /CS_ADC2. F09/F18 must guarantee exclusive selection; F06 concerns timing. ERC does not model deselected high impedance. |
| V45 / I47 | Warning: U1.17 TESTP_PACE_OUT1 ↔ U4.5, +3.3V = actual U1 AVDD | VT | F03 repaired wiring; F18 mode restriction. TI permits the unused pin tied to AVDD. Keep the optional output function disabled. |
| V46 / I48 | Warning: U1.18 TESTP_PACE_OUT2 in library ↔ U4.5, +3.3V = actual U1 AVDD | VT | Same F03/F18 conditions. Manufacturer calls physical pin 18 TESTN_PACE_OUT2; spelling is a separate documentation discrepancy. |
| V58 / I59 | Warning: U2.17 TESTP_PACE_OUT1 ↔ U4.5, +3.3V = actual U2 AVDD | VT | Same unused-to-AVDD recommendation and F03/F18 restrictions. |
| V59 / I60 | Warning: U2.18 TESTP_PACE_OUT2 in library ↔ U4.5, +3.3V = actual U2 AVDD | VT | Same unused-to-AVDD recommendation and pin-18 naming distinction. |


The ADCs' DOUT drivers enter high impedance when their individual CS is high. This supports the common MISO connection; it does not prove reset/boot non-overlap. Arbitrarily splitting the bus, adding pullups or changing output pin types is unjustified. TI's unused-pin footnote also supports pins 17/18 tied to their own actual AVDD. Preserve those ties and verify the mode contract; enabling an output against the tie would be a different, firmware-dependent error. [ADS1298, pp.10,57,59–60](https://www.ti.com/lit/ds/symlink/ads1298.pdf).

### 3.5 Unconnected wire endpoints — 19 warnings

**Every row below is SD: schematic cleanup/documentation.** Sixteen are redundant 1.27 mm tails at already-connected positive input nodes; two are 1.27 mm tails at intentionally unused RLDOUT pins. They do not indicate 16 missing electrodes or missing ADC connections. Preserve the true connection or existing NC marker. The last row is different: part of its wire carries a real CS connection.

Coordinates below identify the ERC-reported wire position and the node to retain. The reported position is not always the free endpoint. Exact wire UUIDs appear in section 7.

| Final / initial | Reported coordinate → retained node (mm) | Affected path / actual net | Class / review link |
|---|---|---|---|
| V36 / I37 | (62.23, 36.83) → (63.50, 36.83) | E1 P: R1.2 / C1.1 / U1.16; `Net-(U1-IN1P)` | SD; F12 topology preservation; review §10.1 |
| V37 / I38 | (62.23, 57.15) → (63.50, 57.15) | E2 P: R3.2 / C3.1 / U1.14; `Net-(U1-IN2P)` | SD; F12 topology preservation |
| V38 / I39 | (62.23, 78.74) → (63.50, 78.74) | E3 P: R5.2 / C5.1 / U1.12; `Net-(U1-IN3P)` | SD; F12 topology preservation |
| V39 / I40 | (62.23, 99.06) → (63.50, 99.06) | E4 P: R7.2 / C11.1 / U1.10; `Net-(U1-IN4P)` | SD; F12 topology preservation |
| V40 / I41 | (62.23, 119.38) → (63.50, 119.38) | E5 P: R9.2 / C13.1 / U1.8; `Net-(U1-IN5P)` | SD; F12 topology preservation |
| V41 / I42 | (66.04, 144.78) → (67.31, 144.78) | E6 P: R11.2 / C15.1 / U1.6; `Net-(U1-IN6P)` | SD; F12 topology preservation |
| V42 / I43 | (66.04, 166.37) → (67.31, 166.37) | E7 P: R13.2 / C17.1 / U1.4; `Net-(U1-IN7P)` | SD; F12 topology preservation |
| V43 / I44 | (66.04, 187.96) → (67.31, 187.96) | E8 P: R15.2 / C21.1 / U1.2; `Net-(U1-IN8P)` | SD; F12 topology preservation |
| V44 / I46 | (194.31, 109.22) → (195.58, 109.22) | U1.63 RLDOUT; retain NC; `unconnected-(U1-RLDOUT-Pad63)` | SD; F07/F18; no bias function added |
| V48 / I49 | (289.56, 35.56) → (290.83, 35.56) | E9 P: R17.2 / C27.1 / U2.16; `Net-(U2-IN1P)` | SD; F12 topology preservation |
| V49 / I50 | (289.56, 55.88) → (290.83, 55.88) | E10 P: R19.2 / C29.1 / U2.14; `Net-(U2-IN2P)` | SD; F12 topology preservation |
| V50 / I51 | (289.56, 77.47) → (290.83, 77.47) | E11 P: R21.2 / C31.1 / U2.12; `Net-(U2-IN3P)` | SD; F12 topology preservation |
| V51 / I52 | (289.56, 97.79) → (290.83, 97.79) | E12 P: R23.2 / C37.1 / U2.10; `Net-(U2-IN4P)` | SD; F12 topology preservation |
| V52 / I53 | (289.56, 118.11) → (290.83, 118.11) | E13 P: R25.2 / C39.1 / U2.8; `Net-(U2-IN5P)` | SD; F12 topology preservation |
| V54 / I55 | (293.37, 143.51) → (294.64, 143.51) | E14 P: R27.2 / C41.1 / U2.6; `Net-(U2-IN6P)` | SD; F12 topology preservation |
| V55 / I56 | (293.37, 165.10) → (294.64, 165.10) | E15 P: R29.2 / C43.1 / U2.4; `Net-(U2-IN7P)` | SD; F12 topology preservation |
| V56 / I57 | (293.37, 186.69) → (294.64, 186.69) | E16 P: R31.2 / C47.1 / U2.2; `Net-(U2-IN8P)` | SD; F12 topology preservation |
| V57 / I58 | (421.64, 107.95) → (422.91, 107.95) | U2.63 RLDOUT; retain NC; `unconnected-(U2-RLDOUT-Pad63)` | SD; F07/F18; no bias function added |
| V60 / I61 | (562.61, 96.52) → (568.96, 96.52) | U3.20 GPIO14 → U2.39 CS; `/CS_ADC2` | SD; F09/F18; retain signal path and label |

For the 18 short tails, removal of the identified tiny wire object can preserve the separately connected resistor/capacitor/ADC node or the NC at the RLDOUT pin. This is candidate cleanup, not a repair to acquisition or body bias.

**V60 must not be fixed by deleting its whole wire.** Wire 34341901-2092-4668-89af-eb552c157d44 runs from (562.61,96.52) to (576.58,96.52). The CS_ADC2 label, UUID f775580c-f47c-4bc7-a9f8-15143a81985e, is at the interior point (568.96,96.52). A future cleanup can trim only the excess segment from x568.96 to x576.58, retaining the x562.61→568.96 signal path and the attached label. Deleting the entire 13.97 mm wire would break U3-to-U2 chip select.

These stubs were already described as inherited cleanup in the original review §10.1/§11.5 and both implementation reports. Removing them would not close F07, F09, F12 or F18. A subsequent cleanup must prove exact functional net partitions, all 16 P/N mappings and preserved RLD NC intent using a new native export; no such edit is made here.

### 3.6 Multiple net names — two warnings

| Final / initial | Affected labels / actual net | Class | Review link and disposition |
|---|---|---|---|
| V47 / I45 | +3.3V global and four local AVDD labels on one common supply | SD | F01/F03 wiring remains repaired; F04 remains unresolved. V47 selected a different representative only. Consolidate redundant aliases later without creating an implied independent analog rail or changing any supply/aux pin membership. |
| V53 / I54 | Global AGND and GND power symbols, represented by #PWR032, on the same AGND net | SD | F02 common return remains repaired. Normalize redundant names consistently; do not split grounds or remove the battery/MCU/ADC return bond. |


Labels can be misleading without being electrically disconnected. These two warnings are not surviving instances of the original F01/F02 supply faults. Supply/return partitioning is independently established by native pin memberships, not by the displayed label.

### 3.7 Cached-library mismatch — one warning

| Final / initial | Affected item | Class | Review link |
|---|---|---|---|
| V35 / I36 | BT1 Battery at (36.83,312.42); Device:Battery cached definition versus installed library | SD | F19 library/BOM documentation; F08/F15 actual cell qualification remains separate |

A read-only structural comparison of the embedded definition and installed /Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym finds the same geometry and passive pin 1 (+) / pin 2 (−) mapping. The installed definition adds three simulation fields absent from the embedded copy: `Sim.Device = "V"`, `Sim.Type = "DC"`, and `Sim.Pins = "1=+ 2=-"`. After ignoring those fields and the library-qualified root symbol name, the structures match.

This is not evidence of reversed battery polarity or a broken terminal. A later V1.2-local cache reconciliation can preserve all instance properties, pin numbers and native net partitions; do not edit the shared Device library or historical revisions. It does not specify a battery part, protection circuit, discharge cutoff or simulation source voltage.

## 4. What can safely be resolved without an architectural change

The recommendations below are future work. No NC flags, PWR_FLAGs, exclusions, pin-type changes or schematic edits were made in this analysis.

### Direct cleanup candidates

1. **The 19 verified wire-tail warnings:** remove only the redundant tails listed in section 3.5. V60 requires trimming its excess tail, not deleting its connection-bearing wire. Preserve all acquisition nodes and RLD NCs.
2. **The two alias warnings:** consistently consolidate redundant names on the currently identical nets; verify all old pin partitions and all rail/return assignments. Do not implement a power split through an incidental rename.
3. **The BT1 mismatch:** reconcile only the V1.2 embedded cache against the verified library metadata while preserving geometry, pin mapping, instance fields and connectivity.

These address **22 cleanup warnings** without changing the current circuit architecture. Their removal would not establish usable power, safe wearer connection or measured performance.

### Documentation/modeling candidates after intent is confirmed

- **27 UI header errors:** confirm and document that each external carrier terminal is unused, including DevKit-internal roles, then use truthful per-pin NC annotations if desired in a later authorized cleanup. This records existing intent; it does not qualify MCU reset configuration or disconnect internal DevKit circuits.
- **AGND and +3.7V source-model errors:** after reviewing the intended physical source and return, a truthful source declaration can represent the battery/return function ERC cannot infer from passive pins. Do not treat that declaration as battery qualification or add one to a disabled/undefined rail merely to obtain a pass.
- **The two CHIP_PU reports and +5V:** confirm the fitted assembly and power mode first. An intact reference DevKit can justify assembly-aware documentation/modeling; a bare module or modified board may require real circuitry instead.
- **DOUT and TEST/PACE conflicts:** retain the manufacturer-supported wiring and document its operating restrictions. Firmware/non-overlap evidence is needed for operation. Do not change pin electrical types, globally weaken conflict rules or disconnect valid nets solely to clear them.
- A local correction of the pin-18 TESTP/TESTN name can improve documentation without changing physical pin 18; it would not eliminate the underlying generic bidirectional-to-supply warning.

KiCad distinguishes truthful no-connection intent and source declarations from actual electrical behavior. These mechanisms should only represent verified design intent, not conceal unresolved conditions. [KiCad 10.0 schematic documentation](https://docs.kicad.org/10.0/en/eeschema/eeschema.html#_no_connection_flags).

### Not a safe cleanup-only correction

V03, the **F04 parallel-LDO error**, requires an explicit source/rail/isolation decision. Neither enabling both regulators, removing R38, adding a power flag nor changing a pin type resolves it. F05's development OFF state must not be mistaken for an operating power architecture. Defining a real bias/protection path or adding an arbitrary CS-default network also exceeds cleanup and requires the requirements discussed below.

## 5. Prioritized recommendations

| Priority | Action and evidence needed | Findings |
|---|---|---|
| 1 — before any power-up | Resolve the parallel sources and select a usable power/enable architecture. Define actual battery range/cutoff, DevKit identity and permitted USB/5V/3V3 modes; design reverse-current/source isolation and assess capacitance/current/thermal limits. Keep the development OFF strap fitted until redesign. | F04/F05/F13/F15/F16/F17/F19 |
| 1 — before acquisition claims | Establish supply/input sequencing and exclusive CS through reset/boot; implement and observe master-clock startup, slave initialization, reference setup and synchronized conversions. A valid shared-MISO topology is not evidence this happens. | F06/F09/F18 |
| 1 — before wearer connection | Define protected body bias and fault-current/ESD/external-interface requirements, model normal and fault paths, then verify with a simulator and appropriate safety review. No unverified RLD/protection values should be chosen to clear an issue. | F07/F08 |
| 2 — establish component/assembly facts | Confirm actual DevKit/reset/power circuits, battery and regulator silicon; complete component procurement and ratings. Resolve AE classifications using that evidence. | F14/F15/F16/F17/F19 |
| 3 — independent schematic cleanup | Carry out the 22 bounded cleanup candidates and truthful per-pin documentation after review. Require native netlist equivalence and unchanged functional constraints; retain meaningful ERC errors. | F19 and preservation constraints of F02/F07/F09/F12/F18 |
| 4 — performance/physical qualification | Bound contacts/offsets/gain/passband and lead-off policy; build/review PCB returns, RF, thermal behavior and probe access; measure after the power/safety gates. | F10/F11/F12/F14/F16/F18/F20/F21 |

The original three Critical wiring findings F01–F03 remain repaired in the native netlist. Their repaired status does not qualify the source that would energize those correctly connected pins. Original finding severities are not being re-ranked from the number of ERC markers.

## 6. Critical and high-impact electrical problems ERC cannot establish

This section separates subsystem blockers from the 60 reported violations. **F04 is detected by ERC and is therefore not an ERC blind spot.** The following absent guarantees remain even if all cosmetic and model warnings disappear. Original severities are retained; “unverified” does not mean a measured failure.

| Blocker outside current ERC's behavioral coverage | Finding / original severity | Confirmed fact versus missing evidence |
|---|---|---|
| No implemented operating battery-fed +3.3V state while R38 is fitted | F05 High; F04 High dependency | R38 deliberately holds both EN inputs low. ERC still sees regulator power-output pin types; it does not simulate enable state or measure voltage. This is documented containment, not a newly discovered accidental fault. |
| No deliberate DC body-bias path | F07 High | Both RLD paths remain intentionally NC and no passive bias contact/path exists. Those NCs do not generate a “missing body operating point” ERC error. Actual common-mode excursion is unmeasured. |
| Wearer protection, fault current and external-interface safety unestablished | F08 Unverified | Component ESD/current ratings and 2 kΩ series resistors do not establish product-level normal/single-fault safety. The current and required limits have not been demonstrated; no compliance failure magnitude is invented. |
| USB/5V can introduce another source and output-above-input exposure | F17 Medium; F04/F13 dependencies | DevKit internal regulation and U5's disabled output-discharge path are not expanded or behaviorally simulated by ERC. Actual reverse current/hot-plug waveform and fitted-board details remain unverified. OFF is not isolation. |
| CS boot states, sequencing and absent-supply signal injection | F09 High; F18 Medium | Separate CS nets and pulldowns do not guarantee arbitration, low inputs during supply ramps, safe MCU glitches or no back-powering. No complete startup waveform/firmware evidence exists. |
| A connected CLK net does not prove a running shared clock | F06 High; F18 Medium | U1 CLK_EN resets disabled; U2 relies on a valid external clock for initialization. ERC sees U1.37/U2.37/TP1 continuity but cannot prove firmware startup, frequency or all-16-channel sample alignment. |

Additional performance, source and physical requirements ERC also cannot close:

| Requirement | Findings | Remaining evidence |
|---|---|---|
| LDO stability, startup and reverse-current behavior | F13; F04/F17 | 242.6 µF nominal common output capacitance before DevKit is known. Effective C/ESR, LP silicon and actual stability/transients remain unknown; no oscillation is asserted. |
| Battery headroom/cutoff and RF-load transient/thermal margin | F15/F16 | Cell window, source impedance, duty, PCB copper/enclosure and rail/temperature measurements. |
| PGA offset/common-mode headroom, passband and contact-dependent CMRR | F10/F11/F12 | Contact/body models and measurements, chosen gain/rate/filter policy. Nominal matched RC fields are not achieved CMRR. |
| Internal reference, unused outputs/GPIOs, gain/rate/lead-off and data validity | F18 | Actual firmware configuration/readback, settling/timing and sample-validity behavior. Grounded GPIO outputs must never be driven high; optional hard-tied outputs must remain off. |
| Actual capacitor/resistor parts and physical implementation | F14/F19/F20/F21 | C25/C51's ≥10V field and C55's leakage requirement are procurement requirements, not qualified parts. Effective capacitance at VCAP3 bias, ratings, footprints, PCB/RF/return paths and physical probe access remain open. |

Historically, F01/F02 wrong supply assignments and F03's relative overvoltage exposure demonstrate why ERC counts are insufficient: pin-type rules do not fully evaluate supply span or analog absolute limits. Current connections repair those original mechanisms; do not list them as persisting faults. No new analog performance, electrical-safety or wearable-readiness conclusion follows from this analysis.

## 7. Complete identity ledger

This ledger covers all 60 final records exactly once. UUIDs are the JSON item identities (pin UUIDs for pin reports, wire UUIDs for wire reports, symbol/label UUIDs where reported), not newly assigned issue IDs. Coordinates and complete item descriptions remain in the linked source JSON. For two-item conflicts, both UUIDs are listed. All entries are exact initial matches except V47's representative change explained in section 2.

| Final / initial | ERC type / severity | Class | Reported item UUID(s) |
|---|---|---|---|
| V01 / I01 | power_pin_not_driven / error | VT | `b7896f6d-cdbb-4979-8766-b73a29a4a88c` |
| V02 / I02 | power_pin_not_driven / error | VT | `65299478-57c1-477c-9211-c345cd2d6218` |
| V03 / I04 | pin_to_pin / error | CE | `4c0e44dd-2a5a-49e7-8d26-4bcdeffa7f68`<br>`9c8398c4-090c-4e7a-8d13-dcc86bb5565a` |
| V04 / I05 | pin_to_pin / error | VT | `a804e879-7924-4735-86f4-5aa8ba00f675`<br>`38cbf10d-4065-4bb5-a23b-2fdeb250f324` |
| V05 / I06 | pin_not_connected / error | AE | `cfa969c5-8e37-47bf-a045-3c017c96281a` |
| V06 / I07 | pin_not_driven / error | AE | `cfa969c5-8e37-47bf-a045-3c017c96281a` |
| V07 / I08 | pin_not_connected / error | UI | `c7fe87fa-2f10-4e56-9051-aeceb5f4602b` |
| V08 / I09 | pin_not_connected / error | UI | `8bb9b256-c392-44af-bfa4-09054b34d0a7` |
| V09 / I10 | pin_not_connected / error | UI | `2128f0e8-66fd-46f4-ba85-acf025c5b7cf` |
| V10 / I11 | pin_not_connected / error | UI | `571dad94-66a7-4e67-a30e-274a75cd4444` |
| V11 / I12 | pin_not_connected / error | UI | `67b54cb9-47f7-429f-86bf-e2a4540d044f` |
| V12 / I13 | pin_not_connected / error | UI | `28b07b49-2e3b-4f16-9059-48baaabbe63d` |
| V13 / I14 | power_pin_not_driven / error | AE | `3fa1685c-0ed0-4d29-a1de-00eaa0c3700e` |
| V14 / I15 | pin_not_connected / error | UI | `8f0de143-24a2-4cf6-82f6-77b68d9dccf3` |
| V15 / I16 | pin_not_connected / error | UI | `6b5bb64b-0a3b-4969-bc23-3e5d90a5f588` |
| V16 / I17 | pin_not_connected / error | UI | `24b9956c-0093-480e-bf6e-3c202986e453` |
| V17 / I18 | pin_not_connected / error | UI | `0fb67ce2-47a8-4ea4-8e65-9aec3f990419` |
| V18 / I19 | pin_not_connected / error | UI | `6889afaf-5d7f-4314-a13c-b142ace68a25` |
| V19 / I20 | pin_not_connected / error | UI | `01c982f1-204d-4a47-ae93-ca21543eda82` |
| V20 / I21 | pin_not_connected / error | UI | `0605c299-2d2b-40ac-a74f-924d39c69476` |
| V21 / I22 | pin_not_connected / error | UI | `810351da-8113-4a08-bf3b-96eeeeea5f0e` |
| V22 / I23 | pin_not_connected / error | UI | `bc5f3d45-c62f-45b0-9e17-3cc02c3ce904` |
| V23 / I24 | pin_not_connected / error | UI | `e24ff256-1407-4452-8b62-3796e883c65d` |
| V24 / I25 | pin_not_connected / error | UI | `dafc3c56-e60a-4c8a-976d-8ddd6a369fe7` |
| V25 / I26 | pin_not_connected / error | UI | `31c584f3-6db0-446c-8ab6-d6b7279d63f3` |
| V26 / I27 | pin_not_connected / error | UI | `36304e0b-1d68-481f-94c6-02ea6862afd0` |
| V27 / I28 | pin_not_connected / error | UI | `d18b7919-c2ee-400f-acb0-078f68386a32` |
| V28 / I29 | pin_not_connected / error | UI | `b0c1911a-52aa-44fe-9881-4f8e7abadddf` |
| V29 / I30 | pin_not_connected / error | UI | `2efdaa0d-fb86-4275-b912-9c8071aec0d4` |
| V30 / I31 | pin_not_connected / error | UI | `29b85401-be1e-47de-9737-c20fda741df7` |
| V31 / I32 | pin_not_connected / error | UI | `797d7d25-675e-4474-9bf3-85f68873e5dc` |
| V32 / I33 | pin_not_connected / error | UI | `0868d39f-2c75-409e-9e48-0b160740f239` |
| V33 / I34 | pin_not_connected / error | UI | `edea7cb7-c3e8-4dc8-9bc8-14e6716c3785` |
| V34 / I35 | pin_not_connected / error | UI | `8f307098-1866-4a3e-926d-d4024adc4b70` |
| V35 / I36 | lib_symbol_mismatch / warning | SD | `149825b1-8c0c-479c-a2e9-5c608ac46157` |
| V36 / I37 | unconnected_wire_endpoint / warning | SD | `e8554e5f-764e-4ed9-b3b5-af17444eaea4` |
| V37 / I38 | unconnected_wire_endpoint / warning | SD | `a1d6f88d-0e8a-413e-a213-337d5f4dfb8c` |
| V38 / I39 | unconnected_wire_endpoint / warning | SD | `b9ec5222-9de5-4232-ac72-616ed32d16fa` |
| V39 / I40 | unconnected_wire_endpoint / warning | SD | `fed4f893-2155-4132-a14d-83d66da5026f` |
| V40 / I41 | unconnected_wire_endpoint / warning | SD | `d5e72200-7740-47f6-bcd1-166d3890ab1a` |
| V41 / I42 | unconnected_wire_endpoint / warning | SD | `13c6d5b3-2529-4363-adf9-c4bf92ed6b75` |
| V42 / I43 | unconnected_wire_endpoint / warning | SD | `7629d020-a15b-4a11-a0da-525dc621807c` |
| V43 / I44 | unconnected_wire_endpoint / warning | SD | `1944fad2-2fdc-4b3d-bc63-86c9cadeb58c` |
| V44 / I46 | unconnected_wire_endpoint / warning | SD | `921c1c3f-7201-4f7d-b96d-27f51fc32b80` |
| V45 / I47 | pin_to_pin / warning | VT | `b2a93068-aa80-4aec-ba64-11e021b26d31`<br>`4c0e44dd-2a5a-49e7-8d26-4bcdeffa7f68` |
| V46 / I48 | pin_to_pin / warning | VT | `dfe0ee43-f77c-4980-aeb6-83c6ee313096`<br>`4c0e44dd-2a5a-49e7-8d26-4bcdeffa7f68` |
| V47 / I45 | multiple_net_names / warning | SD | `8b21c772-a7e2-49e8-be88-8f0bc106d537`<br>`3589528b-9c95-40c8-a912-f86516f6c24c` |
| V48 / I49 | unconnected_wire_endpoint / warning | SD | `8928b8b2-a15b-4448-9ee8-2288aad4981d` |
| V49 / I50 | unconnected_wire_endpoint / warning | SD | `9bb1d07d-9b6b-4b89-b88f-7bd033c17f63` |
| V50 / I51 | unconnected_wire_endpoint / warning | SD | `d7e9643c-0720-4f66-9307-e79118aac293` |
| V51 / I52 | unconnected_wire_endpoint / warning | SD | `7ecfa58c-ad63-49c8-a47a-781baca645b6` |
| V52 / I53 | unconnected_wire_endpoint / warning | SD | `b6acd6a4-9497-49d0-8aa5-178ccdce006e` |
| V53 / I54 | multiple_net_names / warning | SD | `f8029c61-176b-4e4e-8cca-70ca9f9dbd18`<br>`3859c848-39c3-4f96-8e1a-3b5564814a99` |
| V54 / I55 | unconnected_wire_endpoint / warning | SD | `a88e4c81-bd1e-4997-b072-fb203d08f059` |
| V55 / I56 | unconnected_wire_endpoint / warning | SD | `b8457160-69b9-41fc-8320-2b8cf245d5cd` |
| V56 / I57 | unconnected_wire_endpoint / warning | SD | `917266e2-ea46-48be-8937-e23d14e2e70e` |
| V57 / I58 | unconnected_wire_endpoint / warning | SD | `b88d0700-d107-4800-a4a8-d3b91c190de7` |
| V58 / I59 | pin_to_pin / warning | VT | `d51af41d-e08a-4bb5-b997-5ec080c5b364`<br>`4c0e44dd-2a5a-49e7-8d26-4bcdeffa7f68` |
| V59 / I60 | pin_to_pin / warning | VT | `5174a6bf-688a-47ed-8972-27129b0243ef`<br>`4c0e44dd-2a5a-49e7-8d26-4bcdeffa7f68` |
| V60 / I61 | unconnected_wire_endpoint / warning | SD | `34341901-2092-4668-89af-eb552c157d44` |

## 8. Analysis integrity and limits

The 242 pre-existing files captured at analysis start, including the schematic/project, both requested ERC files, all earlier reports/diagnostics, historical revisions and manufacturer documents, are checked again when this report is saved. The only new file is reviews_v1.2/erc_analysis.md. No ERC was rerun, no existing diagnostic was overwritten, no schematic/model/library was updated, and no check was suppressed.

Both input reports already list these four ignored checks: single_global_label, four_way_junction, simulation_model_issue and footprint_filter. Their configuration is unchanged; requesting all included severities does not enable an ignored check. There are no newly introduced exclusions in this analysis.

The classifications concern the exact reported static topology and available assembly evidence. They do not demonstrate powered operation or safe use on a person. The device remains unsuitable for initial power-up and human-worn testing while the identified power, sequencing and safety blockers remain unresolved.

