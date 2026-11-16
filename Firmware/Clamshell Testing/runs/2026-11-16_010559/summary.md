# ADS1298 clamshell validation — summary

Run: 2026-11-16_010559 · hardware on /dev/cu.usbserial-1140 · 114 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 112/114 captures trustworthy |
| A | Shorted-input noise floor | ✕ FAIL | 500 SPS: median 0.613 µVrms; 2000 SPS: median 1.07 µVrms; 4000 SPS: median 1.49 µVrms |
| B | Noise spectrum (PSD) | ! WARN | floor ≈ 39 nV/√Hz, 9 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.789 µVrms, e_ADC ≈ 2.22 µVrms; suggested gain G8 |
| D | Data-rate sweep | ! WARN | RMS grows with rate^0.39 (white noise = 0.50). |
| E | Multichannel correlation | ✕ FAIL | 500 SPS: max |r| = 0.44, channel-average ratio 0.985 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ✕ FAIL | 6 of 19 variants affect the noise |
| G | Internal test signal | ✕ FAIL | median amplitude 1.9138 mV vs 2.000 mV expected (-4.3 %) |
| H | Supply measurement (MVDD) | ✕ FAIL | WiFi off: (AVDD+AVSS)/2 = 1.254 V, DVDD/4 = 0.710 V, ripple ≈ 34.6 µVrms |
| I | Temperature & long-term drift | ! WARN | temperature -23.89 → -23.86 °C over 119 s (range -23.89–-23.86 °C) |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 2 of 114 captures in this run failed integrity checks.

## A · Shorted-input noise floor — FAIL

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **FAIL** 500 SPS: median 0.613 µVrms, 1.08× expected (worst 11.45×); noisiest CH1 at 6.49 µVrms
- **PASS** 2000 SPS: median 1.07 µVrms, 0.94× expected (worst 1.27×)
- **PASS** 4000 SPS: median 1.49 µVrms, 0.93× expected (worst 1.17×)

## B · Noise spectrum (PSD) — WARN

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **WARN** Other spectral lines on 9 channel spectra; check them against Experiments D (alias?) and F (aggressor?).

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.789 µVrms, e_ADC ≈ 2.22 µVrms; suggested gain G8
- **INFO** 2000 SPS: e_PGA ≈ 0.987 µVrms, e_ADC ≈ 4.92 µVrms; suggested gain G12
- **INFO** 4000 SPS: e_PGA ≈ 1.22 µVrms, e_ADC ≈ 7.07 µVrms; suggested gain G12

## D · Data-rate sweep — WARN

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **PASS** RMS grows with rate^0.39 (white noise = 0.50).
- **WARN** Some lines appear at one data rate only: likely aliases of interference above Nyquist (the sinc³ filter rejects only partially between its nulls).

## E · Multichannel correlation — FAIL

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **FAIL** 500 SPS: max |r| = 0.44, channel-average ratio 0.985 (1 = independent, 2.83 = fully shared)
- **FAIL** 2000 SPS: max |r| = 0.4, channel-average ratio 0.995 (1 = independent, 2.83 = fully shared)
- **FAIL** 4000 SPS: max |r| = 0.32, channel-average ratio 1 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — FAIL

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **FAIL** 500 SPS, WiFi access point (beacons): noise +51.3 %, pp/rms 11
- **WARN** 500 SPS, WiFi scanning (continuous TX): noise +8.0 %, pp/rms 9.7
- **WARN** 2000 SPS, WiFi access point (beacons): noise +38.5 %, pp/rms 13, new lines 575 Hz
- **WARN** 2000 SPS, WiFi scanning (continuous TX): noise +7.5 %, pp/rms 14, new lines 89 Hz
- **WARN** 4000 SPS, WiFi access point (beacons): noise +26.3 %, pp/rms 13
- **FAIL** 4000 SPS, WiFi scanning (continuous TX): noise +15867.6 %, pp/rms 2e+02, new lines 574 Hz

## G · Internal test signal — FAIL

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **FAIL** median amplitude 1.9138 mV vs 2.000 mV expected (-4.3 %)
- **WARN** Gain cross-check: amplitude spread across gains 1.056× (1.00 ideal); log-log slope vs gain +0.02
- **FAIL** Noise on DC test levels exceeds shorted noise in 6 cases: reference noise.

