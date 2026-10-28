"""Generate a two-column comparison using fresh V0 and V1.4 evidence."""
import csv,json,hashlib,re
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
previous=json.loads((OUT.parent/'condition_findings.json').read_text())
records={}
def put(id,status,why,v14):
    records[id]={'status':status,'why':why,'v14':v14}

put('A1','CANNOT VERIFY','An IC needs a supply inside its operating range.',
    'The missing analog-source connection is corrected under H2: U1/U2 AVDD19/21/22/54/56/59 and DVDD48/50 now reach /+3.3V from U3.1/.2; negatives reach /GND. Nominal 3.3 V meets ADC analog 2.7–5.25 V, digital 1.65–3.6 V and ESP module 3.0–3.6 V ranges. Actual loaded voltage is unmeasured, and the V0 floating voltage was unknown: do not count a numerical undervoltage as FIXED. Keep connections; identify fitted DevKit/source and measure supplies at U3 and both ADCs during startup and Wi-Fi loading. [S1,S2]')
put('B1','CANNOT VERIFY','Excess dissipation can overheat a resistor.',
    'Input R1–R32 retain 2 kΩ and now specify ≥0.1 W; R39/R40 CS and R41 strap pulls are 10 kΩ with ≥0.1 W requirements. These are selection requirements, not proof of fitted parts/input-voltage limits. R33–R35 have no selected power rating. Select compliant parts and document actual voltage bounds; no resistance change justified. A 10 kΩ resistor across 3.3 V dissipates 1.089 mW; 3.3 V across 2 kΩ gives 5.445 mW. Compare actual P=V²/R to the selected rating; these examples are not measured electrode losses.')
put('C1','CANNOT VERIFY','Capacitor voltage must remain below its terminal-to-terminal rating.',
    'VCAP3 capacitors C25/C51 and added C58/C59 now require ≥10 V, addressing the approximately 5.2 V nominal internal node at 3.3 V AVDD. A written requirement is not a fitted-part inspection, and other ratings remain incomplete. Select parts meeting existing requirements and compare maximum actual voltages to ratings. No value change or added capacitor follows solely from this check. The 5.2 V projection is not a guaranteed overshoot maximum. No excluded tolerance/DC-bias analysis performed. [S1]')
put('C2','NOT FOUND','An open terminal prevents the capacitor from serving its circuit.',
    'All 58 capacitors have both terminals connected to another component terminal in the fresh netlist. No open capacitor terminal found in either revision. No correction; connectivity checks do not prove stability or physical placement.')
put('C3','NOT FOUND','A bypass capacitor needs a valid ground return.',
    'All grounded capacitor returns, including C8/C9/C34/C35, reach /GND with both ADCs and U3 grounds. V0 capacitor returns also reached valid battery ground. Keep the connections; this is NOT FOUND, not a V0 fault credited as fixed.')
put('C4','NOT FOUND','A regulator needs its specified output capacitance for stable regulation.',
    'External LDOs/capacitors are removed. The complete U3 board includes its own regulator bypass; carrier rail bypass totals 42.6 µF nominal. Insufficient capacitance is not demonstrated. Do not add output capacitance. Identify fitted regulator and qualify its existing combined bank: reference SGM2212 recommends 1–10 µF effective output capacitance. That is a compatibility question, not proof that the present rail oscillates. Do not delete ADC bypasses without evidence. [S3,S4]')
put('C5','CANNOT VERIFY','Some regulators require particular capacitor ESR, the effective series resistance.',
    'LP2985 is removed; its legacy ESR constraints do not transfer automatically to U3. Reference-board SGM2212 supports ceramic capacitors. Exact fitted regulator/capacitor specifications remain unknown, and its complete output bank needs qualification. Identify parts and check documentation or measure startup/load-step stability before selecting a capacitor or regulator change. No ESR resistor justified by a generic warning. No measured oscillation asserted. [S4]')
put('C6','CANNOT VERIFY','A rail dip can corrupt operation or trigger a reset.',
    'C6–C9/C32–C35 and added C60–C63 bypass the shared rail, but no waveform establishes ≤5% droop. Measure 3V3 relative to local ground at U3 and both ADCs during boot and peak Wi-Fi/ADC activity. Five percent of 3.3 V is 165 mV. Do not add bulk capacitance without demonstrated need.')
