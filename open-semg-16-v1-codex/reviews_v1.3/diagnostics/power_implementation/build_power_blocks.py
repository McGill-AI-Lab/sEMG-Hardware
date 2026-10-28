"""Generate proposed V1.3 power blocks; never writes the active schematic.

build(root_uuid) returns qualified embedded library definitions and schematic
objects. The executable only writes JSON and a review-directory preview.
TPS63802 pin identities follow TI SLVSEU9D p.4. Its unusual DLA0010A HotRod
footprint is deliberately unassigned pending an exact local footprint review.
"""
from pathlib import Path
import json
import math
import re
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
LIB = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NS = uuid.UUID('6257d51c-419a-47be-adcc-c104a4860d73')

class Node(list): pass

def parse(text):
    stack=[]; roots=[]
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        t=m.group()
        if t=='(':
            n=Node(); n.start=m.start(); stack.append(n)
        elif t==')':
            n=stack.pop(); n.end=m.end()
            (stack[-1] if stack else roots).append(n)
        else: stack[-1].append(json.loads(t) if t.startswith('"') else t)
    assert not stack and len(roots)==1
    return roots[0]

def all_(n,k): return [c for c in n if isinstance(c,list) and c and c[0]==k]
def one(n,k): return next(iter(all_(n,k)),None)
def q(v): return json.dumps(str(v),ensure_ascii=False)
def u(v): return str(uuid.uuid5(NS,v))
def num(v): return f'{float(v):.5f}'.rstrip('0').rstrip('.') if float(v) else '0'

def installed(lib_id):
    lib,name=lib_id.split(':',1); src=(LIB/(lib+'.kicad_sym')).read_text()
    n=next(n for n in all_(parse(src),'symbol') if n[1]==name)
    text=src[n.start:n.end]
    return text.replace('(symbol '+q(name), '(symbol '+q(lib_id),1)

def pins(definition):
    p={}
    for group in all_(parse(definition),'symbol'):
        for pin in all_(group,'pin'):
            a=one(pin,'at'); p[one(pin,'number')[1]]=(float(a[1]),float(a[2]),float(a[3]),pin[1])
    return p

def custom_tps():
    name='TPS63802DLAR'
    # All ten physical terminals are represented. DLA has no separate pin11 EP.
    spec=[('10','VIN','power_in',-12.7,7.62,0),
          ('1','EN','input',-12.7,2.54,0),
          ('2','MODE','input',-12.7,-2.54,0),
          ('3','AGND','power_in',-2.54,-12.7,90),
          ('8','GND','power_in',2.54,-12.7,90),
          ('4','FB','input',12.7,-2.54,180),
          ('5','PG','open_collector',12.7,-7.62,180),
          ('6','VOUT','power_out',12.7,7.62,180),
          ('9','L1','passive',-5.08,12.7,270),
          ('7','L2','passive',5.08,12.7,270)]
    pp=[]
    for no,pn,pt,x,y,a in spec:
        pp.append(f'(pin {pt} line (at {num(x)} {num(y)} {a}) (length 2.54) '
                  f'(name {q(pn)} (effects (font (size 1.0 1.0)))) '
                  f'(number {q(no)} (effects (font (size 1.0 1.0)))))')
    return f'''(symbol "V13_Power:{name}"
      (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at -7.62 15.24 0) (effects (font (size 1.27 1.27))))
      (property "Value" "{name}" (at 0 -16.51 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tps63802.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "2A buck-boost; 10-pin TI DLA0010A HotRod; verified pin map SLVSEU9D p4" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "{name}_0_1" (rectangle (start -10.16 10.16) (end 10.16 -10.16) (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "{name}_1_1" {' '.join(pp)})
      (embedded_fonts no))'''


