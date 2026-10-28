# V1.2 analog and passive-component decision evidence

27 October 2026. Scope: outstanding F07/F08/F10/F11/F12/F14/F19/F20/F21, using the [original review](../../reviews_v1/full_review.md) and [V1.1 implementation report](../../reviews_v1.1/updates_from_v1.md). This note records proposed component requirements and their limits. It does not select an actual manufacturer part, change a schematic, establish a performance result, or qualify wearable use.

## Verified starting connections

The supplied [initial native netlist](../initial-netlist.xml) confirms:

- C25 is 1 µF between `/VCAP3_ADC1` and AGND. The non-return net contains only C25.1, U1.55 and TP10.1. C51 is the equivalent independent 1 µF network with U2.55 and TP15.1.
- C55 is 10 nF between U4.4/BP and AGND. Its BP net contains only U4.4 and C55.1.
- C19/C20 and C45/C46 remain separate 100 nF/10 µF reference pairs, each returned to AGND. No reference outputs are joined.
- Each ADC retains 22 µF at VCAP1 and 1 µF at VCAP2/3/4, with AGND returns. These nodes have diagnostic test points, not external power loads.
- All 32 input shunt capacitors are 620 pF to AGND. Their references are C1–C5, C10–C18, C21/C22, C27–C31, C36–C44 and C47/C48. Each ADC-side input net retains its own series 2 kΩ resistor from R1–R32.
- Both ADCs retain explicitly disconnected RLDREF60, RLDINV61, RLDOUT63 and WCT64. RLDIN62 remains tied to the same supply net as actual AVDD in this baseline. No body-bias contact or feedback loop exists.

## Requirements justified without an architecture change

| Components / findings | Proposed requirement fields | Basis and qualification boundary |
|---|---|---|
| C25/C51; F14 | `Voltage_Rating_Min = 10 V`; retain `Value = 1uF`; require recorded DC-bias/effective-capacitance qualification at approximately 5.2 V, with tolerance, temperature and aging considered | ADS1298 pin 55 is an internally elevated bypass node. The voltage requirement is an engineering selection with margin, not a TI requirement for a particular 10 V part. A voltage rating alone does not establish usable capacitance or a qualified capacitor. |
| C55; F14 | Retain `Value = 10nF`; `Leakage_Max < 100 nA` at the actual bypass operating conditions | LP2985 §7.1.3 sets a 100 nA upper leakage boundary for this bypass function. The proposed strict inequality preserves margin at the boundary. Any final part must substantiate the limit; a generic ceramic description does not. C0G is an acceptable dielectric selection, but not an additional manufacturer mandate. |
| All 32 input 620 pF shunts; F12/F14 | `Dielectric = C0G/NP0`; `Tolerance = +/-1%`; retain nominal value and connections | Original review §5.4 identifies component mismatch and electrode impedance as separate causes of common-to-differential conversion. C0G avoids class-II DC-bias/aging behavior. The 1% tolerance is the selected engineering specification; it is not mandated by ADS1298 or a demonstrated wrist-CMRR requirement. |
| R1–R32; F12/F14 | `Tolerance = +/-0.1%`; `Power_Rating_Min = 0.1 W`; retain 2 kΩ nominal and connections | These are selected engineering specifications that bound previously unspecified matching and ordinary dissipation. Temperature derating, working voltage, pulse capability and exact physical part remain to be checked. They are not a wearer-protection design. |

No MPN, footprint, procured assembly, matched-array behavior or guaranteed effective capacitance is implied by these fields. F12/F14/F19 cannot be closed by adding them alone. Input topology, nominal RC values, sampling configuration, voltage-reference networks and VCAP topology/nominal values remain unchanged by the proposal.

## Calculations and electrical consequences

