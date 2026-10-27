# Open-sEMG-16 V2 — review-driven implementation record

27 October 2026. Authoritative starting point: [V1 full_review.md](../reviews_v1/full_review.md), particularly its F01–F21 table, subsystem explanations/calculations, Section 9.2 verified features, and recommended actions. The supporting [analog](../reviews_v1/analog-notes.md), [digital](../reviews_v1/digital-notes.md), [power](../reviews_v1/power-notes.md), [hardware](../reviews_v1/hardware-audit.md) and diagnostic records were consulted. This document records implementation, not a replacement audit or a new checklist.

## A. Summary

**V2 is still not ready for power-up or human-worn testing.** Three critical connectivity faults are fixed; unresolved power-source, bias, sequencing, qualification and safety work still prevents a readiness claim.

V2 began as a byte-identical copy of the supplied V1 schematic and project settings. Its initial native KiCad netlist reproduced the reviewed connections, including zero analog supply span, the invalid digital supply/return network, paralleled regulator outputs, floating regulator enables and the missing intended shared clock connection. Baseline ERC reproduced **38 errors and 27 warnings, 65 total**.

The changes actually implemented are:

- Reconnected U1/U2 AVDD, AVDD1 and DVDD to the **existing intended +3.3V net**, rather than the decoupling return buses. Established a common electrical return, named AGND, for battery negative, MCU grounds, ADC physical ground pins and intended digital-low connections. The existing LDO arrangement was not redesigned.
- Preserved the unused auxiliary analog ties to +3.3V; because actual AVDD is now on that same net, these ties follow AVDD as specified.
- Connected the existing U1 CLK wire to its existing ADC_CLK label, joining both ADC CLK pins without adding an oscillator or changing the SPI architecture.
- Added R33/R34/R35, each 10 kΩ, from START/RESET/PWDN respectively to AGND. They provide a low bias while controller pins are high impedance. CS defaults and complete power sequencing remain unresolved.
- Added TP1–TP16 for shared CLK, both DRDY signals, +3.3V, battery, AGND, both references and all eight VCAP nodes. U2 DRDY now has a real, independent probe connection; it was not connected to another MCU GPIO or to U1 DRDY.
- Added schematic notes describing the remaining blockers and firmware requirements. No firmware, component procurement, PCB, or human testing was performed.

**Finding counts:** 3 **Fixed** (F01–F03); 3 **Partially fixed** (F06, F09, F21); 15 other findings remain open to design decisions, firmware, measurements, simulation, or manufacturing work. Thus **18 of the 21 findings are not fully closed**. F18 received explicit firmware requirements but no firmware implementation and remains open. No finding is reclassified as previously misdiagnosed.

The five original High-severity findings remain either unresolved or partial: F04, F05 and F07 are unresolved; F06 and F09 are partial. The three original Critical findings are closed **for their diagnosed schematic connectivity mechanisms**, not as a general power-source or wearer-safety certification. Original severities and the distinction between confirmed defects and unverified risks are preserved below.

Final ERC is **35 errors and 26 warnings, 61 total**. [Targeted checks](diagnostics/verify_v2.py) pass **637 connectivity, component-preservation and file-integrity assertions**. The small ERC reduction does not measure the importance of the supply corrections: ERC did not detect every reviewed electrical mechanism.

### Targeting and tool limitation

Only `open-semg-16-v2.kicad_sch` was edited. All KiCad CLI exports and ERC calls explicitly named that V2 schematic; the matching V2 `.kicad_pro` remained unchanged. Initial/final exported metadata identifies the V2 source file.

The MCP initially reported V1 as its active project. Its requested switch to V2 returned **“MCP tool call requires approval, but approval policy is never”** and did not change its configuration. No MCP design-write operation was subsequently used. Local, V2-restricted source-span edits were validated by the installed KiCad CLI 10.0.7. Original/shared libraries were read only.

## B. Complete F01–F21 tracking

“Fixed” below applies to the exact original diagnosis. It does not mean an IC has been powered, a rail qualified, or a complete subsystem measured. Original **Unverified** severities remain unverified; they are not converted into demonstrated failures.

