# ADS1298 clamshell validation — summary

Run: 2026-11-15_130451_sim · simulator (clean, 5× speed) · 112 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✓ PASS | 112/112 captures trustworthy |
| A | Shorted-input noise floor | ✓ PASS | 500 SPS: median 0.639 µVrms; 2000 SPS: median 1.25 µVrms; 4000 SPS: median 1.74 µVrms |
| B | Noise spectrum (PSD) | ✓ PASS | floor ≈ 39 nV/√Hz, 0 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.589 µVrms, e_ADC ≈ 1.57 µVrms; suggested gain G4 |
| D | Data-rate sweep | ✓ PASS | RMS grows with rate^0.48 (white noise = 0.50). |
| E | Multichannel correlation | ✓ PASS | 500 SPS: max |r| = 0.082, channel-average ratio 1.08 (1 = independent, 2.83 = fully shared) |
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

- **PASS** 500 SPS: median 0.639 µVrms, 1.13× expected (worst 1.17×)
- **PASS** 2000 SPS: median 1.25 µVrms, 1.10× expected (worst 1.12×)
- **PASS** 4000 SPS: median 1.74 µVrms, 1.09× expected (worst 1.11×)

## B · Noise spectrum (PSD) — PASS

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **PASS** No spectral lines above the threshold: the floor is clean.

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.589 µVrms, e_ADC ≈ 1.57 µVrms; suggested gain G4
- **INFO** 2000 SPS: e_PGA ≈ 1.13 µVrms, e_ADC ≈ 3.17 µVrms; suggested gain G4
- **INFO** 4000 SPS: e_PGA ≈ 1.59 µVrms, e_ADC ≈ 4.48 µVrms; suggested gain G4

## D · Data-rate sweep — PASS

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **PASS** RMS grows with rate^0.48 (white noise = 0.50).

## E · Multichannel correlation — PASS

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **PASS** 500 SPS: max |r| = 0.082, channel-average ratio 1.08 (1 = independent, 2.83 = fully shared)
- **PASS** 2000 SPS: max |r| = 0.047, channel-average ratio 1.05 (1 = independent, 2.83 = fully shared)
- **PASS** 4000 SPS: max |r| = 0.032, channel-average ratio 1.02 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 500 SPS, WiFi scanning (continuous TX): noise +8.1 %, pp/rms 13
- **WARN** 2000 SPS, WiFi scanning (continuous TX): noise +2.5 %, pp/rms 11

## G · Internal test signal — PASS

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **PASS** median amplitude 2.0000 mV vs 2.000 mV expected (+0.0 %)
- **PASS** Gain cross-check: amplitude spread across gains 1.000× (1.00 ideal); log-log slope vs gain -0.00
- **PASS** Noise on DC test levels is close to the shorted noise: reference noise negligible.

