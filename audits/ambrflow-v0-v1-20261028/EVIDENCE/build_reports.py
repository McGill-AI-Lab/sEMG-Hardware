"""Generate the requested reports from the reviewed, condition-by-condition findings."""
import csv, json, hashlib, re
from collections import Counter
from pathlib import Path

ADS = '[TI ADS1298, SBAS459K](https://www.ti.com/lit/ds/symlink/ads1298.pdf)'
LP = '[TI LP2985, SLVS522S](https://www.ti.com/lit/ds/symlink/lp2985.pdf)'
TLV = '[TI TLV755P, SBVS320D](https://www.ti.com/lit/ds/symlink/tlv755p.pdf)'
ESP = '[Espressif ESP32-S3 datasheet v2.2](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)'
MOD = '[Espressif WROOM-1/1U datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)'
BOARD = '[Espressif DevKitC-1 v1.1 schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20221130.pdf)'
GUIDE = '[Espressif DevKitC power guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.0.html)'
PAR = '[TI parallel-LDO reference, §2.2.1.1](https://www.ti.com/lit/pdf/tiducs7)'
CATEGORIES = {'A':'Analog — supply pins','B':'Analog — resistors','C':'Analog — capacitors','D':'Analog — LEDs','E':'Analog — regulators','F':'Analog — amplifiers','G':'Analog — power multiplexers','H':'Analog — wiring','I':'Mixed-signal','J':'Firmware — reset conditions','K':'Firmware — operating states','L':'Firmware — state transitions'}
rows = []

def add(id, condition, classification, priority, c0, v0, c1, v1, evidence, requirement, change, fix, verify):
    rows.append(dict(ID=id,Category=CATEGORIES[id[0]],Ambrflow_condition=condition,V0_component=c0,V0_finding=v0,V1_component=c1,V1_finding=v1,Classification=classification,Priority=priority,Evidence=evidence,Recommended_fix=fix,Verification_needed=verify,Requirement=requirement,Difference=change))

add('A1','An IC supply pin operates above its rating or below its minimum operating voltage.','CANNOT VERIFY','P0',
    'U1/U2 ADS1298; U6 ESP32; U4/U7 LDOs',
    'ADC AVDD/AVDD1 pins19/21/22/54/56/59 are on source-free +3.3VA. This confirms missing power under H2, but the floating voltage cannot be assigned a number. DVDD48/50 and U6.2 are on +3.3V relative to AGND.',
    'U1/U2 ADS1298; U3 DevKit; U4/U5 LDOs',
    'CONFIRMED V1 failure: AVDD/AVDD1 and AVSS are AGND, so analog span is 0 V. DVDD48/50 instead joins isolated DGND; U3 grounds are on that island. A valid digital supply span is also not established.',
    'v0/v1.net.xml: +3.3VA, +3.3V, AGND, DGND; embedded PAG pin tables; see Findings1/4/7/8 below.',
    f'{ADS} §§6,7.1,7.3: analog span2.7–5.25V; digital span1.65–3.6V. No valid span exists with the V1 analog pins on one net.',
    'V0 missing analog source became a V1 ground connection. CANNOT VERIFY applies to the strict before/after voltage comparison, not to the proven V1 fault. Do not call this fixed or assume V0 was0V.',
    'Implement the connection-only corrections in Findings1/7/8: separate positive supplies from ground; use valid analog/digital3.3V sources.',
    'Re-export corrected netlist; then measure each supply relative to its actual ground at U1/U2/U3. Specify battery limits before rating signoff.')
add('B1','A resistor dissipates more power than its footprint or component rating allows.','CANNOT VERIFY','UNKNOWN',
    'R3–R19/R21–R35=2kΩ; R1/R36=1MΩ; R20=10kΩ', 'No resistor power ratings, manufacturer parts or footprints specified; electrode voltages are unspecified. No demonstrated excessive resistor dissipation.',
    'R1–R32=2kΩ','Same input resistance; power ratings/parts still absent. Feedback and module-EN resistors removed with their circuits.',
    'Complete symbol properties and both connectivity exports; resistor values are explicit, ratings are not.',
    'P=V²/R or I²R; compare with actual specified resistor rating. Illustratively3.3V across2kΩ gives5.445mW; across10kΩ gives1.089mW. These are conditional, not measured operating losses.',
    'Renumbering the input resistors does not prove a power-rating improvement.','No value/component change justified. Obtain power-rated BOM parts and actual applied-voltage bounds.','Calculate worst-case loss from actual inputs/states and compare to selected part ratings.')
add('C1','Voltage across a capacitor reaches or exceeds its rating.','CANNOT VERIFY','UNKNOWN',
    'All capacitors; especially C65/C4 VCAP3','Capacitances are given, but voltage ratings and orderable parts are absent.',
    'All capacitors; especially C25/C51 VCAP3','Ratings remain absent. VCAP3 is an important check after supply correction; it is not simply a3.3V node.',
    'All capacitor properties lack voltage-rating fields. V0 U1.55→C65.1, U2.55→C4.1; V1 U1.55→C25.1, U2.55→C51.1; returns AGND.',
    f'{ADS} PAG pin55 description: VCAP3 is internally AVDD+1.9V, referenced to AVSS. At a corrected3.3V analog span this is approximately5.2V; actual capacitor rating must exceed its maximum applied voltage.',
    'VCAP capacitors retained with changed references; no demonstrated voltage-rating fix.','Get capacitor voltage ratings, actual analog/battery limits and relevant node maxima; do not change capacitance or add capacitors from this check alone.','Compare maximum pin-to-pin voltage with each selected capacitor rating. No tolerance/DC-bias-derating review performed.')
add('C2','A capacitor has a pin connected to nothing.','NOT FOUND','—',
    'C1–C73 as populated','Every drawn capacitor pin joins a net containing another component connection.',
    'C1–C57','Every drawn capacitor pin likewise joins another component connection.',
    'Both complete XML netlists: each capacitor has both pins present, with another connected component. Floating supply networks are covered separately, not mistaken for a physically unconnected pin.',
    'A connected resistor/IC terminal is a connection even if the larger network is floating.','No open capacitor terminal established in either revision.','None under C2.','Connectivity check completed; inspect C3/H2 separately for invalid returns/sources.')
add('C3','A decoupling capacitor has a floating ground connection.','NEW IN V1','P0',
    'C20/C21/C71/C72 and other return capacitors','All capacitor returns that are drawn as ground connect to the battery-negative AGND/GND net.',
    'C8=0.1µF, C9=10µF, C34=0.1µF, C35=10µF',
    'Each pin1 is +3.3V; pin2 is isolated DGND. That net has no valid battery/regulator ground connection. This is the same return-network defect as H1, not four separate faults.',
    'v1.net.xml: DGND includes these four pin2 terminals and U3 grounds, but excludes BT1.2/U4.2/U5.2; V0 counterparts return to AGND.',
    'Decoupling must connect between the supplied rail and its receiving circuit’s valid return; ADS actual DGND33/49/51 is AGND here.',
    'The return symbols changed electrically: V0 returns were valid; V1 returns land on a separate net.',
    'First remove ADC DVDD48/50 from DGND and connect them to digital3.3V. Then join genuine DGND returns to battery/regulator ground; retain these capacitor values.',
    'Netlist must place capacitor pin2, MCU ground and BT1.2 on one return net, with ADC DVDD separate; measure rail across each capacitor after correction.')
add('C4','A voltage regulator has insufficient output capacitance.','NOT FOUND','—',
    'U4/C44=2.2µF; U7/C46=200µF','Both regulators have nominal output capacitance meeting their stated minimums.',
    'U4/C54=2.2µF; U5/C57=200µF','Same nominal values; no minimum-capacitance shortfall demonstrated.',
    'C44/C54 pin1→U4.5; C46/C57 pin1→U7.5/U5.5; all pin2→AGND. Presently both outputs share +3.3V.',
    f'{LP} §6.3/§7.1.2: legacy minimum2.2µF (new-chip requirements differ); {TLV} pin table/§7.1.1:1µF nominal recommended, with at least0.47µF effective for stability. Drawn nominal values do not show a minimum shortfall.',
    'Capacitance unchanged; this is NOT FOUND, not FIXED. No excluded tolerance/DC-bias investigation undertaken.','Preserve each existing output capacitor on its own LDO output when separating E5; no increase justified by this check.','Connectivity/value check completed. Actual part selection/ESR remains C5; no performance certification implied.')
add('C5','A regulator requires output-capacitor ESR but uses only unsuitable ceramic capacitors.','CANNOT VERIFY','UNKNOWN',
    'U4/C44; U7/C46','Capacitor technology/ESR and exact LP2985 orderable chip identity are absent.',
    'U4/C54; U5/C57','Same limitation; a generic unpolarized capacitor symbol does not establish ceramic technology or ESR.',
    'No capacitor manufacturer, technology or ESR properties. U4 is only LP2985-3.3, without complete orderable suffix.',
    f'{LP} §§7.1.1–7.1.2 distinguish legacy stability/ESR requirements and a new ceramic-stable chip; {TLV} supports ceramic output capacitors. ESR is the small effective resistance in series with a real capacitor.',
    'No evidence either revision used only unsuitable ceramics; do not infer an ESR fix from renumbering.','Identify U4 generation and capacitor parts; compare the complete output network to that chip’s stability requirements. Add resistance/change parts only if this demonstrates a mismatch.','BOM/part-marking check and ESR-versus-temperature/frequency specifications; stability measurement only if still uncertain.')