| Finding | Original severity | Original diagnosis | V2 action | Status | Verification |
|---|---|---|---|---|---|
| F01 | Critical | Both ADC analog supply spans are 0 V because AVDD/AVDD1 share AGND with AVSS | Moved actual AVDD/AVDD1 branches to the existing intended +3.3V buses; retained AVSS/AVSS1 at return | **Fixed** — diagnosed wiring | Both native ADC pin maps now distinguish supply from return. Actual rail regulation remains F04/F05/F13/F15/F16. |
| F02 | Critical | ADC DVDD is on the net named DGND while physical DGND is on AGND; MCU has no battery return | Moved DVDD to +3.3V and unified return-symbol values on AGND | **Fixed** — diagnosed wiring | Both ADC physical ground sets, U3 grounds, battery negative and intended-low terminals share AGND; no separate DGND island remains. |
| F03 | Critical | Aux 17/18/62 on +3.3V exceed actual AVDD+0.3V if that rail starts while AVDD is grounded | Preserved aux ties; corrected AVDD onto the same net | **Fixed** — diagnosed relative overvoltage | Each aux pin is electrically identical to actual AVDD. Optional output/rerouting restrictions remain F18. |
| F04 | High | Two independent LDO outputs directly drive one rail | Left U4.5/U5.5 unchanged; documented architecture alternatives | **Requires design decision** | Both outputs still share +3.3V. No sharing, source isolation, or third-source USB solution was invented. |
| F05 | High | Both LDO EN inputs float | Left shared EN unchanged rather than forcing both parallel regulators on | **Requires design decision** | EN still contains only U4.3/U5.3. Resolve enable policy together with F04/F17. |
| F06 | High | Intended shared ADC conversion clock connection absent | Extended the existing U1 wire to its existing ADC_CLK label; clarified CLK_EN requirement | **Partially fixed** | CLK net now contains U1.37/U2.37/TP1. U1 CLKSEL is +3.3V, U2 CLKSEL is physical ground. Firmware startup and observed synchronization remain unverified. |
| F07 | High | No deliberate DC body-bias/RLD path | No bias electrode or feedback/protection values chosen without evidence/approval | **Requires design decision** | Existing RLDREF/RLDINV/RLDOUT/WCT disconnections retained. No bias function or stable loop is claimed. |
| F08 | Unverified | Wearer current limits, ESD, external-power isolation and single faults unestablished | No unsupported safety circuit or compliance claim; retained as a test gate | **Requires measurement/simulation** and safety/design work | No new body drive path. Protected cell, complete fault analysis, simulator tests and external-interface qualification remain necessary. |
| F09 | High | CS/RESET/PWDN/START lack defined external reset states | Added 10 kΩ START/RESET/PWDN pulldowns; specified remaining sequencing contract | **Partially fixed** | R33–R35 have only their intended control/return terminals. CS defaults, actual MCU reset pulls, all-inputs-low startup and firmware remain open. |
| F10 | Medium | No bounded gain/offset/common-mode headroom policy | Preserved direct-coupled inputs; did not add an unqualified analog high-pass or select gain | **Requires measurement/simulation** and firmware | All original input values/mapping preserved. Measure contact offsets/artifacts/common mode, then specify gain and clipping recovery. |
| F11 | Medium | At2 kSPS the digital filter attenuates 850 Hz by about 8.26 dB | No fixed sample-rate change encoded in hardware | **Requires firmware** and passband decision | Original 2/4 kSPS filter calculations remain applicable; actual configured rate/attenuation is not established. |
| F12 | Unverified | Electrode impedance and 620 pF shunts may limit system CMRR/loading | Preserved all 32 nominal RC legs pending impedance/matching data | **Requires measurement/simulation** | No new RC values, tolerance claims or achieved CMRR figure. |
| F13 | Unverified | Effective output capacitance/ESR unresolved; nominal total exceeds specified 200 µF range | Preserved all capacitor values; recomputed common-return total after F02 | **Requires design decision** and capacitor qualification | Nominal total is now 242.6 µF across +3.3V/AGND, excluding DevKit capacitors. No oscillation is asserted. |
| F14 | Unverified | Capacitor voltage/derating and resistor ratings unspecified, notably VCAP3 | No guessed voltage ratings, dielectric or MPN added | **Requires PCB/manufacturing work** and part data | VCAP3 voltage calculation remains about 5.2 V at a corrected 3.3 V analog supply; C25/C51 remain unspecified. New pulls/probe pads also need physical definition. |
| F15 | Medium | Single-cell/LDO full-discharge headroom lacks cutoff policy | Retained battery and regulators pending source/cell decision | **Requires design decision** | No cell range, runtime, dropout occurrence or cutoff is assumed from the +3.7V label. |
| F16 | Unverified | DBV thermal/RF-load transient margin unqualified | Kept U5 package/part; recorded added pulldown load | **Requires measurement/simulation** and PCB work | No claimed temperature or >5% dip. Old conditional thermal screens remain screens. |
| F17 | Medium | DevKit USB/5V may introduce another source/backfeed | Kept DevKit and power interface; documented need for approved supply modes/isolation | **Requires design decision** | No USB/battery combination has been qualified or made safe by a note. |
| F18 | Medium | Reference, gain, rate, optional modes, intended-low GPIOs and lead-off need deliberate firmware | Added explicit clock/reference/mode restrictions to notes and this record | **Requires firmware** | No firmware files supplied or created; no register setting or timing behavior claimed implemented. |
| F19 | Medium | Most footprints/MPNs missing; installed DevKit/LP silicon unspecified | Preserved existing IC packages and all original footprints; added only V2-local TestPoint cache | **Requires PCB/manufacturing work** | Original 106 unassigned footprints remain; new 3 resistors+16 test points bring total to 125. No shared library or V1 cache changed. |
| F20 | Unverified | PCB returns, RF, decoupling placement, SPI edges and antenna unreviewed | No PCB/layout exists to modify or qualify | **Requires PCB/manufacturing work**, then measurement | Native connectivity is checked; no routed-layout or physical/RF signoff. |
| F21 | Low | No dedicated access to slave DRDY and useful diagnostic nodes | Added TP1–TP16 and independent U2 DRDY probe net | **Partially fixed** | All intended probe nodes verified; physical footprints, pad placement, loading and assembled access remain PCB work. |

## C. Detailed implementation log

### C1. F01/F02 — supply branches and actual return connections