## H · Supply measurement (MVDD) — PASS

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **PASS** WiFi off: (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45 µVrms
- **PASS** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 44.8 µVrms

## I · Temperature & long-term drift — PASS

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **PASS** temperature 29.94 → 29.95 °C over 19 s (range 29.94–29.95 °C)
- **INFO** longest useful averaging time ≈ 4.98 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | 0.715 | 0.6165 | 4.148 | 6.729 | PASS |
| A | shorted, each | 6 | HR 500 | 2 | 26.84 | 0.6545 | 4.148 | 6.338 | PASS |
| A | shorted, each | 6 | HR 500 | 3 | -21.12 | 0.6324 | 4.625 | 7.314 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 26.84 | 0.6322 | 4.244 | 6.713 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | -11.45 | 0.6445 | 5.054 | 7.842 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | -4.41 | 0.6428 | 4.148 | 6.454 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | 19.46 | 0.636 | 4.244 | 6.673 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -5.582 | 0.6437 | 4.673 | 7.259 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | 0.8057 | 0.6552 | 4.101 | 6.259 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | 26.57 | 0.6622 | 4.005 | 6.049 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -21.1 | 0.6458 | 4.148 | 6.423 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 26.93 | 0.6343 | 4.148 | 6.54 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -11.53 | 0.6415 | 4.053 | 6.318 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | -4.372 | 0.6358 | 3.958 | 6.225 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | 19.46 | 0.6259 | 4.005 | 6.399 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -5.491 | 0.6331 | 4.339 | 6.854 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | 0.9061 | 1.257 | 9.871 | 7.855 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | 26.6 | 1.263 | 9.298 | 7.364 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -21.11 | 1.26 | 9.871 | 7.833 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 26.9 | 1.24 | 9.012 | 7.267 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | -11.49 | 1.226 | 8.297 | 6.766 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | -4.357 | 1.24 | 9.251 | 7.458 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | 19.43 | 1.25 | 9.298 | 7.437 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -5.446 | 1.229 | 8.535 | 6.943 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | 0.8533 | 1.251 | 8.774 | 7.013 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | 26.44 | 1.247 | 9.489 | 7.611 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -21.11 | 1.229 | 9.775 | 7.955 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 27.02 | 1.239 | 9.489 | 7.659 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -11.46 | 1.245 | 9.584 | 7.699 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | -4.226 | 1.231 | 9.298 | 7.552 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | 19.45 | 1.267 | 9.251 | 7.298 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -5.49 | 1.273 | 9.966 | 7.83 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | 0.7743 | 1.739 | 13.3 | 7.65 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | 26.39 | 1.75 | 14.35 | 8.202 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -20.92 | 1.743 | 13.26 | 7.605 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 26.94 | 1.729 | 14.02 | 8.106 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | -11.62 | 1.752 | 13.21 | 7.539 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | -4.135 | 1.736 | 13.4 | 7.72 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | 19.39 | 1.74 | 13.45 | 7.73 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -5.522 | 1.756 | 13.49 | 7.683 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | 0.8007 | 1.755 | 14.02 | 7.987 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | 26.31 | 1.774 | 13.45 | 7.58 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -20.95 | 1.734 | 13.26 | 7.646 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 26.97 | 1.776 | 13.78 | 7.758 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -11.6 | 1.762 | 13.69 | 7.765 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | -4.042 | 1.741 | 12.78 | 7.341 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | 19.3 | 1.741 | 13.45 | 7.724 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -5.526 | 1.734 | 14.21 | 8.196 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 1.71 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 0.9442 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 0.7784 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.6758 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.6508 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.6295 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.5918 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 1.678 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 0.9822 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.7828 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.7337 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.6403 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.6305 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.5974 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 1.655 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 1.001 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 0.7627 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 0.704 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.6317 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.6258 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.5955 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 1.782 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 0.9817 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 0.8211 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.7158 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.645 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.6332 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.6083 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 1.708 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 0.9877 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 0.8124 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.7073 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.6412 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.6268 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.6009 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 1.663 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 0.9805 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 0.7729 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.7012 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.6314 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.6148 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.5949 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 1.667 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 0.9985 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.7812 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.6679 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.638 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.6366 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.6251 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 1.628 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 0.9883 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.7918 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.6906 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.6482 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.609 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.5954 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 3.346 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 1.938 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 1.568 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.388 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.262 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 1.209 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 1.165 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 3.448 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 1.939 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.516 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.367 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 1.261 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 1.182 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 1.153 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 3.359 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 1.954 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 1.559 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 1.358 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.23 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 1.189 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 1.162 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 3.395 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 1.92 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 1.539 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.362 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.25 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 1.192 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 1.184 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 3.371 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 1.936 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 1.545 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.386 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.252 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 1.187 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 1.163 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 3.366 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 1.937 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.527 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.369 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.242 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 1.193 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 1.166 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 3.365 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 1.927 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.538 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.401 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.259 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 1.208 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 1.167 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 3.332 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 1.938 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.544 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.38 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 1.241 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 1.182 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 1.15 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 4.715 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 2.781 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.186 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 1.943 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.737 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.677 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.629 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 4.731 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 2.738 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.191 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 1.927 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.76 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.688 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 1.64 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 4.792 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 2.707 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 2.179 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 1.949 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.765 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.663 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.599 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 4.758 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 2.731 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.195 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 1.959 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.745 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.667 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.619 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 4.749 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 2.731 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.166 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 1.939 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.738 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.692 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.642 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 4.749 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 2.748 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.181 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 1.958 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.745 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.684 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.626 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 4.765 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 2.735 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.173 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 1.926 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.761 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.706 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 1.608 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 4.747 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 2.769 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.179 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 1.927 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.768 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.666 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 1.639 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | 0.8585 | 0.6157 | 4.482 | 7.28 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | 25.95 | 0.6384 | 3.767 | 5.901 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -20.76 | 0.6602 | 4.721 | 7.151 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 26.91 | 0.6189 | 4.339 | 7.012 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -11.65 | 0.6689 | 4.387 | 6.558 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | -3.972 | 0.631 | 3.91 | 6.196 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | 19.19 | 0.6488 | 4.244 | 6.541 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -5.604 | 0.6419 | 4.435 | 6.909 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | 0.8841 | 0.6386 | 4.387 | 6.869 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | 26.04 | 0.633 | 5.198 | 8.211 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -20.86 | 0.6515 | 4.816 | 7.393 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 27.14 | 0.6521 | 4.244 | 6.508 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -11.65 | 0.6521 | 4.768 | 7.313 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | -4.02 | 0.6353 | 3.958 | 6.229 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | 19.35 | 0.6537 | 4.53 | 6.93 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -5.458 | 0.6443 | 3.91 | 6.068 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | 0.8765 | 0.6667 | 4.292 | 6.437 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | 26.09 | 0.6662 | 4.482 | 6.728 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -20.89 | 0.645 | 3.91 | 6.062 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 26.92 | 0.6875 | 4.625 | 6.727 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -11.57 | 0.6994 | 4.387 | 6.273 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | -4.003 | 0.6779 | 4.578 | 6.752 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | 19.27 | 0.6672 | 4.482 | 6.718 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -5.671 | 0.6973 | 4.578 | 6.565 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | 0.8753 | 0.6588 | 4.101 | 6.224 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | 26.11 | 0.6419 | 4.292 | 6.686 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -20.78 | 0.6415 | 4.196 | 6.541 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 27.04 | 0.6262 | 4.387 | 7.006 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -11.63 | 0.6474 | 4.578 | 7.071 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | -3.918 | 0.6257 | 3.91 | 6.249 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | 19.29 | 0.6546 | 5.054 | 7.722 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -5.606 | 0.6495 | 3.91 | 6.02 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | 0.8135 | 0.6326 | 4.387 | 6.935 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | 26.08 | 0.6797 | 4.244 | 6.244 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -20.82 | 0.6578 | 4.482 | 6.814 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 27.04 | 0.6556 | 4.005 | 6.11 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -11.58 | 0.6571 | 4.721 | 7.184 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | -3.941 | 0.6293 | 4.244 | 6.743 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | 19.34 | 0.6258 | 3.815 | 6.096 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -5.56 | 0.6507 | 4.768 | 7.328 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | 0.7852 | 0.6604 | 7.01 | 10.61 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | 26.03 | 0.6906 | 9.298 | 13.46 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -20.91 | 0.6874 | 9.06 | 13.18 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 27.04 | 0.6783 | 8.106 | 11.95 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -11.72 | 0.7084 | 5.96 | 8.414 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | -3.912 | 0.738 | 9.584 | 12.99 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | 19.28 | 0.7262 | 8.821 | 12.15 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -5.596 | 0.6512 | 5.198 | 7.982 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | 0.843 | 0.598 | 3.481 | 5.821 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | 25.97 | 0.5886 | 3.147 | 5.347 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -20.84 | 0.6025 | 3.433 | 5.699 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 26.87 | 0.6031 | 3.576 | 5.929 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -11.81 | 0.5995 | 3.433 | 5.726 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | -3.988 | 0.6258 | 3.719 | 5.943 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | 19.23 | 0.64 | 3.958 | 6.184 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -5.654 | 0.5879 | 3.624 | 6.164 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | 0.8499 | 1.233 | 8.965 | 7.271 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | 26.07 | 1.268 | 10.06 | 7.933 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -20.8 | 1.247 | 9.06 | 7.266 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 27.06 | 1.267 | 9.441 | 7.455 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -11.73 | 1.225 | 8.154 | 6.657 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | -4.001 | 1.234 | 8.869 | 7.189 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | 19.28 | 1.243 | 10.44 | 8.398 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -5.605 | 1.246 | 9.394 | 7.542 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | 0.7606 | 1.315 | 10.35 | 7.871 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | 26.01 | 1.281 | 9.012 | 7.033 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -20.76 | 1.31 | 9.06 | 6.916 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 27.14 | 1.315 | 10.2 | 7.761 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -11.56 | 1.316 | 9.346 | 7.101 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | -3.898 | 1.299 | 9.727 | 7.49 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | 19.31 | 1.307 | 9.489 | 7.26 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -5.592 | 1.295 | 10.49 | 8.099 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | 0.7545 | 1.244 | 8.106 | 6.518 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | 26.15 | 1.267 | 9.584 | 7.563 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -20.83 | 1.263 | 9.727 | 7.702 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 26.94 | 1.239 | 10.54 | 8.505 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -11.59 | 1.234 | 9.108 | 7.378 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | -3.946 | 1.251 | 9.489 | 7.584 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | 19.26 | 1.269 | 8.774 | 6.916 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -5.564 | 1.232 | 9.251 | 7.51 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | 0.7755 | 1.258 | 9.441 | 7.506 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | 26.12 | 1.235 | 8.631 | 6.989 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -20.83 | 1.249 | 8.488 | 6.794 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 27 | 1.232 | 9.203 | 7.47 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -11.76 | 1.28 | 11.25 | 8.792 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | -3.991 | 1.25 | 10.49 | 8.395 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | 19.2 | 1.24 | 9.346 | 7.535 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -5.616 | 1.259 | 9.918 | 7.878 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | 0.888 | 1.274 | 9.298 | 7.298 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | 26.04 | 1.272 | 10.59 | 8.324 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -20.74 | 1.277 | 10.44 | 8.177 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 26.99 | 1.282 | 9.775 | 7.627 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -11.67 | 1.282 | 13.59 | 10.6 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | -4.091 | 1.279 | 11.16 | 8.725 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | 19.24 | 1.278 | 12.45 | 9.74 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -5.487 | 1.272 | 11.35 | 8.921 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | 0.8134 | 1.201 | 9.155 | 7.626 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | 25.99 | 1.22 | 8.488 | 6.956 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -20.93 | 1.209 | 8.154 | 6.746 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 26.98 | 1.198 | 8.631 | 7.204 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -11.66 | 1.222 | 8.297 | 6.791 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | -4.012 | 1.186 | 8.678 | 7.314 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | 19.37 | 1.237 | 8.678 | 7.018 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -5.498 | 1.206 | 7.629 | 6.326 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | 0.7908 | 1.754 | 13.88 | 7.91 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | 25.95 | 1.731 | 13.73 | 7.933 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -20.75 | 1.765 | 13.45 | 7.618 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 27.07 | 1.761 | 13.07 | 7.418 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -11.7 | 1.748 | 13.26 | 7.585 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | -3.989 | 1.731 | 14.26 | 8.239 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | 19.24 | 1.765 | 15.35 | 8.698 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -5.559 | 1.75 | 13.64 | 7.791 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | 0.8607 | 1.84 | 14.73 | 8.007 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | 26.04 | 1.842 | 14.11 | 7.664 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -20.88 | 1.844 | 14.16 | 7.681 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 26.86 | 1.838 | 14.54 | 7.911 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -11.73 | 1.834 | 15.35 | 8.37 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | -4.003 | 1.802 | 13.11 | 7.277 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | 19.32 | 1.836 | 13.54 | 7.374 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -5.461 | 1.829 | 14.64 | 8.004 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | 0.83 | 1.748 | 13.59 | 7.776 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | 26.01 | 1.751 | 13.54 | 7.735 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -20.74 | 1.775 | 13.21 | 7.44 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 26.99 | 1.752 | 13.21 | 7.539 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -11.71 | 1.754 | 12.49 | 7.121 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | -4.084 | 1.752 | 13.4 | 7.65 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | 19.23 | 1.757 | 14.45 | 8.223 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -5.488 | 1.763 | 13.02 | 7.386 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | 0.8353 | 1.75 | 14.02 | 8.009 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | 26.08 | 1.76 | 14.88 | 8.452 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -20.81 | 1.743 | 15.35 | 8.81 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 27.05 | 1.734 | 14.78 | 8.527 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -11.71 | 1.735 | 12.87 | 7.419 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | -3.962 | 1.763 | 13.73 | 7.79 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | 19.21 | 1.752 | 14.35 | 8.194 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -5.573 | 1.762 | 14.88 | 8.443 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | 0.8216 | 1.78 | 14.16 | 7.956 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | 25.98 | 1.784 | 14.54 | 8.154 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -20.73 | 1.752 | 14.21 | 8.109 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 27 | 1.781 | 14.59 | 8.191 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -11.67 | 1.748 | 15.12 | 8.648 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | -4.012 | 1.764 | 14.16 | 8.028 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | 19.19 | 1.75 | 15.97 | 9.13 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -5.529 | 1.767 | 13.69 | 7.747 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | 0.707 | 1.696 | 12.21 | 7.197 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | 26.09 | 1.701 | 12.3 | 7.231 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -20.68 | 1.695 | 12.68 | 7.484 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 27.11 | 1.699 | 12.11 | 7.127 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -11.64 | 1.677 | 11.68 | 6.967 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | -3.866 | 1.673 | 11.68 | 6.981 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | 19.24 | 1.735 | 13.11 | 7.558 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -5.581 | 1.671 | 11.83 | 7.079 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | 0.7062 | 0.6607 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | 26.93 | 0.6304 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -21.32 | 0.6286 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | 26.84 | 0.6461 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -11.31 | 0.6334 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -4.686 | 0.6268 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | 19.69 | 0.6291 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -5.46 | 0.6478 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | 0.8028 | 0.6361 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | 27.13 | 0.6584 |  |  | amplitude 1.9998 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -21.39 | 0.636 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | 26.95 | 0.6572 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -11.24 | 0.6255 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -4.61 | 0.6359 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | 19.68 | 0.6415 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -5.455 | 0.6191 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | 0.6412 | 1.253 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | 27.06 | 1.237 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -21.41 | 1.248 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | 26.91 | 1.227 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -11.21 | 1.258 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -4.568 | 1.242 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | 19.64 | 1.246 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -5.5 | 1.244 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | 0.7265 | 1.232 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | 27.04 | 1.238 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -21.42 | 1.243 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | 26.99 | 1.237 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -11.3 | 1.233 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -4.645 | 1.25 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | 19.7 | 1.26 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -5.552 | 1.263 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | 0.7195 | 1.77 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | 27.16 | 1.747 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -21.44 | 1.739 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | 26.92 | 1.728 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -11.31 | 1.752 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -4.535 | 1.745 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | 19.69 | 1.744 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -5.427 | 1.751 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | 0.7701 | 1.734 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | 26.98 | 1.74 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -21.36 | 1.741 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | 27.03 | 1.744 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -11.25 | 1.758 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -4.616 | 1.725 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | 19.7 | 1.746 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -5.401 | 1.742 |  |  | amplitude 2.0000 mV (+0.0 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.647e+06 | 46.82 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.647e+06 | 45.18 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 8.25e+05 | 44.69 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 8.25e+05 | 44.88 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.647e+06 | 45.12 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.647e+06 | 46.24 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 1.647e+06 | 43.93 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 1.647e+06 | 44.58 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.647e+06 | 44.87 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.647e+06 | 44.62 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 8.25e+05 | 43.83 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 8.25e+05 | 45.58 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.647e+06 | 44.3 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.647e+06 | 45.08 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 1.647e+06 | 43.26 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 1.647e+06 | 45.09 |  |  | (AVDD+AVSS)/2 -0.20 % |
