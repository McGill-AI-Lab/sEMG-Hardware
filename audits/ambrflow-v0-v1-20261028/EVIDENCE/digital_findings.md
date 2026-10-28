# Digital/reset audit working evidence

Read-only review of both complete active schematics. Both have one root sheet and no hierarchical sheets. Parsed all root objects and embedded symbols; exported XML netlists cross-checked against their pin definitions. `v0.parsed.json` and `v1.parsed.json` are evidence copies of the parsed source data, not source changes.

## Actual controller and pin mapping

V0 represents a **bare ESP32-S3-WROOM-1 module**, U6. It does not represent a development board. V1 represents a **development board**, U3 `PCM_Espressif:ESP32-S3-DevKitC`. Exact board revision/module memory suffix is unspecified. The official DevKitC-1 v1.1 is the manufacturer reference used to establish the board's internal circuits; confirm the installed board matches it.

| Function | V0 | V1 |
|---|---|---|
| ADC chip select | U6.5 GPIO5 -> U1.39/U2.39 `/CS` | U3.16 GPIO10 -> U1.39 `/CS_ADC1`; U3.20 GPIO14 -> U2.39 `/CS_ADC2` |
| ADC reset | U6.7 GPIO7 -> U1.36/U2.36 `/RESET` | U3.6 GPIO6 -> same ADC pins/net |
| ADC power down | U6.6 GPIO6 -> U1.35/U2.35 `/PWDN` | U3.7 GPIO7 -> same ADC pins/net |
| START | U6.23 GPIO21 -> U1.38/U2.38 `/START` | U3.12 GPIO8 -> same ADC pins/net |
| MOSI | U6.19 GPIO11 -> U1.34/U2.34 | U3.17 GPIO11 -> same ADC pins |
| SCLK | U6.21 GPIO13 -> U1.40/U2.40 | U3.18 GPIO12 -> same ADC pins |
| MISO | U1.43 -> U6.20 GPIO12; U2.43 -> U1.41 daisy input | U1.43 and U2.43 -> U3.19 GPIO13 |
| DRDY | U1.47 -> U6.12 GPIO8 | U1.47 -> U3.15 GPIO9 |

V0 module EN U6.3 has R20=10k pull-up to +3.3V. V1 external U3.3 CHIP_PU is unconnected, but the official board has internal **R5=10k pull-up and C6=1uF to board ground**, plus reset/autoprogram circuitry. External EN pull-up omission is therefore **not a demonstrated fault**. Reference-board source: [Espressif DevKitC-1 v1.1 schematic, sheet 2](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf). Downloaded PDF and rendered page2 PNG are in this folder.

## Confirmed reset-state design omissions (J2/J3)

ESP32-S3 [SoC datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf), Table 2-1 pp16-18: GPIO5/6/7/8/21 have no reset pull or output setting; GPIO9-14 have input-enable at reset but no weak pull. Footnote 6 defines IE/WPU/WPD. None of the used ADC-control GPIOs has a guaranteed reset drive or pull.

Both schematics connect shared `/PWDN`, `/RESET`, `/START` directly to those GPIOs, with no external bias resistor. ADS1298 digital input pin descriptions and electrical specifications give no guaranteed internal pull on those control pins. Firmware is absent from the specified electrical sources, and cannot establish an output while the MCU is held in reset. Thus **there is no guaranteed hardware default on ADC enable/reset controls in either revision**. This is a confirmed design omission, P1, not proof of a particular observed glitch. Consequences depend on actual startup waveforms.

Simplest supported starting correction: 10k pulldowns on `/PWDN` and `/RESET`, and a START pulldown for a defined conversion default. Ground them to the ADC's actual DGND after fixing the supply/ground errors. One pull serves both ADCs on a shared net. With two ADC input leakage limits of 10uA each, 10k gives at most 0.20V bias error, below 0.66V VIL at 3.3V DVDD. A driven high draws about 0.33mA through the resistor. Verify these defaults with MCU reset held and all supply modes tested.

