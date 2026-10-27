"""Recheck static audit facts from KiCad's exported pin/net data; not a design pass."""
from pathlib import Path
import collections
import json
import math

OUT = Path(__file__).resolve().parent
data = json.loads((OUT / 'current-connectivity.json').read_text())
comp, nets = data['components'], data['nets']


def net(ref, pin):
    return comp[ref]['pins'][str(pin)]['net']


cap_pairs = [(1, 2), (3, 4), (5, 10), (11, 12), (13, 14), (15, 16),
             (17, 18), (21, 22), (27, 28), (29, 30), (31, 36), (37, 38),
             (39, 40), (41, 42), (43, 44), (47, 48)]
mapping = []
for ch, (cp, cn) in enumerate(cap_pairs, 1):
    adc = 'U1' if ch <= 8 else 'U2'
    n = (ch - 1) % 8 + 1
    rp, rn = 'R' + str(2 * ch - 1), 'R' + str(2 * ch)
    ep = 'E' + str(ch)
    facts = [net(ep, 1) == net(rp, 1), net(ep, 2) == net(rn, 1),
             net(rp, 2) == net(adc, 18 - 2 * n) == net('C' + str(cp), 1),
             net(rn, 2) == net(adc, 17 - 2 * n) == net('C' + str(cn), 1),
             net('C' + str(cp), 2) == net('C' + str(cn), 2) == 'AGND',
             comp[rp]['value'] == comp[rn]['value'] == '2KΩ',
             comp['C' + str(cp)]['value'] == comp['C' + str(cn)]['value'] == '620pF']
    assert all(facts), (ch, facts)
    mapping.append({'channel': ch, 'mapping_and_nominal_filter_confirmed': True})

faults = {}
for adc in ('U1', 'U2'):
    assert all(net(adc, p) == 'AGND' for p in
               (19, 21, 22, 54, 56, 59, 20, 23, 32, 53, 57, 58, 33, 49, 51))
    assert all(net(adc, p) == 'DGND' for p in (48, 50))
    assert all(net(adc, p) == '+3.3V' for p in (17, 18, 62))
    faults[adc] = {'analog_supply_span_V': 0,
                   'digital_supply_net': 'DGND', 'physical_digital_ground_net': 'AGND',
                   'aux_analog_pins_on_3V3': [17, 18, 62]}
assert net('BT1', 2) == 'AGND' and net('U3', 44) == 'DGND'
assert net('U4', 5) == net('U5', 5) == '+3.3V'
assert {(n['ref'], n['pin']) for n in nets['/EN']} == {('U4', '3'), ('U5', '3')}
assert len(nets['ADC_CLK']) == 1 and net('U2', 37) == 'ADC_CLK'
assert net('U1', 37).startswith('unconnected-')
assert sum(r.startswith('C') for r in comp) == 57
assert all(len(c['pins']) == 2 for r, c in comp.items() if r.startswith('C'))
assert data == json.loads((OUT / 'reference-connectivity.json').read_text())

erc = json.loads((OUT / 'current-erc.json').read_text())
violations = [v for sh in erc['sheets'] for v in sh['violations']]
severity = dict(collections.Counter(v['severity'] for v in violations))
assert severity == {'error': 38, 'warning': 27}, severity

R, C, temp_K = 2000, 620e-12, 300
fc = 1 / (2 * math.pi * R * C)
en = math.sqrt(4 * 1.380649e-23 * temp_K * 2 * R)
calcs = {'R_ohm_per_leg': R, 'C_F_per_leg': C, 'temperature_K_assumed': temp_K,
         'RC_pole_Hz': fc, 'pair_resistor_noise_V_per_sqrtHz': en,
         'rectangular_20_to_850_Hz_resistor_noise_Vrms': en * math.sqrt(830),
         'Cout_direct_AGND_uF_nominal': 222.4,
         'Cout_after_ground_correction_uF_nominal_excluding_DevKit': 242.6,
         'VCAP3_V_assumed_3V3_supply': 3.3 + 1.9}
for rate in (2000, 4000):
    h850 = (math.sin(math.pi * 850 / rate) / (math.pi * 850 / rate)) ** 3
    calcs[str(rate) + '_SPS'] = {
        'sinc3_850Hz_gain_dB_large_N_approx': 20 * math.log10(h850),
        'frame_bits_pair': 432, 'ideal_SPI_bits_per_second': 432 * rate,
        'payload_time_at_4MHz_s': 432 / 4e6}

result = {'meaning': 'Static facts reproduced; this is not an electrical design pass.',
          'components': len(comp), 'nets_including_unconnected_pins': len(nets),
          'all_16_mappings': mapping, 'confirmed_supply_faults': faults,
          'parallel_LDO_outputs_confirmed': True, 'undriven_LDO_EN_confirmed': True,
          'missing_shared_clock_confirmed': True, 'all_57_caps_have_two_netlisted_pins': True,
          'reference_connectivity_identical': True, 'ERC_severity_counts': severity,
          'conditional_calculations': calcs}
(OUT / 'audit-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print('Confirmed all 16 input mappings, 57 capacitor connections, supply/EN/clock faults,')
print('identical reference connectivity, and 38-error/27-warning configured ERC result.')
print('Saved audit-checks.json. These checks do not constitute a design pass.')
