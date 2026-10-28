"""Read-only extraction of both complete KiCad schematic S-expressions."""
import re, json, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

BASE = Path('/Users/home/Documents/Projects/Hardware/sEMG-Hardware')
SOURCES = {
    'v0': BASE / 'Archive/electronics-archive/open-semg-16-electronics-v0/open-semg-16.kicad_sch',
    'v1': BASE / 'open-semg-16-v1/open-semg-16-v1.kicad_sch',
}

def parse(text):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack, root = [], None
    for token in tokens:
        if token == '(':
            node = []
            if stack: stack[-1].append(node)
            else: root = node
            stack.append(node)
        elif token == ')': stack.pop()
        else:
            if token.startswith('"'):
                token = token[1:-1].replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
            stack[-1].append(token)
    assert not stack
    return root

def children(node, key):
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == key]

def first(node, key, default=None):
    items = children(node, key)
    return items[0][1:] if items else default

def main():
    manifest = {}
    for version, path in SOURCES.items():
        raw = path.read_text()
        root = parse(raw)
        libs = {x[1]: x for x in children(children(root, 'lib_symbols')[0], 'symbol')}
        instances = []
        for s in children(root, 'symbol'):
            properties = {p[1]: p[2] for p in children(s, 'property')}
            lib_id = first(s, 'lib_id')[0]
            pins = []
            for unit in children(libs[lib_id], 'symbol'):
                for pin in children(unit, 'pin'):
                    pins.append({'number': first(pin, 'number')[0], 'name': first(pin, 'name')[0],
                                 'type': pin[1], 'local_at': first(pin, 'at')})
            instances.append({'reference': properties.get('Reference'), 'value': properties.get('Value'),
                              'properties': properties, 'lib_id': lib_id, 'at': first(s, 'at'),
                              'mirror': first(s, 'mirror'), 'uuid': first(s, 'uuid'), 'pins': pins})
        obj = {'source': str(path), 'root_item_counts': dict(Counter(x[0] for x in root[1:] if isinstance(x, list))),
               'symbols': instances, 'sheets': children(root, 'sheet'), 'texts': children(root, 'text'),
               'labels': {k: children(root, k) for k in ['label', 'global_label', 'hierarchical_label']},
               'wires': children(root, 'wire'), 'junctions': children(root, 'junction'), 'no_connects': children(root, 'no_connect')}
        Path(f'EVIDENCE/{version}.schematic_inventory.json').write_text(json.dumps(obj, indent=2, ensure_ascii=False))
        manifest[version] = {'source': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                             'bytes': path.stat().st_size, 'sheet_count': 1 + len(obj['sheets']),
                             'placed_symbols': len(instances)}
        tree = ET.parse(f'EVIDENCE/{version}.net.xml')
        text = [f'Source: {path}', 'COMPONENTS']
        for c in tree.findall('.//components/comp'):
            text.append(f"{c.get('ref')}: {c.findtext('value')} | {c.findtext('libsource')} | {c.findtext('datasheet', '')}")
        text.append('\nNETS (pin names are those in the embedded symbol)')
        for n in tree.findall('.//nets/net'):
            text.append(n.get('name') + ': ' + ', '.join(f"{x.get('ref')}.{x.get('pin')} [{x.get('pinfunction', '')}]" for x in n.findall('node')))
        Path(f'EVIDENCE/{version}.connectivity.txt').write_text('\n'.join(text) + '\n')
        erc = json.loads(Path(f'EVIDENCE/{version}.erc.json').read_text())
        violations = [x for s in erc['sheets'] for x in s['violations']]
        text = [f'KiCad {erc["kicad_version"]}: {len(violations)} reported violations', str(dict(Counter(x['type'] for x in violations)))]
        for x in violations:
            text.append(f"{x['severity']} | {x['type']} | {x['description']} | " + ' ; '.join(f"{i['description']} at {i.get('pos')}" for i in x['items']))
        Path(f'EVIDENCE/{version}.erc_summary.txt').write_text('\n'.join(text) + '\n')
    Path('EVIDENCE/source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__': main()
