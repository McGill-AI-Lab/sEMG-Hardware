# Open-sEMG-16 V1.4 implementation

28 October 2026. **Schematic implemented; power-up and streaming unqualified. Non-human bench signals only.** Based on [V1.2 corrections](../reviews_v1.2/erc_corrections.md), [V1.3 implementation](../reviews_v1.3/power_implementation.md) and original F01–F21 findings.

USB → stock ESP32-S3 DevKitC-1 → onboard regulator → shared 3.3 V for MCU/both ADS1298s, through U3 header pins 1/2. All returns share GND. Data: 16 differential pairs → ADCs → direct SPI → built-in Wi-Fi → laptop. USB supplies power/programming/debug; streaming firmware is absent.

## Parts and schematic changes

| Native-netlist physical count | Parts |
| --- | ---: |
| Original V1.4 / V1.2 | 133 |
| V1.3, preserved | 204 |
| Final V1.4 | **117** |

Counts include connectors/test points; DevKit counts as one assembly. Final: 58 capacitors, 40 resistors, 16 connectors, three IC/assembly symbols.

- Removed **BT1, U4/U5, C53–C57, R38, TP1–TP16**: battery, LDO/support/bulk network, disable strap and diagnostics; 25 parts. No replacement test points or V1.3 circuitry.
- Retained **R1–R32, all 32 input capacitors, C19/C20/C45/C46 references, all eight VCAP capacitors, C6–C9/C32–C35 supply bypasses, R33–R37 startup pulldowns**, their values and existing procurement requirements.
- Added **R39/R40, 10 kΩ CS pullups**. CS1 moves GPIO10→21; CS2 GPIO14→39. MISO moves GPIO13→40; DRDY1 GPIO9→41; DRDY2 now reaches GPIO42. These choices avoid documented boot LOW glitches on driven return/CS connections.
- Added **R41, 10 kΩ**, defining GPIO3's otherwise floating JTAG strap. Installed eFuses must permit USB JTAG/GPIO39–42; this cannot override forced pad JTAG.
- Added **C58/C59, 100 nF, ≥10 V**, parallel with VCAP3's 1 µF per TI Figure 106. **C60/C61 and C62/C63, 1 µF + 100 nF**, provide local AVDD1/AVSS1 charge-pump bypasses; existing remote capacitance does not establish local routing.
- Reorganized one A1 sheet into ADC/input and ESP32/control areas; replaced obsolete notes/wiring with labels and operating limits. AGND becomes GND. Four released MCU pins receive unused-carrier NCs. **No power flags, exclusions or pin-type edits. Project settings unchanged.**

## Verification

Native exports, **378/378 checks** and [independent review](diagnostics/independent-connectivity-review.md) verify all 128 ADC pins/16 differential mappings. Both ADCs: **19/21/22/54/56/59/48/50 = 3.3 V**; **20/23/32/53/57/58/33/49/51 = GND**; VREFN25 = GND. Independent VREFP/VCAPs, auxiliary ties, master/slave clock, shared START/SPI and separate CS/DRDY pass. No unintended shorts/extra sources found. **340 historical files unchanged.**

Final ERC: **7 errors, 0 warnings**, versus initial 7 errors/4 warnings:

| Remaining error | Count | Explanation |
| --- | ---: | --- |
| 3.3 V/GND not driven | 2 | DevKit assembly symbol omits its internal USB/regulator source; its header pin types remain unchanged. |
| ADS DOUT output/output | 1 | TI §9.4.2.1 permits shared tri-state DOUT with exclusive CS; cached symbols say ordinary output. |
| CHIP_PU unconnected/undriven | 2 | External carrier branch unused; reset circuitry is onboard the complete DevKit. |
| 5V header unconnected/undriven | 2 | No external carrier supply; USB provides onboard 5V internally. |

Evidence: [final schematic PDF](diagnostics/final-schematic.pdf), [native netlist](diagnostics/final-netlist.xml), [ERC](diagnostics/final-erc.json), [verification](diagnostics/verification.json), [component counts](diagnostics/component-counts.json), [exact modifications](diagnostics/modifications.json). Recovery files are in `diagnostics/before-implementation/`.

## Blockers before bench power-up and streaming

**F13/F16/F17 — power:** reference DevKit v1.1 has an **800 mA SGM2212**; actual board/regulator identity remains unknown. A provisional 355 mA characterized TX + 20 mA ADC + 25 mA board allowance gives 400 mA. Preserving the module's full 500 mA capability plus allowances needs **545 mA**, exceeding a 500 mA USB budget. Verify host authorization/cable, regulator temperature, startup/transients and capacitance: carrier bypasses total **42.6 µF**, above the regulator's recommended 1–10 µF before DevKit capacitance. No instability is asserted or alternate architecture substituted. [Power evidence](diagnostics/power-wifi-evidence.md).

**F06/F09/F18 — startup:** verify eFuses, exclusive CS and input-only return GPIOs. Release PWDN, wait U1 POR/VCAP, pulse/release RESET, enable U1 CLK_EN, then allow U2 POR and use its selected SPI RESET. Shared RESET clears the master clock. Enable/settle both 2.4 V references, configure/read back HR/DR=100, then shared START. Scope loaded logic: ESP VOH/ADS VIH meet at 0.8×VDD without guaranteed HIGH margin. Verify TI low-input ramp guidance versus CS pullups. [ADC evidence](diagnostics/adc-evidence.md).

Two frames: **54 bytes × 2,000 = 108 kB/s** including status; 2 MHz SPI occupies 216 µs/500 µs epoch. Ten pairs plus 16-byte header/IPv4/UDP require **116.8 kB/s** before Wi-Fi overhead/retries. Implement DMA, buffering, sequence/drop detection and recovery; test sustained integrity. Arbitrary RF outages cannot be guaranteed lossless.

**F07/F08/F10/F14/F19/F20:** qualify parts/PCB; most footprints/MPNs remain unassigned. Start with internal ADC test/short modes, then a bounded simulator near 1.65 V common mode within rail/PGA limits. No input clamp, body bias, wearer protection, isolation or human-use approval is established.