**Original mechanism:** supply terminals were wired to capacitor return buses. Connecting decouplers to +3.3V elsewhere did not power the IC. A separate net called DGND also isolated the MCU from battery negative and incorrectly served as ADC DVDD.

The repair follows the original design's existing +3.3V analog/digital supply intent. It deliberately does **not** choose which LDO should own that rail. Therefore its present regulation, startup and source conflicts remain open.

| Component / physical pins | V1 and initial V2 net | Final V2 net |
|---|---|---|
| U1 AVDD19/21/22/56/59 and AVDD1 54 | AGND | +3.3V |
| U2 AVDD19/21/22/56/59 and AVDD1 54 | AGND | +3.3V |
| U1 DVDD48/50 | DGND | +3.3V |
| U2 DVDD48/50 | DGND | +3.3V |
| Both ADC AVSS20/23/32/57/58 and AVSS1 53 | AGND | AGND, unchanged |
| Both ADC physical DGND33/49/51 | AGND | AGND, unchanged |
| Both ADC VREFN25 | AGND | AGND, unchanged |
| U3 ground 22/23/24/44 | DGND | AGND |
| BT1 negative 2; U4/U5 ground 2 | AGND | AGND, unchanged |
| Both ADC RESV1 31, DAISY_IN41, GPIO42/44/45/46 | DGND | AGND |
| U2 CLKSEL52 | DGND, also the wrongly wired DVDD net | AGND, now the actual physical digital ground |
| U1 CLKSEL52 | +3.3V | +3.3V, unchanged; now also actual DVDD |
| C8.2/C9.2/C34.2/C35.2 | DGND | AGND |
| C6/C7/C32/C33 ground terminals; reference/VCAP/input-cap returns | AGND / merged GND | AGND, unchanged |

**Exact branch geometry:** U1's capacitor supply bus is y86.36 mm and its return bus is y93.98 mm. Actual AVDD19/21/22/56/59 is at(172.72, 101.60); AVDD1 54 at(177.80, 101.60); DVDD48/50 at(182.88, 101.60). Six original wire objects were rerouted so those stems now start from the upper supply bus. Three junctions moved with their branches. C6/C7 and C8/C9 still bridge supply to return; their return conductors were not left attached to the new stems.

U2 repeats the same six-wire/three-junction correction at offset(+227.33,−1.27) mm: supply bus y85.09, return bus y92.71; AVDD at(400.05, 100.33), AVDD1 at(405.13, 100.33), DVDD at(410.21, 100.33). The [power edit log](diagnostics/power-edit-log.json) records every original and replacement wire/junction object.

Nine existing power-symbol instance values changed from DGND to AGND: **#PWR09, #PWR014, #PWR016, #PWR020, #PWR040, #PWR045, #PWR047, #PWR051, #PWR065**. This establishes a common electrical reference. It does not claim a particular future PCB return-current layout or analog/digital isolation performance. No arbitrary zero-ohm link, PWR_FLAG or pin-type change was introduced.

**Manufacturer check:** ADS1298 SBAS459K pp.10–12 specify the actual supply/return pin assignments and operation at AVDD−AVSS2.7–5.25 V and DVDD−DGND1.65–3.6 V. For a qualified nominal 3.3 V source, the new intended analog/digital spans are 3.3 V, AVDD−DVDD=0 V and AVSS−DGND=0 V. That is compatible with the stated relative limits. Analog headroom above its 2.7 V minimum is 0.6 V; digital margin below its 3.6 V operating maximum is 0.3 V. These are nominal design checks, not measured or guaranteed outputs of the still-unresolved regulator network. Figure 106 single-supply operation is on **p.97**; some V1 review figure references saidp.96, while §11.1 begins onp.96.

**Validation:** [after-power netlist](diagnostics/after-power-netlist.xml), [after-power ERC](diagnostics/after-power-erc.json), final per-pin assertions, unchanged acquisition-net partitions, and visual inspection of the rendered supply circuit. Supply wiring does not wait on a firmware setting to become correct. Existing regulator enable/source issues still prevent energizing the system.

### C2. F03 — auxiliary analog pins now follow actual AVDD

No auxiliary wire, pin mode, or component value was changed. The exact consequence of C1 is:

| Component / pins | V1 connection and relation | V2 connection and relation |
|---|---|---|
| U1/U2 TEST/PACE17/18 and RLDIN62 | +3.3V, while actualAVDD wasAGND | +3.3V, now the same net as actualAVDD |

The diagnosed conditional exposure changes from approximately 3.3 V above AVDD to **0 V above AVDD**. The ADS absolute analog-input upper bound is AVDD+0.3 V (§7.1 p.12); p.10's footnote specifies unused pins 17/18/62 connected to AVDD. Native net identity, rather than assumed rail voltage, verifies the correction. If the eventual power architecture separates analog and digital rails, these auxiliary ties must continue to follow **actual AVDD**, not merely a digital rail named 3.3 V.

This does not authorize enabling PACE outputs against a rail tie or using RLD rerouting toward a contact. Those firmware restrictions remain F18; no body-bias path was added.

### C3. F06 — restore the existing intended clock route

