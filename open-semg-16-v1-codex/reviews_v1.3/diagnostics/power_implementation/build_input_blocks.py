"""Build the V1.3 battery-entry circuit without changing the active design.

build(root_uuid, project_name) returns raw KiCad library/object snippets and a
physical-pin-to-net contract. All generated names are schematic-local caches;
installed/shared libraries and historical revisions are never written.
"""
from pathlib import Path
import json
import re
import uuid

OUT = Path(__file__).resolve().parent
LIB = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
BASELINE = OUT / 'baseline/open-semg-16-v1.3.kicad_sch'
SOURCES = {
    'J17': 'https://www.jst-mfg.com/product/pdf/eng/ePH.pdf',
    'F1': 'https://www.littelfuse.com/assetdocs/littelfuse_fuse_466_datasheet?assetguid=dbe9bcd7-6072-4adf-bf5b-d33e52a6b90f',
    'Q1': 'https://www.aosmd.com/res/data_sheets/AO3401A.pdf',
    'C57': 'https://industrial.panasonic.com/ww/products/pt/os-con/models/6SVP220M',
}
BULK_C57 = {
    'manufacturer': 'Panasonic', 'mpn': '6SVP220M',
    'value': '220uF', 'voltage': '6.3V', 'tolerance': '+/-20%',
    'esr': '25mOhm max at 100kHz',
    'ripple_current': '3.7Arms at 100kHz, 105C',
    'leakage_current_max': '277uA', 'temperature': '-55 to +105C',
    'diameter_mm': 10.0, 'height_mm': 7.9,
    'footprint_candidate': 'Capacitor_SMD:CP_Elec_10x7.9',
    'source': SOURCES['C57'],
    'qualification': 'Polarized: positive to MAIN, negative AGND. Verify land pattern and converter startup with full tolerance network.',
}


def _q(value):
    return json.dumps(str(value), ensure_ascii=False)


def _uid():
    return str(uuid.uuid4())


def _symbol(source, name):
    """Return a balanced symbol expression, respecting quoted parentheses."""
    marker = '(symbol ' + _q(name)
    start = source.find(marker)
    if start < 0:
        raise ValueError('Missing symbol: ' + name)
    # A name can be a prefix, so require quote closure immediately as generated.
    depth = 0
    quoted = False
    escaped = False
    for end in range(start, len(source)):
        c = source[end]
        if quoted:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise ValueError('Unbalanced symbol: ' + name)


def _library(filename, name):
    s = _symbol((LIB / filename).read_text(), name)
    return s.replace('(symbol ' + _q(name), '(symbol ' + _q(filename[:-10] + ':' + name), 1)


def _ao3401a_flat():
    """Flatten the installed AO3401A->TP0610T inheritance without renumbering."""
    source = (LIB / 'Transistor_FET.kicad_sym').read_text()
    base = _symbol(source, 'TP0610T')
    base = base.replace('(symbol "TP0610T"', '(symbol "V13_Power:AO3401A"', 1)
    base = base.replace('TP0610T_', 'AO3401A_')
    base = base.replace('"TP0610T"', '"AO3401A"')
    # Both TP0610T and AO3401A use physical 1=G, 2=S, 3=D in SOT-23.
    base = re.sub(r'\(property "Datasheet" "[^"]*"',
                  '(property "Datasheet" ' + _q(SOURCES['Q1']), base)
    base = re.sub(r'\(property "Description" "[^"]*"',
                  '(property "Description" "AO3401A P-channel MOSFET; physical pins 1=G, 2=S, 3=D"', base)
    return base


def _prop(name, value, x, y, hidden=False):
    return (f'(property {_q(name)} {_q(value)} (at {x:g} {y:g} 0) '
            f'(effects (font (size 1 1)){" (hide yes)" if hidden else ""}))')


