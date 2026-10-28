"""Explicit V1.2-only, source-span edits for unsupported MCP operations.

No schematic serializer is used. Untouched objects retain their original bytes.
MCP plan creation was rejected by runtime approval policy; the authorized
fallback also adds the four explicit local labels. Invoke 'hardware', validate,
then invoke 'specifications' and validate again.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import uuid

OUT = Path(__file__).resolve().parent
ACTIVE = OUT.parents[1] / 'v1.2'
SCH = ACTIVE / 'open-semg-16-v1.2.kicad_sch'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


class Node(list):
    pass


def parse(source):
    stack, roots = [], []
    for match in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', source):
        token = match.group()
        if token == '(':
            node = Node()
            node.start = match.start()
            stack.append(node)
        elif token == ')':
            assert stack, 'Unbalanced closing parenthesis'
            node = stack.pop()
            node.end = match.end()
            if stack:
                stack[-1].append(node)
            else:
                roots.append(node)
        else:
            assert stack, 'Token outside S-expression'
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and len(roots) == 1 and roots[0][0] == 'kicad_sch'
    return roots[0]


def children(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


def one(node, key):
    return next(iter(children(node, key)), None)


def props(node):
    return {n[1]: n[2] for n in children(node, 'property')}


def symbols(root):
    return {props(n)['Reference']: n for n in children(root, 'symbol')}


def q(value):
    return json.dumps(str(value), ensure_ascii=False)


def uid():
    return str(uuid.uuid4())


def property_(name, value, x, y):
    return f'(property {q(name)} {q(value)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))'


def note(text, x, y, size=1.27):
    return f'(text {q(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid()}"))'


def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'


def label(text, x, y):
    if text == 'AGND':
        return f'(global_label {q(text)} (shape input) (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))'
    return f'(label {q(text)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))'


def commit(source, updated, phase, details):
    assert SCH.resolve().parent == ACTIVE.resolve()
    assert SCH.read_text() == source, 'Schematic changed concurrently'
    root = parse(updated)
    ids = re.findall(r'\(uuid\s+"([^"]+)"\)', updated)
    assert len(ids) == len(set(ids)), 'Duplicate UUID'
    assert len(symbols(root)) == len(children(root, 'symbol')), 'Duplicate reference'
    candidate = OUT / f'{phase}-candidate.kicad_sch'
    candidate.write_text(updated)
    command = [CLI, 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
               str(OUT / f'{phase}-candidate-netlist.xml'), str(candidate)]
    process = subprocess.run(command, text=True, capture_output=True)
    assert process.returncode == 0, process.stderr
    temporary = SCH.with_suffix('.kicad_sch.tmp')
    temporary.write_text(updated)
    temporary.replace(SCH)
    (OUT / f'{phase}-edit-log.json').write_text(json.dumps({
        'phase': phase, 'method': 'source-span patch; strict parse, unique UUID/reference checks, native KiCad candidate export, atomic replace',
        'source': str(SCH), 'before_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'after_sha256': hashlib.sha256(updated.encode()).hexdigest(), 'changes': details,
        'candidate_validation': {'argv': command, 'returncode': process.returncode,
                                 'stdout': process.stdout, 'stderr': process.stderr}}, indent=2) + '\n')


def hardware():
    source = SCH.read_text()
    root = parse(source)
    assert not {'R36', 'R37', 'R38'} & set(symbols(root))
    assert one(root, 'uuid')[1] == '240ade95-63db-4882-95be-8d01c1806f6c'
    extra, detail = [], []
    for ref, x, value, purpose in [
        ('R36', 180.34, '10k', 'F09: DIN/MOSI low default while MCU high impedance'),
        ('R37', 205.74, '10k', 'F09: SCLK low default while MCU high impedance'),
        ('R38', 231.14, '0', 'F05: fitted removable development OFF strap; remove only after power architecture redesign')]:
        y = 312.42
        fields = [property_('Purpose', purpose, x, y), property_('Rated power', '>=0.1 W; verify temperature derating', x, y)]
        if ref != 'R38':
            fields.append(property_('Tolerance', '1%', x, y))
        extra.append(f'''(symbol (lib_id "Device:R") (at {x} {y} 0) (unit 1)
            (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")
            (property "Reference" "{ref}" (at {x+2.54:.2f} {y-2.54:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
            (property "Value" "{value}" (at {x+2.54:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))
            {property_('Footprint', '', x, y)} {property_('Datasheet', '', x, y)}
            {' '.join(fields)}
            (pin "1" (uuid "{uid()}")) (pin "2" (uuid "{uid()}"))
            (instances (project "open-semg-16-v1.2" (path "/{one(root,'uuid')[1]}" (reference "{ref}") (unit 1)))))''')
        extra += [wire(x, 302.26, x, 308.61), wire(x, 316.23, x, 322.58)]
        detail.append({'finding': 'F05' if ref == 'R38' else 'F09', 'reference': ref,
                       'value': value, 'center_mm': [x, y], 'purpose': purpose,
                       'fallback_labels': {'pin1': 'EN' if ref == 'R38' else ('MOSI' if ref == 'R36' else 'SCLK'), 'pin2': 'AGND'}})
    extra += [wire(180.34, 322.58, 205.74, 322.58), wire(205.74, 322.58, 231.14, 322.58),
              f'(junction (at 205.74 322.58) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))']
    extra += [label('MOSI',180.34,302.26), label('SCLK',205.74,302.26),
              label('EN',231.14,302.26), label('AGND',180.34,322.58)]
    extra.append(note('V1.2 F09: R36/R37 bias DIN and SCLK low; CS / full sequencing unresolved.\nF05: R38 = 0R FITTED: both LDOs held OFF. No functional enable source.\nDo not remove R38 or drive EN until F04/F13/F15/F16/F17 are resolved.\nUSB / external +3.3V can still backfeed the rail; OFF strap is not isolation.', 171.45, 330.2))
    updated = source[:root.end-1] + '\n' + '\n'.join(extra) + '\n' + source[root.end-1:]
    commit(source, updated, 'hardware', detail)


def specifications():
    source = SCH.read_text()
    root = parse(source)
    ss = symbols(root)
    assert {'R36','R37','R38'} <= set(ss)
    patches, details = [], []
    capacitor_refs = [f'C{i}' for i in (1,2,3,4,5,10,11,12,13,14,15,16,17,18,21,22,27,28,29,30,31,36,37,38,39,40,41,42,43,44,47,48)]
    requirements = {}
    for ref in capacitor_refs:
        assert props(ss[ref])['Value'] == '620pF'
        requirements[ref] = {'Dielectric': 'C0G/NP0', 'Tolerance': '1%',
                             'Qualification': 'F12/F14: matched input RC; component requirements only, electrode CMRR unverified'}
    for i in range(1,33):
        ref = f'R{i}'
        assert props(ss[ref])['Value'] == '2KΩ'
        requirements[ref] = {'Tolerance': '0.1%', 'Rated power': '>=0.1 W; verify temperature derating and fault pulses',
                             'Qualification': 'F12/F14: preserve 2k input topology; resistor rating does not establish wearer protection'}
    for ref in ('C25','C51'):
        requirements[ref] = {'Voltage rating': '>=10 V',
                             'Qualification': 'F14: qualify selected 1uF part at VCAP3 bias (~5.2V at 3.3V AVDD), including DC bias, tolerance and temperature'}
    requirements['C55'] = {'Leakage current': '<100 nA at operating bias and temperature',
                           'Qualification': 'F14: LP2985 section 7.1.3; retain 10nF BP bypass; exact MPN pending'}
    for ref, fields in requirements.items():
        n = ss[ref]
        assert not set(fields) & set(props(n)), f'{ref}: requirement already exists'
        x,y = one(n,'at')[1:3]
        patches.append((n.end-1, n.end-1, '\n' + '\n'.join(property_(k,v,x,y) for k,v in fields.items()) + '\n'))
        details.append({'finding': 'F12/F14' if ref in capacitor_refs or ref.startswith('R') else 'F14',
                        'reference': ref, 'fields_added': fields, 'value_and_connections': 'unchanged'})
    for n in children(root,'text'):
        if n[1].startswith('V2 PARTIAL CORRECTIONS'):
            text = ('V1.2 PARTIAL CORRECTIONS - NOT READY FOR POWER-UP OR WEARER USE\n'
                    'F04: LDO outputs remain parallel. F05: fitted R38 holds EN low; power architecture unresolved.\n'
                    'F06/F18: restore U1 CLK_EN after RESET; allow U2 clock/POR; configure before shared START.\n'
                    'F09: START/RESET/PWDN plus DIN/SCLK have pulldowns; CS/full sequencing unresolved.\n'
                    'Enable/settle 2.4V reference; verify gain/rate; keep PACE/RLD/WCT and RLD rerouting off.\n'
                    'F07/F08: protected body bias and wearer protection remain unimplemented.')
            at = one(n,'at')
            patches.append((n.start,n.end,note(text,at[1],at[2],1.27)))
            details.append({'finding':'F05/F09/F18','change':'replace stale V2/floating-EN note with actual V1.2 partial-correction state'})
    extra = note('V1.2 F12/F14 - PROCUREMENT REQUIREMENTS (not qualified installed parts)\n'
                 'R1-R32: 2k unchanged; 0.1%, >=0.1W, derating/pulse review required.\n'
                 'All 32 input 620pF caps: C0G/NP0, 1%; electrode impedance/CMRR still unverified.\n'
                 'C25/C51 VCAP3: 1uF unchanged, >=10V; qualify capacitance at ~5.2V DC.\n'
                 'C55 BP: 10nF unchanged; leakage <100nA at operating bias/temperature.\n'
                 'No MPN, footprint, physical performance or wearer-safety qualification is implied.', 266.7, 302.26)
    patches.append((root.end-1,root.end-1,'\n'+extra+'\n'))
    updated = source
    for start,end,replacement in sorted(patches,reverse=True):
        updated = updated[:start] + replacement + updated[end:]
    commit(source, updated, 'specifications', details)


def ground_scope():
    source = SCH.read_text()
    root = parse(source)
    matches = [n for n in children(root,'label') if n[1]=='AGND' and one(n,'at')[1:3]==['180.34','322.58']]
    assert len(matches)==1
    n=matches[0]
    replacement=label('AGND',180.34,322.58)
    updated=source[:n.start]+replacement+source[n.end:]
    commit(source,updated,'ground-scope',[{'finding':'F05/F09','change':'Use existing global AGND scope consistently at new common return; exact net membership unchanged. Removes new same_local_global_label ambiguity.'}])


if __name__ == '__main__':
    {'hardware': hardware, 'specifications': specifications, 'ground-scope': ground_scope}[sys.argv[1]]()
