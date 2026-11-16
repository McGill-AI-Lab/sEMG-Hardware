# ADS1298 clamshell validation — summary

Run: 2026-11-16_013247 · hardware on /dev/cu.usbserial-1140 · 114 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 112/114 captures trustworthy |
| A | Shorted-input noise floor | ✕ FAIL | 500 SPS: median 0.59 µVrms; 2000 SPS: median 0.99 µVrms; 4000 SPS: median 1.41 µVrms |
| B | Noise spectrum (PSD) | ! WARN | floor ≈ 38 nV/√Hz, 7 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.491 µVrms, e_ADC ≈ 2.53 µVrms; suggested gain G12 |
| D | Data-rate sweep | ! WARN | RMS grows with rate^0.42 (white noise = 0.50). |
| E | Multichannel correlation | ✕ FAIL | 500 SPS: max |r| = 0.34, channel-average ratio 0.921 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ! WARN | 6 of 19 variants affect the noise |
| G | Internal test signal | ✕ FAIL | median amplitude 1.8536 mV vs 2.000 mV expected (-7.3 %) |
| H | Supply measurement (MVDD) | ✕ FAIL | WiFi off: (AVDD+AVSS)/2 = 1.227 V, DVDD/4 = 0.709 V, ripple ≈ 104 µVrms |
| I | Temperature & long-term drift | ! WARN | temperature -17.49 → -17.36 °C over 118 s (range -17.52–-17.36 °C) |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 2 of 114 captures in this run failed integrity checks.

## A · Shorted-input noise floor — FAIL

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **FAIL** 500 SPS: median 0.59 µVrms, 1.04× expected (worst 11.09×); noisiest CH1 at 6.28 µVrms
- **PASS** 2000 SPS: median 0.99 µVrms, 0.87× expected (worst 1.24×)
- **PASS** 4000 SPS: median 1.41 µVrms, 0.88× expected (worst 1.18×)

## B · Noise spectrum (PSD) — WARN

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **WARN** Other spectral lines on 7 channel spectra; check them against Experiments D (alias?) and F (aggressor?).

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.491 µVrms, e_ADC ≈ 2.53 µVrms; suggested gain G12
- **INFO** 2000 SPS: e_PGA ≈ 0.74 µVrms, e_ADC ≈ 4.91 µVrms; suggested gain G12
- **INFO** 4000 SPS: e_PGA ≈ 1.07 µVrms, e_ADC ≈ 6.99 µVrms; suggested gain G12

## D · Data-rate sweep — WARN

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **WARN** RMS grows with rate^0.42 (white noise = 0.50).
- **WARN** Some lines appear at one data rate only: likely aliases of interference above Nyquist (the sinc³ filter rejects only partially between its nulls).

## E · Multichannel correlation — FAIL

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **FAIL** 500 SPS: max |r| = 0.34, channel-average ratio 0.921 (1 = independent, 2.83 = fully shared)
- **FAIL** 2000 SPS: max |r| = 0.26, channel-average ratio 0.937 (1 = independent, 2.83 = fully shared)
- **FAIL** 4000 SPS: max |r| = 0.25, channel-average ratio 0.925 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 500 SPS, WiFi access point (beacons): noise +44.1 %, pp/rms 11
- **WARN** 500 SPS, WiFi scanning (continuous TX): noise +6.0 %, pp/rms 11
- **WARN** 2000 SPS, WiFi access point (beacons): noise +41.8 %, pp/rms 13
- **WARN** 2000 SPS, WiFi scanning (continuous TX): noise +8.6 %, pp/rms 15
- **WARN** 4000 SPS, WiFi access point (beacons): noise +24.1 %, pp/rms 13, new lines 942 Hz
- **WARN** 4000 SPS, WiFi scanning (continuous TX): noise +6.9 %, pp/rms 15

## G · Internal test signal — FAIL

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **FAIL** median amplitude 1.8536 mV vs 2.000 mV expected (-7.3 %)
- **WARN** Gain cross-check: amplitude spread across gains 1.061× (1.00 ideal); log-log slope vs gain +0.02
- **WARN** Noise on DC test levels exceeds shorted noise in 6 cases: reference noise.

