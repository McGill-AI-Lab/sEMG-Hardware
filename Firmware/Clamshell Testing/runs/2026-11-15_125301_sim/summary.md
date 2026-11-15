# ADS1298 clamshell validation — summary

Run: 2026-11-15_125301_sim · simulator (clean, 5× speed) · 112 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✓ PASS | 112/112 captures trustworthy |
| A | Shorted-input noise floor | ✓ PASS | 500 SPS: median 0.636 µVrms; 2000 SPS: median 1.24 µVrms; 4000 SPS: median 1.74 µVrms |
| B | Noise spectrum (PSD) | ✓ PASS | floor ≈ 38 nV/√Hz, 0 spectra with lines |
| C | Gain sweep (PGA vs ADC noise) | ✓ PASS | 500 SPS: e_PGA ≈ 0.588 µVrms, e_ADC ≈ 1.59 µVrms; suggested gain G6 |
| D | Data-rate sweep | ✓ PASS | RMS grows with rate^0.48 (white noise = 0.50). |
| E | Multichannel correlation | ✓ PASS | 500 SPS: max |r| = 0.073, channel-average ratio 1.04 (1 = independent, 2.83 = fully shared) |
| F | Aggressor toggling (ESP32, USB, SPI) | ! WARN | 1 of 19 variants affect the noise |
| G | Internal test signal | ✓ PASS | median amplitude 2.0000 mV vs 2.000 mV expected (+0.0 %) |
| H | Supply measurement (MVDD) | ✓ PASS | WiFi off: (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45.2 µVrms |
| I | Temperature & long-term drift | ✓ PASS | temperature 29.94 → 29.95 °C over 19 s (range 29.94–29.95 °C) |

## P · Prerequisites & data integrity — PASS

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **PASS** All 112 captures passed the integrity checks.

## A · Shorted-input noise floor — PASS

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **PASS** 500 SPS: median 0.636 µVrms, 1.12× expected (worst 1.21×)
- **PASS** 2000 SPS: median 1.24 µVrms, 1.10× expected (worst 1.13×)
- **PASS** 4000 SPS: median 1.74 µVrms, 1.09× expected (worst 1.10×)

## B · Noise spectrum (PSD) — PASS

Find what KIND of noise is present: flat white floor, 1/f rise, mains lines, USB or ESP32 lines.

- **PASS** No spectral lines above the threshold: the floor is clean.

## C · Gain sweep (PGA vs ADC noise) — PASS

Find which block dominates the noise. Input-referred noise should fall with gain and flatten out: the flat level is the PGA noise, the low-gain rise is ADC noise divided by the gain.

- **INFO** 500 SPS: e_PGA ≈ 0.588 µVrms, e_ADC ≈ 1.59 µVrms; suggested gain G6
- **INFO** 2000 SPS: e_PGA ≈ 1.12 µVrms, e_ADC ≈ 3.18 µVrms; suggested gain G4
- **INFO** 4000 SPS: e_PGA ≈ 1.59 µVrms, e_ADC ≈ 4.47 µVrms; suggested gain G4

## D · Data-rate sweep — PASS

Check that the noise behaves as white noise (RMS grows as √bandwidth, ×√2 per doubling) and separate real in-band lines (fixed frequency) from aliases (move when the rate changes).

- **PASS** RMS grows with rate^0.48 (white noise = 0.50).

## E · Multichannel correlation — PASS

Separate noise that belongs to each channel from noise that all channels share (reference, supply, ground). Shared noise looks like a real synchronous signal and is the most dangerous kind for sEMG.

- **PASS** 500 SPS: max |r| = 0.073, channel-average ratio 1.04 (1 = independent, 2.83 = fully shared)
- **PASS** 2000 SPS: max |r| = 0.037, channel-average ratio 1.04 (1 = independent, 2.83 = fully shared)
- **PASS** 4000 SPS: max |r| = 0.047, channel-average ratio 1.03 (1 = independent, 2.83 = fully shared)

## F · Aggressor toggling (ESP32, USB, SPI) — WARN

Find which system activity couples into the ADC by changing one thing at a time against a baseline.

- **WARN** 500 SPS, WiFi scanning (continuous TX): noise +5.9 %, pp/rms 12

## G · Internal test signal — PASS

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **PASS** median amplitude 2.0000 mV vs 2.000 mV expected (+0.0 %)
- **PASS** Gain cross-check: amplitude spread across gains 1.000× (1.00 ideal); log-log slope vs gain +0.00
- **PASS** Noise on DC test levels is close to the shorted noise: reference noise negligible.

## H · Supply measurement (MVDD) — PASS

Measure the ADS1298's own supply rails and their ripple using the chip itself.

- **PASS** WiFi off: (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45.2 µVrms
- **PASS** WiFi scanning (TX): (AVDD+AVSS)/2 = 1.647 V, DVDD/4 = 0.825 V, ripple ≈ 45.2 µVrms

## I · Temperature & long-term drift — PASS

See how offset and noise change during warm-up and over minutes; find the longest useful averaging time.

- **PASS** temperature 29.94 → 29.95 °C over 19 s (range 29.94–29.95 °C)
- **INFO** longest useful averaging time ≈ 4.98 s (median over channels)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | 0.7706 | 0.6313 | 3.91 | 6.194 | PASS |
| A | shorted, each | 6 | HR 500 | 2 | 26.88 | 0.6835 | 4.578 | 6.697 | PASS |
| A | shorted, each | 6 | HR 500 | 3 | -21.2 | 0.6343 | 4.578 | 7.217 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 26.97 | 0.6353 | 4.053 | 6.38 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | -11.37 | 0.6399 | 4.435 | 6.93 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | -4.426 | 0.6483 | 4.911 | 7.575 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | 19.56 | 0.6039 | 3.91 | 6.474 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -5.538 | 0.6335 | 4.053 | 6.398 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | 0.6668 | 0.6419 | 4.292 | 6.686 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | 26.63 | 0.6468 | 4.435 | 6.856 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -21.16 | 0.6327 | 3.767 | 5.953 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 26.87 | 0.6373 | 4.387 | 6.884 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -11.39 | 0.6561 | 4.911 | 7.485 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | -4.367 | 0.619 | 4.148 | 6.702 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | 19.49 | 0.6212 | 3.815 | 6.141 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -5.407 | 0.6528 | 3.91 | 5.99 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | 0.7559 | 1.251 | 9.966 | 7.969 | PASS |
| A | shorted, each | 6 | HR 2000 | 2 | 26.61 | 1.256 | 9.012 | 7.173 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -21.07 | 1.243 | 9.871 | 7.941 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 26.91 | 1.217 | 8.631 | 7.089 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | -11.42 | 1.226 | 8.917 | 7.273 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | -4.288 | 1.23 | 8.917 | 7.251 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | 19.37 | 1.238 | 9.68 | 7.817 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -5.484 | 1.213 | 9.203 | 7.586 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | 0.8979 | 1.247 | 8.774 | 7.034 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | 26.41 | 1.253 | 8.678 | 6.928 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -21.03 | 1.249 | 9.918 | 7.938 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 27.01 | 1.244 | 8.965 | 7.209 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -11.46 | 1.23 | 9.727 | 7.907 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | -4.256 | 1.238 | 9.251 | 7.473 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | 19.54 | 1.265 | 9.06 | 7.16 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -5.459 | 1.283 | 9.775 | 7.621 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | 0.7569 | 1.736 | 13.21 | 7.608 | PASS |
| A | shorted, each | 6 | HR 4000 | 2 | 26.4 | 1.749 | 14.54 | 8.314 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -20.93 | 1.737 | 13.35 | 7.688 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 26.94 | 1.733 | 13.16 | 7.595 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | -11.6 | 1.747 | 13.59 | 7.781 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | -4.155 | 1.739 | 13.73 | 7.896 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | 19.41 | 1.731 | 13.78 | 7.959 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -5.536 | 1.748 | 13.4 | 7.665 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | 0.7388 | 1.752 | 12.68 | 7.241 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | 26.36 | 1.755 | 13.64 | 7.771 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -20.86 | 1.743 | 13.49 | 7.744 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 26.99 | 1.762 | 12.68 | 7.2 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -11.74 | 1.74 | 14.16 | 8.14 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | -4.087 | 1.74 | 13.3 | 7.647 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | 19.37 | 1.738 | 13.21 | 7.6 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -5.611 | 1.733 | 12.97 | 7.486 | PASS |
| C | shorted, gain sweep | 1 | HR 500 | 1 |  | 1.644 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 1 |  | 0.9897 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 1 |  | 0.7986 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 1 |  | 0.6901 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 1 |  | 0.6176 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 1 |  | 0.595 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 1 |  | 0.5932 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 2 |  | 1.72 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 2 |  | 0.988 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 2 |  | 0.812 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 2 |  | 0.7183 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 2 |  | 0.6522 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 2 |  | 0.6039 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 2 |  | 0.5876 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 3 |  | 1.685 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 3 |  | 1.023 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 3 |  | 0.7917 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 3 |  | 0.6968 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 3 |  | 0.6384 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 3 |  | 0.6225 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 3 |  | 0.5952 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 4 |  | 1.696 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 4 |  | 1.001 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 4 |  | 0.7952 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 4 |  | 0.7204 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 4 |  | 0.6469 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 4 |  | 0.6444 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 4 |  | 0.5975 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 5 |  | 1.643 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 5 |  | 0.9985 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 5 |  | 0.7998 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 5 |  | 0.7044 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 5 |  | 0.6557 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 5 |  | 0.6046 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 5 |  | 0.6116 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 6 |  | 1.706 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 6 |  | 0.9701 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 6 |  | 0.7758 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 6 |  | 0.7031 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 6 |  | 0.6567 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 6 |  | 0.6229 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 6 |  | 0.5772 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 7 |  | 1.698 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 7 |  | 0.9907 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 7 |  | 0.7692 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 7 |  | 0.7043 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 7 |  | 0.652 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 7 |  | 0.6278 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 7 |  | 0.5842 |  |  |  |
| C | shorted, gain sweep | 1 | HR 500 | 8 |  | 1.657 |  |  |  |
| C | shorted, gain sweep | 2 | HR 500 | 8 |  | 0.986 |  |  |  |
| C | shorted, gain sweep | 3 | HR 500 | 8 |  | 0.7882 |  |  |  |
| C | shorted, gain sweep | 4 | HR 500 | 8 |  | 0.7283 |  |  |  |
| C | shorted, gain sweep | 6 | HR 500 | 8 |  | 0.6498 |  |  |  |
| C | shorted, gain sweep | 8 | HR 500 | 8 |  | 0.6037 |  |  |  |
| C | shorted, gain sweep | 12 | HR 500 | 8 |  | 0.5841 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 1 |  | 3.379 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 1 |  | 1.931 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 1 |  | 1.56 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 1 |  | 1.383 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 1 |  | 1.281 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 1 |  | 1.2 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 1 |  | 1.167 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 2 |  | 3.418 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 2 |  | 1.962 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 2 |  | 1.526 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 2 |  | 1.382 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 2 |  | 1.241 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 2 |  | 1.188 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 2 |  | 1.155 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 3 |  | 3.38 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 3 |  | 1.933 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 3 |  | 1.551 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 3 |  | 1.369 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 3 |  | 1.24 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 3 |  | 1.176 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 3 |  | 1.151 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 4 |  | 3.348 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 4 |  | 1.944 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 4 |  | 1.54 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 4 |  | 1.368 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 4 |  | 1.267 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 4 |  | 1.207 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 4 |  | 1.169 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 5 |  | 3.37 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 5 |  | 1.938 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 5 |  | 1.537 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 5 |  | 1.376 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 5 |  | 1.25 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 5 |  | 1.189 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 5 |  | 1.165 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 6 |  | 3.369 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 6 |  | 1.944 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 6 |  | 1.533 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 6 |  | 1.356 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 6 |  | 1.23 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 6 |  | 1.204 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 6 |  | 1.15 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 7 |  | 3.376 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 7 |  | 1.945 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 7 |  | 1.543 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 7 |  | 1.387 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 7 |  | 1.242 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 7 |  | 1.176 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 7 |  | 1.17 |  |  |  |
| C | shorted, gain sweep | 1 | HR 2000 | 8 |  | 3.357 |  |  |  |
| C | shorted, gain sweep | 2 | HR 2000 | 8 |  | 1.955 |  |  |  |
| C | shorted, gain sweep | 3 | HR 2000 | 8 |  | 1.545 |  |  |  |
| C | shorted, gain sweep | 4 | HR 2000 | 8 |  | 1.367 |  |  |  |
| C | shorted, gain sweep | 6 | HR 2000 | 8 |  | 1.24 |  |  |  |
| C | shorted, gain sweep | 8 | HR 2000 | 8 |  | 1.191 |  |  |  |
| C | shorted, gain sweep | 12 | HR 2000 | 8 |  | 1.162 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 1 |  | 4.728 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 1 |  | 2.753 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 1 |  | 2.196 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 1 |  | 1.95 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 1 |  | 1.739 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 1 |  | 1.668 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 1 |  | 1.619 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 2 |  | 4.755 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 2 |  | 2.738 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 2 |  | 2.172 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 2 |  | 1.957 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 2 |  | 1.752 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 2 |  | 1.688 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 2 |  | 1.634 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 3 |  | 4.763 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 3 |  | 2.74 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 3 |  | 2.181 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 3 |  | 1.924 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 3 |  | 1.753 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 3 |  | 1.684 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 3 |  | 1.622 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 4 |  | 4.763 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 4 |  | 2.726 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 4 |  | 2.173 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 4 |  | 1.948 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 4 |  | 1.747 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 4 |  | 1.684 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 4 |  | 1.633 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 5 |  | 4.697 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 5 |  | 2.706 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 5 |  | 2.19 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 5 |  | 1.945 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 5 |  | 1.745 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 5 |  | 1.678 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 5 |  | 1.619 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 6 |  | 4.741 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 6 |  | 2.751 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 6 |  | 2.169 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 6 |  | 1.956 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 6 |  | 1.754 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 6 |  | 1.674 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 6 |  | 1.631 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 7 |  | 4.799 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 7 |  | 2.722 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 7 |  | 2.178 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 7 |  | 1.917 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 7 |  | 1.768 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 7 |  | 1.684 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 7 |  | 1.609 |  |  |  |
| C | shorted, gain sweep | 1 | HR 4000 | 8 |  | 4.711 |  |  |  |
| C | shorted, gain sweep | 2 | HR 4000 | 8 |  | 2.762 |  |  |  |
| C | shorted, gain sweep | 3 | HR 4000 | 8 |  | 2.191 |  |  |  |
| C | shorted, gain sweep | 4 | HR 4000 | 8 |  | 1.927 |  |  |  |
| C | shorted, gain sweep | 6 | HR 4000 | 8 |  | 1.733 |  |  |  |
| C | shorted, gain sweep | 8 | HR 4000 | 8 |  | 1.68 |  |  |  |
| C | shorted, gain sweep | 12 | HR 4000 | 8 |  | 1.617 |  |  |  |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 1 | 0.8731 | 0.6401 | 4.387 | 6.853 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 2 | 26.04 | 0.6676 | 4.625 | 6.928 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 3 | -20.91 | 0.6324 | 4.053 | 6.41 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 4 | 27.01 | 0.6391 | 4.387 | 6.864 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 5 | -11.77 | 0.6281 | 5.15 | 8.199 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 6 | -4.036 | 0.6456 | 4.101 | 6.352 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 7 | 19.28 | 0.6323 | 4.244 | 6.712 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 500 | 8 | -5.538 | 0.661 | 4.244 | 6.42 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 1 | 0.8421 | 0.6296 | 4.148 | 6.589 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 2 | 26.01 | 0.6462 | 4.482 | 6.936 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 3 | -20.79 | 0.6316 | 4.387 | 6.946 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 4 | 27.07 | 0.6641 | 4.387 | 6.606 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 5 | -11.6 | 0.6283 | 4.482 | 7.134 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 6 | -4.004 | 0.6613 | 4.768 | 7.211 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 7 | 19.17 | 0.6446 | 4.673 | 7.25 | PASS |
| F | SPI 500 kHz | 6 | HR 500 | 8 | -5.494 | 0.657 | 4.482 | 6.822 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 1 | 0.8302 | 0.6801 | 4.053 | 5.959 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 2 | 26.08 | 0.6786 | 4.721 | 6.956 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 3 | -20.78 | 0.6806 | 4.673 | 6.866 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 4 | 27.01 | 0.6644 | 4.101 | 6.172 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 5 | -11.69 | 0.6918 | 4.673 | 6.755 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 6 | -4.044 | 0.6731 | 4.244 | 6.305 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 7 | 19.24 | 0.6376 | 4.435 | 6.955 | PASS |
| F | SPI 8 MHz | 6 | HR 500 | 8 | -5.573 | 0.6768 | 4.578 | 6.763 | PASS |
| F | CPU busy | 6 | HR 500 | 1 | 0.8693 | 0.6946 | 4.578 | 6.59 | PASS |
| F | CPU busy | 6 | HR 500 | 2 | 26.08 | 0.641 | 4.244 | 6.62 | PASS |
| F | CPU busy | 6 | HR 500 | 3 | -20.78 | 0.6408 | 4.339 | 6.772 | PASS |
| F | CPU busy | 6 | HR 500 | 4 | 27.03 | 0.6442 | 3.958 | 6.144 | PASS |
| F | CPU busy | 6 | HR 500 | 5 | -11.64 | 0.6331 | 4.864 | 7.683 | PASS |
| F | CPU busy | 6 | HR 500 | 6 | -3.985 | 0.6327 | 4.911 | 7.763 | PASS |
| F | CPU busy | 6 | HR 500 | 7 | 19.28 | 0.6389 | 5.15 | 8.061 | PASS |
| F | CPU busy | 6 | HR 500 | 8 | -5.499 | 0.6446 | 4.292 | 6.658 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 1 | 0.8808 | 0.633 | 4.578 | 7.232 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 2 | 26.03 | 0.6409 | 4.816 | 7.514 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 3 | -20.68 | 0.6478 | 4.435 | 6.846 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 4 | 27.09 | 0.6504 | 4.196 | 6.452 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 5 | -11.69 | 0.6452 | 4.625 | 7.169 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 6 | -3.933 | 0.6592 | 4.482 | 6.8 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 7 | 19.3 | 0.6438 | 4.196 | 6.517 | PASS |
| F | WiFi access point (beacons) | 6 | HR 500 | 8 | -5.573 | 0.6571 | 4.387 | 6.676 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 1 | 0.7999 | 0.7112 | 7.582 | 10.66 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 2 | 26.03 | 0.7049 | 6.199 | 8.794 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 3 | -20.84 | 0.6908 | 8.583 | 12.43 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 4 | 27 | 0.6783 | 6.723 | 9.912 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 5 | -11.52 | 0.6746 | 5.77 | 8.553 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 6 | -3.996 | 0.6543 | 6.104 | 9.328 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 7 | 19.21 | 0.6611 | 5.579 | 8.439 | WARN |
| F | WiFi scanning (continuous TX) | 6 | HR 500 | 8 | -5.48 | 0.6737 | 6.676 | 9.909 | WARN |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 1 | 0.7783 | 0.5989 | 3.29 | 5.493 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 2 | 26.15 | 0.5843 | 3.481 | 5.957 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 3 | -20.81 | 0.6281 | 3.529 | 5.618 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 4 | 26.98 | 0.563 | 3.386 | 6.014 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 5 | -11.75 | 0.6193 | 3.624 | 5.852 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 6 | -3.967 | 0.6281 | 3.767 | 5.998 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 7 | 18.97 | 0.6212 | 3.815 | 6.141 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 500 | 8 | -5.545 | 0.6131 | 3.147 | 5.134 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 1 | 0.8306 | 1.246 | 9.108 | 7.309 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 2 | 26.04 | 1.251 | 8.821 | 7.049 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 3 | -20.8 | 1.266 | 9.346 | 7.385 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 4 | 27.09 | 1.236 | 9.584 | 7.757 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 5 | -11.73 | 1.25 | 8.726 | 6.982 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 6 | -3.906 | 1.223 | 9.346 | 7.64 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 7 | 19.14 | 1.235 | 9.298 | 7.53 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 2000 | 8 | -5.501 | 1.253 | 8.678 | 6.926 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 1 | 0.813 | 1.305 | 9.251 | 7.089 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 2 | 26.05 | 1.311 | 9.251 | 7.056 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 3 | -20.76 | 1.318 | 9.775 | 7.415 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 4 | 27.08 | 1.313 | 9.203 | 7.01 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 5 | -11.55 | 1.308 | 10.11 | 7.729 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 6 | -3.985 | 1.308 | 9.203 | 7.035 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 7 | 19.28 | 1.304 | 9.727 | 7.457 | PASS |
| F | SPI 8 MHz | 6 | HR 2000 | 8 | -5.539 | 1.306 | 9.966 | 7.633 | PASS |
| F | CPU busy | 6 | HR 2000 | 1 | 0.9959 | 1.244 | 8.869 | 7.132 | PASS |
| F | CPU busy | 6 | HR 2000 | 2 | 25.95 | 1.246 | 8.488 | 6.809 | PASS |
| F | CPU busy | 6 | HR 2000 | 3 | -20.89 | 1.249 | 10.3 | 8.246 | PASS |
| F | CPU busy | 6 | HR 2000 | 4 | 27.03 | 1.253 | 9.537 | 7.61 | PASS |
| F | CPU busy | 6 | HR 2000 | 5 | -11.61 | 1.255 | 10.44 | 8.323 | PASS |
| F | CPU busy | 6 | HR 2000 | 6 | -3.884 | 1.23 | 8.535 | 6.94 | PASS |
| F | CPU busy | 6 | HR 2000 | 7 | 19.24 | 1.251 | 9.489 | 7.587 | PASS |
| F | CPU busy | 6 | HR 2000 | 8 | -5.568 | 1.257 | 9.108 | 7.245 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 1 | 0.9153 | 1.233 | 8.726 | 7.079 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 2 | 25.97 | 1.244 | 8.631 | 6.938 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 3 | -20.76 | 1.222 | 8.44 | 6.906 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 4 | 26.92 | 1.263 | 11.4 | 9.021 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 5 | -11.67 | 1.248 | 9.727 | 7.795 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 6 | -4.08 | 1.239 | 9.632 | 7.776 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 7 | 19.21 | 1.247 | 9.251 | 7.418 | PASS |
| F | WiFi access point (beacons) | 6 | HR 2000 | 8 | -5.567 | 1.253 | 8.965 | 7.152 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 1 | 0.8231 | 1.268 | 11.4 | 8.986 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 2 | 26.04 | 1.269 | 10.78 | 8.49 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 3 | -20.86 | 1.265 | 11.78 | 9.314 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 4 | 26.95 | 1.263 | 10.11 | 8.003 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 5 | -11.6 | 1.26 | 9.823 | 7.799 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 6 | -3.954 | 1.265 | 10.3 | 8.14 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 7 | 19.28 | 1.271 | 10.82 | 8.518 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 2000 | 8 | -5.578 | 1.263 | 10.3 | 8.157 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 1 | 0.8422 | 1.171 | 7.677 | 6.556 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 2 | 25.95 | 1.181 | 8.631 | 7.308 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 3 | -20.72 | 1.256 | 9.68 | 7.708 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 4 | 27.1 | 1.235 | 7.677 | 6.217 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 5 | -11.87 | 1.2 | 7.296 | 6.079 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 6 | -4.046 | 1.195 | 8.202 | 6.861 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 7 | 19.33 | 1.187 | 7.915 | 6.666 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 2000 | 8 | -5.535 | 1.181 | 8.774 | 7.426 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 1 | 0.8838 | 1.748 | 14.21 | 8.131 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 2 | 26.08 | 1.765 | 13.59 | 7.701 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 3 | -20.82 | 1.75 | 12.54 | 7.165 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 4 | 27 | 1.744 | 14.07 | 8.065 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 5 | -11.72 | 1.745 | 12.78 | 7.322 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 6 | -3.885 | 1.76 | 13.54 | 7.695 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 7 | 19.21 | 1.764 | 13.88 | 7.866 | PASS |
| F | baseline (WiFi off, idle, 4 MHz, streaming) | 6 | HR 4000 | 8 | -5.539 | 1.758 | 16.26 | 9.249 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 1 | 0.8823 | 1.849 | 16.31 | 8.822 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 2 | 25.93 | 1.829 | 13.64 | 7.456 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 3 | -20.87 | 1.829 | 14.02 | 7.666 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 4 | 27 | 1.834 | 13.69 | 7.461 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 5 | -11.7 | 1.834 | 14.73 | 8.032 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 6 | -3.994 | 1.837 | 13.83 | 7.529 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 7 | 19.17 | 1.821 | 13.11 | 7.2 | PASS |
| F | SPI 8 MHz | 6 | HR 4000 | 8 | -5.553 | 1.815 | 14.69 | 8.092 | PASS |
| F | CPU busy | 6 | HR 4000 | 1 | 0.8484 | 1.752 | 13.73 | 7.839 | PASS |
| F | CPU busy | 6 | HR 4000 | 2 | 26 | 1.766 | 13.02 | 7.37 | PASS |
| F | CPU busy | 6 | HR 4000 | 3 | -20.85 | 1.753 | 13.69 | 7.809 | PASS |
| F | CPU busy | 6 | HR 4000 | 4 | 26.97 | 1.739 | 13.92 | 8.006 | PASS |
| F | CPU busy | 6 | HR 4000 | 5 | -11.62 | 1.758 | 13.59 | 7.732 | PASS |
| F | CPU busy | 6 | HR 4000 | 6 | -4.007 | 1.758 | 14.69 | 8.354 | PASS |
| F | CPU busy | 6 | HR 4000 | 7 | 19.27 | 1.77 | 15.83 | 8.943 | PASS |
| F | CPU busy | 6 | HR 4000 | 8 | -5.566 | 1.741 | 13.78 | 7.915 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 1 | 0.9096 | 1.744 | 12.16 | 6.972 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 2 | 26.02 | 1.748 | 14.45 | 8.265 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 3 | -20.77 | 1.752 | 14.02 | 8.003 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 4 | 26.88 | 1.745 | 13.02 | 7.462 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 5 | -11.68 | 1.747 | 13.54 | 7.752 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 6 | -3.834 | 1.752 | 15.45 | 8.819 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 7 | 19.12 | 1.759 | 15.02 | 8.54 | PASS |
| F | WiFi access point (beacons) | 6 | HR 4000 | 8 | -5.513 | 1.744 | 13.02 | 7.465 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 1 | 0.7046 | 1.764 | 14.78 | 8.382 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 2 | 25.91 | 1.777 | 15.54 | 8.746 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 3 | -20.82 | 1.774 | 14.5 | 8.173 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 4 | 26.95 | 1.773 | 14.21 | 8.014 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 5 | -11.7 | 1.787 | 14.78 | 8.271 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 6 | -4.053 | 1.766 | 13.78 | 7.805 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 7 | 19.18 | 1.788 | 13.97 | 7.814 | PASS |
| F | WiFi scanning (continuous TX) | 6 | HR 4000 | 8 | -5.645 | 1.781 | 15.59 | 8.754 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 1 | 0.7583 | 1.676 | 11.73 | 6.997 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 2 | 25.87 | 1.694 | 12.06 | 7.123 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 3 | -20.56 | 1.683 | 12.11 | 7.197 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 4 | 27.08 | 1.721 | 11.78 | 6.843 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 5 | -11.49 | 1.687 | 12.59 | 7.464 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 6 | -3.997 | 1.702 | 12.49 | 7.341 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 7 | 19.27 | 1.719 | 12.4 | 7.212 | PASS |
| F | USB quiet (buffered in RAM) | 6 | HR 4000 | 8 | -5.504 | 1.708 | 13.02 | 7.621 | PASS |
| G | test 2 Hz, each | 6 | HR 500 | 1 | 0.6999 | 0.6369 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | 26.99 | 0.6331 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 3 | -21.38 | 0.629 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | 26.96 | 0.6842 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -11.31 | 0.6349 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -4.652 | 0.6389 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | 19.62 | 0.6263 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -5.45 | 0.6286 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | 0.7016 | 0.6203 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | 27.04 | 0.6524 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -21.26 | 0.6339 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | 26.94 | 0.6398 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -11.25 | 0.6466 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -4.546 | 0.6447 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | 19.71 | 0.6465 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -5.413 | 0.6384 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | 0.7253 | 1.246 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | 27.04 | 1.217 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -21.38 | 1.23 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | 26.93 | 1.253 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -11.37 | 1.231 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -4.634 | 1.253 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | 19.61 | 1.246 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -5.52 | 1.244 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 1 | 0.6634 | 1.273 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 2 | 26.98 | 1.229 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 3 | -21.32 | 1.234 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 4 | 26.91 | 1.249 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 5 | -11.33 | 1.236 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 6 | -4.62 | 1.233 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 7 | 19.64 | 1.239 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 2000 | 8 | -5.499 | 1.232 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 1 | 0.7205 | 1.768 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 2 | 27.16 | 1.746 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 3 | -21.45 | 1.741 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 4 | 26.93 | 1.728 |  |  | amplitude 2.0001 mV (+0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 5 | -11.3 | 1.747 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 6 | -4.529 | 1.748 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 7 | 19.7 | 1.757 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, each | 6 | HR 4000 | 8 | -5.41 | 1.754 |  |  | amplitude 2.0000 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 1 | 0.7602 | 1.748 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 2 | 27.05 | 1.736 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 3 | -21.37 | 1.719 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 4 | 27 | 1.738 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 5 | -11.33 | 1.741 |  |  | amplitude 1.9999 mV (-0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 6 | -4.553 | 1.758 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 7 | 19.66 | 1.744 |  |  | amplitude 2.0000 mV (+0.0 %) |
| G | test 2 Hz, all | 6 | HR 4000 | 8 | -5.419 | 1.752 |  |  | amplitude 2.0000 mV (+0.0 %) |
| H | MVDD WiFi off | 1 | HR 500 | 1 | 1.647e+06 | 47.12 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 2 | 1.647e+06 | 44.51 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 3 | 8.25e+05 | 44.9 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 4 | 8.25e+05 | 46.15 |  |  | DVDD/4 +0.00 % |
| H | MVDD WiFi off | 1 | HR 500 | 5 | 1.647e+06 | 44.47 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 6 | 1.647e+06 | 46.33 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 7 | 1.647e+06 | 45.23 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi off | 1 | HR 500 | 8 | 1.647e+06 | 45.22 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 1 | 1.647e+06 | 45.3 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 2 | 1.647e+06 | 46.14 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 3 | 8.25e+05 | 45.21 |  |  | DVDD/4 +0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 4 | 8.25e+05 | 45.25 |  |  | DVDD/4 -0.00 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 5 | 1.647e+06 | 46.2 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 6 | 1.647e+06 | 46.3 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 7 | 1.647e+06 | 44.55 |  |  | (AVDD+AVSS)/2 -0.20 % |
| H | MVDD WiFi scanning (TX) | 1 | HR 500 | 8 | 1.647e+06 | 45.22 |  |  | (AVDD+AVSS)/2 -0.20 % |
