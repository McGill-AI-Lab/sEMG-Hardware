# Open-sEMG-16 V1.2 — ERC corrections and verification

27 October 2026. Follow-up implementation using [erc_analysis.md](erc_analysis.md), the [original F01–F21 review](../reviews_v1/full_review.md), the [V1.1 implementation report](../reviews_v1.1/updates_from_v1.md) and the [earlier V1.2 implementation record](updates_from_v1.1.md). Those documents and their diagnostic snapshots remain unchanged. This report describes the current active schematic after this task.

## A. Outcome

**49 of the 50 requested targets are resolved:** the confirmed F04 parallel-output error, 26 of the 27 unused-pin reports, and all 22 cleanup warnings. **GPIO3/U3.13 is deliberately not marked No Connect**: the user confirmed its STRAP_JTAG_SEL eFuse state is unknown, so the required per-pin verification cannot justify an NC yet.

The active [V1.2 schematic](../v1.2/open-semg-16-v1.2.kicad_sch) now has:

- U4's output and C54 on an isolated, two-terminal LP2985_OUT_DISABLED net. U4 no longer directly shares the main output with U5. Both regulators remain OFF through the existing fitted R38.
- Twenty-six individually verified No Connect markers on unused external U3 carrier terminals.
- Eighteen redundant wire objects removed; only the excess CS_ADC2 wire tail trimmed.
- Eight functional AVDD/DVDD label attachments consolidated to global +3.3V; 43 existing ground-symbol values consolidated to AGND.
- The embedded Battery cache reconciled with the installed library's three missing simulation fields, without changing its physical pins or BT1 instance.
- Current-state annotations and one compact supply-label presentation correction.

ERC changes from **34 errors / 26 warnings (60)** to **7 errors / 4 warnings (11)**. No new electrical ERC condition is introduced. The seven valid-topology/source-model conditions and all three original evidence-dependent conditions remain. GPIO3 supplies the additional retained report. The four TEST/PACE warnings necessarily reference U5's output instead of U4's after F04's real output disconnection; their auxiliary-to-actual-AVDD connections and mode restrictions are preserved.

Final validation passes **2,050 static checks**. Every original non-power pin assignment is unchanged except U4.5 and C54.1, the two deliberately isolated terminals. All 16 acquisition P/N mappings, reference/VCAP networks, control/clock/SPI assignments and test nodes remain intact.

**This is not power-up or wearer release.** R38 still disables both regulators; a qualified operating supply, F13 capacitance/ESR and startup qualification, USB/reverse-current handling, firmware, body bias and protection remain outstanding.

## B. Baseline, scope and editing method

Read-only MCP queries confirmed the active project open-semg-16-v1.2.kicad_pro, matching schematic, build profile and write mode. The exposed plan tools support label insertion, but not the required symbol removal, No Connect placement, wire trimming, global-label replacement or cache reconciliation. The earlier plan-creation rejection under approval_policy=never remains documented in the prior implementation record; it was not repeatedly retried.

The user-authorized controlled fallback uses [implement.py](diagnostics/erc_corrections/implement.py): explicit source-span patches, strict S-expression parsing, unique UUID/reference checks, native candidate netlist validation and atomic replacement of only the active V1.2 schematic. Every phase has a before-copy, candidate and operation log. No shared library, historical revision, ERC pin type, severity, exclusion or power flag was changed.

Before design edits, [recovery copies](diagnostics/erc_corrections/baseline/open-semg-16-v1.2.kicad_sch) and [243 pre-existing file hashes](diagnostics/erc_corrections/pre-edit-hashes.json) were saved. Fresh [initial ERC](diagnostics/erc_corrections/initial-erc.json) and [netlist](diagnostics/erc_corrections/initial-netlist.xml) reproduced 60 reports and the analyzed connectivity. The [explicit plan](diagnostics/erc_corrections/modification-plan.json) includes each pin's source, decision and coordinates.

