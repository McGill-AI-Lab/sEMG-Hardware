# Open-sEMG-16 hardware

Sixteen differential acquisition channels using two ADS1298 ADCs and an ESP32-S3 DevKitC-1. Each revision is independent; V1 is the immutable baseline.

V1.4 is the active development revision. Its target is 2 kSPS per channel with Wi-Fi acquisition-data transmission; USB supplies power and programming/debug access. Firmware and assembled-hardware streaming have not been validated. USB-connected operation is restricted to non-human bench signals. No revision is approved for human-worn testing.

| Version | Purpose | Main changes | Power architecture | Status |
| ------- | ------- | ------------ | ------------------ | ------ |
| [V1](v1/open-semg-16-v1.kicad_pro) | Original 16-channel design | Baseline preserved for the F01–F21 audit | Battery and two directly paralleled 3.3 V LDOs; incorrect ADC supply/ground connections | Audited baseline; confirmed wiring faults; not ready for power-up |
| [V1.1](v1.1/open-semg-16-v1.1.kicad_pro) | Repair critical connectivity | Corrected ADC supplies/grounds and shared clock; added startup pulls and TP1–TP16 | Original battery/LDO arrangement retained | Implemented schematic; power-source and startup blockers remain. Historical report calls this revision “V2” |
| [V1.2](v1.2/open-semg-16-v1.2.kicad_pro) | Incremental electrical and ERC corrections | Added DIN/SCLK pulls and passive requirements; isolated unused LP2985 output; cleaned verified unused connections | Battery/LDO circuitry retained; both LDOs deliberately disabled by R38 | Implemented schematic; final ERC 7 errors / 4 warnings; operational supply unresolved |
| [V1.3](v1.3/open-semg-16-v1.3.kicad_pro) | Battery power and controlled interface | Added protected input, converters, quiet ADC supply, monitoring and interface isolation | 1S battery → 3.3 V MAIN; separate 4.0 V converter → 2.98 V ADC LDO. Seated USB prohibited | Implemented schematic; final ERC 5 errors / 4 warnings; hardware qualification pending |
| [V1.4](v1.4/open-semg-16-v1.4.kicad_pro) | Minimal USB-powered, Wi-Fi-streaming 16-channel sEMG bench prototype, powered through the ESP32-S3 DevKitC-1. | Direct SPI; removed obsolete power and diagnostic hardware; 117 physical parts versus V1.2’s 133 | USB → DevKit onboard regulator → shared 3.3 V for ESP32 and both ADCs | Implemented schematic; final ERC 7 errors / 0 warnings; power, startup and streaming qualification pending |

```text
v1/, v1.1/, v1.2/, v1.3/, v1.4/   Independent KiCad revisions and local libraries
reviews_v1/, reviews_v1.1/, …       Review records, implementation reports and evidence
```

Read the [original engineering review](reviews_v1/full_review.md), [V1.1 changes](reviews_v1.1/updates_from_v1.md), [V1.2 changes](reviews_v1.2/updates_from_v1.1.md) and [final ERC corrections](reviews_v1.2/erc_corrections.md), [V1.3 implementation](reviews_v1.3/power_implementation.md), and [V1.4 implementation](reviews_v1.4/implementation.md). V1.3’s earlier [architecture proposal](reviews_v1.3/power_architecture.md) is decision history; its proposed 3.4 V single-prestage tree was superseded by the implemented circuit above.
