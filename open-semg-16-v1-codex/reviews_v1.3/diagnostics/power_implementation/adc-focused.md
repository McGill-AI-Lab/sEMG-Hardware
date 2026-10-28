# Focused ADC supply and interface decision

27 October 2026. Read-only follow-up to the power-architecture proposal. No schematic edits. This note addresses whether the proposed 2.98 V ADC rail is justified for the intended EMG configuration, and how to preserve the existing separate-CS/shared-MISO cascade interface.

## Decision

**The ADS1298 permits an approximately 3 V supply, but the intended EMG envelope has not been specified sufficiently to verify the 2.98 V choice.** The prior reports leave gain, sample rate, electrode offsets, body bias, motion/common-mode excursion and acceptable noise unresolved (F07/F10/F11/F18). No firmware or measured input envelope was identified. Reset gain 6 is a device default, not an agreed application configuration. The existing 2/4 kSPS calculations are alternatives, not implemented firmware evidence.

This is a blocker to claiming that the reduced rail is qualified for the intended electrode configuration. It does not prohibit a clearly scoped **bench prototype with grounded dummy inputs**, initial input-short/test-signal configuration, current-limited supply and no wearer. If authorization makes implementation conditional on verifying the intended EMG envelope first, that condition has not been met; it must not be silently replaced by an assumed gain/rate.

For the least communication change, retain both ADC DVDD domains at the same regulated rail as the MCU, retain both DOUT43 connections on the current shared MISO, retain independent CS, shared ADC_CLK and shared START. A separate analog rail may be evaluated without changing the logical SPI architecture. However, direct GPIO and startup remain qualification issues, detailed below. Do not claim that the SPI topology has been measured or that the existing VOH/noise margin is already validated merely because it is manufacturer-supported.

## Actual constraints and headroom

Primary sources: [ADS1298 SBAS459K](../../../../docs/datasheets/originals/components/ADS1298.pdf), printed pp.12,16–17,31–33,48,67,69,85,96–97; [ESP32-S3-WROOM-1 v1.8](../../../../docs/datasheets/originals/components/ESP32-S3-WROOM-1.pdf), printed pp.27–28; original review §7.5 and V1.2 digital evidence.

ADS operating ranges: AVDD−AVSS = 2.7–5.25 V; DVDD = 1.65–3.6 V; AVDD−DVDD = −2.1 to +3.6 V. Thus AVDD = 2.98 V, DVDD = 3.40 V is permitted in steady state (difference −0.42 V). At the proposal's analog-low/digital-high corner, 2.9155−3.446 = −0.5305 V, still inside that range. Unpowered transient states require separate analysis; these steady-state inequalities do not qualify every rail ramp.

With AVSS = 0, Eq.2 is:

`0.2 + G × abs(VD)/2 < VCM < AVDD − 0.2 − G × abs(VD)/2`.

The 2.4 V internal reference and gain 6 give nominal differential full scale ±400 mV at either 3.3 V or 2.98 V, but do not preserve common-mode headroom:

| Maximum differential magnitude, gain 6 | At 3.30 V AVDD | At 2.98 V nominal | At 2.9155 V low corner |
|---:|---:|---:|---:|
| 300 mV | 1.10–2.20 V | 1.10–1.88 V | 1.10–1.8155 V |
| 350 mV | 1.25–2.05 V | 1.25–1.73 V | 1.25–1.6655 V |
| 400 mV | 1.40–1.90 V | 1.40–1.58 V | 1.40–1.5155 V |

Bounds are strict. At the low corner and 400 mV differential, midpoint bias is 1.45775 V and theoretical common-mode excursion is only ±57.75 mV. No supplied body-bias or electrode evidence demonstrates that condition. Lower gain could increase headroom but would be an application decision, not a power-only repair. Sample rate affects bandwidth, noise, current and timing; choosing a rate alone does not repair a violated PGA headroom bound.

