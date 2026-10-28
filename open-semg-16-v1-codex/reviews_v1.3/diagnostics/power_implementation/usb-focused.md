# Focused implementation gate: DevKit, USB and reverse current

27 October 2026. Read-only focused assessment of the proposed MAIN_3V4 interface. No schematic or physical-board changes performed.

## Decision

**The unchanged proposal cannot pass a requirement to verify electrical USB/backfeed prevention.** The architecture report proposed a mechanical unseating/exclusion contract; the current schematic does not implement that mechanical feature or electrical source isolation. It must not be relabeled as a verified no-backfeed circuit.

This is an evidence/design gate, not a claim that a stock DevKit has already failed or been damaged. Whether to pause all schematic implementation or complete independent work must follow the user's exact conditional authorization.

## Manufacturer check

The [SGMICRO SGM2212 datasheet, July 2023 Rev.A.2](https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf), p.3, gives VIN-to-GND absolute maximum 22 V and operating VIN 2.7–20 V. It does **not** establish an output-to-input absolute maximum of VIN+0.3 V, a reverse-current blocking guarantee, or a guaranteed externally driven output condition with VIN absent. Do not transfer TI TLV755P's output bound to this part. Absence of that specification proves neither safe operation nor a specific damage mechanism/current magnitude.

The [official DevKit guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#power-supply-options) allows nominal 3V3-header powering as one of three mutually exclusive methods; USB and 5V-header sources must be excluded in that mode. This supports the normal nominal-3.3-V use case of a matching assembly. It does not establish the proposed 3.4 V assembly-wide voltage qualification or safe simultaneous-source/hotplug states on an unidentified installed board.

The [official V1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf), p.2, identifies SGM2212 as board U2 with VIN3, GND1, VOUT2 and VOUT tab4. These are board-internal references, not carrier U2. In an unmodified matching board, its regulated output reaches the external 3V3 supply domain. The carrier cannot remove that internal path by leaving U3.21 or USB data header branches unconnected.

WROOM and CP2102N VDD voltage ranges include 3.4 V. They do not establish SGM2212 absent-input reverse behavior, all fitted board loads, or USB source separation.

## Why simple carrier additions do not close the gate

| Candidate change | What it can establish | Remaining issue |
|---|---|---|
| MAIN-to-U3.1/.2 series diode or reverse-blocking switch | With correctly selected device/conditions, blocks current from DevKit 3V3 back into MAIN | Does not isolate the DevKit's own LDO output from external battery drive, guarantee source overlap behavior, or remove internal USB paths. A plain diode also spends voltage margin. |
| Turn converter EN off when USB is detected | Can request shutdown after a detected event | EN is not inherently reverse blocking; startup/hotplug races and stored charge remain. Actual USB-detection node and source paths must be known. |
| External power mux at U3.1/.2 only | Can choose external sources on its controlled pins | The DevKit's internal USB-to-LDO output path bypasses an external mux unless deliberately disconnected or incorporated into the design. |
| VBUS-cut cable | Removes one cable conductor if it is correctly built | Does not qualify bridge/native-USB attach behavior, both sockets, other cables, absent-supply GPIO paths or the onboard LDO reverse condition. |
| Feed a boost into U3.21 only | Avoids externally driving the DevKit LDO output | USB exclusion/isolation is still required. The guide calls USB and 5V-header inputs mutually exclusive; the actual diode/bridge/native-USB paths require board verification. Also changes conversion losses, main voltage, AFE headroom and thermal budget. |
| Remove DevKit from carrier before USB | Physically removes all power/GPIO paths **when actually removed** | Requires a real removable socket/enclosure arrangement and verification; it is an operating/mechanical contract, not current electrical isolation. It does not independently qualify 3.4 V battery powering into the stock LDO output. |

A correctly specified reverse blocker at the MAIN-to-DevKit boundary, together with complete power-off-tolerant signal isolation and no alternate supply connection, **can** prevent USB-derived current returning to MAIN/the battery. That narrower result is technically possible without interrupting the internal USB source itself. It does not establish the direct-3.4-V onboard-regulator drive condition, source overlap on the DevKit rail, board-load voltage qualification or complete assembly behavior. Do not confuse these distinct claims.

A switcher operating in forced PWM can accept reverse energy; the earlier TPS63802 choice therefore makes explicit backfeed handling especially relevant. Current-limited laboratory measurements cannot substitute for a missing semiconductor guaranteed condition when making a broad safe-mode claim.

## Smallest defensible correction paths

**Retain the proposed efficient direct-header architecture:** specify an exact DevKit revision/SKU and a verified modified assembly that disconnects every internal source capable of driving the 3V3 domain. For the matching official reference, that includes the regulator VOUT pin and tab, not only its VIN. Confirm the bridge VDD/VREGIN, onboard links, USB VBUS and UART/USB signal paths; a presumed regulator removal alone is not full proof. Use an explicit modified-assembly symbol/BOM and a validated service/source circuit. Actual component/link identity and physical modification evidence are required before pin-level instructions are final.

**Retain an unmodified DevKit:** keep its official nominal external 3.3 V input mode and enforce the proven mechanical USB exclusion/unseating arrangement, then choose an independent analog conversion path if 3.3 V leaves inadequate quiet-LDO headroom. This can satisfy a prevention requirement only if the user accepts and the actual mechanical design verifies that method. It still does not provide electrical tolerance of USB inserted while seated.

**Require electrical protection for inserted USB while seated:** redesign around the verified actual board power paths, or replace the MCU assembly with one whose complete source selection is controllable. A higher-voltage battery converter feeding a reverse-blocked 5V domain is a possible architecture to evaluate, but its USB-side reverse paths, host VBUS, onboard LDO thermal load and AFE supply all need fresh calculations. It is not a drop-in one-component correction to the approved 3.4 V direct-header tree.

## Required evidence before this interface can pass

- Actual board manufacturer, revision, module SKU and fitted regulator/bridge/LED identities; matching full board schematic/netlist or verified continuity mapping.
- Chosen power-mode requirement: mechanical exclusion with detached service, or electrical tolerance of seated USB insertion. These are distinct requirements.
- If modified, exact source-path disconnection drawing/BOM and physical verification, including regulator output tab and all parallel links/bridge paths.
- Source-pair analysis for battery/USB absent, present, ramping and removed; specified blocking components and worst-case leakage/transient limits; no powered signal injection into absent rails.
- Measured current-limited verification of the assembled implementation after schematic/netlist review. No human wearer attached during those tests.

The current V1.3 channels and historical revisions remain unchanged. F17 remains open; missing source qualification must not be hidden by fewer ERC reports.