add('C6','Missing or insufficient decoupling causes a rail dip greater than5%.','CANNOT VERIFY','UNKNOWN',
    'ADC decoupling; C44/C46/C47/C48; U6','Capacitors exist; missing analog source is H2. No transient evidence establishes a greater-than5% dip.',
    'ADC decoupling; C54/C57; U3','Four invalid capacitor returns are confirmed under C3. No rail waveform establishes dip magnitude.',
    'Supply capacitors in both exports; no load-step waveform, supply impedance or validated transient model supplied.',
    '5% of3.3V=0.165V. A static wiring defect does not specify a time-varying voltage dip.',
    'V1 return error worsens supply integrity, but a numerical droop cannot be fabricated.','Correct C3/H1/H2/E5/E6 first; do not add bulk capacitance without a demonstrated transient need.','Measure rail-to-local-ground during startup and intended peak loads, with actual battery/source impedance; compare droop with165mV.')
add('C7','A capacitive load makes an amplifier unstable.','CANNOT VERIFY','UNKNOWN',
    'U1 RLDOUT63; R36=1MΩ/C73=1.5nF; J1','Output electrode/cable load and enabled RLD settings are unknown. Feedback capacitance is not proof of an unstable load.',
    'U1/U2 internal RLD/PGA/PACE','External RLD feedback/electrode output networks removed; no external amplifier output load is drawn. No instability demonstrated.',
    'V0 U1.63→R36/C73/J1; V1 RLDOUT63 NC. V0 U2.63 also NC, despite a schematic note about a PCB connection.',
    f'{ADS} RLD/optional-output sections apply only to the enabled configuration and actual load.','Removing an optional circuit does not prove that a demonstrated instability was corrected.','No compensation component change justified; obtain actual enabled-loop and load information.','After valid supplies, simulate the actual enabled loop with cable/electrode model or measure step/ringing response; V1 external-load case is absent.')
add('D1','An LED has no suitable current limitation.','NOT FOUND','—',
    'No LED in V0 schematic','No relevant LED circuit in the module carrier.',
    'U3 reference-board D5/R11 and D6','Official DevKit reference power LED D5 has R11=5.1kΩ; RGB D6 is a smart LED with internal driver. No missing external current limiter found.',
    'V0 complete symbol inventory; official DevKitC v1.1 sheet2 shows D5/R11 and SK68XXMINI-HS D6. Exact fitted board revision is unspecified.',
    f'{BOARD} sheet2: passive LED series resistance is present. At3.3V, even zero LED forward voltage gives3.3/5100=0.647mA through R11. D6 is not a bare LED requiring a GPIO series-current resistor.',
    'V1 introduces a board with documented LED circuits, not a demonstrated LED fault.','None supported. Confirm fitted board if it differs from the official reference.','Reference-board schematic check completed; inspect actual board documentation if variant differs.')
add('D2','An LED is driven directly into an open-collector sink causing incorrect operation/excessive current.','NOT APPLICABLE','—',
    'None','No LED/open-collector arrangement.', 'U3 reference-board LEDs','No such direct LED/open-collector arrangement is shown in the carrier or reference board.',
    'Complete carrier inventories and official board schematic.','No applicable LED sink arrangement.','No relevant arrangement introduced.','None.','No further check under this condition.')
add('E1','Regulator input voltage exceeds the maximum rating.','CANNOT VERIFY','UNKNOWN',
    'BT1; U4.1/U7.1','Both inputs are labelled +3.7V, below their limits nominally; actual BT1 maximum is unspecified.',
    'BT1; U4.1/U5.1; U3 onboard LDO','Same external source; fitted board and its USB/header use are unspecified.',
    'BT1 has only generic Battery value; no chemistry, cell count, charger, cutoff or min/max specification.',
    f'{LP} input recommended maximum16V; {TLV} recommended maximum5.5V, absolute maximum6V. The rail name alone cannot establish worst-case voltage.',
    'No nominal overvoltage shown and no demonstrated input-rating fix.','Specify maximum source/charger voltage; change parts only if actual range exceeds limits.','Compare maximum loaded/unloaded source voltage, including charging if applicable, against actual fitted regulator ratings.')
add('E2','A regulator enters dropout during expected operation.','CANNOT VERIFY','UNKNOWN',
    'U4 LP2985-3.3; U7 TLV75533PDBV','Battery minimum under load and actual regulator current sharing unknown.',
    'U4; U5 TLV75533PDBV','Same nominal voltages, same missing operating-range data; current-sharing error remains E5.',
    'Both inputs +3.7V, both nominal outputs3.3V: labelled headroom3.7−3.3=0.400V. See calculation below.',
    f'{LP} electrical table and {TLV} §5.5 specify load/temperature-dependent dropout. Dropout is the extra input voltage required above the output to maintain regulation.',
    'Neither voltage label nor reference change demonstrates adequate headroom across battery discharge.','Get minimum battery voltage, cutoff, load and chip identity; check headroom before selecting any replacement regulator or converter.','Use VIN(min,loaded)≥VOUT(max)+VDO(max at actual load/temperature), then measure near battery cutoff.')
add('E3','A regulator is disabled by its own enable arrangement or remains latched off.','CANNOT VERIFY','UNKNOWN',
    'U4.3/U7.3 /EN','Undriven shared enable is confirmed under E6; its actual voltage/off state is not known. No self-output dependency is drawn.',
    'U4.3/U5.3 /EN','Same; no proven latch-off sequence or self-powered enable arrangement.',
    '/EN contains only the two enable inputs in each revision. It does not connect to either output rail, MCU EN or a power-good output.',
    f'{LP} and {TLV} enable requirements apply. An undriven input does not establish a specific measured low state or latch behavior.',
    'E6 persists; do not count an imagined latched-off waveform as another verified fault.','Correct E6 with a defined always-on connection or specified shutdown controller.','Measure EN and both outputs through cold start/power cycling after wiring corrections; no latch claim without a waveform.')
add('E4','Regulator output voltage does not match the voltage indicated by its rail name.','NOT FOUND','—',
    'U4.5/U7.5','Both3.3V fixed-output types drive +3.3V.', 'U4.5/U5.5','Both3.3V fixed-output types still drive +3.3V.',
    'Exact component values LP2985-3.3 and TLV75533PDBV; exported output net +3.3V.',
    f'{LP}/{TLV} fixed-output part identities.','Missing V0 +3.3VA source and grounded V1 AVDD are supply wiring faults, not mismatched LDO setpoints.','None under E4; fix H2/A1 separately.','Part-identity/net-name check completed.')
add('E5','Two regulator outputs drive the same rail.','STILL PRESENT','P1',
    'U4.5 LP2985; U7.5 TLV75533','Both output pins directly share +3.3V.',
    'U4.5 LP2985; U5.5 TLV75533','Same direct parallel outputs. Reference DevKit onboard LDO can additionally drive the header rail if USB/5V powers it; that use is unverified.',
    'Both netlists +3.3V; both ERC reports explicitly flag the two LDO power outputs. V1 U3.1/.2 also +3.3V.',
    f'{PAR}: independent regulator references require a deliberate sharing arrangement. Directly tying these outputs provides no specified current sharing; do not add150mA+500mA as an available rating.',
    'U7→U5 is renumbering; topology did not change. No measured oscillation, damage or particular overload is claimed.',
    'Separate existing outputs: U4.5 plus C54 to analog +3.3VA; U5.5 plus C57 to digital/MCU +3.3V. Use one approved DevKit supply mode; no added mux or sharing circuit needed.',
    'Corrected netlist must separate U4.5/U5.5 and assign intended loads/caps; check each load budget and board supply mode; repeat targeted ERC.')
add('E6','Regulator enable input floats or depends incorrectly on another rail’s power-good.','STILL PRESENT','P1',
    'U4.3/U7.3 /EN','Only these two input pins occupy /EN; there is no driver, pull or switch.',
    'U4.3/U5.3 /EN','Exactly the same omission; no power-good output is present.',
    'Netlists /EN pin memberships; ERC undriven U4.3. Module U6.3 EN is a different net.',
    f'{LP} ON/OFF must be terminated; {TLV} EN needs a valid level. Neither diagram provides one.',
    'Moving and renumbering regulators did not add an enable source.','For always-on operation, connect both enable pin3 inputs directly to their common input +3.7V (pin1 supply), subject to specified source range. No resistor needed. If shutdown is required, define its source/default first.','Netlist /EN must include the intended driver/input supply; measure enables and outputs at startup.')
add('E7','A switching regulator directly supplies an analog IC with potentially unacceptable noise.','NOT APPLICABLE','—',
    'U4/U7','Both explicit regulators are linear LDOs.', 'U4/U5/U3 reference onboard regulator','Linear LDO supply path; no switching regulator shown.',
    'Complete power-component inventory; manufacturer identities and official DevKit schematic.',
    'No switching-regulator arrangement to evaluate.','No applicable switching regulator introduced.','None; no independent analog-noise/layout investigation.','No additional check under E7.')
