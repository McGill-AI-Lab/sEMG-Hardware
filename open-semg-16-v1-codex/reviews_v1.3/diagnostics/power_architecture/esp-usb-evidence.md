# ESP32-S3 / DevKit power and USB evidence

27 October 2026. Independent read-only contribution for the V1.3 power review. No schematic edit, powered test, board identity confirmation or wearable readiness claim.

## Evidence and actual carrier connectivity

Read the original review and successive V1.1/V1.2 change and ERC records, including V1.2 `erc_corrections.md`, which supersedes the earlier parallel-output state. Checked the fresh V1.3 native XML at [v1.3-netlist.xml](v1.3-netlist.xml). It confirms:

- U3 is the complete 44-terminal ESP32-S3-DevKitC assembly symbol, not a bare WROOM module. Its pins 1 and 2 connect directly to the common `+3.3V` net, U5 OUT5, both ADC supply groups and C57. U3 grounds 22/23/24/44 share actual AGND and battery negative.
- U3.21 is alone on `+5V` in the carrier. This is not evidence that the internal DevKit 5 V node stays unpowered when USB is attached.
- U3.3 CHIP_PU has no carrier connection; an intact matching reference DevKit already supplies its reset circuit. U3.25/.26 (GPIO19 USB D−/GPIO20 USB D+) are carrier-unconnected, which leaves the board's internal USB connections intact.
- U3 GPIO6/7/8/9 (carrier 6/7/12/15) serve ADC RESET/PWDN/START/DRDY; GPIO10/11/12/13/14 (16/17/18/19/20) serve CS1/DIN/SCLK/DOUT/CS2. They are not the boot straps or USB data signals. Existing pulldowns only constrain high-impedance conditions; CS has no external bias or gate.
- U4 output is isolated, while U5 output remains tied to the DevKit's 3V3 headers. F04's original two-carrier-LDO sharing mechanism is fixed; F17 remains.

## Module demand: specified data and design allowance

Local manufacturer source: [ESP32-S3-WROOM-1/-1U datasheet v1.8](../../../../docs/datasheets/originals/components/ESP32-S3-WROOM-1.pdf), verified against the [official current PDF](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf).

Table 6-2, p.27: supply 3.0–3.6 V, nominal 3.3 V; external supply capability at least 0.5 A. This is a supply design requirement, not a claim that normal current is constantly 500 mA.

Table 6-4, p.28 lists Wi-Fi peak current at 3.3 V and 25 °C, TX at 100% duty, RX with peripherals disabled and CPU idle:

| Operation | Stated peak |
|---|---:|
| 802.11b, 1 Mbps, 20.5 dBm TX | 355 mA |
| 802.11g, 54 Mbps, 18 dBm TX | 297 mA |
| 802.11n HT20 MCS7, 17.5 dBm TX | 286 mA |
| 802.11n HT40 MCS7, 17 dBm TX | 285 mA |
| 802.11b/g/n HT20 RX | 95 mA |
| HT40 RX | 97 mA |

Table 6-5: Bluetooth LE TX peaks 344/202/187/119 mA at +20/+9/0/−15 dBm; RX 93 mA. These are characterization conditions, not a guaranteed assembly worst case over temperature and application software. CPU, flash/PSRAM use, RF duty cycle and actual DevKit overhead must be measured. Do not add every table entry as simultaneous load, and do not treat module deep-sleep numbers as DevKit board consumption. A 1 A class external converter provides useful engineering margin; the minimum deliverable output at the lowest battery voltage, current limit, thermal derating and wiring losses still need verification.

## Hidden DevKit power sources and loads