## H · Supply measurement (MVDD) — FAIL

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **FAIL** WiFi off: (AVDD+AVSS)/2 = 1.254 V, DVDD/4 = 0.710 V, ripple ≈ 34.6 µVrms
- **FAIL** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.254 V, DVDD/4 = 0.710 V, ripple ≈ 80.8 µVrms

## I · Temperature & long-term drift — WARN

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **WARN** temperature -23.89 → -23.86 °C over 119 s (range -23.89–-23.86 °C)
- **INFO** longest useful averaging time ≈ 10.7 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | -222.1 | 6.486 | 24.32 | 3.749 | FAIL |
| A | shorted, each | 6 | HR 500 | 2 | -58.13 | 0.504 | 3.481 | 6.907 | PASS |
| A | shorted, each | 6 | HR 500 | 3 | 24.48 | 0.4968 | 3.862 | 7.775 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | -40.64 | 0.5189 | 3.624 | 6.985 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | -48.55 | 0.4995 | 3.195 | 6.396 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | -61.39 | 0.5312 | 4.196 | 7.899 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | -237.3 | 0.5056 | 3.815 | 7.545 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -48.35 | 0.4915 | 3.624 | 7.374 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | -80.1 | 0.7395 | 5.865 | 7.932 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | -29.5 | 0.6057 | 4.244 | 7.006 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -69.85 | 0.6755 | 4.959 | 7.341 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | -185.7 | 0.8296 | 5.913 | 7.127 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -12.63 | 0.6449 | 4.768 | 7.394 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | -150.3 | 0.6922 | 5.15 | 7.44 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | -327 | 0.6711 | 4.959 | 7.39 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -69 | 0.621 | 4.673 | 7.525 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | -214.5 | 1.085 | 10.16 | 9.365 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | -58.24 | 0.9197 | 8.011 | 8.71 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | 24.13 | 0.9248 | 7.343 | 7.94 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | -40.32 | 0.9396 | 7.391 | 7.866 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | -48.24 | 0.9742 | 8.249 | 8.467 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | -61.59 | 0.9779 | 9.394 | 9.606 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | -237.4 | 0.9277 | 8.011 | 8.635 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -48.03 | 0.9432 | 8.011 | 8.494 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | -80.26 | 1.268 | 11.49 | 9.062 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | -29.27 | 1.078 | 9.155 | 8.492 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -70.05 | 1.173 | 10.44 | 8.904 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | -185.2 | 1.444 | 11.44 | 7.927 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -12.52 | 1.058 | 8.44 | 7.976 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | -149.7 | 1.16 | 9.632 | 8.303 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | -326.5 | 1.102 | 8.345 | 7.573 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -68.32 | 1.088 | 9.203 | 8.458 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | -214.5 | 1.563 | 12.97 | 8.297 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | -58.52 | 1.354 | 11.49 | 8.487 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | 24 | 1.373 | 13.54 | 9.864 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | -40.39 | 1.334 | 11.73 | 8.795 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | -47.55 | 1.473 | 11.78 | 7.998 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | -61.22 | 1.378 | 11.68 | 8.477 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | -237.5 | 1.385 | 11.25 | 8.125 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -48.39 | 1.397 | 11.44 | 8.19 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | -80.33 | 1.672 | 14.54 | 8.699 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | -29.63 | 1.507 | 11.83 | 7.85 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -69.37 | 1.575 | 12.64 | 8.023 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | -184.6 | 1.876 | 14.83 | 7.904 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -12.77 | 1.455 | 11.87 | 8.158 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | -149.4 | 1.569 | 12.59 | 8.023 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | -326.7 | 1.52 | 13.4 | 8.815 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -68.65 | 1.53 | 12.16 | 7.946 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 2.953 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 1.86 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 1.461 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 1.139 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.7579 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.6019 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.5435 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 2.13 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 1.596 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 1.265 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.9109 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.5803 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.5159 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.4422 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 2.28 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 1.796 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 1.414 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 1.009 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.6305 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.5309 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.4437 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 2.493 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 2.457 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 2.105 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 1.449 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.8421 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.6284 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.5265 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 2.213 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 1.462 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 1.139 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.8659 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.612 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.5217 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.4504 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 2.288 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 1.712 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 1.349 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 1.006 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.649 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.5234 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.4554 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 2.53 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 1.582 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 1.24 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.9192 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.6329 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.5262 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.4482 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 2.289 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 1.391 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 1.109 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.8449 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.607 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.5165 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.4426 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 5.888 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 3.178 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 2.159 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.793 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.236 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 1.041 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 0.8286 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 4.559 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 2.838 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.986 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.545 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 1.082 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 0.9076 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 0.7098 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 5.004 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 3.104 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 2.156 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 1.671 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.162 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 0.9455 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 0.7658 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 5.223 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 4.046 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 2.956 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 2.182 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.446 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 1.111 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 0.8273 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 4.549 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 2.568 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 1.831 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.449 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.054 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 0.8826 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 0.7226 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 4.998 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 2.99 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 2.093 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.622 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.152 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 0.9942 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 0.7936 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 4.967 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 2.724 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.986 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.535 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.096 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 0.9251 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 0.7456 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 4.919 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 2.636 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.87 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.483 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 1.095 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 0.8883 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 0.7429 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 7.896 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 4.16 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.923 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 2.336 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.642 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.374 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.122 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 6.532 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 3.78 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.715 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 2.077 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.492 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.226 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 0.9915 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 7.108 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 4.177 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 2.964 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 2.239 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.572 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.284 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.028 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 7.302 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 5.111 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 3.811 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 2.761 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.855 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.457 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.124 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 6.552 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 3.559 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.585 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 2.013 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.463 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.209 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 0.985 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 7.197 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 4.103 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.844 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 2.189 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.559 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.28 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.031 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 7.415 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 3.941 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.812 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 2.144 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.495 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.254 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 1.008 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 7.034 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 3.749 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.636 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 2.054 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.49 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.229 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 1 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | -79.11 | 0.7254 | 5.054 | 6.967 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | -29.8 | 0.5806 | 4.482 | 7.72 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -70 | 0.6384 | 4.244 | 6.648 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | -184.7 | 0.8357 | 6.39 | 7.646 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -11.43 | 0.6227 | 4.387 | 7.045 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | -150.5 | 0.6583 | 4.768 | 7.243 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | -325.7 | 0.6344 | 4.864 | 7.667 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -70.41 | 0.6058 | 4.148 | 6.848 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | -79.61 | 0.7726 | 5.007 | 6.481 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | -29.92 | 0.5844 | 4.435 | 7.588 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -70.37 | 0.6735 | 5.007 | 7.434 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | -184.6 | 0.8434 | 5.96 | 7.067 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -11.41 | 0.6125 | 4.53 | 7.395 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | -150.7 | 0.7307 | 4.768 | 6.526 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | -325.4 | 0.6339 | 4.625 | 7.296 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -70.15 | 0.6026 | 4.101 | 6.806 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | -79.71 | 0.7337 | 5.388 | 7.344 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | -29.86 | 0.5946 | 4.148 | 6.977 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -69.89 | 0.6478 | 4.721 | 7.287 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | -184.6 | 0.8279 | 5.77 | 6.969 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -11.6 | 0.5968 | 4.196 | 7.032 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | -150.9 | 0.6421 | 4.387 | 6.832 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | -325.6 | 0.6498 | 4.721 | 7.265 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -70.05 | 0.602 | 4.053 | 6.733 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | -79.67 | 0.7335 | 5.054 | 6.891 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | -29.97 | 0.5932 | 4.339 | 7.315 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -70.11 | 0.6771 | 4.959 | 7.325 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | -184.6 | 0.8411 | 6.008 | 7.143 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -11.7 | 0.6074 | 4.435 | 7.301 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | -151 | 0.6734 | 4.53 | 6.727 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | -325.5 | 0.6978 | 5.245 | 7.517 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -70.13 | 0.5762 | 4.482 | 7.779 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | -78.77 | 1.66 | 18.98 | 11.43 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | -30.25 | 0.6482 | 5.341 | 8.239 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -69.94 | 0.8551 | 8.726 | 10.2 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | -184.6 | 1.443 | 15.97 | 11.07 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -11.27 | 0.6267 | 4.435 | 7.077 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | -151.3 | 1.012 | 10.68 | 10.56 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | -326 | 1.165 | 11.92 | 10.23 | FAIL |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -69.94 | 0.6125 | 4.053 | 6.618 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | -79.09 | 0.878 | 8.535 | 9.721 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | -30.34 | 0.5871 | 4.387 | 7.472 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -70.02 | 0.687 | 5.579 | 8.121 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | -184.7 | 0.9235 | 8.011 | 8.674 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -11.34 | 0.6356 | 4.911 | 7.728 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | -150.9 | 0.6877 | 5.722 | 8.321 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | -326.1 | 0.7397 | 6.628 | 8.961 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -69.98 | 0.5879 | 4.101 | 6.976 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | -79.97 | 0.8109 | 4.768 | 5.88 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | -29.54 | 0.5943 | 4.053 | 6.82 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -70.02 | 0.6551 | 4.196 | 6.405 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | -184.8 | 0.7921 | 4.292 | 5.418 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -12.02 | 0.6224 | 3.576 | 5.746 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | -151.1 | 0.63 | 3.91 | 6.207 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | -325.4 | 0.6046 | 4.101 | 6.782 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -70.04 | 0.5324 | 3.29 | 6.18 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | -79.72 | 1.275 | 10.82 | 8.486 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | -30.26 | 1.12 | 8.869 | 7.916 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -70.09 | 1.167 | 9.537 | 8.174 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | -184.6 | 1.433 | 13.21 | 9.22 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -11.76 | 1.052 | 8.965 | 8.525 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | -150.4 | 1.14 | 9.871 | 8.657 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | -325.4 | 1.11 | 8.154 | 7.348 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -70.25 | 1.1 | 8.726 | 7.933 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | -79.61 | 1.248 | 10.11 | 8.098 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | -29.8 | 1.103 | 8.44 | 7.653 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -69.87 | 1.169 | 9.632 | 8.238 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | -184.3 | 1.433 | 11.01 | 7.686 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -11.31 | 1.079 | 9.346 | 8.663 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | -150.6 | 1.17 | 9.489 | 8.112 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | -325 | 1.109 | 8.631 | 7.784 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -69.96 | 1.063 | 8.678 | 8.168 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | -79.52 | 1.356 | 11.68 | 8.612 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | -29.88 | 1.066 | 8.965 | 8.41 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -69.68 | 1.184 | 9.537 | 8.052 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | -184.5 | 1.5 | 12.59 | 8.39 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -11.17 | 1.074 | 8.726 | 8.124 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | -150.4 | 1.208 | 9.441 | 7.817 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | -325.6 | 1.179 | 8.917 | 7.562 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -69.96 | 1.068 | 9.06 | 8.484 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | -78.93 | 2.559 | 32.66 | 12.77 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | -30.07 | 1.145 | 9.584 | 8.37 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -69.54 | 1.442 | 16.69 | 11.58 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | -184.2 | 2.275 | 28.23 | 12.41 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -10.63 | 1.084 | 10.06 | 9.284 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | -151 | 1.631 | 18.64 | 11.43 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | -326.3 | 1.799 | 22.75 | 12.64 | WARN |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -69.86 | 1.081 | 7.963 | 7.366 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | -79.47 | 1.563 | 22.27 | 14.25 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | -29.69 | 1.111 | 9.251 | 8.324 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -69.96 | 1.207 | 11.83 | 9.802 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | -184.2 | 1.614 | 22.75 | 14.09 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -10.75 | 1.049 | 9.584 | 9.138 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | -150.8 | 1.239 | 13.92 | 11.24 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | -326.2 | 1.25 | 17.83 | 14.26 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -70.34 | 1.069 | 8.917 | 8.344 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | -80.27 | 1.264 | 8.965 | 7.09 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | -29.27 | 1.089 | 6.723 | 6.172 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -70 | 1.17 | 8.726 | 7.456 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | -183.9 | 1.411 | 10.01 | 7.095 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -11.09 | 1.021 | 7.582 | 7.429 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | -150.2 | 1.121 | 7.582 | 6.762 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | -325.5 | 1.112 | 7.486 | 6.731 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -70.69 | 1.051 | 7.343 | 6.99 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | -79.78 | 1.664 | 14.88 | 8.939 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | -29.71 | 1.486 | 11.68 | 7.859 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -69.68 | 1.582 | 13.21 | 8.349 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | -183.8 | 1.861 | 15.02 | 8.072 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -11 | 1.451 | 12.87 | 8.875 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | -150 | 1.573 | 12.59 | 8.002 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | -325.8 | 1.514 | 11.83 | 7.813 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -70.29 | 1.498 | 12.4 | 8.274 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | -79.73 | 1.699 | 15.07 | 8.871 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | -29.85 | 1.527 | 13.02 | 8.526 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -69.32 | 1.631 | 14.02 | 8.597 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | -184.1 | 1.885 | 15.69 | 8.322 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -11.32 | 1.481 | 12.16 | 8.208 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | -149.8 | 1.609 | 15.07 | 9.364 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | -325.9 | 1.551 | 12.4 | 7.995 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -69.75 | 1.542 | 13.11 | 8.503 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | -79.49 | 1.813 | 14.45 | 7.969 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | -30.14 | 1.467 | 12.21 | 8.322 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -69.07 | 1.616 | 12.87 | 7.965 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | -184.5 | 1.955 | 15.31 | 7.829 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -11.27 | 1.449 | 11.68 | 8.061 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | -149.7 | 1.623 | 13.64 | 8.403 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | -326.2 | 1.599 | 13.54 | 8.471 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -69.83 | 1.502 | 12.68 | 8.444 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | -79.04 | 2.862 | 35.67 | 12.46 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | -30.11 | 1.516 | 12.92 | 8.522 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -69.27 | 1.818 | 19.41 | 10.67 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | -184.1 | 2.624 | 34.57 | 13.18 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -11.16 | 1.498 | 12.54 | 8.374 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | -149.9 | 1.997 | 22.22 | 11.13 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | -326.9 | 2.135 | 26.8 | 12.55 | WARN |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -69.89 | 1.504 | 12.11 | 8.055 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | -79.19 | 1.987 | 27.56 | 13.87 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | -30.21 | 1.487 | 12.49 | 8.401 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -69.7 | 1.639 | 16.74 | 10.21 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | -183.9 | 2.061 | 27.18 | 13.19 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -11.29 | 1.467 | 12.06 | 8.226 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | -149.9 | 1.681 | 19.22 | 11.43 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | -326.5 | 6.403 | 1245 | 194.5 | FAIL |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -79.51 | 2000 | 4.062e+05 | 203.1 | FAIL |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | -79.81 | 1.688 | 13.11 | 7.771 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | -29.97 | 1.472 | 11.92 | 8.098 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -69.61 | 1.55 | 10.49 | 6.768 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | -184.4 | 1.843 | 12.21 | 6.624 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -11.35 | 1.452 | 10.49 | 7.223 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | -149.3 | 1.596 | 10.68 | 6.693 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | -325.8 | 1.506 | 10.63 | 7.062 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -70.12 | 1.507 | 10.73 | 7.121 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | -1628 | 2.42 |  |  | amplitude 1.5558 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | -1527 | 0.7788 |  |  | amplitude 1.5447 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -1438 | 0.7055 |  |  | amplitude 1.5450 mV (-22.7 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | -1502 | 0.656 |  |  | amplitude 1.5444 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -1513 | 0.6595 |  |  | amplitude 1.5433 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -1525 | 0.6511 |  |  | amplitude 1.5443 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | -1699 | 0.6476 |  |  | amplitude 1.5428 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -1511 | 0.65 |  |  | amplitude 1.5438 mV (-22.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | -3285 | 3.047 |  |  | amplitude 2.2763 mV (+13.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | -3307 | 2.635 |  |  | amplitude 2.2933 mV (+14.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -3240 | 2.735 |  |  | amplitude 2.3015 mV (+15.1 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | -3288 | 2.916 |  |  | amplitude 2.3045 mV (+15.2 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -3256 | 2.844 |  |  | amplitude 2.2910 mV (+14.5 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -3325 | 2.89 |  |  | amplitude 2.2951 mV (+14.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | -3518 | 2.839 |  |  | amplitude 2.2939 mV (+14.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -3274 | 3.181 |  |  | amplitude 2.2977 mV (+14.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | -1629 | 2.776 |  |  | amplitude 1.5558 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | -1526 | 1.797 |  |  | amplitude 1.5448 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -1438 | 1.151 |  |  | amplitude 1.5452 mV (-22.7 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | -1502 | 1.095 |  |  | amplitude 1.5445 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -1513 | 1.159 |  |  | amplitude 1.5436 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -1525 | 1.127 |  |  | amplitude 1.5444 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | -1699 | 1.096 |  |  | amplitude 1.5429 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -1511 | 1.118 |  |  | amplitude 1.5439 mV (-22.8 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | -3284 | 3.516 |  |  | amplitude 2.2738 mV (+13.7 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | -3306 | 3.113 |  |  | amplitude 2.2909 mV (+14.5 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -3239 | 3.202 |  |  | amplitude 2.2989 mV (+14.9 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | -3287 | 3.329 |  |  | amplitude 2.3019 mV (+15.1 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -3254 | 3.091 |  |  | amplitude 2.2886 mV (+14.4 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -3323 | 3.213 |  |  | amplitude 2.2927 mV (+14.6 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | -3517 | 3.151 |  |  | amplitude 2.2914 mV (+14.6 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -3272 | 3.442 |  |  | amplitude 2.2952 mV (+14.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | -1630 | 3.319 |  |  | amplitude 1.5556 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | -1527 | 2.403 |  |  | amplitude 1.5447 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -1439 | 1.675 |  |  | amplitude 1.5452 mV (-22.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | -1503 | 1.602 |  |  | amplitude 1.5446 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -1514 | 1.771 |  |  | amplitude 1.5435 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -1525 | 1.654 |  |  | amplitude 1.5444 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | -1699 | 1.559 |  |  | amplitude 1.5429 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -1512 | 1.674 |  |  | amplitude 1.5439 mV (-22.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | -3283 | 3.899 |  |  | amplitude 2.2717 mV (+13.6 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | -3305 | 3.417 |  |  | amplitude 2.2890 mV (+14.4 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -3238 | 3.561 |  |  | amplitude 2.2968 mV (+14.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | -3286 | 3.587 |  |  | amplitude 2.2998 mV (+15.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -3254 | 3.525 |  |  | amplitude 2.2867 mV (+14.3 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -3322 | 3.639 |  |  | amplitude 2.2908 mV (+14.5 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | -3517 | 3.625 |  |  | amplitude 2.2893 mV (+14.5 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -3271 | 3.789 |  |  | amplitude 2.2931 mV (+14.7 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.392e+06 | 42.85 |  |  | (AVDD+AVSS)/2 -15.63 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.402e+06 | 65.51 |  |  | (AVDD+AVSS)/2 -15.04 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 7.082e+05 | 26.42 |  |  | DVDD/4 -14.16 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 7.122e+05 | 8.74 |  |  | DVDD/4 -13.67 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.402e+06 | 46.73 |  |  | (AVDD+AVSS)/2 -15.03 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.402e+06 | 46.85 |  |  | (AVDD+AVSS)/2 -15.02 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 9.631e+05 | 14.31 |  |  | (AVDD+AVSS)/2 -41.63 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 9.643e+05 | 14.19 |  |  | (AVDD+AVSS)/2 -41.56 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.392e+06 | 83.57 |  |  | (AVDD+AVSS)/2 -15.62 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.402e+06 | 102.1 |  |  | (AVDD+AVSS)/2 -15.03 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 7.082e+05 | 52.33 |  |  | DVDD/4 -14.16 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 7.123e+05 | 46.17 |  |  | DVDD/4 -13.67 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.402e+06 | 91.63 |  |  | (AVDD+AVSS)/2 -15.02 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.402e+06 | 91.9 |  |  | (AVDD+AVSS)/2 -15.01 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 9.628e+05 | 77.96 |  |  | (AVDD+AVSS)/2 -41.65 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 9.64e+05 | 75.67 |  |  | (AVDD+AVSS)/2 -41.58 % |
