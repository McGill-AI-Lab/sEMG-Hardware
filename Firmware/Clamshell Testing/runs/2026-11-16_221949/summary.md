# ADS1298 clamshell validation — summary

Run: 2026-11-16_221949 · hardware on /dev/cu.usbserial-1140 · 114 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 113/114 captures trustworthy |
| A | Shorted-input noise floor | ✕ FAIL | 500 SPS: median 0.672 µVrms; 2000 SPS: median 1.01 µVrms; 4000 SPS: median 1.4 µVrms |
| B | Noise spectrum (PSD) | ! WARN | floor ≈ 38 nV/√Hz, 9 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.488 µVrms, e_ADC ≈ 2.48 µVrms; suggested gain G8 |
| D | Data-rate sweep | ! WARN | RMS grows with rate^0.35 (white noise = 0.50). |
| E | Multichannel correlation | ✕ FAIL | 500 SPS: max |r| = 0.37, channel-average ratio 0.909 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ! WARN | 5 of 19 variants affect the noise |
| G | Internal test signal | ✕ FAIL | median amplitude 1.8792 mV vs 2.000 mV expected (-6.0 %) |
| H | Supply measurement (MVDD) | ✕ FAIL | WiFi off: (AVDD+AVSS)/2 = 1.260 V, DVDD/4 = 0.711 V, ripple ≈ 40.6 µVrms |
| I | Temperature & long-term drift | ! WARN | temperature -9.24 → -9.16 °C over 119 s (range -9.24–-9.15 °C) |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 1 of 114 captures in this run failed integrity checks.

## A · Shorted-input noise floor — FAIL

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **FAIL** 500 SPS: median 0.672 µVrms, 1.19× expected (worst 14.65×); noisiest CH1 at 8.3 µVrms
- **PASS** 2000 SPS: median 1.01 µVrms, 0.89× expected (worst 1.24×)
- **PASS** 4000 SPS: median 1.4 µVrms, 0.87× expected (worst 1.18×)

## B · Noise spectrum (PSD) — WARN

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **WARN** Other spectral lines on 9 channel spectra; check them against Experiments D (alias?) and F (aggressor?).

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.488 µVrms, e_ADC ≈ 2.48 µVrms; suggested gain G8
- **INFO** 2000 SPS: e_PGA ≈ 0.725 µVrms, e_ADC ≈ 5.02 µVrms; suggested gain G12
- **INFO** 4000 SPS: e_PGA ≈ 1.67 µVrms, e_ADC ≈ 6.95 µVrms; suggested gain G12

## D · Data-rate sweep — WARN

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **WARN** RMS grows with rate^0.35 (white noise = 0.50).
- **WARN** Some lines appear at one data rate only: likely aliases of interference above Nyquist (the sinc³ filter rejects only partially between its nulls).

## E · Multichannel correlation — FAIL

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **FAIL** 500 SPS: max |r| = 0.37, channel-average ratio 0.909 (1 = independent, 2.83 = fully shared)
- **FAIL** 2000 SPS: max |r| = 0.31, channel-average ratio 0.93 (1 = independent, 2.83 = fully shared)
- **FAIL** 4000 SPS: max |r| = 0.27, channel-average ratio 0.933 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 500 SPS, WiFi access point (beacons): noise +35.5 %, pp/rms 11, new lines 39 Hz, 49 Hz, 58 Hz, 68 Hz, 78 Hz
- **WARN** 2000 SPS, WiFi access point (beacons): noise +48.9 %, pp/rms 13, new lines 49 Hz, 58 Hz, 68 Hz, 78 Hz, 88 Hz
- **WARN** 2000 SPS, WiFi scanning (continuous TX): noise +5.6 %, pp/rms 15, new lines 849 Hz
- **WARN** 4000 SPS, WiFi access point (beacons): noise +23.3 %, pp/rms 12, new lines 58 Hz, 68 Hz, 78 Hz, 88 Hz, 98 Hz
- **WARN** 4000 SPS, WiFi scanning (continuous TX): noise +4.6 %, pp/rms 14, new lines 1417 Hz

