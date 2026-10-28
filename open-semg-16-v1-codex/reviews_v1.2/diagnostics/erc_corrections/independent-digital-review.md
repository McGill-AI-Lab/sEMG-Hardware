# Independent final digital and No Connect review

27 October 2026. Scope: current V1.2 source, [initial native netlist](initial-netlist.xml), [final native netlist](final-netlist.xml) and [final ERC](final-erc.json) from this ERC-correction pass. This reviewer modified no design/project/library or diagnostic file; only this review note was created.

**Result: no unintended digital connectivity regression found.** Exactly 26 No Connect markers were added to individually approved unused carrier-header terminals. GPIO3 remains deferred because the user confirmed STRAP_JTAG_SEL is unknown. CHIP_PU and the5V header also have no new NC. Final ERC reports 7 errors and 4 warnings, including the deliberately retained GPIO3 report.

Reviewed final schematic SHA-256: `202b2b320076c5e802f55e6ed566ae640cb948c6544777b9d51b11222e371208`. The earlier electrical-review snapshot was `c70cce6a7f7677ccb413ca9a73af67c5e9f39819fecc1eee2636885cd3ec2529`; the limited presentation follow-up below verifies the only subsequent source change.

## Component boundary and circuit requirements

The active U3 instance is PCM_Espressif:ESP32-S3-DevKitC, with value ESP32-S3-DevKitC, its DevKit footprint, and44 distinct pins. It represents the complete development-board assembly, rather than a bare 41-pin WROOM module. Its full symbol-instance source is byte-identical to the pre-edit instance in before-power.kicad_sch.

“No Connect” here records that the **carrier does not connect this external DevKit header terminal**. It does not disconnect or disable circuitry inside the DevKit. The existing ADC/SPI/control assignments use GPIO6–14; none of the approved26 terminals belongs to those functional nets. OrdinaryGPIO multiplexed alternatives are optional rather than missing required connections. The per-pin matrix below explicitly preserves onboard UART/USB/RGB, boot straps and variant-dependent memory roles.

The fitted board/SKU, actual eFuse contents, startup behavior, USB-power policy and firmware qualification remain unresolved. No NC was added to an evidence-dependent terminal merely to eliminate its report.

## Manufacturer sources