add('E8','A regulator cannot sink current when a required output-setpoint change occurs.','NOT APPLICABLE','—',
    'U4/U7','Fixed3.3V parts; no output-setpoint switching.', 'U4/U5','Same fixed outputs; no required setpoint-lowering transition.',
    'No feedback-programming circuit or switched setpoint in either full schematic.',
    'No required setpoint transition to evaluate. TLV active discharge is not evidence of such a system requirement.','No applicable arrangement.','None.','No additional check under E8.')
add('E9','A control/signal voltage rises before the receiver supply is valid.','CANNOT VERIFY','UNKNOWN',
    'U6→U1/U2 control nets','No ramp or pre-firmware waveform; analog rail is source-free.',
    'U3→U1/U2 controls; TEST/PACE17/18 and RLDIN62','No measured ordering. Separately, V1 hard-ties unused analog pins to +3.3V while AVDD is grounded: a confirmed static overvoltage if3.3V is on, described in Finding1. It is not an invented ramp.',
    '/PWDN,/RESET,/START,/CS*,MOSI,SCLK; v1 analog pins17/18/62 on +3.3V vs AVDD on AGND.',
    f'{ADS} §11.1: keep digital inputs low until supplies stabilize. Analog input bound §7.1 is AVDD+0.3V; with grounded AVDD, intended3.3V exceeds0.3V.',
    'Supply/control wiring changed, but actual event order is not supplied. Static analog-pin hazard uses the same AVDD repair, not another independent count.','Correct supply wiring and move unused analog pin ties to the corrected analog rail; define reset defaults and firmware release order.','Scope AVDD/DVDD/controls through cold start, MCU reset and intended external-board power modes; inspect firmware initialization.')
add('F1','Amplifier supply span exceeds or falls below its allowed limits.','CANNOT VERIFY','P0',
    'U1/U2 internal PGA/RLD','Analog supply has no valid source; numeric voltage on +3.3VA unknown.',
    'U1/U2 internal PGA/RLD','CONFIRMED V1: amplifier analog supply span0V because AVDD and AVSS share AGND.',
    'Same exact supply pins as A1/H2; no separate external op-amp exists.',
    f'{ADS} supply ratings apply to its internal analog circuits.','Strict comparison cannot assign V0 a voltage; V1 failure is confirmed. Same root as H2, not an additional amplifier defect.','Fix the analog supply in Finding1; no amplifier replacement.','Check corrected span/netlist, then measure AVDD−AVSS against the2.7–5.25V operating range.')
add('F2','Amplifier positive/negative supply pins are reversed.','NOT FOUND','—',
    'U1/U2 internal analog circuits','AVSS is grounded; AVDD is source-free, not shown connected to a negative source.',
    'U1/U2 internal analog circuits','AVDD and AVSS are the same net. This is zero span, not reversed polarity.',
    'PAG supply pin definitions and both netlists.','A reversed supply requires positive supply below negative supply; no such deliberate connection established.','Do not relabel A1/H2 as reversed supplies.','None under F2; correct A1/H2.','Pin polarity check completed; power fault remains independently verified.')
add('F3','Amplifier input is outside its common-mode range.','CANNOT VERIFY','UNKNOWN',
    'U1/U2 input pairs and optional RLD','Electrode common-mode/DC offsets and enabled bias configuration unknown.',
    'U1/U2 input pairs; RLD circuit removed','No external bias source shown, but this alone does not prove the electrodes’ actual common-mode voltage is invalid.',
    'Input pin pairs16/15,14/13,12/11,10/9,8/7,6/5,4/3,2/1;2kΩ/620pF networks unchanged. RLD changes mapped below.',
    f'{ADS} §9.3.1.5.1 equation2 gives PGA common-mode limits; §9.3.1.5.2 equation3 gives differential range. Common-mode means the average (INP+INN)/2; it differs from the small differential EMG signal.',
    'Removing RLD is an electrical change, but is not proof that a measured common-mode fault exists or was fixed. Invalid supplies must be corrected first.','No independent bias/RLD redesign justified. Obtain actual source model, offsets, gain/reference/lead-off/RLD settings.','Measure input average and difference relative to actual chip ground; compare to the programmed gain/reference and datasheet limits after supply repair.')
add('F4','Amplifier oscillates/rings because of inadequate stability or phase margin.','CANNOT VERIFY','UNKNOWN',
    'U1 RLD loop; internal amplifiers','No loop model or measured response;1MΩ∥1.5nF feedback does not certify or disprove stability.',
    'U1/U2 optional internal amplifiers','External RLD loop removed; enabled states unknown. Unconnected feedback on a disabled optional amplifier is not proof of oscillation.',
    'V0 R36/C73 and R1/C1; V1 RLDINV61/RLDOUT63 NC. No simulation or waveform supplied.',
    f'{ADS} RLD sections apply to actual enabled loop/load; phase margin is the stability reserve of a feedback loop.','No demonstrated oscillation in either revision; do not call deletion a verified fix.','No compensation change without actual loop/load evidence.','For an enabled loop, simulate its real load or measure ringing/oscillation after correcting supplies; V1 drawn external RLD loop is absent.')
add('F5','Amplifier output is clipped, saturated or overloaded.','CANNOT VERIFY','UNKNOWN',
    'U1/U2 PGA and RLD','Actual input magnitude/DC offset, gain/reference, RLD enable and load unknown.',
    'U1/U2 PGA and optional outputs','Same missing acquisition configuration/source data. The confirmed supply fault already prevents valid operation; it does not specify an output waveform.',
    'Input/output netlists and absence of firmware/source/load data.',
    f'{ADS} §7.3 differential full scale±VREF/gain and §9.3.1.5.1 PGA headroom apply to validly powered operation.','No separate clipping or overload fault proven; no fix credited.','Repair supply wiring, obtain configuration and inputs; change gain/bias/load only if limits are exceeded.','Measure or calculate PGA input/output headroom with actual DC offsets and configured gain/reference; measure any enabled external output load.')
gconditions = {
    'G1':'Power multiplexer output remains off.', 'G2':'Priority input is never used.',
    'G3':'A power-multiplexer input is rejected incorrectly.', 'G4':'Expected power-multiplexer failover does not work.',
    'G5':'A power-multiplexer control pin floats.', 'G6':'A power-multiplexer input is disconnected.',
    'G7':'Power-multiplexer output rail specifies a voltage no input can provide.'}
for id, condition in gconditions.items():
    add(id,condition,'NOT APPLICABLE','—','None','No power multiplexer.','None','No power multiplexer.',
        'Complete component inventories; two external linear LDOs are not a power multiplexer. DevKit USB diodes do not create the described controlled-priority mux.',
        'No relevant multiplexer requirement.','No mux introduced.','None; no additional mux architecture is justified.','Not applicable.')
add('H1','An IC has no valid ground connection.','NEW IN V1','P0',
    'U1/U2; U6; U4/U7','Actual ADC DGND33/49/51, AVSS, MCU GND1/40/41 and LDO GND2 all connect to BT1.2 on AGND/GND. The separately named DGND control island is not an actual V0 IC supply-ground connection.',
    'U3 GND22/23/24/44; U1/U2 ground pins','U3 grounds connect only to isolated DGND, while BT1.2/LDO grounds and actual ADC grounds remain AGND. No valid controller DC return.',
    'Both netlists AGND/DGND memberships; raw V1 ground-box tie(36.83,267.97)→(48.26,267.97)mm joins AGND and GND only, not DGND.',
    f'{BOARD}/{MOD}: supply must be referenced to actual board/module ground. A symbol named DGND does not automatically join AGND.',
    'V1 moves the controller return onto a previously isolated control-reference net. It also moves four decoupler returns there (C3).',
    'After moving misplaced ADC DVDD pins off DGND, connect genuine MCU/digital returns to BT1.2/U4.2/U5.2 common ground. No isolated-ground architecture needed.',
    'Netlist continuity from every genuine IC ground to BT1.2, excluding positive supplies; measure U3 supply between its3V3 and GND headers after correction.')
add('H2','A power rail is disconnected from all valid sources.','STILL PRESENT','P0',
    'U1/U2 +3.3VA','Analog rail contains only ADC positive-supply pins and decouplers; no battery/regulator output.',
    'U1/U2 AVDD/AVDD1 and DVDD','Analog positive supply now grounded instead of reaching a positive source; digital positive supplies also moved off +3.3V to isolated DGND.',
    'v0.net.xml +3.3VA members; v1.net.xml AGND/DGND. ADC AVDD19/21/22/54/56/59; DVDD48/50.',
    f'{ADS} requires valid positive analog/digital supplies, not merely similarly named capacitor buses.',
    'Analog power remains invalid and is worsened by a direct ground tie; separate V1 digital-supply error is Finding7.','Connect ADC analog positives to the separated U4 analog output, digital positives to U5 digital output; preserve actual ground pins.','Re-export pin-to-net membership; ensure each positive supply has exactly the intended source, then verify DC rail spans.')
