# Audit evidence

All files in this folder are audit outputs. The two original project directories were read only. Source paths, SHA-256 hashes, sizes and sheet counts are in `source_manifest.json`. The final classifications are in the audit-root reports and `condition_findings.json`; analyst notes are supporting material.

KiCad CLI version: **10.0.7**. Each active source is a complete flat schematic with no hierarchical sheets. `.history` was excluded.

Commands used for each source (`SOURCE` denotes its absolute `.kicad_sch` path; `v0` or `v1` denotes the revision):

```sh
kicad-cli sch export netlist --format kicadxml --output EVIDENCE/v0.net.xml 'SOURCE'
kicad-cli sch erc --format json --severity-all --output EVIDENCE/v0.erc.json 'SOURCE'
kicad-cli sch export svg --output EVIDENCE/v0-svg/ 'SOURCE'
```

The corresponding V1 outputs use `v1` names. All commands completed; no schematic editing command was used. The CLI printed a Fontconfig warning. V0 netlist export additionally warned of annotation errors; the two V0 reference-electrode connector instances share J1. Do not infer unique physical connector instance mapping from that reference alone. ADC supply/control traces do not depend on that ambiguity.

- `v*.net.xml`: actual KiCad connectivity exports.
- `v*.connectivity.txt`: readable components and complete net/pin membership.
- `v*.erc.json` / `v*.erc_summary.txt`: full and condensed ERC results, including ignored-check metadata. V0 has 62 messages; V1 has 65. These are messages, not counts of functioning/failing circuits.
- `v*-svg/`: schematic plots.
- `v*.schematic_inventory.json`: complete parsed placed-symbol/pin/property inventory, wires, labels, junctions, notes and no-connect markers. Other `parsed`/`all-symbols` JSON files are independent analysts’ extraction artifacts.
- `esp32-devkitc-v11.pdf` and rendered page: official reference board schematic, used to distinguish board-level EN/reset/LED/LDO circuitry from bare-module assumptions. Its fit to the actual installed board remains to confirm.
- `power_findings.md`, `adc_findings.md`, `digital_findings.md`: technical supporting notes and manufacturer links. Final A1/F1 comparison classifications are deliberately stricter than initial analyst suggestions: uncertain V0 numeric voltage, confirmed V1 zero span.
- `extract_audit.py`: read-only full-source parser and readable export generator.
- `build_reports.py`: creates the three final reports and enforces CSV coverage/count/source-hash consistency.
- `validate_evidence.py` / `validation_results.json`: independent checks of reported net membership, control arrangements, complete input filters, all 48 conditions, local links and unchanged schematic hashes.

No source firmware, rated passive BOM, battery range specification, electrode/load model or physical/simulated transient data was available. No unmeasured waveform is asserted by these artifacts. ERC is supporting evidence, not proof of functionality.
