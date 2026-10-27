# Independent analog audit notes — current schematic

Scope: current `open-semg-16-v1.kicad_sch` and KiCad 10 XML netlist only; no earlier revision or Amberflow checklist used to form these findings. No design changes made. Calculations below describe the nominal network; the current supply faults prevent valid acquisition. Original manufacturer PDFs were checked using the PDFKit text extracts in `reviews/diagnostics/pdf-text/`, not solely converted Markdown.

## Verified sources

- TI ADS1298 family datasheet **SBAS459K, August 2015** (`../docs/datasheets/originals/components/ADS1298.pdf`): PDF/printed pp. 10–11 TQFP pin definitions; p.12 §§7.1,7.3 limits; p.13 §7.5 input characteristics; p.14 AC performance; p.22 Tables 1–2 noise; p.26 Figure24 input protection and internal EMI filter; p.32 §§9.3.1.5.1–.3 Eq2/Eq3; p.33 §9.3.1.6 reference; pp.39–40 lead-off; pp.41–42 §9.3.1.7.6 RLD; p.49 Eq5 decimation filter; p.69 CONFIG3/Table20; p.71 CHnSET/Table22; pp.96–97 single/bipolar supplies; p.98 §12.1 layout.
- TI **SBAA188B, October 2026**, `../docs/datasheets/originals/ti-app-notes/SBAA188.pdf`: p.3 §2 common-to-differential conversion from mismatched R/C; pp.4–5 bias/protection tradeoffs; pp.5–6 RLD/disconnection.
- TI **SBAA185, May 2011**, `../docs/datasheets/originals/ti-app-notes/SBAA185.pdf`: p.3 Eq1 resistor thermal noise; pp.4–5 combining uncorrelated sources. Caution: the app note's p.5 use of single-pole noise-bandwidth factor π/2 should not be applied indiscriminately to the actual third-order sinc filter.
- TI **SBAA196A, January 2015**, `../docs/datasheets/originals/ti-app-notes/SBAA196.pdf`: p.2 undefined common mode without a DC bias point; pp.3–5 lead-off return paths, offsets/noise; p.11 frequency overlap warning for AC lead-off.

## 1. Critical analog power and overvoltage faults

For **both U1 and U2**, every AVDD pin **19,21,22,56,59** and AVDD1 pin **54** is on the same **AGND** net as every AVSS pin **20,23,32,57,58**, AVSS1 **53**, VREFN **25**, and the physical DGND pins **33,49,51**. Therefore **AVDD−AVSS=0V**, 2.7V below the recommended 2.7V minimum (§7.3,p12). This is not a grounding-style preference; the analog core has no supply voltage.

Digital supply pins **48,50** go to net **DGND**, while physical digital ground pins **33,49,51** go to **AGND**. Since AGND and DGND are distinct nets with no DC tie in the exported netlist, the digital supply voltage is **V(net DGND)−V(net AGND)** and is undefined, not demonstrably 0V. If the two grounds were bonded without correcting the supply pins, this becomes 0V, below the 1.65V minimum. Current digital rail/return connections therefore cannot support the intended behavior. The physical-ground labels must not be confused with the names of the nets.

Both ICs' **17 TESTP_PACE_OUT1**, **18 TESTN_PACE_OUT2** (symbol calls pin18 TESTP; manufacturer says TESTN), and **62 RLDIN** are hard tied **+3.3V**. If the regulator rail reaches 3.3V relative AGND, these analog pins sit 3.3V above their AVDD=AGND, exceeding the **AVDD+0.3V absolute maximum by 3.0V** (p12 §7.1), with no series current limiting. Clamp conduction/back-powering/damage is possible. Datasheet footnote p10 says unused pins17/18/62 connect to **AVDD**, which only coincides with +3.3V after an explicit power correction. These ties are not evidence that AVDD receives power. Pace output modes must remain disabled when the pins are hard tied to a rail.

Correction to propose, not implement: rebuild/verify power connections pin by pin; AVDD/AVDD1 to the selected analog supply; AVSS/AVSS1 to analog return; DVDD to the selected digital supply; DGND pins to digital return, and a deliberate valid return connection between domains. Connect actual decoupling between each supply and its return. Verify DC ohms and all IC pin voltages before placing/powering ICs, then current-limited bench supply. Recheck pin17/18/62 against actual AVDD.

