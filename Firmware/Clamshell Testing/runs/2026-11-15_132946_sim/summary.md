# ADS1298 clamshell validation — summary

Run: 2026-11-15_132946_sim · simulator (faulty, 5× speed) · 4 captures

| Exp | Experiment | Verdict | Headline |
|---|---|---|---|
| P | Prerequisites & data integrity | ✕ FAIL | 0/4 captures trustworthy |

## P · Prerequisites & data integrity — FAIL

Prove the data path is trustworthy before measuring noise: device ID, register readback, exact frame and DRDY counts, valid status words, no interleaved zeros, correct sample rate.

- **PASS** ID register = 0x92 (expected 0x92)
- **FAIL** 500 SPS · all 8 · test signal: register readback mismatch: CH8SET: wrote 0x05, read 0x0D
- **FAIL** 500 SPS · all 8 · test signal: 744 frames with an invalid status word (misaligned / zero frames)
- **FAIL** 2000 SPS · all 8 · test signal: register readback mismatch: CH8SET: wrote 0x05, read 0x0D
- **FAIL** 2000 SPS · all 8 · test signal: 3027 frames with an invalid status word (misaligned / zero frames)
- **FAIL** 4000 SPS · all 8 · test signal: register readback mismatch: CH8SET: wrote 0x05, read 0x0D
- **FAIL** 4000 SPS · all 8 · test signal: 45 conversions missed (SPI/UART could not keep up)
- **FAIL** 4000 SPS · all 8 · test signal: 6061 frames with an invalid status word (misaligned / zero frames)
- **FAIL** power cycle 1 · 500 SPS: register readback mismatch: CH8SET: wrote 0x05, read 0x0D
- **FAIL** power cycle 1 · 500 SPS: 507 frames with an invalid status word (misaligned / zero frames)
- **FAIL** 4 of 4 captures in this run failed integrity checks.

## Results log (clamshell_validation.md §13)

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes |
|---|---|---|---|---|---|---|---|---|---|
