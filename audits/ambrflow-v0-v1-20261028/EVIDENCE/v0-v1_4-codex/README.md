# V0 versus V1.4-codex audit evidence

Active V1.4 source: `open-semg-16-v1-codex/v1.4/open-semg-16-v1.4.kicad_sch`. Review candidates and historical snapshots were not active sources. V0 and V1.4 were read only. Absolute source paths and before-export SHA-256 hashes are in `source_manifest.json`; both hashes are checked unchanged afterward.

Fresh exports used KiCad CLI 10.0.7 for each absolute source:

    kicad-cli sch export netlist --format kicadxml --output EVIDENCE/v0-v1_4-codex/v1_4.net.xml 'SOURCE'
    kicad-cli sch erc --format json --severity-all --output EVIDENCE/v0-v1_4-codex/v1_4.erc.json 'SOURCE'
    kicad-cli sch export svg --output EVIDENCE/v0-v1_4-codex/v1_4-svg/ 'SOURCE'

V0 outputs use v0 names. Fontconfig warnings did not prevent generation. V0 also warns about duplicate J1 reference-electrode annotation; physical connector-instance naming is ambiguous, but supply/control traces do not depend on it.

- Net XML/connectivity text: fresh native component/net exports and readable memberships.
- ERC JSON/summary: full/condensed rule checks; V0 62 messages, V1.4 7 errors and no warnings. These are not functional pass/fail counts.
- SVG folders: complete schematic plots.
- Inventory JSON: complete-source extraction of symbols, embedded pins, wiring, labels, notes and no-connect markers. Both sources are flat single sheets.
- Condition findings JSON: final 48 condition decisions.
- Extraction/build/validation Python scripts: reproducible audit operations; source directories are never output targets.
- Validation results JSON: checks and practical limits.

Six distinct V0 wiring defects correspond to five FIXED checklist rows because J3 overlaps multiple arrangements. Remaining rows: 24 CANNOT VERIFY, 9 NOT FOUND and 10 NOT APPLICABLE. Unmeasured transients/specification gaps are not credited as fixes.

Earlier V0/V1 reports remain untouched. New report/CSV filenames begin `AMBRFLOW_V0_V1_4_CODEX_COMPARISON`. No physical measurement, simulation or firmware execution was performed.
