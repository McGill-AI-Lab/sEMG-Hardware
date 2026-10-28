# ADS1298 power evidence for V1.3

27 October 2026. Read-only schematic review; no design edits. The required historical review/implementation/ERC documents were consulted, with priority given to the latest `erc_corrections.md` for current state. Actual pin assignments below were independently checked against the root agent's fresh `v1.3-connectivity.json` and native XML export.

## Current state

For **each** U1/U2, AVDD pins 19/21/22/56/59, AVDD1 pin 54, DVDD pins 48/50 and unused auxiliary pins 17/18/62 share +3.3V. AVSS pins 20/23/32/57/58, AVSS1 pin 53, DGND pins 33/49/51 and VREFN pin25 share AGND. These repairs of original F01–F03 remain present; they are not current zero-span failures. U1 CLKSEL52 is +3.3V, U2 CLKSEL52 is AGND. Both CLK37 share ADC_CLK. Both DOUT43 share /MISO with U3.19. START38/RESET36/PWDN35/SCLK40/DIN34 are shared controls; CS39 remains separate per ADC. U1 DRDY47 connects to MCU; U2 DRDY47 remains a separate test node.

U1 direct-rail banks C6=100nF/C7=10uF and C8=100nF/C9=10uF; U2 C32/C33 and C34/C35 equivalent. Each ADC has independent VREFP24 with 100nF||10uF to VREFN25/AGND (C19/C20 and C45/C46). VCAP1 pin28 has 22uF (C23/C49), VCAP2 pin30 1uF (C24/C50), VCAP3 pin55 1uF (C25/C51), VCAP4 pin26 1uF (C26/C52), all to AGND. These internal-node/reference capacitors are **not** direct regulator-output capacitance. C57=200uF plus four 10uF+100nF banks makes main direct nominal capacitance 240.4uF before DevKit capacitance. U4/C54 is isolated; R38 still turns U4/U5 off, as detailed by root.

RLDREF60/RLDINV61/RLDOUT63/WCT64 remain unconnected. No deliberate body-bias source is added by any power architecture. Inputs retain all 16 original differential channels.

## Authoritative component constraints