put('C7','CANNOT VERIFY','Capacitive loading can destabilize an enabled amplifier.',
    'The external RLD feedback/electrode-output branches are removed; RLDOUT63/RLDINV61/RLDREF60 are unused. No external RLD load is drawn. This does not establish a V0 instability or a verified stability fix. Keep optional RLD/WCT/PACE functions disabled as specified. No compensation change; test an actual enabled loop only if one is required. [S1]')
put('D1','NOT FOUND','A bare LED requires current limitation.',
    'U3 is a complete DevKit. Official reference-board power LED D5 has R11=5.1 kΩ; RGB D6 contains a driver. No missing limiter found in that reference. Even zero forward voltage gives 3.3/5100=0.647 mA through R11. No added resistor; confirm installed board variant. These are internal board references, not new carrier parts. [S3]')
put('D2','NOT APPLICABLE','An inappropriate LED/open-collector connection can cause wrong behavior or excess current.',
    'No direct bare-LED/open-collector arrangement in the carrier or official board reference. No correction.')
put('E1','CANNOT VERIFY','Excess input voltage can damage a regulator.',
    'BT1 and both external regulators are removed. USB supplies U3’s internal LDO; nominal USB does not show input overvoltage, but installed board/source remain unverified. Use documented board power mode and compare actual LDO input to fitted-part limits. Reference SGM2212 operates over 2.7–20 V; do not assign that rating to an unidentified clone. [S3,S4]')
put('E2','CANNOT VERIFY','Dropout is the extra input voltage an LDO needs above its output to maintain regulation.',
    'V0 battery-to-3.3 V path no longer exists. USB powers the onboard LDO, but actual cable/diode losses and load are unknown. Measure minimum LDO input/output under peak load. Reference SGM2212-3.3 maximum dropout is 0.380 V at 500 mA and 0.610 V at 800 mA over the stated temperature range. Include output tolerance; its dropout point is defined at 95% output, not exact nominal regulation. No added converter justified by V0’s uncertain headroom. [S4]')
put('E3','CANNOT VERIFY','Self-dependent enables or latches can keep a supply off.',
    'Old LDOs and /EN are gone. U3 has its documented onboard CHIP_PU pull-up/reset network; no carrier self-latching enable arrangement is present. No extra enable part. Power-cycle actual board to verify startup. V0’s actual latch/off waveform was never established, so do not count that hypothetical failure as FIXED; E6 records the real floating-enable correction. [S3]')
put('E4','NOT FOUND','A wrong regulator setpoint can deliver the wrong named voltage.',
    'Documented fixed 3.3 V board output supplies /+3.3V. No setpoint/rail-name mismatch found. V0’s source-free +3.3VA was a connection fault, not an LDO setpoint mismatch. No E4 correction; measure the delivered rail.')
put('E5','FIXED','Paralleled independent outputs have no guaranteed current sharing.',
    'V0 U4.5 LP2985 and U7.5 TLV755 are both removed. One USB-powered board LDO supplies the carrier through U3 3V3 headers1/2; two pins from one output are not two regulators. Keep the explicit one-source mode: no external 3.3 V or 5 V injection while using USB. No added mux/sharing circuit. Fresh netlist confirms no other carrier power source. [S3]')
put('E6','FIXED','Two joined enable inputs do not generate a valid enable level.',
    'V0 U4/U7 and their two-input-only /EN net are removed. External U3.3 CHIP_PU is unused, but the complete reference board has R5=10 kΩ pull-up and C6=1 µF reset capacitor. No extra external EN resistor required. Verify installed board matches the documented assembly; ERC cannot see its internal RC. [S3]')
put('E7','NOT APPLICABLE','A switching supply can cause analog noise in some arrangements.',
    'Documented U3 regulator is a linear LDO, as were V0 U4/U7. No switching-regulator-to-ADC arrangement appears. Confirm actual board identity. No switching-supply redesign or independent analog-noise/layout investigation. [S4]')
put('E8','NOT APPLICABLE','Lowering a programmed output may require sinking current.',
    'Fixed 3.3 V supply; no adjustable setpoint or required lowering transition in either revision. No correction.')
put('E9','CANNOT VERIFY','A signal before valid receiver power can violate sequencing or inject current.',
    'Common MCU/ADC rail removes separate carrier power domains; R33–R37 hold forward controls low while GPIOs are high impedance. R39/R40 now pull CS high with the rail, requiring a check against TI all-inputs-low ramp guidance. Capture rail/CS/RESET/PWDN/GPIO timing through cold start and supply loss. Validate existing sequence before adding supervisors or isolation. A passive network does not establish an actual waveform. [S1 §11.1]')
