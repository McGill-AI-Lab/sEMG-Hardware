# Minimal ADC power/control implementation assessment

27 October 2026. Focused read-only decision, not a broad audit or a claim of powered verification.

## Recommendation

Use one regulated 3.3 V buck-boost rail, a default-OFF TPS22919 ADC power switch, and one SN74LVC244A powered from the switched ADC rail for the seven MCU→ADC signals. Keep all ADC analog/digital supplies at the same switched approximately3.3 V rail. Keep the supported separate-CS/shared-MISO cascade protocol and the common ADC clock. Two series resistors in the DOUT branches provide a bounded startup-contention current instead of the former mux and gating network. This is a reasonable **bench prototype** simplification, subject to the specific constraints below.

A single additional dual return buffer powered from MAIN, Nexperia74LVC2G125DP, is the economical way to establish explicit power-off tolerance for both shared MISO and DRDY. It preserves the shared bus, adds one8-pin IC, and avoids assuming ADC stored charge always disappears before MCU power. If omitted, abrupt-removal return injection remains a measured-qualification condition; do not call the forward buffer alone complete power-off isolation.

## Manufacturer constraints and concrete values

[ADS1298 SBAS459K](../../../../docs/datasheets/originals/components/ADS1298.pdf), pp.12,16–17,96–97, and [SN74LVC244A Rev.AG](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf), electrical table and §7.3, support these distinctions:

- ADS DVDD3.3 V is permitted; equal AVDD/DVDD avoids a separate analog/digital ramp dependency. Keep actual AVDD pins19/21/22/54/56/59, DVDD48/50, auxiliaries17/18/62 and U1CLKSEL52 on the switched rail. Preserve grounds, internal bypass and references. U2CLKSEL remainsgrounded.
- The 244 accepts powered MCU inputs while its own VCC is zero and specifies Ioff; it cannot be assumed fully functional below its1.65 V operating minimum. Powering it from ADC supply keeps its driven outputs within the ADC supply domain.
- A100 kΩ,1% receiver pulldown draws at most3.35/99k≈33.84 μA whenhigh. Adding the ADS ±10 μA input specification for two receivers gives about53.84 μA, below the244's100 μA light-load test condition. Its VOH≥VCC−0.2 V then gives at least0.2×DVDD−0.2≈0.45 V forward high margin atDVDD3.25 V. Apply the actual selected package/temperature table.
- A100 kΩ pulldown does **not** independently guarantee a low into20 μA leakage: its passive-only screen is2.02 V at101 kΩ. LOW during a valid switched rail depends on the244 actively driving the MCU's preconfigured LOW. Do not describe the larger pulls as a standalone guarantee through every supply ramp. Keep this limitation distinct from absolute-limit safety: receiver andbuffer supply track together.
- Use **3.6 kΩ,1% per DOUT branch** rather than3.3 kΩ if relying on the characterized±500 μA output-load condition. With an assumed3.35 V maximumrail and both minimum resistances, worst opposed-driver current≤3.35/(2×3.564k)=0.470 mA. Each resistor dissipates less than0.8 mW. Both normal CS exclusivity and power-up tests remain necessary.
- ADS p.12's10 mA continuous value is **input current**, not an output-current rating. There is no basis here for calling DOUT±10 mA rated. The500 μA output characterization is the conservative comparison used above; no maximum output-short rating is invented.

