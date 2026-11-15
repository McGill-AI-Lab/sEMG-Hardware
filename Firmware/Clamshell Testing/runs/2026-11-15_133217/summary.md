# ADS1298 clamshell validation — summary

Run: 2026-11-15_133217 · hardware on /dev/cu.usbserial-1140 · 114 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 113/114 captures trustworthy |
| A | Shorted-input noise floor | ✓ PASS | 500 SPS: median 0.669 µVrms; 2000 SPS: median 1.19 µVrms; 4000 SPS: median 1.75 µVrms |
| B | Noise spectrum (PSD) | ✓ PASS | floor ≈ 43 nV/√Hz, 0 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 3.36 µVrms, e_ADC ≈ 0 µVrms; suggested gain G12 |
| D | Data-rate sweep | ✓ PASS | RMS grows with rate^0.44 (white noise = 0.50). |
| E | Multichannel correlation | ! WARN | 500 SPS: max |r| = 0.056, channel-average ratio 1 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ! WARN | 1 of 19 variants affect the noise |
| G | Internal test signal | ✕ FAIL | median amplitude 0.1554 mV vs 2.000 mV expected (-92.2 %) |
| H | Supply measurement (MVDD) | ✕ FAIL | WiFi off: (AVDD+AVSS)/2 = 1.479 V, DVDD/4 = 0.815 V, ripple ≈ 882 µVrms |
| I | Temperature & long-term drift | ✓ PASS | temperature 18.05 → 18.21 °C over 119 s (range 18.03–18.21 °C) |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 1 of 114 captures in this run failed integrity checks.

## A · Shorted-input noise floor — PASS

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **PASS** 500 SPS: median 0.669 µVrms, 1.18× expected (worst 1.27×)
- **PASS** 2000 SPS: median 1.19 µVrms, 1.05× expected (worst 1.12×)
- **PASS** 4000 SPS: median 1.75 µVrms, 1.09× expected (worst 1.14×)

## B · Noise spectrum (PSD) — PASS

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **PASS** No spectral lines above the threshold: the floor is clean.

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 3.36 µVrms, e_ADC ≈ 0 µVrms; suggested gain G12
- **INFO** 2000 SPS: e_PGA ≈ 0.828 µVrms, e_ADC ≈ 4.83 µVrms; suggested gain G12
- **INFO** 4000 SPS: e_PGA ≈ 1.13 µVrms, e_ADC ≈ 7.1 µVrms; suggested gain G12

## D · Data-rate sweep — PASS

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **PASS** RMS grows with rate^0.44 (white noise = 0.50).

## E · Multichannel correlation — WARN

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **PASS** 500 SPS: max |r| = 0.056, channel-average ratio 1 (1 = independent, 2.83 = fully shared)
- **PASS** 2000 SPS: max |r| = 0.032, channel-average ratio 1.04 (1 = independent, 2.83 = fully shared)
- **WARN** 4000 SPS: max |r| = 0.066, channel-average ratio 1.08 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 4000 SPS, WiFi scanning (continuous TX): noise +0.6 %, pp/rms 8.7

## G · Internal test signal — FAIL

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **FAIL** median amplitude 0.1554 mV vs 2.000 mV expected (-92.2 %) — almost exactly 1/12 of expected: the PGA gain and the scaling do not match
- **FAIL** Gain cross-check: amplitude spread across gains 1.168× (1.00 ideal); log-log slope vs gain +0.06
- **FAIL** Noise on DC test levels exceeds shorted noise in 6 cases: reference noise.

## H · Supply measurement (MVDD) — FAIL

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **FAIL** WiFi off: (AVDD+AVSS)/2 = 1.479 V, DVDD/4 = 0.815 V, ripple ≈ 882 µVrms
- **FAIL** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.478 V, DVDD/4 = 0.814 V, ripple ≈ 878 µVrms