put('F1','CANNOT VERIFY','Internal amplifiers require a valid analog supply span.',
    'AVDD/AVDD1 now connect to nominal 3.3 V and AVSS/AVSS1 to /GND. H2 closes the source connection fault. V0 numerical floating voltage and V1.4 actual loaded span remain unmeasured, so a numerical F1 comparison is unresolved. Measure span against 2.7–5.25 V at both ADCs. No amplifier replacement; no duplicate supply-fault count. [S1]')
put('F2','NOT FOUND','Reversed positive/negative supplies can prevent operation or cause damage.',
    'AVDD=nominal3.3 V and AVSS=GND. V0 had grounded AVSS and unpowered AVDD, not a deliberately reversed source. Pin identities/net polarity checked; no F2 correction.')
put('F3','CANNOT VERIFY','Common-mode is the input pair’s average voltage; even a small differential signal can be invalid if that average is outside PGA limits.',
    'Removed RLD/reference-electrode branches do not establish actual electrode common-mode or a measured fault/fix. Specify input average, differential amplitude, DC offsets and programmed gain/reference. At 3.3 V, gain6 and |VD|=0.4 V, PGA common-mode requires 1.4 V<VCM<1.9 V, with additional full-scale/rail constraints. Measure actual inputs; select bias correction only if needed. No independent RLD redesign. [S1 §9.3.1.5]')
put('F4','CANNOT VERIFY','An unstable feedback loop can oscillate or ring.',
    'External RLD loop removed; optional RLD/WCT/PACE must remain off. No V0 oscillation or V1.4 instability measurement exists. No compensation change based on deletion of a circuit. If an enabled loop is required, test its actual load/model. Board LDO/capacitor qualification is addressed separately. [S1]')
put('F5','CANNOT VERIFY','Input offset/signal can exceed gain-dependent headroom; an output can also be overloaded.',
    'Schematic gives bounded bench-source/gain examples, but actual input/firmware data are absent. Enable/settle/read back both 2.4 V references and gain settings. At gain6 the nominal reference full scale is ±0.4 V, subject also to PGA common-mode limits. Measure full input DC plus signal; alter gain/bias only after showing a violation. No separate clipping or overload proven. [S1]')
for id in ['G1','G2','G3','G4','G5','G6','G7']:
    put(id,'NOT APPLICABLE','This condition requires the controlled power-multiplexer arrangement described by Ambrflow.',
        'Neither revision contains a power multiplexer. Reference-board USB diodes are not a controlled-priority mux. Complete inventories checked; no mux component or new architecture justified.')
put('H1','NOT FOUND','An IC needs a valid supply return; a ground name alone is insufficient.',
    'U1/U2 real AVSS/DGND and U3 GND22/23/24/44 all share /GND. V0 real IC supply grounds also reached battery negative; its separate DGND control island was a J3 fault. No H1 fault in either comparison revision. Keep common return; no added ground architecture.')
put('H2','FIXED','A source-free analog rail cannot deliberately power the ADCs.',
    'U1/U2 AVDD19/21/22/54/56/59 and DVDD48/50 all reach /+3.3V via U3.1/.2; actual returns reach U3 ground. Source is inside the complete USB-powered board. No missing rail connection remains. Confirm actual board and measure loaded rail. Do not add another regulator or PWR_FLAG solely because the carrier symbol omits internal power-output modeling. V0 floating voltage is not assumed0 V. [S3]')
put('I1','CANNOT VERIFY','Logic must meet receiver thresholds under actual loading.',
    'All interfaces share nominal3.3 V/GND. ADS→ESP nominal static margins are0.425 V. ESP minimum VOH and ADS minimum VIH both equal0.8×3.3=2.64 V, with no extra guaranteed high margin; 10 kΩ pulls load highs by≈0.33 mA. Measure loaded levels at ADC receivers and check drive settings/test conditions before changing pulls or adding translators. Compatible nominal labels do not prove dynamic operation; equality is not a measured failure. [S1,S2]')
put('I2','CANNOT VERIFY','Slow edges can violate serial timing.',
    'No large external bus RC; bias resistors and changed GPIOs do not prove edge compliance. Measure SCLK/DIN/DOUT at receivers under selected speed/loading and compare timing. SCLK is Schmitt-triggered. No buffer/series part justified by schematic names alone. [S1]')
