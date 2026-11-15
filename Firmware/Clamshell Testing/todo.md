# sEMG wearable product development plan

This is a gated engineering test plan for moving the current ESP32-S3 + ADS1298 breadboard setup toward a wearable product. Do not add wireless, a second ADC, and a custom PCB simultaneously. Preserve a known-good reference at every phase and answer one new question at a time.

## Proposed system target

- [ ] Define whether this is a research/fitness product or a medical device.
- [ ] Define the required recording duration.
- [ ] Define the required wireless range.
- [ ] Define acceptable sample loss, if any.
- [ ] Define the intended sEMG frequency band.
- [ ] Target 16 simultaneous channels using two ADS1298s.
- [ ] Start at 1,000 samples/s per channel.
- [ ] Keep the architecture capable of 2,000 samples/s per channel.
- [ ] Preserve raw 24-bit acquisition internally during development.
- [ ] Add BLE streaming with local buffering or local storage.
- [ ] Use battery-only operation while the device is attached to a person.
- [ ] Give every sample a sequence count and explicitly report lost samples.

Most sEMG energy is below approximately 400–500 Hz. Sampling at 1 kSPS is a practical minimum when the input is appropriately low-pass filtered. A 2 kSPS rate gives better anti-aliasing margin and is commonly preferred.

References:

- [Analysis and Biophysics of Surface EMG](https://pmc.ncbi.nlm.nih.gov/articles/PMC7594523)
- [Surface EMG detection, conditioning and preprocessing: best practices](https://www.robertomerletti.it/assets/pdfs/publications/2020_Tutorial_Merletti_Cerone.pdf)

## Phase 1: Establish one trustworthy channel

Start with the ADS1298 internal generator on channel 1.

### Correct the known firmware problems

- [ ] Change the internal test configuration from `0x51` to `0x11`:

```cpp
// Current
constexpr uint8_t CONFIG2_INTERNAL_TEST_1MV_2HZ = 0x51;

// Corrected
constexpr uint8_t CONFIG2_INTERNAL_TEST_1MV_2HZ = 0x11;
```

- [ ] Correct the CONFIG1 comment: `0x06` is low-power mode at 250 SPS, not high-resolution mode at 500 SPS.
- [ ] Reuse the conservative PWDN/reset timing from the working register diagnostic.
- [ ] Use either the START pin or START command consistently instead of both.
- [ ] Stop acquisition with an explicit error if the ADS1298 ID or configuration readback is wrong.

Required configuration readback:

```text
ID      = 0x92
CONFIG1 = 0x06
CONFIG2 = 0x11
CONFIG3 = 0xC0
CH1SET  = 0x05
```

### Run the CH1 test

- [ ] Capture 30 seconds of internal CH1 data.
- [ ] Count DRDY events.
- [ ] Count captured frames.
- [ ] Validate the 24-bit status word in every frame.
- [ ] Confirm that no frame is entirely zero or entirely `0xFF`.
- [ ] Calculate the measured sample rate.
- [ ] Calculate signal minimum, maximum, mean, peak-to-peak amplitude and frequency.
- [ ] Repeat after ten complete power cycles.

### Replace the Boolean DRDY flag

A Boolean cannot tell whether multiple DRDY events occurred before `loop()` handled the first one.

```cpp
volatile uint32_t pendingSamples = 0;

void IRAM_ATTR adsDrdyISR() {
    pendingSamples++;
}
```

### Phase 1 pass gate

- [ ] ID and all configuration readbacks are correct.
- [ ] Received frame count is within one frame of the expected count.
- [ ] Status words remain valid.
- [ ] Signal frequency is approximately 1.953 Hz.
- [ ] No samples are silently lost.
- [ ] All ten power-cycle tests give the same result.

## Phase 2: Validate all eight channels internally

### Test each channel separately

For each channel from 1 through 8:

- [ ] Send STOP and SDATAC.
- [ ] Write `0x81` to all CHnSET registers.
- [ ] Write `0x05` only to the selected channel.
- [ ] Read all CHnSET registers back and verify them.
- [ ] Restart conversions.
- [ ] Discard at least the first three samples for digital-filter settling.
- [ ] Record at least ten complete test-signal periods.
- [ ] Record frequency, peak-to-peak amplitude, mean, lost frames and status errors.

Channel `n` begins at this offset in the 27-byte frame:

```cpp
int offset = 3 + 3 * channelIndex;  // channelIndex is 0 through 7
```

Results table:

| Channel | Frequency | Peak-to-peak | Mean | Lost frames | Status errors | Result |
|---|---:|---:|---:|---:|---:|---|
| CH1 | | | | | | |
| CH2 | | | | | | |
| CH3 | | | | | | |
| CH4 | | | | | | |
| CH5 | | | | | | |
| CH6 | | | | | | |
| CH7 | | | | | | |
| CH8 | | | | | | |

### Test all eight channels simultaneously

- [ ] Write `0x05` to registers `0x05` through `0x0C`.
- [ ] Parse all eight results from every 27-byte frame.
- [ ] Print one CSV or binary record per frame rather than eight independent text lines.
- [ ] Measure channel-to-channel gain variation.
- [ ] Measure channel offset.
- [ ] Measure correlation and phase difference between channels.
- [ ] Confirm that enabling all channels does not change the sample count.
- [ ] Confirm that output formatting does not cause missed frames.

Suggested debug format:

```text
sample,adc_status,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8
```

### Phase 2 pass gate

- [ ] Every channel passes individually.
- [ ] All eight channels pass simultaneously.
- [ ] All channel register readbacks are correct.
- [ ] No sample or frame loss occurs during the defined test duration.
- [ ] Channel-to-channel differences are measured and documented.

## Phase 3: Characterize the external analog inputs

After the internal tests pass, disable the internal generator and select normal channel inputs.

### Input-short noise test

Set each channel MUX to its internal short.

- [ ] Measure mean ADC code.
- [ ] Measure RMS noise.
- [ ] Measure peak-to-peak noise.
- [ ] Measure 50/60 Hz content.
- [ ] Compare noise with the radio off and transmitting.
- [ ] Compare one active channel with all channels active.
- [ ] Repeat for all intended PGA gains.

### DC and sine-wave tests

Use a properly biased differential signal source.

- [ ] Apply zero differential voltage at a valid common-mode voltage.
- [ ] Sweep differential DC input across the intended range.
- [ ] Test sine waves at 10, 50, 100, 250, 400 and 450 Hz.
- [ ] Repeat at several amplitudes.
- [ ] Repeat at PGA gains 6 and 12.
- [ ] Measure amplitude error.
- [ ] Measure phase error.
- [ ] Measure distortion.
- [ ] Record clipping thresholds.
- [ ] Repeat with realistic cable and electrode impedances.

The ideal input-referred code size at gain 6 is:

```text
2.4 V / (6 × 8,388,607) ≈ 47.7 nV/code
```

This does not mean the product has 47.7 nV useful resolution. Measure the effective resolution because input noise, electrode noise, reference noise and interference dominate.

Choose the highest gain that does not clip during:

- [ ] Maximum muscle contraction.
- [ ] Electrode movement.
- [ ] Electrode reconnect.
- [ ] Common-mode disturbances.

### Anti-aliasing test

- [ ] Inject frequencies above the intended signal band.
- [ ] Check whether they appear as false lower-frequency signals.
- [ ] For 1 kSPS operation, establish an analog bandwidth below 500 Hz, typically around 400–450 Hz.
- [ ] Use 2 kSPS if reliable information up to approximately 500 Hz is required.

### Phase 3 pass gate

- [ ] Input-referred noise meets the product requirement.
- [ ] No unacceptable clipping occurs over the expected electrode and motion range.
- [ ] Gain and frequency response are documented.
- [ ] The analog and digital filters prevent unacceptable aliasing.

## Phase 4: Prove sample integrity before adding wireless

Define a block record containing:

```text
protocol version
device ID
session ID
block sequence number
first sample index
sample rate
channel mask
samples per block
ADC status/error flags
battery state
payload
CRC
```

- [ ] Use a continuously increasing 64-bit sample index.
- [ ] Timestamp the start of each block.
- [ ] Derive individual sample time from sample index and sample rate.
- [ ] Do not timestamp every sample using `millis()`.
- [ ] Add a CRC to detect corrupted blocks.
- [ ] Add explicit counters for acquisition loss and transmission loss.

Sample timing should be reconstructed as:

```text
sample_time = block_time + sample_offset / sample_rate
```

Run these tests over USB before introducing BLE:

- [ ] 10-minute continuous capture.
- [ ] One-hour continuous capture.
- [ ] CPU stress while acquiring.
- [ ] Deliberately slow output to exercise buffer overflow.
- [ ] Power interruption and restart.
- [ ] Sequence-number wrap or simulated wrap.
- [ ] Corrupt a packet and verify CRC rejection.
- [ ] Confirm that lost data are reported rather than hidden.

### Phase 4 pass gate

- [ ] A one-hour USB capture has the expected sample count.
- [ ] Sequence numbers are continuous.
- [ ] Timing can be reconstructed without software-loop jitter.
- [ ] Buffer overflows and corrupted packets are detectable.

## Phase 5: Add the second ADS1298

Use two ADS1298s in cascade configuration first. Daisy chain can be evaluated later.

### Initial two-ADC architecture

- [ ] Share SCLK.
- [ ] Share MOSI/DIN.
- [ ] Share MISO/DOUT using separate chip selects.
- [ ] Give each ADC a separate CS.
- [ ] Keep separate DRDY signals during initial debugging.
- [ ] Share START.
- [ ] Share the ADS master clock.
- [ ] Prefer a dedicated shared oscillator for the product design.

TI recommends sharing CLK and START to synchronize multiple converters. One ADS can output its internal oscillator to the other, but a dedicated oscillator makes synchronization independent of either ADC's health.

Reference: [ADS1298 datasheet and multiple-device configuration](https://www.ti.com/lit/ds/symlink/ads1298.pdf)

### Synchronization test

- [ ] Verify ADC 1 independently using its CS.
- [ ] Verify ADC 2 independently using its CS.
- [ ] Confirm both return `ID=0x92`.
- [ ] Configure identical sample rates.
- [ ] Feed both from the same master clock.
- [ ] Pulse the common START signal.
- [ ] Capture both DRDY signals with an oscilloscope or logic analyzer.
- [ ] Measure and document the fixed DRDY offset.
- [ ] Route the internal test generator to all 16 channels.
- [ ] Confirm phase alignment across both devices.
- [ ] Run an hour-long sample-count test.

At 1 kSPS, there is 1 ms to read both devices. Two frames contain:

```text
2 × 27 bytes = 54 bytes = 432 SPI bits
```

| SPI clock | Approximate two-frame transfer time |
|---:|---:|
| 1 MHz | 432 µs |
| 2 MHz | 216 µs |
| 4 MHz | 108 µs |
| 8 MHz | 54 µs |

- [ ] Start at 2–4 MHz SPI and validate signal integrity.
- [ ] Avoid relying on 1 MHz at 2 kSPS because the 500 µs frame period leaves little margin.

### Evaluate daisy chain only after cascade passes

Daisy-chain disadvantages include an extra clock between device data sets, limited downstream register readback and shared configuration behavior.

- [ ] Quantify pin savings.
- [ ] Confirm whether both ADCs always use identical configuration.
- [ ] Implement the required extra SCLK between device data sets.
- [ ] Verify frame parsing and error recovery.
- [ ] Decide whether the pin saving justifies the debugging and diagnostic limitations.

### Phase 5 pass gate

- [ ] Both ADCs pass independently.
- [ ] Both ADCs remain synchronized for the required recording duration.
- [ ] All 16 channels pass internal testing.
- [ ] The ESP32 reads both frames with comfortable timing margin.

## Phase 6: Calculate and design wireless bandwidth

Raw ADS frame rates:

| ADCs/channels | Sample rate | Raw frame rate | One-hour data |
|---|---:|---:|---:|
| 1 ADC / 8 ch | 1 kSPS | 27 kB/s | 97.2 MB |
| 1 ADC / 8 ch | 2 kSPS | 54 kB/s | 194.4 MB |
| 2 ADCs / 16 ch | 1 kSPS | 54 kB/s | 194.4 MB |
| 2 ADCs / 16 ch | 2 kSPS | 108 kB/s | 388.8 MB |

These figures include each ADC's status word but exclude wireless headers, timestamps, CRCs and retransmissions. Budget an additional 10–25%.

BLE LE 2M has a 2 Mb/s physical rate, but real application throughput is lower and depends on the central device, MTU, connection interval, packet length and RF environment.

Reference: [Bluetooth LE physical-layer specification](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core_v7.0/out/en/low-energy-controller/radiophysical-layer-rfphy--specification.html)

### Firmware architecture

```text
ADS DRDY
   ↓
high-priority acquisition task
   ↓
RAM ring buffer
   ├── local raw storage
   └── BLE packetization task
          ↓
       phone/computer
```

- [ ] Ensure the radio task can never block SPI acquisition.
- [ ] Keep raw 24-bit values during characterization.
- [ ] Measure system noise and effective number of bits.
- [ ] Decide whether BLE payloads can use 16-, 18-, 20- or 24-bit samples.

At signed 16 bits:

```text
16 channels × 2 bytes × 1000 SPS = 32 kB/s
```

### Phase 6 pass gate

- [ ] Required payload bandwidth is calculated with overhead and retransmission margin.
- [ ] The selected format does not discard useful measured resolution.
- [ ] Acquisition remains correct when wireless transmission stalls.

## Phase 7: Wireless verification

Use BLE for configuration and live streaming. Consider Wi-Fi only for laboratory bulk transfer or cases where its additional power is acceptable.

### BLE tests

- [ ] Test LE 1M PHY.
- [ ] Test LE 2M PHY.
- [ ] Test several phones and computers.
- [ ] Test at 1, 3, 5 and 10 metres.
- [ ] Test with the body between transmitter and receiver.
- [ ] Test while walking and moving the arm.
- [ ] Test in a crowded 2.4 GHz environment.
- [ ] Test with nearby Wi-Fi traffic.
- [ ] Test reconnect after leaving range.
- [ ] Test when the receiving application is paused or backgrounded.
- [ ] Test maximum recording duration.
- [ ] Verify that acquisition continues during wireless loss.

### Wireless pass gate

- [ ] Radio operation causes no acquisition loss.
- [ ] Every missing wireless block is detectable using sequence numbers.
- [ ] Reconnection does not require restarting acquisition.
- [ ] Clean-environment throughput is at least twice the required sustained payload rate.
- [ ] Buffering covers the specified RF outage duration.

Initial buffer target:

```text
16 channels, 1 kSPS, raw frames: 54–108 kB for 1–2 seconds
16 channels, 2 kSPS, raw frames: 108–216 kB for 1–2 seconds
```

- [ ] If recordings cannot tolerate loss, add local flash or microSD.
- [ ] Treat local storage as the authoritative recording and BLE as live preview.

## Phase 8: Battery and power tests

Move to battery power before attaching the system to a person.

### Measure current in every state

- [ ] Deep sleep.
- [ ] Idle and BLE advertising.
- [ ] One ADC acquiring.
- [ ] Two ADCs acquiring.
- [ ] BLE connected without streaming.
- [ ] Continuous BLE streaming.
- [ ] Local storage writing.
- [ ] Maximum combined load.

Estimate runtime using measured current:

```text
estimated hours ≈ usable battery capacity in mAh / average current in mA
```

- [ ] Apply capacity, temperature, aging and regulator-efficiency margin.
- [ ] Measure actual runtime over multiple charge cycles.
- [ ] Measure supply ripple during BLE transmission bursts.
- [ ] Compare ADC noise with radio off and transmitting.
- [ ] Test brownout during connection and storage writes.
- [ ] Test battery depletion and clean shutdown.
- [ ] Validate battery-state reporting.
- [ ] Test charging temperature.
- [ ] Decide whether operation while charging is allowed.

### Safety restriction

- [ ] Do not wear the prototype while it is connected to a laptop, grounded oscilloscope or bench function generator unless appropriate patient isolation has been designed and verified.

## Phase 9: Replace the breadboard with a first wearable PCB

The first custom PCB should prioritize observability over minimum size.

### Include in the design

- [ ] Test pads for every supply rail.
- [ ] Test pads for CLK, START, DRDY, CS, SCLK, DIN and DOUT.
- [ ] Separate analog and digital power filtering.
- [ ] Local decoupling at every ADS supply pin.
- [ ] Short differential electrode traces.
- [ ] Short SPI traces.
- [ ] Antenna separation from ADC inputs and electrode cables.
- [ ] Programming/debug connector.
- [ ] Current-measurement jumper.
- [ ] Optional zero-ohm links around sensitive sections.
- [ ] Hardware revision identification.

### Review before fabrication

- [ ] Power-tree limits.
- [ ] ADS1298 reference capacitors.
- [ ] Clock routing.
- [ ] Ground return paths.
- [ ] Input protection.
- [ ] ESD protection.
- [ ] Battery charger and protection circuit.
- [ ] Antenna clearance.
- [ ] Isolation assumptions.

### PCB bring-up

- [ ] Run the same register diagnostic used on the breadboard.
- [ ] Run the same internal CH1 test.
- [ ] Run the same eight-channel test.
- [ ] Run the same two-ADC test.
- [ ] Compare PCB noise against the breadboard reference.
- [ ] Investigate every regression before adding new features.

## Phase 10: Electrode and wearable testing

Test in this order:

- [ ] Electrode phantom or precision resistor network.
- [ ] Battery-powered recording on a static subject.
- [ ] Controlled contractions.
- [ ] Repeated electrode placement.
- [ ] Walking and normal motion.
- [ ] Sweat and long-duration wear.
- [ ] Different body sizes and skin conditions.

Record:

- [ ] Electrode impedance.
- [ ] Baseline noise.
- [ ] Motion artifact.
- [ ] Power-line interference.
- [ ] Channel saturation.
- [ ] Electrode detachment.
- [ ] Cross-talk between nearby muscles.
- [ ] Temperature under the enclosure.
- [ ] Mechanical strain at cables and connectors.

- [ ] Do not describe prototype measurements as clinical data until intended use, validation and regulatory requirements are defined.

## Phase 11: Product reliability, security and safety

### Reliability testing

- [ ] ESD at electrode and enclosure contacts.
- [ ] Radiated and conducted RF immunity.
- [ ] Radio coexistence.
- [ ] Drop and vibration.
- [ ] Connector insertion cycles.
- [ ] Sweat and cleaning exposure.
- [ ] Battery abuse and charger faults.
- [ ] Thermal limits.
- [ ] Firmware-update interruption.
- [ ] Corrupted settings.
- [ ] Unresponsive ADC.
- [ ] Stuck DRDY.
- [ ] Wireless denial or malformed commands.

### Security testing

- [ ] Secure pairing.
- [ ] Encrypted wireless communication.
- [ ] Authenticated firmware updates.
- [ ] Device-unique credentials.
- [ ] Protection against firmware downgrade.
- [ ] Documented vulnerability-response process.

### Medical-device path, if applicable

- [ ] Start a risk-management file early.
- [ ] Determine applicable electrical-safety and EMC standards.
- [ ] Define essential performance.
- [ ] Define leakage-current and isolation requirements.
- [ ] Establish software lifecycle and traceability requirements.
- [ ] Establish cybersecurity requirements.

References:

- [ISO 14971 medical-device risk management](https://www.iso.org/standard/72704.html)
- [IEC 60601-1-2 electromagnetic disturbances](https://webstore.iec.ch/en/publication/2590)
- [FDA wireless medical devices](https://www.fda.gov/medical-devices/digital-health-center-excellence/wireless-medical-devices)
- [FDA medical-device cybersecurity guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-system-considerations-and-content-premarket-submissions)

## Immediate next milestone

Do not start the second ADC or wireless implementation yet.

- [ ] Correct the channel-1 internal-test firmware.
- [ ] Verify configuration readbacks.
- [ ] Capture 30 seconds with exact DRDY and frame counts.
- [ ] Validate status words and internal-signal frequency.
- [ ] Repeat through ten power cycles.
- [ ] Extend the same verified implementation to all eight internal channels.
- [ ] Complete an eight-channel simultaneous capture without frame loss.

Once that milestone passes, add the second ADS1298 in cascade configuration and repeat the same tests across 16 channels.
