"""Generate the minimal common-3V3 ADC interface; never edits the active design.

build(root_uuid, project_name, net_aliases=None) returns embedded symbol definitions,
KiCad objects, exact pin/net mapping and integration notes. Sources are pin-level
manufacturer datasheets, not inferred generic pin ordering.
"""
from pathlib import Path
import argparse
import json
import uuid
HERE=Path(__file__).resolve().parent
NS=uuid.UUID('f7190e3f-ddb3-48a7-9ed1-4615266f4704')
def uid(key): return str(uuid.uuid5(NS, key))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def num(n): return f'{float(n):.5f}'.rstrip('0').rstrip('.')
def effects(size=1.0, extra=''): return f'(effects (font (size {size} {size})) {extra})'

def pin(n, name, kind='input', side='L'):
    return {'number':str(n), 'name':name, 'type':kind, 'side':side}

SPECS={
 'FWD': {'name':'SN74LVC244APWR','footprint':'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
  'url':'https://www.ti.com/lit/ds/symlink/sn74lvc244a.pdf',
  'pins':[pin(1,'~1OE'),pin(2,'1A1'),pin(4,'1A2'),pin(6,'1A3'),pin(8,'1A4'),pin(11,'2A1'),pin(13,'2A2'),pin(15,'2A3'),pin(17,'2A4'),pin(19,'~2OE'),pin(10,'GND','power_in'),pin(20,'VCC','power_in','R'),pin(18,'1Y1','tri_state','R'),pin(16,'1Y2','tri_state','R'),pin(14,'1Y3','tri_state','R'),pin(12,'1Y4','tri_state','R'),pin(9,'2Y1','tri_state','R'),pin(7,'2Y2','tri_state','R'),pin(5,'2Y3','tri_state','R'),pin(3,'2Y4','tri_state','R')]},
 'RET': {'name':'74LVC2G125DP','footprint':'Package_SO:TSSOP-8_3x3mm_P0.65mm',
  'url':'https://assets.nexperia.com/documents/data-sheet/74LVC2G125.pdf',
  'pins':[pin(1,'~1OE'),pin(2,'1A'),pin(7,'~2OE'),pin(5,'2A'),pin(4,'GND','power_in'),pin(8,'VCC','power_in','R'),pin(6,'1Y','tri_state','R'),pin(3,'2Y','tri_state','R')]},
 'R': {'name':'R_Verified','footprint':'Resistor_SMD:R_0603_1608Metric','url':'',
  'pins':[pin(1,'1','passive'),pin(2,'2','passive','R')]},
 'C': {'name':'C_Verified','footprint':'Capacitor_SMD:C_0603_1608Metric','url':'',
  'pins':[pin(1,'1','passive'),pin(2,'2','passive','R')]},
}
def geometry(spec):
    passive = spec['name'].endswith('_Verified')
    width = 2.54 if passive else 20.32
    sides = {s:[p for p in spec['pins'] if p['side']==s] for s in ('L','R')}
    count=max(map(len,sides.values()))
    height=2.54 if passive else max(7.62, (count+1)*2.54/2)
    points={}
    for side, ps in sides.items():
        for i,p in enumerate(ps):
            y=(len(ps)-1)*2.54/2-i*2.54
            points[p['number']]=((-width-5.08 if side=='L' else width+5.08), y)
    return width,height,points

def lib_symbol(key):
    spec=SPECS[key]; name='V13_SimpleActive:'+spec['name']; w,h,points=geometry(spec)
    fields=[f'(property "Reference" "{key if key in ("R","C") else "U"}" (at 0 {num(h+3.81)} 0) {effects()})',
            f'(property "Value" {q(spec["name"])} (at 0 {num(h+1.27)} 0) {effects()})']
    drawings=[]
    if key=='C':
        for x in (-0.635,0.635):
            drawings.append(f'(polyline (pts (xy {x} -1.905) (xy {x} 1.905)) (stroke (width 0.254) (type default)) (fill (type none)))')
    else:
        drawings.append(f'(rectangle (start {-w} {h}) (end {w} {-h}) (stroke (width 0.254) (type default)) (fill (type background)))')
    pins=[]
    for p in spec['pins']:
        x,y=points[p['number']]; a=0 if p['side']=='L' else 180
        length=5.08 if key not in ('R','C') else 6.985 if key=='C' else 5.08
        pins.append(f'(pin {p["type"]} line (at {num(x)} {num(y)} {a}) (length {num(length)}) (name {q(p["name"])} {effects()}) (number {q(p["number"])} {effects()}))')
    return f'(symbol {q(name)} (pin_names (offset 0.762)) (in_bom yes) (on_board yes) {" ".join(fields)} (symbol {q(spec["name"]+"_0_1")} {" ".join(drawings)}) (symbol {q(spec["name"]+"_1_1")} {" ".join(pins)}))'