def _instance(lib_id, ref, value, x, y, footprint, pin_numbers, root_uuid,
              project_name, datasheet='', fields=None, in_bom=True):
    props = [
        _prop('Reference', ref, x + 8, y - 4),
        _prop('Value', value, x + 8, y - 1),
        _prop('Footprint', footprint, x, y, True),
        _prop('Datasheet', datasheet, x, y, True),
    ]
    for key, val in (fields or {}).items():
        props.append(_prop(key, val, x, y, True))
    pins = '\n'.join(f'(pin {_q(p)} (uuid {_q(_uid())}))' for p in pin_numbers)
    return (f'(symbol (lib_id {_q(lib_id)}) (at {x:g} {y:g} 0) (unit 1) '
            f'(exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) '
            f'(on_board yes) (dnp no) (uuid {_q(_uid())})\n'
            + '\n'.join(props) + '\n' + pins + '\n'
            + f'(instances (project {_q(project_name)} (path {_q("/" + root_uuid)} '
            + f'(reference {_q(ref)}) (unit 1)))))')


def _wire(x1, y1, x2, y2):
    return (f'(wire (pts (xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})) '
            f'(stroke (width 0) (type default)) (uuid {_q(_uid())}))')


def _global(net, x, y, angle=0):
    return (f'(global_label {_q(net)} (shape input) (at {x:g} {y:g} {angle}) '
            f'(effects (font (size 1 1)) (justify left)) (uuid {_q(_uid())}) '
            + _prop('Intersheetrefs', '${INTERSHEET_REFS}', x, y, True) + ')')


def _note(text, x, y, size=1):
    return (f'(text {_q(text)} (at {x:g} {y:g} 0) '
            f'(effects (font (size {size:g} {size:g})) (justify left)) '
            f'(uuid {_q(_uid())}))')