**C6/C7, C32/C33** (100nF/10µF) connect +3.3V–AGND and **C8/C9,C34/C35** (100nF/10µF) +3.3V–DGND. They do not decouple the ADS1298 AVDD/DVDD pins as wired. The latter bank has a return floating relative the battery, so “capacitors exist beside the chip” does not establish effective IC decoupling.

## 2. All 16 input mappings verified

Each E symbol has two electrical terminals. E1–E8 feed U1 channels1–8; E9–E16 feed U2 channels1–8. For channel n, positive input pin is 18−2n and negative pin 17−2n. Electrode terminal1 consistently feeds P through the odd-numbered resistor; terminal2 feeds N through the even resistor. All input series resistors are 2kΩ. Every ADC-side node has a 620pF shunt capacitor to AGND. There are no cross-channel shorts or polarity swaps in these 32 nets.

| Electrode | IC/channel | P/N IC pins | P/N resistors | P/N capacitors |
|---|---|---|---|---|
| E1 | U1/1 |16/15|R1/R2|C1/C2|
| E2 | U1/2 |14/13|R3/R4|C3/C4|
| E3 | U1/3 |12/11|R5/R6|C5/C10|
| E4 | U1/4 |10/9|R7/R8|C11/C12|
| E5 | U1/5 |8/7|R9/R10|C13/C14|
| E6 | U1/6 |6/5|R11/R12|C15/C16|
| E7 | U1/7 |4/3|R13/R14|C17/C18|
| E8 | U1/8 |2/1|R15/R16|C21/C22|
| E9 | U2/1 |16/15|R17/R18|C27/C28|
| E10 | U2/2 |14/13|R19/R20|C29/C30|
| E11 | U2/3 |12/11|R21/R22|C31/C36|
| E12 | U2/4 |10/9|R23/R24|C37/C38|
| E13 | U2/5 |8/7|R25/R26|C39/C40|
| E14 | U2/6 |6/5|R27/R28|C41/C42|
| E15 | U2/7 |4/3|R29/R30|C43/C44|
| E16 | U2/8 |2/1|R31/R32|C47/C48|

The 16 symbols represent **32 acquisition contacts**; no 33rd bias/reference contact is instantiated. Electrode footprints/physical connector definitions are absent, so mechanical mapping and gold plating are not verified by this schematic.

## 3. RLD/bias absent; common-mode operating point undefined

For both ICs **RLDREF60, RLDINV61, RLDOUT63 and WCT64 have explicit no-connect markers**. RLDIN62 is +3.3V as described above. No external feedback resistor/capacitor, no driven body electrode, and no passive mid-supply body-bias electrode or per-input DC-bias resistors exist. All 32 contacts terminate through 2kΩ into ADC input pins, with capacitors providing only AC return.

There are **no two RLD drivers tied together**, and no current RLD output capacitive loading to analyze. Both amplifiers default powered down (CONFIG3 bit2=0, p69), so do not claim proven RLD oscillation. Correctly leaving optional WCT output unused is consistent with a differential sEMG architecture.

However, the intended common-mode feedback/bias function is missing. A disconnected or absent bias contact is not a grounded contact: capacitance and uncontrolled leakage do not fix the body's DC potential. ADS1298's nominal ≥1GΩ DC input impedance does not establish a chosen midpoint. With lead-off disabled (reset), input bias current, motion charge and ambient common-mode pickup can move inputs beyond the PGA common-mode range or to clamps. The exact body voltage cannot be predicted from this schematic. TI SBAA196A p2 explains this undefined-common-mode problem.

Specific recommendation: select and document either a protected passive body bias or **one** compensated RLD driver with a dedicated protected bias contact; select RLD sensing channels intentionally; keep the second amplifier powered down. Set RLDREF internally or provide its external reference. Model electrode/cable/body capacitance, large series protection resistance, disconnected electrodes, and amplifier output current/swing; demonstrate phase margin and recovery experimentally. No RLD stability or human safety conclusion can be made for a future circuit from its absence now.

