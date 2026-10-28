# ESP32 and interface check for the simpler shared-3.3-V architecture

27 October 2026. Focused design check only; no schematic edit. This considers one nominal 3.3 V buck-boost for MCU and ADC loads, a TPS22919 switching both ADS1298 supply domains together, and an ADC-powered SN74LVC244A for the seven forward controls. The accepted stock-DevKit mechanical USB exclusion/detached-service contract remains unchanged.

## Decision

**This is a workable simpler architecture for controlled bring-up with explicit firmware initialization and measured reset behavior.** It does not establish that GPIO4 goes low for every possible MCU reset. One MAIN supervisor is enough for the shared supply's voltage-monitor function; a second rail hierarchy is unnecessary. Keep F09's software-reset and discharge qualification explicit instead of claiming universal automatic shutdown from a GPIO default.

## GPIO4 is a suitable power-enable choice

The [Espressif SoC datasheet v2.2, Tables 2-1/2-2, pp.16–18](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf) shows GPIO4 without a default pull and with a LOW power-up glitch (60 µs typical). GPIO9 and GPIO13 become input-enabled after reset, without a default pull, and also have LOW glitches. GPIO4 is not a strap, memory pin or USB data pin. Its carrier terminal is U3.4.

An external **10 kΩ pulldown on TPS22919 ON / GPIO4** therefore gives the required cold-start OFF bias; a LOW glitch reinforces OFF. Do not rely only on the switch's typical smart pulldown. The switch is active-high, and its recommended ON levels are LOW ≤0.35 V / HIGH ≥1.0 V. Keep ON loading light and verify its actual LOW during resets. The [TPS22919 datasheet, §§6.3/6.5/8.3](https://www.ti.com/lit/ds/symlink/tps22919.pdf) supports 1.6–5.5 V input, controlled rise, 1.5 A continuous rating, and adjustable QOD. Pin1=IN,2=GND,3=ON,4=NC,5=QOD,6=OUT. Short QOD5 to OUT6 for the smallest discharge network. Its 24 Ω QOD resistance and turn-off/fall timings are typical, not a guaranteed full-board discharge time. It does not specify reverse-current blocking.

The MCU remains on MAIN; both ADC AVDD/AVDD1 and DVDD, auxiliary ties and master CLKSEL follow switched ADC_3V3. This preserves equal ADC voltage domains and avoids the former quiet-LDO headroom problem. MAIN and ADC voltage minima still need switch, connector and transient-drop allowance.

## Forward buffer and default controls

[TI SN74LVC244A, §§5.3/5.5/7.3](https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf): supply 1.65–3.6 V, inputs tolerate up to 5.5 V, and Ioff limits power-off leakage. At VCC=0, outputs are disabled regardless of input state. Ground both active-low OEs, power VCC from ADC_3V3, provide 100 nF bypass, tie the unused input low and leave its output unloaded. Seven channels carry DIN, SCLK, START, RESET, PWDN, CS1 and CS2.

Do not leave the buffer's seven MCU-side inputs floating while it is powered during a reset/discharge interval. Reuse existing 10 kΩ pulls on the corresponding **buffer-input side**, or retain them and add the needed input biases; ensure both CS inputs also have defined LOW startup bias. Firmware drives all seven LOW before ADC power is enabled. Ioff qualifies the fully OFF condition; behavior below the buffer's 1.65 V operating minimum during a supply ramp is not a valid-logic guarantee. Scope the ADC-side controls through the real ramp.

When ADC supply is established and TI's startup waits have elapsed, firmware can drive both CS HIGH and perform controlled reset/configuration. The seven inputs need not be MCU-driven HIGH during the supply ramp.

## Return signals: no automatic pull-up, but firmware must preserve that

GPIO9/13 default states do not create a HIGH pull-up into an unpowered ADC. Configure them deliberately as **input-only with both internal pulls disabled**, and never use them as outputs. Espressif's [GPIO API](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/gpio.html) warns that boot/application code can alter hardware defaults. In particular, `gpio_reset_pin()` enables a pull-up: it is not a suitable final configuration for these return pins. Check the actual configuration with `gpio_dump_io_configuration()`.