The ADS1298 supply-sequencing instructions (§11.1) require low inputs until supplies stabilize. Therefore do not blindly pull every control high. Firmware should set the two CS outputs high after valid supplies and before releasing reset/power-down. The precise CS/MOSI/SCLK passive-default policy must be checked against the selected startup sequence; if deterministic low defaults on every input are required, their pull-downs are justified, but cannot be treated as unnecessary generic additions. The datasheet does not explicitly guarantee DOUT high impedance during PWDN, so do not claim preboot shared-MISO contention is impossible merely because PWDN is low.

## Clock-control case within J3

V0: `Net-(U1-CLK)` contains only U1.37 CLK and U1.52 CLKSEL. The equivalent U2 net contains only those two pins. Neither net has a rail connection or external drive. ADS1298 Table 11 p50 and CONFIG1 p67 establish that at reset CLK_EN=0: with CLKSEL low, CLK is an input; with CLKSEL high, CLK is tri-state. Tying the pins together therefore does not define CLKSEL. This is confirmed floating control at reset.

V1: U1.52 is tied to +3.3V; U2.52 is tied to schematic `DGND`. The intended master/slave selection is clear, but U1.37 is unconnected and the adjacent global ADC_CLK label is dangling (ERC also reports both). U2.37 is the only pin on `ADC_CLK`; it has no clock source. Thus V1 corrects the local floating CLKSEL arrangement, but the selected clock arrangement is incomplete. Root issue **PARTIALLY FIXED**, P1/P0 functional blocker depending counting policy; do not count a complete clock fix. Exact KiCad correction: connect U1.37 to `ADC_CLK`, which already reaches U2.37, retain U1 CLKSEL high/U2 CLKSEL low on valid rails, and verify firmware sets U1 CONFIG1.CLK_EN=1. This is a connection and firmware-state completion of the chosen clock-control scheme, not a request for a new oscillator.

## Bootstrap J1 is not a proven normal-boot failure

GPIO0, GPIO45 and GPIO46 are externally unconnected in both revisions, but have manufacturer-defined internal pulls. They are not floating simply because ERC says unconnected.

GPIO3 is genuinely unconnected without an internal pull: V0 U6.15; V1 U3.13 (official board also routes it directly). However [module datasheet §4.4/Table4-5](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf) says this strap affects JTAG source only with particular nondefault eFuse settings; it is ignored for default settings. The schematic establishes a floating strap, but not that it must select a particular JTAG source. Recommended classification: **CANNOT VERIFY** functional fault because eFuse/debug policy is missing. Do not invent a failed boot or add a resistor without choosing a required JTAG state.

## Logic-level calculation (I1)

For the valid common-rail V0 digital interface at 3.3V relative to AGND:

- ADS VIH=0.8*DVDD=2.64V; ESP VOH minimum=0.8*VDD=2.64V. Compatible at the stated limits, with zero guaranteed high-level margin; this is not proof of a fault.
- ADS VIL=0.66V; ESP VOL maximum=0.33V.
- ADS VOH minimum=DVDD-0.4=2.9V; ESP VIH minimum=0.75*3.3=2.475V.
- ADS VOL maximum=0.4V; ESP VIL maximum=0.825V.

Actual drive strength/timing still needs firmware/waveforms. V1 cannot be treated as a valid 3.3V logic interface: ADS AVDD is tied to AGND, ADS DVDD is on a separate DGND net, actual ADC DGND pins are on AGND, and MCU board ground is on DGND. Fix these A1/H1/H2 errors before assessing actual digital levels; do not invent a voltage for the floating island or duplicate its consequences as several independent confirmed faults.

## Checklist disposition recommendations

