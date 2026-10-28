# ADS1298 analog audit evidence (read-only)

Sources inspected: complete active V0 and V1 `.kicad_sch` files, including embedded symbol pin definitions; exported KiCad XML netlists and ERC. Both schematics are single-sheet: zero hierarchical sheet instances. V0 has two instances called J1, so their connector mapping is ambiguous; netlist warned annotation errors. This is an evidence limitation, not a separate excluded connector review.

Manufacturer source: [TI ADS129x datasheet, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf). Relevant sections: pin tables pp10–11; recommended/absolute ratings p12; input characteristics p13; PGA pp31–32; RLD p41; clock p50; configuration p69; application common-mode pp86–87.

## Confirmed supply evidence — A1, F1, H2 (one root fault, not three independent problems)

V0 U1 and U2 are both ADS1298xPAG symbols with identical embedded electrical pin definitions. AVDD pins19,21,22,56,59 and charge-pump AVDD1 pin54 connect to +3.3VA. +3.3VA net has ADC supplies and C18/C19/C69/C70 only: no regulator or battery source. Both regulator outputs (U4.5 and U7.5) are instead +3.3V. V0 AVSS20/23/32/57/58, AVSS1.53 and chip DGND33/49/51 are AGND, which includes BT1.2 and regulator GND2. Thus V0 provides no valid analog supply. Do not invent a numerical voltage on the floating +3.3VA net.

V1 AVDD19/21/22/56/59 and AVDD1.54 are AGND, the same net as AVSS20/23/32/57/58 and AVSS1.53: analog span is exactly 0 V by connectivity. V1 DVDD48/50 are on the separate DGND net, rather than +3.3V. Actual chip DGND33/49/51 remains AGND. U3 controller GND pins22/23/24/44 are DGND, whereas BT1.2 and regulator GND2 are AGND. V1 has no valid analog supply and introduces digital supply/ground wiring failures.

Raw-wire proof for V1 U1: symbol origin(177.8,144.78), AVDD endpoint(172.72,101.6), AVDD1 endpoint(177.8,101.6), DVDD endpoint(182.88,101.6). Each is wired up to y93.98, the capacitor return row. +3.3V capacitor top row is y86.36. U2 repeats this wiring error. Supply labels over capacitor top rows do not mean the ADC supply endpoints are on that row.

Required analog span is 2.7–5.25 V; digital span 1.65–3.6 V (TI §7.3). The internal PGA shares the invalid analog supply, so F1 is a consequence of A1, not an extra independent amplifier failure. F2 reversed supplies: NOT FOUND; a zero span is not reversal.

Simplest supported correction, not implemented: after choosing separate regulator outputs as already intended, move ADC positive supply endpoints from ground rows to appropriate positive rows; keep AVSS and actual chip DGND on battery-negative common ground. Join controller ground and digital decoupling returns to this valid ground. Do not simply merge DGND into AGND first while DVDD is still on DGND, because this would explicitly ground DVDD. Verify netlist positive/negative pin memberships and direct rail spans before operating.

## Analog inputs and common mode — F3

Both revisions: every differential electrode input has 2 kΩ series resistance and 620 pF to AGND at its ADC end. ADC pin pairs are IN1P/N16/15, IN2P/N14/13, IN3P/N12/11, IN4P/N10/9, IN5P/N8/7, IN6P/N6/5, IN7P/N4/3, IN8P/N2/1.

V0 U1 E17–E24 map V1 U1 E1–E8. V0 U1 resistor sequence is R3,R21–R35, mapping in order to V1 R1–R16. V0 U2 E1–E8 map V1 U2 E9–E16. V0 U2 R4–R19 map V1 R17–R32.

V0 U1 has R36=1 MΩ parallel C73=1.5 nF between RLDOUT63 and RLDINV61 and a reference-electrode J1 on the output. V0 U2 has R1/C1 of the same values terminating on another J1 instance, but U2 RLDOUT63 is genuinely unconnected in the active schematic; notes promising a PCB connection do not create a schematic net. Both RLDREF60 and RLDIN62 are NC in V0. V1 removes both RLD feedback networks and both reference-electrode instances; RLDOUT63/RLDINV61/RLDREF60 are NC and RLDIN62 is +3.3V. There is no DC input-bias connection shown at V1 electrodes. This does not alone prove measured electrode common-mode is outside its allowed range.

