# ADS1298 clamshell validation — summary

Run: 2026-11-15_133147 · hardware on /dev/cu.usbserial-1140 · 4 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✓ PASS | 4/4 captures trustworthy |
| A | Shorted-input noise floor | – SKIP | no data |
| B | Noise spectrum (PSD) | – SKIP |  |
| C | Gain sweep (PGA vs ADC noise) | – SKIP |  |
| D | Data-rate sweep | – SKIP |  |
| E | Multichannel correlation | – SKIP |  |
| F | Aggressor toggling (ESP32, USB, SPI) | – SKIP |  |
| G | Internal test signal | – SKIP |  |
| H | Supply measurement (MVDD) | – SKIP |  |
| I | Temperature & long-term drift | – SKIP |  |

## P · Prerequisites & data integrity — PASS

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **PASS** All 4 captures passed the integrity checks.

## A · Shorted-input noise floor — SKIP

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.


## B · Noise spectrum (PSD) — SKIP

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **SKIP** No Experiment A data.

## C · Gain sweep (PGA vs ADC noise) — SKIP

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **SKIP** Not enough gain-sweep data.

## D · Data-rate sweep — SKIP

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **SKIP** Needs Experiment A at two or more data rates.

## E · Multichannel correlation — SKIP

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **SKIP** Needs an Experiment A capture with channel_plan 'all'.

## F · Aggressor toggling (ESP32, USB, SPI) — SKIP

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **SKIP** No captures.

## G · Internal test signal — SKIP

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.


## H · Supply measurement (MVDD) — SKIP

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **SKIP** No captures.

## I · Temperature & long-term drift — SKIP

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **SKIP** No capture.

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
