# Updated DevKit implementation gate — accepted mechanical USB exclusion

27 October 2026. This update supersedes the blocking conclusion in [usb-focused.md](usb-focused.md) **for the revised nominal-3.3-V MCU architecture described here**. The earlier note remains applicable to the abandoned 3.4-V stock-board interface and to claims of electrical seated-USB tolerance.

## Decision: pass for schematic implementation, with explicit design requirements

The user has explicitly accepted that both USB sockets are physically inaccessible while the stock DevKit is mounted, and USB service requires removing the DevKit from the carrier. With that accepted mode contract, a nominal **3.3 V** TPS63802 supply feeding the stock board's **3V3 headers** is a manufacturer-supported architecture. Separate battery-fed AFE conversion followed by LT3042 at the already-proposed 2.98 V avoids requiring 3.4 V at the DevKit.

The [official Espressif guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#power-supply-options) explicitly permits external 3V3-header powering when USB/5V-header powering is excluded. Thus lack of a separate SGM2212 reverse-current guarantee does not by itself block use of that supported stock-board mode. It does not prove electrical tolerance of prohibited source combinations.

Specify the intended assembly as a procurement/design requirement before schematic release: genuine Espressif ESP32-S3-DevKitC-1 **board revision V1.1**, matching the [2022-11-30 reference schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf), with an explicit WROOM module SKU consistent with firmware/memory requirements. For example, N8R8 is a possible selection if 8 MB flash/8 MB octal PSRAM meets those requirements; GPIO35–37 remain unavailable and GPIO38 is the board RGB control, none of which changes the existing GPIO6–14 acquisition interface. Do not imply that a SKU alone guarantees the board revision.

Physical board identification and continuity checks can occur before the first hardware power test; the lack of an already-installed board does not prevent selecting the exact intended assembly in the schematic/BOM now.

Required schematic/assembly notes and verification:

- MAIN nominal 3.3 V to both U3.1/.2, common AGND; U3.21 has no external source. No USB while seated. Keep RGB disabled for acquisition.
- Real socket/enclosure arrangement prevents access to **both** USB connectors while seated. Battery OFF/disconnected and DevKit unseated before USB service. USB powers only the detached board.
- No charger, debugger or alternative power cable while worn. Pack charging remains disconnected and off body.
- The separate AFE converter can target 3.8 or 4.0 V followed by LT3042 at 2.98 V, after its own voltage tolerance/current/stability checks. Its input/output supply must not connect to U3 3V3 or 5V accidentally. This creates materially more LDO headroom; switching/noise and sequencing still require qualification.
- Verify complete-board 3V3 extrema remain within the WROOM 3.0–3.6 V operating range, including connector/wiring drop and RF transients. Budget a source capable of at least 500 mA for the module plus actual board loads; converter switch-current rating is not its deliverable output rating.
- No electrical seated-USB fault tolerance, galvanic isolation or safe wearer operation follows from this mechanical source-prevention contract.

An additional MAIN-to-DevKit reverse blocker is optional fault containment, not necessary to satisfy the accepted operating mode. It adds loss, capacitance/startup behavior and reverse-leakage analysis, and would not authorize seated USB insertion. Avoid adding it merely to simulate support for a prohibited mode.

No schematic edits were made by this reviewer. Existing safety, PCB, supervisor/readiness, ADC startup and hardware validation gates remain independent requirements.
