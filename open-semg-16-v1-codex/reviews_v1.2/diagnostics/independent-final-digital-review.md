# Independent final digital review — V1.2

27 October 2026. Read-only design review of the current `v1.2/open-semg-16-v1.2.kicad_sch`, [final native netlist](final-netlist.xml), [initial native netlist](../initial-netlist.xml), and initial/final ERC artifacts. No schematic edits performed. The earlier [decision evidence](digital-decision-evidence.md) documents electrical calculations and manufacturer sources; this note independently checks the resulting implementation.

**Result: no unintended digital or acquisition connectivity regression found.** This is a static review, not powered or firmware qualification.

| Component | Confirmed final value/properties | Confirmed endpoints |
|---|---|---|
| R36 | Device:R, 10 kΩ, tolerance 1%, fitted | Pin 1 `/MOSI`: U1.34, U2.34, U3.17 GPIO11; pin 2 AGND |
| R37 | Device:R, 10 kΩ, tolerance 1%, fitted | Pin 1 `/SCLK`: U1.40, U2.40, U3.18 GPIO12; pin 2 AGND |
| R38 | Device:R, 0 Ω, fitted development OFF strap | Pin 1 `/EN`: U4.3/U5.3; pin 2 AGND |

The schematic parses with the KiCad-aware source reader. All three symbols have valid V1.2 instances, `dnp no`, `in_bom yes`, and `on_board yes`. Their wire endpoints meet the resistor pins, the three signal labels meet their intended wire ends, and the common return has a global AGND label. The native netlist confirms that return is the actual ADC/MCU/battery ground, rather than a newly isolated local net. The block lies within the A2 sheet. These checks do not select footprints or demonstrate assembled access.

Independent set comparisons establish:

- All **416 baseline component-pin net partitions** remain unchanged when the three added resistor components are excluded.
- All **32 ADC acquisition input-net memberships** remain exactly unchanged. This preserves all 16 channel mappings and electrode polarity from the validated baseline.
- MISO and both CS nets retain exactly their prior terminals. Shared START/RESET/PWDN retain their existing R33/R34/R35 connections without modification.
- `ADC_CLK` still contains only U1.37/U2.37/TP1; U1 CLKSEL52 remains on its DVDD net and U2 CLKSEL52 on actual ground. Both DRDY nets remain distinct.
- Both reference networks remain separate. All VCAP networks, return terminals and nominal capacitor values remain unchanged.
- For the hardware additions, only R36.1 joins MOSI, R37.1 joins SCLK, R38.1 joins EN, and their pin-2 terminals join AGND.

Initial native ERC is **35 errors + 26 warnings**; final native ERC is **34 errors + 26 warnings**. The reduced undriven-enable report does not establish a functioning power architecture or correct digital startup. The root validation separately examines complete ERC identities and protected file hashes.

R36/R37 implement the intended low defaults under the documented high-impedance MCU condition. Their nominal high-state load is 0.33 mA each, up to 0.66 mA together; at 3.3 V with the 1% low-resistance endpoint, the pair draws approximately 0.667 mA. No material static conflict is introduced. Loaded high-level noise margin, SCLK edges, startup transients and absent-supply behavior remain unmeasured. The original table-bound ESP-to-ADS high-level margin was already zero at equal nominal rails; the added loads do not justify a new positive-margin claim.

R38 deliberately holds both existing regulators disabled. It removes floating EN as a development state while leaving the parallel outputs and operational enable architecture unresolved. Do not apply an external EN driver against the fitted strap. It is neither source isolation nor protection against USB/external-rail backfeed; disabling a regulator does not make an externally powered output harmless. Its power consequences require the power review.

**Remaining digital limits:** F09 remains partial because CS default behavior, driven MCU startup glitches, complete supply sequencing and nonoverlap selection are unresolved. F06 remains partial because firmware must establish the master clock and slave initialization and bench testing must demonstrate sample alignment. F18 remains firmware work: reference settling, gain/rate, safe optional modes, grounded GPIO policy, frame timing, register readback and recovery. No sample-rate, reference, body-bias or protection architecture was inferred from these checks.