Use 2.4 V internal reference; enable and settle it independently on each ADC. Retain all reference/VCAP nodes and auxiliary restrictions. No power proposal closes the missing body-bias circuit.

## Direct-GPIO comparison

ADS p.16: VIH minimum = 0.8 DVDD; VIL maximum = 0.2 DVDD; VOH minimum = DVDD−0.4 V and VOL maximum = 0.4 V at ±500 µA. The high-input row's upper bound is DVDD+0.1 V. The absolute input limit on p.12 is DVDD+0.3 V, which is a stress limit, not the normal operating target.

ESP module p.27: VIH minimum = 0.75 VDD, VIL maximum = 0.25 VDD, VOH minimum = 0.8 VDD, VOL maximum = 0.1 VDD. The footnote says VOH/VOL are measured into a high-impedance load; the table is titled 3.3 V/25 °C. Ratio-based corner calculations below are useful screens, not additional full-temperature guarantees at 3.4 V or at the existing 10 kΩ pull loads.

| Rails / direction | Table-based result | Decision |
|---|---|---|
| Common MCU/ADC DVDD = 3.30 V, MCU→ADS | 2.64−2.64 = 0 V high margin; 0.66−0.33 = 0.33 V low margin | Same-voltage operation does not inherently require translation, but these tables do not prove positive worst-case high noise margin. This pre-existing qualification risk remains. |
| Common MCU/ADC DVDD = 3.40 V, MCU→ADS | Ratio screen still gives 0 V high margin | Raising both rails does not fix the high-margin limitation. |
| Common 3.30 V, ADS→MCU | High: 2.90−2.475 = 0.425 V; low: 0.825−0.4 = 0.425 V | Positive table-bound return margins under the specified loads. |
| Common 3.40 V, ADS→MCU | Ratio screen: high 3.00−2.55 = 0.45 V; low 0.85−0.4 = 0.45 V | Return direction remains favorable; verify the actual board/temperature/edge conditions. |
| MCU 3.40 V, separate ADC DVDD 3.30 V | Nominal forward high margin = 80 mV; MCU high is already at DVDD+0.1 V normal-input upper bound | Not a robust direct-GPIO solution across independent tolerances. |
| MCU 3.40 V, ADC DVDD 2.98 V, direct return | ADS minimum VOH 2.58 V versus MCU VIH 2.55 V gives only 30 mV nominal | At the report corners, ADS minimum VOH = 2.5155 V but MCU VIH screen = 0.75×3.446 = 2.5845 V: −69 mV. Forward highs can also exceed the ADC's supply-relative input limits. Direct wiring cannot be retained for that split. |

For an independent 3.3 V DVDD with an illustrative ±1.5% accuracy and report main range 3.354–3.446 V:

- Forward minimum-high screen: `0.8×3.354 − 0.8×3.3495 = 3.6 mV`.
- A possible MCU high at 3.446 V exceeds low-DVDD normal upper bound `3.2505+0.1 = 3.3505 V` by 95.5 mV, although it remains below the absolute +0.3 V limit.

Consequently a separate 3.3 V ADC digital supply with a 3.4 V MCU is not a defensible way to avoid receiver-powered buffers. The prior shared 3.3 V direct interface did not have this independent-rail input-upper-bound problem. It did already have the zero table-bound forward high-margin concern.

A forward buffer powered by ADC DVDD can improve loaded VOH and isolate unpowered inputs while preserving separate CS/shared MISO at the logical level. It still needs a concrete startup contract. Adding a DOUT mux is not necessary for normal manufacturer-supported cascade operation; it was introduced in the previous proposal to eliminate a specific possible startup contention path, rather than to repair the normal cascade topology.

## Startup and brownout are not solved by choosing DVDD