| Item | Before | After |
|---|---|---|
| Wire UUID533df57d-c904-4f56-83a9-8aa8b1ee9e94 |(195.58, 157.48) to(210.82, 157.48) mm |(195.58, 157.48) to(220.98, 157.48) mm |
| Existing U1 global ADC_CLK label | At(220.98, 157.48), dangling | Same position, now attached to the wire |
| U1 pin 37 | Unconnected pin net | ADC_CLK |
| U2 pin 37 | ADC_CLK, singleton | ADC_CLK shared with U1.37 and passiveTP1 |
| U1 pin 52 / U2 pin 52 | +3.3V / invalid-reference DGND | +3.3V / actual AGND after C1 |

This implements the already drawn clock intent. No external oscillator, daisy-chain arrangement, SPI-pin reassignment, or new timing source was selected. Existing clock notes now state **“U1 CLK_EN=1 required”**; a separate schematic note records the shared-RESET consequence.

ADS Table 11 p.50 and CONFIG1 p.67 specify CLKSEL high selects the internal oscillator and CLK_EN must be 1 to expose it on CLK. CLK_EN resets 0. With the repaired supplies U2 CLKSEL is now genuinely low, selecting external CLK. **A wire alone cannot enable the master clock or guarantee simultaneous samples.** Shared RESET clears master CLK_EN again; firmware must restore the output and initialize the slave with a valid clock before relying on it.

Validation: [after-clock netlist](diagnostics/after-clock-netlist.xml) and [ERC](diagnostics/after-clock-erc.json). The clock net had only both ADC pins before adding TP1, and now has those pins plus TP1. U1 CLK-disconnection error, dangling ADC_CLK error, and that clock wire's dangling-end warning disappeared. Clock continuity, frequency, startup and paired-DRDY alignment still require bench verification.

### C4. F09 — add low-bias control defaults without selecting an unresolved power architecture

| New component | Value | Pin 1 | Pin 2 | Prior state of that control net |
|---|---|---|---|---|
| R33 |10 kΩ | START: U1.38/U2.38/U3.12(GPIO8) | AGND | MCU and two ADC inputs only |
| R34 |10 kΩ | RESET: U1.36/U2.36/U3.6(GPIO6) | AGND | MCU and two ADC inputs only |
| R35 |10 kΩ | PWDN: U1.35/U2.35/U3.7(GPIO7) | AGND | MCU and two ADC inputs only |

Original components and values were not changed. These are new passive pulldowns, placed in a separate schematic block. Their reference designators and values are visible; new ground-symbol references are hidden using normal presentation attributes, with ground values visible. No resistor footprint, tolerance, power rating or MPN is asserted to have been procured; those remain F19/F14 work.

START low inhibits unintended conversion start; active-low RESET and PWDN are biased toward reset/power-down while the MCU is high impedance. This favors an inactive initial state compatible with the review's concern. Existing MCU pins can still drive the same controls high when an appropriate startup sequence is implemented.

**Leakage/loading calculation:** D1 p.16 lists up to±10 µA per ADC digital input. For two shared inputs, a nominal 10 kΩ pulldown gives an illustrative worst-case 20 µA×10 kΩ=0.20 V; including 50 nA controller input leakage adds about 0.0005 V. Against VIL≤0.2DVDD=0.66 V at 3.3 V, that leaves approximately 0.4595 V margin **under the assumed high-impedance/no-opposing-pull model**. Actual MCU reset pulls, resistor tolerance and startup waveforms still need checking; these calculations do not establish every reset condition.

When a control is driven to 3.3 V, each pull draws 0.33 mA and dissipates 1.09 mW. If all three are high in acquisition, they add up to **0.99 mA** rail load and 3.27 mW resistor dissipation. This is a new budget item, not a measured current. Any chosen resistor part must meet its rating with tolerance and voltage margin.

**Why no CS pull-ups were added:** the original review suggests them, but also requires complete power sequencing. D1 §11.1 p.96 requires inputs low until supplies stabilize. A passive pull-up that rises with DVDD does not independently prove compliance, particularly with unresolved MCU/USB power states. Choosing a complete power/default-state policy is therefore still necessary. The present CS nets remain unchanged, and the implementation makes no claim that output contention at reset is eliminated.

F09 remains partial: hardware low bias is supplied for three controls; CS states, actual controller reset behavior and full sequencing are not resolved. This is narrower than claiming a safe or deterministic complete startup.

### C5. F21 — actual diagnostic connections, not warning suppression

All test points are standard passive one-pin Connector:TestPoint symbols. The standard definition was copied into **V2's embedded symbol cache only**. No system/shared library or V1 embedded symbol changed. Test points have no selected footprint or physical placement yet.

| Test point | Final net | Existing node exposed |
|---|---|---|
| TP1 | ADC_CLK | U1.37 andU2.37 |
| TP2 | DRDY_ADC1 | U1.47 and unchanged U3.15(GPIO9) |
| TP3 | DRDY_ADC2 | U2.47 only; no MCU assignment |
| TP4 | +3.3V | Existing shared regulator/output supply |
| TP5 | +3.7V | BT1 positive and regulator inputs |
| TP6 | AGND | Actual common circuit return |
| TP7 | VREFP_ADC1 | U1.24 and C19/C20 positive terminals |
| TP8 | VCAP1_ADC1 | U1.28 and C23 positive terminal |
| TP9 | VCAP2_ADC1 | U1.30 and C24 positive terminal |
| TP10 | VCAP3_ADC1 | U1.55 and C25 positive terminal |
| TP11 | VCAP4_ADC1 | U1.26 and C26 positive terminal |
| TP12 | VREFP_ADC2 | U2.24 and C45/C46 positive terminals |
| TP13 | VCAP1_ADC2 | U2.28 and C49 positive terminal |
| TP14 | VCAP2_ADC2 | U2.30 and C50 positive terminal |
| TP15 | VCAP3_ADC2 | U2.55 and C51 positive terminal |
| TP16 | VCAP4_ADC2 | U2.26 and C52 positive terminal |

