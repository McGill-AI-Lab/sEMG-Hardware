"""Verify report assertions against fresh native exports and source hashes."""
import csv,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
OUT=Path(__file__).resolve().parent; ROOT=OUT.parent.parent
checks=[]
def require(label,condition):
    assert condition,label
    checks.append(label)
nets={}; components={}
for v in ['v0','v1_4']:
    tree=ET.parse(OUT/f'{v}.net.xml')
    nets[v]={n.get('name'):{(x.get('ref'),x.get('pin')) for x in n.findall('node')} for n in tree.findall('.//nets/net')}
    components[v]={c.get('ref'):c for c in tree.findall('.//components/comp')}
    for ref,c in components[v].items():
        if ref.startswith('C'):
            for pin in ['1','2']:
                matches=[m for m in nets[v].values() if (ref,pin) in m]
                require(f'{v} {ref}.{pin} connected to another component',len(matches)==1 and any(r!=ref for r,p in matches[0]))
    for adc in ['U1','U2']:
        for pin in map(str,range(1,17)):
            m=next(m for m in nets[v].values() if (adc,pin) in m)
            rs=[r for r,p in m if r.startswith('R')]; cs=[r for r,p in m if r.startswith('C')]
            require(f'{v} {adc} input{pin}:2k/620p filter',len(rs)==len(cs)==1 and components[v][rs[0]].findtext('value')=='2KΩ' and components[v][cs[0]].findtext('value')=='620pF')
    inv=json.loads((OUT/f'{v}.inventory.json').read_text())
    require(f'{v} no omitted hierarchy',not inv['sheets'])
    for s in inv['symbols']:
        if s['properties'].get('Reference') in ['U1','U2']:
            pm={p['number']:p['name'] for p in s['pins']}
            require(f'{v} ADC embedded positive definitions',all(pm[p].startswith('AVDD') for p in ['19','21','22','54','56','59']) and all(pm[p]=='DVDD' for p in ['48','50']))
            require(f'{v} ADC embedded real digital ground definitions',all(pm[p]=='DGND' for p in ['33','49','51']))

require('V0 analog source absent',all(r in ['U1','U2','C18','C19','C69','C70'] for r,p in nets['v0']['+3.3VA']))
require('V0 LDO outputs paralleled',{('U4','5'),('U7','5')}<=nets['v0']['+3.3V'])
require('V0 LDO enables only input pair',nets['v0']['/EN']=={('U4','3'),('U7','3')})
require('V0 DGND isolated from actual ground',('BT1','2') not in nets['v0']['DGND'] and ('U1','33') not in nets['v0']['DGND'])
for adc in ['U1','U2']:
    require(f'V0 {adc} clock self-tie',nets['v0'][f'Net-({adc}-CLK)']=={(adc,'37'),(adc,'52')})
require('V0 reset controls without external bias',nets['v0']['/PWDN']=={('U1','35'),('U2','35'),('U6','6')} and nets['v0']['/RESET']=={('U1','36'),('U2','36'),('U6','7')})

require('V1.4 carrier has only ADCs and complete MCU board as ICs',{r for r in components['v1_4'] if r.startswith('U')}=={'U1','U2','U3'})
require('V1.4 battery/old LDOs removed',not ({'BT1','U4','U5','U7'} & components['v1_4'].keys()))
require('V1.4 board3V3 source header joins rail',{('U3','1'),('U3','2')}<=nets['v1_4']['/+3.3V'])
require('V1.4 board ground joins return',{('U3',p) for p in ['22','23','24','44']}<=nets['v1_4']['/GND'])
for adc in ['U1','U2']:
    require(f'V1.4 {adc} all positive supplies at3V3',{(adc,p) for p in ['19','21','22','54','56','59','48','50']}<=nets['v1_4']['/+3.3V'])
    require(f'V1.4 {adc} actual grounds/low ties valid',{(adc,p) for p in ['20','23','25','31','32','33','41','42','44','45','46','49','51','53','57','58']}<=nets['v1_4']['/GND'])
    require(f'V1.4 {adc} unused analog ties follow AVDD',{(adc,p) for p in ['17','18','62']}<=nets['v1_4']['/+3.3V'])