The [TPS22919](https://www.ti.com/lit/ds/symlink/tps22919.pdf), §§8.3/9.2, provides controlled rise and configurable quick output discharge. Pin1VIN,2GND,3ON,4NC,5QOD,6VOUT. TieQOD toVOUT for its typical24 Ω discharge path unless a justified external resistance is needed. This is not a guaranteed maximum resistance; §8.3.3.1 warns discharge strength decreases asVIN collapses. Keep a10 kΩ ON pulldown and useGPIO4 forADC_POWER_EN. Keep C57's large bank onMAIN; ADC local40.4 µF plus addedbuffer/ADC bypasses determines switched-rail startup/discharge. Internal reference/VCAP charge is additional.

## GPIO/reset and sequencing contract

The [ESP32-S3 SoC v2.2](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf), Table2-1, shows no default WPU/WPD forGPIO6–14; its reset table includes input-enable states for the return/control pins. Table2-2 lists LOW-only typical60 μs power-up glitches onGPIO4 andGPIO6–14. GPIO4 is not a strapping pin. These facts do not imply every firmware or GPIO-hold configuration resets identically.

1. ADC_POWER_EN has its external pulldown and defaultsOFF. The stock DevKit remains powered fromMAIN while ADC power is off.
2. Firmware first drivesADC_POWER_EN LOW, disables internal pulls on MISO/DRDY and the interface, waits for the measured ADC discharge condition, then configures all seven forward MCU outputs LOW. Do not enable ADC while those 244 inputs float.
3. RaiseADC_POWER_EN. Hold all seven signals LOW through the measured switched-rail stabilization interval. The244 OEs may remain grounded; its power-off tolerance prevents normal MCU boot GPIOs from energizing an ADC whose switched rail isoff.
4. After supplies settle, drive both CS HIGH before clocked transactions. The two DOUT series resistors bound the possible preceding opposed-driver condition. Do not interpret MISO as valid while both CS areLOW; optionally disable its MCU input buffer until this state ends.
5. Follow the established PWDN, valid-clock,2^18-clock/VCAP1>1.1 V, reset, reference and U1-master/U2-slave initialization. Do not pulse sharedRESET after setting U1CLK_EN. Start conversions only after configuration/readback/settling.
6. Before intentional restart, sleep or normal shutdown, stop acquisition, set all forward outputs LOW, disable ADC power and wait for discharge. Forbid GPIO/RTC hold retainingADC_POWER_EN through reset. Verify watchdog/software-reset and abrupt battery-removal waveforms; no automatic recovery guarantee is inferred.

Direct DRDY and shared MISO must have **no pullup to powered MAIN while ADC isOFF**. Default GPIO states do not show such pullups, but firmware configuration must preserve that condition. On abrupt MAIN loss, ADC local capacitance may retain voltage; direct return paths can then inject the MCU. That is an exposure requiring discharge measurements or the one-chip return buffer, not a confirmed damage event.

## Series-MISO timing and minimum test

DOUT's17 ns maximum delay is characterized at20 pF||100 kΩ and DVDD2.7–3.6 V. Adding3.6 kΩ changes the load/network; it does not preserve that original delay by definition. For an illustrative lumped20 pF bus, Rmax=3.636 kΩ givesτ≈72.7 ns. Using ADS guaranteed high2.9 V and ESP high threshold2.475 V, the rising threshold time is roughly `−RC ln(1−2.475/2.9)≈140 ns`, before the ADC delay and MCU setup. At50 pF it becomes roughly350 ns. Thus2 MHz may be comfortable for a short20 pF implementation and fail for a50 pF one;1 MHz has more margin. These are RC screens, not timing guarantees.

A MAIN-powered TTL-input return buffer lowers the threshold to2.0 V and regenerates fast edges. For the same20 pF model, the resistor charging time is roughly85 ns; add ADC/buffer propagation and MCU setup. Its Ioff also has a direct power-state purpose. For the optional [Nexperia74LVC2G125DP](https://assets.nexperia.com/documents/data-sheet/74LVC2G125.pdf), verified pins are1OE1,1A2,1Y6;2OE7,2A5,2Y3;GND4,VCC8. Ground bothOEs. Channel1 receives the resistor-combined MISO and drivesMCU MISO; channel2 receivesU1DRDY and drivesMCU DRDY. Do not mistakenly exchange1Y6 and2Y3.

Start bench SPI at1 MHz with conservative command spacing, then scope/load-test2 MHz if the chosen sample rate requires it. Two8-channel frames contain432 bits: payload alone is432 μs at1 MHz or216 μs at2 MHz. Consequently1 MHz cannot support4 kSPS paired reads, and even2 MHz leaves limited firmware/CS overhead at4 kSPS. The intended rate remains a firmware requirement; do not silently claim4 kSPS from a successful low-rate test.

This simplification removes the lower analog-rail headroom decision, second converter/LDO, rail-supervisor logic, readiness gates and DOUT mux. It retains the specific startup, battery/source and bench verification requirements needed to make the simpler hardware usable. All16 differential input paths remain unchanged.
