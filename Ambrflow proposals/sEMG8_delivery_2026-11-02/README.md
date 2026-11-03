# sEMG-8 board: design package

Version of 2 November 2026. This package holds four complete 8-channel surface-EMG board designs based on the client's
open-semg-8 board (github.com/McGill-AI-Lab/sEMG-Hardware). The signal is 1–5 mV and must be resolved to 20 µV.

Each design is a KiCad project with:

- a schematic PDF;
- a priced full-board BOM;
- a table of test limits for bring-up.

**What's on every board.** These sections come from the client's base design:

- the battery and two regulators: LP2985 for the analog rail, TLV75533 for the digital rail;
- the ESP32-S3-WROOM-1;
- the eight electrode connectors and the reference-electrode connector.

The front end is the part that differs:

- **Candidate A**: eight low-cost op-amp channels feeding the ESP32-S3's own ADC1. There are three op-amp choices.
- **Candidate B**: TI's ADS1298 8-channel 24-bit front end, talking to the ESP32-S3 over SPI.

## Choosing a design

| Design | Converter | Front-end power, 8 ch at 3.3 V (typ) | Front-end parts | Whole board, sourced parts | Resolution | CMRR (worst case) |
|---|---|---|---|---|---|---|
| **A1** TLV9004 (lowest power) | ESP32-S3 ADC1, 12-bit | 6.6 mW (8.2 mW max) | $4.71 | $10.55 | 20 µV → ≥ 2.13 mV at the ADC (3 LSB) | 48.7 dB |
| **A2** MCP6004 | ESP32-S3 ADC1 | 10.8 mW (18.3 mW max) | $3.80 | $9.64 | same | 48.7 dB |
| **A3** LMV324B (lowest cost) | ESP32-S3 ADC1 | 8.7–11.4 mW, see check 1 | $1.28 | $7.12 | same | 48.6 dB |
| **B** ADS1298 | 24-bit ΔΣ, internal | ≈ 17 mW: ADS1298 ≈ 10.7 + oscillator 6.6 | $41.66 | $48.89 | 6.0–7.3 µVpp input noise at 2 kSPS | 105 dB min (TI) |

**What the figures cover.**

- **Prices:** per board at quantity 100, from DigiKey on 2026-11-02. The battery, connectors and PCB are excluded; the
  base design doesn't name parts for them.
- **Power:** the front end only. The ESP32-S3 and the regulators are the same on every board and aren't counted.
  - **Candidate A:** the op amps' quiescent current (32 amplifiers), plus the body-reference buffer (0.2 mW), at 3.3 V.
    The "max" figure uses datasheet maxima, which are stated at 5.5 V.
  - **Candidate B:** TI's typical supply currents at 3.3 V on AVDD and DVDD, plus the 2.048 MHz oscillator: 2.0 mA
    typical, 10 mA maximum (Abracon datasheet).
  - **Option for B:** the ADS1298's internal oscillator would save the 6.6 mW and $1.70. It means tying CLKSEL high
    instead of low, which changes TI's configuration, so the choice is the client's. The internal clock is accurate to
    ±0.5 % at 25 °C and ±2 % over temperature.

**A note on op-amp choice.** All three Candidate A boards share the same resistors and capacitors. The op amp is the
only difference.

## What's in each folder

```
A1_TLV9004_lowest-power/    A2_MCP6004/    A3_LMV324B_lowest-cost/    B_ADS1298/
    <name>.kicad_pro            KiCad project (opens in KiCad 9 or 10)
    <name>.kicad_sch            root sheet: power, ESP32-S3, connectors, programming header, and the front-end sheet symbols
    channel.kicad_sch (A)       one sEMG channel, placed 8 times (CH1 to CH8, pages 2 to 9; references R1xx to R8xx)
    ads1298.kicad_sch (B)       the ADS1298 core (page 2)
    <name>.pdf                  every sheet, printed
    bom.csv                     full-board BOM: section, refs, MPN, maker, KiCad footprint, qty per board, price at 100, DigiKey link
    test_limits.csv             bring-up tests: spec limit and the expected value, per test
    LICENSE.txt                 the front-end reference's licence (see Licences)
reference_designs/              the two reference front ends, as admitted, with their original values
opamp_sweep_ranking.csv         all 21 orderable quad op amps tried for Candidate A, ranked by power then price
```