Put one **3.3 kΩ series resistor on each ADC DOUT before joining MISO**, and one on DRDY1 before GPIO9. The third resistor addresses the GPIO9 LOW-glitch interval if an ADC is still powered during warm reset. Optional 100 kΩ pulldowns on the MCU-side MISO and DRDY nodes define otherwise floating idle/off inputs and shunt ordinary input leakage; they add little load when the ADC drives HIGH.

The series resistors limit, rather than eliminate, contention or injection. At 3.3 V, two opposing DOUT drivers see roughly 0.5 mA through 6.6 kΩ; one HIGH ADC output against a LOW MCU glitch sees roughly 1 mA through 3.3 kΩ. These are conditional full-rail current screens, not an ADS absolute-limit qualification. A return resistor does not make an unpowered ADS pin HIGH-tolerant. The no-pull/input-only firmware contract is essential. If electrical tolerance of arbitrary MCU output/pull configuration is required, add a dedicated two-channel return buffer with suitable powered-off inputs; that is a stronger requirement than normal controlled bring-up.

Check MISO rise/fall timing at the MCU after adding these resistors. For illustration, 3.3 kΩ×20 pF gives 66 ns time constant, before ADC output delay. The two ADC frames contain 432 bits total: 2 kSPS requires 0.864 Mbit/s and 4 kSPS 1.728 Mbit/s before timing/software margin. Do not select SPI speed from the bare ADC limit alone; verify both throughput and receiver-threshold timing with actual capacitance.

## Reset/brownout minimum

ESP32 has CPU-only, core, system and chip resets. A CPU-only reset does not reset GPIO/peripherals. The [ESP-IDF restart API](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/system/misc_system_api.html#_CPPv411esp_restartv) explicitly notes that `esp_restart()` restarts the CPUs while many peripherals remain configured. Thus “any reset forces GPIO4 LOW” is unsupported.

Keep **one precision MAIN supervisor to CHIP_PU**, around 3.1 V after full threshold/transient calculation, alongside the stock reset network. It provides a defined voltage floor above the module's 3.0 V minimum and actual chip-reset behavior when MAIN fails. Retain firmware brownout detection. The supervisor should affect the real chip enable/reset, not only a firmware status input. It cannot detect every CPU-only restart, and the onboard RC alone does not establish slow-ramp/brownout recovery. No second AFE supervisor/latch hierarchy is needed simply because the load switch exists.

Minimal firmware contract, on every entry and planned restart:

1. Mark acquisition invalid; force GPIO4 LOW **before enabling its output driver or touching other acquisition GPIOs**. Disable pad hold and unintended RTC/peripheral ownership.
2. Wait a qualified interval for ADC_3V3 to discharge; verify the required interval from the real QOD/capacitance/load waveform. A software restart cannot assume it began from a cold ADC.
3. Set the seven forward output latches LOW before enabling their output drivers. Configure GPIO9/13 as inputs with pulls disabled. Verify SPI driver setup does not re-enable pulls or drive MISO.
4. Once MAIN is stable, enable ADC power. Observe rail stabilization, VCAP1/tPOR and clock requirements; then configure both ADCs, both references and exclusive CS selection before marking data valid.
5. Before a planned restart/shutdown, stop acquisition, set controls LOW and disable ADC power. Unplanned watchdog/panic recovery repeats steps1–4; scope actual reset cases rather than assuming they all clear GPIO4.

A precision supervisor plus these firmware steps supports a small usable design. Strict hardware enforcement for **every** CPU reset or arbitrary firmware failure would need an additional external watchdog/gating function and is not established by this minimum circuit. Preserve that distinction in the implementation report. Initial verification uses dummy inputs, battery emulation and no wearer; the accepted USB exclusion remains mechanical prevention, not seated-USB fault tolerance.