def build(root_uuid, project_name='open-semg-16-v1.3'):
    defs={i:installed(i) for i in ['Device:R','Device:C','Device:L','Regulator_Linear:LT3042xMSE']}
    defs['V13_Power:TPS63802DLAR']=custom_tps()
    items=[]; bom=[]; pin_nets={}; physical={}; ids=set()
    def emit(kind,key,s):
        assert key not in ids, key
        ids.add(key); items.append(s)
    def wire(a,b,key):
        emit('wire',key,f'(wire (pts (xy {num(a[0])} {num(a[1])}) (xy {num(b[0])} {num(b[1])})) (stroke (width 0) (type default)) (uuid {q(u(key))}))')
    def label(x,y,net,key,angle=0):
        emit('label',key,f'(label {q(net)} (at {num(x)} {num(y)} {angle}) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid {q(u(key))}))')
    def text(x,y,value,key):
        emit('text',key,f'(text {q(value)} (at {num(x)} {num(y)} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid {q(u(key))}))')
    def component(ref,lib_id,value,x,y,connections,footprint='',mpn='',fields=None,angle=0):
        x=round(x/1.27)*1.27; y=round(y/1.27)*1.27  # exact 50-mil connection grid
        definition=defs[lib_id]; pp=pins(definition); ip=[]; sf=[]
        th=math.radians(angle)
        for no,(px,py,pa,pt) in pp.items():
            wx=round(x+px*math.cos(th)-py*math.sin(th),5)
            wy=round(y-py*math.cos(th)-px*math.sin(th),5)
            physical[(ref,no)]=(wx,wy)
            ip.append(f'(pin {q(no)} (uuid {q(u(ref+".pin."+no))}))')
        visible=[('Reference',ref,x+3.81,y-4.8),('Value',value,x+3.81,y-2.0)] if ref[0] in 'RCL' else [('Reference',ref,x-6,y-18),('Value',value,x-6,y-15)]
        for pn,pv,ax,ay in visible:
            sf.append(f'(property {q(pn)} {q(pv)} (at {num(ax)} {num(ay)} 0) (effects (font (size 1.0 1.0)) (justify left)))')
        extra={'Footprint':footprint,'Datasheet':next((p[2] for p in all_(parse(definition),'property') if p[1]=='Datasheet'),''),'MPN':mpn}
        extra.update(fields or {})
        for pn,pv in extra.items():
            sf.append(f'(property {q(pn)} {q(pv)} (at {num(x)} {num(y)} 0) (effects (font (size 1.0 1.0)) (hide yes)))')
        emit('symbol',ref,f'''(symbol (lib_id {q(lib_id)}) (at {num(x)} {num(y)} {angle}) (unit 1)
        (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(u(ref))})
        {' '.join(sf)} {' '.join(ip)}
        (instances (project {q(project_name)} (path {q('/'+root_uuid)} (reference {q(ref)}) (unit 1)))))''')
        connected_coordinates=set()
        for no,net in connections.items():
            assert no in pp, (ref,no)
            pin_nets[f'{ref}.{no}']=net
            a=physical[(ref,no)]
            if a in connected_coordinates: continue  # stacked physical terminals
            connected_coordinates.add(a)
            if net is None:
                emit('no_connect',f'{ref}.nc.{no}',f'(no_connect (at {num(a[0])} {num(a[1])}) (uuid {q(u(ref+".nc."+no))}))')
                continue
            pa=pp[no][2]; direction=math.radians(pa-angle)
            # Extend outward from the pin end, opposite the pin's inward direction.
            b=(round(a[0]-2.54*math.cos(direction),5),round(a[1]+2.54*math.sin(direction),5))
            wire(a,b,f'{ref}.stub.{no}'); label(*b,net,f'{ref}.net.{no}')
        assert set(connections)==set(pp), (ref,set(pp)-set(connections))
        bom.append({'ref':ref,'value':value,'lib_id':lib_id,'mpn':mpn,'footprint':footprint,'fields':fields or {}})
    def resistor(ref,value,x,y,a,b,mpncode,prec=True):
        component(ref,'Device:R',value,x,y,{'1':a,'2':b},'Resistor_SMD:R_0603_1608Metric',
                  'TNPW0603'+mpncode+('BYTA' if prec else 'FETA'),
                  {'Tolerance':'0.1%' if prec else '1%','TCR':'10 ppm/K' if prec else '25 ppm/K',
                   'Qualification':'Vishay TNPW ordering-code candidate; procurement availability to verify'})
    def capacitor(ref,value,x,y,a,b,mpn,requirement):
        component(ref,'Device:C',value,x,y,{'1':a,'2':b},'Capacitor_SMD:C_0805_2012Metric',mpn,
                  {'Manufacturer':'Murata','Qualification':requirement})
    tpsfields={'Manufacturer':'Texas Instruments','Footprint_Requirement':'TI DLA0010A HotRod 4223750/D. No generic 10+EP substitute; exact local footprint required before PCB',
               'Operating_Requirement':'Bench input 3.0-4.2V; protected pack and cell-specific cutoff/inrush qualification before battery use'}
    component('U6','V13_Power:TPS63802DLAR','TPS63802DLAR MAIN 3.3V',120,450,
              {'10':'SW_BAT_PROT','1':'MAIN_ENABLE','2':'SW_BAT_PROT','3':'AGND','8':'AGND',
               '4':'MAIN_FB','5':'MAIN_PG','6':'MAIN_3V3','9':'MAIN_SW1','7':'MAIN_SW2'},mpn='TPS63802DLAR',fields=tpsfields)
    component('U7','V13_Power:TPS63802DLAR','TPS63802DLAR AFE PRE 4.0V',300,450,
              {'10':'SW_BAT_PROT','1':'MAIN_PG','2':'SW_BAT_PROT','3':'AGND','8':'AGND',
               '4':'AFE_PRE_FB','5':None,'6':'AFE_PRE_4V0','9':'AFE_PRE_SW1','7':'AFE_PRE_SW2'},mpn='TPS63802DLAR',fields=tpsfields)
    for ref,x,prefix in [('L1',120,'MAIN'),('L2',300,'AFE_PRE')]:
        component(ref,'Device:L','0.47uH XFL4015',x,412,{'1':prefix+'_SW1','2':prefix+'_SW2'},
                  mpn='XFL4015-471MEC',fields={'Manufacturer':'Coilcraft','Footprint_Requirement':'Exact XFL4015 4x4mm manufacturer recommended land pattern required before PCB',
                  'Qualification':'TI TPS63802 reference candidate. At25C: Isat5.4A at20% L drop,6.6A at30%; verify all tolerance/current/temp corners and application eligibility'},angle=90)
    capacitor('C58','10u 16V',60,440,'SW_BAT_PROT','AGND','GRM21BR61C106KE15L','MAIN CIN: >=4uF effective at4.2V including tolerance/bias/temp; candidate data curve needed')
    capacitor('C59','22u 16V',180,440,'MAIN_3V3','AGND','GRM21BR61C226ME44L','MAIN COUT: >=7uF effective at3.3V; verify ESR/bias/temp; existing C57 additional')
    capacitor('C60','10u 16V',240,440,'SW_BAT_PROT','AGND','GRM21BR61C106KE15L','PRE CIN: >=4uF effective at4.2V including tolerance/bias/temp; candidate data curve needed')
    capacitor('C61','22u 16V',360,440,'AFE_PRE_4V0','AGND','GRM21BR61C226ME44L','PRE COUT part1 of2x22uF nominal per TI VOUT>3.6V recommendation; >=7uF combined effective')
    capacitor('C62','22u 16V',410,440,'AFE_PRE_4V0','AGND','GRM21BR61C226ME44L','PRE COUT part2 of2x22uF nominal; effective C/ESR/bias/temp to verify')
    resistor('R39','56.0k 0.1%',55,495,'MAIN_3V3','MAIN_FB','56K0')
    resistor('R40','10.0k 0.1%',95,495,'MAIN_FB','AGND','10K0')
    resistor('R41','22.0k 0.1%',140,495,'SW_BAT_PROT','MAIN_ENABLE','22K0')
    resistor('R42','10.0k 0.1%',185,495,'MAIN_ENABLE','AGND','10K0')
    resistor('R43','10.0k 0.1%',225,495,'MAIN_3V3','MAIN_PG','10K0')
    resistor('R44','69.8k 0.1%',275,495,'AFE_PRE_4V0','PRE_FB_TOP','69K8')
    resistor('R45','200R 0.1%',320,495,'PRE_FB_TOP','AFE_PRE_FB','200R')
    resistor('R46','10.0k 0.1%',365,495,'AFE_PRE_FB','AGND','10K0')
    resistor('R50','100k 0.1%',410,495,'MAIN_PG','AGND','100K')
    component('U8','Regulator_Linear:LT3042xMSE','LT3042IMSE AFE 2.98V',300,590,
              {'1':'AFE_PRE_4V0','2':'AFE_PRE_4V0','3':'MAIN_PG','4':None,'5':'AFE_ILIM',
               '6':'AFE_PRE_4V0','7':'AFE_SET','8':'AGND','9':'AFE_2V98','10':'AFE_2V98','11':'AGND'},
              'Package_SO:MSOP-10-1EP_3x3mm_P0.5mm_EP1.68x1.88mm','LT3042IMSE#PBF',
              {'Manufacturer':'Analog Devices','Qualification':'IN/OUT local >=4.7uF effective; output ESR<50mOhm ESL<2nH. PGFB=IN disables fast start. SET leakage/precision/layout qualification required'})
    capacitor('C63','10u 16V',240,580,'AFE_PRE_4V0','AGND','GRM21BR61C106KE15L','LT3042 CIN local >=4.7uF effective at4.06V; verify bias/tolerance/temp')
    capacitor('C64','10u 16V',365,580,'AFE_2V98','AGND','GRM21BR61C106KE15L','LT3042 COUT local >=4.7uF effective at3.05V; ESR<50mOhm ESL<2nH plus existing40.4uF ADC banks')
    capacitor('C65','4.7u 10V X7R',190,615,'AFE_SET','AGND','GRM21BR71A475KA73L','SET capacitor: low leakage and microphonics; nominal4.7uF, slow start with PGFB=IN')
    resistor('R47','29.8k 0.1%',240,615,'AFE_SET','AGND','29K8')
    resistor('R48','2.49k 0.1%',300,615,'AFE_ILIM','AGND','2K49')
    resistor('R49','2.70k 0.1%',365,615,'AFE_2V98','AGND','2K70')
    text(50,390,'V1.3 POWER: protected 1S pack / bench3.0-4.2V. NO USB while seated. Unplug pack for OFF/service.','note.heading')
    text(50,525,'U6:3.3V main; U7:independent4.0V pre; U8:quiet2.98V AVDD+DVDD. Outputs never paralleled.','note.tree')
    text(50,535,'22k/10k MAIN EN cutoff is provisional: about3.10-3.31V falling at switched/protected input; pack qualification required.','note.cutoff')
    text(50,545,'MAIN_PG sequences preconverter and LDO; separate supervisors/READY gate must isolate every MCU/ADC path on rail/reset fault.','note.sequence')
    text(50,555,'PCB/BOM release gate: exact TPS DLA0010A+inductor footprints, MLCC effective-C/ESR/leakage, inrush/UVLO/rebound/noise/thermal tests.','note.gates')
    result={'lib_definitions':defs,'items':'\n'.join(items),'bom':bom,'pin_nets':pin_nets,
            'ports':{'input':'SW_BAT_PROT','main':'MAIN_3V3','pre':'AFE_PRE_4V0','afe':'AFE_2V98','enable':'MAIN_ENABLE','main_good':'MAIN_PG','ground':'AGND'},
            'references':[b['ref'] for b in bom],
            'facts':{'main_nominal_V':3.3,'pre_nominal_V':4.0,'afe_nominal_V':2.98,'main_DC_with_0p2pct_resistors_V':[3.2503229317365268,3.3499458693386774],
                     'pre_DC_with_0p2pct_resistors_V':[3.9391536646706586,4.061182336673346],'afe_DC_with_0p2pct_RSET_V':[2.9125592,3.0476792]}}
    return result


