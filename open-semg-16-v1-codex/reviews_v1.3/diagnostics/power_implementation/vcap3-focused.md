# Independent VCAP3 bypass candidate verification

27 October 2026. No active schematic edit. This note supports preparing a candidate only while active-project confirmation and final power/USB decisions remain unresolved.

The actual local ADS1298 SBAS459K original PDF was rendered and visually inspected on printed p.97. [Rendered page](ads1298-page97.png) shows Figure 106 placing **1 µF and 0.1 µF in parallel from VCAP3 to AVSS**. Figure 107 uses the same pair. The TQFP pin table on p.11 identifies VCAP3 as pin 55, with a 1 µF bypass to AVSS. The optional 100 nF addition therefore follows a manufacturer reference; it does not establish that the current 1 µF-only circuit fails.

A bounded candidate adds one 100 nF capacitor from U1.55 `/VCAP3_ADC1` to AGND and another from U2.55 `/VCAP3_ADC2` to AGND. Retain existing C25/C51 = 1 µF and their ≥10 V requirements, all original net partitions except these added passive endpoints, all 16 acquisition channels, controls, shared cascade MISO, references and VCAP nodes. Keep R38 fitted and both regulators OFF. No part of this change authorizes power-up.

These new capacitors are on internal charge-pump nodes, not directly across the regulator output. The direct main bank remains **240.4 µF nominal**; indirect charge-pump startup load increases slightly. Their physical loop must be short to pin55 and its analog return; schematic-only presence does not establish useful high-frequency bypassing.

VCAP3 is described as internally generated AVDD + 1.9 V. At 3.3 V AVDD, that is approximately5.2 V; at maximum recommended analog span5.25 V, approximately7.15 V. **7.15 V is a nominal projection, not a guaranteed VCAP3 maximum**, because1.9 V is not specified as a worst-case limit or an overshoot bound. A 50 V C0G part has substantial voltage margin for these normal-use projections and avoids the voltage-dependent capacitance/microphonics concerns of ferroelectric dielectrics.

Candidate MPN: **KEMET C1206C104J5GACTU**, 1206,100 nF,±5%,50 V,C0G, matte-Sn termination,7-inch reel. The [manufacturer C1003_C0G family datasheet dated20 February2025](https://content.kemet.com/datasheets/KEM_C1003_C0G_SMD.pdf), pp.1–2, supplies the ordering-code interpretation and dielectric characteristics. This verifies the component coding/specification basis; exact orderable lifecycle and stock remain procurement checks. Assign the matching1206 footprint and record the MPN and ratings in candidate fields; do not claim the assembled BOM has been qualified.

No independent reason was found to prohibit this addition before choosing the final regulated rails. It is suitable as a reviewable diagnostic candidate. Activating it remains subject to the user's actual project-confirmation/edit requirements; failure to confirm the active MCP project must not be bypassed by treating this technical recommendation as permission to edit the live schematic.