## H · Supply measurement (MVDD) — FAIL

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **FAIL** WiFi off: (AVDD+AVSS)/2 = 1.227 V, DVDD/4 = 0.709 V, ripple ≈ 104 µVrms
- **FAIL** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.227 V, DVDD/4 = 0.709 V, ripple ≈ 82.2 µVrms

## I · Temperature & long-term drift — WARN

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **WARN** temperature -17.49 → -17.36 °C over 118 s (range -17.52–-17.36 °C)
- **INFO** longest useful averaging time ≈ 16.1 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | -214.5 | 6.283 | 24.41 | 3.885 | FAIL |
| A | shorted, each | 6 | HR 500 | 2 | -111.8 | 4.603 | 17.45 | 3.791 | FAIL |
| A | shorted, each | 6 | HR 500 | 3 | -144.2 | 0.5912 | 4.005 | 6.775 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 12.37 | 0.4962 | 3.386 | 6.823 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | 68.88 | 0.5144 | 4.005 | 7.787 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | 79.6 | 0.5887 | 3.91 | 6.642 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | -100.5 | 0.5024 | 3.815 | 7.593 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -342.3 | 0.508 | 3.815 | 7.51 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | -101.1 | 0.6766 | 5.15 | 7.611 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | -120.1 | 0.561 | 3.958 | 7.054 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -268.3 | 0.794 | 5.722 | 7.207 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 27.35 | 0.6283 | 4.196 | 6.678 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -14.98 | 0.7806 | 4.911 | 6.292 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | 170.5 | 0.6962 | 5.245 | 7.534 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | -114.2 | 0.5634 | 4.005 | 7.11 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -357.8 | 0.5662 | 3.624 | 6.401 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | -191.2 | 1.165 | 10.82 | 9.29 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | -119.1 | 0.9295 | 7.963 | 8.567 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -143.5 | 0.9242 | 7.915 | 8.565 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 12.23 | 0.9306 | 7.105 | 7.635 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | 69.18 | 0.9219 | 7.153 | 7.759 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | 79 | 0.9407 | 7.629 | 8.11 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | -100.5 | 0.9436 | 7.772 | 8.237 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -342.6 | 0.9107 | 7.105 | 7.801 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | -100.9 | 1.152 | 9.489 | 8.239 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | -119.8 | 1.006 | 8.392 | 8.343 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -268.1 | 1.409 | 11.44 | 8.121 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 27.32 | 1.128 | 8.249 | 7.315 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -15.55 | 1.108 | 9.06 | 8.176 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | 170.9 | 1.084 | 9.06 | 8.354 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | -114.2 | 1.007 | 7.963 | 7.909 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -358.4 | 0.9733 | 7.963 | 8.181 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | -191.2 | 1.507 | 14.5 | 9.619 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | -119 | 1.346 | 11.11 | 8.257 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -143.7 | 1.363 | 11.54 | 8.469 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 12.17 | 1.348 | 12.06 | 8.948 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | 68.61 | 1.357 | 11.92 | 8.786 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | 79.89 | 1.362 | 11.92 | 8.755 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | -100.5 | 1.364 | 11.21 | 8.216 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -342.6 | 1.353 | 10.68 | 7.896 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | -100.7 | 1.624 | 15.31 | 9.423 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | -119.8 | 1.445 | 11.73 | 8.12 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -267.9 | 1.897 | 15.5 | 8.171 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 27.6 | 1.506 | 12.21 | 8.107 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -15.58 | 1.52 | 11.97 | 7.874 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | 171.5 | 1.51 | 11.97 | 7.928 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | -114.1 | 1.438 | 12.25 | 8.522 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -358.9 | 1.384 | 11.59 | 8.37 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 2.75 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 1.394 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 1.206 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.8355 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.648 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.6047 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.4776 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 2.297 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 1.274 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.9281 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.7248 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.5575 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.4772 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.4033 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 2.787 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 2.032 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 1.607 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 1.112 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.8186 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.5649 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.4242 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 2.237 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 1.514 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 1.196 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.8846 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.63 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.495 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.4377 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 2.748 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 1.576 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 1.133 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.8558 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.6228 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.5454 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.4651 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 2.842 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 1.458 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 1.018 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.7842 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.5922 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.5774 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.4239 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 2.403 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 1.219 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.9365 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.7789 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.5653 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.488 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.4249 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 2.188 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 1.178 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.8918 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.6906 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.5463 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.5158 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.4121 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 5.564 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 2.735 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 2.151 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.622 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.137 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 0.9484 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 0.7877 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 4.569 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 2.439 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.74 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.348 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 0.9999 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 0.8431 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 0.6955 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 5.822 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 3.834 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 2.817 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 2.116 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.383 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 1.063 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 0.7647 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 4.709 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 2.775 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 2.033 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.543 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.099 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 0.8993 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 0.7147 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 5.223 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 2.814 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 2.031 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.556 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.084 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 0.922 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 0.7231 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 5.692 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 2.737 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.873 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.474 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.076 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 0.8786 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 0.7116 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 4.611 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 2.44 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.758 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.369 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.014 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 0.8633 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 0.6972 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 4.353 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 2.355 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.665 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.306 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 0.9873 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 0.8326 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 0.7156 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 7.652 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 3.908 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.906 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 2.263 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.588 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.315 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.063 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 6.599 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 3.528 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.563 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 1.968 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.433 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.173 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 0.9808 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 8.257 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 5.182 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 3.804 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 2.859 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.899 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.455 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.091 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 6.832 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 3.915 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.807 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 2.164 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.521 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.237 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 0.9938 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 7.29 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 3.896 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.762 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 2.144 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.491 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.242 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.003 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 7.959 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 3.89 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.699 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 2.104 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.505 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.244 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 0.9872 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 6.583 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 3.488 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.519 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 1.964 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.424 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.187 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 0.9695 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 6.558 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 3.481 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.462 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 1.905 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.41 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.164 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 0.9576 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | -101.5 | 0.6575 | 4.339 | 6.6 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | -119.4 | 0.5697 | 4.148 | 7.281 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -268.3 | 0.8109 | 5.77 | 7.115 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 27.57 | 0.6137 | 4.053 | 6.605 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -14.71 | 0.6276 | 4.339 | 6.914 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | 170.5 | 0.5769 | 4.053 | 7.026 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | -114.5 | 0.5601 | 3.862 | 6.895 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -357.8 | 0.5656 | 4.292 | 7.587 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | -101.9 | 0.7197 | 5.341 | 7.421 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | -119.4 | 0.5683 | 4.101 | 7.216 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -268.4 | 0.8122 | 5.77 | 7.104 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 27.68 | 0.6021 | 4.339 | 7.207 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -14.52 | 0.6431 | 4.435 | 6.895 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | 170.6 | 0.5835 | 4.435 | 7.6 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | -114.5 | 0.5967 | 4.101 | 6.873 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -357.8 | 0.5714 | 4.911 | 8.595 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | -102.1 | 0.6409 | 4.673 | 7.292 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | -119.7 | 0.5384 | 3.862 | 7.174 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -268.6 | 0.7975 | 5.293 | 6.637 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 27.97 | 0.5975 | 4.148 | 6.943 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -14.64 | 0.6355 | 5.436 | 8.554 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | 170.5 | 0.5841 | 4.196 | 7.184 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | -114.3 | 0.5863 | 4.005 | 6.832 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -357.6 | 0.5256 | 3.719 | 7.076 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | -101.8 | 0.6474 | 5.77 | 8.912 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | -119.8 | 0.562 | 3.576 | 6.364 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -268.4 | 0.81 | 5.627 | 6.947 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 28.11 | 0.6056 | 4.816 | 7.952 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -14.39 | 0.6549 | 4.768 | 7.281 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | 170.6 | 0.5783 | 4.148 | 7.173 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | -113.8 | 0.5469 | 4.292 | 7.847 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -357.5 | 0.5428 | 4.196 | 7.73 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | -101.5 | 1.187 | 12.87 | 10.85 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | -119.7 | 0.5846 | 4.768 | 8.156 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -268.5 | 1.245 | 12.73 | 10.23 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 27.71 | 0.639 | 5.007 | 7.835 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -14.59 | 1.165 | 12.35 | 10.6 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | 171.2 | 1.23 | 12.68 | 10.32 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | -113.9 | 0.5581 | 4.053 | 7.262 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -358.2 | 0.5711 | 4.244 | 7.43 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | -101.3 | 0.7292 | 6.247 | 8.566 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | -119.9 | 0.5471 | 3.91 | 7.147 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -268.2 | 0.8562 | 7.296 | 8.521 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 27.55 | 0.6359 | 4.387 | 6.899 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -14.51 | 0.7161 | 7.534 | 10.52 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | 170.9 | 0.695 | 6.723 | 9.674 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | -114.1 | 0.5616 | 4.005 | 7.133 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -358.1 | 0.5423 | 3.91 | 7.21 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | -102.4 | 0.6107 | 3.386 | 5.544 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | -120.1 | 0.5151 | 3.147 | 6.109 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -268 | 0.8097 | 5.245 | 6.478 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 27.66 | 0.6299 | 3.481 | 5.526 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -14.18 | 0.5417 | 2.909 | 5.369 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | 170.7 | 0.5996 | 3.862 | 6.442 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | -113.9 | 0.5369 | 3.338 | 6.217 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -357.3 | 0.5153 | 3.004 | 5.83 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | -102 | 1.16 | 9.108 | 7.849 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | -120.1 | 1 | 8.583 | 8.582 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -268 | 1.38 | 10.63 | 7.706 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 27.34 | 1.095 | 8.631 | 7.884 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -14.32 | 1.069 | 7.963 | 7.446 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | 170.6 | 1.057 | 8.44 | 7.986 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | -113.9 | 0.9918 | 8.488 | 8.558 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -358 | 0.9888 | 7.677 | 7.764 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | -101.9 | 1.13 | 9.108 | 8.059 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | -120.1 | 1.008 | 7.677 | 7.616 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -268.1 | 1.381 | 11.35 | 8.218 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 27.52 | 1.102 | 8.345 | 7.574 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -14.26 | 1.088 | 8.249 | 7.585 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | 170.3 | 1.083 | 9.298 | 8.583 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | -113.8 | 1.02 | 7.82 | 7.671 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -357.9 | 0.9918 | 7.534 | 7.597 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | -101.7 | 1.208 | 9.251 | 7.66 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | -120.3 | 0.9996 | 8.154 | 8.157 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -268.2 | 1.429 | 11.87 | 8.311 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 27.8 | 1.091 | 9.775 | 8.96 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -14.27 | 1.153 | 8.678 | 7.527 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | 170.7 | 1.136 | 8.297 | 7.303 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | -113.8 | 1.002 | 7.486 | 7.471 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -357.9 | 0.9985 | 7.82 | 7.832 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | -101.6 | 2.011 | 24.03 | 11.95 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | -119.8 | 1.089 | 10.4 | 9.55 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -268.4 | 2.118 | 27.04 | 12.76 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 27.62 | 1.096 | 9.155 | 8.352 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -14.51 | 1.958 | 23.51 | 12.01 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | 171.6 | 2.091 | 24.6 | 11.76 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | -113.8 | 1.001 | 7.105 | 7.095 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -358.8 | 1.034 | 9.155 | 8.858 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | -101.6 | 1.306 | 18.22 | 13.94 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | -120.1 | 1.015 | 9.06 | 8.923 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -268.3 | 1.521 | 17.12 | 11.25 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 27.42 | 1.099 | 8.726 | 7.939 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -14.33 | 1.268 | 17.88 | 14.1 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | 171.8 | 1.294 | 18.79 | 14.52 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | -113.9 | 1.007 | 7.868 | 7.815 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -358.8 | 0.9836 | 8.154 | 8.29 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | -102.1 | 1.12 | 8.345 | 7.449 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | -120.4 | 1.002 | 7.391 | 7.379 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -268 | 1.354 | 9.823 | 7.256 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 28.19 | 1.079 | 7.343 | 6.806 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -14.03 | 1.086 | 7.391 | 6.803 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | 171.1 | 1.011 | 6.962 | 6.886 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | -113.8 | 0.9957 | 7.296 | 7.327 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -357.9 | 0.9796 | 6.771 | 6.912 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | -101.6 | 1.582 | 11.92 | 7.536 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | -120.3 | 1.429 | 13.35 | 9.344 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -267.8 | 1.882 | 14.35 | 7.625 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 27.72 | 1.512 | 12.25 | 8.105 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -14.27 | 1.501 | 13.49 | 8.993 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | 170.6 | 1.502 | 12.02 | 8 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | -114 | 1.436 | 12.06 | 8.402 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -358.2 | 1.385 | 12.11 | 8.742 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | -101.8 | 1.626 | 13.26 | 8.152 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | -120.1 | 1.458 | 12.54 | 8.602 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -267.5 | 1.887 | 16.5 | 8.742 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 27.34 | 1.533 | 13.78 | 8.989 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -14.59 | 1.534 | 13.02 | 8.486 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | 171 | 1.536 | 13.69 | 8.909 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | -113.8 | 1.458 | 12.54 | 8.6 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -358.3 | 1.415 | 11.83 | 8.357 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | -101.5 | 1.672 | 13.59 | 8.128 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | -120.2 | 1.428 | 12.45 | 8.713 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -267.9 | 1.959 | 15.31 | 7.815 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 27.28 | 1.535 | 12.92 | 8.419 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -14.22 | 1.604 | 12.11 | 7.551 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | 171.4 | 1.605 | 13.26 | 8.258 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | -113.8 | 1.442 | 12.59 | 8.731 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -358.6 | 1.404 | 11.21 | 7.981 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | -101.5 | 2.313 | 30.14 | 13.03 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | -119.7 | 1.493 | 13.3 | 8.91 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -267.9 | 2.467 | 30.14 | 12.22 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 27.05 | 1.508 | 12.97 | 8.601 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -14.54 | 2.208 | 25.56 | 11.58 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | 171.9 | 2.342 | 27.99 | 11.95 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | -113.9 | 1.431 | 12.4 | 8.665 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -359.1 | 1.415 | 13.07 | 9.23 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | -101.4 | 1.803 | 25.56 | 14.18 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | -119.6 | 1.441 | 12.68 | 8.803 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -267.8 | 2.041 | 25.46 | 12.48 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 26.99 | 1.522 | 13.11 | 8.616 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -14.53 | 1.697 | 22.41 | 13.21 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | 171.7 | 1.735 | 25.22 | 14.54 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | -113.6 | 1.445 | 11.87 | 8.214 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -358.8 | 1.388 | 11.44 | 8.246 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | -102.1 | 1.574 | 11.11 | 7.059 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | -119.6 | 1.441 | 9.537 | 6.619 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -267.4 | 1.891 | 13.73 | 7.262 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 27.6 | 1.503 | 10.68 | 7.104 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -14.26 | 1.486 | 10.4 | 6.995 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | 171.1 | 1.486 | 10.82 | 7.282 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | -113.6 | 1.417 | 10.59 | 7.472 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -358.3 | 1.374 | 9.584 | 6.978 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | -1562 | 1.958 |  |  | amplitude 1.5566 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | -1550 | 0.6233 |  |  | amplitude 1.5422 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -1576 | 0.6519 |  |  | amplitude 1.5424 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | -1428 | 0.6141 |  |  | amplitude 1.5430 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -1355 | 0.604 |  |  | amplitude 1.5443 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -1359 | 0.6248 |  |  | amplitude 1.5405 mV (-23.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | -1536 | 0.6918 |  |  | amplitude 1.5423 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -1782 | 0.6263 |  |  | amplitude 1.5411 mV (-22.9 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | -3194 | 2.444 |  |  | amplitude 2.1561 mV (+7.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | -3214 | 2.431 |  |  | amplitude 2.1769 mV (+8.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -3295 | 2.513 |  |  | amplitude 2.1836 mV (+9.2 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | -3179 | 2.451 |  |  | amplitude 2.1832 mV (+9.2 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -3109 | 2.369 |  |  | amplitude 2.1726 mV (+8.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -2954 | 2.388 |  |  | amplitude 2.1786 mV (+8.9 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | -3223 | 2.518 |  |  | amplitude 2.1910 mV (+9.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -3501 | 2.353 |  |  | amplitude 2.1783 mV (+8.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | -1561 | 2.713 |  |  | amplitude 1.5567 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | -1549 | 1.372 |  |  | amplitude 1.5426 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -1575 | 1.096 |  |  | amplitude 1.5428 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | -1427 | 1.125 |  |  | amplitude 1.5433 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -1355 | 1.219 |  |  | amplitude 1.5447 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -1359 | 1.12 |  |  | amplitude 1.5409 mV (-23.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | -1535 | 1.11 |  |  | amplitude 1.5426 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -1781 | 1.06 |  |  | amplitude 1.5414 mV (-22.9 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | -3192 | 3.118 |  |  | amplitude 2.1527 mV (+7.6 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | -3212 | 2.907 |  |  | amplitude 2.1737 mV (+8.7 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -3291 | 2.992 |  |  | amplitude 2.1802 mV (+9.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | -3176 | 3.056 |  |  | amplitude 2.1797 mV (+9.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -3107 | 2.791 |  |  | amplitude 2.1695 mV (+8.5 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -2951 | 2.901 |  |  | amplitude 2.1753 mV (+8.8 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | -3220 | 2.943 |  |  | amplitude 2.1877 mV (+9.4 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -3499 | 2.803 |  |  | amplitude 2.1749 mV (+8.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | -1561 | 3.24 |  |  | amplitude 1.5567 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | -1549 | 1.982 |  |  | amplitude 1.5429 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -1575 | 1.576 |  |  | amplitude 1.5429 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | -1427 | 1.635 |  |  | amplitude 1.5435 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -1354 | 1.783 |  |  | amplitude 1.5447 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -1359 | 1.618 |  |  | amplitude 1.5409 mV (-23.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | -1535 | 1.568 |  |  | amplitude 1.5426 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -1782 | 1.567 |  |  | amplitude 1.5414 mV (-22.9 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | -3191 | 3.537 |  |  | amplitude 2.1505 mV (+7.5 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | -3211 | 3.33 |  |  | amplitude 2.1714 mV (+8.6 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -3290 | 3.435 |  |  | amplitude 2.1780 mV (+8.9 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | -3175 | 3.453 |  |  | amplitude 2.1774 mV (+8.9 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -3106 | 3.285 |  |  | amplitude 2.1672 mV (+8.4 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -2950 | 3.278 |  |  | amplitude 2.1731 mV (+8.7 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | -3218 | 3.284 |  |  | amplitude 2.1854 mV (+9.3 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -3498 | 3.288 |  |  | amplitude 2.1727 mV (+8.6 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.402e+06 | 54.75 |  |  | (AVDD+AVSS)/2 -15.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.402e+06 | 59.36 |  |  | (AVDD+AVSS)/2 -15.03 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 7.066e+05 | 125.9 |  |  | DVDD/4 -14.35 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 7.113e+05 | 143.9 |  |  | DVDD/4 -13.79 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.316e+06 | 82.61 |  |  | (AVDD+AVSS)/2 -20.24 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.317e+06 | 81.88 |  |  | (AVDD+AVSS)/2 -20.19 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 9.626e+05 | 199.4 |  |  | (AVDD+AVSS)/2 -41.66 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 9.621e+05 | 199.8 |  |  | (AVDD+AVSS)/2 -41.69 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.402e+06 | 131.4 |  |  | (AVDD+AVSS)/2 -15.02 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.402e+06 | 91.3 |  |  | (AVDD+AVSS)/2 -15.02 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 7.068e+05 | 46.13 |  |  | DVDD/4 -14.33 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 7.114e+05 | 44.34 |  |  | DVDD/4 -13.77 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.316e+06 | 157 |  |  | (AVDD+AVSS)/2 -20.24 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.317e+06 | 155.2 |  |  | (AVDD+AVSS)/2 -20.19 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 9.625e+05 | 72.31 |  |  | (AVDD+AVSS)/2 -41.67 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 9.62e+05 | 73.11 |  |  | (AVDD+AVSS)/2 -41.70 % |
