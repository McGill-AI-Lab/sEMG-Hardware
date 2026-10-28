# Ambrflow meeting summary — V0 versus V1

**28 October 2026 · active schematics only · no source files changed**

## A. Overall result

**V1 still has confirmed supply and control wiring problems. No complete V0 problem is demonstrably closed.**

| Result | Count |
|---|---:|
| Confirmed distinct V0 wiring/control problems |6|
| Fully fixed in V1 |0|
| Partially fixed |1|
| Still present |5|
| Newly introduced distinct V1 problems |2|
| Checklist comparisons that cannot be verified |25 of 48|

Eight distinct problems need correction/completion. Counts group overlapping checklist entries; no completion percentage is claimed. A1/F1 are uncertain only in their numerical V0 comparison: **V1’s analog supply is confirmed 0 V**; V0’s source-free rail voltage is unknown. H2 counts the missing valid analog supply in both.

## B. What we fixed

**No fully verified closure. One local improvement is real:**

| Ambrflow ID | Original V0 problem | Change in V1 | Why it helps / remaining limit |
|---|---|---|---|
|J3 — partial|CLKSEL tied only to CLK: undefined at reset|U1 gets a high strap; U2 intended as clock slave|U1 strap becomes valid after supply repair. Slave clock connection is still missing; complete it and validate startup.|

LDO renumbering and unchanged 2 kΩ/620 pF input filters are not fixes. The DevKit already includes EN/reset circuitry.

## C. What still needs fixing

Proposed changes only. Exact connections/verification: detailed Findings 1–8.

| Priority | Ambrflow ID | V1 components | Problem | Simple solution |
|---|---|---|---|---|
|P0|H2; A1/F1|U1/U2 AVDD19/21/22/54/56/59|Analog supply grounded:0 V span; analog-pin overvoltage risk|Move analog positives/unused analog ties to dedicated U4 output; keep negatives grounded.|
|P0|H2/A1|U1/U2 DVDD48/50|Digital positive supply on DGND|Move DVDD to U5 digital 3.3 V **before joining grounds**.|
|P0|H1/C3|U3 GND22/23/24/44; C8/C9/C34/C35.2|No battery return for controller/decouplers|After DVDD correction, join genuine returns to battery/LDO ground.|
|P0|J3 partial|U1/U2 CLK37|ADC2 selects an external clock, but ADC_CLK has no source|Connect U1.37 to ADC_CLK/U2.37; firmware sets U1 CLK_EN.|
|P1|E5|U4.5/U5.5|Two independent LDO outputs share +3.3V|Separate existing outputs: U4 analog, U5 digital/MCU; retain each output capacitor.|
|P1|E6/J3|U4.3/U5.3|Shared /EN has only input pins|If always-on, connect enables to their shared input supply; no extra resistor.|
|P1|J3|U1/U2 pins 31/41/42/44/45/46; U2.52|Low straps on ungrounded DGND|Connect to valid ground after removing misplaced supply pins.|
|P1|J2/J3|Shared PWDN35/RESET36/START38|No guaranteed hardware defaults before firmware|10 kΩ pulldowns on shared PWDN/RESET, and START for conversion-off; validate CS/startup sequence.|

P0 denotes verified operating blockers or overvoltage risk. No measured damage, oscillation or brownout (low-supply reset) is claimed.

## D. What we cannot yet verify

Missing: rated passive BOM/LP2985 identity; battery limits/load; firmware/eFuses; electrode source/load/configuration; startup and transient measurements. These limit power-rating, dropout, ESR, input-range, settling and timing conclusions. Dropout means inadequate regulator voltage headroom; ESR is capacitor series resistance; common-mode is the input pair’s average voltage.

Shared MISO is valid with exclusive chip selection. ADS1298’s PGA/delta-sigma inputs do not justify a generic SAR settling warning. Missing RLD alone proves no measured input-range fault.

## E. Questions for Ambrflow

1. Does connectivity identify V0’s source-free +3.3VA and V1’s AVDD connection to the capacitor ground row?
2. Which exact /EN and isolated-DGND connections did your checks flag?
3. Which LP2985 generation and capacitor ESR/parts were assumed?
4. What battery limits, cutoff and LDO loads informed dropout checks?
5. Were ESP reset defaults, ADS CLK_EN=0 and the DevKit’s internal EN network modeled?
6. Which startup/chip-select/USB-power states supported any contention or high-before-power warning?
7. Did settling analysis use ADS1298’s actual architecture, our 2 kΩ/620 pF network, and what electrode impedance/error target?
8. Which eFuse/JTAG requirement would make floating GPIO3 a functional fault?

## F. Next actions

1. Correct supply/return connections and split LDO outputs; re-export netlists/ERC before powering.
2. Complete clock/reset defaults and validate master-first startup: shared reset clears ADC1’s clock output. Confirm DevKit power mode.
3. Obtain missing BOM/battery/configuration data; measure rails/startup/CS behavior before recommending further components.

Evidence, manufacturer links and all 48 condition decisions: [detailed audit](AMBRFLOW_DETAILED_AUDIT.md), [CSV matrix](AMBRFLOW_ISSUE_MATRIX.csv), and `EVIDENCE/` netlist/ERC exports.
