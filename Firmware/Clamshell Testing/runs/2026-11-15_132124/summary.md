# ADS1298 clamshell validation — summary

Run: 2026-11-15_132124 · hardware on /dev/cu.usbserial-1140 · 3 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 0/3 captures trustworthy |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 3 of 3 captures in this run failed integrity checks.

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
