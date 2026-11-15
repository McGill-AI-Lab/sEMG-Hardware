# ADS1298 clamshell validation — summary

Run: 2026-11-15_125013_sim · simulator (clean, 5× speed) · 112 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✓ PASS | 112/112 captures trustworthy |
| A | Shorted-input noise floor | ✓ PASS | 500 SPS: median 0.634 µVrms; 2000 SPS: median 1.24 µVrms; 4000 SPS: median 1.74 µVrms |
| B | Noise spectrum (PSD) | ✓ PASS | floor ≈ 38 nV/√Hz, 0 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.586 µVrms, e_ADC ≈ 1.57 µVrms; suggested gain G4 |
| D | Data-rate sweep | ✓ PASS | RMS grows with rate^0.48 (white noise = 0.50). |
| E | Multichannel correlation | ✓ PASS | 500 SPS: max |r| = 0.075, channel-average ratio 1.06 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ! WARN | 2 of 19 variants affect the noise |
| G | Internal test signal | ✓ PASS | median amplitude 2.0000 mV vs 2.000 mV expected (+0.0 %) |
| H | Supply measurement (MVDD) | ✓ PASS | WiFi off: (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45 µVrms |
| I | Temperature & long-term drift | ✓ PASS | temperature 29.94 → 29.95 °C over 19 s (range 29.94–29.95 °C) |

## P · Prerequisites & data integrity — PASS

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **PASS** All 112 captures passed the integrity checks.

## A · Shorted-input noise floor — PASS

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **PASS** 500 SPS: median 0.634 µVrms, 1.12× expected (worst 1.16×)
- **PASS** 2000 SPS: median 1.24 µVrms, 1.09× expected (worst 1.12×)
- **PASS** 4000 SPS: median 1.74 µVrms, 1.09× expected (worst 1.10×)

## B · Noise spectrum (PSD) — PASS

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **PASS** No spectral lines above the threshold: the floor is clean.

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.586 µVrms, e_ADC ≈ 1.57 µVrms; suggested gain G4
- **INFO** 2000 SPS: e_PGA ≈ 1.12 µVrms, e_ADC ≈ 3.18 µVrms; suggested gain G4
- **INFO** 4000 SPS: e_PGA ≈ 1.58 µVrms, e_ADC ≈ 4.47 µVrms; suggested gain G4

## D · Data-rate sweep — PASS

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **PASS** RMS grows with rate^0.48 (white noise = 0.50).

## E · Multichannel correlation — PASS

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **PASS** 500 SPS: max |r| = 0.075, channel-average ratio 1.06 (1 = independent, 2.83 = fully shared)
- **PASS** 2000 SPS: max |r| = 0.038, channel-average ratio 1.04 (1 = independent, 2.83 = fully shared)
- **PASS** 4000 SPS: max |r| = 0.028, channel-average ratio 1.03 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 500 SPS, WiFi scanning (continuous TX): noise +9.4 %, pp/rms 14
- **WARN** 2000 SPS, WiFi scanning (continuous TX): noise +2.8 %, pp/rms 10

## G · Internal test signal — PASS

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **PASS** median amplitude 2.0000 mV vs 2.000 mV expected (+0.0 %)
- **PASS** Gain cross-check: amplitude spread across gains 1.000× (1.00 ideal); log-log slope vs gain +0.00
- **PASS** Noise on DC test levels is close to the shorted noise: reference noise negligible.

## H · Supply measurement (MVDD) — PASS

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **PASS** WiFi off: (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45 µVrms
- **PASS** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45.2 µVrms

## I · Temperature & long-term drift — PASS

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **PASS** temperature 29.94 → 29.95 °C over 19 s (range 29.94–29.95 °C)
- **INFO** longest useful averaging time ≈ 4.98 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | 0.7461 | 0.6134 | 3.862 | 6.296 | PASS |
| A | shorted, each | 6 | HR 500 | 2 | 26.87 | 0.6508 | 4.005 | 6.154 | PASS |
| A | shorted, each | 6 | HR 500 | 3 | -21.2 | 0.626 | 4.148 | 6.627 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 26.96 | 0.6336 | 4.339 | 6.848 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | -11.32 | 0.6588 | 4.864 | 7.382 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | -4.34 | 0.6494 | 4.435 | 6.829 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | 19.51 | 0.6297 | 5.054 | 8.027 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -5.572 | 0.6337 | 4.482 | 7.073 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | 0.7478 | 0.6572 | 4.435 | 6.747 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | 26.6 | 0.6448 | 4.148 | 6.434 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -21.07 | 0.63 | 4.339 | 6.888 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 26.94 | 0.6164 | 3.958 | 6.42 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -11.45 | 0.6307 | 4.196 | 6.653 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | -4.452 | 0.655 | 4.148 | 6.334 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | 19.54 | 0.6391 | 4.101 | 6.416 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -5.506 | 0.6335 | 3.91 | 6.172 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | 0.8134 | 1.234 | 9.775 | 7.922 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | 26.65 | 1.251 | 9.489 | 7.582 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -21.12 | 1.227 | 10.01 | 8.164 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 26.91 | 1.214 | 8.678 | 7.15 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | -11.43 | 1.236 | 9.203 | 7.448 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | -4.226 | 1.245 | 8.869 | 7.126 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | 19.43 | 1.239 | 9.394 | 7.579 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -5.5 | 1.234 | 8.774 | 7.11 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | 0.8437 | 1.268 | 9.012 | 7.107 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | 26.38 | 1.254 | 9.346 | 7.452 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -21.02 | 1.255 | 9.632 | 7.673 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 27.01 | 1.235 | 9.203 | 7.449 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -11.5 | 1.239 | 9.584 | 7.736 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | -4.179 | 1.237 | 9.298 | 7.516 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | 19.42 | 1.249 | 9.108 | 7.294 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -5.485 | 1.268 | 8.726 | 6.881 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | 0.7664 | 1.744 | 13.21 | 7.573 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | 26.39 | 1.751 | 14.4 | 8.222 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -20.94 | 1.738 | 13.26 | 7.625 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 26.94 | 1.732 | 14.07 | 8.123 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | -11.62 | 1.759 | 13.21 | 7.507 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | -4.151 | 1.735 | 13.35 | 7.694 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | 19.38 | 1.745 | 13.4 | 7.678 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -5.548 | 1.769 | 13.49 | 7.627 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | 0.803 | 1.756 | 13.26 | 7.549 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | 26.33 | 1.768 | 13.49 | 7.632 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -20.95 | 1.737 | 13.07 | 7.521 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 27.03 | 1.749 | 13.88 | 7.932 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -11.5 | 1.742 | 12.78 | 7.336 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | -4.052 | 1.741 | 13.07 | 7.506 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | 19.28 | 1.749 | 12.92 | 7.39 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -5.598 | 1.741 | 13.69 | 7.86 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 1.713 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 1.003 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 0.7748 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.7219 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.6458 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.6229 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.6006 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 1.692 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 1.018 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.7941 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.678 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.6446 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.6024 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.5919 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 1.66 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 0.9577 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 0.7668 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 0.7259 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.6384 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.6199 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.6053 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 1.672 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 0.9551 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 0.7889 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.7012 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.6399 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.612 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.5905 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 1.643 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 1.014 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 0.8063 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.7106 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.6257 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.6198 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.5972 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 1.72 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 1.003 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 0.7823 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.7336 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.6377 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.6199 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.6121 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 1.671 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 0.9825 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.7967 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.7122 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.6264 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.6114 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.5803 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 1.675 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 1.002 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.7841 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.7067 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.6508 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.6266 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.6008 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 3.363 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 1.939 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 1.544 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.371 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.258 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 1.189 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 1.159 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 3.421 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 1.949 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.554 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.384 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 1.256 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 1.191 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 1.158 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 3.367 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 1.92 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 1.542 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 1.375 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.242 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 1.174 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 1.163 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 3.368 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 1.927 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 1.536 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.38 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.249 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 1.188 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 1.162 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 3.404 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 1.946 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 1.52 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.397 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.253 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 1.178 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 1.166 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 3.37 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 1.955 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.526 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.37 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.23 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 1.181 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 1.154 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 3.4 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 1.928 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.555 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.373 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.241 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 1.194 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 1.168 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 3.33 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 1.945 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.536 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.395 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 1.243 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 1.196 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 1.151 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 4.744 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 2.741 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.189 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 1.928 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.731 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.675 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.617 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 4.74 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 2.732 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.176 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 1.934 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.752 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.674 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 1.633 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 4.811 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 2.721 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 2.185 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 1.97 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.758 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.7 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.613 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 4.738 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 2.754 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.175 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 1.959 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.749 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.666 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.63 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 4.737 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 2.724 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.17 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 1.929 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.749 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.678 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.628 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 4.711 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 2.752 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.164 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 1.951 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.768 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.689 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.643 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 4.729 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 2.727 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.181 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 1.938 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.753 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.674 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 1.619 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 4.7 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 2.748 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.179 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 1.943 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.754 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.657 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 1.625 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | 0.7957 | 0.6419 | 5.007 | 7.8 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | 25.96 | 0.6164 | 3.862 | 6.266 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -20.85 | 0.6436 | 3.958 | 6.15 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 27.05 | 0.6227 | 4.244 | 6.815 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -11.67 | 0.6315 | 4.387 | 6.946 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | -3.967 | 0.665 | 4.387 | 6.597 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | 19.23 | 0.6454 | 4.387 | 6.797 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -5.576 | 0.6319 | 4.578 | 7.245 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | 0.7985 | 0.6382 | 4.244 | 6.65 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | 26.11 | 0.6424 | 4.387 | 6.829 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -20.84 | 0.6502 | 4.387 | 6.747 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 27.01 | 0.6345 | 4.387 | 6.914 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -11.64 | 0.6293 | 4.435 | 7.047 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | -3.859 | 0.6637 | 4.625 | 6.969 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | 19.25 | 0.6607 | 4.673 | 7.072 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -5.477 | 0.6432 | 4.482 | 6.968 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | 0.7917 | 0.6584 | 4.53 | 6.88 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | 26.03 | 0.6704 | 4.292 | 6.402 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -20.88 | 0.677 | 4.578 | 6.762 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 26.98 | 0.6603 | 4.148 | 6.283 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -11.6 | 0.6773 | 4.53 | 6.688 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | -4.013 | 0.6849 | 4.482 | 6.545 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | 19.19 | 0.6487 | 4.435 | 6.836 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -5.506 | 0.673 | 4.196 | 6.235 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | 0.8177 | 0.6188 | 4.101 | 6.627 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | 26.12 | 0.6574 | 4.292 | 6.528 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -20.81 | 0.6472 | 4.292 | 6.631 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 27.09 | 0.6251 | 4.005 | 6.408 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -11.72 | 0.6207 | 3.862 | 6.222 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | -3.993 | 0.6323 | 4.053 | 6.41 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | 19.35 | 0.656 | 4.625 | 7.051 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -5.493 | 0.6681 | 4.196 | 6.28 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | 0.8936 | 0.6773 | 4.244 | 6.266 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | 26.03 | 0.6492 | 4.387 | 6.758 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -20.84 | 0.6399 | 4.339 | 6.782 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 27.11 | 0.6315 | 4.339 | 6.871 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -11.59 | 0.653 | 4.005 | 6.134 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | -3.985 | 0.6305 | 3.91 | 6.202 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | 19.28 | 0.6613 | 5.102 | 7.715 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -5.459 | 0.6229 | 4.387 | 7.042 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | 0.8453 | 0.6998 | 6.866 | 9.812 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | 26.06 | 0.6814 | 7.82 | 11.48 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -20.86 | 0.717 | 9.012 | 12.57 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 26.86 | 0.7072 | 8.774 | 12.41 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -11.66 | 0.7071 | 7.01 | 9.913 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | -3.954 | 0.6857 | 7.248 | 10.57 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | 19.3 | 0.6846 | 7.296 | 10.66 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -5.59 | 0.6964 | 9.632 | 13.83 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | 0.7694 | 0.6452 | 3.815 | 5.912 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | 25.94 | 0.5381 | 3.195 | 5.937 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -20.85 | 0.6053 | 3.433 | 5.672 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 26.98 | 0.61 | 4.148 | 6.801 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -11.56 | 0.5807 | 3.576 | 6.159 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | -4.014 | 0.6121 | 3.958 | 6.466 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | 18.95 | 0.6135 | 3.672 | 5.985 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -5.655 | 0.6335 | 3.624 | 5.72 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | 0.8637 | 1.248 | 9.346 | 7.489 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | 25.99 | 1.238 | 9.727 | 7.855 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -20.79 | 1.239 | 9.727 | 7.849 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 26.98 | 1.251 | 9.346 | 7.468 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -11.47 | 1.216 | 8.965 | 7.371 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | -4.018 | 1.239 | 9.727 | 7.85 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | 19.31 | 1.248 | 9.871 | 7.909 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -5.555 | 1.241 | 10.63 | 8.567 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | 0.8792 | 1.316 | 9.775 | 7.426 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | 25.96 | 1.301 | 9.727 | 7.475 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -20.77 | 1.312 | 9.823 | 7.489 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 26.98 | 1.303 | 10.11 | 7.76 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -11.69 | 1.302 | 10.78 | 8.278 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | -4.043 | 1.31 | 10.35 | 7.901 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | 19.33 | 1.306 | 9.108 | 6.973 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -5.465 | 1.315 | 9.68 | 7.361 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | 0.7714 | 1.24 | 9.346 | 7.537 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | 26.12 | 1.25 | 9.346 | 7.476 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -20.78 | 1.262 | 9.489 | 7.52 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 27 | 1.266 | 9.06 | 7.157 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -11.7 | 1.243 | 9.871 | 7.941 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | -3.904 | 1.269 | 10.06 | 7.929 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | 19.17 | 1.243 | 10.54 | 8.476 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -5.611 | 1.244 | 8.869 | 7.128 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | 0.7923 | 1.249 | 9.584 | 7.672 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | 25.97 | 1.25 | 9.632 | 7.709 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -20.81 | 1.251 | 9.06 | 7.241 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 27.04 | 1.263 | 9.632 | 7.629 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -11.61 | 1.236 | 9.537 | 7.717 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | -4.079 | 1.234 | 8.821 | 7.147 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | 19.2 | 1.24 | 9.632 | 7.765 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -5.589 | 1.232 | 9.346 | 7.586 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | 0.7231 | 1.284 | 10.01 | 7.8 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | 26 | 1.265 | 11.11 | 8.781 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -20.84 | 1.271 | 10.4 | 8.177 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 27.04 | 1.284 | 11.78 | 9.174 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -11.67 | 1.275 | 12.97 | 10.18 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | -3.87 | 1.271 | 10.3 | 8.101 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | 19.42 | 1.288 | 11.87 | 9.217 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -5.577 | 1.264 | 9.489 | 7.508 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | 0.7905 | 1.221 | 8.917 | 7.306 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | 25.97 | 1.234 | 9.203 | 7.456 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -20.79 | 1.218 | 7.772 | 6.381 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 26.9 | 1.164 | 7.343 | 6.306 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -11.64 | 1.219 | 8.583 | 7.041 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | -3.921 | 1.183 | 8.44 | 7.134 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | 19.24 | 1.218 | 7.677 | 6.305 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -5.734 | 1.211 | 8.106 | 6.693 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | 0.7474 | 1.738 | 13.83 | 7.955 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | 26.12 | 1.771 | 14.02 | 7.914 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -20.73 | 1.748 | 13.26 | 7.584 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 27.01 | 1.741 | 13.45 | 7.722 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -11.62 | 1.738 | 13.3 | 7.653 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | -3.977 | 1.739 | 13.92 | 8.005 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | 19.22 | 1.749 | 13.3 | 7.606 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -5.528 | 1.751 | 13.54 | 7.735 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | 0.8833 | 1.827 | 13.49 | 7.386 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | 25.89 | 1.862 | 14.31 | 7.683 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -20.82 | 1.824 | 14.97 | 8.21 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 27 | 1.838 | 14.59 | 7.938 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -11.63 | 1.83 | 14.07 | 7.687 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | -4.053 | 1.853 | 14.35 | 7.744 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | 19.16 | 1.85 | 15.5 | 8.377 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -5.481 | 1.83 | 15.35 | 8.391 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | 0.9188 | 1.755 | 13.78 | 7.852 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | 26.06 | 1.752 | 13.92 | 7.946 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -20.81 | 1.784 | 13.4 | 7.51 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 26.99 | 1.741 | 13.11 | 7.532 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -11.71 | 1.757 | 13.64 | 7.762 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | -3.988 | 1.751 | 13.3 | 7.599 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | 19.15 | 1.746 | 12.4 | 7.1 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -5.577 | 1.763 | 13.3 | 7.546 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | 0.8439 | 1.764 | 12.97 | 7.353 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | 26.05 | 1.75 | 13.78 | 7.874 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -20.83 | 1.743 | 13.26 | 7.605 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 26.94 | 1.727 | 12.68 | 7.346 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -11.5 | 1.746 | 15.21 | 8.71 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | -4.058 | 1.763 | 13.97 | 7.927 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | 19.16 | 1.755 | 13.35 | 7.608 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -5.576 | 1.764 | 14.02 | 7.949 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | 0.9222 | 1.782 | 14.97 | 8.401 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | 25.97 | 1.774 | 14.5 | 8.169 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -20.75 | 1.746 | 13.78 | 7.892 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 26.97 | 1.737 | 13.11 | 7.548 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -11.75 | 1.783 | 14.83 | 8.319 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | -3.933 | 1.778 | 14.69 | 8.259 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | 19.18 | 1.775 | 13.11 | 7.386 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -5.663 | 1.751 | 13.78 | 7.87 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | 0.9346 | 1.718 | 12.25 | 7.135 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | 26.09 | 1.679 | 13.21 | 7.865 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -20.74 | 1.708 | 13.16 | 7.706 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 27.15 | 1.671 | 11.83 | 7.077 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -11.82 | 1.704 | 12.35 | 7.249 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | -3.966 | 1.714 | 12.16 | 7.094 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | 19.24 | 1.709 | 12.4 | 7.254 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -5.575 | 1.712 | 13.11 | 7.657 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | 0.7069 | 0.6444 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | 26.91 | 0.6226 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -21.35 | 0.6313 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | 26.94 | 0.6431 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -11.28 | 0.6353 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -4.618 | 0.6079 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | 19.65 | 0.6519 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -5.416 | 0.6519 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | 0.7822 | 0.6346 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | 27.06 | 0.6287 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -21.39 | 0.637 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | 26.98 | 0.6206 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -11.24 | 0.63 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -4.61 | 0.6655 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | 19.71 | 0.6345 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -5.456 | 0.6244 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | 0.7148 | 1.249 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | 27.06 | 1.231 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -21.36 | 1.227 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | 26.82 | 1.24 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -11.37 | 1.224 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -4.606 | 1.239 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | 19.66 | 1.24 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -5.494 | 1.246 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | 0.6477 | 1.25 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | 27.02 | 1.226 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -21.35 | 1.223 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | 26.94 | 1.237 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -11.33 | 1.234 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -4.626 | 1.234 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | 19.68 | 1.244 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -5.41 | 1.235 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | 0.5502 | 1.743 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | 27.09 | 1.741 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -21.41 | 1.743 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | 26.93 | 1.734 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -11.31 | 1.77 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -4.668 | 1.751 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | 19.67 | 1.747 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -5.445 | 1.757 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | 0.7868 | 1.742 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | 26.98 | 1.744 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -21.28 | 1.727 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | 26.82 | 1.735 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -11.28 | 1.742 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -4.591 | 1.727 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | 19.78 | 1.732 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -5.43 | 1.732 |  |  | amplitude 2.0000 mV (-0.0 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.647e+06 | 46 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.647e+06 | 44.57 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 8.25e+05 | 44.51 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 8.25e+05 | 45.11 |  |  | DVDD/4 +0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.647e+06 | 45.05 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.647e+06 | 45.7 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 1.647e+06 | 44.9 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 1.647e+06 | 44.38 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.647e+06 | 42.98 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.647e+06 | 44.62 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 8.25e+05 | 45.33 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 8.25e+05 | 45.92 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.647e+06 | 44.85 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.647e+06 | 45.23 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 1.647e+06 | 45.66 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 1.647e+06 | 46.48 |  |  | (AVDD+AVSS)/2 -0.20 % |
