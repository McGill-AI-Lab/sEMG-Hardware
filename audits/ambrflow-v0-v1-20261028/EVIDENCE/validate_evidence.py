"""Cross-check final report assertions against exported source connectivity."""
import csv, hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

checks=[]
def check(name, condition):
    if not condition: raise AssertionError(name)
    checks.append(name)

nets={}
for v in ['v0','v1']:
    tree=ET.parse(f'EVIDENCE/{v}.net.xml')
    nets[v]={n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in tree.findall('.//nets/net')}
    for r in ['U1','U2']:
        analog={(r,p) for p in ['19','21','22','54','56','59']}
        check(f'{v} {r} analog positive supply membership',analog<=nets[v]['+3.3VA' if v=='v0' else 'AGND'])
        digital={(r,p) for p in ['48','50']}
        check(f'{v} {r} digital positive supply membership',digital<=nets[v]['+3.3V' if v=='v0' else 'DGND'])
        returns={(r,p) for p in ['20','23','25','32','33','49','51','53','57','58']}
        check(f'{v} {r} actual ground membership',returns<=nets[v]['AGND'])
    other='U7' if v=='v0' else 'U5'
    check(f'{v} parallel LDO outputs',{('U4','5'),(other,'5')}<=nets[v]['+3.3V'])
    check(f'{v} enable has only two inputs',nets[v]['/EN']=={('U4','3'),(other,'3')})
    check(f'{v} battery and LDO grounds share AGND',{('BT1','2'),('U4','2'),(other,'2')}<=nets[v]['AGND'])
    components={c.get('ref'):c.findtext('value') for c in tree.findall('.//components/comp')}
    for ref in [c for c in components if c.startswith('C')]:
        for pin in ['1','2']:
            matches=[m for m in nets[v].values() if (ref,pin) in m]
            check(f'{v} {ref}.{pin} has another component terminal',len(matches)==1 and any(x[0]!=ref for x in matches[0]))
    for r in ['U1','U2']:
        for pin in map(str,range(1,17)):
            m=next(m for m in nets[v].values() if (r,pin) in m)
            rs=[x for x,p in m if x.startswith('R')]
            cs=[x for x,p in m if x.startswith('C')]
            check(f'{v} {r} input{pin} has unchanged2k/620p network',len(rs)==len(cs)==1 and components[rs[0]]=='2KΩ' and components[cs[0]]=='620pF')

check('V0 analog island has no regulator/battery source',all(ref in ['U1','U2','C18','C19','C69','C70'] for ref,pin in nets['v0']['+3.3VA']))
check('V0 module true grounds valid',{('U6',p) for p in ['1','40','41']}<=nets['v0']['AGND'])
check('V0 DGND remains separate control island',not ({('BT1','2'),('U1','33'),('U6','1')} & nets['v0']['DGND']))
check('V1 controller grounds isolated',{('U3',p) for p in ['22','23','24','44']}<=nets['v1']['DGND'] and ('BT1','2') not in nets['v1']['DGND'])
check('V1 four capacitor returns isolated',{(c,'2') for c in ['C8','C9','C34','C35']}<=nets['v1']['DGND'])
check('V1 four digital capacitor positives on3.3V',{(c,'1') for c in ['C8','C9','C34','C35']}<=nets['v1']['+3.3V'])
check('V1 unused analog pins17/18/62 tied3.3V',{(r,p) for r in ['U1','U2'] for p in ['17','18','62']}<=nets['v1']['+3.3V'])
for r in ['U1','U2']:
    check(f'V0 {r} clock self-loop has no driver',nets['v0'][f'Net-({r}-CLK)']=={(r,'37'),(r,'52')})
check('V1 slave ADC_CLK sole node',nets['v1']['ADC_CLK']=={('U2','37')})
check('V1 master CLK unconnected',any(m=={('U1','37')} and name.startswith('unconnected-') for name,m in nets['v1'].items()))
check('V1 separate chip selects',('U1','39') in nets['v1']['/CS_ADC1'] and ('U2','39') in nets['v1']['/CS_ADC2'])
check('V1 shared MISO outputs',{('U1','43'),('U2','43'),('U3','19')}<=nets['v1']['/MISO'])

for v in ['v0','v1']:
    erc=json.loads(Path(f'EVIDENCE/{v}.erc.json').read_text())
    violations=[x for s in erc['sheets'] for x in s['violations']]
    check(f'{v} reported ERC count',len(violations)==(62 if v=='v0' else 65))
    inventory=json.loads(Path(f'EVIDENCE/{v}.schematic_inventory.json').read_text())
    check(f'{v} contains no omitted hierarchy',not inventory['sheets'])
    for x in inventory['symbols']:
        if x['reference'] in ['U1','U2']:
            pinmap={p['number']:p['name'] for p in x['pins']}
            check(f'{v} embedded {x["reference"]} ADS supply definitions',all(pinmap[p].startswith('AVDD') for p in ['19','21','22','54','56','59']) and all(pinmap[p]=='DVDD' for p in ['48','50']) and all(pinmap[p]=='DGND' for p in ['33','49','51']))

expected=[f'{c}{i}' for c,n in zip('ABCDEFGHIJKL',[1,1,7,2,9,5,7,2,5,4,3,2]) for i in range(1,n+1)]
with Path('AMBRFLOW_ISSUE_MATRIX.csv').open(newline='') as f: rows=list(csv.DictReader(f))
check('CSV all48 unique IDs in order',[r['ID'] for r in rows]==expected)
check('CSV required12 columns',len(rows[0])==12)
check('CSV every required field filled',all(all(row.values()) for row in rows))
counts=Counter(r['Classification'] for r in rows)
check('CSV classification counts',counts==Counter({'CANNOT VERIFY':25,'NOT APPLICABLE':10,'NOT FOUND':6,'STILL PRESENT':4,'NEW IN V1':2,'PARTIALLY FIXED':1}))
for p in Path('.').glob('AMBRFLOW_*.md'):
    content=p.read_text()
    check(f'{p} no formatting placeholders','@@PROTECTED' not in content)
    for target in re.findall(r'\]\(([^)]+)\)',content):
        if not target.startswith('https://'): check(f'{p} local target {target}',Path(target.split('#')[0]).exists())
detail=Path('AMBRFLOW_DETAILED_AUDIT.md').read_text()
check('Detailed report includes all48 issue headings',re.findall(r'^### ([A-L][1-9]) —',detail,re.M)==expected)
manifest=json.loads(Path('EVIDENCE/source_manifest.json').read_text())
for v,item in manifest.items(): check(f'{v} source schematic hash unchanged',hashlib.sha256(Path(item['source']).read_bytes()).hexdigest()==item['sha256'])
out={'result':'PASS','checks_passed':len(checks),'checks':checks,'condition_counts':dict(counts),'limits':'Connectivity/document validation only. No physical, firmware or transient performance validation.'}
Path('EVIDENCE/validation_results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