## Changes from the client's base design

The base-design sections are kept as drawn, with these changes:

1. **Supply wiring fixed**, as proposed in the
   [28 October audit](../../audits/ambrflow-v0-v1-20261028/AMBRFLOW_MEETING_SUMMARY.md) of the base design:
   - U4 (LP2985) now feeds only the analog rail, +3.3VA, which powers the front ends and the ADS1298's AVDD.
   - U7 (TLV75533) feeds only the digital rail, +3.3V, which powers the ESP32-S3 and the ADS1298's DVDD.
   - Before: both outputs were tied together on +3.3V, and +3.3VA had no source.
   - Both enables are tied to the battery (always on). Before, the enable net had no driver.
   - The board has one ground.
   - C44 (2.2 µF) is now U4's output capacitor.
   - The base's C20 is renumbered C64, because TI's core has its own C20.
2. **Added a programming header, J2:** 3V3, GND, EN, IO0, TXD0, RXD0, USB D− and USB D+. The base leaves all of these
   unconnected, which leaves no way to program the ESP32-S3. For download mode, hold J2 pin 4 (IO0) low at reset.
3. **Candidate A only:**
   - **ESP32 ADC pins.** Each channel's output goes to an ESP32-S3 ADC1 pin: CH1 IO1, CH2 IO2, CH3 IO4, CH4 IO5, CH5 IO6,
     CH6 IO7, CH7 IO8, CH8 IO9. IO3 is skipped because it is a strapping pin.
   - **Body reference.** The reference electrode J1 is held at VCC/2 = 1.65 V. That is the electrode potential the
     front end was simulated at. The driver is Patchy's own reference block at its own values (1 MΩ/1 MΩ, 100 nF,
     2.2 µF), buffered by a TLV9001 (U8). Patchy likewise drives its reference electrode from its buffered mid-supply.
   - **Input filters.** The base's 2 kΩ/620 pF input filters belong to its ADS1298 front end and are not on the
     Candidate A boards. Each channel has its own input clamps and filter capacitor.
4. **Candidate B only:**
   - **SPI wiring** is the base design's: CS IO5, PWDN IO6, RESET IO7, DRDY IO8, MOSI IO11, MISO IO12, SCLK IO13,
     START IO21.
   - **Clock.** Y1 supplies the 2.048 MHz master clock that TI's core selects. TI's EVM part (Fox FXO-HC735) is not in
     stock, so Y1 is an Abracon ASV-2.048MHZ-ERS-T of the same 7×5 mm size.
   - **Unused ADS1298 pins** are tied as TI's datasheet says: DAISY_IN and GPIO1–4 to ground, and the test/pace outputs to
     AVDD.
   - **Reference electrode.** J1 carries TI's right-leg drive (ELEC_RL).
   - **Input filters.** The base's 2 kΩ/620 pF input filters are not on this board. The front end follows TI's
     direct-input configuration, which is the configuration that was simulated, and the filters can be added back.

## What was verified, and how

**The front ends** were iterated on the design loop's circuit simulator against a locked specification until every
check passed:

- Candidate A against semg8-opamp (73a6d4ada293);
- Candidate B against semg8-ads1298 (f30ae840439c);
- both on engine e735a0e.

The checks covered gain, range, resolution, CMRR, op-amp stability and supply corners, with every resistor at ±1 % and
the supply at ±1.5 %.

**The whole boards.** For each board, KiCad's netlist of the full hierarchy was checked against the intended
connectivity, pin by pin: 101 nets on each Candidate A board and 47 on Candidate B. It matches exactly. KiCad's electrical
rules check reports:

- **Candidate A:** no errors or warnings.
- **Candidate B:** six warnings, all from the datasheet-recommended ties of unused ADS1298 pins to a supply or ground.

**Not simulated.** The board-level sections were not run through the design-loop simulator: power, ESP32-S3, the body
reference and the clock. Running the whole board through it is the natural next step.