Firmware must keep RLD disabled for this current topology. A channel set to RLD rerouting MUX110/111 could connect the hard-tied RLDIN rail toward a wearer contact; do not enable those modes inadvertently.

## 4. Differential offset/headroom constraints — conditional after power repair

No analog high-pass network exists. That avoids a separate pair of high-pass mismatch terms and preserves DC, but passes electrode offsets and motion artifacts directly into the PGA. Digital high-pass filtering cannot recover analog clipping.

Actual gain/reference/HR/LP settings are firmware dependent and were not supplied. **CHnSET resets to gain6**, not gain1 (p71 Table22). Internal reference buffer is **off at reset** (CONFIG3 bit7=0, p69; p33), and VREFP only has capacitors—there is no external reference source. Firmware must enable the internal reference, select2.4V for a 3.3V analog supply, wait for settling, and read registers back. This is a required firmware action, not by itself a missing hardware-reference defect. Do not select the 4V reference on a3.3V analog supply.

For assumed corrected AVDD=3.3V, AVSS=0V, internal VREF=2.4V:

- ADC differential endpoint = ±VREF/G (p32 Eq3). G1 ±2.4V; G2 ±1.2V; G3 ±0.8V; G4 ±0.6V; G6 ±0.4V; G8 ±0.3V; G12 ±0.2V. Lower-gain endpoints can be limited by PGA output/common-mode headroom before nominal ADC endpoints.
- PGA common mode (p32 Eq2): **0.2V + G|VD|max/2 < VCM < 3.1V − G|VD|max/2**. G6, |VD|max=300mV gives **1.10<VCM<2.20V**; G6,350mV gives **1.25<VCM<2.05V**; G6,400mV gives **1.40<VCM<1.90V**. A nominally valid differential voltage alone does not ensure linear conversion.
- At G6, a300mV electrode offset leaves only100mV to the nearer ±400mV endpoint for EMG plus artifacts. At G12 the same offset clips even before muscle activity. These offsets are illustrative design stresses, not measured values for the supplied dry electrodes.
- G6 LSB for2.4V ref is (2VREF/G)/2^24 = **47.68nV**. This is a code weight, not effective resolution.

Bench evidence required: record each input's common mode and maximum differential electrode DC offset, motion artifact excursions, clipped-code count/recovery, and gain/register settings. Consider gain1–4 during attachment or an offset servo only after quantifying effects. Adding a generic high-pass is not automatically the preferred correction.

## 5. Exact RC response and CMRR implications

For a negligible source impedance and high-impedance ADC, each leg has **H(s)=1/(1+sRC)**, R=2000Ω, C=620pF, τ=1.24µs, **fc=128350.76Hz**. The matched differential response is also H(s), not a cascade of two RC poles. In odd-mode analysis the two shunt caps are C/2 across the pair and the two series resistors total2R, giving the same RC time constant. There is no capacitor directly bridging P and N.

- External filter attenuation: **−0.000190dB at850Hz**; **−6.97dB at256kHz**; **−12.28dB at512kHz**.
- Thus these are EMI filters, not 850Hz anti-alias filters. ADS1298 is a buffered-PGA delta-sigma architecture with intrinsic EMI filtering (~3MHz p26) and sinc³ decimation, so a SAR sample-acquisition capacitor settling rule should not be imported uncritically. Nevertheless digital passbands repeat at fMOD multiples (p49): external filter suppression near256/512kHz and RF rectification at input need validation.
- External cap magnitude |Zc| is **5.134MΩ at50Hz,4.278MΩ at60Hz,302kΩ at850Hz** per leg. With an illustrative100kΩ resistive source per electrode, total series resistance102kΩ lowers the branch pole to2.517kHz and gives approximately−0.469dB at850Hz; at1MΩ it becomes256Hz and approximately−10.8dB. These are illustrative impedances, not supplied electrode measurements. This materially lowers AC input impedance from the IC's ≥1GΩ DC value. ADS1298's input capacitance is20pF typical (p13); exact loading is frequency dependent and the intrinsic EMI network means it should not simply be assigned to a lumped external cap for all frequencies.