put('I3','NOT FOUND','An open-drain output needs a suitable pull-up.',
    'DOUT/DRDY are driven outputs. CS pull-ups define input deselection, not an open-drain DOUT/DRDY requirement. Reference-board reset sink has its own10 kΩ pull-up. No missing/excessive relevant pull-up found. Do not add generic DRDY pulls; excluded general sink-capability analysis not performed. [S1,S3]')
put('I4','CANNOT VERIFY','Source impedance/settling must match this ADC’s architecture and accuracy needs.',
    'Same2 kΩ/620 pF lead filters; ADS1298 has CMOS PGA inputs ahead of delta-sigma conversion, not a directly driven generic SAR sample-and-hold. RC=1.24 µs, simple pole≈128.4 kHz;1.2 nA through the drawn2 kΩ alone gives2.4 µV. These do not include electrode impedance or prove24-bit settling. Obtain actual source/gain/data-rate and test settled output. No input buffer or filter-value change justified. [S1]')
put('I5','CANNOT VERIFY','Slow/noisy threshold crossings can repeatedly trigger an input without adequate hysteresis.',
    'Defined reset bias does not certify clean ramps. SCLK has documented hysteresis (different rising/falling thresholds); U3’s EN RC is onboard. Measure relevant ramp/noise crossings before adding Schmitt buffers or changing RC values. No chatter waveform established. [S1,S3]')
put('J1','CANNOT VERIFY','A wrong boot/debug strap can select unintended behavior.',
    'R41=10 kΩ now pulls U3 GPIO3 pin13 high, defining USB JTAG when strap-controlled. Default/forced eFuse modes still determine ownership; the resistor cannot override forced pad JTAG. GPIO39–42 now serve CS2/MISO/DRDY and overlap JTAG pads. Read eFuses, reserve pins and verify cold boot; do not burn eFuses automatically. Physical floating strap improved, but no V0 functional boot failure was proven. [S2]')
put('J2','FIXED','ADC power-down/enable needs a defined state before firmware.',
    'R35=10 kΩ now pulls both PWDN35 low while U3 GPIO7 is high impedance; R34 similarly biases RESET36 and R33 START38. Retain pulls; hold MCU reset and verify levels. Two10 µA leakage limits through10 kΩ give≤0.20 V versus VIL=0.66 V at3.3 V. This fixes missing hardware bias; a pull does not override actively driven warm-reset states. [S1,S2]')
put('J3','FIXED','Undefined controls can make power/reset/clock selection unpredictable.',
    'Old floating LDO /EN removed; intended low straps now share real /GND. R33–R37=10 kΩ define START/RESET/PWDN/MOSI/SCLK and R39/R40 define CS high. U1 CLKSEL52=3V3, U2 CLKSEL52=GND; both CLK37 join /ADC_CLK. No missing passive bias/clock connection remains for these V0 omissions. Firmware must enable U1 CLK_EN and validate master-first reset/recovery. Check held-reset defaults and measure clock at both chips. [S1,S2]')
put('J4','NOT FOUND','An MCU input must stay within its local supply-referenced voltage limits.',
    'MISO U3.37 and DRDY U3.38/.39 receive ADC outputs on the same3.3 V rail/ground. No5 V GPIO connection or excessive static input voltage found in either revision. Board USB5 V is an internal power input, not GPIO drive. No level shifter justified by these connections; startup/overshoot remain measurement checks under E9/L2/I2.')
put('K1','CANNOT VERIFY','An excessive load or incompatible driven state can overstress a GPIO.',
    'Bias currents are≈0.33 mA when driving against10 kΩ, with no demonstrated overload. Actual GPIO/ADC modes unknown. Grounded ADS GPIO42/44/45/46 must remain inputs/output-low; optional modes on tied analog pins must stay off. Inspect/read back configuration and restart states. No driver/series resistor justified from a hypothetical misconfiguration.')
put('K2','CANNOT VERIFY','Opposing active outputs can contend.',
    'U1/U2 DOUT43 share /SPI_MISO with U3 GPIO40. This is supported with separate CS and high-impedance deselected DOUT; R39/R40 default deselection. Actual firmware exclusivity and JTAG/input ownership are unverified. Keep shared bus; configure one CS low at a time and GPIO40–42 as inputs. Scope both CS/MISO during boot/reset/reads and inspect eFuses. ERC output/output alone is not proof of conflict. [S1 §9.4.2.1,S2]')
put('K3','CANNOT VERIFY','Driving an unpowered receiver can inject input current.',
    'Common always-connected MCU/ADC3V3 removes separate carrier power domains. PWDN is an operating control, not a drawn DVDD switch. Actual ramp/reset combinations are unmeasured. Validate actual supply/control timing; do not equate power-down mode with physically removed DVDD or add isolation without a demonstrated state. [S1]')