The [official v1.1 board guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#power-supply-options) explicitly treats USB, 5 V headers and 3V3 headers as mutually exclusive supply methods. Both USB sockets are power entry points. Initial and v1.1 boards coexist; RGB uses GPIO48 versus GPIO38 respectively. Installed board revision, exact module suffix and any clones/modifications remain unknown.

The [official v1.1 schematic dated 2022-11-30, p.2](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) identifies board U2 as SGM2212-3.3XKC3G/TR, CP2102N USB-UART bridge, RGB LED, red power LED, zero-ohm links and a Schottky diode. Its regulator output and 3V3 headers belong to the same supply domain. Onboard reset uses R5=10 kΩ and C6=1 µF, with buttons and automatic-programming transistors. Verify all of this on the selected physical assembly before relying on it. The carrier cannot disconnect board-internal paths merely by leaving header branches unconnected.

Consequences derived from these connections: attaching USB can energize the carrier common rail, even with the battery absent or R38 fitted. With external battery regulation active it creates competing 3.3 V sources; with U5 disabled it can drive U5's output-discharge path. It can also expose an unpowered converter/LDO output above its input. Board USB diodes are not proof of complete 3V3-source or human-interface isolation.

The [SGMICRO SGM2212 datasheet, July 2023 Rev. A.2](https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf), pp.1,4–6,10: 800 mA rating; no verified reverse-current blocking guarantee in this document. Pin description recommends 1–10 µF effective ceramic output capacitance while application text gives a 1 µF effective minimum. Neither proves that a large external capacitor bank is unstable. Whole-rail capacitance and startup must be qualified. Its SOT-223 thermal figure 117 °C/W is a reference fixture value, not the actual DevKit thermal resistance.

A 5 V boost powering U3.21 avoids external 3V3 drive into the board LDO, but its nominal LDO efficiency is only 3.3/5=66%. At 355 mA the LDO loss screen is (5−3.3)×0.355=0.604 W; at 500 mA, 0.85 W. These screens and USB source exclusivity remain even if that alternative is selected.

## Reset, brownout and startup

[Espressif schematic checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html#chip-power-up-and-reset-timing): stabilize supply before CHIP_PU release; allow ≥50 µs stabilization and ≥50 µs reset assertion. Recommended RC is typically 10 kΩ/1 µF, adjusted for actual ramps. Slow or unstable supplies may need a monitor near 3.0 V. Main entrance needs at least 10 µF; RF current steps can collapse a weak supply. GPIO6–14 have documented startup low glitches, so pulldowns/pullups alone are not a complete ADC interface sequencing guarantee.

The [current ESP-IDF v6.1 configuration reference](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/kconfig-reference.html#config-esp-brownout-det) enables brownout reset by default and lists approximate, chip-variable thresholds. Firmware/build settings were not supplied. Brownout reset does not disconnect the battery or ensure ADC reset, analog rail validity, safe GPIO states or clean restart. Use an external supervisor and explicit hardware interface sequencing, retain firmware brownout detection, and verify fault recovery. Design its threshold above the module's 3.0 V minimum after tolerance and propagation/droop allowances; approximately 3.1 V can be a starting engineering target, subject to rail tolerance margin.

A supervisor's open-drain reset may pull U3.3 CHIP_PU low alongside the board's existing reset network, if its sink/leakage/timing specifications and board identity are checked. Do not add another arbitrary RC or a push-pull driver against the automatic-program circuit. ADC supplies/inputs need their own valid-state gating; MCU reset alone is not it.

## Concrete USB mode contract

Lowest-complexity design recommendation while retaining a stock DevKit and battery-only worn use:

1. RUN: regulated external 3V3 into U3.1/.2; U3.21 has no external source. Both USB sockets must be physically inaccessible in the worn assembly. Use OTA for routine updates only after stable operation is established.
2. OFF-BODY USB SERVICE: disconnect battery and remove U3 from its carrier sockets before attaching USB for programming. This physically removes all power and GPIO backfeed paths to the carrier; USB powers the detached board only. Battery disconnection alone is insufficient while U3 remains connected to U5/ADCs.
3. CHARGE: remove/disconnect the battery and use a suitable charger for the specified cell off the body; no charger is present in the carrier.
4. FULL-CARRIER USB SERVICE: unsupported until a verified circuit isolates the DevKit onboard LDO output from externally driven 3V3, defines USB-UART bridge power and native USB attach behavior, controls both USB power paths and all absent-supply signal paths, and includes a complete source selector. A carrier-only ideal diode does not stop USB energizing the rest of a common rail through the DevKit. A VBUS-cut cable is not by itself a verified solution.

If assembled USB bench operation is a firm requirement, it can alter the architecture choice: specify an exact modifiable DevKit revision and disconnect its internal LDO output (including tab/zero-ohm bypass paths as applicable) before implementing a validated external power mux, or use a dedicated service adapter with deliberate VBUS/signal isolation. Do not name a link to remove without verifying its actual schematic function and fitted board. These are proposed requirements, not authorized hardware changes.

## Additional check: proposed 3.4 V main rail

A proposed main rail of 3.4 V, statically bounded 3.354–3.446 V, fits the WROOM module's 3.0–3.6 V operating range. It is an engineering choice for downstream analog-LDO headroom, not the DevKit guide's nominal 3.3 V recommendation. It reduces margin to the 3.6 V upper operating limit: from 154 mV at the stated worst static upper bound, all ripple, load-release overshoot and startup excursions must also fit. At unchanged current, digital power rises approximately 3% compared with 3.3 V; actual current changes are unmeasured.

The [Silicon Labs CP2102N datasheet](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf), Table 3.1, specifies VDD=3.0–3.6 V, VIO=1.71 V to VDD and VREGIN=3.0–5.25 V. Its external-supply regulator-bypass connection ties VREGIN to VDD. Thus 3.4 V is within CP2102N VDD limits **if the actual board powers those pins in that permitted configuration**. The carrier symbol alone does not establish that condition.

The [Normand SK68XX MINI-HS manufacturer datasheet Rev.04](https://www.normandled.com/upload/202105/SK6812MINI-HS%20LED%20Datasheet.pdf), p.5, lists a 3.7–5.5 V supply range; consequently it does not establish normal RGB LED operation at either 3.3 or 3.4 V. The exact fitted LED silicon and DevKit LED supply path need verification. Keep RGB disabled for acquisition; if the fitted LED cannot be qualified on the selected rail, isolate/depopulate it during the later authorized implementation. Do not infer damage, excess current or reliable operation from an undervoltage condition without evidence.

An alternative 3.3 V main / 2.9 V analog split may preserve a 0.3 V LDO headroom bound after tolerances if an appropriate fixed 2.9 V LDO variant is available. It reduces ADS1298 analog-minimum/common-mode/offset margin and still needs its full accuracy/PSRR guarantee checked. No universal superiority follows from nominal voltage choice alone. The 3.4 V recommendation must remain conditional on exact DevKit assembly qualification and measured rail extrema.
