# ADS1298 Clamshell Validation Plan

A set of bench experiments that use the ADS1298's **internal** test features to tell how much
noise the converter and the board add, before any electrodes or external front end are involved.

Firmware lives in [Firmware/ADS1298_clamshell_test/](Firmware/ADS1298_clamshell_test/).
Plotting helper: [plot_waveform.py](Firmware/ADS1298_clamshell_test/src/plot_waveform.py).

> **Datasheet references** are to the TI *ADS129x Low-Power, 8-Channel, 24-Bit Analog Front-End
> for Biopotential Measurements* datasheet (literature number **SBAS459**). Section names are given
> rather than page numbers because they change between revisions. Check numbers against the
> revision you have.

---

## Contents

0. [Background: input-referred vs output-referred noise](#0-background-input-referred-vs-output-referred-noise)
1. [Prerequisites: make the data trustworthy](#1-prerequisites-make-the-data-trustworthy)
2. [Experiment A: shorted-input noise floor](#2-experiment-a--shorted-input-noise-floor)
3. [Experiment B: noise spectrum (PSD)](#3-experiment-b--noise-spectrum-psd)
4. [Experiment C: gain sweep](#4-experiment-c--gain-sweep-separating-pga-vs-adc-noise)
5. [Experiment D: data-rate sweep](#5-experiment-d--data-rate-sweep)
6. [Experiment E: multichannel correlation](#6-experiment-e--multichannel-correlation)
7. [Experiment F: aggressor toggling](#7-experiment-f--aggressor-toggling-esp32-usb-power)
8. [Experiment G: internal test signal](#8-experiment-g--internal-test-signal)
9. [Experiment H: supply measurement (MVDD)](#9-experiment-h--supply-measurement-mvdd)
10. [Experiment I: temperature and long-term drift](#10-experiment-i--temperature-and-long-term-drift)
11. [Experiment J: shorting at the connector (front end)](#11-experiment-j--shorting-at-the-connector-front-end)
12. [What these tests cannot tell you](#12-what-these-tests-cannot-tell-you)
13. [Results log template](#13-results-log-template)
14. [References](#14-references)

---

## 0. Background: input-referred vs output-referred noise

Each ADS1298 channel is a chain of two noisy blocks:

```
 electrode ──► [ PGA, gain G ] ──► [ ΔΣ modulator + digital filter ] ──► 24-bit code
               adds e_PGA          adds e_ADC (incl. reference noise,
               (at its input)      quantization, coupled digital noise)
```

Noise enters at different points in the chain, so there are two ways to describe the same noise:

| Term | Where it is measured | Units | Meaning |
|---|---|---|---|
| **Output-referred** | At the ADC, *after* the gain | volts at the modulator input, or LSB/codes | "How much the digital number jitters." |
| **Input-referred** | Moved back to the *input pins* by dividing by the gain | µV at the electrodes | "How big a signal at the input would cause this much jitter." Compare this directly against your sEMG signal. |

Dividing by gain is just a change of reference point:

```
v_noise,input-referred = v_noise,output-referred / G
```

Because the two blocks are independent, their noise powers add (they combine as root-sum-square,
RSS):

```
output-referred:   v_out² = G²·e_PGA² + e_ADC²
input-referred:    v_in²  = e_PGA²   + (e_ADC / G)²
```

**Why this matters:**

- At **low gain**, the `e_ADC / G` term dominates. ADC and reference noise are divided by only a
  small G, so input-referred noise is high.
- At **high gain**, the ADC noise is divided down and the PGA noise sets the floor.
- An sEMG signal at the skin is tens of µV to a few mV, so **input-referred µV** is the figure that
  sets your SNR.

**In this codebase:** `codeToVolts(code, vref, gain)` in
[main.cpp](Firmware/ADS1298_clamshell_test/src/internal_wg_test/main.cpp) divides by `gain`, so
**its output is already input-referred**. The raw `int32_t` code is output-referred, in LSBs.

One LSB, input-referred (datasheet, *Data Format* section: positive full scale is `VREF / G`
over 2²³ codes):

```
LSB_in = VREF / (G · (2²³ − 1))
       = 2.4 V / (6 · 8 388 607) ≈ 47.7 nV   (G = 6)
```

In practice the noise is many LSBs wide, so with a 24-bit ΔΣ converter quantization is never the
limit. The analog noise is (Kester, MT-004).

**RMS vs peak-to-peak.** Datasheets quote both. For Gaussian noise, about 99.9 % of samples fall
within **≈ 6.6 × RMS** peak-to-peak (Kester, MT-001/MT-004). If your measured pp/rms ratio is much
larger than ~6–7, the noise has spikes or interference in it and is not purely random.

---

## 1. Prerequisites: make the data trustworthy

Noise statistics are meaningless if samples are corrupted or misconfigured. Check all of these
first.

### 1.1 Known issues in the current `internal_wg_test` sketch

| Issue | Evidence | Fix / check |
|---|---|---|
| Interleaved exact `0.000000` samples | Example output at the bottom of `main.cpp` | A real ADC sample is never exactly 0 every other sample. Suspect an extra read per DRDY, a read starting while DRDY is high, or a frame read that collides with the next conversion. In RDATAC mode the frame must be fully read before the next DRDY falls (datasheet, *RDATAC: Read Data Continuous*). Check DRDY and CS on a scope. |
| Test-signal amplitude ≈ 0.35 mVpp instead of ≈ 2 mVpp | Same output | With `TEST_AMP = 0` the signal is `±(VREFP − VREFN)/2.4 mV` = ±1 mV (datasheet, *CONFIG2* register description). The ≈ 1/6 ratio suggests a gain or scaling mismatch. Compare the printed `CH1SET` value with what was written. |
| `CONFIG1 = 0x06` is commented "HR mode, 500 SPS" | Datasheet *CONFIG1* register: bit 7 = HR, bit 6 = DAISY_EN (0 = daisy-chain), DR[2:0] | `0x06` is **low-power mode, 250 SPS**. Use `0x86` for HR 500 SPS, `0x83` for HR 4 kSPS. |
| Serial printing floats per sample | `Serial.println(float, 6)` | Too slow at high rates, and it rounds the data. For noise work, log **raw int32 codes**, ideally as binary. |

### 1.2 SPI budget

One RDATAC frame = 3 status bytes + 8 × 3 channel bytes = **216 bits**.

| Data rate | Period | Min SCLK (216 bits / period) | Recommendation |
|---|---|---|---|
| 500 SPS | 2 ms | 108 kHz | 500 kHz OK |
| 4 kSPS | 250 µs | 864 kHz | ≥ 4 MHz |

- Maximum SCLK is 20 MHz for DVDD 2.7–3.6 V (datasheet, *Timing Requirements*, t_SCLK).
- Multi-byte commands (RREG/WREG) need **t_SDECODE = 4 t_CLK ≈ 1.96 µs** between bytes at
  f_CLK = 2.048 MHz (datasheet, *SPI Command Definitions*). At 500 kHz a byte already takes 16 µs,
  so this is met automatically. At ≥ 4 MHz, add a delay between bytes or use a slower
  `SPISettings` for register access.

### 1.3 Sanity checks before every capture

1. Read back the `ID` register. Expect the ADS1298 device ID (datasheet, *ID: ID Control
   Register*).
2. Read back every register you wrote and confirm it matches.
3. Count DRDY pulses for 10 s and confirm the expected sample rate (e.g. 500 SPS → 5000 ± 1).
4. Monitor the **status word** (first 24 bits of each frame). Its top nibble must be `1100`
   (datasheet, *Data Output Protocol*). Any frame without it is misaligned: discard it and count
   it.
5. Wait ≥ 150 ms after enabling the internal reference (datasheet, *Internal Reference* wake-up
   time). Also discard the first few samples after any register change or START. The sinc³
   digital filter needs a few conversions to settle (datasheet, *Digital Filter* / *Settling
   Time*).

### 1.4 Logging recommendation

- Stream raw codes (int32, all 8 channels + status) over USB CDC, preferably as binary.
- Capture **≥ 10 s** per condition (≥ 5000 samples at 500 SPS). This gives stable RMS estimates
  and enough frequency resolution (0.1 Hz) to resolve mains harmonics.
- Name files by condition: `shorted_G6_HR500_wifiOff_usb.bin`.

Starter analysis (Python, NumPy/SciPy):

```python
import numpy as np
from scipy.signal import welch

VREF = 2.4
def codes_to_uV_input(codes, gain):
    return codes * VREF / (gain * (2**23 - 1)) * 1e6

x = codes_to_uV_input(codes_ch1, gain=6)
x = x - x.mean()                      # remove offset
rms = x.std()
pp  = x.max() - x.min()
print(f"{rms:.3f} uVrms, {pp:.3f} uVpp, pp/rms = {pp/rms:.1f}")

f, psd = welch(x, fs=500, nperseg=2048)  # uV^2/Hz (Welch, 1967)
asd = np.sqrt(psd)                       # uV/sqrt(Hz)
```

---

## 2. Experiment A: shorted-input noise floor

**Goal:** measure the intrinsic noise of the ADS1298 as mounted on your board. Every other result
is compared against this baseline.

**Setup**
- CHnSET MUX = `001` (input shorted), all channels powered up (`PDn = 0`). Datasheet, *CHnSET*:
  "input shorted (for offset or noise measurements)".
- CONFIG1 = HR mode, 500 SPS (`0x86`). Gain 6.
- Internal reference on (CONFIG3 = `0xC0`).

**Procedure**
1. Configure, settle, and discard the first ~50 samples.
2. Capture 10 s on all channels.
3. For each channel: subtract the mean, then compute input-referred µVrms, µVpp and the pp/rms
   ratio.
4. Record the **mean** separately. It is the channel **offset** (datasheet, *Offset error*).

**Reference values**
- Datasheet headline: **4 µVpp input-referred, 150 Hz bandwidth, G = 6** (front-page features
  list). The *Noise Measurements* section has full tables of µVrms/µVpp versus gain and data rate
  for HR and LP modes. Those were measured with the inputs **internally shorted**, which is
  exactly this experiment.
- Note that 500 SPS gives a −3 dB bandwidth of ≈ 0.262 × f_DR ≈ 131 Hz (datasheet, *Digital
  Filter*). This is close to the datasheet's 150 Hz condition but not identical.

**Interpretation**

| Result | Meaning |
|---|---|
| Within ~1.0–1.5× the datasheet table | The chip is performing as designed, and the board isn't adding noise inside the chip's bandwidth. |
| Clearly above the table, PSD white | Wideband noise from the supplies, reference decoupling or ground is getting in. Check AVDD/AVSS and VREFP decoupling (datasheet, *Power Supply Recommendations* and *Layout Guidelines*). |
| pp/rms ≫ 6.6 | Spikes or bursts rather than random noise. Usually digital coupling (WiFi TX, USB, SPI activity). Go to Experiment F. |
| Large offset differences between channels | Normal to some extent (datasheet, *Offset error*). Remove in software, or calibrate with a shorted-input capture. |

---

## 3. Experiment B: noise spectrum (PSD)

**Goal:** find *what kind* of noise is present. Experiment A only tells you how much.

**Procedure:** take the Experiment A capture and compute the Welch power spectral density (Welch,
1967), using a Hann window and ≥ 8 averaged segments. Plot the amplitude spectral density
(µV/√Hz) on a log-log scale. Heinzel et al. (2002) explain the difference between PSD and power
spectrum and the scaling conventions.

**How to read it**

| Feature | Likely cause |
|---|---|
| Flat floor | White noise of the PGA and modulator. This is the floor you can't remove. |
| Rising as 1/f below a few Hz | Flicker (1/f) noise of the input stage (Kester, MT-048). It matters for sEMG only if you keep content below ~10–20 Hz, which a typical 20 Hz high-pass removes (De Luca et al., 2010). |
| Sharp line at 50 or 60 Hz plus harmonics | Mains coupling. With an *internally shorted* input it can't come in through the electrodes, so it is entering via the supply, ground or reference. |
| Line at 1 kHz or aliases of it | USB full-speed start-of-frame traffic every 1 ms (USB 2.0 spec). Visible only if the data rate is above 2 kHz, otherwise it aliases. |
| Bursts or lines at odd frequencies | ESP32 activity (WiFi beacons, BLE advertising, task tick) or the regulator switching frequency aliased down. Confirm with Experiment F. |

**Aliasing:** anything above f_DR/2 that isn't fully rejected by the sinc³ filter folds down
into the band. The sinc³ filter has nulls at multiples of f_DR, but between the nulls it rejects
only partially (datasheet, *Digital Filter* frequency response figure). A line that moves when
you change the data rate (Experiment D) is an alias.

---

## 4. Experiment C: gain sweep (separating PGA vs ADC noise)

**Goal:** find out which block dominates the noise, using the model in
[Section 0](#0-background-input-referred-vs-output-referred-noise).

**Procedure:** repeat Experiment A at G = 1, 2, 3, 4, 6, 8 and 12 (CHnSET bits 6:4). Record
input-referred µVrms at each gain.

**Interpretation**
- Plot **input-referred noise vs G**. It should fall as G increases and then flatten out.
  - The flat level is `e_PGA`.
  - The low-gain rise is `e_ADC / G`.
- Fit `v_in² = e_PGA² + (e_ADC/G)²` to get both numbers.
- If the input-referred noise **doesn't fall** with gain, most of the noise enters *before or at*
  the PGA input, or it is common to all channels via the supply.
- If the **output-referred** noise (in LSBs) is constant across gain, noise after the PGA
  dominates: reference, modulator or digital coupling.
- **Choosing a gain for sEMG:** use the lowest G at which input-referred noise is near its floor.
  Higher gain cuts headroom (input range = ±VREF/G) for motion artifacts and electrode DC offset,
  which can reach hundreds of mV (Merletti & Parker, 2004).

---

## 5. Experiment D: data-rate sweep

**Goal:** check that noise behaves as white noise, and find aliased interference.

**Procedure:** repeat Experiment A at G = 6 for each HR data rate: 500 SPS, 1k, 2k, 4k, 8k
(CONFIG1 DR[2:0] = 110 → 010). Check the SPI budget in Section 1.2 first.

**Interpretation**
- White noise in RMS scales with √(bandwidth). Doubling f_DR should raise µVrms by about **√2**.
  The datasheet noise tables show this trend.
- Rising **faster** than √2 per doubling: interference is entering at high frequency.
- A spectral line that **moves** when f_DR changes is an alias of something above Nyquist.
- A line that **stays fixed** is real, in-band interference.
- To compare spectra fairly across rates, use µV/√Hz, not µVrms. The floor in µV/√Hz should
  overlap between rates.

---

## 6. Experiment E: multichannel correlation

**Goal:** separate noise that belongs to each channel from noise that **all channels share**. The
shared part comes from the reference, supply or ground.

**Procedure:** in shorted mode with all 8 channels on, capture 10 s. Then:
1. Compute the 8×8 **Pearson correlation matrix** of the mean-removed signals.
2. Compute the **channel average** `x̄ = mean(ch1..ch8)` and its RMS.
3. Compute the **cross-spectral coherence** between channel pairs
   (`scipy.signal.coherence`).

**Interpretation**

| Result | Meaning |
|---|---|
| Off-diagonal correlations ≈ 0 (\|r\| < ~0.05) | Noise is independent per channel. That's the ideal case. |
| RMS(x̄) ≈ σ/√8 | Confirms independence: averaging N independent sources cuts RMS by √N. |
| Strong positive correlation, RMS(x̄) ≈ σ | Shared noise: reference (VREFP) noise, the AVDD/AVSS supplies, or a ground return. Improve reference and supply decoupling and the layout (Ott, 2009). |
| High coherence at specific frequencies only | A specific shared interferer at that frequency (mains, regulator, ESP32). |

Shared noise is the most dangerous kind for sEMG. Differential or bipolar processing between
channels can't remove it if it differs slightly between channels, and it looks like a real
synchronous signal.

---

## 7. Experiment F: aggressor toggling (ESP32, USB, power)

**Goal:** find which system activity is coupling into the ADC.

**Procedure:** repeat Experiment A (and B), changing one thing at a time:

| Condition | Variants |
|---|---|
| ESP32 radio | WiFi/BLE off → idle connected → continuous TX (e.g. streaming) |
| Power source | USB from laptop on mains → laptop on battery → battery pack / isolated supply |
| USB | Streaming over USB CDC vs logging to RAM and dumping afterwards |
| SPI clock | 500 kHz vs 4 MHz vs 8 MHz |
| CPU load | Idle loop vs busy loop |

**Interpretation**
- Any condition that raises the floor, adds lines or increases pp/rms is a coupling path to fix.
  Fixes include layout, filtering, timing SPI reads away from conversions, or ferrites
  (Ott, 2009).
- If the noise is lower **on battery**, mains-referenced ground loops through the PC are getting
  in. This matters for safety and noise in the final design, which should be isolated.
- If faster SCLK raises noise, SPI edges are coupling into the analog side. Keep the slower
  clock, or add series termination resistors on SCLK/DOUT.

---

## 8. Experiment G: internal test signal

**Goal:** check gain, offset, timing and **reference noise**. The shorted input can't reveal
reference noise.

**Setup:** MUX = `101` (test signal). CONFIG2 sets the signal (datasheet, *CONFIG2*):
- `INT_TEST = 1` (internal source).
- `TEST_AMP = 0` → ±(VREFP−VREFN)/2.4 mV = **±1 mV**; `TEST_AMP = 1` → ±2 mV.
- `TEST_FREQ = 00` → f_CLK/2²¹ ≈ **0.98 Hz**; `01` → f_CLK/2²⁰ ≈ **1.95 Hz**; `11` → DC.

**Procedure**
1. Capture ≥ 20 periods of the square wave.
2. Split the samples into the high and low plateaus (threshold at the midpoint; drop ~5 samples
   after each edge for filter settling).
3. Compute:
   - **Amplitude** = mean(high) − mean(low). Expect ≈ 2 mV (TEST_AMP = 0), input-referred.
   - **Midpoint** = (mean(high) + mean(low)) / 2 → offset.
   - **Plateau noise** = std(high), std(low).
   - **Period** from the edge times. Expect 1/1.953 Hz = 512 ms.
4. Repeat with `TEST_FREQ = 11` (DC) at both amplitudes. This gives a clean, long capture for
   noise at a non-zero input.

**Interpretation**

| Result | Meaning |
|---|---|
| Amplitude ≈ 2.000 mV (within a few %) | Gain path and scaling are correct. Expect tolerance from the reference error and the test-signal accuracy, which TI doesn't specify tightly. Treat this as a functional check, not a calibration. |
| Amplitude off by a factor of G | `codeToVolts` gain doesn't match the CHnSET gain. |
| Plateau noise ≈ shorted noise | Reference noise is negligible at this signal level. |
| Plateau noise > shorted noise and growing with amplitude | **Reference noise**. Its output is proportional to the input (`code ∝ V_in / V_REF`), so it scales with signal size and disappears at 0 V. Improve VREFP decoupling (datasheet, *Internal Reference* recommended capacitors). |
| Period wrong, or jitter in edge positions | Lost or duplicated samples. Points back to the Section 1 issues. |
| Overshoot or ringing at edges | Expected sinc³ settling of about 3 conversions (datasheet, *Settling Time*). Longer tails suggest an issue. |

---

## 9. Experiment H: supply measurement (MVDD)

**Goal:** measure the ADS1298's own supply rails and their ripple, using the chip itself.

**Setup:** MUX = `011` (MVDD) and **gain = 1** so the PGA doesn't saturate (datasheet, *Supply
Measurements (MVDDP, MVDDN)*). Per the datasheet, channels 1, 2 and 5–8 measure
**(AVDD + AVSS)/2**, and channels 3 and 4 measure **DVDD/4**. Confirm against your revision.

**Procedure**
1. Capture 10 s and compute the mean (DC rail value) and the RMS and spectrum of the ripple.
2. Repeat under the Experiment F aggressor conditions, especially WiFi TX.

**Interpretation**
- The mean should match the expected rail (e.g. 3.3 V AVDD → 1.65 V reading).
- Ripple lines in the MVDD spectrum that **also** appear in the shorted-input spectrum show the
  supply as the coupling path. Compare their amplitudes to estimate the effective power-supply
  rejection (datasheet, *PSRR*).
- Dips that line up with WiFi TX bursts mean the regulator or decoupling isn't holding the rail
  under load steps.

---

## 10. Experiment I: temperature and long-term drift

**Goal:** see how offset and noise change over warm-up and over minutes. This matters for long
sEMG sessions.

**Setup:** one channel on MUX = `100` (temperature sensor). Datasheet, *Temperature Sensor*:

```
Temperature (°C) = (V_reading(µV) − 145 300 µV) / 490 µV/°C + 25 °C
```

Keep the other channels in shorted mode.

**Procedure**
1. Power on from cold and log for 30–60 min.
2. Track the temperature and the per-channel shorted-input **mean** (offset) over time.
3. Compute the **Allan deviation** of the shorted-input data (Allan, 1966).

**Interpretation**
- Offset following temperature gives the offset drift. Compare with the datasheet's *Offset
  drift* specification.
- Allan deviation:
  - Falling with slope −½ means white noise, so averaging helps.
  - Flat means flicker noise.
  - Rising means drift or random walk.
  - The minimum gives the longest useful averaging time.
- sEMG is high-pass filtered at ~20 Hz (De Luca et al., 2010), so slow drift mostly matters for
  headroom, not for the signal itself.

---

## 11. Experiment J: shorting at the connector (front end)

This step goes beyond internal testing, but it's needed to finish the picture.

**Goal:** measure the noise added by **your** front end: input RC filters, protection resistors,
connectors and traces.

**Procedure:** set MUX = `000` (normal input) and short each channel's IN+ and IN− **at the
electrode connector** with the external network in place. Also tie the pair to the bias/RLD
reference so the inputs stay in their common-mode range (datasheet, *Input Common-Mode Range*).
Repeat Experiments A and B.

**Interpretation**
- Front-end noise ≈ √(v_connector² − v_internal²), using input-referred RMS values.
- Compare it against the **thermal (Johnson) noise** of the series resistors (Johnson, 1928;
  Nyquist, 1928):

  ```
  e_n = √(4 k T R · Δf)
  ```

  For example, 10 kΩ at 300 K is 12.9 nV/√Hz, or ≈ 0.27 µVrms over 450 Hz. Two such resistors
  (one per input) add as RSS.
- Much more noise than the resistor thermal noise points to pickup on the input traces or
  connector, or leakage. Investigate layout and shielding.
- Mains now appearing (and absent in internal-short mode) is coupling into the input wiring.
  The RLD loop and CMRR deal with this (TI SBAA188).

---

## 12. What these tests cannot tell you

| Not covered | Why | How to test |
|---|---|---|
| Electrode–skin noise and impedance | Inputs are shorted internally | Real electrodes, or electrode-impedance phantoms |
| CMRR with real electrode impedance mismatch | Needs a common-mode signal and unbalanced source impedances | Common-mode sine injection through mismatched resistors (TI SBAA188) |
| Motion artifacts | Mechanical/electrochemical effects | Subject testing (De Luca et al., 2010) |
| Absolute gain accuracy | The internal test-signal amplitude isn't a precision reference | Precision external source (the `external_wg_test` sketch) |
| Linearity / THD | Square wave only | External low-distortion sine plus FFT |

---

## 13. Results log template

| Exp | Condition | Gain | Mode/Rate | Ch | Offset (µV) | Noise (µVrms) | Noise (µVpp) | pp/rms | Notes / spectral lines |
|---|---|---|---|---|---|---|---|---|---|
| A | shorted, WiFi off, USB | 6 | HR 500 | 1 | | | | | |
| A | shorted, WiFi off, USB | 6 | HR 500 | 2 | | | | | |
| … | | | | | | | | | |

Datasheet comparison value for each row: *Noise Measurements* tables (SBAS459).

---

## 14. References

**Datasheets and application notes**

1. Texas Instruments, *ADS129x Low-Power, 8-Channel, 24-Bit Analog Front-End for Biopotential
   Measurements*, datasheet **SBAS459**. Sections used: Features; Electrical Characteristics;
   Timing Requirements; Noise Measurements; Digital Filter; Settling Time; Data Format; Data
   Output Protocol; SPI Command Definitions (RDATAC, RREG/WREG, t_SDECODE); Register Map (ID,
   CONFIG1–4, CHnSET); Internal Reference; Supply Measurements; Temperature Sensor; Input
   Common-Mode Range; Power Supply Recommendations; Layout Guidelines.
   https://www.ti.com/product/ADS1298
2. Texas Instruments, *ADS1298ECG-FE / ADS1198ECG-FE Demonstration Kit User's Guide*, **SBAU171**.
   Reference bench noise-measurement procedure and layout.
3. Texas Instruments, *Improving Common-Mode Rejection Using the Right-Leg Drive Amplifier*,
   application report **SBAA188**.
4. W. Kester, *MT-001: Taking the Mystery out of the Infamous Formula "SNR = 6.02N + 1.76 dB"*,
   Analog Devices tutorial.
5. W. Kester, *MT-004: The Good, the Bad, and the Ugly Aspects of ADC Input Noise—Is No Noise Good
   Noise?*, Analog Devices tutorial. Covers input-referred noise, code-transition noise and
   RMS-to-pp ratios.
6. W. Kester, *MT-048: Op Amp Noise Relationships: 1/f Noise, RMS Noise, and Equivalent Noise
   Bandwidth*, Analog Devices tutorial.

**Books**

7. A. Kay, *Operational Amplifier Noise: Techniques and Tips for Analyzing and Reducing Noise*,
   Newnes/Elsevier, 2012. Covers input/output-referred noise, RSS addition and noise-vs-gain
   analysis.
8. H. W. Ott, *Electromagnetic Compatibility Engineering*, Wiley, 2009. Covers grounding,
   decoupling and digital-to-analog coupling.
9. R. Merletti and P. A. Parker (eds.), *Electromyography: Physiology, Engineering, and
   Noninvasive Applications*, Wiley-IEEE Press, 2004.

**Papers**

10. P. D. Welch, "The use of fast Fourier transform for the estimation of power spectra: A method
    based on time averaging over short, modified periodograms," *IEEE Trans. Audio
    Electroacoustics*, vol. 15, no. 2, pp. 70–73, 1967.
11. G. Heinzel, A. Rüdiger, R. Schilling, "Spectrum and spectral density estimation by the
    Discrete Fourier transform (DFT), including a comprehensive list of window functions and some
    new flat-top windows," Max-Planck-Institut für Gravitationsphysik, technical report, 2002.
12. D. W. Allan, "Statistics of atomic frequency standards," *Proc. IEEE*, vol. 54, no. 2,
    pp. 221–230, 1966.
13. J. B. Johnson, "Thermal agitation of electricity in conductors," *Phys. Rev.*, vol. 32,
    pp. 97–109, 1928; H. Nyquist, "Thermal agitation of electric charge in conductors,"
    *Phys. Rev.*, vol. 32, pp. 110–113, 1928.
14. C. J. De Luca, L. D. Gilmore, M. Kuznetsov, S. H. Roy, "Filtering the surface EMG signal:
    Movement artifact and baseline noise contamination," *J. Biomechanics*, vol. 43, no. 8,
    pp. 1573–1579, 2010.