def preview(blocks, baseline):
    source=baseline.read_text(); root=parse(source)
    libs=one(root,'lib_symbols'); existing={n[1] for n in all_(libs,'symbol')}
    addition='\n'.join(v for k,v in blocks['lib_definitions'].items() if k not in existing)
    modified=source[:libs.end-1]+addition+source[libs.end-1:]
    modified=modified.replace('(paper "A2")','(paper "A0")',1)
    modified=modified.rstrip()[:-1]+'\n'+blocks['items']+'\n)\n'
    return modified

if __name__=='__main__':
    baseline=HERE/'baseline/open-semg-16-v1.3.kicad_sch'
    root_uuid=one(parse(baseline.read_text()),'uuid')[1]
    b=build(root_uuid)
    (HERE/'power-blocks.sexpr.json').write_text(json.dumps(b,indent=2)+'\n')
    target=HERE/'power-blocks-preview.kicad_sch'
    target.write_text(preview(b,baseline))
    out=HERE/'power-blocks-preview-netlist.xml'
    r=subprocess.run([CLI,'sch','export','netlist','--format','kicadxml','--output',str(out),str(target)],text=True,capture_output=True)
    (HERE/'power-blocks-build-log.json').write_text(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
    print(json.dumps({'components':len(b['bom']),'root_uuid':root_uuid,'returncode':r.returncode,'netlist':str(out)},indent=2))
    if r.returncode: raise SystemExit(r.returncode)
