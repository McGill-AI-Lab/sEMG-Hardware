"""Verify the review-driven V2 changes against the preserved native KiCad netlists."""
from pathlib import Path
import collections
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from schematic_tools import read, all_, one, symbols, props

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def native(stem):
    tree = ET.parse(OUT / f'{stem}-netlist.xml').getroot()
    components = {c.get('ref'): {
        'value': c.findtext('value'), 'footprint': c.findtext('footprint'),
        'libsource': dict(c.find('libsource').attrib), 'pins': {}
    } for c in tree.findall('./components/comp')}
    nets = {}
    for node in tree.findall('./nets/net'):
        members = {(p.get('ref'), p.get('pin')) for p in node.findall('node')}
        nets[node.get('name')] = members
        for ref, pin in members:
            components[ref]['pins'][pin] = node.get('name')
    return components, nets


initial, ni = native('initial')
final, nf = native('final')
checks = []


def check(name, condition):
    assert condition, name
    checks.append(name)


def pin(ref, number):
    return final[ref]['pins'][str(number)]


check('111 original components retained; only R33–R35 and TP1–TP16 added',
      set(final) == set(initial) | {f'R{i}' for i in range(33, 36)} |
      {f'TP{i}' for i in range(1, 17)})
for ref, original in initial.items():
    check(f'{ref}: original value, footprint, library ID and pin numbers unchanged',
          all(final[ref][key] == original[key] for key in ('value', 'footprint', 'libsource'))
          and set(final[ref]['pins']) == set(original['pins']))

# Every original pin must have precisely the expected final net name.
# Internal-node labels were introduced solely to connect passive diagnostic probes.
changes = []
for ref, original in initial.items():
    for number, old in original['pins'].items():
        expected = 'AGND' if old == 'DGND' else old
        if ref in ('U1', 'U2'):
            if int(number) in (19, 21, 22, 48, 50, 54, 56, 59): expected = '+3.3V'
            if number == '37': expected = 'ADC_CLK'
            if ref == 'U2' and number == '47': expected = '/DRDY_ADC2'
        match = re.fullmatch(r'Net-\((U[12])-(VREFP|VCAP[1-4])\)', old)
        if match:
            adc, node = match.groups()
            expected = f'/{node}_ADC{adc[1]}'
        check(f'{ref}.{number}: expected final pin/net assignment', pin(ref, number) == expected)
        if old != expected:
            changes.append({'component': ref, 'pin': number, 'initial': old, 'final': expected})

for adc in ('U1', 'U2'):
    check(f'{adc}: AVDD/AVDD1/DVDD all on intended 3.3 V',
          all(pin(adc, n) == '+3.3V' for n in (19,21,22,54,56,59,48,50)))
    check(f'{adc}: all physical returns and unused digital low pins share battery return',
          all(pin(adc, n) == 'AGND' for n in
              (20,23,25,31,32,33,41,42,44,45,46,49,51,53,57,58)))
    check(f'{adc}: unused analog auxiliary pins equal actual AVDD',
          all(pin(adc, n) == pin(adc, 19) for n in (17,18,62)))
    for n in range(1,17):
        check(f'{adc} acquisition pin{n}: exact original net membership retained',
              nf[pin(adc,n)] == ni[initial[adc]['pins'][str(n)]])

check('master CLKSEL high; slave CLKSEL at actual physical ground',
      pin('U1',52) == '+3.3V' and pin('U2',52) == pin('U2',33) == 'AGND')
check('shared CLK has only both ADC pins and passive TP1',
      nf['ADC_CLK'] == {('U1','37'),('U2','37'),('TP1','1')})
for net in ('/MISO','/MOSI','/SCLK','/CS_ADC1','/CS_ADC2'):
    check(f'{net}: exact original SPI pin membership retained', nf[net] == ni[net])

for ref, net in (('R33','/START'),('R34','/RESET'),('R35','/PWDN')):
    check(f'{ref}: only intended 10k pulldown',
          final[ref]['value'] == '10k' and pin(ref,1) == net and pin(ref,2) == 'AGND')
    check(f'{net}: original control pins retained with one added passive resistor',
          nf[net] == ni[net] | {(ref,'1')})
check('U2 DRDY independently probed, never tied to master DRDY or MCU',
      nf['/DRDY_ADC2'] == {('U2','47'),('TP3','1')})