put('L1','CANNOT VERIFY','A load transition can lower the rail and cause brownout, a reset due to low supply.',
    'Wi-Fi and ADCs share the DevKit rail; actual source/load budget and transition traces remain absent. Capture3V3 at U3/ADCs, LDO input and reset reason under actual Wi-Fi/ADC changes. No brownout event established; do not add bulk capacitance or a separate rail before measuring. C6’s5% threshold is165 mV.')
put('L2','CANNOT VERIFY','A GPIO high before receiver power is valid can violate sequencing.',
    'R33–R37 give low defaults while GPIOs are high impedance; common rails reduce supply differences. CS pulls rise with the rail; precise ramp behavior and warm-reset active states remain unverified. Capture rails/CS/RESET/PWDN/forward GPIOs and validate startup note. Consult TI about CS ramp guidance if unresolved; no new control IC justified by an unobserved transient. [S1 §11.1]')

def prose(s):
    """Space ordinary prose quantities without changing nets, IDs or links."""
    saved=[]
    def hold(m):
        saved.append(m.group()); return f'@@KEEP_{len(saved)-1}@@'
    s=re.sub(r'https?://[^\s)]+|(?<=\]\()[^)\n]+(?=\))|`[^`]+`|/?\+(?:3\.3VA|3\.3V|3\.7V|5V)\b',hold,s)
    s=re.sub(r'’s(?=\d)','’s ',s)
    s=re.sub(r'([,;])(?=\d)',r'\1 ',s)
    s=s.replace('CLI10','CLI 10')
    s=re.sub(r'\b([A-Z]?[a-z]{2,}|at|At|of|Of|to|To|no|No)(?=\d)',r'\1 ',s)
    s=re.sub(r'(?<=\d)(?=(?:µF|nF|pF|kΩ|MΩ|mA|µA|nA|mV|µV|V|mW|kHz|MHz|µs|ms)\b)',' ',s)
    for i,p in enumerate(saved): s=s.replace(f'@@KEEP_{i}@@',p)
    return s

expected=[f'{c}{i}' for c,n in zip('ABCDEFGHIJKL',[1,1,7,2,9,5,7,2,5,4,3,2]) for i in range(1,n+1)]
assert list(records)==expected
source_urls={
    'S1':'https://www.ti.com/lit/ds/symlink/ads1298.pdf',
    'S2':'https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf',
    'S3':'https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf',
    'S4':'https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf',
}
def citations(s):
    def link(m):
        return ', '.join('['+p.strip()+']('+source_urls[p.strip()[:2]]+')' for p in m.group(1).split(','))
    return re.sub(r'\[(S[1-4][^\]]*)\]',link,s)
rows=[]
for old in previous:
    id=old['ID']; r=records[id]
    v0=old['V0_finding']
    if id=='D1': v0='No LED circuit is represented by the V0 module/carrier schematic.'
    left=f"**{id} — {old['Ambrflow_condition']}**<br>**Why it matters:** {r['why']}<br>**V0 components:** {old['V0_component']}.<br>**V0 finding:** {v0}"
    right=citations(f"**{r['status']}.** {r['v14']}")
    rows.append({'ID':id,'Category':old['Category'],'Classification':r['status'],'Problem':prose(left),'V1_4':prose(right)})
counts=Counter(r['Classification'] for r in rows)