def build(root_uuid,project_name='open-semg-16-v1.3',net_aliases=None):
    aliases={'ADC_MOSI':'MOSI','ADC_SCLK':'SCLK','ADC_START':'START','ADC_RESET':'RESET','ADC_PWDN':'PWDN',
      'ADC_CS1':'CS_ADC1','ADC_CS2':'CS_ADC2','ADC_DOUT1':'DOUT_ADC1','ADC_DOUT2':'DOUT_ADC2'}
    aliases.update(net_aliases or {})
    def net(n):return aliases.get(n,n)
    d={'libdefs':[lib_symbol(k) for k in SPECS], 'objects':[], 'pinmap':{},'components':{},'external_connections':{}}
    def add(key,ref,x,y,mapping,value=None,properties=None):
        x=round(x/1.27)*1.27;y=round(y/1.27)*1.27
        sp=SPECS[key];w,h,pts=geometry(sp);value=value or sp['name']
        props={'Reference':ref,'Value':value,'Footprint':sp['footprint'],'Datasheet':sp['url'],
          'MPN':sp['name'] if key not in ('R','C') else 'TBD',
          'Manufacturer':'Texas Instruments' if key=='FWD' else 'Nexperia' if key=='RET' else 'TBD',
          'Purpose':'Minimal V1.3 common-rail ADC interface; bench verification required'}
        props.update(properties or {})
        fields=[]
        for k,v in props.items():
            hide='' if k in ('Reference','Value') else '(hide yes)'
            yy=y-h-5.08+(2.54 if k=='Value' else 0)
            fields.append(f'(property {q(k)} {q(v)} (at {num(x)} {num(yy)} 0) {hide} {effects(1.0)})')
        pins=' '.join(f'(pin {q(p["number"])} (uuid {q(uid(ref+":"+p["number"]))}))' for p in sp['pins'])
        d['objects'].append(f'(symbol (lib_id {q("V13_SimpleActive:"+sp["name"])}) (at {num(x)} {num(y)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid(ref))}) {" ".join(fields)} {pins} (instances (project {q(project_name)} (path {q("/"+root_uuid)} (reference {q(ref)}) (unit 1)))))')
        d['pinmap'][ref]={};d['components'][ref]={'value':value,'footprint':sp['footprint'],'datasheet':sp['url'],'pins':{}}
        for p in sp['pins']:
            pn=p['number'];n=mapping.get(pn);dx,dy=pts[pn];px,py=x+dx,y-dy
            d['pinmap'][ref][pn]=net(n) if n is not None else None
            d['components'][ref]['pins'][pn]={'name':p['name'],'net':net(n) if n is not None else None,'xy':[round(px,5),round(py,5)]}
            ident=ref+':'+pn
            if n is None:
                d['objects'].append(f'(no_connect (at {num(px)} {num(py)}) (uuid {q(uid(ident+":nc"))}))');continue
            end=px-7.62 if p['side']=='L' else px+7.62
            d['objects'].append(f'(wire (pts (xy {num(px)} {num(py)}) (xy {num(end)} {num(py)})) (stroke (width 0) (type default)) (uuid {q(uid(ident+":wire"))}))')
            angle=0 if p['side']=='L' else 180
            d['objects'].append(f'(label {q(net(n))} (at {num(end)} {num(py)} {angle}) {effects(0.9,"(justify left bottom)")} (uuid {q(uid(ident+":label"))}))')
    M='MAIN_3V3';G='AGND'
    fwd={'1':G,'19':G,'10':G,'20':M,'17':G,'3':None}
    chans=[('MCU_MOSI','ADC_MOSI',2,18),('MCU_SCLK','ADC_SCLK',4,16),('MCU_START','ADC_START',6,14),('MCU_RESET','ADC_RESET',8,12),('MCU_PWDN','ADC_PWDN',11,9),('MCU_CS1','ADC_CS1',13,7),('MCU_CS2','ADC_CS2',15,5)]
    for src,dst,ip,op in chans:fwd[str(ip)]=src;fwd[str(op)]=dst
    add('FWD','U7',620,100,fwd,properties={'Purpose':'Seven forward controls; OEs grounded; input pulldowns on MCU side; unused input low/output NC'})
    add('RET','U8',820,100,{'1':G,'2':'MISO_RAW','3':'DRDY_DRV','4':G,'5':'DRDY_ADC1','6':'MISO_DRV','7':G,'8':M},properties={'Purpose':'Shared-MISO and DRDY regeneration; all domains on MAIN; both OEs grounded; exact Nexperia output pin map'})
    rs=[('R70','10k','MCU_CS1',G,'Defined CS1 input LOW through MCU boot'),('R71','10k','MCU_CS2',G,'Defined CS2 input LOW through MCU boot'),
      ('R72','3.6k','ADC_DOUT1','MISO_RAW','Limit possible startup DOUT contention; retain logical shared bus'),('R73','3.6k','ADC_DOUT2','MISO_RAW','Limit possible startup DOUT contention; retain logical shared bus'),
      ('R74','1k','MISO_DRV','MISO','Limit return-buffer versus MCU LOW glitch current; actual waveform/current qualification required'),('R75','1k','DRDY_DRV','MCU_DRDY','Limit return-buffer versus MCU LOW glitch current; actual waveform/current qualification required'),
      ('R76','100k','MISO_RAW',G,'Defined MISO_RAW when both ADCs deselected'),('R77','100k','DRDY_ADC1',G,'Defined raw DRDY during startup')]
    for i,(ref,value,n1,n2,purpose) in enumerate(rs):
        add('R',ref,610+(i%3)*145,220+(i//3)*35,{'1':n1,'2':n2},value,{'Tolerance':'1%','Power rating':'>=0.1W','Purpose':purpose})
    for i,ref in enumerate(('C60','C61')):
        add('C',ref,610+i*145,330,{'1':M,'2':G},'100nF',{'Voltage rating':'>=10V','Dielectric':'X7R or qualified C0G','Purpose':('U7' if i==0 else 'U8')+' local bypass; effective capacitance and placement required'})
    ext={'U3.17':'MCU_MOSI','U3.18':'MCU_SCLK','U3.12':'MCU_START','U3.6':'MCU_RESET','U3.7':'MCU_PWDN','U3.16':'MCU_CS1','U3.20':'MCU_CS2','U3.19':'MISO','U3.15':'MCU_DRDY',
      'U1.34':'ADC_MOSI','U2.34':'ADC_MOSI','U1.40':'ADC_SCLK','U2.40':'ADC_SCLK','U1.38':'ADC_START','U2.38':'ADC_START','U1.36':'ADC_RESET','U2.36':'ADC_RESET','U1.35':'ADC_PWDN','U2.35':'ADC_PWDN','U1.39':'ADC_CS1','U2.39':'ADC_CS2','U1.43':'ADC_DOUT1','U2.43':'ADC_DOUT2','U1.47':'DRDY_ADC1','TP2.1':'DRDY_ADC1',
      'R33.1':'MCU_START','R34.1':'MCU_RESET','R35.1':'MCU_PWDN','R36.1':'MCU_MOSI','R37.1':'MCU_SCLK'}
    d['external_connections']={p:net(n) for p,n in ext.items()}
    d['notes']=[
      'Only U7/U8,R70-R77,C60-C61 are added by this generator. Root moves existing R33-R37 to indicated MCU-side nets, unchanged 10k.',
      'All MCU, ADC DVDD and buffers share MAIN. ADC AVDD/AVDD1 and analog auxiliaries follow the separately routed 2.2ohm filter branch; U1 CLKSEL follows DVDD/MAIN.',
      'No ADC power switch, READY GPIO, return mux, gating IC or added supervisor is present.',
      'Normal separate-CS/shared-MISO cascade is preserved. Two series DOUT resistors bound initial both-CS-low current; normal transactions still require exclusive selection.',
      'Do not cite ADS10mA input-current limit as a DOUT output rating. At MAINmax3.35V and R72/R73 minima3.564k each, opposing-driver current<=0.470mA, within500uA characterized output-load condition.',
      'R74/R75 limit a return-buffer HIGH versus MCU LOW to about3.4mA at3.35V/990ohm. This is a current bound, not an invented ESP guaranteed output rating; scope warm-reset waveforms.',
      'All seven MCU outputs LOW through startup; MCU-side pulls work against 244 input leakage, not ADS input leakage. Forbid GPIO hold/contradictory pullups. Initialize clock/reference/reset after measured rail settling.',
      'Initial bench SPI1MHz;2MHz and4kSPS require actual capacitance/edge/throughput validation. No wearer or analog-performance release follows.'
    ]
    d['references']=sorted(d['components']);d['lib_symbols']=d['libdefs'];d['pin_map']=d['pinmap']
    return d

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root-uuid',required=True);ap.add_argument('--project-name',default='open-semg-16-v1.3');ap.add_argument('--output',type=Path,default=HERE/'interface-blocks.json');a=ap.parse_args();d=build(a.root_uuid,a.project_name)
    a.output.write_text(json.dumps(d,indent=2)+'\n');a.output.with_suffix('.lib.sexpr').write_text('\n'.join(d['libdefs'])+'\n');a.output.with_suffix('.objects.sexpr').write_text('\n'.join(d['objects'])+'\n')
    print(json.dumps({'output':str(a.output),'components':len(d['components']),'references':d['references']}))