Primary local source: [TI ADS1298 SBAS459K](../../../../docs/datasheets/originals/components/ADS1298.pdf), especially printed pp.10–17,31–33,48,51–55,67–71,85,96–99. Existing original-review PDF text extraction `../../../reviews_v1/diagnostics/pdf-text/ADS1298.txt` was used to cross-check the processed manufacturer text. Official current [TI datasheet](https://www.ti.com/lit/ds/symlink/ads1298.pdf) is still Rev.K; an online cross-check did not identify a new power specification.

- Recommended analog span 2.7–5.25V; DVDD 1.65–3.6V; AVDD–DVDD −2.1…+3.6V (p.12). A 3.0V AVDD /3.3V DVDD split is valid steady-state: −0.3V. It preserves 3.3V digital signaling. Supplying raw full-charge 1S LiPo to DVDD is invalid.
- Analog inputs absolute window AVSS−0.3…AVDD+0.3V; digital inputs and outputs DGND−0.3…DVDD+0.3V (p.12). These are stress limits, not normal operating targets. An unpowered ADS input has no assumed 3.3V tolerance. RESET/PWDN do not provide IO isolation.
- Supply currents p.16 with RLD/WCT/PACE off, under the electrical table's general conditions (AVDD3V, DVDD1.8V unless separately stated, 500SPS HR, gain6, external2.048MHz): analog2.75mA HR or1.8mA LP per ADS1298; digital0.3mA at1.8V,0.5mA at3V. Two devices therefore approximately5.5mA analog +1.0mA digital using the separate3V current rows. These are typical benchmarks, **not** guaranteed maxima for3.0/3.3V, higher data rates, clock-output loading or enabled support amplifiers. Allocate at least10mA analog +2mA ADC digital pending measurements; this is engineering headroom, not a new IC specification. Pull resistors, control buffers and clock loading add current. At3.0V, 5.5mA analog is16.5mW; at3.3V,1mA digital is3.3mW.
- p.31 notes PGA signal-dependent current in addition to quiescent current. p.16 headline power dissipation is not a whole-system power budget.
- AVDD1 supplies the charge pump and has transients at fCLK. Star-connect AVDD1/AVSS1 to AVDD/AVSS; bypass each supply with1uF||100nF close to pins and route digital/radio returns away from analog returns (p.96). Existing10uF/100nF general analog/digital banks may be retained with selected effective capacitance; add explicit local1uF||100nF at each AVDD1/AVSS1 pair. Do not implement disconnected ground islands. Use continuous low-impedance return with placement controlling current paths.
- VCAP3 approximately AVDD+1.9V relativeAVSS:4.9V at3.0 analog or5.2V at3.3 analog. Retain >=10V procurement requirement and confirm >=1uF **effective** capacitance at bias. Fig.106 p.97 also shows100nF atVCAP3; addition is reasonable but its current omission alone is not a demonstrated failure. Keep all internal bypass nodes independent and unloaded.
- VCAP1 noise degrades internal-reference operation. TI specifically highlights microphonic ferroelectric MLCCs under vibration; select an appropriate low-leakage, nonferroelectric option or measure the actual chosen capacitor under wrist movement (p.96). "X7R" alone is not an analog-noise qualification.
- Each internal2.4V reference must be enabled separately; reset leaves internal-reference buffer off. Do not select4V reference mode on3V supply. Retain independent10uF||100nF networks and wait for settled reference; no fixed measured settling delay has been established here (pp.33,69,85). Do not treat the capacitor as a voltage source.

## Analog headroom tradeoff

Eq.2 p.32: `0.2 + G*abs(VD)/2 < VCM < AVDD - 0.2 - G*abs(VD)/2` forAVSS0. With gain6:

| Maximum differential magnitude | VCM limits at3.0V AVDD | At3.3V AVDD |
|---:|---:|---:|
|300mV|1.10…1.90V|1.10…2.20V|
|350mV|1.25…1.75V|1.25…2.05V|
|400mV|1.40…1.60V|1.40…1.90V|

Bounds are strict; do not target endpoints. Preferred middle bias moves1.65→1.50V. Full-scale differential at2.4V reference/gain6 remains nominal±400mV, but common-mode headroom is narrower. Electrode DC offset, motion and missing F07 bias remain important. 3.0V quiet analog supply is sensible if electrode/gain/common-mode requirements fit; measured need for greater margin may justify an independent analog boost+3.3V LDO or other supply architecture. Directly raising the digital rail to3.6V would leave no3.6V-rated MCU/ADC tolerance margin.

## Startup, shutdown and brownout

TI pp.96–97 requires analog/digital inputs low before and through stabilized supplies. After supplies settle, establish clock, wait `tPOR=2^18*tCLK` **and** VCAP1>1.1V, whichever is later, issue reset low>=2*tCLK, then wait18*tCLK before commands. At2.048MHz these times are128ms,0.977us and8.789us respectively. Use measuredVCAP1 behavior; an arbitrary150ms delay may be inadequate. For an external-clock slave, tPOR starts only afterCLK is valid. Internal oscillator typical wakeup is20us but is not a guaranteed system-startup timeout.

Existing U1 oscillator selection can start U1 internally, but CLK_EN resets0. Initialize U1 using its internal clock and enable its CLK output before starting U2's external-clock tPOR. Shared RESET later clears CLK_EN again; initialize/reset U2 with its individual command after clock is valid, or explicitly design another clock strategy. Preserve mode, rate, reference and exclusive CS configuration/readback before commonSTART.

PWDN low powers down circuitry; on release oscillator/reference need wakeup time (p.48). Reset takes18clock cycles and restores register defaults, including reference-off and CLK-output-off. No guaranteed ADS brownout threshold or automatic recovery contract is supplied by this review. External rail monitoring must invalidate data/assert safe controls on undervoltage and repeat complete initialization after recovery. ESP's own brownout detector does not monitor analog rail.

The p.12 AVDD–DVDD recommended operating difference calls for checking startup ramps and rail-failure states; the datasheet does not impose one explicit rail-order requirement or characterize every transient beyond operating conditions. A conservative implementation can start analog3.0V first and gate ADC DVDD3.3V until analog-good, then remove ADC DVDD before analog on shutdown. Buffer all powered MCU→unpowered ADC paths; otherwise sequencing the supply alone is incomplete. Size ADC-DVDD switch/soft-start for at least20.2uF existing bank plus additions:20.2uF×3.3V/1ms≈66.7mA startup charging before load.

## Reviewable digital isolation option

This is a concrete logic proposal for root's report, not implemented or fully qualified procurement:

1. Main3V3 powers MCU and analog3.0V LDO. Default-OFF ADC-DVDD load switch turns on only after analog-good, with controlled rise. Analog/digital supervisors force disable on either invalid rail.
2. Seven MCU→ADS controls(DIN,SCLK,START,RESET,PWDN,CS1,CS2) pass through default-disabled buffers with receiver-side10k pulldowns. [TI SN74AXC8T245](https://www.ti.com/lit/ds/symlink/sn74axc8t245.pdf), Rev.C p.1/§8.3, is a stronger candidate than an ordinary single-supply244 when ADC-DVDD is separately switched: VCCA=main3V3, VCCB=ADC-DVDD, DIR1 = HIGH and DIR2 = LOW for all eight bits A→B (Table 7-1); OE pullup to VCCA. It specifies partial-power-down protection and isolation when either supply is below100mV. Rail-good AND explicit firmware-ready permitsOE low only after rails settle; pin-level control implementation and supervisor delays need final design. MCU ready has an external pulldown and must use a verified GPIO without a high startup glitch. Review boot, watchdog and software resets as well as external CHIP_PU.
3. MCU sets CS1=CS2=HIGH while buffers remain disabled and all ADS control inputs stayLOW; sets other controlsLOW. After rails-good, firmware releases isolation, making both CS high with no SCLK activity. PWDN/RESET then follow the TI sequence above.
4. During the initial all-low state both ADC CS areLOW. Do **not** assume both DOUTs are high impedance because RESET/PWDN is low. For fully conservative startup, split the existing DOUT short and feed independent DOUTs to a2:1 digital mux; one mux output reaches MCU MISO. Verified [TI SN74LVC157A](https://www.ti.com/lit/ds/symlink/sn74lvc157a.pdf) is a quad2:1 mux candidate(use one channel; terminate unused inputs). Select can track CS1(LOW→U1,HIGH→U2), with transactions only when exactly one CS isLOW. This preserves16acquisition channels while avoiding a physical DOUT contention path during ramp or simultaneous accidental selection. The unverified part nameSN74LVC1G157 must **not** appear in a BOM. Equivalent individual tri-state DOUT buffers withhardwareREADY/CS gating are possible.
5. DRDY/MISO return-side power-off behavior must also be reviewed: powering MCU and the return buffer/mux from the same main rail, withADC-DVDD defaultOFF and no USB source, simplifies this. Add fail-safe isolation if any permitted state retainsADC power with MCU power absent.
6. Loss of rail-good disables interface before outputs become invalid; hardware forces safeRESET/PWDN/START defaults. Then turnADC-DVDD off, retain/dischargeanalog appropriately, and restart only with undervoltage hysteresis/latching. The shutdown timing must cover abrupt battery removal; do not rely only on firmware.

TI's analog-input-low guidance is not satisfied merely by digital gates. For initial bench powerup, no wearer or independently powered electrodes are connected; use ground-referenced dummy inputs. Future power-on while electrodes are attached depends on F07/F08 body bias/protection and normal/fault interface analysis. Adding32input switches or assuming electrode offsets zero is not justified by current evidence.

## Preferred final architecture after comparison

The preceding 3.0 V AVDD / 3.3 V DVDD sequencing proposal is an evaluated alternative. The preferred final proposal uses a main 3.4 V buck-boost rail for the ESP32 and an LT3042 quiet LDO rail, nominal 2.98 V with RSET = 29.8 kΩ, for **both** ADC AVDD/AVDD1 and DVDD. This removes the ADC-DVDD switch and separate ADC rail-ramp dependencies. The final regulator selection and tolerance calculations are in the root report; this ADC note does not replace that assessment.

The seven forward controls pass through an SN74AXC8T245 with VCCA = main 3.4 V and VCCB = AFE 2.98 V. **DIR1 = HIGH and DIR2 = LOW** gives all eight bits A→B, as verified against Rev. C Table 7-1. Both direction inputs HIGH would reverse bits 5:8 and is incorrect for this use. OE has a pullup to VCCA; only rails-good plus firmware-ready enables the interface. Terminate the unused input. Receiver-side pull resistors retain the input-low state during disabled operation. U1 CLKSEL follows AFE DVDD; pins 17/18/62 follow AFE AVDD. All grounds remain common.

Use two [Nexperia 74LVC1G157](https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf) parts for the return paths. The first selects the independent DOUT signals for MCU MISO; the second has I0 and I1 both connected to U1 DRDY and S tied to ground, regenerating DRDY at the MCU rail. Both are powered by main 3.4 V. Rev. 12 defines I1 pin 1, GND pin 2, I0 pin 3, Y pin 4, VCC pin 5 and S pin 6. Tie DOUT1 to I0, DOUT2 to I1, and the MISO selector S to the MCU-side CS1 signal, so CS1 LOW selects U1. Transactions still require exactly one CS asserted. The two physical ADC DOUTs no longer share a net and cannot directly fight during the all-low startup state.

The Nexperia part explicitly specifies partial-power-down IOFF protection, unlike the previously considered TI quad LVC157A whose datasheet did not provide IOFF. Nexperia Table 7 gives VIH = 2.0 V and VIL = 0.8 V for VCC = 2.7–3.6 V; output VOH is at least VCC−0.1 V at −100 μA. ADS VOH is at least DVDD−0.4 V at 500 μA. At a conservative AFE floor of 2.90 V this supplies at least 2.50 V to a 2.0 V minimum-high input. Ensure mux leakage and pull loading remain below the ADS test-load condition, and check actual timing and signal integrity.

Both ADS supply domains at approximately 2.98 V are allowed by §7.3. Figure 106 actually shows 3.0 V analog and 1.8 V digital; it must not be described as a literal 3.0/3.0 V reference circuit. ADC DVDD's approximately 1 mA typical two-device total shares the quiet regulator, with distinct local bypass and return routing; MCU and radio currents stay in the main branch. Main 3.4 V increases ESP power relative to 3.3 V and requires the complete tolerance, ripple and overshoot sum to remain below 3.6 V.

The common-mode table above uses exactly 3.0 V. At nominal 2.98 V, its upper boundaries decrease by 20 mV: gain 6 and 300/350/400 mV maximum differential magnitude respectively allow 1.10–1.88 V, 1.25–1.73 V and 1.40–1.58 V common mode. All boundaries remain strict and actual worst-case rail voltage must be used. Nominal midpoint bias is 1.49 V. At an AFE floor of 2.90 V the corresponding upper bounds are 1.80/1.65/1.50 V. Confirm electrode offset and body-bias requirements before implementation.