The LT3042 proposal's large SET capacitor deliberately makes AVDD slow. If DVDD is connected directly to main, it can reach approximately 3.4 V while AVDD remains near zero. The resulting difference is outside the recommended operating range during that interval. The ADS datasheet does not specify one explicit rail-order rule or characterize every such transient, so this is an unqualified ramp state, not a proved damage event. A conservative design gates DVDD until the analog rail is ready, or uses coupled rails. Every powered GPIO and clock path must be included in that decision.

TI §11.1 calls for low inputs before and through supply stabilization. Existing START/RESET/PWDN/DIN/SCLK pulls cannot override driven MCU boot states; CS has no complete startup control. RESET/PWDN do not establish off-state input tolerance or a guaranteed DOUT-high-impedance state. Both ADC CS low can expose the physically shared DOUT net to conflicting outputs; no actual conflict waveform is established.

A simple CS pullup tracking DVDD prevents powered-input-above-DVDD injection and helps normal deselection, but departs from a literal all-inputs-low ramp. Do not call it a complete manufacturer-verified sequencing solution without a justified startup interpretation and testing or TI clarification. Conversely, holding both CS low to follow that guidance requires ensuring the shared output drivers cannot contend. Any required gates should be narrowly scoped to that startup issue; preserve the supported logical cascade and avoid redesigning frame handling without need.

Once supplies and clock are valid, wait at least 2^18 clock periods and until VCAP1>1.1 V, whichever is later; reset low at least two clocks, then wait 18 clocks. Initialize U1 internally, enable CLK_EN, then give U2 its clock-dependent wait and selected RESET command. A later shared RESET would disable U1's exported clock again. Repeat the full reference/clock initialization after a qualified rail fault; no ADS automatic brownout-recovery guarantee was identified.

## Least-change power implementation options

1. **Best match to a requirement to preserve the current direct communication wiring:** use the evaluated single regulated 3.3 V buck-boost architecture, with a separately routed, low-DC-drop analog filter branch and common MCU/ADC digital supply. This avoids deliberately reducing nominal ADC analog supply to 2.98 V and avoids a new MISO mux. Qualify filter drop/noise and startup; do not claim radio immunity or robust forward logic margin without evidence. Ferrite/RC selection must account for DCR, resonance, effective capacitors and transient loading; a filter is not a substitute for measurement.
2. **If a separately regulated quiet 2.98 V analog rail is expressly accepted for bench work:** keep ADC DVDD on the MCU rail, move only AVDD/AVDD1 plus auxiliary ties to the quiet rail, and solve the resulting startup/control paths. U1 CLKSEL must follow DVDD, not the lower analog rail. Keep both DOUT43 pins on MISO, unless a narrowly justified startup isolation change is accepted. Direct GPIO still has the forward table-margin limitation; it must not be represented as newly guaranteed.
3. **If both ADC domains use 2.98 V:** the previously proposed level-regenerated interfaces are justified by the numerical logic margins; removing them while retaining that rail split is not equivalent. A strict instruction to preserve physical shared-DOUT wiring therefore conflicts with that particular complete proposal. Resolve the architecture rather than silently dropping its necessary interface treatment.

For option 2 the exact rail reassignment is AVDD/AVDD1 pins 19/21/22/54/56/59 and auxiliaries 17/18/62 to quiet analog; DVDD48/50 and U1 CLKSEL52 remain on the MCU-compatible digital rail. U2 CLKSEL52 stays grounded. Analog banks C6/C7/C32/C33 follow analog; digital banks C8/C9/C34/C35 follow digital. Preserve AVSS/DGND/VREFN returns, VCAP/reference networks, shared CLK37/START38, CS39 assignments, DOUT43 cascade and all 32 acquisition-input paths. This pin list does not itself authorize or qualify the split.

No claim of intended EMG performance or wearer readiness follows from a bench-only implementation. The minimum missing application evidence is a bounded gain/reference/rate/input-offset/common-mode contract; the minimum power-interface evidence is an explicit boot/brownout/USB state design. These are specific unresolved conditions, not a request for another broad audit.
