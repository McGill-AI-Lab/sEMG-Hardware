# Independent cleanup review — V1.2 ERC corrections

27 October 2026. Read-only review of the active schematic against this task's preserved baseline and native initial/final diagnostics. No design file or ERC setting was edited by this reviewer. The only reviewer-created file is this note.

Reviewed final schematic SHA-256: `202b2b320076c5e802f55e6ed566ae640cb948c6544777b9d51b11222e371208`.

Baseline schematic SHA-256: `7efd6a06e2ac45a553e7731665950c98c9a680dd36da6db584a826dc016e9494`.

## Result

The 22 cleanup diagnoses are resolved through actual source-object cleanup and metadata reconciliation. No cleanup connectivity regression was found. The delivered final verification passes **2,050 assertions**. Native final ERC has **11 reports: 7 errors and 4 warnings**. The additional error beyond the originally projected ten reports is the deliberately retained U3.13/GPIO3 unconnected-pin report; it is not a new wiring fault or a suppressed condition.

| Scope | Independently verified result |
|---|---|
| Eighteen short wire tails | All 18 identified 1.27 mm wire UUIDs are absent. The retained input nodes remain correctly connected; both RLDOUT no-connect markers remain. |
| CS_ADC2 tail | Wire `34341901-2092-4668-89af-eb552c157d44` retains the path `(562.61,96.52)` to `(568.96,96.52)`. Its label `f775580c-f47c-4bc7-a9f8-15143a81985e` remains attached at the endpoint. Only the unused tail toward x576.58 was removed. |
| Supply aliases | Four AVDD and four DVDD local labels retain their original UUIDs and exact electrical anchors, now as global +3.3V labels. Seven retain their original orientation; the eighth has the presentation-only adjustment described below. No functional label link was deleted. |
| Ground aliases | Exactly 43 former GND-valued power instances now have Value AGND. After excluding only the Value property, each instance is structurally identical to its baseline: same reference, UUID, pin UUID, library identity, position and power-input model. |
| Battery cache | The only altered embedded symbol definition is Device:Battery. Exactly Sim.Device=`V`, Sim.Type=`DC` and Sim.Pins=`1=+ 2=-` were added before ki_keywords, matching installed library ordering. Removing only those three properties reproduces the complete baseline structure. |
| BT1 and ADC/MCU instances | BT1, U1, U2 and U3 instance source blocks are byte-identical to baseline. Battery polarity, pin numbering and component properties are preserved. |
| Project/ERC rules | Active project is byte-identical to its preserved baseline; initial and final ignored-check lists match. No severity, conflict matrix or exclusion change was used to remove cleanup reports. |

## Eight supply-label links

All remain on the same intended common +3.3V net; this cleanup does not introduce separate analog and digital supplies.

| Original label | UUID | Preserved anchor / final angle (mm / degrees) |
|---|---|---|
| AVDD | 066ca9c8-7bd4-4f0b-92e4-56350bd7253c | 160.02,85.09 / 0 |
| AVDD | 3589528b-9c95-40c8-a912-f86516f6c24c | 201.93,116.84 / 0 |
| DVDD | 3be50cba-7e40-47bb-8d96-339bceed5caa | 193.04,85.09 / 0 |
| DVDD | 75fc8b9d-1b77-49f1-bb82-13b6eff87138 | 209.55,160.02 / 0 (presentation adjusted from 180) |
| AVDD | 792ff479-7cd1-49c0-b4af-14b86c12e8f8 | 387.35,83.82 / 0 |
| DVDD | 96726343-f5a2-426c-a935-6769c922104b | 420.37,83.82 / 0 |
| DVDD | a495d871-c532-473d-aa7f-0b108779b50c | 539.75,38.10 / 0 |
| AVDD | bd298a1f-5ec1-4f2d-a055-09b58728a7c2 | 429.26,115.57 / 0 |

The first cleanup ERC exposed +3.3V/DVDD as another pre-existing alias on the same rail after the AVDD name was consolidated. The retained cleanup-first artifacts contain that warning. Its subsequent correction preserves all four DVDD anchors and all original electrical assignments. The final ERC contains no multiple_net_names, unconnected_wire_endpoint or lib_symbol_mismatch violation. This is completion of the original alias cleanup rather than a new power architecture.

After the first independent review, label UUID `75fc8b9d-1b77-49f1-bb82-13b6eff87138` was rotated from 180 to 0 degrees, reduced from 1.27 mm to 1.0 mm font and changed to left justification to avoid overlapping START text. Independent comparison against `before-label-presentation.kicad_sch` confirms that this single global-label object is the entire subsequent source delta; replacing that object reconstructs the final source byte-for-byte. Its +3.3V text, UUID and `(209.55,160.02)` anchor are unchanged, so no electrical attachment changed. The [presentation edit log](label-presentation-edit-log.json) records the adjustment. Final verification and ERC remain passing/unchanged as reported above.

## Native connectivity and retained reports

An independent comparison of every baseline native pin/net assignment finds only the two explicitly authorized F04 changes: U4.5 and C54.1 move from +3.3V to `/LP2985_OUT_DISABLED`. No other represented baseline pin changes its net name. There remain 133 components. This preserves all acquisition, control, reference and VCAP pin assignments. The F04 electrical design decision is reviewed separately; the two changes are not caused by cleanup.

The seven valid-topology/source-model conditions remain present: AGND and battery-source power-input modeling errors, shared DOUT output conflict, and four unused TEST/PACE-to-AVDD warnings. The four TEST/PACE warnings now cite U5.5 as the supply-output representative after U4's output isolation; their ADC pins, actual rail ties and required disabled-mode restrictions are unchanged. This representative change is a direct consequence of the authorized F04 correction, not a removal of valid ADC ties or weakened ERC rule.

The three previously evidence-dependent reports remain: U3 CHIP_PU unconnected and undriven, and +5V source-model uncertainty. No marker or flag was used to conceal them. U3 GPIO3 additionally remains unconnected pending the per-pin reviewer’s strap evidence decision. No No Connect flag was added at that pin by the cleanup work.

## Limits

This review validates source changes and native static connectivity. It does not qualify an operating power architecture, enabled regulation, real CS/startup behavior, body bias/protection, physical parts, analog performance or wearer safety. The existing power-up and human-use blockers remain relevant despite the ERC reduction.