VREFP/VCAP autogenerated net names such as `Net-(U1-VREFP)` now have explicit sheet-local names such as `/VREFP_ADC1` solely to connect their test points. No two reference outputs or VCAP nodes were joined. The slash in native local net names is KiCad's sheet path, not an extra conductor or polarity indicator.

The sole NC-marker removal was at U2 DRDY47(422.91, 163.83), replaced by a real wire to(436.88, 163.83) and a DRDY_ADC2 label connected to TP3. The other eight explicit NC markers remain. Existing nearby text now says the slave output is for testing and that the MCU still uses U1 DRDY. No NC marker was added to hide a missing signal.

VCAP nodes remain bypass nodes, not power outputs for loads. Test pads and probes add physical capacitance/leakage; layout and probe selection must keep that loading appropriate. F21 is partial because no physical PCB pads, access clearance or loaded measurements exist yet.

### C6. F18 and implementation boundaries — documented firmware contract

The schematic includes a concise note that the corrections are partial, the power/bias blockers remain, the reference must be enabled/settled, and optional output/rerouting modes must stay off. It also records that shared RESET clears U1's clock-output enable.

No firmware state is established by that text. A candidate sequence to verify after resolving power-source/default-state choices is:

1. Establish valid qualified rails and safe receiver input states. Keep conversion start inactive and control signals compliant through power-up; current passive defaults cover only part of this requirement.
2. Initialize the MCU's output values before enabling its outputs; ensure only one CS can be active. Release PWDN/RESET in a datasheet-compliant sequence.
3. Initialize U1 using its internal oscillator, honor POR/VCAP1/reset timing, send SDATAC for configuration, and enable U1 CLK_EN.
4. With the clock now valid at U2, allow its clock-dependent POR/VCAP conditions. Use an appropriate **individually selected slave RESET opcode/configuration**, or another demonstrated sequence, without clearing U1 CLK_EN through another shared hardware reset. Allow 18tCLK after RESET, honor 4tCLK command-decode spacing, and observe rate-specific filter settling times.
5. Enable/settle the appropriate internal reference on each ADC, choose compatible gain/rate/lead-off settings, read both IDs/registers back, and keep PACE/RLD/WCT output/rerouting modes disabled for their unused wiring. Keep grounded ADS GPIOs inputs or output-low.
6. Use shared START after matching configuration; verify both DRDY waveforms and sample alignment. Read complete 216-bit frames per ADC with exclusive CS, correct SPI timing/update keepout, DIN zero during normal frame retrieval, and bounded transfer latency.
7. Treat shared RESET/PWDN changes or a supply interruption as reasons to reestablish the clock/initialization sequence. Detect missing/clipped/invalid samples explicitly.

This candidate sequence is a documented dependency for review, not validated software or a guaranteed power-up procedure. No chosen 2/4 kSPS rate, gain, reference register, lead-off excitation or radio throughput has been implemented. In particular, keep the reviewed 500 Hz AC lead-off contamination at 2 kSPS in the firmware decision.

## D. Validation results

### D1. Preserved baseline and checkpoints

| Checkpoint | Errors | Warnings | Total | Interpretation |
|---|---:|---:|---:|---|
| [Initial ERC](diagnostics/initial-erc.json) / [netlist](diagnostics/initial-netlist.xml) |38|27|65|Reproduces V1 audit and identical initial V2 |
| [After power](diagnostics/after-power-erc.json) / [netlist](diagnostics/after-power-netlist.xml) |37|27|64|Return islands combined and actual supply branches corrected |
| [After clock](diagnostics/after-clock-erc.json) / [netlist](diagnostics/after-clock-netlist.xml) |35|26|61|U1 CLK, global label and dangling clock endpoint connected |
| [Final ERC](diagnostics/final-erc.json) / [netlist](diagnostics/final-netlist.xml) |35|26|61|Control pulls/probes and final annotations introduce no additional reported violations |

Three errors and one warning were eliminated: one power-input-not-driven error associated with the former separate DGND net, U1 CLK-not-connected, dangling ADC_CLK label, and the dangling clock-wire endpoint warning. Important AVDD/DVDD wiring corrections were not represented by a large ERC error count in the first place.

### D2. Final ERC inventory and why violations remain