add('I1','Logic voltage is too low/high for the receiving component.','CANNOT VERIFY','UNKNOWN',
    'U6↔U1/U2; floating DGND straps','At nominal common3.3V, normal SPI/DRDY thresholds are compatible. DGND control island has no guaranteed logic-low reference (J3).',
    'U3↔U1/U2','No valid digital supply/reference due to DVDD and ground errors. Actual voltages on that island cannot be calculated from its name.',
    'V0 valid interface nets +3.3V/AGND; V1 DVDD→DGND, actual ADC DGND→AGND and U3 GND→DGND. Logic comparison table below.',
    f'{ADS} digital thresholds; {ESP} DC levels. Compatibility at limits is not proof of a measured voltage violation or adequate dynamic margin.',
    '3.3V digital interfaces were not inherently incompatible; V1 introduces supply/reference faults, already counted separately.','Correct supplies/grounds and low-level straps first. No level shifter justified by nominal3.3V interfaces alone.','Measure actual transmitter VOH/VOL at receiver pins versus local supply/ground and VIH/VIL; verify configured direction/drive.')
add('I2','A digital signal edge is too slow for its interface.','CANNOT VERIFY','UNKNOWN',
    'SPI/START/RESET/DRDY','No measured edge rate or total load supplied; no large external RC on SPI nets.',
    'Same; shared MISO','Changed pin mapping/bus loads do not establish an edge-rate violation.',
    'Digital netlists; no timing waveform, trace/cable load or firmware clock-rate specification.',
    f'{ADS} serial timing requirements apply; SCLK has a Schmitt input (§9.5.1.2).','No demonstrated slow edge fixed or introduced. A missing clock is not a slow edge.','No series/parallel component change supported.','Scope actual edges at receiver under selected SPI speed/load; compare to datasheet timing. No separate general signal-integrity review.')
add('I3','An open-drain signal lacks a pull-up or has an excessively strong pull-up.','NOT FOUND','—',
    'U1/U2 DOUT43 and DRDY47','These are driven outputs, not open-drain lines needing generic pull-ups. No power-good line exists.',
    'U1/U2 DOUT/DRDY; U3 reference reset circuitry','ADC signals remain driven outputs. Official board reset/autoprogram sinks have a documented10kΩ CHIP_PU pull-up; no missing relevant pull-up found.',
    'ADS pin/interface definitions; reference-board R5=10kΩ on CHIP_PU. No carrier open-drain interface appears.',
    f'{ADS} digital-output definitions and {BOARD} reset circuit.','No demonstrated open-drain pull fault. Do not add a DRDY pull-up by habit.','None supported. Excluded general sink-capability review not undertaken.','Interface-type and reference-board pull-up check completed; fitted board variant still to confirm.')
add('I4','ADC source impedance/settling prevents valid acquisition.','CANNOT VERIFY','UNKNOWN',
    'U1/U2 input2kΩ/620pF networks','Actual electrode impedance versus frequency and data-rate/gain/settling requirements absent.',
    'U1/U2 R1–R32 and input620pF caps','Same electrical filter values; no demonstrated acquisition fault from the drawn series resistors.',
    'All16 differential pairs have2kΩ on each lead and620pF to AGND at ADC side. See filter calculation and mapping below.',
    f'{ADS} CMOS PGA inputs precede delta-sigma conversion; do not apply a generic SAR sample-capacitor acquisition model.',
    'Filter renumbering is not a fix. Source/load and selected digital-filter settling remain unknown.','No added buffer or resistor/capacitor change justified.','Obtain actual electrode source model, gain/data-rate and valid-settling criterion; apply a representative input step and check settled output after supplies/clocks are repaired.')
add('I5','A slow signal enters a non-hysteretic input or crosses threshold repeatedly.','CANNOT VERIFY','UNKNOWN',
    'Control inputs; U6 EN RC','No signal waveform demonstrating a slow/chattering crossing. Module EN has its RC network.',
    'Control inputs; U3 internal reset RC','Reference board has built-in EN/reset network; no measured repeated crossings. ADC clock omission is not proof of chatter.',
    'No threshold-crossing waveform or noise amplitude supplied; SCLK explicitly has hysteresis in ADS documentation.',
    f'{ADS} §9.5.1.2 identifies SCLK Schmitt hysteresis (different rising/falling thresholds). Other control waveforms must be checked individually.',
    'Moving the EN RC inside the development board does not show its removal.','No Schmitt buffer or RC change justified without waveform evidence.','Measure relevant slow control/enable ramps and compare input hysteresis/threshold requirements for the actual component.')
add('J1','A boot-strapping pin floats or is held at the wrong level.','CANNOT VERIFY','UNKNOWN',
    'U6 GPIO0 pin27; GPIO3 pin15; GPIO45 pin26; GPIO46 pin16','GPIO0/45/46 have defined internal default pulls. GPIO3 has no pull, but its effect depends on eFuse-selected JTAG policy; normal boot failure is unproven.',
    'U3 GPIO0 pin31; GPIO3 pin13; GPIO45 pin30; GPIO46 pin14','Same strap issue; board adds normal boot/reset hardware. Required GPIO3/JTAG setting is unspecified.',
    'Both inventories, ESP strapping table, module §4.4. GPIO3 is physically floating; that observation is not proof that the application requires either level.',
    f'{MOD} boot/JTAG strapping tables: GPIO3 affects JTAG source only under relevant nondefault eFuse selection.',
    'No demonstrated boot fix or new boot fault.','Do not add a GPIO3 resistor without selecting a required debug/JTAG state. If required by eFuse policy, bias it to that chosen state.','Read eFuses and required boot/debug configuration; confirm normal cold boot. Do not mistake all unconnected GPIOs for floating boot straps.')
add('J2','A switch/enable relies only on an uncertain controller reset pull state.','STILL PRESENT','P1',
    'U6 GPIO6→U1/U2 PWDN35','ADC power-down/enable depends on a GPIO with no guaranteed reset bias; no external pull.',
    'U3 GPIO7→U1/U2 PWDN35','Same omission after GPIO remap.',
    '/PWDN net contains only GPIO and both ADC inputs; ESP reset table gives no WPU/WPD/drive on used GPIO6/7.',
    f'{ESP} Table2-1 reset states; {ADS} control input definitions/§11.1.','Controller pin changed, hardware default did not. This overlaps the reset-bias root under J3.','Add one10kΩ pulldown on shared /PWDN to valid ADC ground, as part of the reset-default correction below.','Hold controller reset and measure /PWDN before firmware; calculate leakage versus pull strength and verify startup sequence.')
add('J3','A transistor gate/regulator enable/control input floats during controller idle/reset.','PARTIALLY FIXED','P0',
    'U4/U7 EN; U1/U2 controls, CLKSEL and DGND straps','Floating LDO enable, unreferenced DGND strap island, ADC reset/start/enable GPIO nets, and CLK37 tied only to CLKSEL52.',
    'U4/U5 EN; U1/U2 controls/CLKSEL; U3','Several controls remain undefined. U1 CLKSEL now has a deliberate +3.3V tie; U2 selects external clock via isolated DGND, and its ADC_CLK has no source because U1 CLK37 is disconnected.',
    'V0 CLK/CLKSEL two-pin-only nets; V1 U1.37 NC, dangling ADC_CLK label, U2.37 sole ADC_CLK member. /EN and reset nets as above. Board U3 CHIP_PU has internal R5/C6 and is not a missing external pull fault.',
    f'{ADS} Table11 and CONFIG1: reset CLK_EN=0 makes CLK either input or tri-state, so V0 self-tie cannot bias CLKSEL. {ESP} reset defaults do not drive used ADC controls. {BOARD} provides its own EN pull/RC.',
    'A local clock-selection wiring improvement earns PARTIALLY FIXED, not FIXED; its logic level is usable only after supply repair. Other floating-control faults persist, and slave clock routing remains incomplete. Row spans Findings2/4/5/6; do not count it as one independent extra fault.',
    'Complete existing master clock connection U1.37→ADC_CLK→U2.37, keep U1 CLKSEL at digital high and U2 at valid ground, set U1 CLK_EN in firmware; define ADC reset defaults and fix /EN/DGND as below.',
    'Netlist must show both CLK37 pins on ADC_CLK. Hold MCU reset to check defaults. Initialize U1 first and enable CLK_EN; after U2 clock-valid tPOR and VCAP1 settling, reset/configure U2 through its separate CS. Shared reset would clear U1 CLK_EN. Confirm clock at both ADCs and validate the timed sequence.')
add('J4','A controller input exceeds its maximum input voltage.','CANNOT VERIFY','UNKNOWN',
    'U6 MISO20/DRDY12','Nominal3.3V ADC outputs do not show overvoltage; actual fault-state waveforms absent.',
    'U3 MISO19/DRDY15','No explicit5V GPIO connection, but controller ground is disconnected. Its input voltages relative to local ground cannot be assigned.',
    'Only U3.21 is on +5V; it is the board5V supply header, not a GPIO. ADC DOUT/DRDY nets use nominal3.3V domain.',
    f'{MOD}/{ESP} DC input limits apply relative to valid local ground; a labelled5V supply pin is not a5V GPIO drive.','No demonstrated controller input-overvoltage waveform; ground fault remains confirmed under H1.','Correct supplies/grounds; no level shifter supported from nominal net names alone.','Measure MISO/DRDY versus local MCU ground through intended startup/power modes and compare absolute/DC limits.')
