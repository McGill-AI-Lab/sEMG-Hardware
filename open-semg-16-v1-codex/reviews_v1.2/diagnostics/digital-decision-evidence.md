# V1.2 digital correction evidence — F09, F06 and F18

27 October 2026. This note supports a targeted continuation of the original F01–F21 review. Sources read first: [V1 full review](../../reviews_v1/full_review.md) and [V1.1 implementation report](../../reviews_v1.1/updates_from_v1.md). The V1.1 report retains historical “V2” wording; this investigation concerns V1.2.

**R36/R37 are proposed corrections in this evidence note.** Their implementation and final connectivity require independent confirmation from the final native KiCad netlist. This note does not claim an applied edit, successful ERC result, demonstrated startup sequence or bench measurement.

## F09 — define low defaults for shared DIN and SCLK

The supplied [initial V1.2 netlist](../initial-netlist.xml) establishes these presently unbiased inputs:

| Proposed component | Value and intended tolerance | Pin 1 | Pin 2 |
|---|---|---|---|
| R36 | 10 kΩ, 1% | `/MOSI`: U1.34 DIN, U2.34 DIN, U3.17 GPIO11 | AGND |
| R37 | 10 kΩ, 1% | `/SCLK`: U1.40 SCLK, U2.40 SCLK, U3.18 GPIO12 | AGND |

Each initial signal net contains only the three listed semiconductor terminals. Existing R33/R34/R35 already bias shared START/RESET/PWDN low. Adding the two pulldowns extends defined low bias to the shared command and serial-clock inputs while the MCU pins are high impedance. It does not change the SPI pin assignment, conversion clock, frame format, acquisition channels or sample-rate selection.

[ADS1298 SBAS459K](../../../docs/datasheets/originals/components/ADS1298.pdf), §11.1 p.96, requires low inputs before and during supply stabilization. The low default also agrees with the DIN-zero requirement for ordinary continuous frame retrieval. SCLK is a Schmitt input (§9.5.1.2 p.59); that property does not establish an idle state for an otherwise floating wire. These pulldowns are shunt loads, not series damping or off-state isolation.

### Static electrical screen

ADS1298 p.16 specifies digital input leakage up to ±10 µA per ADC input. The ESP32-S3 DC table specifies input leakage up to 50 nA at its stated 3.3 V, 25°C conditions. Assuming two leaking ADC inputs, a high-impedance MCU input with no opposing pull, and a 1% resistor:

`Ileak = 2 × 10 µA + 50 nA = 20.05 µA`

`Rmax = 10.1 kΩ`

`Vlow,max = 20.05 µA × 10.1 kΩ = 0.202505 V`

At nominal DVDD = 3.3 V, ADS VIL(max) = 0.2 × DVDD = 0.66 V. The corresponding static low margin is approximately 0.4575 V. This is a conditional leakage calculation, not a guarantee during an unqualified rail ramp, external-power state or actively driven MCU output.

When driven high at 3.3 V, each nominal 10 kΩ pull draws 0.33 mA and dissipates 1.089 mW. At the 9.9 kΩ tolerance endpoint, those values are 0.3333 mA and 1.10 mW; both pulls together draw 0.6667 mA. At 3.6 V and 9.9 kΩ, each draws 0.3636 mA and dissipates 1.309 mW. Final component selection must meet tolerance and rating requirements; an intended resistance/tolerance is not a procured MPN or PCB definition.

These loads are small compared with the controller's typical drive characterization, but that characterization is not a guaranteed per-pin current limit. The published ESP VOH minimum of 0.8 × VDD is measured with a high-impedance load and equals ADS VIH(min) = 0.8 × DVDD when the rails are equal. Consequently no new guaranteed positive high-level noise margin is claimed with either existing or proposed pulldowns. Loaded levels and clock edges need measurement.

## MCU reset evidence and remaining CS decision

The [official ESP32-S3 SoC datasheet v2.2](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf), Table 2-1 pp.16–17, lists no WPU/WPD default for GPIO6–14. Table 2-2 p.18 lists typical 60 µs low-output power-up glitches on these pins. Table 5-4 p.65 supplies the leakage, voltage and typical drive figures used here. These chip-level facts supplement the local module document; they do not identify the installed DevKit revision or prove its complete startup behavior.

The initial CS nets remain U1.39/U3.16 GPIO10 and U2.39/U3.20 GPIO14. Plain pullups to DVDD would rise with that rail before verified supply stabilization. They also cannot guarantee inactive CS against a driven low boot glitch. Thus the proposed DIN/SCLK pulls improve F09 without closing the CS or complete power-up finding.

Remaining alternatives are a documented power-qualified CS/control gating scheme, or a demonstrated startup contract that keeps the ADCs inactive while low startup CS is permitted and establishes exclusive CS before releasing/configuring acquisition. Their choice must include MCU reset, ADC clock/POR timing, external-power and supply-loss states. Passive pulls alone do not enforce firmware nonoverlap or protect an unpowered ADC against driven inputs. No gating architecture is selected here.

## F06 and F18 — preserve verified connections, retain firmware requirements

The initial native netlist already places only U1.37, U2.37 and TP1 on `ADC_CLK`. U1 CLKSEL52 follows its actual DVDD rail; U2 CLKSEL52 follows actual digital ground/AGND. Preserve these connections. ADS Table 11 p.50 and CONFIG1 p.67 require U1 CLK_EN = 1 for its internal oscillator to appear on CLK; the bit resets to zero. Firmware must enable that output, allow the slave's clock-dependent POR conditions, and use the slave's individually selected RESET opcode or another demonstrated initialization sequence without clearing the master's CLK_EN through another shared hardware reset. Shared START and equal register configuration still require observed DRDY/sample-alignment validation.

The unused ADS GPIO42/44/45/46 already connect to actual AGND. This follows ADS §9.3.2.1 p.46; preserve the ties and keep the GPIOs inputs or output-low. Keep hard-tied TEST/PACE outputs, unused RLD/WCT functions and RLD rerouting disabled. Reference enable/settling, gain/rate, lead-off policy, register readback, full-frame reads and recovery remain F18 firmware work. No oscillator, MCU pin reassignment, sample-rate decision or reference-network change is justified by this investigation.

## Required implementation verification

The final native netlist should add only R36.1 to `/MOSI`, R37.1 to `/SCLK`, and both pin-2 terminals to AGND for this correction. All previous bus/control/clock pin memberships and all 16 input mappings must remain intact. Check the native schematic parser/export and ERC; compare violations with the baseline and investigate any new one. These checks establish static implementation evidence only. Complete supply sequencing, CS arbitration, loaded logic levels, edges, firmware behavior and actual synchronization require further verification.