- **D1:** [ESP32-S3-WROOM-1/-1U datasheet v1.8](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf), also supplied locally at ../../../../docs/datasheets/originals/components/ESP32-S3-WROOM-1.pdf. Table 3-1 pp.11–12 identifies module functions and memory/voltage-domain caveats; boot Tables 4-1/4-3/4-4/4-5 pp.13–16 establish strap behavior and conditionalGPIO3 use.
- **D2:** [Official DevKitC-1 v1.1 guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html), J1/J3 header tables and revision details. The original DevKit RGB usesGPIO48; v1.1 usesGPIO38.
- **D3:** [Official DevKit schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf), p.2, for retained internal USB/UART, RGB and boot/reset circuits.
- **D4:** [ESP32-S3 hardware design checklist](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html#gpio), GPIO section and optional RTC-clock section. Its guidance permits software-managed input pulls for unused high-impedance inputs and identifies external RTC clocking as optional. It does not require adding arbitrary external bias to these carrier headers.
- **D5:** [ESP32-S3 SoC datasheet v2.2](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf), Tables 3-1/3-3 and JTAG source selection. It corroborates the boot and default/eFuse distinctions; no input-only claim about GPIO46 is needed here.

The module datasheet's pin numbers differ from this carrier's44-pad U3 numbering. The matrix uses U3 pad numbers and D2's header positions, preventing accidental placement at bare-module coordinates.

## Per-pin verification and final NC anchors

All 26 entries are **approved for an unused external carrier connection**, with the stated board-internal and firmware constraints. Coordinates are mm. Each new NC UUID was read independently from the final source and confirmed to anchor at the exact current U3 pin coordinate. No functional wire was removed to make a pin appear unused.

| U3 pin / function | Coordinate | Why the carrier can leave it unconnected / constraints | Manufacturer cross-reference |
|---|---|---|---|
| U3.8 / GPIO15/ADC2_CH4/32K_P | 511.81, 50.80 | Optional RTC crystal terminal; no carrier RTC crystal or UART-flow-control requirement. ADC timebase is separate. | D1 Table 3-1; D2 J1.8; D4 optional RTC clock |
| U3.9 / GPIO16/ADC2_CH5/32K_N | 511.81, 53.34 | Optional RTC crystal terminal; same unused carrier role as GPIO15. | D1 Table 3-1; D2 J1.9; D4 optional RTC clock |
| U3.36 / GPIO39/MTCK | 511.81, 60.96 | External JTAG clock header unused; internal module/debug configuration remains intact. | D1 Table 3-1; D2 J3.9 |
| U3.37 / GPIO40/MTDO | 511.81, 63.50 | External JTAG data-output header unused; no carrier JTAG cable is required. | D1 Table 3-1; D2 J3.8 |
| U3.38 / GPIO41/MTDI | 511.81, 66.04 | External JTAG data-input header unused; no carrier JTAG cable is required. | D1 Table 3-1; D2 J3.7 |
| U3.39 / GPIO42/MTMS | 511.81, 68.58 | External JTAG mode-select header unused; no carrier JTAG cable is required. | D1 Table 3-1; D2 J3.6 |
| U3.43 / GPIO43/U0TXD | 562.61, 43.18 | External UART TX header unused; DevKit onboard USB-UART connection remains internal. | D1 Table 3-1; D2 J3.2; D3 p.2 |
| U3.42 / GPIO44/U0RXD | 562.61, 45.72 | External UART RX header unused; retain onboard USB-UART connection and its firmware role. | D1 Table 3-1; D2 J3.3; D3 p.2 |
| U3.26 / GPIO20/USB_D+ | 562.61, 50.80 | External USB_D+ header branch unused; onboard native USB data circuit is retained. | D1 Table 3-1; D2 J3.19; D3 p.2 |
| U3.25 / GPIO19/USB_D- | 562.61, 53.34 | External USB_D- header branch unused; onboard native USB data circuit is retained. | D1 Table 3-1; D2 J3.20; D3 p.2 |
| U3.31 / GPIO0 | 562.61, 60.96 | No carrier boot control required. Preserve module weak pull-up and DevKit boot/programming circuitry; carrier does not force a strap value. | D1 Tables 4-1/4-3; D2 J3.14; D3 p.2 |
| U3.41 / GPIO1/ADC1_CH0 | 562.61, 63.50 | General optional GPIO/ADC/touch terminal; current carrier assigns no function. | D1 Table 3-1; D2 J3.4 |
| U3.40 / GPIO2/ADC1_CH1 | 562.61, 66.04 | General optional GPIO/ADC/touch terminal; current carrier assigns no function. | D1 Table 3-1; D2 J3.5 |
| U3.4 / GPIO4/ADC1_CH3 | 562.61, 71.12 | General optional GPIO/ADC/touch terminal; current carrier assigns no function. | D1 Table 3-1; D2 J1.4 |
| U3.5 / GPIO5/ADC1_CH4 | 562.61, 73.66 | General optional GPIO/ADC/touch terminal; current carrier assigns no function. | D1 Table 3-1; D2 J1.5 |
| U3.10 / GPIO17/ADC2_CH6 | 562.61, 99.06 | Optional GPIO/UART1 terminal; current carrier uses neither function. | D1 Table 3-1; D2 J1.10 |
| U3.11 / GPIO18/ADC2_CH7 | 562.61, 101.60 | Optional GPIO/UART1 terminal; current carrier uses neither function. | D1 Table 3-1; D2 J1.11 |
| U3.27 / GPIO21 | 562.61, 104.14 | General optional GPIO terminal; current carrier assigns no function. | D1 Table 3-1; D2 J3.18 |
| U3.32 / GPIO35 | 562.61, 106.68 | May connect to module-internal octal PSRAM; leaving carrier pad unrouted avoids loading it. On other variants no carrier function is assigned. | D1 Table 3-1 footnote b; D2 J3.13 |
| U3.33 / GPIO36 | 562.61, 109.22 | Same memory-reservation constraint; no carrier connection is required. | D1 Table 3-1 footnote b; D2 J3.12 |
| U3.34 / GPIO37 | 562.61, 111.76 | Same memory-reservation constraint; no carrier connection is required. | D1 Table 3-1 footnote b; D2 J3.11 |
| U3.35 / GPIO38 | 562.61, 114.30 | External carrier header unused; v1.1 DevKit RGB connection remains internal. Do not blanket-disable its onboard role. | D1 Table 3-1; D2 J3.10/revisiondetails; D3 p.2 |
| U3.30 / GPIO45 | 562.61, 116.84 | Leave carrier strap branch unconnected. Preserve internal weak pull-down and module memory-voltage eFuse behavior; do not force this node high. | D1 Tables 4-1/4-4; D2 J3.15 |
| U3.14 / GPIO46 | 562.61, 119.38 | Leave carrier strap branch unconnected. Preserve internal weak pull-down and DevKit GPIO0 boot circuitry; no extra carrier strap drive is required. | D1 Tables 4-1/4-3; D2 J1.14 |
| U3.28 / GPIO47 | 562.61, 121.92 | Optional carrier GPIO; no function assigned. Some S3R16V modules use 1.8 V here, so no arbitrary 3.3 V bias is appropriate. | D1 Table 3-1 footnote c; D2 J3.17 |
| U3.29 / GPIO48 | 562.61, 124.46 | External header unused; RGB role on initial DevKit remains internal. Some S3R16V modules use 1.8 V here; do not impose a carrier bias. | D1 Table 3-1 footnote c; D2 J3.16/revisiondetails |

### Traceability: original pin UUID to new NC UUID

| U3 pin | Unchanged pin UUID | New NC UUID |
|---|---|---|
| U3.8 | `c7fe87fa-2f10-4e56-9051-aeceb5f4602b` | `005568c3-a093-4aad-9895-66820163b617` |
| U3.9 | `8bb9b256-c392-44af-bfa4-09054b34d0a7` | `2eaa6fec-8efc-4bf7-8634-9d6bf6b88b0b` |
| U3.36 | `2128f0e8-66fd-46f4-ba85-acf025c5b7cf` | `f3374efa-fc59-45e5-ac1c-e093a64e7812` |
| U3.37 | `571dad94-66a7-4e67-a30e-274a75cd4444` | `e2a93457-abd4-46cf-8365-ba8e6f99d299` |
| U3.38 | `67b54cb9-47f7-429f-86bf-e2a4540d044f` | `786dd66d-57c1-4423-8a75-f6d3db73a113` |
| U3.39 | `28b07b49-2e3b-4f16-9059-48baaabbe63d` | `320c5176-b669-4be7-8c20-19af3ddf3299` |
| U3.43 | `8f0de143-24a2-4cf6-82f6-77b68d9dccf3` | `acc1c8d3-01b2-48cf-853e-7ad91e02913d` |
| U3.42 | `6b5bb64b-0a3b-4969-bc23-3e5d90a5f588` | `a2136587-0274-4152-8d18-4c0f68a44297` |
| U3.26 | `24b9956c-0093-480e-bf6e-3c202986e453` | `adc73fa3-fd21-4ddd-a6a5-55071a3293cb` |
| U3.25 | `0fb67ce2-47a8-4ea4-8e65-9aec3f990419` | `6cd226e8-2882-4162-a568-bdb86d5b246c` |
| U3.31 | `6889afaf-5d7f-4314-a13c-b142ace68a25` | `adfc9d2e-4ad1-49f0-a32f-b946f868799f` |
| U3.41 | `01c982f1-204d-4a47-ae93-ca21543eda82` | `acf88517-9be1-4649-8bad-19ccba012c4b` |
| U3.40 | `0605c299-2d2b-40ac-a74f-924d39c69476` | `79551241-3fcc-4ef9-a202-bb9b63f27eed` |
| U3.4 | `bc5f3d45-c62f-45b0-9e17-3cc02c3ce904` | `a0bc7fb2-9376-43f9-9453-68a37d61c47b` |
| U3.5 | `e24ff256-1407-4452-8b62-3796e883c65d` | `d7158f60-a0d9-4e57-bf80-d48116bd4d83` |
| U3.10 | `dafc3c56-e60a-4c8a-976d-8ddd6a369fe7` | `51f45d35-0adb-4257-b856-8ab978029dc6` |
| U3.11 | `31c584f3-6db0-446c-8ab6-d6b7279d63f3` | `3f551da2-ed74-47a1-b20e-d1a129a74a4a` |
| U3.27 | `36304e0b-1d68-481f-94c6-02ea6862afd0` | `0eb1e856-e21f-4532-b8ed-cad9e532b06b` |
| U3.32 | `d18b7919-c2ee-400f-acb0-078f68386a32` | `f75ba201-fa98-45a6-b98c-07be8824f48c` |
| U3.33 | `b0c1911a-52aa-44fe-9881-4f8e7abadddf` | `ac8dff60-8bbc-4c29-bdbb-f8b8a5d44ae0` |
| U3.34 | `2efdaa0d-fb86-4275-b912-9c8071aec0d4` | `fa36cfbc-bd74-4da0-be1d-132c0b451ec1` |
| U3.35 | `29b85401-be1e-47de-9737-c20fda741df7` | `5bb6a921-35d2-4f48-ad29-2d23acfec1df` |
| U3.30 | `797d7d25-675e-4474-9bf3-85f68873e5dc` | `79d72a07-73cf-4a4c-ae0a-6539a5e79329` |
| U3.14 | `0868d39f-2c75-409e-9e48-0b160740f239` | `23a91c4d-1937-44c2-9840-fcc060452ccc` |
| U3.28 | `edea7cb7-c3e8-4dc8-9bc8-14e6716c3785` | `dc9a7496-f042-4dae-bfe7-ef0185af6e41` |
| U3.29 | `8f307098-1866-4a3e-926d-d4024adc4b70` | `9c177f68-7caf-4133-a054-65b6115171ae` |

## Deferred and protected terminals

- **U3.13 / GPIO3:** (562.61,68.58), pin UUID `810351da-8113-4a08-bf3b-96eeeeea5f0e`. No NC. D1 §4.4/Table 4-5 shows that GPIO3 is ignored for certain eFuse settings but must have a defined external level when it selects the JTAG source. The user reported STRAP_JTAG_SEL unknown; factory default provisioning was not assumed. Its pin_not_connected report is intentionally retained pending evidence or a justified design.
- **U3.3 / CHIP_PU:** (511.81,43.18), pin UUID `cfa969c5-8e37-47bf-a045-3c017c96281a`. No NC and no reset-circuit change. Both existing pin_not_connected and pin_not_driven reports remain.
- **U3.21 / 5V:** no NC and no supply-role alteration. Its source-model/evidence-dependent report remains.
- All 8 pre-existing RLD/WCT NC marker objects are byte-preserved. Total explicit NC markers are now 34 = 8 original + 26 new.
- Shared DOUT remains a supported cascade topology subject to exclusiveCS and valid supply/startup behavior. No bus splitting, pin-type change or generic pullup was introduced.

## Independent source and netlist checks

The independent review executed **132 passed checks** using a read-only source-span S-expression parser and native XML netlist inspection. This is separate from the root verifier's final 2,050 passed assertions.

Verified:

1. U3's complete instance remains byte-identical; exactly 26 approved NC anchors exist and no others were added.
2. All44 U3 pin-to-net assignments remain identical. Every carrier signal-net partition is preserved.
3. U3's+3.3V supply memberships differ only by the documented F04 isolation of U4.5 and C54.1. The independent comparison explicitly permits those two removals and no others.
4. Every one of the 32 ADC acquisition input nets has exactly the same members as the baseline; thus all 16 differential channels retain their input mappings.
5. MISO, MOSI, SCLK, both CS nets, START, RESET, PWDN, both DRDY nets and shared ADC_CLK retain exact memberships.
6. Both independent reference nets and all 8VCAP nets retain exact memberships.
7. Final ERC contains exactly 7 errors / 4 warnings. The only pin_not_connected reports are CHIP_PU and deferredGPIO3. The expected valid-topology and evidence-dependent reports remain.

A first comparison correctly detected the intentional F04 supply partition before that declared exception was incorporated into this digital review's invariant. No additional connectivity difference was found; this was not a design revision.

## Final label-presentation follow-up

The [pre-presentation source](before-label-presentation.kicad_sch) hashes to the earlier electrical-review snapshot above. A source-span comparison against the delivered schematic proves that **only one global-label object changed**: UUID `75fc8b9d-1b77-49f1-bb82-13b6eff87138`, the `+3.3V` label at (209.55,160.02) mm. The exact changes are font 1.27→1.0 mm, angle 180→0 degrees, and right→left justification. Label text, global scope, shape, anchor and UUID remain unchanged. All source bytes outside that object are identical.

The complete explicit-NC UUID set is unchanged. Therefore the reviewed 26 new NC anchors, all eight original NCs, the U3 instance and every wire remain as reviewed. The final native net partitions exactly match the preceding unused-pin-stage export and the presentation candidate export; this also independently confirms that the cleanup/presentation operations introduced no electrical net change after the documented power isolation. The [presentation edit log](label-presentation-edit-log.json) and final root checks report 2,050 passes; final ERC remains **7 errors / 4 warnings**. No design file was edited by this review.

## Firmware and readiness limits

NC markers do not configure a GPIO input buffer, pull, peripheral multiplexer, eFuse or power state. D4 recommends appropriate external or software-enabled pulls for genuinely unused high-impedance inputs to avoid excess current. An F18 firmware pin-state policy is still required; it must **not blanket-reset all 26 GPIOs**, because memory, UART, USB, boot and onboard RGB roles may remain active internally.

This static review does not qualify actual boot behavior, powered logic margins, synchronization, USB/battery source interactions, analog performance, RF/thermal behavior or wearer safety. It does not close F06/F09/F18/F19 or justify initial power-up/human-worn testing.

