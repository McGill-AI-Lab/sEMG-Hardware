"""Native ERC/netlist validation and exhaustive comparison to this task baseline."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from implement import OUT,ACTIVE,SCH,CLI,LIB,NC_PINS,SHORT_WIRES,CS_WIRE,AVDD_LABELS,DVDD_LABELS,parse,all_,one,id_,symbols,props,pin_positions


def native(path):
    r=ET.parse(path).getroot();comps={}
    for c in r.findall('./components/comp'):
        comps[c.get('ref')]={'value':c.findtext('value'),'footprint':c.findtext('footprint'),
            'libsource':dict(c.find('libsource').attrib),'pins':{}}
    nets={}
    for n in r.findall('./nets/net'):
        members={(p.get('ref'),p.get('pin')) for p in n.findall('node')};nets[n.get('name')]=members
        for ref,pin in members:comps[ref]['pins'][pin]=n.get('name')
    return comps,nets


def reports(path):
    r=json.loads(path.read_text());return r,[v for s in r['sheets'] for v in s['violations']]


def main(stage):
    assert stage in ('power','unused','final')
    logs=[];commands=[['sch','export','netlist','--format','kicadxml','--output',str(OUT/f'{stage}-netlist.xml'),str(SCH)],
        ['sch','erc','--format','json','--severity-all','--output',str(OUT/f'{stage}-erc.json'),str(SCH)]]
    if stage=='final':commands += [['sch','export','pdf','--output',str(OUT/'final-schematic.pdf'),str(SCH)],
        ['sch','export','svg','--output',str(OUT/'final-svg'),str(SCH)]]
    for args in commands:
        p=subprocess.run([CLI]+args,text=True,capture_output=True)
        logs.append({'argv':[CLI]+args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        assert p.returncode==0,logs[-1]
    (OUT/f'{stage}-cli-log.json').write_text(json.dumps(logs,indent=2)+'\n')
    a,ni=native(OUT/'initial-netlist.xml');b,nf=native(OUT/f'{stage}-netlist.xml')
    checks=[]
    def check(name,condition):checks.append({'check':name,'passed':bool(condition)})
    def pin(ref,num):return b[ref]['pins'][str(num)]
    check('All133 existing non-power components retained; no new components',set(a)==set(b) and len(b)==133)
    expected_changed={('U4','5'),('C54','1')}
    changed=[]
    for ref,c in a.items():
        for field in ('value','footprint','libsource'):check(f'{ref}: original {field} retained',b[ref][field]==c[field])
        check(f'{ref}: same physical pin number set',set(c['pins'])==set(b[ref]['pins']))
        for num,old in c['pins'].items():
            expected='/LP2985_OUT_DISABLED' if (ref,num) in expected_changed else old
            check(f'{ref}.{num}: only permitted net assignment',pin(ref,num)==expected)
            if pin(ref,num)!=old:changed.append({'component':ref,'pin':num,'before':old,'after':pin(ref,num)})
    check('Exactly U4.5 and C54.1 deliberately changed nets',{(c['component'],c['pin']) for c in changed}==expected_changed)
    check('Isolated U4 output contains only U4.5 and C54.1',nf['/LP2985_OUT_DISABLED']==expected_changed)
    check('One net added for physical output separation',set(nf)==set(ni)|{'/LP2985_OUT_DISABLED'})
    for net,members in ni.items():
        expected=members-expected_changed if net=='+3.3V' else members
        check(f'{net}: exact baseline membership, allowing only F04 split',nf[net]==expected)
    check('Both LDO EN remain at fitted OFF strap',nf['/EN']=={('U4','3'),('U5','3'),('R38','1')} and pin('R38',2)=='AGND' and b['R38']['value']=='0')
    for adc in ('U1','U2'):
        check(f'{adc}: repaired supplies/aux ties remain main rail',all(pin(adc,p)=='+3.3V' for p in (17,18,19,21,22,48,50,54,56,59,62)))
        check(f'{adc}: physical returns/unused lows unchanged',all(pin(adc,p)=='AGND' for p in (20,23,25,31,32,33,41,42,44,45,46,49,51,53,57,58)))
        for p in range(1,17):check(f'{adc} input{p}: exact acquired net unchanged',nf[pin(adc,p)]==ni[a[adc]['pins'][str(p)]])
    for channel in range(1,17):
        adc='U1' if channel<=8 else 'U2';ch=(channel-1)%8+1
        for pol,adcp,rnum,ep in [('P',18-2*ch,2*channel-1,1),('N',17-2*ch,2*channel,2)]:
            check(f'Channel{channel}{pol}: electrode/R/ADC polarity retained',pin(f'E{channel}',ep)==pin(f'R{rnum}',1) and pin(f'R{rnum}',2)==pin(adc,adcp))
    check('Distinct ADC reference outputs retained',pin('U1',24)!=pin('U2',24))
    for i in range(1,58):
        check(f'C{i}: both terminals preserved except documented C54 output split',b[f'C{i}']['pins']==({**a[f'C{i}']['pins'],'1':'/LP2985_OUT_DISABLED'} if i==54 else a[f'C{i}']['pins']))
    check('RLD/WCT NC intent retained',all(pin(adc,p).startswith('unconnected-') for adc in ('U1','U2') for p in (60,61,63,64)))
    s0=(OUT/'baseline/open-semg-16-v1.2.kicad_sch').read_text();sf=SCH.read_text()
    r0=parse(s0,'kicad_sch');rf=parse(sf,'kicad_sch');ss0=symbols(r0);ssf=symbols(rf)
    for ref in a:check(f'{ref}: complete instance source bytes unchanged',s0[ss0[ref].start:ss0[ref].end]==sf[ssf[ref].start:ssf[ref].end])
    old_nc={tuple(map(float,one(n,'at')[1:3])) for n in all_(r0,'no_connect')}
    new_nc={tuple(map(float,one(n,'at')[1:3])) for n in all_(rf,'no_connect')}
    positions=pin_positions(rf,'U3')
    added_expected={tuple(positions[str(p)]['xy']) for p in NC_PINS} if stage!='power' else set()
    check('Only26 verified NCs added at actual U3 pin coordinates',new_nc==old_nc|added_expected and len(all_(rf,'no_connect'))==8+len(added_expected))
    check('No NC on GPIO3, CHIP_PU or5V evidence-dependent terminals',all(tuple(positions[str(p)]['xy']) not in new_nc for p in (13,3,21)))
    for n in all_(r0,'no_connect'):check(f'Existing NC{id_(n)} byte preserved',s0[n.start:n.end] in sf)
    libs0={n[1]:n for n in all_(one(r0,'lib_symbols'),'symbol')};libsf={n[1]:n for n in all_(one(rf,'lib_symbols'),'symbol')}
    check('No embedded symbol added/removed',set(libs0)==set(libsf))
    for name,n in libs0.items():
        if stage=='final' and name=='Device:Battery':continue
        check(f'Cached{name}: exact original definition preserved',s0[n.start:n.end]==sf[libsf[name].start:libsf[name].end])
    if stage=='final':
        library=parse(LIB.read_text(),'kicad_symbol_lib');installed=next(n for n in all_(library,'symbol') if n[1]=='Battery')
        expected=list(installed);expected[1]='Device:Battery'
        check('Battery cache now matches installed definition structurally',list(libsf['Device:Battery'])==expected)
        old_wires={id_(n):s0[n.start:n.end] for n in all_(r0,'wire')};new_wires={id_(n):sf[n.start:n.end] for n in all_(rf,'wire')}
        check('Exactly18 redundant wire objects removed',set(old_wires)-set(new_wires)==set(SHORT_WIRES))
        for u,w in old_wires.items():
            if u in SHORT_WIRES or u==CS_WIRE:continue
            check(f'Unaffected wire{u}: exact bytes preserved',new_wires.get(u)==w)
        cs=next(n for n in all_(rf,'wire') if id_(n)==CS_WIRE)
        check('CS_ADC2 shortened only to connected label', [p[1:] for p in all_(one(cs,'pts'),'xy')]==[['562.61','96.52'],['568.96','96.52']])
        label0=next(n for n in all_(r0,'label') if id_(n)=='f775580c-f47c-4bc7-a9f8-15143a81985e')
        check('CS_ADC2 label original bytes preserved',s0[label0.start:label0.end] in sf)
        for u in AVDD_LABELS+DVDD_LABELS:
            n=next(n for n in all_(rf,'global_label') if id_(n)==u)
            o=next(n for n in all_(r0,'label') if id_(n)==u)
            check(f'{u}: supply alias link retained as global +3.3V at exact anchor',n[1]=='+3.3V' and one(n,'at')[1:3]==one(o,'at')[1:3])
            check(f'{u}: only intended label-presentation orientation change',one(n,'at')[3]==('0' if u=='75fc8b9d-1b77-49f1-bb82-13b6eff87138' else one(o,'at')[3]))
        grounds=[ref for ref,n in ss0.items() if one(n,'lib_id')[1]=='power:GND' and props(n)['Value']=='GND']
        check('Exactly43 GND values normalized without power model changes',len(grounds)==43 and all(props(ssf[ref])['Value']=='AGND' and id_(ssf[ref])==id_(ss0[ref]) and one(ssf[ref],'lib_id')==one(ss0[ref],'lib_id') for ref in grounds))
    initial_report,vi=reports(OUT/'initial-erc.json');current_report,vf=reports(OUT/f'{stage}-erc.json')
    check('Ignored checks and included severities unchanged',initial_report['ignored_checks']==current_report['ignored_checks'] and initial_report['included_severities']==current_report['included_severities'])
    expected_counts={'power':{'error':33,'warning':26},'unused':{'error':7,'warning':26},'final':{'error':7,'warning':4}}
    check('ERC counts match permitted resolved conditions',dict(Counter(v['severity'] for v in vf))==expected_counts[stage])
    def identity(v,ss):
        if v['type']=='power_pin_not_driven':
            match=re.match(r'Symbol (\S+) Pin ',v['items'][0]['description']);value=props(ss[match[1]])['Value']
            return (v['type'],v['severity'],'AGND' if value=='GND' else value)
        if v['type']=='pin_to_pin' and v['severity']=='warning':
            adc=next(i for i in v['items'] if re.match(r'Symbol U[12] Pin (17|18) ',i['description']))
            power=next(i for i in v['items'] if 'Power output' in i['description'])
            return (v['type'],v['severity'],adc['uuid'],'U5.5' if 'Symbol U5 Pin 5 ' in power['description'] else 'U4.5')
        if v['type']=='multiple_net_names':return (v['type'],v['severity'],v['description'])
        return (v['type'],v['severity'],v['description'],tuple(sorted(i['uuid'] for i in v['items'])))
    def remove(v):
        if v['type']=='pin_to_pin' and v['severity']=='error' and any('Symbol U4 Pin 5 ' in i['description'] for i in v['items']):return True
        if stage!='power' and v['type']=='pin_not_connected':
            m=re.match(r'Symbol U3 Pin (\d+) ',v['items'][0]['description'])
            if m and int(m[1]) in NC_PINS:return True
        return stage=='final' and v['type'] in ('unconnected_wire_endpoint','multiple_net_names','lib_symbol_mismatch')
    expected=[]
    for v in vi:
        if remove(v):continue
        key=identity(v,ss0)
        if v['type']=='pin_to_pin' and v['severity']=='warning':key=(*key[:-1],'U5.5')
        expected.append(key)
    check('Every remaining ERC condition preserved; only allowed removals and justified U5 representative change',Counter(expected)==Counter(identity(v,ssf) for v in vf))
    check('GPIO3 unresolved report retained',any(v['type']=='pin_not_connected' and any(i['uuid']=='810351da-8113-4a08-bf3b-96eeeeea5f0e' for i in v['items']) for v in vf))
    history=json.loads((OUT/'pre-edit-hashes.json').read_text())['hashes']
    for name,sha in history.items():
        if Path(name)==SCH:continue
        check(f'Pre-existing protected file unchanged:{name}',Path(name).is_file() and hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha)
    result={'stage':stage,'passed':all(c['passed'] for c in checks),'assertions':len(checks),'failed':[c['check'] for c in checks if not c['passed']],
        'erc':{'total':len(vf),'severities':dict(Counter(v['severity'] for v in vf)),'types':dict(Counter(v['type'] for v in vf))},'component_count':len(b),'net_count':len(nf),
        'intentional_pin_changes':changed,'remaining_erc':vf,'checks':checks,
        'limits':'Static connectivity,source andrule checks only. No operating supply, firmware, analog performance, physical orwearer-safety qualification.'}
    (OUT/f'{stage}-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/f'{stage}-connectivity.json').write_text(json.dumps({'components':b,'nets':{n:sorted(m) for n,m in nf.items()}},indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','remaining_erc')},indent=2))
    assert result['passed'],result['failed']


if __name__=='__main__':main(sys.argv[1])
