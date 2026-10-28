"""Native KiCad exports plus exhaustive baseline pin/net regression checks.

Run with a stage name: after-hardware or final. Artifacts stay in this directory.
These are static schematic checks, not analog-performance or safety validation.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from edit_v1_2 import parse, children, one, props, symbols

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1] / 'v1.2'
SCH = ROOT / 'open-semg-16-v1.2.kicad_sch'
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


def native(path):
    root = ET.parse(path).getroot()
    comps = {c.get('ref'): {'value': c.findtext('value'),
             'footprint': c.findtext('footprint'),
             'libsource': dict(c.find('libsource').attrib),
             'fields': {f.get('name'): f.text for f in c.findall('./fields/field')},
             'pins': {}} for c in root.findall('./components/comp')}
    nets = {}
    for n in root.findall('./nets/net'):
        members = {(p.get('ref'), p.get('pin')) for p in n.findall('node')}
        nets[n.get('name')] = members
        for ref, pin in members:
            comps[ref]['pins'][pin] = n.get('name')
    return comps, nets


def erc(path):
    report = json.loads(path.read_text())
    violations = [v for s in report['sheets'] for v in s['violations']]
    return {'severities': dict(Counter(v['severity'] for v in violations)),
            'type_severity': dict(Counter(f"{v['type']}:{v['severity']}" for v in violations)),
            'total': len(violations)}, violations


def main(stage):
    assert stage in ('after-hardware', 'final')
    logs = []
    commands = [
        ['sch','export','netlist','--format','kicadxml','--output',str(OUT/f'{stage}-netlist.xml'),str(SCH)],
        ['sch','erc','--format','json','--severity-all','--output',str(OUT/f'{stage}-erc.json'),str(SCH)]]
    if stage == 'final':
        commands.append(['sch','export','pdf','--output',str(OUT/'final-schematic.pdf'),str(SCH)])
        commands.append(['sch','export','svg','--output',str(OUT/'final-svg'),str(SCH)])
    for args in commands:
        result = subprocess.run([CLI]+args, text=True, capture_output=True)
        logs.append({'argv':[CLI]+args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        assert result.returncode == 0, logs[-1]
    (OUT/f'{stage}-cli-log.json').write_text(json.dumps(logs,indent=2)+'\n')
    initial, ni = native(OUT/'initial-netlist.xml')
    final, nf = native(OUT/f'{stage}-netlist.xml')
    checks = []

    def check(name, condition):
        checks.append({'check':name,'passed':bool(condition)})

    def pin(ref, num):
        return final[ref]['pins'][str(num)]

    check('Only R36, R37 and R38 added to all 130 baseline components',set(final)==set(initial)|{'R36','R37','R38'})
    for ref, comp in initial.items():
        for key in ('value','footprint','libsource','pins'):
            check(f'{ref}: baseline {key} retained', final[ref][key]==comp[key])
    additions = {'/MOSI':{('R36','1')},'/SCLK':{('R37','1')},'/EN':{('R38','1')},
                 'AGND':{('R36','2'),('R37','2'),('R38','2')}}
    check('No net introduced or removed',set(ni)==set(nf))
    for name, members in ni.items():
        check(f'{name}: exact baseline membership plus only declared resistor terminals',nf[name]==members|additions.get(name,set()))
    for ref, net, value in [('R36','/MOSI','10k'),('R37','/SCLK','10k'),('R38','/EN','0')]:
        check(f'{ref}: intended value and endpoints',final[ref]['value']==value and pin(ref,1)==net and pin(ref,2)=='AGND')
    for adc in ('U1','U2'):
        check(f'{adc}: AVDD/AVDD1/DVDD remain on intended +3.3V',all(pin(adc,n)=='+3.3V' for n in (19,21,22,54,56,59,48,50)))
        check(f'{adc}: physical returns and intended digital lows remain AGND',all(pin(adc,n)=='AGND' for n in (20,23,25,31,32,33,41,42,44,45,46,49,51,53,57,58)))
        check(f'{adc}: aux 17/18/62 still follow actual AVDD',all(pin(adc,n)==pin(adc,19) for n in (17,18,62)))
        for n in range(1,17):
            check(f'{adc} input{n}: exact baseline net membership',nf[pin(adc,n)]==ni[initial[adc]['pins'][str(n)]])
    for ch in range(1,17):
        adc='U1' if ch<=8 else 'U2'
        adc_ch=(ch-1)%8+1
        for polarity, p, rnum in [('P',18-2*adc_ch,2*ch-1),('N',17-2*adc_ch,2*ch)]:
            check(f'channel{ch}{polarity}: same ADC and 2k resistor mapping',pin(adc,p)==pin(f'R{rnum}',2))
            check(f'channel{ch}{polarity}: electrode terminal through correct resistor',pin(f'E{ch}',1 if polarity=='P' else 2)==pin(f'R{rnum}',1))
    check('Shared conversion CLK remains only U1.37/U2.37/TP1.1',nf['ADC_CLK']=={('U1','37'),('U2','37'),('TP1','1')})
    check('Master/slave CLKSEL retained',pin('U1',52)=='+3.3V' and pin('U2',52)=='AGND')
    check('Both reference nets remain independent',pin('U1',24)!=pin('U2',24))
    for adc,cbase in [('U1',0),('U2',26)]:
        for p, caps in [(24,(19,20)),(28,(23,)),(30,(24,)),(55,(25,)),(26,(26,))]:
            for c in caps:
                check(f'{adc} bypass {p}/C{c+cbase}: topology and return retained',pin(adc,p)==pin(f'C{c+cbase}',1) and pin(f'C{c+cbase}',2)=='AGND')
    check('RLD/WCT disconnections retained; no body drive added',all(pin(adc,p).startswith('unconnected-') for adc in ('U1','U2') for p in (60,61,63,64)))
    check('F04 remains open: parallel LDO outputs unaltered',pin('U4',5)==pin('U5',5)=='+3.3V')
    check('F05: EN has only regulator inputs and fitted zero-ohm OFF strap',nf['/EN']=={('U4','3'),('U5','3'),('R38','1')} and pin('R38',2)=='AGND' and final['R38']['value']=='0')
    s0=(OUT/'baseline/open-semg-16-v1.2.kicad_sch').read_text()
    sf=SCH.read_text(); r0=parse(s0); rf=parse(sf)
    libs0={n[1]:s0[n.start:n.end] for n in children(one(r0,'lib_symbols'),'symbol')}
    libsf={n[1]:sf[n.start:n.end] for n in children(one(rf,'lib_symbols'),'symbol')}
    check('Embedded libraries byte-identical',libs0==libsf)
    for kind in ('wire','no_connect','global_label','junction'):
        old={s0[n.start:n.end] for n in children(r0,kind)}
        new={sf[n.start:n.end] for n in children(rf,kind)}
        check(f'Every pre-existing {kind} object byte-preserved',old<=new)
    check('No additional NC marker',len(children(r0,'no_connect'))==len(children(rf,'no_connect'))==8)
    check('Exactly three local signal labels and one global AGND label added',len(children(rf,'label'))==len(children(r0,'label'))+3 and len(children(rf,'global_label'))==len(children(r0,'global_label'))+1)
    ss=symbols(rf)
    if stage=='final':
        input_caps=[1,2,3,4,5,10,11,12,13,14,15,16,17,18,21,22,27,28,29,30,31,36,37,38,39,40,41,42,43,44,47,48]
        for i in input_caps:
            f=props(ss[f'C{i}']);check(f'C{i}: C0G/NP0 1% requirement exported',f.get('Dielectric')=='C0G/NP0' and f.get('Tolerance')=='1%' and final[f'C{i}']['fields'].get('Dielectric')=='C0G/NP0')
        for i in range(1,33):
            f=props(ss[f'R{i}']);check(f'R{i}: 0.1% >=0.1W requirement exported',f.get('Tolerance')=='0.1%' and f.get('Rated power','').startswith('>=0.1 W') and final[f'R{i}']['fields'].get('Tolerance')=='0.1%')
        for ref in ('C25','C51'):
            check(f'{ref}: >=10V requirement exported',props(ss[ref]).get('Voltage rating')=='>=10 V' and final[ref]['fields'].get('Voltage rating')=='>=10 V')
        check('C55 leakage <100nA requirement exported',props(ss['C55']).get('Leakage current','').startswith('<100 nA') and final['C55']['fields'].get('Leakage current','').startswith('<100 nA'))
    history=json.loads((OUT/'pre-edit-hashes.json').read_text())
    for path, sha in {**history['protected'],**history['active_existing'],**history['review_existing']}.items():
        if Path(path)==SCH:continue
        check(f'Protected/pre-existing file unchanged: {path}',Path(path).is_file() and hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha)
    base_erc, vb=erc(OUT/'initial-erc.json');new_erc,vf=erc(OUT/f'{stage}-erc.json')
    expected_types=Counter(base_erc['type_severity']); expected_types['pin_not_driven:error']-=1
    check('ERC changes limited to removal of undriven U4 EN after OFF strap',new_erc['type_severity']==dict(expected_types) and new_erc['severities']=={'error':34,'warning':26} and new_erc['total']==60)
    def violation_key(v):
        # KiCad may choose a different unchanged AVDD/ground label to represent
        # the same alias warning across runs. Compare its complete diagnosis;
        # original label bytes and all net memberships are checked separately.
        if v['type']=='multiple_net_names':
            return (v['type'],v['severity'],v['description'],())
        return (v['type'],v['severity'],v['description'],tuple(sorted(i.get('uuid','') for i in v.get('items',[]))))
    removed=[v for v in vb if v['type']=='pin_not_driven' and any('Symbol U4 Pin 3 ' in i.get('description','') for i in v.get('items',[]))]
    check('Exactly original U4 EN undriven violation removed; all other ERC identities preserved',len(removed)==1 and Counter(map(violation_key,vb))-Counter(map(violation_key,removed))==Counter(map(violation_key,vf)))
    prior_c,prior_n=native(OUT.parents[1]/'reviews_v1.1/diagnostics/final-netlist.xml')
    check('Initial V1.2 net partitions match V1.1 final',set(map(frozenset,ni.values()))==set(map(frozenset,prior_n.values())))
    result={'stage':stage,'passed':all(c['passed'] for c in checks),'assertion_count':len(checks),
            'failed':[c['check'] for c in checks if not c['passed']],'initial_erc':base_erc,'stage_erc':new_erc,
            'component_count':len(final),'net_count':len(nf),'checks':checks,
            'limits':'Static connectivity/specification/file-integrity checks only. No powered, analog, physical, firmware or wearer-safety qualification.'}
    (OUT/f'{stage}-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/f'{stage}-connectivity.json').write_text(json.dumps({'components':final,'nets':{k:sorted(v) for k,v in nf.items()}},indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
    assert result['passed'], result['failed']


if __name__=='__main__':
    main(sys.argv[1])