**VCAP3:** the ADS1298 TQFP pin table gives the internal node approximately 1.9 V above AVDD. Therefore the C25/C51 operating voltage relative to AVSS is approximately `3.3 + 1.9 = 5.2 V` for the intended nominal analog supply. The proposed 10 V minimum rating is approximately 1.92 times that nominal voltage. If a later architecture used the ADC's 5.25 V maximum recommended analog span, the corresponding nominal calculation would be 7.15 V; that is a future qualification condition, not the present rail. The internal-node approximation is not a guaranteed transient maximum. A candidate capacitor still needs a bias curve, tolerance/temperature/aging assessment and bypass-function qualification against the manufacturer's 1 µF recommendation. Do not infer effective 1 µF from a nominal 1 µF marking or a 10 V voltage rating.

**Matching screen:** nominal `RC = 2000 x 620 pF = 1.24 us`; `fc = 1/(2*pi*RC) = 128.35 kHz`. Opposing extremes of the selected 0.1% resistor and 1% capacitor tolerances give normalized time constants `(1.001)(1.01) = 1.01101` and `(0.999)(0.99) = 0.98901`. Their difference is 2.2% of nominal. Using the original review's low-frequency, ideal-source model at 60 Hz gives `-20*log10(2*pi*60*1.24e-6*0.022) = 99.76 dB` component-only rejection. This is a calculation about tolerance bounds, not a predicted or measured system CMRR. Complex, unequal electrode impedance, body bias, protection and PCB coupling remain outside this screen.

**Resistor screen:** the original review's illustrative 5 V entirely across 2 kΩ gives `I = 2.5 mA` and `P = 12.5 mW`. A nominal 0.1 W rating is eight times that screen before temperature derating. This does not establish that such a fault occurs, that the part tolerates an ESD pulse, or that 2.5 mA is acceptable through a wearer. Complete parallel paths and normal/single-fault safety analysis remain necessary.

## Decisions that remain unresolved

- **F07/F08:** protected passive bias and one compensated RLD are materially different viable approaches. The electrode/body/cable impedance model, chosen contact, external-power states and fault-current requirements are unavailable. No safe drive resistor, feedback compensation or protection network can be inferred merely from an ADC application example. Leave the existing unused RLD/WCT disconnections intact until that design is supported and validated.
- **F10:** the direct-coupled front end must accommodate contact DC offsets, common mode and motion excursions simultaneously. Neither a new high-pass topology nor a gain selection follows without representative measurements and a clipping/recovery policy.
- **F11:** selecting 2 or 4 kSPS requires an accepted passband attenuation/noise/transport policy. The reviewed sinc-cubed filter results remain approximately -8.26 dB and -1.97 dB at 850 Hz respectively; no rate is selected here.
- **F19/F20/F21:** procurement identities, component/connector footprints, PCB geometry, thermal/RF behavior, test-pad loading and assembled probe access require further physical design and verification. The existing schematic probes provide logical access only.

## Primary manufacturer references

- [TI ADS1298 SBAS459K, local original](../../../docs/datasheets/originals/components/ADS1298.pdf), pp.10–11 pin assignments/bypass values, p.32 headroom, p.49 digital filter; [official PDF](https://www.ti.com/lit/ds/symlink/ads1298.pdf). The VCAP3 voltage calculation follows the pin description; it is not a measured rail voltage.
- [TI LP2985 SLVS522S, local original](../../../docs/datasheets/originals/components/LP2985.pdf), §7.1.3 p.21, bypass capacitance/leakage; [official PDF](https://www.ti.com/lit/ds/symlink/lp2985.pdf).
- [TI SBAA188B, local original](../../../docs/datasheets/originals/ti-app-notes/SBAA188.pdf), pp.3–6 mismatch, bias and RLD stability/disconnection; [official PDF](https://www.ti.com/lit/an/sbaa188/sbaa188.pdf). Its ECG examples do not define this product's safety classification or fault-current target.
- [Murata primary dielectric/DC-bias guidance](https://www.murata.com/en-us/support/faqs/capacitor/ceramiccapacitor/char/0005) and [dielectric characteristics](https://www.murata.com/en-us/support/faqs/capacitor/ceramiccapacitor/char/0030), consulted 27 October 2026, support C0G selection and the need to distinguish nominal from effective capacitance.

Only this evidence document was created by this investigation. No schematic, historical revision, previous review or manufacturer document was modified.
