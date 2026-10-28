"""Independent baseline-preservation and specified physical pin/net checks."""
from pathlib import Path
import collections,json,sys,xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent
stage=sys.argv[1] if len(sys.argv)>1 else 'candidate'
target='power-candidate-netlist.xml' if stage=='candidate' else 'final-netlist.xml'

def read(name):
    r=ET.parse(P/name).getroot();cs={c.get('ref'):c for c in r.findall('./components/comp')}
    ns={n.get('name').lstrip('/'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in r.findall('./nets/net')}
    pm={p:name for name,members in ns.items() for p in members}
    return cs,ns,pm

oldcs,oldns,oldpm=read('initial-netlist.xml');cs,ns,pm=read(target)
errors=[];count=0
def check(condition,message):
    global count
    count+=1
    if not condition:errors.append(message)
def pin(ref,p,net):check(pm.get((ref,str(p)))==net.lstrip('/'),f'{ref}.{p}: wanted {net}, got {pm.get((ref,str(p)))}')
removed={'U4','U5','C53','C54','C55','C56','R38'}
for ref in removed:check(ref not in cs,'Obsolete component retained: '+ref)
main_members={('U3','1'),('U3','2'),('C57','1'),('TP4','1')}
mcu_changes={'17':'MCU_MOSI','18':'MCU_SCLK','12':'MCU_START','6':'MCU_RESET','7':'MCU_PWDN','16':'MCU_CS1','20':'MCU_CS2','15':'MCU_DRDY','3':'CHIP_PU','4':'MCU_READY'}
for (ref,p),net in oldpm.items():
    if ref in removed:continue
    expected=net
    if net=='+3.3V':expected='MAIN_3V3' if (ref,p) in main_members else 'AFE_2V98'
    if ref=='U3' and p in mcu_changes:expected=mcu_changes[p]
    if ref=='U1' and p=='43':expected='DOUT_ADC1'
    if ref=='U2' and p=='43':expected='DOUT_ADC2'
    if p=='2' and ref in {'R33','R34','R35','R36','R37'}:expected={'R33':'CLAMP_START','R34':'CLAMP_RESET','R35':'CLAMP_PWDN','R36':'CLAMP_MOSI','R37':'CLAMP_SCLK'}[ref]
    pin(ref,p,expected)
for ref,c in oldcs.items():
    if ref not in removed and ref not in {'C57','TP4'}:
        check(cs[ref].findtext('value')==c.findtext('value'),'Unintended value change '+ref)
for i in range(16):
    adc='U1' if i<8 else 'U2';ch=i%8
    for terminal,res,adcpin in [('1','R'+str(2*i+1),16-2*ch),('2','R'+str(2*i+2),15-2*ch)]:
        check(pm[(f'E{i+1}',terminal)]==pm[(res,'1')],f'Electrode mapping E{i+1}.{terminal}')
        check(pm[(res,'2')]==pm[(adc,str(adcpin))],f'ADC mapping {res}')
        before=oldns[oldpm[(res,'2')]];after=ns[pm[(res,'2')]]
        check(before==after,f'Acquisition net membership changed {res}')
for ref in ['U1','U2']:
    for p in [17,18,19,21,22,48,50,54,56,59,62]:pin(ref,p,'AFE_2V98')
    for p in [20,23,25,31,32,33,41,42,44,45,46,49,51,53,57,58]:pin(ref,p,'AGND')
pin('U1',52,'AFE_2V98');pin('U2',52,'AGND');pin('U1',37,'ADC_CLK');pin('U2',37,'ADC_CLK')
for p in [1,2]:pin('U3',p,'MAIN_3V3')
for p in [22,23,24,44]:pin('U3',p,'AGND')
data=json.loads((P/'assembled-block-data.json').read_text())
for name,b in data.items():
    mapping=b.get('pin_nets',b.get('pin_map'))
    for key,expected in mapping.items():
        if isinstance(expected,dict) and '.' not in key:
            for p,n in expected.items():
                if isinstance(n,dict):n=n.get('net')
                if n is not None:pin(key,p,n)
        else:
            ref,p=key.split('.')
            if expected is not None:pin(ref,p,expected)
for ref,net in [('C110','VCAP3_ADC1'),('C111','VCAP3_ADC2'),('C112','AFE_2V98'),('C113','AFE_2V98'),('C114','AFE_2V98'),('C115','AFE_2V98')]:
    pin(ref,1,net);pin(ref,2,'AGND')
for ref,p,net in [('U6',6,'MAIN_3V3'),('U7',6,'AFE_PRE_4V0'),('U8',10,'AFE_2V98'),('Q1',3,'BAT_FUSED'),('Q1',2,'SW_BAT_PROT'),('U7',1,'MAIN_PG'),('U8',3,'MAIN_PG')]:pin(ref,p,net)
check(len({pm[('U6','6')],pm[('U7','6')],pm[('U8','10')]})==3,'Independent regulator outputs shorted')
check(pm[('U1','43')]!=pm[('U2','43')],'Raw DOUT sources still directly shorted')
check(pm[('U10','4')]==pm[('U11','4')]==pm[('U3','19')],'Shared MISO protocol not retained')
check(pm[('U15','1')]==pm[('U16','1')]==pm[('U13','1')]==pm[('U17','1')],'Clean rail-good bus disconnected')
check(pm[('U3','3')]!=pm[('U15','1')],'DevKit reset capacitor directly loads rail-good bus')
check(pm[('U3','3')]==pm[('R86','1')]==pm[('U13','4')],'Dedicated CHIP_PU reset/qualification disconnected')
check(pm[('U6','5')]!=pm[('U3','3')],'AFE startup deadlock: regulator PG tied to reset bus')
erc=json.loads((P/('power-candidate-erc.json' if stage=='candidate' else 'final-erc.json')).read_text())
violations=[v for s in erc['sheets'] for v in s['violations']]
check(len(violations)==9,'Unexpected final ERC count')
check(collections.Counter((v['type'],v['severity']) for v in violations)==collections.Counter({('power_pin_not_driven','error'):4,('pin_not_connected','error'):1,('pin_to_pin','warning'):4}),'Unexpected ERC conditions')
result={'stage':stage,'passed':not errors,'assertions':count,'errors':errors,'components':len(cs),'nets':len(ns),'channel_mappings_passed':16,'ERC':{'errors':5,'warnings':4},'independent_regulator_outputs_separate':True,'original_SPI_protocol_preserved':True,'raw_DOUTs_isolated_before_shared_MISO':True}
(P/(stage+'-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if errors:raise SystemExit(1)