For simplified resistive electrode impedances ZP,ZN, branches **HP=1/[1+jωCP(RP+ZP)]**, HN similarly. Desired differential gain is (HP+HN)/2; common-to-differential conversion is HP−HN, hence **CMRRext=20log10(|(HP+HN)/2|/|HP−HN|)**. For low ωτ and matched C, this reduces approximately to **−20log10(ωC|ΔZ|)**. Illustrative ΔZ=100kΩ gives only **32.63dB at60Hz** (34.21dB at50Hz). This is a model demonstrating vulnerability, not predicted measured wrist CMRR. Purely resistive source models omit complex electrode/contact capacitance and channel interaction through a shared body.

For ideal zero electrode impedance, ±1% resistor limits can create a40Ω pair difference and a nominal worst-case100.58dB external-filter CMRR at60Hz. ±5% capacitors can create a62pF pair difference and **86.60dB**. These are **assumed tolerance examples**, not component specifications; no actual tolerance/dielectric/MPN is provided. The device's ~115dB typical intrinsic60Hz CMRR (p14) cannot be claimed for this assembled system. A C0G capacitor selection and tight matching help component mismatch, while electrode imbalance requires separate analysis and bias/common-mode control (SBAA188B p3; ADS §12.1).

## 6. Actual acquisition bandwidth and noise

ADS1298 sinc³ response (p49 Eq5), **|H(f)|=|sin(Nπf/fMOD)/[Nsin(πf/fMOD)]|³**, N=fMOD/fDR. With nominal fCLK2.048MHz, fMOD512kHz HR /256kHz LP (p32). The numbers below are HR mode; LP response is almost identical at equal fDR with a different decimation ratio.

| fDR | −3dB bandwidth (Table1,p22) | Gain at500Hz | Gain at850Hz | Gain atNyquist |
|---|---|---|---|---|
|2kSPS|524Hz|−2.736dB|**−8.262dB**|−11.767dB|
|4kSPS|1048Hz|−0.673dB|**−1.965dB**|−11.767dB|

At2kSPS,850Hz is mathematically below Nyquist but substantially attenuated; calling20–850Hz “flat” is incorrect. 4kSPS better preserves upper EMG content, at higher noise/power/data burden. Equalization would amplify noise and cannot recover aliases. Ensure intended anti-aliasing and passband specifications are explicit.

For two uncorrelated2kΩ series resistors, at300K, **en=√[4kT(2R)] =8.1407nV/√Hz**. An ideal rectangular20–850Hz post-filter gives **√[4kT(4000Ω)(830Hz)]=0.2345µVrms**; external128kHz RC loss is negligible in this band. If each electrode's real impedance were100kΩ resistive over this entire band, its pair adds **1.658µVrms** under the same simplified model; actual complex electrodes and excess/contact noise are unknown. Bias-current offset through a100kΩ imbalance is20µV for200pA (the25°C datasheet maximum test value), but actual individual currents and their differences must be considered.

Datasheet Table1 p22 typical **shorted-input HR noise** at3V analog/2.4V ref:

| Gain |2kSPS rms|4kSPS rms|
|---|---|---|
|1|4.1µV|6.1µV|
|4|1.3µV|1.9µV|
|6|1.1µV|1.5µV|
|12|0.9µV|1.2µV|

For LP mode atG6, Table2 gives1.4µVrms at2kSPS and2.4µVrms at4kSPS. These are converter full-output-band integrated values (including internal reference in the test), not densities and not20–850Hz noise after an identical post-filter. Do not directly RSS the830Hz resistor number with these values and call it a bandwidth-consistent system noise result. The present wiring cannot achieve these performance numbers; they are conditional design benchmarks. Actual noise includes reference, supply/ground coupling, interference, electrode/contact and motion sources and needs measurement.

## 7. Lead-off is available, but unspecified and not innocuous

No firmware exists in the supplied project to establish lead-off configuration. LOFF_SENSP/N reset00 (pp74–75); unused lead-off circuitry does not automatically detect bad contacts or establish a body bias. Treat status as valid only for enabled channels. With no valid bias path, disconnected electrodes may drift, rail, or pick up environmental EMG-like interference; do not accept all24-bit words as physiological samples.