check('master DRDY MCU mapping preserved with TP2 added',
      nf['/DRDY_ADC1'] == ni['/DRDY_ADC1'] | {('TP2','1')})
probe_nets = ['ADC_CLK','/DRDY_ADC1','/DRDY_ADC2','+3.3V','+3.7V','AGND'] + [
    f'/{node}_ADC{adc}' for adc in (1,2) for node in ('VREFP','VCAP1','VCAP2','VCAP3','VCAP4')]
for i, net in enumerate(probe_nets,1):
    check(f'TP{i}: correct node', pin(f'TP{i}',1) == net)
check('all 57 original capacitors still have two connected terminals',
      all(len(final[f'C{i}']['pins']) == 2 for i in range(1,58)))
check('F04 explicitly still open: parallel LDO sources unchanged',
      pin('U4',5) == pin('U5',5) == '+3.3V')
check('F05 explicitly still open: EN contains only both LDO inputs',
      nf['/EN'] == {('U4','3'),('U5','3')})
check('no new body-bias or RLD output connection',
      all(pin(u,p).startswith('unconnected-') for u in ('U1','U2') for p in (60,61,63,64)))

# Verify the original embedded symbol definitions remain byte-identical.
source_i, root_i = read(OUT / 'initial-v2.kicad_sch')
source_f, root_f = read(ROOT / 'open-semg-16-v2.kicad_sch')
libs_i = {n[1]: source_i[n.start:n.end] for n in all_(one(root_i,'lib_symbols'),'symbol')}
libs_f = {n[1]: source_f[n.start:n.end] for n in all_(one(root_f,'lib_symbols'),'symbol')}
check('all original embedded library symbols unmodified; TestPoint cache only addition',
      set(libs_f) == set(libs_i)|{'Connector:TestPoint'} and
      all(libs_f[k] == v for k,v in libs_i.items()))
check('no NC markers added; only formerly unused U2 DRDY marker removed',
      len(all_(root_i,'no_connect')) == 9 and len(all_(root_f,'no_connect')) == 8 and
      {tuple(one(n,'at')[1:]) for n in all_(root_i,'no_connect')} -
      {tuple(one(n,'at')[1:]) for n in all_(root_f,'no_connect')} == {('422.91','163.83')})

baseline = json.loads((OUT/'pre-edit-hashes.json').read_text())
protected = {name: digest for name,digest in baseline.items()
             if name != 'open-semg-16-v2.kicad_sch'}
for name,digest in protected.items():
    check(f'protected original file unchanged: {name}',
          hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest)

stages = {}
for stem in ('initial','after-power','after-clock','final'):
    erc = json.loads((OUT/f'{stem}-erc.json').read_text())
    violations = [v for s in erc['sheets'] for v in s['violations']]
    stages[stem] = {'total':len(violations),
                   'severities':dict(collections.Counter(v['severity'] for v in violations)),
                   'types':dict(collections.Counter(v['type'] for v in violations))}
check('configured ERC errors/warnings improved as expected',
      stages['initial']['severities'] == {'error':38,'warning':27} and
      stages['final']['severities'] == {'error':35,'warning':26})
check('same inherited ERC disabled-check configuration',
      json.loads((OUT/'initial-erc.json').read_text())['ignored_checks'] ==
      json.loads((OUT/'final-erc.json').read_text())['ignored_checks'])

result = {'passed_checks':len(checks), 'checks':checks,
          'initial_components':len(initial),'final_components':len(final),
          'original_pin_net_changes':changes, 'ERC_stages':stages,
          'protected_files_verified_unchanged':len(protected),
          'only_modified_preexisting_file':'open-semg-16-v2.kicad_sch',
          'readiness':'NOT READY: F04/F05/F07 and partial F06/F09 plus safety/qualification work remain.'}
(OUT/'validation-results.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'final-connectivity.json').write_text(json.dumps(final,indent=2)+'\n')
print(f'{len(checks)} targeted connectivity/preservation checks passed.')
print('ERC: 38 errors + 27 warnings -> 35 errors + 26 warnings.')
print(f'{len(protected)} protected files unchanged, including all V1 reviews/design and V2 project.')
print('These checks do not establish power-source qualification, firmware operation or wearer safety.')