F3 classification: CANNOT VERIFY (UNKNOWN). No electrode DC common-mode, electrode offsets, source model, firmware gain, lead-off settings, or RLD selection is supplied. First correct supplies. Measure common-mode `(INP+INN)/2` and differential input during intended operation, compare to TI equation2 and ±VREF/gain. Do not add an RLD architecture solely from this check; any bias correction must follow observed/input-model requirements. Common-mode means the average voltage of a differential pair, measured relative to the chip ground.

## I4 — actual input architecture and acquisition

ADS1298 has high-impedance CMOS PGA inputs ahead of delta-sigma modulators, not a directly driven generic SAR sample-and-hold. The existing passive network does not establish an acquisition fault. Using its stated values, each external RC time constant is 2000×620 pF=1.24 µs; its simple one-pole corner is about128.4 kHz. A 1.2 nA input-bias bound through the drawn 2 kΩ alone gives2.4 µV. These are calculations of the drawn resistor, not a claim about total electrode source impedance or settled 24-bit accuracy.

I4 classification: CANNOT VERIFY (UNKNOWN) because electrode/source impedance and settling/data-rate/gain requirements are unspecified. The unchanged 2 kΩ/620 pF network is not a verified fault. Verification: provide source impedance versus frequency and programmed gain/data rate; step a representative source and observe filtered settling at selected output rate. No buffer or RC change is justified just from the schematic.

## C7/F4/F5 — stability and clipping

C7: CANNOT VERIFY for actual V0 driven-electrode load because cable/electrode impedance and enabled RLD configuration are absent. The 1.5 nF part is parallel feedback compensation, not proof of an unstable amplifier capacitive load. V1 has no external RLD/PACE output load drawn; do not assume its unused RLD amplifier is enabled.

F4: CANNOT VERIFY. No loop simulation, frequency response, transient response or oscillation measurement exists. V0 U1 RLD 1 MΩ//1.5 nF is recognizable compensated feedback but does not certify complete electrode-loop stability. V1 removes the external RLD path. Unconnected feedback on a disabled optional amplifier is not proof that an operating amplifier oscillates.

F5: CANNOT VERIFY independently of the confirmed invalid supplies. Input amplitudes, electrode DC offsets, gain/reference choices and RLD/PACE enables are absent. No separate confirmed clipping/overload is established. Obtain actual configuration and input voltages; verify ADC full scale/PGA headroom only after supply wiring is corrected.

## Other analog-input hazard directly created by supply miswire

V1 U1/U2 TEST/PACE17/18 and RLDIN62 are hard-wired to +3.3V but AVDD is AGND. When +3.3V is valid, these analog pins sit3.3 V above AVDD, exceeding the analog-pin absolute limit AVDD+0.3 V. This is a direct result of supply miswiring, not an independent RLD redesign finding. Restoring AVDD to +3.3V makes these unused-pin connections consistent with the manufacturer's AVDD tie recommendation. Before then, do not claim a damage current value: no regulator enable state, effective source impedance or clamp I–V model is given.

## Clock/reset handoff to digital audit

V0 each CLK37 is tied to CLKSEL52 on an isolated net, with no supply strap or clock driver. V1 U1 CLKSEL52 is +3.3V but CLK37 is NC. The nearby global ADC_CLK label is dangling; ERC explicitly reports this. U2 CLKSEL52 is DGND and CLK37 is ADC_CLK, whose sole connected component is U2.37. Therefore the intended U1-to-U2 clock has no electrical connection. A valid fix is U1.37 to U2.37, with firmware clock-output enable; or use independent internal oscillators only if synchronization requirements permit. This is a floating-control/no-valid-clock issue, not evidence of a slow edge.
