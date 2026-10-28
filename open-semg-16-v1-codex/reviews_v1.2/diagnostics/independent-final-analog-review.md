# Independent final analog review — V1.2

27 October 2026. Read-only review of the actual [V1.2 schematic](../../v1.2/open-semg-16-v1.2.kicad_sch), [final native netlist](final-netlist.xml), [initial native netlist](initial-netlist.xml) and [recovery schematic](baseline/open-semg-16-v1.2.kicad_sch). The review follows the original F01–F21 diagnoses and the prior implementation report; it does not repeat the comprehensive V1 audit.

**Result: no analog connectivity regression or incorrect requirement field was found in the reviewed source.** The changes define missing component requirements and add three passive control elements. They do not demonstrate acquisition performance, component qualification or wearer safety.

## Independent checks

KiCad S-expressions and native XML were parsed independently of the implementation's validation script. The source remained hash-identical during this review. Checks confirmed:

- All 416 original component-pin entries retain their original net memberships when the three added resistor terminals are excluded from comparison. This compares connected terminal sets, rather than relying on visible net names.
- All 16 electrode pairs retain terminal 1 to the corresponding positive ADC input through the odd-numbered resistor and terminal 2 to the negative input through the even-numbered resistor. All 32 ADC-side nets retain exactly their original ADC pin, resistor terminal and capacitor terminal. No channel crossover, polarity reversal, short or open was found.
- All 57 original capacitors retain both original connected terminals. Both independent 100 nF/10 µF reference pairs, all VCAP networks and their AGND returns are preserved. C25/C51 remain separate 1 µF VCAP3 bypass networks with their original TP10/TP15 access.
- Every original component retains its nominal value and footprint field. Component count is 130 initially and 133 finally; the only additions are R36/R37/R38. No selected MPN or new footprint is claimed by the requirements.
- All eight explicit NC markers and the complete embedded symbol-definition block are byte-identical to the recovery schematic. RLDREF60, RLDINV61, RLDOUT63 and WCT64 remain disconnected on both ADCs; no body-connected circuit was added.
- The actual schematic fields agree with the exported fields for all 32 input capacitors, R1–R32, C25/C51 and C55. These checks included 646 targeted scalar assertions, together with the original-net-membership comparison and source/backup checks.

## Requirement-field assessment

| Item | Verified final requirement | Assessment |
|---|---|---|
| All 32 input shunts | 620 pF retained; C0G/NP0; 1% tolerance; qualification text explicitly leaves electrode CMRR unverified | Consistent with the original mismatch/derating concern. The dielectric and tolerance are selected engineering specifications, not a new manufacturer mandate or measured CMRR result. |
| R1–R32 | 2 kΩ retained; 0.1% tolerance; at least 0.1 W with temperature/pulse qualification; explicit wearer-protection limitation | Reasonable specification of previously unspecified properties. It does not select a component or establish a fault-current limit. |
| C25/C51 | 1 µF retained; voltage rating at least 10 V; selected-part qualification at approximately 5.2 V including bias, tolerance and temperature | Consistent with ADS1298 pin 55's AVDD+1.9 V bypass-node description. The rating includes nominal voltage margin; effective capacitance, internal-node excursions and actual part suitability remain unqualified. No existing overstressed capacitor is assumed. |
| C55 | 10 nF retained; leakage below 100 nA at operating bias/temperature; exact MPN pending | Consistent with LP2985 §7.1.3. The requirement is stricter than the manufacturer's 100 nA upper boundary; compliance requires selected-part evidence. |

The calculations and manufacturer/local references are recorded in [analog-decision-evidence.md](analog-decision-evidence.md). The ideal-source matching calculation is a component-tolerance screen only. The 5 V / 2 kΩ = 12.5 mW resistor screen is unrelated to proving acceptable wearer current.

## Added passive controls and remaining blockers

R36 is 10 kΩ from MOSI/DIN to AGND; R37 is 10 kΩ from SCLK to AGND. Their added terminals preserve all existing SPI endpoints and all analog acquisition nets. They provide passive low bias only under the stated high-impedance/no-opposing-drive condition; this analog review does not establish complete controller reset behavior, noise margin, bus edge quality or power sequencing.

R38 is a fitted 0 Ω development OFF strap from the shared regulator EN net to AGND. It defines an OFF state rather than enabling the still-paralleled outputs. It does not isolate those outputs, eliminate reverse-current paths, qualify a power source or establish safety under external DevKit power. It is not an operational power-architecture solution.

F12/F14 are partial requirements improvements; actual parts, bias/temperature curves, matching, noise and fault/pulse qualification remain open. F07/F08 remain unresolved because a protected bias architecture, contact/body/cable model and full normal/single-fault external-interface assessment are missing. F10 still needs representative offset/common-mode/motion measurements and a gain/clipping policy. F11 still needs an accepted passband/noise/transport decision and firmware implementation. F19/F20/F21 still require physical parts, layout, test-pad qualification and measurements. No power-up or human-worn readiness follows from these static checks.

## Reviewed source identity

- Schematic SHA-256: `7efd6a06e2ac45a553e7731665950c98c9a680dd36da6db584a826dc016e9494`
- Final netlist SHA-256: `b7259f146fdcd87fa9a245c18484b1d68a350c542bc523589a5f772e5b82b7a8`
- Initial netlist SHA-256: `7a5a1d9e6d083c6c5821e3703dfdf9426e39640997cd156fe0bf456346f28137`

The final netlist identifies the actual V1.2 schematic as its source. Only this review document was created by the independent final review; no schematic or other design source was edited.