| ID | Finding / recommended classification |
|---|---|
| I1 | V0 nominal thresholds compatible; V1 valid logic supply/reference absent as part of confirmed power errors. Actual input voltage cannot be calculated from static floating nets. |
| I2 | CANNOT VERIFY: actual edge rate/load/waveform absent. No big RC on serial control nets; SCLK has hysteresis internally. |
| I3 | NOT APPLICABLE: ADC DOUT and DRDY are ordinary driven outputs; no open-drain interface or power-good line in the parent circuit. Do not add pull-ups to DRDY by habit. |
| I5 | CANNOT VERIFY: no reliable waveform proving slow/chattering threshold crossings. SCLK is explicitly Schmitt-triggered (§9.5.1.2). |
| J1 | CANNOT VERIFY functional effect of GPIO3 strap without eFuse/debug requirements; internal defaults make GPIO0/45/46 valid. |
| J2 | STILL PRESENT for uncertain hardware default on ADC PWDN enable; overlaps J3 root reset-bias omission. Regulators are not MCU-controlled in these schematics. |
| J3 | STILL PRESENT overall for ADC enable/reset controls; clock-control subfinding partially fixed as described. |
| J4 | CANNOT VERIFY real voltage during startup/ground faults; no explicit 5V connection to MCU GPIO. V0 nominal ADS outputs are within 3.3V receiver bounds. |
| K1 | CANNOT VERIFY operating currents without firmware state/loading; no resistor/LED DC load demanding excess GPIO current shown. |
| K2 | CANNOT VERIFY: V1 shared MISO is valid with mutually exclusive CS. Both CS asserted could conflict, but firmware is unknown. V0 daisy chain does not short ADC DOUTs together. ADC GPIOs tied low in both designs are safe only while configured as inputs/low; no proof firmware changes them high. |
| K3 | CANNOT VERIFY operating states; V1 has invalid ADC supply wiring, so do not assume any valid operation; V0 analog rail lacks source. No fabricated GPIO-high state. |
| E9/L2 | CANNOT VERIFY actual order/ramp without supply/firmware traces. §11.1 establishes the requirement but cannot establish observed timing. |
| L1 | CANNOT VERIFY: no supply load-step waveform, battery impedance or firmware state transition evidence. |

## Board power caveat within E5

The official board has a 5V-to-3.3V LDO (SGM2212-3.3) whose output reaches the 3V3 headers through R24=0. The main V1 circuit ties both 3V3 headers to its external +3.3V rail. USB can make that internal LDO another active source. The [official board guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html) describes USB, 5V-header and 3V3-header supply methods as mutually exclusive. Do not claim USB is actually connected; establish intended powered/programming modes. Parent-circuit U4/U5 output paralleling is already a definite issue independent of USB.

## LEDs on the development board (D1/D2)

V0 has no LED symbols. V1 has no parent-circuit LED, but the official DevKitC board includes them. On official board schematic sheet 2, power LED D5 is fed from VCC_3V3 through **R11=5.1k**, with D5 returning to GND. Even ignoring the LED forward drop, current is bounded by 3.3/5100=0.647mA. It has current limitation. RGB D6 is `SK68XXMINI-HS`, a smart LED with integrated controller/current drive, not bare RGB junctions requiring external series resistors. [OPSCO's product page](https://www.opscoled.com/en/product/details.html?id=29) identifies the integrated IC and current variants. Its [manufacturer-issued datasheet mirrored at Adafruit](https://cdn-shop.adafruit.com/product-files/2659/2304101800_OPSCO-Optoelectronics-SK6812MINI-HS_C2922787.pdf) is available for the specific SK6812MINI-HS family member. The exact populated board revision/LED variant is unspecified, so cite the reference implementation without claiming the actual unit's BOM. D1 NOT FOUND overall (V0 not applicable); D2 NOT APPLICABLE: neither circuit has the open-collector LED arrangement in the condition.

## Useful meeting questions

1. Was GPIO3 flagged as a normal boot fault, or only as an undefined JTAG strap? What eFuse setting was assumed?
2. What reset-time GPIO pulls were assumed for ADC PWDN/RESET/CS? The selected ESP32 GPIOs do not have guaranteed reset pulls.
3. Does the detector model ADS1298 CLK_EN reset=0 when CLK and CLKSEL are tied together in V0?
4. Can the detector distinguish a DevKitC's built-in EN pull-up/RC from an externally unconnected bare MCU/module input?
5. Was shared MISO flagged because both ADCs can be selected by firmware, or did the detector assume both outputs always drive?
6. Which USB/external power combinations were assumed for the V1 development-board LDO?