The root final-erc.json/final-netlist.xml referenced by the earlier analysis remain historical snapshots. New final evidence is under **diagnostics/erc_corrections/** so the old report's hashes and individual V01–V60 references remain reproducible.

## C. F04 — remove the actual parallel-output connection

### Previous and corrected connectivity

| Connection | Before | After |
|---|---|---|
| U4.5 VOUT / C54.1 | Both on main +3.3V with U5.5 | Only these two terminals on /LP2985_OUT_DISABLED |
| U5.5 / acquisition and MCU supply loads | Main +3.3V | Main +3.3V, with only U4.5/C54.1 removed |
| U4.3 / U5.3 EN | Shared EN, held low by fitted R38 = 0 Ω to AGND | Unchanged |
| C54 | 2.2 µF from U4 output to AGND | Same part/value and return; retained on isolated U4 output |
| U4 input/C53/BP/C55/ground | Existing connections | Unchanged |

The old branch wire b45f1363-5760-4117-8a39-e214e470fb27 connects U4.5 at (128.27,269.24) to C54.1 at (147.32,269.24). Its connection to the common supply was power symbol **#PWR069**, UUID 899e2864-2071-420a-97ee-909270af09ae. That global supply symbol was replaced by an explicit local LP2985_OUT_DISABLED label at the same point. The wire and capacitor remain.

This changes a real electrical connection: a same-named power symbol joins a global rail, while the unique local label does not. The native netlist proves the new two-member partition. It is not an ERC pin-type change or a cosmetic rename concealing outputs that remain joined.

### Reasoning and consequences

The original review identifies independent LDO loops driving one rail without sharing/isolation as F04. Isolating the unused, disabled U4 branch removes that diagnosed mechanism while retaining its local output capacitor. It does not assume an approved battery/USB operating architecture or energize either regulator.

Main-rail nominal capacitance becomes **240.4 µF** rather than 242.6 µF; isolated U4 retains **2.2 µF**. Actual effective capacitance, ESR and LP silicon remain unqualified. The LP2985 legacy output-capacitance/ESR requirements must be met before enabling it; its capacitor has not been discarded. U5's recommended output-capacitance range still requires F13 work, so no stability or transient signoff follows. See [LP2985 §7.1.2.2, p.21](https://www.ti.com/lit/ds/symlink/lp2985.pdf) and [TLV755P recommended conditions](https://www.ti.com/lit/ds/symlink/tlv755p.pdf).

F04 is **fixed for direct U4/U5 output sharing**. F05's functional-enable/source qualification and F13/F15/F16/F17 remain open. The DevKit's internal source/backfeed possibilities are not removed by parking U4. Keep R38 fitted until the operating power solution is qualified.

Source changes and annotation updates are enumerated in [power-edit-log.json](diagnostics/erc_corrections/power-edit-log.json). [Independent power review](diagnostics/erc_corrections/independent-power-review.md) confirms the exact partition and preserved conditions.

## D. Per-pin No Connect verification — 26 added, one deferred

### Evidence and circuit requirements

U3's identity is the complete **44-pad ESP32-S3-DevKitC assembly**, not a bare WROOM module. The current acquisition interface uses GPIO6–14. None of the 26 approved header terminals participates in an acquisition, control, supply, return or test-point net. The complete U3 symbol instance remains byte-identical; the markers are separate schematic objects placed on its existing terminal coordinates.

The annotations declare **no external connection from this carrier**. They do not remove internal DevKit USB/UART/reset/boot/RGB or module memory circuitry. Replacing U3 with a bare module would require a different design review.

Source references:

- [D1: ESP32-S3-WROOM-1/-1U v1.8](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf): pin functions Table 3-1 pp.11–12; boot/strap Tables 4-1/4-3/4-4/4-5 and §4.4 pp.13–16.
- [D2: DevKitC-1 v1.1 guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html): J1/J3 header tables, module variants and hardware revision differences.
- [D3: official DevKit schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf): p.2 onboard USB/UART/boot/reset/RGB circuitry.
- [D4: GPIO design checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html#gpio): GPIO and optional RTC-clock requirements; unused high-impedance input management.

### Individual decisions

| U3 pin / function | Coordinate mm | Decision | Datasheet and circuit verification |
|---|---|---|---|
| 8 — GPIO15/ADC2_CH4/32K_P | 511.81, 50.80 | NC added | Optional 32 kHz RTC crystal terminal; the carrier/ADC timebase requires no RTC crystal. [D1, D2, D4] |
| 9 — GPIO16/ADC2_CH5/32K_N | 511.81, 53.34 | NC added | Optional 32 kHz RTC crystal terminal; no carrier RTC function is allocated. [D1, D2, D4] |
| 36 — GPIO39/MTCK | 511.81, 60.96 | NC added | Optional external JTAG header unused; internal JTAG configuration remains unchanged. [D1, D2] |
| 37 — GPIO40/MTDO | 511.81, 63.50 | NC added | Optional external JTAG header unused; internal JTAG configuration remains unchanged. [D1, D2] |
| 38 — GPIO41/MTDI | 511.81, 66.04 | NC added | Optional external JTAG header unused; internal JTAG configuration remains unchanged. [D1, D2] |
| 39 — GPIO42/MTMS | 511.81, 68.58 | NC added | Optional external JTAG header unused; internal JTAG configuration remains unchanged. [D1, D2] |
| 43 — GPIO43/U0TXD | 562.61, 43.18 | NC added | UART TX already connects to the DevKit USB-UART bridge; this external header branch is unused. [D2, D3] |
| 42 — GPIO44/U0RXD | 562.61, 45.72 | NC added | UART RX already connects to the DevKit USB-UART bridge; do not add competing bias or disable its onboard role. [D2, D3] |
| 26 — GPIO20/USB_D+ | 562.61, 50.80 | NC added | Onboard USB D+ wiring remains internal to the DevKit; external carrier branch unused. [D1, D2, D3] |
| 25 — GPIO19/USB_D- | 562.61, 53.34 | NC added | Onboard USB D− wiring remains internal; this NC does not resolve USB power isolation. [D1, D2, D3] |
| 31 — GPIO0 | 562.61, 60.96 | NC added | GPIO0 internal pull-up and DevKit boot/programming circuitry remain; no carrier boot-control connection is required. [D1, D3] |
| 41 — GPIO1/ADC1_CH0 | 562.61, 63.50 | NC added | Optional GPIO1; no carrier signal or required peripheral is allocated. [D1, D2, D4] |
| 40 — GPIO2/ADC1_CH1 | 562.61, 66.04 | NC added | Optional GPIO2; no carrier signal or required peripheral is allocated. [D1, D2, D4] |
| 13 — GPIO3/ADC1_CH2 | 562.61, 68.58 | NO NC — deferred | DEFERRED: user reports JTAG strap eFuse state unknown. D1 §4.4/Table 4-5 requires a defined GPIO3 level in strap-selected modes; default-compatible modes ignore it. [D1, D2] |
| 4 — GPIO4/ADC1_CH3 | 562.61, 71.12 | NC added | Optional GPIO4; no carrier signal or required peripheral is allocated. [D1, D2, D4] |
| 5 — GPIO5/ADC1_CH4 | 562.61, 73.66 | NC added | Optional GPIO5; no carrier signal or required peripheral is allocated. [D1, D2, D4] |
| 10 — GPIO17/ADC2_CH6 | 562.61, 99.06 | NC added | Optional GPIO17/UART1; neither function is used by this carrier. [D1, D2, D4] |
| 11 — GPIO18/ADC2_CH7 | 562.61, 101.60 | NC added | Optional GPIO18/UART1; neither function is used by this carrier. [D1, D2, D4] |
| 27 — GPIO21 | 562.61, 104.14 | NC added | Optional GPIO21; no carrier function allocated. [D1, D2, D4] |
| 32 — GPIO35 | 562.61, 106.68 | NC added | GPIO35 may be reserved for internal octal memory. Leaving the external carrier terminal unrouted preserves that role. [D1, D2] |
| 33 — GPIO36 | 562.61, 109.22 | NC added | GPIO36 may be reserved for internal octal memory; no carrier connection is appropriate. [D1, D2] |
| 34 — GPIO37 | 562.61, 111.76 | NC added | GPIO37 may be reserved for internal octal memory; no carrier connection is appropriate. [D1, D2] |
| 35 — GPIO38 | 562.61, 114.30 | NC added | GPIO38 drives onboard RGB on DevKit v1.1; the external carrier terminal is unused. [D2, D3] |
| 30 — GPIO45 | 562.61, 116.84 | NC added | GPIO45's internal pulldown and module memory-voltage/eFuse policy remain. The carrier adds no forced strap level. [D1, D2] |
| 14 — GPIO46 | 562.61, 119.38 | NC added | GPIO46's internal pulldown/boot-ROM strap role remains with DevKit GPIO0 circuitry. No carrier connection is required. [D1, D2, D3] |
| 28 — GPIO47 | 562.61, 121.92 | NC added | Optional GPIO47; unrouted, including variants with the documented 1.8 V domain caveat. [D1, D2, D4] |
| 29 — GPIO48 | 562.61, 124.46 | NC added | GPIO48 drives RGB on the initial DevKit and is otherwise carrier-unused; preserve the voltage-domain/board role. [D1, D2, D3] |

The [unused-pin operation log](diagnostics/erc_corrections/unused-edit-log.json) records all 26 new marker UUIDs, pin UUIDs, positions, evidence and meanings individually. The [independent digital review](diagnostics/erc_corrections/independent-digital-review.md) includes the same per-pin matrix and pin-to-marker ledger.

**GPIO3:** U3.13 at (562.61,68.58), pin UUID 810351da-8113-4a08-bf3b-96eeeeea5f0e, remains unflagged. D1 §4.4/Table 4-5 permits it to be ignored under documented default-compatible JTAG modes but requires a defined external level when it selects JTAG. The user answered **“Unknown / needs checking”** for STRAP_JTAG_SEL. No factory-default assumption, arbitrary strap resistor or eFuse change was made. Obtain the applicable provisioning/eFuse configuration before deciding its disposition.

D4 retains a firmware obligation to manage genuinely unused high-impedance GPIOs appropriately. Do not blanket-reconfigure all marked terminals: USB, UART, memory, straps and onboard RGB retain their respective roles. The NC annotations do not implement that firmware policy or qualify actual boot behavior.

The original eight RLD/WCT NC markers remain unchanged. No NC was added to CHIP_PU or the +5V terminal; their original evidence-dependent findings remain.

## E. The 22 cleanup diagnoses

### E1. Nineteen dangling-wire warnings

- Removed exactly the **18 redundant 1.27 mm wire objects** identified by UUID in the original analysis. Sixteen were tails at already-connected positive acquisition nodes; two were tails at U1/U2 RLDOUT pins whose NC markers remain.
- Trimmed only the second endpoint of CS_ADC2 wire 34341901-2092-4668-89af-eb552c157d44: **(576.58,96.52) → (568.96,96.52)**.
- Retained its first endpoint (562.61,96.52) and the attached CS_ADC2 label f775580c-f47c-4bc7-a9f8-15143a81985e at (568.96,96.52). U3.20 still reaches U2.39.

The complete removed UUID/endpoints list is in [cleanup-edit-log.json](diagnostics/erc_corrections/cleanup-edit-log.json), cross-referenced to [analysis §3.5](erc_analysis.md#35-unconnected-wire-endpoints--19-warnings). No electrode, capacitor, ADC connection or body-bias NC was replaced by a cosmetic marker. Exact original net memberships outside the declared F04 split are preserved.

### E2. Shared-supply aliases

The four AVDD labels carried functional links and could not simply be deleted. They were replaced by global +3.3V labels at their same coordinates and UUIDs. Native ERC then exposed **DVDD as another pre-existing name on that same rail**, previously masked by the AVDD representative. Its four functional label anchors were likewise retained as global +3.3V.

| Original local name | Label UUID | Preserved attachment mm |
|---|---|---|
| AVDD | `066ca9c8-7bd4-4f0b-92e4-56350bd7253c` | 160.02, 85.09 |
| AVDD | `3589528b-9c95-40c8-a912-f86516f6c24c` | 201.93, 116.84 |
| AVDD | `792ff479-7cd1-49c0-b4af-14b86c12e8f8` | 387.35, 83.82 |
| AVDD | `bd298a1f-5ec1-4f2d-a055-09b58728a7c2` | 429.26, 115.57 |
| DVDD | `3be50cba-7e40-47bb-8d96-339bceed5caa` | 193.04, 85.09 |
| DVDD | `75fc8b9d-1b77-49f1-bb82-13b6eff87138` | 209.55, 160.02 |
| DVDD | `96726343-f5a2-426c-a935-6769c922104b` | 420.37, 83.82 |
| DVDD | `a495d871-c532-473d-aa7f-0b108779b50c` | 539.75, 38.1 |

These global labels preserve both supply buses, unused analog ties, the master CLKSEL strap and the DevKit supply connection. Converting them merely to local +3.3V would create a conflicting local/global scope; global replacements address the naming problem directly. No analog/digital rail split or new supply source is implied.

Visual inspection found that the new CLKSEL supply flag crowded START text. Label 75fc8b9d-1b77-49f1-bb82-13b6eff87138 was compacted from 1.27 to 1.0 mm font and rotated from 180° to 0°, keeping its UUID, global +3.3V name and (209.55,160.02) anchor. This presentation-only correction is recorded in [label-presentation-edit-log.json](diagnostics/erc_corrections/label-presentation-edit-log.json).

### E3. Ground alias

Exactly **43 power:GND instances** had Value GND on the already-bonded AGND return. Only those instance Value fields changed to AGND. References, UUIDs, positions, wires, cached pin definitions and power-input types remain unchanged. The original already-AGND instances were retained.

Affected references:

`#PWR032`, `#PWR046`, `#PWR078`, `#PWR052`, `#PWR049`, `#PWR056`, `#PWR043`, `#PWR017`, `#PWR050`, `#PWR073`, `#PWR035`, `#PWR027`, `#PWR058`, `#PWR010`, `#PWR02`, `#PWR067`, `#PWR05`, `#PWR071`, `#PWR041`, `#PWR011`, `#PWR048`, `#PWR072`, `#PWR033`, `#PWR077`, `#PWR034`, `#PWR03`, `#PWR01`, `#PWR025`, `#PWR018`, `#PWR036`, `#PWR04`, `#PWR019`, `#PWR044`, `#PWR070`, `#PWR042`, `#PWR057`, `#PWR013`, `#PWR080`, `#PWR026`, `#PWR021`, `#PWR015`, `#PWR079`, `#PWR012`.

This consolidates actual names on the existing common return; it neither splits grounds nor adds a PWR_FLAG. The AGND source-model report remains, as requested.

### E4. Battery library/cache mismatch

Added only these missing properties to the embedded **Device:Battery** definition:

- Sim.Device = “V”
- Sim.Type = “DC”
- Sim.Pins = `1=+ 2=-`

The nodes were copied from the installed library in its property order. The cache now matches the installed definition structurally after normalizing its qualified root name. Geometry and passive pin 1 (+) / pin 2 (−) are unchanged; the complete BT1 instance and native connectivity are unchanged. No cell, protection, source voltage or battery qualification was invented. The shared installed Device library was not edited.

### E5. Caught preparation and intermediate checks

A strict cache-order assertion stopped the first preparation before any design write because the three Sim fields had been staged after ki_keywords rather than before it. The insertion order was corrected; [preparation-check-log.json](diagnostics/erc_corrections/preparation-check-log.json) records that the active file still matched the validated preceding stage.

The first native cleanup ERC retained a +3.3V/DVDD alias warning. Its [ERC](diagnostics/erc_corrections/cleanup-first-erc.json), [netlist](diagnostics/erc_corrections/cleanup-first-netlist.xml) and [failed validation](diagnostics/erc_corrections/cleanup-first-validation.json) are retained. The subsequent four DVDD replacements resolve that actual remaining alias. No severity, exclusion or rule was changed to make the check pass.

Every affected object is listed in the per-phase edit logs and the [explicit modification plan](diagnostics/erc_corrections/modification-plan.json). [Independent cleanup review](diagnostics/erc_corrections/independent-cleanup-review.md) confirms all 22 cleanup diagnoses are resolved without a cleanup connectivity regression.

## F. Validation and individual ERC comparison

### Native KiCad results

| Stage | Errors | Warnings | Total | Verification |
|---|---:|---:|---:|---|
| Initial | 34 | 26 | 60 | Reproduces analyzed state |
| After F04 output isolation | 33 | 26 | 59 | 1,620 assertions pass |
| After 26 verified NC markers | 7 | 26 | 33 | 1,620 assertions pass |
| First cleanup, before remaining DVDD alias | 7 | 5 | 12 | Remaining alias correctly rejected |
| Final, including presentation check | 7 | 4 | 11 | **2,050 assertions pass** |

Final [ERC](diagnostics/erc_corrections/final-erc.json), [netlist](diagnostics/erc_corrections/final-netlist.xml), [connectivity map](diagnostics/erc_corrections/final-connectivity.json), [validation](diagnostics/erc_corrections/final-validation.json), [PDF](diagnostics/erc_corrections/final-schematic.pdf) and native SVG are retained. CLI commands/stdout/stderr are recorded by stage. The existing fontconfig warning did not prevent native exports.

### Exactly which analyzed entries were resolved

| Original analysis IDs | Result |
|---|---|
| V03 | F04 actual direct-output connection removed |
| V07–V12, V14–V20, V22–V34 | 26 verified carrier NC annotations; reports disappear |
| V35 | Battery cache metadata mismatch corrected |
| V36–V44, V48–V52, V54–V57, V60 | 19 redundant wire-tail conditions corrected |
| V47, V53 | Supply/ground naming and scope corrected, including the masked DVDD name |
| V21 | GPIO3 retained: eFuse evidence unavailable |
| V01/V02/V04/V45/V46/V58/V59 | Seven valid-topology/source-model conditions retained |
| V05/V06/V13 | Three original evidence-dependent conditions retained |

The [complete 60-entry comparison](diagnostics/erc_corrections/erc-comparison.json) maps each original analysis ID to its final record or specific resolution. It records **49 resolved, zero introduced electrical conditions and 11 remaining**. Seven remaining parsed records match the historical report exactly. Four TEST/PACE records select a different supply-output partner as a necessary consequence of disconnecting U4, rather than representing a new electrical problem.

### Remaining records — all 11

| Final index | Original analysis ID / class | ERC type / severity | Affected items | Current interpretation |
|---|---|---|---|---|
| 1 | V01 / VT | power_pin_not_driven / error | #PWR01 Pin 1 [Power input] | Source/return model limitation; no flag added |
| 2 | V02 / VT | power_pin_not_driven / error | #PWR068 Pin 1 [Power input] | Source/return model limitation; no flag added |
| 3 | V04 / VT | pin_to_pin / error | U1 Pin 43 [DOUT, Output]<br>U2 Pin 43 [DOUT, Output] | Supported shared DOUT with exclusive CS and valid supplies |
| 4 | V05 / AE | pin_not_connected / error | U3 Pin 3 [CHIP_PU, Input] | Original evidence-dependent finding preserved |
| 5 | V06 / AE | pin_not_driven / error | U3 Pin 3 [CHIP_PU, Input] | Original evidence-dependent finding preserved |
| 6 | V13 / AE | power_pin_not_driven / error | #PWR063 Pin 1 [Power input] | Original evidence-dependent finding preserved |
| 7 | V21 / UI → deferred | pin_not_connected / error | U3 Pin 13 [GPIO3/ADC1_CH2, Bidirectional] | GPIO3 requires eFuse/provisioning evidence |
| 8 | V45 / VT | pin_to_pin / warning | U1 Pin 17 [TESTP_PACE_OUT1, Bidirectional]<br>U5 Pin 5 [OUT, Power output] | Valid unused-to-actual-AVDD tie; optional output modes must stay disabled. Representative now U5.5. |
| 9 | V46 / VT | pin_to_pin / warning | U1 Pin 18 [TESTP_PACE_OUT2, Bidirectional]<br>U5 Pin 5 [OUT, Power output] | Valid unused-to-actual-AVDD tie; optional output modes must stay disabled. Representative now U5.5. |
| 10 | V58 / VT | pin_to_pin / warning | U2 Pin 17 [TESTP_PACE_OUT1, Bidirectional]<br>U5 Pin 5 [OUT, Power output] | Valid unused-to-actual-AVDD tie; optional output modes must stay disabled. Representative now U5.5. |
| 11 | V59 / VT | pin_to_pin / warning | U2 Pin 18 [TESTP_PACE_OUT2, Bidirectional]<br>U5 Pin 5 [OUT, Power output] | Valid unused-to-actual-AVDD tie; optional output modes must stay disabled. Representative now U5.5. |

### Protected conditions and why four representatives changed

No wiring, NC or pin-type change was made to shared DOUT, the four TEST/PACE ties, the battery/ground source models, CHIP_PU or +5V. ADC auxiliary pins remain on the same net as their actual AVDD. Removing U4 from that net necessarily makes **U5.5** the reported supply-output partner of the four auxiliary warnings. This is the explicit justification for that report-item change; retaining U4 as their partner would mean the parallel connection had not actually been removed.

### Netlist and source preservation

- **133 non-power components retained**, with all original values, footprints and library identities.
- **133 nets**, versus 132 initially: one isolated U4/C54 output net added.
- Only U4.5 and C54.1 change net names. Every other pin assignment and every other net partition is exact.
- All 32 acquisition input memberships and all 16 electrode P/N/resistor/ADC mappings remain unchanged.
- Both reference networks, all VCAP values/returns, physical supply/ground repairs F01–F03, CLK/CLKSEL, DRDY, SPI/CS/control/pulldown connections and TP1–TP16 are preserved.
- All eight pre-existing NC markers remain; exactly 26 approved markers were added. GPIO3, CHIP_PU and +5V have no new NC.
- Every original non-power symbol instance is byte-identical. Only the Battery cache gains the three documented simulation properties; all other cached definitions remain byte-identical.
- Project ERC configuration, severities, pin types, ignored checks and exclusions remain unchanged. No PWR_FLAG was added.

Independent [power](diagnostics/erc_corrections/independent-power-review.md), [digital](diagnostics/erc_corrections/independent-digital-review.md) and [cleanup](diagnostics/erc_corrections/independent-cleanup-review.md) reviews checked the final source/native data. The digital reviewer additionally records 132 independent checks. The final single-object label-presentation delta was separately reviewed.

Rendered [power](diagnostics/erc_corrections/power-view.png), [MCU NC](diagnostics/erc_corrections/mcu-nc-view.png) and [supply-label](diagnostics/erc_corrections/supply-alias-view.png) crops were inspected for connection intent, NC placement and readability. These are static presentation checks, not physical or electrical qualification.

Final schematic SHA-256: `202b2b320076c5e802f55e6ed566ae640cb948c6544777b9d51b11222e371208`.

## G. Remaining work and exact limits

**GPIO3/U3.13:** establish the relevant JTAG eFuse/provisioning configuration. If GPIO3 is ignored by the intended mode, its carrier NC can be considered with that evidence; if it selects JTAG, design the required defined level rather than adding an NC. No assumption was made here.

**Power:** F04's original direct sharing mechanism is removed, but both regulators remain deliberately OFF. Functional EN/source selection, the battery window/cutoff, the nominal 240.4 µF bank's effective capacitance/ESR, U5 RF current/thermal behavior, LP silicon/C54 suitability and DevKit USB/backfeed/reverse-current states remain F05/F13/F15/F16/F17/F19 work.

**Acquisition and safety:** F06/F09/F18 startup/CS/clock/reference/firmware behavior, F07/F08 protected body bias and fault-current/isolation analysis, F10/F11/F12 signal/gain/passband/contact evidence, and F14/F19/F20/F21 parts/PCB/probe qualification are not established by this cleanup.

No PCB/DRC, firmware execution, powered measurement, circuit/body simulator test or wearer test occurred. There is no initial-power-up or human-worn-readiness claim.

## H. Files and historical integrity

Only the pre-existing **open-semg-16-v1.2.kicad_sch** design file was modified. V1.2 project/local libraries/settings and all V1/V1.1 designs, prior review documents, previous diagnostics and manufacturer documents remain unchanged. The [final integrity result](diagnostics/erc_corrections/final-file-integrity.json) checks the 243-file starting record and lists the sole changed existing file.

All new diagnostic artifacts are under diagnostics/erc_corrections/; this report is erc_corrections.md. The [exact retained-file manifest](diagnostics/erc_corrections/created-file-manifest.txt) enumerates every created file. Before-copies and intermediate candidates/results are recovery/history artifacts; the active schematic and final-* evidence are the current delivered state. The temporary rendering binary was removed after use.



### Exact retained new file list

- [diagnostics/erc_corrections/baseline/open-semg-16-v1.2.kicad_pro](diagnostics/erc_corrections/baseline/open-semg-16-v1.2.kicad_pro)
- [diagnostics/erc_corrections/baseline/open-semg-16-v1.2.kicad_sch](diagnostics/erc_corrections/baseline/open-semg-16-v1.2.kicad_sch)
- [diagnostics/erc_corrections/before-cleanup.kicad_sch](diagnostics/erc_corrections/before-cleanup.kicad_sch)
- [diagnostics/erc_corrections/before-label-presentation.kicad_sch](diagnostics/erc_corrections/before-label-presentation.kicad_sch)
- [diagnostics/erc_corrections/before-power.kicad_sch](diagnostics/erc_corrections/before-power.kicad_sch)
- [diagnostics/erc_corrections/before-supply-alias-completion.kicad_sch](diagnostics/erc_corrections/before-supply-alias-completion.kicad_sch)
- [diagnostics/erc_corrections/before-unused.kicad_sch](diagnostics/erc_corrections/before-unused.kicad_sch)
- [diagnostics/erc_corrections/cleanup-candidate-netlist.xml](diagnostics/erc_corrections/cleanup-candidate-netlist.xml)
- [diagnostics/erc_corrections/cleanup-candidate.kicad_sch](diagnostics/erc_corrections/cleanup-candidate.kicad_sch)
- [diagnostics/erc_corrections/cleanup-edit-log.json](diagnostics/erc_corrections/cleanup-edit-log.json)
- [diagnostics/erc_corrections/cleanup-first-cli-log.json](diagnostics/erc_corrections/cleanup-first-cli-log.json)
- [diagnostics/erc_corrections/cleanup-first-connectivity.json](diagnostics/erc_corrections/cleanup-first-connectivity.json)
- [diagnostics/erc_corrections/cleanup-first-erc.json](diagnostics/erc_corrections/cleanup-first-erc.json)
- [diagnostics/erc_corrections/cleanup-first-netlist.xml](diagnostics/erc_corrections/cleanup-first-netlist.xml)
- [diagnostics/erc_corrections/cleanup-first-validation.json](diagnostics/erc_corrections/cleanup-first-validation.json)
- [diagnostics/erc_corrections/created-file-manifest.txt](diagnostics/erc_corrections/created-file-manifest.txt)
- [diagnostics/erc_corrections/erc-comparison.json](diagnostics/erc_corrections/erc-comparison.json)
- [diagnostics/erc_corrections/final-cli-log.json](diagnostics/erc_corrections/final-cli-log.json)
- [diagnostics/erc_corrections/final-connectivity.json](diagnostics/erc_corrections/final-connectivity.json)
- [diagnostics/erc_corrections/final-erc.json](diagnostics/erc_corrections/final-erc.json)
- [diagnostics/erc_corrections/final-file-integrity.json](diagnostics/erc_corrections/final-file-integrity.json)
- [diagnostics/erc_corrections/final-netlist.xml](diagnostics/erc_corrections/final-netlist.xml)
- [diagnostics/erc_corrections/final-schematic.pdf](diagnostics/erc_corrections/final-schematic.pdf)
- [diagnostics/erc_corrections/final-svg/open-semg-16-v1.2.svg](diagnostics/erc_corrections/final-svg/open-semg-16-v1.2.svg)
- [diagnostics/erc_corrections/final-validation.json](diagnostics/erc_corrections/final-validation.json)
- [diagnostics/erc_corrections/implement.py](diagnostics/erc_corrections/implement.py)
- [diagnostics/erc_corrections/independent-cleanup-review.md](diagnostics/erc_corrections/independent-cleanup-review.md)
- [diagnostics/erc_corrections/independent-digital-review.md](diagnostics/erc_corrections/independent-digital-review.md)
- [diagnostics/erc_corrections/independent-power-review.md](diagnostics/erc_corrections/independent-power-review.md)
- [diagnostics/erc_corrections/initial-cli-log.json](diagnostics/erc_corrections/initial-cli-log.json)
- [diagnostics/erc_corrections/initial-erc.json](diagnostics/erc_corrections/initial-erc.json)
- [diagnostics/erc_corrections/initial-netlist.xml](diagnostics/erc_corrections/initial-netlist.xml)
- [diagnostics/erc_corrections/label-presentation-candidate-netlist.xml](diagnostics/erc_corrections/label-presentation-candidate-netlist.xml)
- [diagnostics/erc_corrections/label-presentation-candidate.kicad_sch](diagnostics/erc_corrections/label-presentation-candidate.kicad_sch)
- [diagnostics/erc_corrections/label-presentation-edit-log.json](diagnostics/erc_corrections/label-presentation-edit-log.json)
- [diagnostics/erc_corrections/mcu-nc-view.png](diagnostics/erc_corrections/mcu-nc-view.png)
- [diagnostics/erc_corrections/modification-plan.json](diagnostics/erc_corrections/modification-plan.json)
- [diagnostics/erc_corrections/power-candidate-netlist.xml](diagnostics/erc_corrections/power-candidate-netlist.xml)
- [diagnostics/erc_corrections/power-candidate.kicad_sch](diagnostics/erc_corrections/power-candidate.kicad_sch)
- [diagnostics/erc_corrections/power-cli-log.json](diagnostics/erc_corrections/power-cli-log.json)
- [diagnostics/erc_corrections/power-connectivity.json](diagnostics/erc_corrections/power-connectivity.json)
- [diagnostics/erc_corrections/power-edit-log.json](diagnostics/erc_corrections/power-edit-log.json)
- [diagnostics/erc_corrections/power-erc.json](diagnostics/erc_corrections/power-erc.json)
- [diagnostics/erc_corrections/power-netlist.xml](diagnostics/erc_corrections/power-netlist.xml)
- [diagnostics/erc_corrections/power-validation.json](diagnostics/erc_corrections/power-validation.json)
- [diagnostics/erc_corrections/power-view.png](diagnostics/erc_corrections/power-view.png)
- [diagnostics/erc_corrections/pre-edit-hashes.json](diagnostics/erc_corrections/pre-edit-hashes.json)
- [diagnostics/erc_corrections/preparation-check-log.json](diagnostics/erc_corrections/preparation-check-log.json)
- [diagnostics/erc_corrections/render-log.json](diagnostics/erc_corrections/render-log.json)
- [diagnostics/erc_corrections/render-pdf.m](diagnostics/erc_corrections/render-pdf.m)
- [diagnostics/erc_corrections/supply-alias-completion-candidate-netlist.xml](diagnostics/erc_corrections/supply-alias-completion-candidate-netlist.xml)
- [diagnostics/erc_corrections/supply-alias-completion-candidate.kicad_sch](diagnostics/erc_corrections/supply-alias-completion-candidate.kicad_sch)
- [diagnostics/erc_corrections/supply-alias-completion-edit-log.json](diagnostics/erc_corrections/supply-alias-completion-edit-log.json)
- [diagnostics/erc_corrections/supply-alias-view.png](diagnostics/erc_corrections/supply-alias-view.png)
- [diagnostics/erc_corrections/unused-candidate-netlist.xml](diagnostics/erc_corrections/unused-candidate-netlist.xml)
- [diagnostics/erc_corrections/unused-candidate.kicad_sch](diagnostics/erc_corrections/unused-candidate.kicad_sch)
- [diagnostics/erc_corrections/unused-cli-log.json](diagnostics/erc_corrections/unused-cli-log.json)
- [diagnostics/erc_corrections/unused-connectivity.json](diagnostics/erc_corrections/unused-connectivity.json)
- [diagnostics/erc_corrections/unused-edit-log.json](diagnostics/erc_corrections/unused-edit-log.json)
- [diagnostics/erc_corrections/unused-erc.json](diagnostics/erc_corrections/unused-erc.json)
- [diagnostics/erc_corrections/unused-netlist.xml](diagnostics/erc_corrections/unused-netlist.xml)
- [diagnostics/erc_corrections/unused-validation.json](diagnostics/erc_corrections/unused-validation.json)
- [diagnostics/erc_corrections/verify.py](diagnostics/erc_corrections/verify.py)
- [erc_corrections.md](erc_corrections.md)