## The test limits

Each `test_limits.csv` row gives a test, its setup, where to measure, a **spec limit** and an **expected** range.

**Candidate A:**

- **Spec limits:**
  - the 3.3 V ±1.5 % analog rail;
  - the ADC's 0–2.9 V window;
  - gain of at least 35.4 V/V across 20–500 Hz, so that 20 µV moves the ADC by at least one LSB;
  - CMRR of at least 48 dB;
  - every op amp inside its linear output range.
- **Expected ranges:** from the simulator, over every combination of:
  - each resistor at ±1 %;
  - the supply at ±1.5 %;
  - all resistors pushed together toward more gain, less gain or more common mode;
  - an electrode offset of −50, 0 and +50 mV.
- **Board rows:** the body-reference voltage, both rails, and a per-channel wiring check through the ESP32-S3's ADC.

**Candidate B:** the limits come from TI's ADS1298 datasheet (SBAS459K), with board rows for the clock frequency, both
rails, and an SPI check that reads the device ID (0x92).

**How to drive the inputs.**

- **Gain tests:** hold the negative electrode input at 1.65 V and drive the positive one with 1.65 V plus a sine of
  5 mV peak or less.
- **CMRR tests:** tie both inputs together and drive them with 1.65 V plus 200 mV p-p.

**Capacitor tolerance was not simulated.** By hand calculation:

- C5 (±10 %) moves the 500 Hz gain by about ±3.3 %.
- C4 (±20 %) lowers the 20 Hz gain by up to about 1.1 %.

Widen the expected gain range at those frequencies by these amounts.

## Check before building

1. **A3 (LMV324B-SR) is a 3PEAK part** simulated on TI's LMV324 model, because the simulator has no 3PEAK model.
   - Distributor copies of 3PEAK's datasheet show figures equal to or better than TI's on every number the checks use:
     2.5–5.5 V, 1 MHz, rail-to-rail input and output, 80 µA typical / 130 µA maximum per amplifier.
   - The official PDF could not be reached. Confirm against it, and against the SOP-14 outline.
   - A TI LMV324 (for example LMV324IDR) is the part the simulated model describes.
2. **Choices the base design leaves open.** These are placeholders, and the client should confirm them:
   - **Battery:** connector JST PH, 2-pin. The base names neither the cell nor the connector.
   - **Connectors:** electrode, reference and programming connectors are 2.54 mm pin headers.
   - **ESP32-S3 module:** the N8 variant (8 MB flash, no PSRAM).
   - **C46:** the base's 200 µF is not a stocked value; 220 µF in 1210 X5R is the nearest. Expect its capacitance to
     drop noticeably at 3.3 V DC bias.
3. **Not on the board:** no battery charger, battery protection or USB connector. The base design has none either.
4. **Body reference (A) tolerance.** With 1 % resistors and the ±1.5 % rail, it sits between 1.609 and 1.692 V. That is
   inside the spec's 1.6–1.7 V electrode range, but the simulator held the negative input at exactly 1.65 V.
5. **Candidate B configuration:** set CONFIG3.RLDREF_INT = 1, since RLDREF is open as on TI's sheet.
6. **Candidate B, C20:** TI's 0.01 µF was sourced as 9.1 nF C0G, and the front end re-simulated with it (it passes).
7. **Things no check covered:**
   - op-amp noise and the ESP32-S3 ADC's own noise and ±50 mV total error;
   - capacitor DC-bias derating;
   - thermal behaviour;
   - the footprints, which match the sourced package names but have not been checked against each part's land pattern.
8. **Prices and stock** are DigiKey's on 2026-11-02, at quantity 100.

## Licences

- **The base-design sections** are the client's own.
- **Candidate A** front ends derive from Upside Down Labs' Muscle BioAmp Patchy, licensed CERN-OHL-S-2.0. It is strongly
  reciprocal: distributing a board that contains them requires publishing the board's design files under CERN-OHL-S-2.0.
- **Candidate B** derives from TI's ADS1298ECG-FE user's guide. TI grants permission to use it only for developing an
  application that uses the TI products it describes.

The full texts are in each folder's `LICENSE.txt`.
