"""Read-only, full-source extraction for the V0 versus active V1.4 comparison."""
import importlib.util,json,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('parser',OUT.parent/'extract_audit.py')
parser=importlib.util.module_from_spec(spec); spec.loader.exec_module(parser)
manifest=json.loads((OUT/'source_manifest.json').read_text())
for version,item in manifest.items():
    path=Path(item['path']); root=parser.parse(path.read_text())
    libs={x[1]:x for x in parser.children(parser.children(root,'lib_symbols')[0],'symbol')}
    instances=[]
    for s in parser.children(root,'symbol'):
        props={p[1]:p[2] for p in parser.children(s,'property')}
        lib_id=parser.first(s,'lib_id')[0]
        pins=[]
        for unit in parser.children(libs[lib_id],'symbol'):
            for pin in parser.children(unit,'pin'):
                pins.append({'number':parser.first(pin,'number')[0],'name':parser.first(pin,'name')[0], 'type':pin[1],'at':parser.first(pin,'at')})
        instances.append({'properties':props,'lib_id':lib_id,'pins':pins,'at':parser.first(s,'at'),'uuid':parser.first(s,'uuid')})
    inv={'source':str(path),'root_counts':dict(Counter(x[0] for x in root[1:] if isinstance(x,list))), 'symbols':instances,'sheets':parser.children(root,'sheet'), 'texts':parser.children(root,'text'), 'wires':parser.children(root,'wire'), 'junctions':parser.children(root,'junction'), 'labels':{k:parser.children(root,k) for k in ['label','global_label','hierarchical_label']},'no_connects':parser.children(root,'no_connect')}
    (OUT/f'{version}.inventory.json').write_text(json.dumps(inv,indent=2,ensure_ascii=False)+'\n')
    assert not inv['sheets'], 'Hierarchy found: read all child files before proceeding'
    tree=ET.parse(OUT/f'{version}.net.xml')
    parts=tree.findall('.//components/comp')
    lines=['COMPONENTS']+[c.get('ref')+' | '+c.findtext('value','')+' | '+c.findtext('datasheet','') for c in parts]+['\nNETS']
    for n in tree.findall('.//nets/net'):
        lines.append(n.get('name')+': '+', '.join(x.get('ref')+'.'+x.get('pin')+' ['+x.get('pinfunction','')+']' for x in n.findall('node')))
    (OUT/f'{version}.connectivity.txt').write_text('\n'.join(lines)+'\n')
    erc=json.loads((OUT/f'{version}.erc.json').read_text()); vs=[x for sh in erc['sheets'] for x in sh['violations']]
    lines=[f'{len(vs)} ERC messages; '+str(dict(Counter(x['type'] for x in vs)))]
    lines += [x['severity']+' | '+x['description']+' | '+'; '.join(i['description'] for i in x['items']) for x in vs]
    (OUT/f'{version}.erc_summary.txt').write_text('\n'.join(lines)+'\n')
    print(version, 'flat sheets=1', 'physical components='+str(len(parts)), 'root item counts='+str(inv['root_counts']))
    if version=='v1_4': print('ALL SCHEMATIC NOTES:\n'+'\n'.join(x[1] for x in inv['texts']))
