# Independent final power review — V1.2

27 October 2026. Scope: targeted review of the V1.2 changes against the V1 audit and V1.1 implementation report; no comprehensive re-audit. Evidence: [initial netlist](initial-netlist.xml), [final netlist](final-netlist.xml), current V1.2 schematic, [final validation](final-validation.json), and the manufacturer documents cited below.

**Result:** no unintended supply/return connectivity change was found. R38 deliberately holds the still-paralleled carrier regulators OFF. This is partial F05 containment, not a working power architecture or a readiness approval. F04 remains unresolved.

The reviewed schematic SHA-256 is `7efd6a06e2ac45a553e7731665950c98c9a680dd36da6db584a826dc016e9494`. The reviewed final-netlist SHA-256 is `b7259f146fdcd87fa9a245c18484b1d68a350c542bc523589a5f772e5b82b7a8`.

## Verified connections and changes

- `+3.3V` and `+3.7V` have exactly their initial V1.2 pin memberships. U4.5 and U5.5 remain paralleled on `+3.3V`; U4.1/U5.1 remain on the battery-labelled `+3.7V` net.
- U1/U2 AVDD19/21/22/56/59, AVDD1 54, DVDD48/50 and unused analog ties 17/18/62 remain on `+3.3V`. Physical analog/digital grounds, VREFN, MCU grounds and battery negative remain on `AGND`. The V1.1 F01–F03 repairs are preserved.
- `/EN` retains U4.3/U5.3 and adds only R38.1. R38.2 joins `AGND`. The schematic specifies R38=0, `in_bom yes`, `on_board yes`, `dnp no`, and describes a fitted removable development OFF strap. No enable driver was added.
- R36.1 joins only the existing MOSI/DIN net; R37.1 joins only the existing SCLK net. Their respective second pins join `AGND`. The complete additions to `AGND` are R36.2/R37.2/R38.2; no original terminal was removed.

With the specified R38 fitted, the EN terminals have a conductive return to actual regulator ground and are biased OFF rather than floating. LP2985's specified full-temperature OFF level is at most 0.15 V; TLV755P's OFF level is at most 0.3 V. A hard strap avoids depending on an unspecified maximum TLV755P EN leakage. It must remain fitted until F04/F05/F17 receive a complete source/control design; simply removing it restores the unresolved enable state. An external source must not drive the strapped EN net. [LP2985 pp.7,16](https://www.ti.com/lit/ds/symlink/lp2985.pdf), [TLV755P pp.6,12](https://www.ti.com/lit/ds/symlink/tlv755p.pdf)

The two new 10 kΩ signal pulldowns add at most 0.66 mA nominal static load if both signals are held at 3.3 V, approximately 1.09 mW in each resistor. Actual switching-average load depends on firmware activity. These currents do not establish source or logic-waveform qualification.

## Remaining power consequences

R38 is not supply isolation. External DevKit USB/5 V power can still bias the common 3.3 V output rail. When input power is sufficient for its discharge circuit, disabled U5 has a typical 120 Ω output-to-ground discharge path; an externally maintained 3.3 V rail would therefore incur an illustrative 27.5 mA discharge load. With battery input absent or collapsing, output-above-input reverse-current exposure also remains. LP2985 new silicon has an output-discharge function, but the fitted silicon remains unspecified. No USB/battery combination is approved. [TLV755P pp.12,17–18](https://www.ti.com/lit/ds/symlink/tlv755p.pdf), [LP2985 pp.16,21–22,30](https://www.ti.com/lit/ds/symlink/lp2985.pdf)

The output bank remains C6/C7/C8/C9/C32/C33/C34/C35/C54/C57 = 242.6 µF nominal, excluding DevKit capacitance. F13 remains an effective-capacitance/ESR/startup qualification concern; oscillation was not demonstrated. F15 battery window/cutoff, F16 DBV thermal/RF-load qualification and F17 source isolation remain unresolved. Espressif lists USB, 5 V header and 3V3 header power as mutually exclusive choices. [Official DevKit guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html)

The final recorded validation passes 1043 assertions; ERC reports 34 errors and26 warnings, compared with 35 errors and26 warnings initially. This review independently checked the above native-netlist memberships and capacitor sum. It did not measure rail behavior, assemble R38, exercise USB, qualify components, inspect a PCB, run firmware, or verify wearer safety. The device remains unqualified for initial power-up and human connection.

No schematic, project, prior revision, prior review or datasheet was changed by this independent review. Its sole created file is this diagnostic note.