| Type | Final errors | Final warnings | Meaning / action |
|---|---:|---:|---|
| pin_not_connected |28|0|Existing U3 CHIP_PU/unused GPIO terminal reports. Intact DevKit internal circuits must be interpreted from its actual assembly; no blanket NCs added. |
| power_pin_not_driven |3|0|AGND, battery-source +3.7V and carrier +5V power-model reports. Passive battery source/DevKit supply mode require truthful modeling once architecture is resolved; no PWR_FLAG added to hide real problems. |
| pin_not_driven |2|0|Actual shared regulator EN remains unresolved; U3 CHIP_PU report depends on DevKit assembly. |
| pin_to_pin |2|4|Errors: parallel LDO outputs, and supported shared DOUT subject to valid CS. Warnings: unused TEST/PACE rail ties; output modes must stay disabled. |
| unconnected_wire_endpoint |0|19|Pre-existing 16 electrode-area stubs, two ADC optional-output-area stubs and a U3-side stub. Native channel/CS connectivity remains correct; unrelated cleanup not performed. |
| multiple_net_names |0|2|Existing +3.3V/AVDD and AGND/GND aliases remain. Actual pin memberships are independently checked. |
| lib_symbol_mismatch |0|1|Existing BT1/cache/library mismatch retained rather than modifying shared libraries or V1. |

No new ERC check type or count increase occurred. The four inherited disabled check types remain exactly as in V1: single_global_label, four_way_junction, simulation_model_issue, footprint_filter. No severity, exclusion, ERC pin type or project setting was changed. “All severity” reports configured checks; it does not enable a check that was disabled in the inherited project.

### D3. Targeted netlist and preservation checks

[validation-results.json](diagnostics/validation-results.json) records 637 passed assertions. These include:

- Every original pin has exactly its expected final net, allowing only documented supply/return/clock/DRDY changes and reference/VCAP net naming for probes.
- All 32 ADC input-net memberships are unchanged. E1–E16 polarity, all R1–R32 values, all 620 pF input capacitors, and direct-coupled filtering remain unchanged.
- All original 111 component values, footprints, library identities and pin numbers are unchanged. Final component count is 130: original 111 plus 3 pulls plus 16 test points.
- All 57 original capacitors retain both connected terminals. Reference networks remain separate and VCAP topology/values/returns are retained.
- MOSI, MISO, SCLK and both CS nets retain **exact original pin membership**. Shared START/RESET/PWDN retain all original terminals plus their respective passive resistor. No bus driver or MCU assignment was added.
- Master/slave CLKSEL are now genuinely high/low relative to valid intended supply/return, and both CLK pins share only each other and TP1.
- U2 DRDY reaches only TP3; U1 DRDY still reaches its existing MCU input plus TP2.
- All original embedded symbol definitions are byte-identical; only standard TestPoint was added to V2's cache. No shared library was modified.
- Exactly one explicit NC marker was removed for a real new connection; none were added. Existing RLD/WCT disconnections were preserved.
- All 54 protected pre-existing files other than the authorized V2 schematic remain hash-identical, including V1 schematic/project, **all original review documents and diagnostic files captured under reviews_v1**, shared local library files, and the V2 project file.

The check script compares native KiCad exports rather than inferring behavior from visible label text. Independent read-only power and digital reviews of the final netlist found no regression in those scopes.

### D4. Visual and tool checks; limitations

[Final schematic PDF](diagnostics/final-schematic.pdf) and diagnostic crops show the supply bus correction, control-pulldown block and probe grid. They support schematic readability/connection review, not PCB or physical performance claims. KiCad emitted a fontconfig warning but generated native netlists, ERC and PDF successfully.

A local edit-helper variable-name error stopped the first controls/probes preparation **before the V2 file was written**. It was corrected, the phase completed and the final exports regenerated. A later label-placement cleanup temporarily detached eight probe-side labels; the targeted netlist assertions caught that regression, the labels were restored, and native ERC plus all 637 assertions were rerun successfully. No incomplete or failing candidate is used as final evidence.

No DRC was run because there is no PCB. No circuit simulation, rail measurement, RF test, startup capture, electrode/body test, thermal test, firmware execution or safety certification was performed. ERC and 637 static assertions are not proof of an electrically qualified power source, actual simultaneous sampling, or safe human use.

## E. Unresolved issues, decisions and exact next actions

### E1. Power architecture — F04/F05/F13/F15/F16/F17

**Decision required:** how the existing DevKit, ADC analog supply, ADC digital supply and external power inputs should be powered. The original review explicitly left this architecture open.

| Alternative | Benefit | What must be established before implementation |
|---|---|---|
| One qualified 3.3 V source | Removes unsanctioned parallel regulation; simple rail topology | Source current/thermal/transient/noise qualification for RF plusADC load; remove/isolate other sources; capacitor network and USB mode |
| Separate U4 analog and U5 digital rails, retaining the existing DevKit | Keeps the 150 mA regulator away from the much larger RF demand and permits separate filtering/qualification | Exact LP silicon, separate capacitor networks, U5 DBV thermal/transient margin, supply sequencing and DevKit USB isolation |
| DevKit onboard digital regulation plus a separate AFE supply | Uses the complete board's existing power circuitry | Valid input source for that board across the selected battery window; battery/USB source selection and analog/digital sequencing; no assumed 5 V from a single cell |

**Recommended direction for approval:** separate analog and digital supplies while retaining the existing DevKit for this revision. The original conditional current comparison is approximately 6.5 mA for the two ADCs versus up to 355 mA for a module RF test condition, before DevKit overhead. This favors keeping MCU current out of U4's150 mA budget. It does **not** prove U5's DBV package or a particular cell is qualified. New control pulls can add up to 0.99 mA when high.