DC lead-off can be implemented internally with10MΩ pull-up/down or nA currents; its source/return paths, input impedance loss, DC offsets and additional noise must be included (ADS pp13,39–40; SBAA196 pp3–5). AC lead-off excitation is **fDR/4** (ADS p40): at2kSPS it is **500Hz inside20–850Hz**, and a generic ECG configuration will inject an in-band EMG artifact; at4kSPS it is1kHz, above850Hz but needing verified rejection and leakage control. Choose a lead-off policy compatible with EMG bandwidth and sample labeling, potentially using timed diagnostics.

## 8. Reference/VCAP network positives and limitations

- U1 VREFP24→C19(100nF)||C20(10µF)→AGND=VREFN25/AVSS; U2 uses C45/C46. Matches nominal reference bypass topology (p33Fig31 and p96Fig106), independently per IC. No two reference-buffer outputs short together.
- U1 VCAP1(28)→C23(22µF), VCAP2(30)→C24(1µF), VCAP3(55)→C25(1µF), VCAP4(26)→C26(1µF), all toAVSS netAGND; U2 equivalentsC49–C52. Values/returns match pin definitions pp10–11. Fig106 also depicts a parallel100nF atVCAP3; its omission is an optimization/review item, not clear proof of instability.
- VCAP3 voltage is internally **AVDD+1.9V relative AVSS**, hence5.2V at intended corrected3.3V rail. C25/C51 must have voltage margin and adequate effective capacitance at5.2V; a proposed6.3V MLCC may be within voltage rating but heavily derated, while4V parts would be overstressed. No rating/MPN/footprint is specified, so do not call a capacitor rating violation proven. Prefer documented10V-or-higher suitable part once size and derating are evaluated.
- Datasheet encouragesC0G for external input filter caps and close local decoupling/ground returns (p98). No PCB exists in workspace so location, leakage, antenna coupling and RF behavior remain unverified.

## 9. Protection and human-worn limits

R1–R32 are the only explicit input series elements; no external clamps, TVS, defibrillation protection or galvanic isolation are instantiated. The ADS's internal component-level HBM/CDM ratings (p12:±2kV/±500V) do not certify an electrode system against user-level ESD or fault currents. Continuous input pin absolute current is10mA (p12), a component survival limit, not a wearer-safe limit.

If an internal rail fault presents4.2V across a2kΩ input resistor, idealized current is**2.1mA** and resistor power**8.82mW**, before body impedance and return paths. This calculation is a screening case, not proof a specific single fault produces that current or a compliance conclusion. It shows2kΩ was selected primarily for filtering/noise, not a substantiated patient-protection architecture. Capacitor short circuits also give a2kΩ contact-toAGND path. Multiple contacts can create parallel fault paths. No resistor rating/footprint or exact battery/protection details are provided. Formal current-limiting and battery-only/USB-disconnected use constraints are necessary before human testing; test with an electrode simulator before any wearer.

## Findings summary for integration

1. **Critical:** analog supplies short to analog return and undefined digital supply/return; hard tied rail on analog aux pins exceeds absolute input ratings if enabled.
2. **High:** no deliberate DC body bias/RLD path; fails the stated architecture and leaves common-mode operating point undefined.
3. **High/Medium conditional:** RC/electrode mismatch and high shuntC degrade systemCMRR; no tolerance or impedance characterization. ActualCMRR unverified.
4. **Medium:** DC offset handling and gain policy unspecified; avoid treating no analogHP as unconditional benefit.
5. **Medium:** at2kSPS850Hz suffers8.26dB sinc³ attenuation; rate/passband objective must be reconciled.
6. **Medium firmware:** enable/settle/reference readback, keep optional outputs/modes disabled, choose EMG-compatible lead-off; AC500Hz at2kSPS is in-band.
7. **Unverified:** physical protection, capacitor/resistor voltage/power ratings, effective capacitance, physical electrode/connector mapping, layout/RF/ESD/stability and real noise.

## Phase 2 comparison

Parent verified the current `.kicad_sch` and `.kicad_pro` are byte-identical to the supplied read-only `../open-semg-16-v1/` reference and normalized connectivity/ERC match. Consequently all confirmed faults above are **Persists** for this supplied comparison; none is demonstrably Fixed or New. The historical Amberflow report itself was not supplied, so this classification establishes presence in both artifacts, not proof Amberflow previously identified each fault.
