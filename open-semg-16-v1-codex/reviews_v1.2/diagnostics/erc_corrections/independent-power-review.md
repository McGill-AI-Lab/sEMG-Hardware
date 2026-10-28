# Independent power and analog review of ERC corrections

27 October 2026. Read-only review of the actual V1.2 schematic and this directory's initial/final native netlists and ERC reports. No design edits were made by this reviewer. The only file created is this review.

Final reviewed schematic SHA-256: `202b2b320076c5e802f55e6ed566ae640cb948c6544777b9d51b11222e371208`.

The initial independent review covered source `c70cce6a7f7677ccb413ca9a73af67c5e9f39819fecc1eee2636885cd3ec2529`. A subsequent complete-source comparison against `before-label-presentation.kicad_sch` verifies exactly one replacement: global +3.3V label UUID `75fc8b9d-1b77-49f1-bb82-13b6eff87138` changes orientation 180°→0°, font 1.27→1.0 mm and justification right→left. Its name and attachment remain +3.3V at (209.55,160.02) mm. No other source bytes change. This improves CLKSEL/START label clearance without changing connectivity. The regenerated [final validation](final-validation.json) passes all **2,050 assertions**, with ERC still seven errors and four warnings; the power/analog conclusions below remain valid.

## Result

**The diagnosed F04 direct parallel-output connection is corrected.** U4's output and its own C54 bypass form a separate, unloaded local net. U5 remains attached to the existing system rail. No unintended power or analog connectivity regression was found in the comparison. This conclusion applies to the schematic mechanism; it does not qualify a functional power supply or establish readiness for power-up or wearer use.

The current schematic replaces the former #PWR069 +3.3V global connection with a local `LP2985_OUT_DISABLED` label at (147.32,269.24) mm. This is a real disconnection of the U4 branch from the common rail, not an ERC pin-type change or suppressed conflict. The existing U4-to-C54 wire remains.

## Independent netlist checks

| Item | Verified final state |
|---|---|
| U4 output branch | `/LP2985_OUT_DISABLED` contains exactly U4.5 and C54.1. |
| Main +3.3V membership | Exactly its baseline membership minus U4.5 and C54.1. No ADC supply, auxiliary tie, MCU supply or system bypass was reassigned. |
| Only original pin-to-net changes | U4.5 and C54.1: +3.3V → /LP2985_OUT_DISABLED. All other original represented pin assignments remain unchanged. |
| Components | All 133 component values, footprints and library identities match the baseline native netlist. |
| Enable inhibit | `/EN` still contains only U4.3, U5.3 and R38.1. R38 remains value 0, fitted (`dnp no`), with pin 2 at AGND. Both regulators remain deliberately OFF in the intended static state. |
| Input and return nets | +3.7V and AGND memberships are unchanged. U4/U5 still share input and return; the separate output branch is not galvanic isolation. |
| Digital constraints | MISO, both CS nets and ADC_CLK retain exact baseline memberships. No changed clock, select or bus architecture is inferred. |
| Analog constraints | ADC supplies/returns, auxiliary-to-actual-AVDD ties, all acquisition mappings, independent references and VCAP connections are preserved by the exhaustive original pin comparison. |

C54 remains 2.2 µF from U4's separate output to AGND. The remaining main-rail nominal bank is:

`C6+C7+C8+C9+C32+C33+C34+C35+C57 = 0.1+10+0.1+10+0.1+10+0.1+10+200 = 240.4 µF`.

This is 2.2 µF less than the former 242.6 µF common bank and still excludes DevKit capacitance. F13 remains an effective-capacitance/ESR/startup/stability qualification issue; no oscillation or measured transient is asserted.

## ERC interpretation and preserved findings

Final native ERC is 11 records: seven errors and four warnings. The original U4.5/U5.5 power-output conflict is absent. All seven previously classified valid-topology/source-model reports and all three evidence-dependent reports retain their electrical meaning:

- AGND and +3.7V source-model reports, shared DOUT, +5V and both CHIP_PU records match their original records exactly.
- The four TEST/PACE warnings retain the same ADC pins, severity, diagnosis and aux-to-actual-AVDD ties. Their other reported pin changes from U4.5 to U5.5 because U4 is now disconnected from that rail. This is an expected, justified representative change caused by the real F04 correction, not a modification to the sanctioned ties or an additional electrical fault.
- The remaining GPIO3 unconnected report is outside those ten protected diagnoses. It was deliberately deferred pending the separate pin/strap evidence; this review does not claim all 27 unused-pin reports were resolved.

No power flag, pin electrical-type change, functional enable source or new source-isolation component was introduced. The three evidence-dependent findings were not resolved by assertion.

## Manufacturer requirements and remaining limits

The [LP2985 datasheet](../../../../docs/datasheets/originals/components/LP2985.pdf), §§6.3.1 and 7.1.2.2, supports keeping the enable low and retaining an output bypass. Legacy silicon requires effective output capacitance and ESR qualification; C54's nominal 2.2 µF is not proof that its selected part would satisfy those requirements. The full LP orderable/silicon and C54 part remain unspecified. Keep U4 disabled until these requirements and its intended future use are resolved. [Official LP2985 datasheet](https://www.ti.com/lit/ds/symlink/lp2985.pdf).

The [TLV755P datasheet](../../../../docs/datasheets/originals/components/TLV755P.pdf), recommended operating table p.4, specifies a 1–200 µF output-capacitance range. The 240.4 µF nominal system bank therefore still needs the existing F13 effective-capacitance and stability assessment; removing U4 does not qualify U5 for the RF load. Its DBV thermal/transient margin, battery window, source capability and reverse-current behavior remain F15/F16/F17 work. [Official TLV755P datasheet](https://www.ti.com/lit/ds/symlink/tlv755p.pdf).

R38's OFF state does not prevent external USB/5V/3V3 power from biasing the system output. Disabled U5 discharge and output-above-input exposure remain relevant. The source/USB architecture, functional enable sequence and cell qualification are unresolved. Missing protected body bias and wearer protection remain F07/F08. F01–F03's original wiring repairs remain preserved; no powered-voltage, analog-performance or safety conclusion follows solely from this ERC reduction.