If approved, a subsequent detailed design should assign actual AVDD/AVDD1, unused analog aux pins and their analog decoupling to the analog rail, and actual DVDD/MCU supply/digital-high straps and digital decoupling to the digital rail, with a deliberate common return. That proposal has not been wired here. Splitting rails alone does not automatically fix the 200 µF output-capacitance concern, reverse-current behavior, sequencing, or RF noise.

**Exact next actions:** approve the source/rail architecture and allowed USB/battery modes; specify the battery and usable voltage window; select the full LP orderable/silicon and capacitor parts; then finalize source isolation and hardware EN states. Do not hard-enable both existing parallel regulators as a standalone “F05 fix.” Manufacturer EN→VIN guidance applies only within an intentionally valid always-on architecture. Select a cutoff/supply solution for low-cell headroom, and qualify steady/burst current, thermal behavior and reverse current.

F13 remains an **unverified qualification concern**: after the return repair, all supply capacitors now contribute a nominal **242.6 µF** across the common output, excluding the DevKit. No capacitor value was changed. D3's recommended output range and D2's new-silicon range end at 200 µF; actual effective capacitance/ESR and architecture still need parts. No oscillation or transient magnitude is claimed.

### E2. Bias and wearer protection — F07/F08

**Decision required:** a protected passive body-bias strategy or one compensated ADS RLD driver with a dedicated bias contact. The present design has neither. No feedback/drive resistor values or protection current limits can be chosen responsibly without the electrode model and applicable safety requirements.

**Recommended direction for approval:** investigate one compensated RLD driver for the desired common-mode rejection, with the second driver off, rather than tying active outputs together. Device/sensing-channel selection, compensation, protected drive path and fault behavior still need design work. A protected passive bias remains the simpler comparison option. This recommendation follows the review's common-mode objective and TI's RLD analysis; it is not an implemented loop or stability claim.

**Exact next actions:** approve the bias approach and intended body contact; obtain representative electrode/body/cable impedance and capacitance; select sensing and safety requirements; design/model the loop and fault-current paths; validate with a simulator including disconnections before any person is connected. Define protected-cell, charging, USB and debug constraints. Do not infer safety from the 2 kΩ series resistors or ADC component-level ESD/current ratings.

### E3. Clock, controls and firmware — F06/F09/F18; sample-rate decision F11

**Exact next actions:** specify and implement a complete power-up/default-state contract, including actual MCU reset pulls and CS behavior. Reconcile CS inactive-high requirements with the manufacturer's all-inputs-low power-up guidance and external-power states; then determine whether pulls, control gating or a different approved sequence are needed. The three existing new pulldowns do not solve this entire problem.

Implement and test the documented master-clock/slave-initialization sequence, reference enable/settling, register readback, grounded GPIO policy, exclusive CS, complete frame handling and failure recovery. Verify both clocks/DRDY signals and sample correspondence with an oscilloscope/logic analyzer. No firmware source was supplied; firmware remains a real dependency.

Choose acceptable passband attenuation and 2/4 kSPS HR operation from the original sinc³ calculations. At850 Hz the reviewed gains remain approximately−8.26 dB at 2 kSPS and−1.97 dB at 4 kSPS. Do not treat “below Nyquist” as flat response, or choose a register rate solely to close a schematic finding. Decide an EMG-compatible lead-off policy and invalid-sample labeling before interpreting physiological data.

### E4. Offsets, CMRR and component qualification — F10/F12/F14

**Exact next actions:** measure representative dry-contact impedances/imbalance, differential DC offsets, common mode and motion excursions; then select gain and clipping recovery, and model the actual RC/protection network. No gain, high-pass network or RC replacement was selected because those choices require that evidence.

Complete component specifications: actual capacitance at DC bias, voltage rating, ESR, dielectric, tolerance and leakage; resistor tolerance/power/pulse ratings; exact IC orderables and installed DevKit. In particular, `VCAP3−AVSS≈(AVDD−AVSS)+1.9 V`, or about 5.2 V with 3.3 V analog supply. C25/C51 ratings remain unknown. No overstressed capacitor part or achieved CMRR figure is claimed without parts or measurement.

### E5. PCB, manufacturing and physical verification — F16/F19/F20/F21

**Exact next actions:** define and place actual parts and test-pad footprints on a PCB; verify all 125 currently unassigned component footprints; perform schematic/PCB parity and DRC; inspect electrode connectors, IC pads/orientation, return currents, local decoupling, VCAP/reference leakage, antenna keepout and thermal copper. Measure edge quality and RF on/off contamination with realistic loads.

TP1–TP16 provide schematic access only. Choose pad geometry, probe access and loading on the actual layout, then demonstrate assembled access. The DevKit symbol still represents a complete 44-pad board; replacing it with a bare WROOM is a consequential change that requires a new interface/power design, not an automatic F19 correction.

### E6. Approval and readiness boundary

Before any energization, resolve the still-paralleled outputs and floating enables, complete the necessary component/source qualification and startup controls, and plan current-limited dummy-input bring-up. Before human use, additionally complete body bias, fault-current/protection/isolation design, simulator testing and the appropriate safety review. The current V2 file is a **partial corrected development design**, not a power-up or wearer release.