require('V1.4 actual shared clock connected',nets['v1_4']['/ADC_CLK']=={('U1','37'),('U2','37')})
require('V1.4 clock selection valid straps',('U1','52') in nets['v1_4']['/+3.3V'] and ('U2','52') in nets['v1_4']['/GND'])
for ref,net in [('R33','/START'),('R34','/RESET'),('R35','/PWDN'),('R36','/SPI_MOSI'),('R37','/SPI_SCLK')]:
    require(ref+'10k low bias',components['v1_4'][ref].findtext('value')=='10k' and (ref,'1') in nets['v1_4'][net] and (ref,'2') in nets['v1_4']['/GND'])
for ref,net in [('R39','/CS_ADC1'),('R40','/CS_ADC2'),('R41','/GPIO3_STRAP')]:
    require(ref+'10k high bias',components['v1_4'][ref].findtext('value')=='10k' and (ref,'1') in nets['v1_4'][net] and (ref,'2') in nets['v1_4']['/+3.3V'])
require('V1.4 shared MISO intended inputs',{('U1','43'),('U2','43'),('U3','37')}==nets['v1_4']['/SPI_MISO'])
for net,node in [('/CS_ADC1',('U3','27')),('/CS_ADC2',('U3','36')),('/DRDY_ADC1',('U3','38')),('/DRDY_ADC2',('U3','39'))]:
    require(net+'actual board pin',node in nets['v1_4'][net])
rail_caps={r for r,p in nets['v1_4']['/+3.3V'] if r.startswith('C') and (r,'2') in nets['v1_4']['/GND']}
values={'0.1uF':0.1,'1uF':1,'10uF':10}
bank=sum(values[components['v1_4'][r].findtext('value')] for r in rail_caps)
require('V1.4 nominal rail capacitor sum42.6uF',abs(bank-42.6)<1e-9)
for v,n in [('v0',62),('v1_4',7)]:
    erc=json.loads((OUT/f'{v}.erc.json').read_text())
    require(v+'native ERC count',sum(len(s['violations']) for s in erc['sheets'])==n)
for v,item in json.loads((OUT/'source_manifest.json').read_text()).items():
    require(v+'source unchanged',hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256'])
expected=[f'{c}{i}' for c,n in zip('ABCDEFGHIJKL',[1,1,7,2,9,5,7,2,5,4,3,2]) for i in range(1,n+1)]
data=json.loads((OUT/'condition_findings.json').read_text())
require('48 conditions in order',[r['ID'] for r in data]==expected)
with (ROOT/'AMBRFLOW_V0_V1_4_CODEX_COMPARISON.csv').open(newline='') as f:
    reader=csv.reader(f); header=next(reader); csvrows=list(reader)
require('CSV exactly2 columns,48 condition rows',len(header)==2 and len(csvrows)==48 and all(len(r)==2 for r in csvrows))
require('CSV IDs preserved',[r[0].split(' —')[0] for r in csvrows]==expected)
report=(ROOT/'AMBRFLOW_V0_V1_4_CODEX_COMPARISON.md').read_text()
require('report all48 main condition rows',re.findall(r'^\| \*\*([A-L][1-9]) —',report.split('## Complete checklist')[1],re.M)==expected)
require('report no formatting placeholders','@@KEEP' not in report)
for target in re.findall(r'\]\(([^)]+)\)',report):
    if not target.startswith('https://'): require('local link '+target,(ROOT/target.split('#')[0]).exists())
result={'result':'PASS','checks_passed':len(checks),'classification_counts':dict(Counter(r['Classification'] for r in data)),'checks':checks,'limits':'Connectivity/document consistency only. No physical, firmware or dynamic-performance validation.'}
(OUT/'validation_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
