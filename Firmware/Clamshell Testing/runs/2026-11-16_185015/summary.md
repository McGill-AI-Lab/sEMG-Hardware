# ADS1298 clamshell validation — summary

Run: 2026-11-16_185015 · hardware on /dev/cu.usbserial-1140 · 27 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| A | Shorted-input noise floor | ✕ FAIL | 500 SPS: median 0.62 µVrms; 2000 SPS: median 0.994 µVrms; 4000 SPS: median 1.4 µVrms |

## A · Shorted-input noise floor — FAIL

Measure the intrinsic noise of the ADS1298 as mounted on your board, with the inputs shorted inside the chip. Every other experiment is compared against this baseline.

- **FAIL** 500 SPS: median 0.62 µVrms, 1.09× expected (worst 15.06×); noisiest CH1 at 8.53 µVrms
- **WARN** 2000 SPS: median 0.994 µVrms, 0.88× expected (worst 1.23×)
- **WARN** 4000 SPS: median 1.4 µVrms, 0.88× expected (worst 1.17×)
- **WARN** 2 channel captures have a pp/rms well above what Gaussian noise gives: spikes or bursts, not pure random noise. See Experiment F (aggressors).

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, each | 6 | HR 500 | 1 | -217 | 8.528 | 48.3 | 5.664 | FAIL |
| A | shorted, each | 6 | HR 500 | 2 | -108.7 | 5.175 | 18.79 | 3.63 | FAIL |
| A | shorted, each | 6 | HR 500 | 3 | -149.9 | 0.5356 | 3.862 | 7.211 | PASS |
| A | shorted, each | 6 | HR 500 | 4 | 14.39 | 0.5092 | 3.576 | 7.023 | PASS |
| A | shorted, each | 6 | HR 500 | 5 | 67.88 | 0.6206 | 5.15 | 8.299 | PASS |
| A | shorted, each | 6 | HR 500 | 6 | 77.12 | 0.5389 | 3.767 | 6.99 | PASS |
| A | shorted, each | 6 | HR 500 | 7 | -101.5 | 0.6197 | 3.958 | 6.387 | PASS |
| A | shorted, each | 6 | HR 500 | 8 | -344.1 | 0.4885 | 3.481 | 7.126 | PASS |
| A | shorted, all | 6 | HR 500 | 1 | -103.8 | 0.6748 | 5.054 | 7.49 | PASS |
| A | shorted, all | 6 | HR 500 | 2 | -114.7 | 0.5439 | 3.91 | 7.189 | PASS |
| A | shorted, all | 6 | HR 500 | 3 | -278.9 | 0.828 | 6.008 | 7.257 | PASS |
| A | shorted, all | 6 | HR 500 | 4 | 28.45 | 0.6718 | 4.864 | 7.24 | PASS |
| A | shorted, all | 6 | HR 500 | 5 | -14.19 | 0.6292 | 4.721 | 7.502 | PASS |
| A | shorted, all | 6 | HR 500 | 6 | 165.3 | 0.6196 | 4.53 | 7.311 | PASS |
| A | shorted, all | 6 | HR 500 | 7 | -118.7 | 0.6289 | 4.53 | 7.203 | PASS |
| A | shorted, all | 6 | HR 500 | 8 | -359.2 | 0.5547 | 3.672 | 6.619 | PASS |
| A | shorted, each | 6 | HR 2000 | 1 | -191.9 | 1.088 | 12.06 | 11.09 | WARN |
| A | shorted, each | 6 | HR 2000 | 2 | -114.6 | 0.9187 | 6.914 | 7.526 | PASS |
| A | shorted, each | 6 | HR 2000 | 3 | -149.2 | 0.9192 | 7.915 | 8.611 | PASS |
| A | shorted, each | 6 | HR 2000 | 4 | 13.44 | 0.939 | 8.202 | 8.734 | PASS |
| A | shorted, each | 6 | HR 2000 | 5 | 67.8 | 0.957 | 8.106 | 8.471 | PASS |
| A | shorted, each | 6 | HR 2000 | 6 | 77.52 | 0.9371 | 7.629 | 8.142 | PASS |
| A | shorted, each | 6 | HR 2000 | 7 | -101.7 | 0.9421 | 7.534 | 7.997 | PASS |
| A | shorted, each | 6 | HR 2000 | 8 | -344.2 | 0.9497 | 7.2 | 7.582 | PASS |
| A | shorted, all | 6 | HR 2000 | 1 | -103.3 | 1.125 | 9.298 | 8.264 | PASS |
| A | shorted, all | 6 | HR 2000 | 2 | -114.8 | 1.003 | 8.345 | 8.316 | PASS |
| A | shorted, all | 6 | HR 2000 | 3 | -278.7 | 1.392 | 10.35 | 7.432 | PASS |
| A | shorted, all | 6 | HR 2000 | 4 | 28.21 | 1.113 | 8.345 | 7.498 | PASS |
| A | shorted, all | 6 | HR 2000 | 5 | -14.1 | 1.094 | 8.774 | 8.017 | PASS |
| A | shorted, all | 6 | HR 2000 | 6 | 164.9 | 1.114 | 9.108 | 8.177 | PASS |
| A | shorted, all | 6 | HR 2000 | 7 | -118.8 | 1.034 | 8.44 | 8.163 | PASS |
| A | shorted, all | 6 | HR 2000 | 8 | -358.6 | 0.9854 | 8.059 | 8.178 | PASS |
| A | shorted, each | 6 | HR 4000 | 1 | -191.5 | 1.523 | 17.45 | 11.46 | WARN |
| A | shorted, each | 6 | HR 4000 | 2 | -114.8 | 1.337 | 11.44 | 8.558 | PASS |
| A | shorted, each | 6 | HR 4000 | 3 | -149.4 | 1.367 | 10.78 | 7.884 | PASS |
| A | shorted, each | 6 | HR 4000 | 4 | 13.35 | 1.325 | 11.59 | 8.744 | PASS |
| A | shorted, each | 6 | HR 4000 | 5 | 67.32 | 1.347 | 10.78 | 8.003 | PASS |
| A | shorted, each | 6 | HR 4000 | 6 | 77.21 | 1.355 | 12.25 | 9.041 | PASS |
| A | shorted, each | 6 | HR 4000 | 7 | -101.3 | 1.333 | 11.11 | 8.337 | PASS |
| A | shorted, each | 6 | HR 4000 | 8 | -343.7 | 1.347 | 11.06 | 8.216 | PASS |
| A | shorted, all | 6 | HR 4000 | 1 | -104 | 1.605 | 12.54 | 7.812 | PASS |
| A | shorted, all | 6 | HR 4000 | 2 | -115.1 | 1.424 | 11.97 | 8.404 | PASS |
| A | shorted, all | 6 | HR 4000 | 3 | -278.1 | 1.876 | 15.59 | 8.311 | PASS |
| A | shorted, all | 6 | HR 4000 | 4 | 28.09 | 1.509 | 13.3 | 8.814 | PASS |
| A | shorted, all | 6 | HR 4000 | 5 | -14.03 | 1.513 | 12.68 | 8.382 | PASS |
| A | shorted, all | 6 | HR 4000 | 6 | 165.3 | 1.531 | 12.87 | 8.407 | PASS |
| A | shorted, all | 6 | HR 4000 | 7 | -118.4 | 1.425 | 11.01 | 7.729 | PASS |
| A | shorted, all | 6 | HR 4000 | 8 | -358.7 | 1.385 | 12.02 | 8.674 | PASS |