## F. Modified and created files

**Modified existing file:** `open-semg-16-v2.kicad_sch` only.

**Unchanged:** `open-semg-16-v2.kicad_pro`; V1 schematic and project; every original review and diagnostic under `reviews_v1/`; all shared/local symbol libraries and other protected pre-existing files. Hash checks compare against the before-edit record. No PCB exists or was modified. The added TestPoint definition is confined to V2's embedded cache.

The exact created-file list is appended below and is also available in [created-file-manifest.txt](diagnostics/created-file-manifest.txt). All paths are inside the authorized workspace. Temporary compiler/cache/binary outputs and unused edit candidates were removed before the final manifest; original review artifacts were not removed or rewritten.

### Manufacturer evidence used for implementation

- [ADS1298 SBAS459K](../../docs/datasheets/originals/components/ADS1298.pdf): pp.10–12 physical pin assignments, unused analog ties, absolute and operating conditions; p.16 digital leakage/thresholds; p.50 Table 11 and p.67 clock enable; pp.48/51–53/59–63 reset/start/SPI timing; pp.69/71 reference/gain; §11.1 p.96 and Fig 106 p.97 power guidance. Original local PDF was re-extracted for this implementation.
- [LP2985 SLVS522S](../../docs/datasheets/originals/components/LP2985.pdf): pinout p.3, enable p.16, capacitor/reverse-current guidance pp.20–21, silicon distinction p.30. Used to establish why unresolved F04/F05/F13 must not be closed by a generic enable/capacitor change.
- [TLV755P SBVS320D](../../docs/datasheets/originals/components/TLV755P.pdf): input/output and EN limits pp.3–6; output discharge pp.12–13; capacitor/dropout/reverse-current/thermal guidance pp.15–18. Source qualification remains outstanding.
- The full original review remains the source for preserved noise/filter/CMRR/current calculations and official DevKit evidence. No new performance figure in this record is presented as a measurement.

### Exact retained file list

- [reviews_v2/diagnostics/after-clock-erc.json](diagnostics/after-clock-erc.json)
- [reviews_v2/diagnostics/after-clock-netlist.xml](diagnostics/after-clock-netlist.xml)
- [reviews_v2/diagnostics/after-power-erc.json](diagnostics/after-power-erc.json)
- [reviews_v2/diagnostics/after-power-netlist.xml](diagnostics/after-power-netlist.xml)
- [reviews_v2/diagnostics/annotation-edit-log.json](diagnostics/annotation-edit-log.json)
- [reviews_v2/diagnostics/clock-edit-log.json](diagnostics/clock-edit-log.json)
- [reviews_v2/diagnostics/controls-view.png](diagnostics/controls-view.png)
- [reviews_v2/diagnostics/controls_probes-edit-log.json](diagnostics/controls_probes-edit-log.json)
- [reviews_v2/diagnostics/created-file-manifest.txt](diagnostics/created-file-manifest.txt)
- [reviews_v2/diagnostics/extract-pdf.m](diagnostics/extract-pdf.m)
- [reviews_v2/diagnostics/final-connectivity.json](diagnostics/final-connectivity.json)
- [reviews_v2/diagnostics/final-erc.json](diagnostics/final-erc.json)
- [reviews_v2/diagnostics/final-netlist.xml](diagnostics/final-netlist.xml)
- [reviews_v2/diagnostics/final-schematic.pdf](diagnostics/final-schematic.pdf)
- [reviews_v2/diagnostics/implement_v2.py](diagnostics/implement_v2.py)
- [reviews_v2/diagnostics/initial-erc.json](diagnostics/initial-erc.json)
- [reviews_v2/diagnostics/initial-geometry.json](diagnostics/initial-geometry.json)
- [reviews_v2/diagnostics/initial-netlist.xml](diagnostics/initial-netlist.xml)
- [reviews_v2/diagnostics/initial-v2.kicad_sch](diagnostics/initial-v2.kicad_sch)
- [reviews_v2/diagnostics/pdf-text/ADS1298.txt](diagnostics/pdf-text/ADS1298.txt)
- [reviews_v2/diagnostics/pdf-text/LP2985.txt](diagnostics/pdf-text/LP2985.txt)
- [reviews_v2/diagnostics/pdf-text/TLV755P.txt](diagnostics/pdf-text/TLV755P.txt)
- [reviews_v2/diagnostics/power-edit-log.json](diagnostics/power-edit-log.json)
- [reviews_v2/diagnostics/power-view.png](diagnostics/power-view.png)
- [reviews_v2/diagnostics/pre-edit-hashes.json](diagnostics/pre-edit-hashes.json)
- [reviews_v2/diagnostics/probes-view.png](diagnostics/probes-view.png)
- [reviews_v2/diagnostics/reference-view.png](diagnostics/reference-view.png)
- [reviews_v2/diagnostics/render-pdf.m](diagnostics/render-pdf.m)
- [reviews_v2/diagnostics/schematic_tools.py](diagnostics/schematic_tools.py)
- [reviews_v2/diagnostics/validation-results.json](diagnostics/validation-results.json)
- [reviews_v2/diagnostics/verify_v2.py](diagnostics/verify_v2.py)
- [reviews_v2/updates_from_v1.md](updates_from_v1.md)