## G · Internal test signal — FAIL

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **FAIL** median amplitude 1.8792 mV vs 2.000 mV expected (-6.0 %)
- **WARN** Gain cross-check: amplitude spread across gains 1.058× (1.00 ideal); log-log slope vs gain +0.02
- **WARN** Noise on DC test levels exceeds shorted noise in 6 cases: reference noise.

## H · Supply measurement (MVDD) — FAIL

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **FAIL** WiFi off: (AVDD+AVSS)/2 = 1.260 V, DVDD/4 = 0.711 V, ripple ≈ 40.6 µVrms
- **FAIL** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.260 V, DVDD/4 = 0.711 V, ripple ≈ 84.1 µVrms

## I · Temperature & long-term drift — WARN

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **WARN** temperature -9.24 → -9.16 °C over 119 s (range -9.24–-9.15 °C)
- **INFO** longest useful averaging time ≈ 5.8 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | -224.5 | 8.298 | 31.38 | 3.781 | FAIL |
| A | shorted, each | 6 | HR 500 | 2 | -105 | 6.965 | 27.04 | 3.882 | FAIL |
| A | shorted, each | 6 | HR 500 | 3 | -145 | 0.6297 | 4.768 | 7.572 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 11.97 | 0.4986 | 3.338 | 6.695 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | 68.74 | 0.5273 | 3.958 | 7.506 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | 77.11 | 0.5282 | 4.53 | 8.577 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | -100.8 | 0.5458 | 3.815 | 6.99 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -343.4 | 0.5495 | 4.053 | 7.376 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | -103.6 | 0.7591 | 6.342 | 8.355 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | -118.4 | 0.5453 | 4.148 | 7.608 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -263.6 | 1.246 | 8.154 | 6.543 | WARN |
| A | shorted, all | 6 | HR 500 | 4 | 23.42 | 0.7147 | 4.864 | 6.805 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -14.25 | 0.7185 | 5.245 | 7.301 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | 168.8 | 0.7403 | 5.293 | 7.15 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | -112.5 | 0.618 | 4.53 | 7.33 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -364.2 | 1.092 | 6.199 | 5.678 | WARN |
| A | shorted, each | 6 | HR 2000 | 1 | -194.2 | 1.058 | 10.3 | 9.732 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | -117.3 | 0.9208 | 7.057 | 7.664 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -145 | 0.9272 | 7.248 | 7.817 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 11.7 | 0.9525 | 7.868 | 8.26 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | 69.36 | 0.9394 | 7.057 | 7.513 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | 76.75 | 0.9582 | 8.297 | 8.659 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | -101.2 | 0.9842 | 8.249 | 8.381 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -344.6 | 0.9701 | 7.725 | 7.963 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | -101.1 | 1.161 | 9.632 | 8.299 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | -114.4 | 1.018 | 8.249 | 8.101 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -262.9 | 1.403 | 10.44 | 7.441 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 21.19 | 1.089 | 8.869 | 8.148 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -17.3 | 1.117 | 8.154 | 7.297 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | 173.4 | 1.116 | 8.726 | 7.82 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | -111.6 | 1.055 | 9.155 | 8.679 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -368 | 1 | 7.534 | 7.534 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | -195 | 1.489 | 15.83 | 10.63 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | -117.5 | 1.331 | 12.16 | 9.138 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -144.9 | 1.353 | 11.3 | 8.351 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 12.07 | 1.342 | 10.68 | 7.959 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | 70.14 | 1.354 | 12.54 | 9.263 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | 76 | 1.357 | 12.54 | 9.24 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | -101.4 | 1.349 | 12.3 | 9.123 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -345.1 | 1.331 | 10.92 | 8.206 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | -102.8 | 1.667 | 14.59 | 8.753 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | -115.6 | 1.415 | 11.97 | 8.459 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -262.3 | 1.898 | 15.21 | 8.014 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 21.22 | 1.491 | 12.64 | 8.475 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -16.21 | 1.535 | 15.07 | 9.818 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | 171.7 | 1.559 | 12.97 | 8.319 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | -111.7 | 1.433 | 12.02 | 8.384 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -367.5 | 1.383 | 11.83 | 8.549 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 2.875 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 1.494 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 1.24 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.8813 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.6633 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.5579 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.4949 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 2.376 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 1.255 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.946 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.7229 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.5621 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.4779 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.4118 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 2.695 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 1.98 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 1.393 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 1.107 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.8454 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.5744 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.4273 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 2.277 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 1.523 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 1.151 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.8988 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.651 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.5067 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.4162 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 2.954 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 1.625 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 1.203 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.9261 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.6519 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.562 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.4535 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 3.003 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 1.559 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 1.091 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.8414 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.6277 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.5191 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.4335 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 2.375 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 1.272 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.9269 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.7382 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.5561 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.4941 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.4361 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 2.231 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 1.18 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.9114 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.7076 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.5445 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.4929 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.4113 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 5.976 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 2.905 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 2.169 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.67 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.18 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 0.9851 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 0.7752 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 4.643 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 2.44 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.752 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.373 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 0.9981 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 0.8603 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 0.7162 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 5.86 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 3.944 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 2.693 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 2.095 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.388 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 1.11 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 0.7767 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 4.701 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 2.808 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 1.984 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.552 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.098 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 0.8882 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 0.7337 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 5.453 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 2.92 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 2.067 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.609 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.106 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 0.9666 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 0.7313 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 6.045 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 2.897 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.916 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.51 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.089 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 0.9029 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 0.7235 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 4.632 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 2.391 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.75 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.373 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.021 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 0.8888 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 0.7036 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 4.381 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 2.338 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.677 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.308 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 0.9838 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 0.8318 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 0.7256 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 7.973 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 4.021 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.938 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 2.879 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 2.762 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.482 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.091 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 6.581 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 3.483 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.474 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 2.409 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 3.111 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.336 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 0.9821 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 8.207 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 5.262 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 3.69 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 2.932 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.987 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.508 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.109 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 6.686 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 3.832 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.635 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 2.446 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 2.054 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.254 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.017 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 7.521 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 4.008 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.786 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 2.753 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 2.661 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.37 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.022 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 8.226 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 3.993 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.684 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 3.517 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 4.923 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.766 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.035 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 6.582 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 3.438 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.502 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 1.998 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.492 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.206 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 0.987 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 6.479 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 3.438 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.422 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 2.493 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 4.141 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.655 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 0.9882 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | -100.3 | 0.7307 | 5.77 | 7.897 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | -111.7 | 0.5526 | 4.578 | 8.284 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -263.5 | 0.925 | 6.723 | 7.268 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 19.39 | 0.6932 | 5.15 | 7.429 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -17.93 | 0.6781 | 5.007 | 7.383 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | 175.9 | 0.6909 | 5.007 | 7.247 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | -111.8 | 0.5957 | 4.148 | 6.964 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -373.1 | 0.7651 | 4.816 | 6.295 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | -100.7 | 0.7295 | 5.627 | 7.713 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | -112 | 0.5679 | 4.196 | 7.388 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -264.4 | 0.8448 | 6.151 | 7.282 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 19.98 | 0.6231 | 4.292 | 6.887 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -17.42 | 0.6994 | 4.911 | 7.023 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | 175.3 | 0.6841 | 4.387 | 6.413 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | -112.1 | 0.6104 | 4.816 | 7.89 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -373.5 | 0.5558 | 4.196 | 7.55 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | -101.3 | 0.7759 | 5.627 | 7.252 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | -112.8 | 0.5959 | 4.911 | 8.242 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -264.4 | 0.8485 | 5.96 | 7.025 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 20.61 | 0.624 | 4.673 | 7.489 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -17.02 | 0.6872 | 4.721 | 6.87 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | 174.5 | 0.734 | 5.627 | 7.666 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | -112 | 0.5519 | 3.862 | 6.999 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -372.6 | 0.5751 | 4.101 | 7.131 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | -101.7 | 0.7018 | 4.816 | 6.862 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | -112.9 | 0.5635 | 3.719 | 6.6 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -264.6 | 0.8528 | 5.96 | 6.99 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 20.6 | 0.6324 | 4.768 | 7.54 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -16.82 | 0.6948 | 4.482 | 6.451 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | 174.2 | 0.7125 | 4.959 | 6.961 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | -112 | 0.5969 | 4.387 | 7.35 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -372.4 | 0.5413 | 4.244 | 7.84 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | -101.5 | 1.317 | 14.11 | 10.72 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | -112.4 | 0.6303 | 4.911 | 7.792 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -264.4 | 1.289 | 13.07 | 10.13 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 20.16 | 0.6181 | 4.196 | 6.789 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -17.03 | 1.271 | 12.73 | 10.02 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | 174.7 | 1.333 | 13.45 | 10.09 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | -111.9 | 0.593 | 4.196 | 7.076 | WARN |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -373 | 0.5815 | 4.148 | 7.134 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | -101.6 | 0.8377 | 6.771 | 8.083 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | -112.5 | 0.5658 | 4.292 | 7.585 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -264.3 | 0.9204 | 6.866 | 7.46 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 19.83 | 0.6505 | 5.007 | 7.697 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -16.73 | 0.7462 | 6.342 | 8.499 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | 174.9 | 0.7544 | 6.914 | 9.165 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | -111.9 | 0.5682 | 4.292 | 7.553 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -372.8 | 0.5854 | 4.53 | 7.738 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | -101.5 | 0.673 | 4.101 | 6.093 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | -112.7 | 0.5343 | 3.338 | 6.247 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -264 | 0.8739 | 5.245 | 6.002 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 20.61 | 0.594 | 3.481 | 5.86 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -16.51 | 0.6672 | 3.815 | 5.717 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | 173.9 | 0.6409 | 4.196 | 6.547 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | -111.6 | 0.5648 | 3.576 | 6.332 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -372.1 | 0.4856 | 2.909 | 5.99 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | -101.8 | 1.193 | 9.155 | 7.674 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | -112.8 | 1.014 | 8.345 | 8.233 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -264.1 | 1.421 | 10.97 | 7.716 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 20.21 | 1.1 | 8.678 | 7.889 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -16.6 | 1.137 | 8.917 | 7.841 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | 173.8 | 1.133 | 9.441 | 8.335 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | -111.9 | 1.017 | 7.629 | 7.503 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -372 | 0.9996 | 8.631 | 8.634 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | -101.8 | 1.206 | 9.775 | 8.103 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | -112.3 | 1.016 | 7.391 | 7.272 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -264.1 | 1.422 | 11.16 | 7.845 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 20.18 | 1.091 | 9.108 | 8.348 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -16.63 | 1.151 | 9.823 | 8.534 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | 173.8 | 1.113 | 9.06 | 8.138 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | -112.3 | 1.034 | 8.345 | 8.068 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -371.9 | 0.9951 | 7.915 | 7.955 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | -101.7 | 1.313 | 9.775 | 7.447 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | -112.3 | 1.007 | 8.202 | 8.147 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -264.2 | 1.471 | 11.78 | 8.007 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 20.24 | 1.102 | 9.108 | 8.264 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -16.85 | 1.176 | 8.869 | 7.543 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | 174.1 | 1.185 | 8.726 | 7.365 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | -112.6 | 1.018 | 8.249 | 8.102 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -372.4 | 0.9924 | 7.391 | 7.448 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | -103.1 | 2.086 | 26.42 | 12.67 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | -114 | 1.253 | 11.49 | 9.17 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -263.7 | 2.057 | 24.65 | 11.98 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 20.68 | 1.123 | 8.774 | 7.816 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -15.45 | 2.069 | 24.7 | 11.94 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | 171.4 | 2.386 | 28.61 | 11.99 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | -112.9 | 1.016 | 8.202 | 8.072 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -370.1 | 1.428 | 12.35 | 8.646 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | -103 | 1.318 | 17.4 | 13.21 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | -114.1 | 1.032 | 10.44 | 10.11 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -263.4 | 1.533 | 18.41 | 12 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 21.06 | 1.082 | 8.535 | 7.886 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -15.35 | 1.261 | 17.21 | 13.65 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | 171 | 1.279 | 18.79 | 14.69 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | -113.1 | 1.019 | 7.963 | 7.814 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -369.7 | 0.9902 | 7.963 | 8.042 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | -103.6 | 1.143 | 7.725 | 6.759 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | -114.3 | 0.9718 | 6.008 | 6.182 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -263.6 | 1.419 | 8.583 | 6.048 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 21.49 | 1.092 | 7.2 | 6.593 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -15.45 | 1.108 | 7.629 | 6.883 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | 170.4 | 1.091 | 7.105 | 6.513 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | -113.2 | 0.9925 | 6.342 | 6.39 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -369.6 | 0.9918 | 7.391 | 7.452 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | -103.4 | 1.621 | 13.4 | 8.267 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | -114.4 | 1.424 | 12.25 | 8.605 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -263.1 | 1.904 | 16.12 | 8.466 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 20.95 | 1.497 | 12.21 | 8.156 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -15.47 | 1.539 | 13.16 | 8.552 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | 171 | 1.535 | 12.16 | 7.921 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | -113 | 1.476 | 12.4 | 8.402 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -370.1 | 1.411 | 11.68 | 8.279 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | -103.5 | 1.642 | 13.88 | 8.45 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | -114.2 | 1.44 | 11.59 | 8.045 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -263.2 | 1.903 | 15.69 | 8.245 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 20.8 | 1.53 | 12.78 | 8.35 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -15.7 | 1.567 | 12.68 | 8.092 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | 171.2 | 1.558 | 15.74 | 10.1 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | -112.9 | 1.446 | 12.16 | 8.41 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -370.3 | 1.413 | 12.3 | 8.707 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | -103.3 | 1.704 | 13.45 | 7.892 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | -114.1 | 1.44 | 12.35 | 8.576 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -263.3 | 1.943 | 16.16 | 8.318 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 20.7 | 1.516 | 12.4 | 8.179 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -15.55 | 1.597 | 12.78 | 8 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | 171.7 | 1.619 | 13.3 | 8.218 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | -113.1 | 1.441 | 11.73 | 8.141 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -370.7 | 1.403 | 11.78 | 8.395 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | -102.5 | 2.366 | 26.89 | 11.37 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | -113.6 | 1.495 | 13.88 | 9.282 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -263.4 | 2.462 | 28.94 | 11.76 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 20.63 | 1.497 | 12.35 | 8.249 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -15.79 | 2.265 | 26.27 | 11.6 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | 172.4 | 2.342 | 27.89 | 11.91 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | -112.7 | 1.442 | 11.97 | 8.3 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -371.6 | 1.433 | 12.4 | 8.654 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | -102.7 | 1.776 | 25.13 | 14.15 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | -113.6 | 1.436 | 13.3 | 9.262 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -263.8 | 2.021 | 24.56 | 12.15 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 20.36 | 1.502 | 12.4 | 8.252 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -15.87 | 1.698 | 22.41 | 13.2 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | 172 | 1.714 | 23.79 | 13.88 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | -112.6 | 1.441 | 12.4 | 8.606 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -371.1 | 1.388 | 12.25 | 8.829 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | -102.8 | 1.621 | 12.16 | 7.502 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | -114 | 1.412 | 12.49 | 8.848 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -263.7 | 1.89 | 14.59 | 7.72 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 20.66 | 1.461 | 10.54 | 7.212 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -15.03 | 1.533 | 10.11 | 6.594 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | 170.9 | 1.56 | 12.11 | 7.766 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | -112.2 | 1.419 | 10.78 | 7.593 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -370.2 | 1.392 | 10.11 | 7.264 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | -1614 | 2.322 |  |  | amplitude 1.5420 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | -1594 | 0.6166 |  |  | amplitude 1.5282 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -1625 | 0.5771 |  |  | amplitude 1.5282 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | -1476 | 0.5543 |  |  | amplitude 1.5287 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -1403 | 0.6341 |  |  | amplitude 1.5298 mV (-23.5 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -1413 | 0.6346 |  |  | amplitude 1.5258 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | -1586 | 0.6713 |  |  | amplitude 1.5275 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -1836 | 0.5764 |  |  | amplitude 1.5262 mV (-23.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | -3312 | 2.351 |  |  | amplitude 2.2261 mV (+11.3 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | -3323 | 2.272 |  |  | amplitude 2.2465 mV (+12.3 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -3404 | 2.255 |  |  | amplitude 2.2522 mV (+12.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | -3294 | 2.412 |  |  | amplitude 2.2517 mV (+12.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -3224 | 2.139 |  |  | amplitude 2.2423 mV (+12.1 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -3067 | 2.185 |  |  | amplitude 2.2480 mV (+12.4 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | -3336 | 2.32 |  |  | amplitude 2.2612 mV (+13.1 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -3622 | 2.142 |  |  | amplitude 2.2465 mV (+12.3 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | -1623 | 3.514 |  |  | amplitude 1.5394 mV (-23.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | -1599 | 1.451 |  |  | amplitude 1.5272 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -1629 | 1.026 |  |  | amplitude 1.5272 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | -1479 | 1.092 |  |  | amplitude 1.5276 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -1406 | 1.084 |  |  | amplitude 1.5287 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -1418 | 1.083 |  |  | amplitude 1.5249 mV (-23.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | -1591 | 1.042 |  |  | amplitude 1.5264 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -1840 | 1.028 |  |  | amplitude 1.5253 mV (-23.7 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | -3308 | 2.87 |  |  | amplitude 2.2213 mV (+11.1 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | -3321 | 2.604 |  |  | amplitude 2.2417 mV (+12.1 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -3401 | 2.697 |  |  | amplitude 2.2474 mV (+12.4 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | -3291 | 2.782 |  |  | amplitude 2.2468 mV (+12.3 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -3221 | 2.516 |  |  | amplitude 2.2375 mV (+11.9 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -3065 | 2.488 |  |  | amplitude 2.2432 mV (+12.2 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | -3333 | 2.565 |  |  | amplitude 2.2563 mV (+12.8 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -3620 | 2.52 |  |  | amplitude 2.2418 mV (+12.1 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | -1632 | 3.699 |  |  | amplitude 1.5371 mV (-23.1 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | -1603 | 2.206 |  |  | amplitude 1.5260 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -1633 | 1.551 |  |  | amplitude 1.5261 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | -1484 | 1.578 |  |  | amplitude 1.5264 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -1410 | 1.654 |  |  | amplitude 1.5277 mV (-23.6 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -1422 | 1.544 |  |  | amplitude 1.5241 mV (-23.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | -1595 | 1.531 |  |  | amplitude 1.5254 mV (-23.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -1845 | 1.488 |  |  | amplitude 1.5242 mV (-23.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | -3307 | 3.227 |  |  | amplitude 2.2164 mV (+10.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | -3319 | 2.96 |  |  | amplitude 2.2367 mV (+11.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -3399 | 3.12 |  |  | amplitude 2.2422 mV (+12.1 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | -3289 | 3.18 |  |  | amplitude 2.2418 mV (+12.1 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -3219 | 2.872 |  |  | amplitude 2.2326 mV (+11.6 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -3063 | 2.852 |  |  | amplitude 2.2383 mV (+11.9 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | -3330 | 2.989 |  |  | amplitude 2.2513 mV (+12.6 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -3618 | 2.887 |  |  | amplitude 2.2368 mV (+11.8 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.414e+06 | 53.6 |  |  | (AVDD+AVSS)/2 -14.31 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.405e+06 | 81.07 |  |  | (AVDD+AVSS)/2 -14.85 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 7.089e+05 | 18.99 |  |  | DVDD/4 -14.07 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 7.13e+05 | 16.55 |  |  | DVDD/4 -13.58 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.41e+06 | 55.86 |  |  | (AVDD+AVSS)/2 -14.55 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.411e+06 | 53.43 |  |  | (AVDD+AVSS)/2 -14.51 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 9.609e+05 | 27.48 |  |  | (AVDD+AVSS)/2 -41.76 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 9.604e+05 | 27.82 |  |  | (AVDD+AVSS)/2 -41.79 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.414e+06 | 92.78 |  |  | (AVDD+AVSS)/2 -14.31 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.405e+06 | 111.5 |  |  | (AVDD+AVSS)/2 -14.84 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 7.09e+05 | 46.09 |  |  | DVDD/4 -14.06 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 7.13e+05 | 45.74 |  |  | DVDD/4 -13.57 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.41e+06 | 97.05 |  |  | (AVDD+AVSS)/2 -14.55 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.411e+06 | 92.45 |  |  | (AVDD+AVSS)/2 -14.50 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 9.606e+05 | 74.79 |  |  | (AVDD+AVSS)/2 -41.78 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 9.601e+05 | 75.75 |  |  | (AVDD+AVSS)/2 -41.81 % |
