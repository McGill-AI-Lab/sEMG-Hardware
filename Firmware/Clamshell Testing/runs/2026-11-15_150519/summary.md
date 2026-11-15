# ADS1298 clamshell validation — summary

Run: 2026-11-15_150519 · hardware on /dev/cu.usbserial-1140 · 18 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| G | Internal test signal | ✕ FAIL | median amplitude 1.5452 mV vs 2.000 mV expected (-22.7 %) |

## G · Internal test signal — FAIL

Check gain, scaling, offset, timing and reference noise with the chip's own square wave. Also tests the known 'amplitude ≈ 1/6 of expected' problem with a gain cross-check.

- **FAIL** median amplitude 1.5452 mV vs 2.000 mV expected (-22.7 %)

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
| G | test 2 Hz, each | 6 | HR 500 | 3 | -1571 | 5.424 |  |  | amplitude 1.5443 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 1 | -1550 | 9.138 |  |  | amplitude 1.5573 mV (-22.1 %) |
| G | test 2 Hz, each | 6 | HR 500 | 2 | -1529 | 3.752 |  |  | amplitude 1.5446 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 5 | -1342 | 2.131 |  |  | amplitude 1.5453 mV (-22.7 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 6 | -1326 | 1.235 |  |  | amplitude 1.5440 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 7 | -1523 | 1.17 |  |  | amplitude 1.5439 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 4 | -1412 | 5.42 |  |  | amplitude 1.5445 mV (-22.8 %) |
| G | test 2 Hz, each | 6 | HR 500 | 8 | -1782 | 1.149 |  |  | amplitude 1.5421 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 8 | -1781 | 1.125 |  |  | amplitude 1.5425 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 4 | -1407 | 1.19 |  |  | amplitude 1.5451 mV (-22.7 %) |
| G | test 2 Hz, each | 6 | HR 500 | 7 | -1526 | 4.409 |  |  | amplitude 1.5431 mV (-22.8 %) |
| G | test 2 Hz, all | 6 | HR 500 | 1 | -2182 | 1573 |  |  | amplitude 3.0728 mV (+53.6 %) |
| G | test 2 Hz, all | 6 | HR 500 | 2 | -2527 | 1632 |  |  | amplitude 2.9580 mV (+47.9 %) |
| G | test 2 Hz, all | 6 | HR 500 | 3 | -3484 | 785.8 |  |  | amplitude 2.2696 mV (+13.5 %) |
| G | test 2 Hz, all | 6 | HR 500 | 4 | -3329 | 786.4 |  |  | amplitude 2.2602 mV (+13.0 %) |
| G | test 2 Hz, all | 6 | HR 500 | 5 | -2940 | 1355 |  |  | amplitude 3.1331 mV (+56.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 6 | -2734 | 1361 |  |  | amplitude 3.0942 mV (+54.7 %) |
| G | test 2 Hz, all | 6 | HR 500 | 7 | -3409 | 995.2 |  |  | amplitude 2.3094 mV (+15.5 %) |
| G | test 2 Hz, all | 6 | HR 500 | 8 | -3679 | 791.6 |  |  | amplitude 2.2797 mV (+14.0 %) |
| G | test 2 Hz, each | 6 | HR 500 | 6 | -1350 | 10.98 |  |  | amplitude 1.5408 mV (-23.0 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 5 | -1325 | 1.421 |  |  | amplitude 1.5482 mV (-22.6 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 2 | -1540 | 8.941 |  |  | amplitude 1.5421 mV (-22.9 %) |
| G | test 2 Hz, each | 6 | HR 500 | 1 | -1607 | 27.29 |  |  | amplitude 1.5562 mV (-22.2 %) |
| G | test 2 Hz, each | 6 | HR 2000 | 3 | -1570 | 1.134 |  |  | amplitude 1.5448 mV (-22.8 %) |