## I · Temperature & long-term drift — PASS

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **PASS** temperature 18.05 → 18.21 °C over 119 s (range 18.03–18.21 °C)
- **INFO** longest useful averaging time ≈ 1.39 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | -273.9 | 0.7124 | 5.007 | 7.028 | PASS |
| A | shorted, each | 6 | HR 500 | 2 | -63.71 | 0.6441 | 4.816 | 7.478 | PASS |
| A | shorted, each | 6 | HR 500 | 3 | -203.6 | 0.6466 | 4.387 | 6.785 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 64.55 | 0.7022 | 4.959 | 7.062 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | 124.3 | 0.656 | 4.482 | 6.833 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | 68.78 | 0.7025 | 4.864 | 6.923 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | -155 | 0.6727 | 5.054 | 7.514 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -476.2 | 0.653 | 4.911 | 7.521 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | -275 | 0.7196 | 5.579 | 7.753 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | -65.31 | 0.7209 | 5.245 | 7.276 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -201.5 | 0.6634 | 5.484 | 8.266 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 55.81 | 0.6755 | 5.15 | 7.624 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | 123.2 | 0.7066 | 5.102 | 7.221 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | 66.81 | 0.6662 | 5.531 | 8.303 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | -155.7 | 0.6472 | 4.482 | 6.925 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -485.4 | 0.6622 | 4.339 | 6.552 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | -274.1 | 1.273 | 10.59 | 8.317 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | -63.49 | 1.186 | 9.823 | 8.285 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -202.6 | 1.182 | 9.203 | 7.784 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 64.58 | 1.2 | 9.489 | 7.906 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | 124.3 | 1.19 | 9.584 | 8.057 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | 68.37 | 1.205 | 10.11 | 8.391 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | -154.8 | 1.203 | 10.16 | 8.444 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -475.8 | 1.199 | 10.63 | 8.866 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | -273.8 | 1.246 | 10.16 | 8.151 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | -65.18 | 1.177 | 9.632 | 8.185 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -200.8 | 1.259 | 10.44 | 8.294 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 55.99 | 1.204 | 9.871 | 8.2 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | 122.8 | 1.188 | 10.68 | 8.99 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | 66.38 | 1.188 | 9.632 | 8.107 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | -155.1 | 1.155 | 9.108 | 7.888 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -483.9 | 1.164 | 9.394 | 8.071 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | -273.1 | 1.827 | 14.11 | 7.725 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | -63.64 | 1.738 | 14.54 | 8.367 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -202.5 | 1.778 | 15.69 | 8.822 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 64.63 | 1.766 | 15.5 | 8.774 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | 124.8 | 1.745 | 14.07 | 8.062 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | 67.89 | 1.765 | 14.78 | 8.377 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | -154.4 | 1.753 | 14.69 | 8.377 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -474.6 | 1.752 | 14.59 | 8.328 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | -273.5 | 1.767 | 14.93 | 8.445 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | -65.44 | 1.685 | 14.4 | 8.546 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -200.2 | 1.772 | 15.83 | 8.932 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 55.64 | 1.701 | 13.83 | 8.128 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | 123.2 | 1.691 | 14.16 | 8.374 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | 66.19 | 1.689 | 16.31 | 9.655 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | -155.3 | 1.679 | 13.54 | 8.064 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -483.5 | 1.688 | 13.64 | 8.08 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 2.163 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 1.266 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 0.9555 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.8719 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 8.162 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 4.237 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.564 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 2.449 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 1.308 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.9855 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.7729 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 14.4 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 6.84 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.5679 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 2.517 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 1.34 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 1.002 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 0.8229 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 4.379 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 4.472 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.5961 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 2.485 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 1.414 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 1.056 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.8341 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 8.683 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 4.188 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.4942 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 2.435 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 1.335 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 0.9577 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.7985 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 6.875 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 3.162 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.4627 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 2.394 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 1.27 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 0.9627 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.7831 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 2.449 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 1.275 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.4779 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 2.405 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 1.294 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.988 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.8295 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 5.842 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 2.683 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.5333 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 2.451 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 1.333 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.9826 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.805 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 14.43 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 5.606 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.5394 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 4.805 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 2.744 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 2.008 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.604 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.195 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 1.085 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 0.8618 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 4.945 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 2.594 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.881 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.481 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 1.115 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 0.9462 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 0.7995 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 5.223 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 2.743 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 1.967 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 1.567 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.169 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 0.9722 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 0.8131 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 4.896 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 2.585 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 1.84 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.478 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.119 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 0.9597 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 0.7996 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 4.97 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 2.681 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 1.916 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.494 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.126 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 0.9558 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 0.7938 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 4.895 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 2.607 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.855 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.461 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.117 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 0.9633 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 0.8007 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 4.834 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 2.586 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.855 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.464 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.108 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 0.9414 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 0.7852 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 4.829 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 2.589 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.855 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.487 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 1.15 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 0.9382 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 0.7802 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 7.178 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 3.936 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.968 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 2.314 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.705 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.43 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.178 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 7.289 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 3.806 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.742 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 2.134 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.586 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.306 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 1.097 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 7.968 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 4.134 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 2.972 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 2.339 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.68 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.418 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.128 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 7.082 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 3.745 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.679 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 2.103 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.565 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.33 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.087 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 7.294 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 3.853 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.775 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 2.174 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.603 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.333 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.086 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 7.204 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 3.771 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.711 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 2.134 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.584 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.331 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.096 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 7.111 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 3.756 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.689 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 2.144 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.571 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.355 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 1.121 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 7.118 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 3.746 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.694 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 2.148 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.562 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.304 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 1.091 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | -230.9 | 0.659 | 4.339 | 6.585 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | -142.4 | 0.6233 | 4.53 | 7.268 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -169.8 | 0.6472 | 4.816 | 7.442 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 10.4 | 0.6013 | 4.339 | 7.217 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | 88.68 | 0.6038 | 4.721 | 7.819 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | 78.82 | 0.6307 | 4.768 | 7.56 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | -126.7 | 0.6301 | 4.244 | 6.735 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -412.7 | 0.6046 | 4.387 | 7.256 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | -232.1 | 0.8337 | 5.245 | 6.291 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | -142.9 | 0.5954 | 4.292 | 7.207 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -170.4 | 0.6266 | 4.387 | 7.001 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 10.62 | 0.5973 | 4.101 | 6.865 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | 89.42 | 0.5856 | 4.292 | 7.328 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | 78.87 | 0.6086 | 4.387 | 7.208 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | -127.5 | 0.5989 | 4.292 | 7.166 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -414 | 0.6195 | 4.292 | 6.927 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | -230.7 | 0.7672 | 5.054 | 6.588 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | -142.3 | 0.6314 | 4.482 | 7.099 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -169.4 | 0.7282 | 5.007 | 6.875 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 10.26 | 0.6187 | 4.244 | 6.86 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | 88.6 | 0.6249 | 4.578 | 7.325 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | 78.65 | 0.5898 | 4.387 | 7.438 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | -126.7 | 0.6364 | 4.435 | 6.969 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -411.7 | 0.8732 | 5.341 | 6.116 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | -231.3 | 0.6951 | 4.768 | 6.86 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | -142.4 | 0.6013 | 4.482 | 7.454 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -170 | 0.6217 | 4.482 | 7.209 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 10.67 | 0.589 | 4.292 | 7.286 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | 88.99 | 0.652 | 4.816 | 7.386 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | 78.77 | 0.5789 | 4.244 | 7.331 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | -127 | 0.6111 | 5.007 | 8.193 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -412.8 | 0.6009 | 4.387 | 7.3 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | -231.3 | 0.6997 | 4.721 | 6.747 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | -142 | 0.6064 | 4.435 | 7.313 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -170.2 | 0.6243 | 5.198 | 8.325 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 10.74 | 0.6016 | 4.435 | 7.372 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | 89.43 | 0.6085 | 4.721 | 7.757 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | 78.65 | 0.596 | 4.292 | 7.201 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | -127.1 | 0.6 | 4.292 | 7.153 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -412.9 | 0.6211 | 4.339 | 6.986 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | -231.5 | 0.6478 | 4.339 | 6.699 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | -142.4 | 0.5893 | 4.101 | 6.959 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -170 | 0.613 | 4.673 | 7.623 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 10.77 | 0.5912 | 4.578 | 7.743 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | 89.38 | 0.587 | 4.53 | 7.717 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | 78.76 | 0.6142 | 4.768 | 7.764 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | -127 | 0.6324 | 4.435 | 7.012 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -413.2 | 0.6192 | 3.958 | 6.391 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | -231.2 | 0.6594 | 3.815 | 5.785 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | -142.7 | 0.5913 | 3.338 | 5.645 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -170.4 | 0.6037 | 3.767 | 6.24 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 10.45 | 0.5746 | 4.005 | 6.971 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | 89.48 | 0.6324 | 3.719 | 5.881 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | 78.79 | 0.5447 | 3.29 | 6.041 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | -127.1 | 0.5765 | 3.624 | 6.286 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -412.5 | 0.5581 | 3.338 | 5.98 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | -230.9 | 1.202 | 10.87 | 9.043 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | -142.7 | 1.112 | 9.441 | 8.49 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -169.6 | 1.139 | 9.012 | 7.914 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 10.46 | 1.11 | 8.821 | 7.946 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | 89.31 | 1.105 | 8.821 | 7.984 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | 78.78 | 1.103 | 8.774 | 7.957 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | -126.9 | 1.1 | 9.394 | 8.536 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -412.3 | 1.096 | 9.155 | 8.351 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | -229.9 | 1.184 | 9.346 | 7.895 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | -141.8 | 1.121 | 9.108 | 8.122 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -169 | 1.136 | 8.631 | 7.6 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 10.52 | 1.107 | 9.441 | 8.531 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | 88.58 | 1.116 | 8.202 | 7.347 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | 78.65 | 1.103 | 8.678 | 7.868 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | -126.2 | 1.116 | 8.154 | 7.309 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -410.5 | 1.107 | 8.726 | 7.881 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | -231.1 | 1.23 | 9.823 | 7.985 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | -142.3 | 1.098 | 9.012 | 8.206 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -170.1 | 1.155 | 8.583 | 7.431 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 10.53 | 1.136 | 8.821 | 7.763 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | 89.09 | 1.099 | 8.631 | 7.85 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | 78.69 | 1.119 | 8.821 | 7.887 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | -127 | 1.093 | 8.392 | 7.676 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -412 | 1.098 | 9.108 | 8.297 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | -230.8 | 1.218 | 9.203 | 7.558 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | -141.9 | 1.107 | 9.155 | 8.274 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -169.8 | 1.167 | 9.108 | 7.806 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 10.16 | 1.116 | 9.108 | 8.16 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | 89.38 | 1.129 | 8.917 | 7.899 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | 78.8 | 1.098 | 9.871 | 8.99 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | -126.9 | 1.1 | 9.632 | 8.753 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -412.5 | 1.116 | 8.726 | 7.816 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | -231 | 1.189 | 10.68 | 8.982 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | -142.4 | 1.097 | 9.108 | 8.299 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -169.8 | 1.135 | 9.251 | 8.151 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 10.46 | 1.085 | 9.012 | 8.303 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | 89.11 | 1.116 | 9.203 | 8.246 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | 79.05 | 1.109 | 8.869 | 7.995 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | -127.3 | 1.095 | 8.678 | 7.927 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -412.6 | 1.094 | 9.394 | 8.589 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | -230.6 | 1.178 | 9.012 | 7.652 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | -142.6 | 1.084 | 7.629 | 7.038 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -170.4 | 1.109 | 7.057 | 6.364 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 10.05 | 1.136 | 7.391 | 6.507 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | 88.48 | 1.093 | 7.2 | 6.588 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | 79.22 | 1.069 | 7.82 | 7.318 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | -127.5 | 1.113 | 8.154 | 7.326 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -412.5 | 1.085 | 7.105 | 6.549 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | -230.6 | 1.69 | 14.07 | 8.322 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | -142.5 | 1.573 | 13.16 | 8.364 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -169.8 | 1.657 | 14.4 | 8.691 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 10.15 | 1.572 | 13.97 | 8.888 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | 88.78 | 1.597 | 14.4 | 9.019 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | 79.17 | 1.548 | 12.68 | 8.192 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | -127.3 | 1.555 | 12.49 | 8.032 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -412.3 | 1.559 | 13.59 | 8.716 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | -230.1 | 1.679 | 14.16 | 8.434 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | -141.9 | 1.564 | 12.25 | 7.837 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -169 | 1.614 | 14.02 | 8.687 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 10.07 | 1.543 | 12.78 | 8.285 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | 88.41 | 1.548 | 13.69 | 8.838 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | 78.65 | 1.548 | 12.25 | 7.919 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | -126.9 | 1.553 | 12.21 | 7.862 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -410.3 | 1.543 | 13.54 | 8.775 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | -230.5 | 1.692 | 13.88 | 8.203 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | -142.6 | 1.574 | 13.92 | 8.845 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -169.9 | 1.662 | 14.31 | 8.609 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 10.35 | 1.557 | 12.16 | 7.81 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | 88.8 | 1.589 | 13.16 | 8.281 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | 78.94 | 1.571 | 12.54 | 7.985 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | -127.6 | 1.558 | 13.78 | 8.845 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -412.2 | 1.552 | 13.21 | 8.513 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | -230.7 | 1.688 | 14.02 | 8.305 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | -142.6 | 1.568 | 11.87 | 7.57 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -170 | 1.657 | 13.59 | 8.202 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 10.3 | 1.577 | 12.59 | 7.985 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | 89.07 | 1.576 | 13.97 | 8.867 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | 78.99 | 1.56 | 15.35 | 9.842 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | -127.3 | 1.559 | 12.73 | 8.169 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -412.6 | 1.57 | 12.35 | 7.864 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | -230.7 | 1.703 | 14.07 | 8.258 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | -142.7 | 1.558 | 12.59 | 8.079 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -169.8 | 1.702 | 14.78 | 8.684 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 10.48 | 1.558 | 12.45 | 7.986 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | 88.99 | 1.584 | 12.54 | 7.917 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | 78.77 | 1.566 | 12.78 | 8.159 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | -127.3 | 1.568 | 12.64 | 8.058 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -412.6 | 1.594 | 12.97 | 8.139 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | -230.6 | 1.639 | 10.87 | 6.633 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | -143.3 | 1.547 | 11.44 | 7.396 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -169.7 | 1.63 | 11.4 | 6.99 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 10.65 | 1.557 | 11.78 | 7.565 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | 89.01 | 1.565 | 10.68 | 6.825 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | 78.81 | 1.564 | 11.59 | 7.411 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | -127 | 1.525 | 11.68 | 7.66 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -412.4 | 1.523 | 11.4 | 7.485 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | 193.2 | 0.6818 |  |  | amplitude 0.1424 mV (-92.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | 218.9 | 0.4143 |  |  | amplitude 0.1481 mV (-92.6 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | 189.2 | 0.4305 |  |  | amplitude 0.1516 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | 302.3 | 0.4147 |  |  | amplitude 0.1498 mV (-92.5 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | 332.3 | 0.4047 |  |  | amplitude 0.1465 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | 340.7 | 0.3924 |  |  | amplitude 0.1469 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | 219.6 | 0.4122 |  |  | amplitude 0.1524 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | 66.42 | 2.082 |  |  | amplitude 0.1460 mV (-92.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | 258.2 | 0.9473 |  |  | amplitude 0.1583 mV (-92.1 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | 289 | 1.197 |  |  | amplitude 0.1687 mV (-91.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | 255.4 | 1.388 |  |  | amplitude 0.1853 mV (-90.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | 416.8 | 1.372 |  |  | amplitude 0.1844 mV (-90.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | 436.1 | 1.362 |  |  | amplitude 0.1721 mV (-91.4 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | 453.4 | 1.365 |  |  | amplitude 0.1769 mV (-91.2 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | 303.5 | 1.371 |  |  | amplitude 0.1912 mV (-90.4 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | 108.7 | 1.278 |  |  | amplitude 0.1840 mV (-90.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | 193.8 | 1.051 |  |  | amplitude 0.1426 mV (-92.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | 218.5 | 0.8845 |  |  | amplitude 0.1482 mV (-92.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | 189.3 | 1.128 |  |  | amplitude 0.1518 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | 302.3 | 0.8412 |  |  | amplitude 0.1500 mV (-92.5 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | 331.6 | 0.8127 |  |  | amplitude 0.1465 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | 340 | 0.829 |  |  | amplitude 0.1469 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | 219.4 | 0.9456 |  |  | amplitude 0.1525 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | 66.45 | 2.541 |  |  | amplitude 0.1461 mV (-92.7 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | 257 | 1.535 |  |  | amplitude 0.1582 mV (-92.1 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | 286.8 | 1.957 |  |  | amplitude 0.1685 mV (-91.6 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | 253.7 | 2.194 |  |  | amplitude 0.1854 mV (-90.7 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | 415 | 2.136 |  |  | amplitude 0.1846 mV (-90.8 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | 433.3 | 2.192 |  |  | amplitude 0.1718 mV (-91.4 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | 450.7 | 2.178 |  |  | amplitude 0.1766 mV (-91.2 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | 301.5 | 2.235 |  |  | amplitude 0.1914 mV (-90.4 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | 107.2 | 2.042 |  |  | amplitude 0.1841 mV (-90.8 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | 194 | 1.956 |  |  | amplitude 0.1426 mV (-92.9 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | 218.3 | 1.925 |  |  | amplitude 0.1482 mV (-92.6 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | 189.6 | 2.206 |  |  | amplitude 0.1518 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | 302.2 | 1.489 |  |  | amplitude 0.1501 mV (-92.5 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | 331.5 | 1.406 |  |  | amplitude 0.1464 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | 339.9 | 1.377 |  |  | amplitude 0.1469 mV (-92.7 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | 220 | 2.17 |  |  | amplitude 0.1526 mV (-92.4 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | 67.2 | 3.213 |  |  | amplitude 0.1459 mV (-92.7 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | 255 | 2.268 |  |  | amplitude 0.1583 mV (-92.1 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | 285.1 | 2.784 |  |  | amplitude 0.1681 mV (-91.6 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | 252 | 3.303 |  |  | amplitude 0.1855 mV (-90.7 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | 412.9 | 3.122 |  |  | amplitude 0.1847 mV (-90.8 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | 431.4 | 3.093 |  |  | amplitude 0.1715 mV (-91.4 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | 447.6 | 3.225 |  |  | amplitude 0.1763 mV (-91.2 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | 300 | 3.251 |  |  | amplitude 0.1915 mV (-90.4 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | 105.8 | 3.037 |  |  | amplitude 0.1843 mV (-90.8 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.623e+06 | 865 |  |  | (AVDD+AVSS)/2 -1.64 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.617e+06 | 886.9 |  |  | (AVDD+AVSS)/2 -1.99 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 8.12e+05 | 423.3 |  |  | DVDD/4 -1.58 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 8.17e+05 | 424.3 |  |  | DVDD/4 -0.97 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.618e+06 | 882.5 |  |  | (AVDD+AVSS)/2 -1.93 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.618e+06 | 882.1 |  |  | (AVDD+AVSS)/2 -1.96 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 1.199e+06 | 1980 |  |  | (AVDD+AVSS)/2 -27.32 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 1.199e+06 | 1980 |  |  | (AVDD+AVSS)/2 -27.33 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.621e+06 | 862.7 |  |  | (AVDD+AVSS)/2 -1.73 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.616e+06 | 883.3 |  |  | (AVDD+AVSS)/2 -2.08 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 8.112e+05 | 422.1 |  |  | DVDD/4 -1.67 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 8.163e+05 | 423.8 |  |  | DVDD/4 -1.06 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.617e+06 | 878.8 |  |  | (AVDD+AVSS)/2 -2.02 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.616e+06 | 878.5 |  |  | (AVDD+AVSS)/2 -2.05 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 1.198e+06 | 1971 |  |  | (AVDD+AVSS)/2 -27.41 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 1.198e+06 | 1971 |  |  | (AVDD+AVSS)/2 -27.42 % |