add('K1','A GPIO exceeds its permitted current.','CANNOT VERIFY','UNKNOWN',
    'U6 ADC-control GPIOs; ADS GPIOs42/44/45/46','No heavy DC GPIO load shown; actual directions, drive and fault-state currents unspecified.',
    'U3 ADC-control GPIOs; ADS GPIOs42/44/45/46','Same input loads; supply errors and firmware states prevent a reliable current bound.',
    'Controller outputs drive ADC inputs; no carrier LED/resistive power load on them. ADS GPIO pins are tied to the DGND island and could contend only in an incompatible programmed state.',
    f'{ESP}/{ADS} output-current/leakage specifications require known direction/loading.','No confirmed excess GPIO-current event, and no current fix credited.','No series resistors or driver added without demonstrated current path. Correct supply wiring and inspect configuration.','Inspect firmware GPIO/ADS direction registers; calculate DC loads and measure current only for actual driven states.')
add('K2','Two output pins drive incompatible levels onto the same net.','CANNOT VERIFY','UNKNOWN',
    'U1.43 MISO; U2.43→U1.41','Daisy path keeps ADC DOUT pins on different nets. No hard two-DOUT short.',
    'U1.43/U2.43→MISO→U3.19','Shared data bus is valid with separate mutually exclusive CS. Both selected together could conflict, but that firmware/reset state is not established.',
    'V1 ERC flags output-output on MISO; U1.39=/CS_ADC1 and U2.39=/CS_ADC2 are separate. ADS GPIO strap behavior also depends on direction/configuration.',
    f'{ADS} §9.4.2.1: deselected DOUT becomes high impedance. ERC pin types cannot represent this chip-select behavior.',
    'Bus architecture changed from daisy chain to shared SPI with separate selects. This is not automatically a new contention fault.','Keep separate selects; firmware must deselect both before releasing ADC reset/power-down and select one for readback. No extra bus switch justified.','Inspect firmware and scope both CS/MISO through cold start/reset/reads. Do not assume DOUT high impedance in power-down without a specified guarantee.')
add('K3','The controller drives a component whose supply is off.','CANNOT VERIFY','UNKNOWN',
    'U6→U1/U2','Analog supply has no source, but digital supply is nominally present; no actual GPIO-high/off-state timing supplied.',
    'U3→U1/U2','Invalid ADC supply wiring is confirmed; actual controller drive states with those supplies are unknown.',
    'No firmware/state table supplied. Digital input limits reference DVDD, so do not equate missing AVDD alone with a proven digital-input clamp current.',
    f'{ADS} §7.1 digital input range and §11.1 supply sequencing.','No fabricated off-state GPIO drive or current magnitude counted.','Correct supply wiring and define valid power/control sequence; add isolation only if an unavoidable actual state demonstrates need.','Inspect firmware and capture receiver DVDD/AVDD plus control voltages during power-down/startup/reset.')
add('L1','A state change causes a supply dip or brownout reset.','CANNOT VERIFY','UNKNOWN',
    'BT1/LDOs/U6','No state-transition/current/supply waveform or source-impedance model.',
    'BT1/LDOs/U3','Same missing evidence; static supply faults do not establish a brownout event.',
    'No firmware transition states or measured rail/reset trace supplied.',
    'A brownout is a reset caused by supply voltage dropping below the controller’s operating/reset threshold. Actual threshold/configuration and waveform are required.',
    'No demonstrated state-transition brownout fixed or introduced.','Correct confirmed wiring first; no bulk-capacitance or architecture change solely from this condition.','Measure local rail and reset reason during actual peak-load/state transitions with specified battery impedance and cutoff.')
add('L2','Controller drives an input high before receiver supply is valid.','CANNOT VERIFY','UNKNOWN',
    'U6 controls→ADS1298','Reset GPIO default levels are not guaranteed; no timing capture proves a high-before-valid event.',
    'U3 controls→ADS1298','Same sequence uncertainty; supply topology itself must first be repaired.',
    'Reset-state omission is confirmed under J2/J3; it does not specify a particular transient level or timing.',
    f'{ADS} §11.1 requires digital inputs low until supplies settle.','No timing fix credited without firmware and waveform evidence.','Use defined low reset/power-down defaults, then release controls only after corrected supplies are valid.','Scope controls, AVDD/DVDD and MCU reset during cold start/restart/power cycling; inspect initialization code.')

def readable(s):
    """Space prose quantities without changing exact nets, MPNs, IDs or links."""
    protected=[]
    def protect(m):
        protected.append(m.group(0)); return f'@@PROTECTED_{len(protected)-1}@@'
    s=re.sub(r'https?://[^\s)]+|(?<=\]\()[^)\n]+(?=\))|`[^`]+`|(?<![\w])\+(?:3\.3VA|3\.3V|3\.7V|5V)\b',protect,s)
    s=s.replace('A10kΩ','A 10kΩ').replace('CLI10','CLI 10').replace('PAG64-pin','PAG 64-pin')
    s=re.sub(r'\b(At|at|In|in|To|to|Of|of|a)(?=\d)',r'\1 ',s)
    s=re.sub(r'\b(?!v(?=\d))([A-Z]?[a-z]{2,})(?=\d)',r'\1 ',s)
    s=re.sub(r'\bp(?=\d)',r'p ',s)
    s=re.sub(r'(?<=\d)(?=(?:µF|nF|pF|kΩ|MΩ|Ω|mA|µA|nA|mV|µV|V|mW|kHz|MHz|µs|ms|mm)\b)',' ',s)
    for i,p in enumerate(protected): s=s.replace(f'@@PROTECTED_{i}@@',p)
    return s

for row in rows:
    for field in row:
        if field not in ['ID','Category','Classification','Priority']:
            row[field]=row[field].replace('Findings1/4/7/8 below','Findings1/4/7/8 above').replace('See calculation below.','See the dropout calculation above.').replace('RLD changes mapped below.','See the RLD mapping above.').replace('Logic comparison table below.','See the logic comparison table above.').replace('filter calculation and mapping below.','filter calculation and mapping above.').replace('reset-default correction below.','reset-default correction in Finding5.').replace('fix /EN/DGND as below.','fix /EN/DGND in Findings2/4.').replace('GPIOs42/44/45/46','GPIO pins42/44/45/46')
            row[field]=readable(row[field])

expected = [f'{c}{i}' for c,n in zip('ABCDEFGHIJKL',[1,1,7,2,9,5,7,2,5,4,3,2]) for i in range(1,n+1)]
assert [r['ID'] for r in rows] == expected
columns = ['ID','Category','Ambrflow_condition','V0_component','V0_finding','V1_component','V1_finding','Classification','Priority','Evidence','Recommended_fix','Verification_needed']
with Path('AMBRFLOW_ISSUE_MATRIX.csv').open('w', newline='') as f:
    writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