intro='''# Ambrflow comparison — V0 versus V1.4-codex

**28 October 2026 · read-only electrical audit · no schematic modifications**

**The six previously confirmed V0 wiring/control defects are corrected in the V1.4 schematic.** None of those six wiring defects remains; no new failure covered by this checklist is confirmed. Loaded power, firmware execution and actual analog input behavior remain unverified. A corrected connection is not proof of working acquisition.

This report applies the same48 original conditions to the two complete active schematics. Ambrflow supplied generic failure conditions, not a component-specific fault list. Column1 identifies relevant components, why each condition matters and whether it was established in V0. Column2 explains the V1.4 result, any supported correction and verification. Backups, review candidates and historical snapshots were not used as active sources.

## Verified corrections to the six V0 defects

| V0 problem, affected components, and why it matters | Solved in V1.4? What changed and what remains to check |
|---|---|
| **H2 — Missing ADC analog source.** U1/U2 AVDD19/21/22/54/56/59 joined source-free `+3.3VA`, so there was no valid deliberate analog supply. | **Yes, wiring fixed.** Analog/digital positives reach U3’s3V3 headers1/2 on `/+3.3V`; negatives reach `/GND`. Source is the USB-powered complete board. Confirm installed board and loaded rail. A1/F1 did not establish a numerical floating V0 voltage, so are not separately credited as FIXED. |
| **E5 — Paralleled LDO outputs.** U4.5 LP2985 and U7.5 TLV755 joined one rail without defined current sharing. | **Yes.** Both external regulators and battery removed; one board LDO supplies the carrier. Two3V3 headers from that one output are one source. Keep the documented USB-only source arrangement; no added mux needed. |
| **E6/J3 — Floating LDO enables.** `/EN` contained only U4.3/U7.3, two inputs; startup was not guaranteed. | **Yes.** Regulators and `/EN` removed. Complete U3 board already contains its own EN pull-up/reset network. Its unused external CHIP_PU header is not a missing internal pull-up. |
| **J3 — Intended low straps were not grounded.** RESV1.31, GPIO42/44/45/46 and U2 DAISY_IN41 used isolated `DGND`. | **Yes.** Those low ties now reach real `/GND` with ADC DGND33/49/51 and U3 grounds. Keep unused ADS GPIOs as inputs/low outputs and conflicting optional modes off. |
| **J2/J3 — No hardware ADC reset bias.** PWDN35/RESET36/START38 depended on unbiassed ESP GPIOs before firmware. | **Yes, missing bias fixed.** R35/R34/R33=10kΩ pull shared controls low. R36/R37 also bias MOSI/SCLK; R39/R40 pull CS high. Loaded levels, ramps and warm-reset active states still need checks. |
| **J3 — CLKSEL self-tied to undriven CLK.** Each ADC CLK37 joined only CLKSEL52; CLK could not define its own reset selection. | **Yes, wiring fixed.** U1 CLKSEL high, U2 low; both CLK37 pins now share `/ADC_CLK`. No clock wire is missing. Firmware must enable U1 CLK_EN and initialize ADC2 after clock readiness; execution is unverified. |

Counts refer to **six distinct wiring arrangements**, not six checklist rows. J3 overlaps several arrangements. No completion percentage across generic conditions is calculated.

Across the48 checklist rows: **5 FIXED,24 CANNOT VERIFY,9 NOT FOUND and10 NOT APPLICABLE**. There are no confirmed STILL PRESENT, PARTIALLY FIXED or NEW IN V1.4 rows. A1/F1 retain uncertainty because V0's floating voltage is unknown; their underlying H2 wiring fault is nevertheless demonstrably corrected. New power-bank/CS-ramp concerns remain uncertainties, not confirmed faults.

## Remaining uncertainties and simplest next steps

| Relevant Ambrflow conditions, components and unresolved concern | Simplest supported action and verification |
|---|---|
| **A1/E2/C6/L1 — shared supply under load.** Complete U3 board, USB source/cable and MCU/ADC3V3. Nominal voltage and the reference LDO’s800mA rating do not establish available header current or droop. | Identify installed board/LDO and source capability. Measure LDO input,3V3 and reset during boot and actual Wi-Fi/ADC loading. No general thermal review or new supply architecture is introduced here. |
| **C4/C5 — board-regulator/capacitor compatibility.** Carrier rail bank is42.6µF nominal before onboard capacitance; reference SGM2212 recommends1–10µF effective output capacitance. | Qualify actual combined bank with manufacturer guidance or startup/load-step response. This is a new configuration concern, **not proof of unsuitable ESR (capacitor series resistance), instability or a >5% dip**. Do not add bulk capacitance, remove ADC bypasses or select a replacement regulator without evidence. No excluded derating investigation performed. |
| **E9/J3/K2/L2 — sequencing.** R39/R40 default CS high while TI requests low inputs during rail stabilization. Shared RESET clears U1’s clock-output setting. | Validate master-first startup below; capture CS/rail/reset and seek TI clarification if the CS ramp remains unresolved. No extra isolator/supervisor is justified by a hypothetical event. |
| **I1/J1/K1/K2 — loaded logic and GPIO ownership.** High-level limits have no extra guaranteed nominal margin;10kΩ biases load highs. GPIO39–42 overlap JTAG. | Read eFuses and firmware modes; reserve pads; measure loaded levels and verify exclusive CS/input-only MISO/DRDY. A shared tri-state bus alone is not output contention. |
| **F3/F5/I4 — analog input range/settling.** Electrode/source average voltage, DC offsets and impedance remain unspecified. | Check actual input envelope against programmed gain/reference and PGA limits; test representative settling. Retained2kΩ resistors do not justify a generic SAR acquisition warning or an added buffer. Removed RLD alone proves no common-mode fault or fix. |
| **B1/C1 — selected component ratings.** Some requirements are now explicit, especially ≥10V VCAP3 capacitors, but rated parts are not fully selected. | Meet existing requirements with actual specified parts and compare maximum voltage/power. Written requirements are not fitted-part inspections. |

These risks are **UNKNOWN** until the missing evidence is obtained. There is no confirmed remaining fault to assign P0/P1/P2 solely from these uncertainties. Their order above is a practical verification order.

## Complete checklist — requested two-column format

'''
doc=[prose(intro)]
current=None
for r in rows:
    if r['Category']!=current:
        current=r['Category']
        doc.append(f"\n### {current}\n\n| Ambrflow problem, components, and why it matters | Is it solved in V1.4? How, or simplest supported correction/verification |\n|---|---|\n")
    doc.append('| '+r['Problem'].replace('|','\\|')+' | '+r['V1_4'].replace('|','\\|')+' |\n')