def build(root_uuid, project_name):
    """Return the reviewable input block; never write an active schematic."""
    # Baseline resistor cache already belongs to the project; return byte-identical
    # cache so the root can deduplicate it safely.
    resistor = _symbol(BASELINE.read_text(), 'Device:R')
    libs = [
        _library('Connector_Generic.kicad_sym', 'Conn_01x02'),
        _library('Device.kicad_sym', 'Fuse'),
        _library('Jumper.kicad_sym', 'Jumper_2_Open'),
        _ao3401a_flat(), resistor,
    ]
    objects = []
    pin_map = {
        'J17': {'1': '+3.7V', '2': 'AGND'},
        'F1': {'1': '+3.7V', '2': 'BAT_FUSED'},
        'Q1': {'1': 'Q1_GATE', '2': 'SW_BAT_PROT', '3': 'BAT_FUSED'},
        'R52': {'1': 'Q1_GATE', '2': 'AGND'},
        'JP1': {'1': 'MAIN_ENABLE', '2': 'AGND'},
    }
    specs = [
        ('Connector_Generic:Conn_01x02', 'J17', 'B2B-PH-K-S(LF)(SN)', 63.5, 373.38,
         'Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical', ['1', '2'], SOURCES['J17'],
         {'Manufacturer': 'JST', 'MPN': 'B2B-PH-K-S(LF)(SN)',
          'Purpose': 'Protected 1S pack input; pin1 positive, pin2 return. Unplug pack for OFF.',
          'Pack requirement': '4.20V maximum; >=1.5A discharge capability; cell protection cutoff >=3.0V; compatible off-body charger',
          'Mating harness': 'PHR-2 housing, SPH-002T-P0.5S contacts, AWG24; verify pack cable pin polarity'}),
        ('Device:Fuse', 'F1', '1.5A FAST', 120.65, 373.38,
         'Fuse:Fuse_1206_3216Metric', ['1', '2'], SOURCES['F1'],
         {'Manufacturer': 'Littelfuse', 'MPN': '046601.5NR',
          'Rating': '1.5A, 63VAC/DC, 1206; 50A interrupt rating; derate for continuous current and temperature',
          'Purpose': 'Secondary board-input protection; not a wearer-current limiter or substitute for protected cell',
          'Cold resistance': '0.046ohm nominal at25C', 'Melting I2t': '0.1103A2s nominal'}),
        ('V13_Power:AO3401A', 'Q1', 'AO3401A', 190.5, 373.38,
         'Package_TO_SOT_SMD:SOT-23', ['1', '2', '3'], SOURCES['Q1'],
         {'Manufacturer': 'Alpha & Omega Semiconductor', 'MPN': 'AO3401A',
          'Purpose': 'Reverse-polarity P-MOS: D3=fused input, S2=protected output; not reverse-current blocking',
          'RDS_on': '85mOhm max atVGS=-2.5V, TJ25C; qualify hot condition',
          'Limits': 'VDS=-30V; VGS=+/-12V'}),
        ('Device:R', 'R52', '100k', 245.11, 373.38,
         'Resistor_SMD:R_0603_1608Metric', ['1', '2'], '',
         {'Manufacturer': 'Yageo', 'MPN': 'RC0603FR-07100KL', 'Tolerance': '1%',
          'Power': '0.1W', 'Purpose': 'Q1 gate pull-down'}),
        ('Jumper:Jumper_2_Open', 'JP1', 'INHIBIT (OPEN=RUN)', 340.36, 373.38,
         'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', ['1', '2'],
         'https://www.samtec.com/products/tsw-102-07-g-s',
         {'Manufacturer': 'Samtec', 'MPN': 'TSW-102-07-G-S',
          'Assembly': 'Fit header, no shunt for RUN; short only for service inhibit',
          'Purpose': 'MAIN_ENABLE to AGND inhibits converter. Not galvanic isolation; unplug pack for OFF.'}),
    ]
    for lib_id, ref, val, x, y, footprint, pins, ds, fields in specs:
        objects.append(_instance(lib_id, ref, val, x, y, footprint, pins,
                                 root_uuid, project_name, ds, fields))

    # Pin endpoints derive from the unrotated installed symbol definitions.
    # Per-pin stubs/global labels give an explicit net contract and avoid long,
    # crossing wires between the separated input components.
    pin_xy = {
        'J17': {'1': (58.42, 373.38), '2': (58.42, 375.92)},
        'F1': {'1': (120.65, 369.57), '2': (120.65, 377.19)},
        'Q1': {'1': (185.42, 373.38), '2': (193.04, 378.46), '3': (193.04, 368.30)},
        'R52': {'1': (245.11, 369.57), '2': (245.11, 377.19)},
        'JP1': {'1': (335.28, 373.38), '2': (345.44, 373.38)},
    }
    for ref, pins in pin_xy.items():
        for p, (x, y) in pins.items():
            if ref in ('F1', 'R52') or (ref == 'Q1' and p in ('2', '3')):
                ex, ey = x, y + (-3.81 if p in ('1', '3') else 3.81)
            else:
                ex, ey = x + (3.81 if ref == 'JP1' and p == '2' else -3.81), y
            objects.append(_wire(x, y, ex, ey))
            objects.append(_global(pin_map[ref][p], ex, ey))
    objects.extend([
        _note('BATTERY ENTRY - specified external protected1S pack; unplug pack for OFF', 50, 357.5, 1.2),
        _note('J17: pin1 POSITIVE, pin2 RETURN. Verify cable polarity; no universal Li-Po connector polarity.', 50, 388.5),
        _note('F1/Q1 add secondary input and polarity protection; Q1 does not block reverse current. No USB/charging while worn.', 50, 392),
        _note('JP1 normally OPEN. Short for service inhibit only; disconnect battery and unseat DevKit before USB service.', 50, 395.5),
    ])
    return {'lib_symbols': libs, 'objects': objects, 'pin_map': pin_map,
            'pin_coordinates': pin_xy, 'references': SOURCES,
            'bulk_c57_recommendation': BULK_C57}


if __name__ == '__main__':
    root_uuid = str(uuid.uuid4())
    data = build(root_uuid, 'input-blocks-candidate')
    target = OUT / 'input-blocks-candidate.kicad_sch'
    target.write_text('(kicad_sch (version 20260306) (generator "eeschema") '
                      f'(uuid {_q(root_uuid)}) (paper "A2")\n(lib_symbols\n'
                      + '\n'.join(data['lib_symbols']) + ')\n'
                      + '\n'.join(data['objects']) + '\n(embedded_fonts no))\n')
    (OUT / 'input-blocks-pin-contract.json').write_text(json.dumps(
        {k: v for k, v in data.items() if k not in ('lib_symbols', 'objects')}, indent=2) + '\n')
    print(target)