Path('EVIDENCE/condition_findings.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
counts=Counter(r['Classification'] for r in rows)
print('Condition classification counts:',dict(counts))

intro = '''# Open-sEMG-16 — Ambrflow electrical feedback audit

**Audit date:** 28 October 2026. **Scope:** only the48 supplied Ambrflow conditions, applied to the two active schematics. Both complete files and embedded pin definitions were parsed and reviewed; each is a single sheet with no hierarchical sheets. `.history` and backup snapshots were not used as active designs. No source project or circuit was modified; proposed changes below are instructions only.

## Overall result and counting

There are **six confirmed V0 wiring/control problems** within scope: **zero fully fixed, one partially fixed, five still present**. V1 adds **two distinct supply/return wiring problems**. Thus **eight distinct problems need a correction or completion in V1**. This is a count of the specific arrangements in Findings1–8 below, not of hypothetical failure modes or duplicated checklist entries. The new AVDD ground tie worsens the existing analog-power problem; it is not counted again as a separate V1 problem. The V1 DVDD error and disconnected controller return require different corrections and are counted separately, even though they touch the same DGND net.

**25 condition comparisons are CANNOT VERIFY.** A1 and F1 are special: V1’s zero analog supply is confirmed, but V0’s actual floating voltage cannot be calculated. Their before/after *voltage* comparison is uncertain; the underlying missing valid analog supply is already a confirmed V0 problem under H2. None of these uncertain entries is credited as a fix.

| Count basis | Fixed | Partially fixed | Still present | New in V1 | Cannot verify | Not found | Not applicable |
|---|---:|---:|---:|---:|---:|---:|---:|
| Distinct wiring/control problems |0|1|5|2|Not counted as confirmed problems|—|—|
|48 checklist rows |0|1|4|2|25|6|10|

The checklist-row counts differ because several rows describe the same wiring problem, and J3 covers several control arrangements. A valid local improvement is recorded without claiming the entire condition was cleared. Passing ERC would not prove functionality; its counts are not issue counts or completion percentages.

## Evidence and limits

V0 source: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/Archive/electronics-archive/open-semg-16-electronics-v0/open-semg-16.kicad_sch`.

V1 source: `/Users/home/Documents/Projects/Hardware/sEMG-Hardware/open-semg-16-v1/open-semg-16-v1.kicad_sch`.

KiCad CLI10.0.7 exported XML netlists, SVG schematics and all-severity ERC JSON into `EVIDENCE/`. Reports: [V0 connectivity](EVIDENCE/v0.connectivity.txt), [V1 connectivity](EVIDENCE/v1.connectivity.txt), [V0 ERC](EVIDENCE/v0.erc_summary.txt), [V1 ERC](EVIDENCE/v1.erc_summary.txt). Complete parsed inventories retain component properties, embedded pin types, positions, wires, labels, junctions, notes and no-connect markers. [Source manifest](EVIDENCE/source_manifest.json) records source hashes and sheet counts.

ERC produced62 V0 and65 V1 messages, including unused/unconnected pins and electrical-type/model warnings. Both runs completed. V0 netlist export warned of annotation errors: two placed reference-electrode symbols are both J1. This limits unambiguous connector-instance naming in the optional RLD path; it does not affect the traced ADC/LDO supply nets. No connector-count or footprint review was performed. Fontconfig printed a missing-default-config warning; netlist/ERC/SVG files were generated successfully.

Relevant ERC corroboration: both revisions flag undriven U4 enable and parallel LDO outputs. V1 flags U1 CLK37 unconnected and ADC_CLK label dangling. V1 shared MISO output-type warning is not proof of contention; the ADS output can tri-state. Likewise, DevKit external CHIP_PU warning does not model its internal reset network. Generic ground labels can hide serious errors that ERC does not diagnose as intended-voltage failures.

No battery operating range, complete power/voltage-rated passive BOM, firmware, source/electrode model or measured/simulated transient response was supplied with these schematic sources. A brownout is a supply drop that triggers controller reset. The nominal `+3.7V` label does not specify battery chemistry, cell count, charging voltage or cutoff. V0’s represented controller is a **WROOM-1 module**, not a DevKit. V1 represents **ESP32-S3-DevKitC**; its precise board revision and module suffix are unspecified. Official DevKitC-1 v1.1 is used as the documented internal-circuit reference; confirm the installed board matches before relying on board-specific details.

## Circuit understanding and equivalent parts

Each revision has two TI ADS1298 ADCs, each with eight differential electrode inputs, internal programmable-gain amplifiers (PGAs), delta-sigma converters, optional RLD circuitry, reference pins and digital control/SPI pins. `ADS1298xPAG` specifies the PAG64-pin TQFP family; the `x` is not a complete orderable grade/packing suffix. Both embedded ADS pin definitions agree with the manufacturer’s PAG supply/input/digital pin numbers. Pin18 is labelled TESTP_PACE_OUT2 in the symbol but is TESTN_PACE_OUT2 in TI’s table; analysis follows pin number18.

| Function | V0 reference/value | V1 reference/value | Electrical comparison |
|---|---|---|---|
| ADCs | U1/U2 ADS1298xPAG | U1/U2 same | Same acquisition devices; supply wiring changed substantially |
| Analog-intended LDO | U4 LP2985-3.3 | U4 same | Exact LP orderable/chip generation absent; output still wrongly shared |
| Digital-intended LDO | U7 TLV75533PDBV | U5 same | TI fixed3.3V, DBV5-pin; rename is not a fix |
| Controller | U6 ESP32-S3-WROOM-1 | U3 ESP32-S3-DevKitC | Module→board; account for board’s existing EN/reset/LDO circuitry |
| Battery | BT1, generic Battery | BT1 same | Both labelled +3.7V; actual range unspecified |
| U1 eight input pairs | E17–E24; R3,R21–R35 | E1–E8; R1–R16 | Resistor sequence maps in pin order; all2kΩ |
| U2 eight input pairs | E1–E8; R4–R19 | E9–E16; R17–R32 | All2kΩ, same input topology |
| U1 input capacitors | C13,C14,C15,C50–C62 | C1–C5,C10–C18,C21,C22 | Per-lead620pF to AGND, unchanged electrically |
| U2 input capacitors | C26–C41 | C27–C31,C36–C44,C47,C48 | Per-lead620pF to AGND; match by ADS pin, not consecutive cap number |
| U1 VCAP1/2/3/4 | C63/C64/C65/C66 | C23/C24/C25/C26 |22µF/1µF/1µF/1µF retained |
| U2 VCAP1/2/3/4 | C2/C3/C4/C5 | C49/C50/C51/C52 | Same values retained |
| U1 VREFP bypass | C67/C68 | C19/C20 |0.1µF/10µF retained |
| U2 VREFP bypass | C17/C11 | C45/C46 |0.1µF/10µF retained |
| U1 analog/digital bypass | C69/C70; C71/C72 | C6/C7; C8/C9 |0.1µF/10µF per rail; V1 pins wired to return rows |
| U2 analog/digital bypass | C18/C19; C20/C21 | C32/C33; C34/C35 | Same values, same V1 wiring error |
| LP input/output/bypass | C43/C44/C42 | C53/C54/C55 |1µF/2.2µF/10nF retained |
| TLV input/output | C45/C46 | C56/C57 |1µF/200µF retained |
| Module supply/EN | C47=22µF,C48=0.1µF; R20=10kΩ,C49=1µF | Inside U3 reference board | External network removal is not evidence of lost EN pull-up |
| Optional RLD feedback | U1 R36/C73; U2 R1/C1; two J1 instances | Removed |1MΩ∥1.5nF; no independent bias/safety redesign investigated |

Reference changes were matched by device pins, net membership, values and circuit role. See the complete inventories for every passive component and the digital evidence file for the full GPIO remap.

| Digital function | V0 module pin / GPIO | V1 board symbol pin / GPIO | ADC pins |
|---|---|---|---|
| Chip select | U6.5/GPIO5, shared /CS | U3.16/GPIO10→/CS_ADC1; U3.20/GPIO14→/CS_ADC2 |39 each |
| Power down | U6.6/GPIO6 | U3.7/GPIO7 |35 each |
| Reset | U6.7/GPIO7 | U3.6/GPIO6 |36 each |
| START | U6.23/GPIO21 | U3.12/GPIO8 |38 each |
| MOSI | U6.19/GPIO11 | U3.17/GPIO11 |34 each |
| SCLK | U6.21/GPIO13 | U3.18/GPIO12 |40 each |
| MISO | U6.20/GPIO12 from U1; U2 DOUT→U1 DAISY_IN | U3.19/GPIO13 from both DOUTs |43; V0 chain input U1.41 |
| DRDY | U6.12/GPIO8 | U3.15/GPIO9 |U1.47; U2.47 unused in both |

## Remaining findings and exact proposed KiCad corrections

These are eight distinct arrangements, grouped here to avoid counting repeated checklist consequences. No changes have been implemented. P0 means a verified operating blocker or damage risk; P1 means verified potential unreliability. Unmeasured timing/analogue behavior remains UNKNOWN even when the responsible wiring omission is certain.

### Finding1 — Analog positive supply has no valid source (STILL PRESENT, P0; H2, with A1/F1 consequences)

**What is wrong / why it matters:** V0’s `+3.3VA` is a source-free island; its exact voltage is unknown. V1 instead connects every ADC analog positive supply to the battery-negative net. Thus `AVDD−AVSS=0V` by connectivity, below the minimum operating span. The PGAs and converters cannot perform valid acquisition with this supply connection. In V1, unused analog pins17/18/62 are tied to `+3.3V` while AVDD is grounded; when the intended3.3V rail is on, those pins exceed `AVDD+0.3V`. This creates a potential damage path; its current is not known.

**Where:** both U1/U2 AVDD19/21/22/56/59 and AVDD1.54; negative AVSS20/23/32/57/58 and AVSS1.53. V0 positives→`+3.3VA`; V1 positives and negatives→`AGND`. U1 V1 supply endpoints around(172.72/177.8,101.6)mm run to y93.98 capacitor-return bus, not y86.36 positive bus. U2 repeats the error. A nearby AVDD label on the capacitor top does not power the IC pin connected to its bottom.

**Exactly change in KiCad:** remove these positive-supply connections from the ground rows. With Finding3’s rail split, connect them to U4.5’s dedicated `+3.3VA`. Put the supply side(pin1) of C6/C7/C32/C33 on that same analog rail. Keep AVSS and those capacitors’ pin2 on valid ground. Connect unused TEST/PACE17/18 and RLDIN62 to this corrected analog rail, following TI’s unused-analog-pin instruction; do not leave them on a separately sequenced digital rail. Keep U1 CLKSEL on the digital logic rail.

**Verify:** netlist must separate all analog positives from AVSS and include U4.5 as their source. Measure span at both ADCs before acquisition; check unused analog-pin voltages against the restored AVDD. No new regulator, buffer or capacitor is justified by this fault.

### Finding2 — LDO enable net has no driver (STILL PRESENT, P1; E6/J3)

**What/why:** `/EN` consists only of two input pins. Joining two inputs does not create a high or low level, so regulator startup is not guaranteed. A particular off or latched state is not proven.

**Where:** V0 U4.3/U7.3; V1 U4.3/U5.3. These are separate from the ESP’s own EN/CHIP_PU.

**Exactly change:** for always-on operation, connect both pin3 enables directly to their shared pin1 input supply `+3.7V`, after specifying its allowed voltage range. This needs no added resistor. If shutdown is required, define its actual controller and reset default before selecting that alternative.

**Verify:** netlist includes the intended input supply/driver; measure enable and outputs during startup. Do not count a speculative E3 latch fault separately.

### Finding3 — Two LDO outputs are tied together (STILL PRESENT, P1; E5)

**What/why:** independent3.3V regulators have slightly different setpoints. Directly joining them does not guarantee current sharing and does not provide an additive650mA supply rating. This topology is verified; a particular overload/oscillation is not.

**Where:** V0 U4.5 and U7.5; V1 U4.5 and U5.5, all on `+3.3V`.

**Exactly change:** keep the existing parts and split their loads: U4.5/C54.1 to `+3.3VA` for the corrected analog supply; U5.5/C57.1 to `+3.3V` for ADC digital and controller supply. Each capacitor return stays at valid common ground. Preserve U4 bypass C55 and input capacitors. No ballast network or power mux is needed to separate these intended loads.

**Verify:** distinct output nets, correct capacitor/load allocation and per-regulator load budget; targeted ERC power-output conflict should disappear. U3’s documented internal LDO also reaches its3V3 header: establish one DevKit supply method. USB/header dual powering is an unresolved operating-mode question, not an assumed additional active source.

### Finding4 — “DGND” control ties are not actually grounded (STILL PRESENT, P1; J3)

**What/why:** a ground symbol’s name matters. Both revisions have a `DGND` net separate from battery-negative `AGND/GND`. V0’s actual IC ground pins are correctly on AGND, but inputs meant to be low sit on the isolated DGND island. Their low state is not guaranteed. V1 expands this island into supply/return faults in Findings7/8.

**Where:** V0 U1/U2 RESV1.31 and GPIO42/44/45/46 plus U2 DAISY_IN41. V1 additionally U1 DAISY_IN41 and U2 CLKSEL52, as well as misplaced DVDD and MCU returns. True ADC DGND33/49/51 stays AGND in both.

**Exactly change:** after removing misplaced DVDD pins from this net, connect the intended low-level/control ground ties to valid battery/regulator ground. No resistor or isolation device is needed to establish that reference. Keep unused ADS GPIOs configured as inputs or low outputs; an actual firmware high-drive conflict has not been established.

**Verify:** all intended low straps share the ADC’s real DGND33/49/51 and BT1.2 net. Check actual control levels while reset is held. Do not merely rename a supply bus “ground.”

### Finding5 — ADC controls lack hardware reset defaults (STILL PRESENT, P1; J2/J3)

**What/why:** before firmware runs, the selected ESP GPIOs provide no guaranteed drive/pull for shared `/PWDN`, `/RESET` and `/START`. The ADS inputs have no specified internal bias that can be relied on. The omission is confirmed; a specific startup glitch or brownout is not.

**Where:** both ADCs PWDN35, RESET36, START38; V0 U6 GPIO6/7/21 and V1 U3 GPIO7/6/8. Separate/shared CS also needs a deliberate startup policy; its actual contention state is unknown.

**Exactly change:** add one10kΩ pulldown from shared `/PWDN` to valid ADC ground and one from shared `/RESET` to that ground. A10kΩ `/START` pulldown defines conversion-off default. These are justified bias components on demonstrated undriven controls. At3.3V a high-driven10kΩ draws0.33mA; two10µA input leakage bounds produce at most0.20V, below the0.66V low threshold. Recheck for the selected actual supply/leakage bounds.

**Verify/firmware:** hold inputs low until both supplies are valid, then establish both CS high before releasing shared PWDN/RESET. Initialize U1 on its internal clock and enable U1 CLK_EN before assuming U2 has a clock. For U2, TI’s power-up wait starts only once its external CLK is valid: wait at least2^18 clock periods (128ms at2.048MHz), or until VCAP1 exceeds1.1V, whichever is later, then reset/configure U2 using its separate CS and RESET opcode. Observe specified reset-completion and command timing. Do not pulse shared RESET at this stage: that would clear U1 CLK_EN and remove U2’s clock. Repeat this master-first validation after a common reset. This is a proposed sequence to verify, not a claim that existing firmware implements it.

Scope all relevant nets during held reset/cold start. Do not blindly add CS pull-ups: they can rise with DVDD before AVDD. Final CS/MOSI/SCLK passive defaults require the selected sequence; do not assume DOUT is tri-stated merely by PWDN. The official DevKit already has its EN pull-up/RC; no extra external EN resistor is justified from the unconnected U3.3 marker.

### Finding6 — Clock selection improved but clock delivery is incomplete (PARTIALLY FIXED, P0; J3)

**What/why:** V0 ties CLK37 only to CLKSEL52 on each ADC. At reset CLK_EN=0, so CLK is input/tri-state and cannot define CLKSEL. V1 adds an explicit U1 CLKSEL high strap and intends U2 external-clock selection; this is a local wiring improvement, usable only after supply repairs. However, U1 CLK37 does not reach the nearby ADC_CLK label. U2 CLK37 is the only component on ADC_CLK, so its selected external clock has no source. U2’s low strap also needs Finding4’s valid ground.

**Exactly change:** connect U1.37 to the existing `ADC_CLK` label/net reaching U2.37. Keep U1.52 on valid digital3.3V and U2.52 on valid ground after supply repairs. Firmware must set U1 CONFIG1.CLK_EN=1 to deliver the clock before ADC2 is expected to operate. No new oscillator is needed for the already chosen master/slave arrangement.

**Verify:** corrected netlist contains U1.37 and U2.37 together; the dangling-label/unconnected-clock ERC findings disappear. With valid supplies and configured master, measure the selected nominal2.048MHz clock at both chips. Validate the master-first reset sequence in Finding5: common RESET clears U1’s clock-output setting. This is completion of the control arrangement within J3, not a separate general timing redesign.

### Finding7 — ADC digital positive supplies moved to the ground island (NEW IN V1, P0; H2/A1)

**What/why:** V0 DVDD48/50 is correctly on `+3.3V`. V1 puts those positive pins on `DGND`, while actual ADC DGND33/49/51 remains `AGND`. There is no valid positive digital supply; simply merging the ground names would ground DVDD. This is distinct from the controller’s missing return in Finding8.

**Exactly change:** remove U1/U2 pins48/50 from the capacitor-return/DGND rows; connect them to the U5 digital `+3.3V` rail, at the supply side of C8/C9/C34/C35. Retain those capacitors’ returns on corrected common ground.

**Verify:** positive DVDD pins share U5.5 and capacitor pin1, never the actual chip-ground net. Measure DVDD relative to ADC DGND against its operating range. Remove these mistaken connections before joining ground nets.

### Finding8 — Controller and digital bypass returns lack battery ground (NEW IN V1, P0; H1/C3)

**What/why:** V0 MCU ground has a valid battery return. V1 U3’s four GND pins and digital decoupler returns join isolated DGND, separate from battery negative and LDO ground. The intended board supply lacks its return reference. A parasitic path through signals or an attached USB cable is not a valid schematic ground connection and is not assumed here.

**Exactly change:** once Finding7 is repaired, join U3 GND22/23/24/44 and C8/C9/C34/C35 pin2 to common battery/LDO/ADC ground. Keeping meaningful net names is fine only if the actual connection is explicit. No new ground-isolation component is supported.

**Verify:** netlist includes U3 grounds, capacitor returns, BT1.2, U4.2/U5.2 and actual ADC grounds on the same return net; DVDD/AVDD remain separate positives. Check board3V3-to-GND voltage directly after corrections.

## Calculations and checks that constrain the conclusions

### Dropout and missing battery limits (E2)

The labels give only0.400V nominal headroom. The following use maximum listed dropout at stated loads/temperature, added to the nominal3.3V target; they are **not full minimum-battery specifications**, because output tolerance and actual load/range remain to be included.

| Regulator/chip | Load | Maximum dropout over full stated temperature range |3.3V+dropout |
|---|---:|---:|---:|
| TLV75533P |500mA|0.238V|3.538V|
| LP2985 legacy |150mA|0.575V|3.875V|
| LP2985 new chip |150mA|0.254V|3.554V|
| LP2985 legacy |50mA|0.225V|3.525V|
| LP2985 new chip |50mA|0.184V|3.484V|

Actual signoff uses `VIN(min under load) ≥ VOUT(max tolerance) + VDO(max at selected load/temperature)` and the selected part’s recommended-input conditions. Do not assume U4 supplies150mA, a particular battery chemistry/cutoff, or fixed current sharing in the present parallel circuit. No added boost/buck architecture is justified until those requirements show a need.

### Nominal digital levels (I1)

For V0’s intended3.3V digital interface and common actual AGND, the stated static limits are compatible. Zero guaranteed margin on one comparison calls for realistic validation; it is not a demonstrated fault.

| Direction | Transmitter guarantee | Receiver requirement | Result at3.3V |
|---|---|---|---|
| ESP→ADS high |VOH≥0.8VDD=2.64V|VIH≥0.8DVDD=2.64V|Meets boundary; no extra guaranteed high margin |
| ESP→ADS low |VOL≤0.1VDD=0.33V|VIL≤0.2DVDD=0.66V|Compatible |
| ADS→ESP high |VOH≥DVDD−0.4=2.90V|VIH≥0.75VDD=2.475V|Compatible |
| ADS→ESP low |VOL≤0.4V|VIL≤0.25VDD=0.825V|Compatible |

Use each datasheet’s stated output test conditions/drive settings; these figures do not bound arbitrary firmware settings or transients. V1’s floating/incorrect supply-reference network prevents the same valid-domain calculation until repaired. No level shifter is supported merely because different chip families are used.

### ADS1298 input architecture (I4)

Each lead’s external network has `R×C=2000×620pF=1.24µs`, giving a simple external one-pole corner of about128.4kHz. A 1.2nA input-bias bound through the drawn2kΩ alone produces2.4µV. These calculations neither describe the total electrode source impedance nor prove24-bit accuracy. ADS1298 has CMOS PGA inputs followed by delta-sigma modulators/digital filters; generic SAR sample-and-hold settling assumptions do not establish a fault here. Actual electrode/source impedance, gain, lead-off settings, data rate and allowed settling error are needed. No added buffer follows from the existing resistor value alone.

### Optional RLD change and limits of the evidence

V0 U1 has1MΩ R36 parallel1.5nF C73 between RLDOUT63 and RLDINV61, with one J1 reference electrode at output. U2 has the analogous R1/C1 toward the other J1 instance, but U2 RLDOUT63 is unconnected in the actual schematic. Text saying “RLDIN -> RLDOUT on PCB” is not a schematic connection. Both RLDREF60 and RLDIN62 are unconnected in V0; their chosen operating modes are undocumented. V1 removes the feedback networks and reference-electrode symbols, leaves RLDOUT/RLDINV/RLDREF unconnected and ties unused RLDIN to the positive-named rail. This does not prove measured common-mode failure, instability or clipping, particularly while optional circuits may be disabled. No independent RLD/electrode-safety/layout/performance review was conducted.

## Condition-by-condition audit

Classification is the comparison result. **CANNOT VERIFY with P0 at A1/F1 means the V0 numerical comparison is unresolved but a V1 fault is already confirmed.** A dash priority means no demonstrated remaining problem under that condition; UNKNOWN means insufficient evidence to rank an alleged failure. Exact proposed corrections above are shared by overlapping rows.
'''

doc=[intro]
current=None
for r in rows:
    if r['Category'] != current:
        current=r['Category']; doc.append(f"\n## {r['ID'][0]}. {current}\n")
    doc.append(f"\n### {r['ID']} — {r['Ambrflow_condition']}\n\n**Status:** {r['Classification']}. **Priority:** {r['Priority']}.\n\n**V0 — {r['V0_component']}:** {r['V0_finding']}\n\n**V1 — {r['V1_component']}:** {r['V1_finding']}\n\n**Exact evidence:** {r['Evidence']}\n\n**Difference / conclusion:** {r['Difference']}\n\n**Requirement / calculation:** {r['Requirement']}\n\n**Simplest correction:** {r['Recommended_fix']}\n\n**Verification:** {r['Verification_needed']}\n")
doc.append(f'''
## Manufacturer sources and supporting evidence

- {ADS}: pin functions pp10–11, ratings p12, input characteristics p13, PGA pp31–32, RLD p41, clock p50, multiple-device SPI pp56–58, configuration/reset registers pp66–70, power-up p96.
- {LP}: pinout p3, recommended conditions p4, dropout/electrical tables pp5–6, ON/OFF and capacitor requirements in §§6–7. Covers legacy/new chips; exact fitted suffix is still required.
- {TLV}: DBV pinout p3, ratings p4, dropout p6, enable/discharge and capacitor requirements §§6–7.
- {ESP} and {MOD}: GPIO reset/strap/DC tables. V0 is a module representation; unspecified eFuses matter for GPIO3 interpretation.
- {BOARD} sheet2, saved as [reference PDF](EVIDENCE/esp32-devkitc-v11.pdf); {GUIDE} describes mutually exclusive board power methods. This reference does not establish the exact installed board revision.
- {PAR}: why parallel independent regulator references require a deliberate current-sharing arrangement; no such arrangement is shown here.
- [Power evidence](EVIDENCE/power_findings.md), [ADC evidence](EVIDENCE/adc_findings.md), [digital evidence](EVIDENCE/digital_findings.md), netlist/ERC/SVG exports and full parsed inventories in `EVIDENCE/`. Raw analyst notes are supporting material; this report and the CSV contain the final classifications, including the stricter A1/F1 comparison treatment.

## Verification still outstanding

No physical voltage, dip, brownout, ringing, oscillation, clipping, clamp current or signal-edge measurement was performed. No loop/transient simulation or firmware execution was possible from the supplied source material. Missing inputs: rated passive BOM, LP2985 chip identity, battery minimum/maximum/cutoff and load budgets, exact DevKit revision/powering modes, GPIO/ADC register/eFuse configuration, electrode/source/load models, and relevant startup/transition captures. These gaps do not weaken the direct pin-to-net wiring findings; they limit claims about actual physical behavior and the25 uncertain condition comparisons.
''')
Path('AMBRFLOW_DETAILED_AUDIT.md').write_text(readable(''.join(doc)))

summary='''# Ambrflow meeting summary — V0 versus V1

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
| Checklist comparisons that cannot be verified |25 of48|

Eight distinct problems need correction/completion. Counts group overlapping checklist entries; no completion percentage is claimed. A1/F1 are uncertain only in their numerical V0 comparison: **V1’s analog supply is confirmed0V**; V0’s source-free rail voltage is unknown. H2 counts the missing valid analog supply in both.

## B. What we fixed

**No fully verified closure. One local improvement is real:**

| Ambrflow ID | Original V0 problem | Change in V1 | Why it helps / remaining limit |
|---|---|---|---|
|J3 — partial|CLKSEL tied only to CLK: undefined at reset|U1 gets a high strap; U2 intended as clock slave|U1 strap becomes valid after supply repair. Slave clock connection is still missing; complete it and validate startup.|

LDO renumbering and unchanged2kΩ/620pF input filters are not fixes. The DevKit already includes EN/reset circuitry.

## C. What still needs fixing

Proposed changes only. Exact connections/verification: detailed Findings1–8.

| Priority | Ambrflow ID | V1 components | Problem | Simple solution |
|---|---|---|---|---|
|P0|H2; A1/F1|U1/U2 AVDD19/21/22/54/56/59|Analog supply grounded:0V span; analog-pin overvoltage risk|Move analog positives/unused analog ties to dedicated U4 output; keep negatives grounded.|
|P0|H2/A1|U1/U2 DVDD48/50|Digital positive supply on DGND|Move DVDD to U5 digital3.3V **before joining grounds**.|
|P0|H1/C3|U3 GND22/23/24/44; C8/C9/C34/C35.2|No battery return for controller/decouplers|After DVDD correction, join genuine returns to battery/LDO ground.|
|P0|J3 partial|U1/U2 CLK37|ADC2 selects an external clock, but ADC_CLK has no source|Connect U1.37 to ADC_CLK/U2.37; firmware sets U1 CLK_EN.|
|P1|E5|U4.5/U5.5|Two independent LDO outputs share +3.3V|Separate existing outputs: U4 analog, U5 digital/MCU; retain each output capacitor.|
|P1|E6/J3|U4.3/U5.3|Shared /EN has only input pins|If always-on, connect enables to their shared input supply; no extra resistor.|
|P1|J3|U1/U2 pins31/41/42/44/45/46; U2.52|Low straps on ungrounded DGND|Connect to valid ground after removing misplaced supply pins.|
|P1|J2/J3|Shared PWDN35/RESET36/START38|No guaranteed hardware defaults before firmware|10kΩ pulldowns on shared PWDN/RESET, and START for conversion-off; validate CS/startup sequence.|

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
7. Did settling analysis use ADS1298’s actual architecture, our2kΩ/620pF network, and what electrode impedance/error target?
8. Which eFuse/JTAG requirement would make floating GPIO3 a functional fault?

## F. Next actions

1. Correct supply/return connections and split LDO outputs; re-export netlists/ERC before powering.
2. Complete clock/reset defaults and validate master-first startup: shared reset clears ADC1’s clock output. Confirm DevKit power mode.
3. Obtain missing BOM/battery/configuration data; measure rails/startup/CS behavior before recommending further components.

Evidence, manufacturer links and all48 condition decisions: [detailed audit](AMBRFLOW_DETAILED_AUDIT.md), [CSV matrix](AMBRFLOW_ISSUE_MATRIX.csv), and `EVIDENCE/` netlist/ERC exports.
'''
Path('AMBRFLOW_MEETING_SUMMARY.md').write_text(readable(summary))

# Validate the machine-readable deliverable and source-read-only claim.
with Path('AMBRFLOW_ISSUE_MATRIX.csv').open(newline='') as f:
    loaded=list(csv.DictReader(f))
assert len(loaded)==48 and [r['ID'] for r in loaded]==expected
assert list(loaded[0])==columns
assert counts==Counter({'CANNOT VERIFY':25,'NOT APPLICABLE':10,'NOT FOUND':6,'STILL PRESENT':4,'NEW IN V1':2,'PARTIALLY FIXED':1})
manifest=json.loads(Path('EVIDENCE/source_manifest.json').read_text())
for item in manifest.values():
    assert hashlib.sha256(Path(item['source']).read_bytes()).hexdigest()==item['sha256'], 'Source schematic changed during audit'
print('Validated48 unique condition rows, exact CSV columns, classification totals, and unchanged source-schematic hashes.')
print('Report words:',{str(p):len(p.read_text().split()) for p in Path('.').glob('AMBRFLOW_*.md')})