appendix='''
## Mapping and evidence needed to interpret the comparison

| Item | Verified fact or limitation |
|---|---|
| **Exact active sources** | V0: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/Archive/electronics-archive/open-semg-16-electronics-v0/open-semg-16.kicad_sch`. V1.4: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/open-semg-16-v1-codex/v1.4/open-semg-16-v1.4.kicad_sch`. Both entire files/embedded definitions were parsed; each is one flat sheet with no hierarchical children. Source hashes checked unchanged after audit. |
| **Controller ambiguity** | V0 U6 has ESP32-S3-WROOM-1 module pins/footprint although one drawing-box title says DevKitC-1. The title does not change actual pin definitions or establish installed board internals. V1.4 U3 explicitly represents a complete ESP32-S3-DevKitC assembly. Exact fitted board revision/regulator/module suffix still needs confirmation; official v1.1 is the internal-circuit reference. |
| **Equivalent input circuits** | U1/U2 remain TI ADS1298xPAG; grade/orderable suffix unspecified. V0 U1 E17–E24/R3,R21–R35 map to V1.4 E1–E8/R1–R16. V0 U2 E1–E8/R4–R19 map to V1.4 E9–E16/R17–R32. Each of32 leads retains2kΩ/620pF. All16 differential mappings checked by ADC pin, not renamed references. |
| **VCAP/reference mapping** | U1 V0 C63/C64/C65/C66→C23/C24/C25/C26; U2 V0 C2/C3/C4/C5→C49/C50/C51/C52:22µF/1µF/1µF/1µF. U1 VREF C67/C68→C19/C20; U2 C17/C11→C45/C46:100nF/10µF. Added C58/C59=100nF parallel VCAP3; C60/C61 and C62/C63=1µF/100nF rail pairs. Added bypasses do not demonstrate a V0 >5% dip or instability. |
| **GPIO remap** | PWDN V0 U6.6/GPIO6→U3.7/GPIO7; RESET U6.7/GPIO7→U3.6/GPIO6; START U6.23/GPIO21→U3.12/GPIO8. MOSI U6.19/GPIO11→U3.17/GPIO11; SCLK U6.21/GPIO13→U3.18/GPIO12. Shared V0 CS U6.5/GPIO5 becomes CS1 U3.27/GPIO21 and CS2 U3.36/GPIO39. Daisy output path becomes shared MISO U3.37/GPIO40; DRDY1 U3.38/GPIO41 and DRDY2 U3.39/GPIO42 both connected. |
| **Rail capacitor arithmetic** | Four10µF + four0.1µF + added(1+0.1+1+0.1)µF =42.6µF nominal directly on3V3. VCAP/reference capacitors are on separate internal nodes, not simply added to LDO output bank. No tolerance/DC-bias-derating calculation performed. |
| **Logic calculation** | ADS VOH≥2.90V versus ESP VIH=2.475V; ADS VOL≤0.4V versus ESP VIL=0.825V: nominal0.425V margins under specified test conditions. ESP VOH(min)=0.8VDD equals ADS VIH(min)=0.8DVDD=2.64V on common3.3V. A 10kΩ high-load current is0.33mA. Loaded high behavior requires measurement; these equal bounds are not a proven fault. |
| **Master-first startup to verify** | After supplies stabilize, release PWDN; wait U1 POR/VCAP1 readiness, pulse/release shared RESET with TI timing, initialize U1 and enable CLK_EN. Then U2 receives its external clock. Wait U2 at least2^18 valid clock periods (128ms at2.048MHz) and VCAP1>1.1V, whichever is later; issue U2-only SPI RESET and observe command/18-clock completion timing. Do not pulse shared RESET again after enabling U1 clock unless restarting the sequence. Enable/settle both2.4V references, configure/read back, then START. Firmware execution is not established by notes in the schematic. |
| **Fresh ERC** | KiCad CLI10.0.7: V0=62 messages; V1.4=7 errors/0 warnings. V1.4 messages:3V3/GND source-model omissions(2), shared DOUT output types(1), external CHIP_PU unconnected/undriven(2), unused5V header unconnected/undriven(2). Complete board has internal power/reset; DOUT can tri-state by CS. Messages were explained, not suppressed. ERC is supporting evidence, not a functional test. |
| **Export limitations** | V0 warns of annotation errors: two reference-electrode instances both J1; unique physical connector mapping cannot be inferred from that reference. Supply/control conclusions do not depend on it. Fontconfig warning did not prevent XML/ERC/SVG outputs. No physical waveform, simulation, firmware execution, brownout, clipping or oscillation test was performed. |
| **Prior reviews used as context** | Read V1.3 power architecture/implementation and V1.4 implementation/power/ADC evidence before recommending next steps. Their project IDs such as F06/F09/F18 are preserved as project references, distinct from Ambrflow A1–L2. Active netlists/datasheets determine this report; unrelated project findings are not imported as Ambrflow faults. |
| **Scope** | No independent RLD, electrode safety, footprint, RF/layout, general thermal, capacitor tolerance or DC-bias review. Supply/load/stability checks above relate only to the supplied conditions. V1.4 itself specifies simulated bench signals; this audit does not extend that use case. |

## Sources

- **S1:** [TI ADS1298 SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf), PAG pins pp10–11, ratings p12, input/DC pp13–16, PGA pp31–32, clock p50, shared SPI pp56–60, configuration p67, startup p96. Local original in `sEMG-Hardware/docs/datasheets/originals/components/ADS1298.pdf`.
- **S2:** [ESP32-S3 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf), reset/glitch/strap/JTAG/DC tables; [WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf), module supply/DC limits.
- **S3:** [Official DevKitC-1 v1.1 schematic, sheet2](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf) and [official power methods](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#power-supply-options). Internal board references U2/R5/C6/D5 are not carrier references.
- **S4:** [SGM2212 Rev.A.2](https://www.sg-micro.com/rect/assets/54089b71-cc25-4f36-af2e-34b07f00a108/SGM2212.pdf), capacitor recommendations pp3–4, dropout p6, capacitor guidance p10. Applies only if fitted regulator matches.
- V0: [TI LP2985](https://www.ti.com/lit/ds/symlink/lp2985.pdf) and [TI TLV755P](https://www.ti.com/lit/ds/symlink/tlv755p.pdf); output/enable/dropout/capacitor checks. Exact V0 LP chip generation unknown.

Fresh audit evidence: [V0 connectivity](EVIDENCE/v0-v1_4-codex/v0.connectivity.txt), [V1.4 connectivity](EVIDENCE/v0-v1_4-codex/v1_4.connectivity.txt), [V1.4 ERC](EVIDENCE/v0-v1_4-codex/v1_4.erc_summary.txt), [source manifest](EVIDENCE/v0-v1_4-codex/source_manifest.json). [Two-column CSV](AMBRFLOW_V0_V1_4_CODEX_COMPARISON.csv).
'''
doc.append(prose(appendix))
name='AMBRFLOW_V0_V1_4_CODEX_COMPARISON'
(ROOT/f'{name}.md').write_text(''.join(doc))
headers=['Ambrflow problem, components, and why it matters','V1.4 status, change, simplest correction and verification']
def plain(s): return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',s.replace('<br>','\n').replace('**',''))
with (ROOT/f'{name}.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(headers)
    for r in rows: w.writerow([plain(r['Problem']),plain(r['V1_4'])])
(OUT/'condition_findings.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
for v,item in json.loads((OUT/'source_manifest.json').read_text()).items():
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'],f'{v} source changed'
print('All48 conditions. Classifications:',dict(counts))
print('Report words:',len((ROOT/f'{name}.md').read_text().split()))
