"""Create reviewable KiCad fragments for V1.3; never edits a design file.

API: build(root_uuid, project_name, net_aliases=None) returns JSON-safe fragments.
All new symbols are local embedded definitions with manufacturer pin numbering.
Standalone output is written beside this script, never to v1.3/.
"""
from pathlib import Path
import argparse
import json
import uuid

HERE = Path(__file__).resolve().parent
NS = uuid.UUID('c95372c4-b8df-452b-bcf5-34839667f1d7')

def uid(key): return str(uuid.uuid5(NS, key))
def q(s): return json.dumps(str(s), ensure_ascii=False)
def num(n): return f'{float(n):.5f}'.rstrip('0').rstrip('.')
def effects(size=1.0, extra=''): return f'(effects (font (size {size} {size})) {extra})'

def pin(n, name, kind='input', side='L'):
    return {'number':str(n), 'name':name, 'type':kind, 'side':side}

# Each numbering list is verified against the exact package datasheet.
SPECS = {
 'AXC': {'name':'SN74AXC8T245PWR', 'footprint':'Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm',
  'url':'https://www.ti.com/lit/ds/symlink/sn74axc8t245.pdf',
  'pins': [pin(1,'VCCA','power_in'), pin(2,'DIR1')]+[pin(i+3,f'A{i+1}','bidirectional') for i in range(8)]+[pin(11,'DIR2'),pin(12,'GND','power_in')]+[pin(24,'VCCB','power_in','R'),pin(23,'VCCB','power_in','R'),pin(22,'~OE','input','R')]+[pin(21-i,f'B{i+1}','bidirectional','R') for i in range(8)]+[pin(13,'GND','power_in','R')]},
 'BUF': {'name':'74LVC1G125GW', 'footprint':'Package_TO_SOT_SMD:SOT-353_SC-70-5',
  'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G125.pdf',
  'pins':[pin(1,'~OE'),pin(2,'A'),pin(3,'GND','power_in'),pin(4,'Y','tri_state','R'),pin(5,'VCC','power_in','R')]},
 'MUX': {'name':'74LVC1G157GW', 'footprint':'Package_TO_SOT_SMD:SOT-363_SC-70-6',
  'url':'https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf',
  'pins':[pin(1,'I1'),pin(3,'I0'),pin(6,'S'),pin(2,'GND','power_in'),pin(4,'Y','output','R'),pin(5,'VCC','power_in','R')]},
 'NAND': {'name':'SN74LVC1G132DCKR', 'footprint':'Package_TO_SOT_SMD:SOT-353_SC-70-5',
  'url':'https://www.ti.com/lit/ds/symlink/sn74lvc1g132.pdf',
  'pins':[pin(1,'A'),pin(2,'B'),pin(3,'GND','power_in'),pin(4,'Y','output','R'),pin(5,'VCC','power_in','R')]},
 'NAND4': {'name':'SN74HCS20PWR','footprint':'Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
  'url':'https://www.ti.com/lit/ds/symlink/sn74hcs20.pdf',
  'pins':[pin(1,'1A'),pin(2,'1B'),pin(4,'1C'),pin(5,'1D'),pin(14,'VCC','power_in'),pin(7,'GND','power_in'),pin(6,'1Y','output','R'),pin(8,'2Y','output','R'),pin(9,'2A','input','R'),pin(10,'2B','input','R'),pin(12,'2C','input','R'),pin(13,'2D','input','R'),pin(3,'NC','passive','R'),pin(11,'NC','passive','R')]},
 'NMOS': {'name':'AO3400A','footprint':'Package_TO_SOT_SMD:SOT-23',
  'url':'https://www.aosmd.com/res/data_sheets/AO3400A.pdf',
  'pins':[pin(1,'G'),pin(2,'S','passive'),pin(3,'D','passive','R')]},
 'OR': {'name':'74LVC2G32DP', 'footprint':'Package_SO:TSSOP-8_3x3mm_P0.65mm',
  'url':'https://assets.nexperia.com/documents/data-sheet/74LVC2G32.pdf',
  'pins':[pin(1,'1A'),pin(2,'1B'),pin(5,'2A'),pin(6,'2B'),pin(4,'GND','power_in'),pin(7,'1Y','output','R'),pin(3,'2Y','output','R'),pin(8,'VCC','power_in','R')]},
 'CLAMP': {'name':'SN74LVC541APWR','footprint':'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
  'url':'https://www.ti.com/lit/ds/symlink/sn74lvc541a.pdf',
  'pins':[pin(1,'~OE1')]+[pin(i+2,'A'+str(i+1)) for i in range(8)]+[pin(10,'GND','power_in')]+[pin(11+i,'Y'+str(8-i),'tri_state','R') for i in range(8)]+[pin(19,'~OE2','input','R'),pin(20,'VCC','power_in','R')]},
 'MON': {'name':'TPS3808G01DBVR', 'footprint':'Package_TO_SOT_SMD:SOT-23-6',
  'url':'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
  'pins':[pin(3,'~MR'),pin(5,'SENSE'),pin(2,'GND','power_in'),pin(6,'VDD','power_in','R'),pin(1,'~RESET','open_collector','R'),pin(4,'CT','input','R')]},
 'R': {'name':'R_Verified', 'footprint':'Resistor_SMD:R_0603_1608Metric', 'url':'',
  'pins':[pin(1,'1','passive'),pin(2,'2','passive','R')]},
 'C': {'name':'C_Verified', 'footprint':'Capacitor_SMD:C_0603_1608Metric', 'url':'',
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
    spec=SPECS[key]; name='Power_Impl:'+spec['name']; w,h,points=geometry(spec)
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

def build(root_uuid, project_name='open-semg-16-v1.3', net_aliases=None):
    aliases={'MAIN_GOOD':'POWER_GOOD','AFE_GOOD':'POWER_GOOD','CHIP_PU':'CHIP_PU',
      'ADC_MOSI':'MOSI','ADC_SCLK':'SCLK','ADC_START':'START','ADC_RESET':'RESET','ADC_PWDN':'PWDN',
      'ADC_CS_ADC1':'CS_ADC1','ADC_CS_ADC2':'CS_ADC2','MCU_CS_ADC1':'MCU_CS1','MCU_CS_ADC2':'MCU_CS2',
      'ADC_DOUT1':'DOUT_ADC1','ADC_DOUT2':'DOUT_ADC2','MCU_MISO':'MISO',
      'ADC_DRDY1':'DRDY_ADC1','MCU_DRDY1':'MCU_DRDY'}
    aliases.update(net_aliases or {})
    def net(n): return aliases.get(n,n)
    result={'lib_symbols':[lib_symbol(k) for k in SPECS], 'objects':[], 'pin_map':{}, 'components':{}, 'external_connections':{}, 'notes':[]}
    def label(n,x,y,key,side='L'):
        # Short labelled stubs connect directly to verified terminals. Local
        # labels deliberately have sheet scope; V1.3 is one root sheet.
        end=x-7.62 if side=='L' else x+7.62
        result['objects'].append(f'(wire (pts (xy {num(x)} {num(y)}) (xy {num(end)} {num(y)})) (stroke (width 0) (type default)) (uuid {q(uid(key+":wire"))}))')
        angle=0 if side=='L' else 180
        result['objects'].append(f'(label {q(net(n))} (at {num(end)} {num(y)} {angle}) {effects(0.9,"(justify left bottom)")} (uuid {q(uid(key+":label"))}))')
    def component(key,ref,x,y,mapping,value=None,properties=None):
        x=round(x/1.27)*1.27; y=round(y/1.27)*1.27
        spec=SPECS[key]; w,h,points=geometry(spec); identity=uid(ref)
        value=value or spec['name']; fields={
          'Reference':ref, 'Value':value,'Footprint':spec['footprint'], 'Datasheet':spec['url'],
          'Manufacturer': 'Texas Instruments' if spec['name'].startswith(('SN','TPS')) else 'Nexperia' if spec['name'].startswith('74') else 'To be selected',
          'MPN':spec['name'] if key not in ('R','C') else 'TBD',
          'Purpose':'V1.3 power sequencing / shared-MISO interface; bench qualification required'}
        fields.update(properties or {})
        pstr=[]
        for i,(k,v) in enumerate(fields.items()):
            visible=k in ('Reference','Value'); py=y-h-5.08+2.54*(0 if k=='Reference' else 1)
            pstr.append(f'(property {q(k)} {q(v)} (at {num(x)} {num(py)} 0) {"" if visible else "(hide yes)"} {effects(1.0)})')
        puuids=' '.join(f'(pin {q(p["number"])} (uuid {q(uid(ref+":"+p["number"]))}))' for p in spec['pins'])
        obj=f'(symbol (lib_id {q("Power_Impl:"+spec["name"])}) (at {num(x)} {num(y)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {q(identity)}) {" ".join(pstr)} {puuids} (instances (project {q(project_name)} (path {q("/"+root_uuid)} (reference {q(ref)}) (unit 1)))))'
        result['objects'].append(obj)
        result['pin_map'][ref]={}; result['components'][ref]={'value':value,'footprint':spec['footprint'],'datasheet':spec['url'],'pins':{}}
        for p in spec['pins']:
            pn=p['number']; n=mapping.get(pn); dx,dy=points[pn]; px,py=x+dx,y-dy
            result['pin_map'][ref][pn]=net(n) if n is not None else None
            result['components'][ref]['pins'][pn]={'name':p['name'],'net':net(n) if n is not None else None,'xy':[round(px,5),round(py,5)]}
            if n is None:
                result['objects'].append(f'(no_connect (at {num(px)} {num(py)}) (uuid {q(uid(ref+":"+pn+":nc"))}))')
            else: label(n,px,py,ref+":"+pn,p['side'])
    M='MAIN_3V3'; A='AFE_2V98'; G='AGND'; B='AFE_BLOCK'
    forward=[('MCU_MOSI','ADC_MOSI'),('MCU_SCLK','ADC_SCLK'),('MCU_START','ADC_START'),('MCU_RESET','ADC_RESET'),('MCU_PWDN','ADC_PWDN'),('MCU_CS_ADC1','ADC_CS_ADC1'),('MCU_CS_ADC2','ADC_CS_ADC2')]
    ax={'1':M,'2':M,'11':G,'12':G,'13':G,'22':B,'23':A,'24':A,'10':'MCU_ALLOW','14':'ALLOW_AFE'}
    for i,(src,dst) in enumerate(forward): ax[str(3+i)]=src; ax[str(21-i)]=dst
    component('AXC','U9',600,300,ax,properties={'Direction':'DIR1=HIGH, DIR2=LOW: all eight A-to-B (TI Table 7-1)'})
    component('BUF','U10',760,280,{'1':'DOUT1_BLOCK','2':'ADC_DOUT1','3':G,'4':'MCU_MISO','5':M})
    component('BUF','U11',760,330,{'1':'DOUT2_BLOCK','2':'ADC_DOUT2','3':G,'4':'MCU_MISO','5':M})
    component('MUX','U12',920,280,{'1':'ADC_DRDY1','2':G,'3':'ADC_DRDY1','4':'MCU_DRDY1','5':M,'6':G},properties={'Purpose':'DRDY level regenerator only; both data inputs identical, select grounded'})
    component('NAND4','U13',600,380,{'1':'POWER_GOOD','2':'MCU_READY','4':'CHIP_PU','5':M,'14':M,'7':G,'6':B,'8':None,'9':G,'10':G,'12':G,'13':G,'3':None,'11':None},properties={'Purpose':'Schmitt NAND: BLOCK=NOT(POWER_GOOD AND MCU_READY AND CHIP_PU). Unused gate inputs grounded/output NC.'})
    component('OR','U14',760,390,{'1':B,'2':'MCU_CS_ADC1','3':'DOUT2_BLOCK','4':G,'5':B,'6':'MCU_CS_ADC2','7':'DOUT1_BLOCK','8':M},properties={'Purpose':'DOUT isolation: /OE=AFE_BLOCK OR corresponding MCU-side /CS (stable HIGH before enable)'})
    # Both reset outputs are open-drain and intentionally form one reset bus.
    # PRE and AFE LDO enable must derive from converter MAIN_PG, never this bus.
    component('MON','U15',940,370,{'1':'POWER_GOOD','2':G,'3':M,'4':None,'5':'MAIN_SENSE','6':M},properties={'Purpose':'MAIN floor monitor; CT open20ms typical. Clean RESET shared with U16; U17/Q2 drive separate DevKit reset.'})
    component('MON','U16',940,430,{'1':'POWER_GOOD','2':G,'3':M,'4':None,'5':'AFE_SENSE','6':M},properties={'Purpose':'AFE floor monitor; CT open gives 20ms typical; any fault resets MCU and releases READY'})
    component('NAND','U17',600,630,{'1':'POWER_GOOD','2':'POWER_GOOD','3':G,'4':'RESET_SINK_GATE','5':M},properties={'Purpose':'Invert rail-good to reset sink; DevKit reset capacitor is isolated from clean POWER_GOOD'})
    component('NMOS','Q2',760,630,{'1':'RESET_SINK_GATE','2':G,'3':'RESET_SINK_DRAIN'},properties={'Manufacturer':'Alpha and Omega Semiconductor','MPN':'AO3400A','Purpose':'G1 S2 D3; dedicated CHIP_PU sink through2.2ohm. Validate reset fall/hold-up/pulse SOA.'})
    component('NAND','U18',600,735,{'1':B,'2':B,'3':G,'4':'MCU_ALLOW','5':M},properties={'Purpose':'Invert AFE_BLOCK for translated active-clamp release on AXC channel8'})
    clamp={'1':'ALLOW_AFE','19':'ALLOW_AFE','20':A,'10':G,**{str(i+2):G for i in range(8)}}
    for p,n in [('18','CLAMP_MOSI'),('17','CLAMP_SCLK'),('16','CLAMP_START'),('15','CLAMP_RESET'),('14','CLAMP_PWDN'),('13','CLAMP_CS1'),('12','CLAMP_CS2'),('11',None)]:clamp[p]=n
    component('CLAMP','U19',880,735,clamp,properties={'Purpose':'All data inputs GND. Outputs LOW while ALLOW_AFE=0, HiZ during acquisition. Individual10k branches bias ADS inputs without permanentHIGH load.'})
    resistors=[
      ('R70','10k','MCU_READY',G,'Defined READY low during reset; GPIO4 must not be held through restart'),
      ('R71','10k',M,B,'AXC disabled during ramp / missing logic drive'),
      ('R72','10k',M,'DOUT1_BLOCK','DOUT1 disabled by default'),
      ('R73','10k',M,'DOUT2_BLOCK','DOUT2 disabled by default'),
      ('R74','10k','ADC_CS_ADC1','CLAMP_CS1','Switched CS1 low bias; clamp releases during acquisition'),
      ('R75','10k','ADC_CS_ADC2','CLAMP_CS2','Switched CS2 low bias; clamp releases during acquisition'),
      ('R76','10k',M,'POWER_GOOD','Clean open-drain rail-good pullup; isolated from DevKit reset RC'),
      ('R77','67.8k',M,'MAIN_SENSE','Main nominal falling threshold 0.405*(1+67.8/10)=3.1509V'),
      ('R78','10k','MAIN_SENSE',G,'Main sense lower divider'),
      ('R79','59.1k',A,'AFE_SENSE','AFE operating-floor threshold 2.79855V; not acquisition-validity guarantee'),
      ('R80','10k','AFE_SENSE',G,'AFE sense lower divider'),
      ('R81','100k','ADC_DOUT1',G,'Weak defined DOUT1 input when ADC deselected'),
      ('R82','100k','ADC_DOUT2',G,'Weak defined DOUT2 input when ADC deselected'),
      ('R83','100k','MCU_MISO',G,'Defined shared MISO when both isolation outputs are high impedance'),
      ('R84','100k','ADC_DRDY1',G,'Defined raw DRDY when ADC domain unpowered'),
      ('R85','100k','RESET_SINK_GATE',G,'Reset sink gate default'),
      ('R86','2.2','CHIP_PU','RESET_SINK_DRAIN','Reset-cap discharge limiter; >=10uJ pulse capability required'),
    ]
    for i,(ref,value,n1,n2,purpose) in enumerate(resistors):
        component('R',ref,550+((i-15)%4)*140 if i>=15 else 550+(i%4)*140,670 if i>=15 else 455+(i//4)*25,{'1':n1,'2':n2},value,{'Tolerance':'0.1%' if ref in ('R77','R78','R79','R80') else '1%','Power rating':'>=0.1W','Purpose':purpose})
    caps=[('C90',M,'U9 VCCA'),('C91',A,'U9 VCCB'),('C92',M,'U10'),('C93',M,'U11'),('C94',M,'U12'),('C95',M,'U13'),('C96',M,'U14'),('C97',M,'U15'),('C98',M,'U16')]
    for i,(ref,n,purpose) in enumerate(caps):
        component('C',ref,550+((i+15)%4)*140,455+((i+15)//4)*25,{'1':n,'2':G},'100nF',{'Voltage rating':'>=10V','Dielectric':'X7R or qualified C0G','Purpose':purpose+' local bypass; verify effective capacitance'})
    component('C','C116',940,630,{'1':M,'2':G},'100nF',{'Voltage rating':'>=10V','Purpose':'U17 local bypass'})
    component('R','R87',1000,790,{'1':'ALLOW_AFE','2':G},'36.0k',{'Tolerance':'1%','MPN':'CRCW060336K0FKEA','Purpose':'LOW:18uA*36.36k<0.8V. HIGH:3.048/35.64k+10uA<100uA AXC load.'})
    component('C','C117',600,790,{'1':M,'2':G},'100nF',{'Voltage rating':'>=10V','Purpose':'U18 local bypass'})
    component('C','C118',800,790,{'1':A,'2':G},'100nF',{'Voltage rating':'>=10V','Purpose':'U19 local bypass'})
    result['external_connections']={
      'U3.3':'CHIP_PU','U3.4':'MCU_READY','U3.17':'MCU_MOSI','U3.18':'MCU_SCLK','U3.12':'MCU_START','U3.6':'MCU_RESET','U3.7':'MCU_PWDN','U3.16':'MCU_CS_ADC1','U3.20':'MCU_CS_ADC2','U3.19':'MCU_MISO','U3.15':'MCU_DRDY1',
      'U1.34':'ADC_MOSI','U2.34':'ADC_MOSI','U1.40':'ADC_SCLK','U2.40':'ADC_SCLK','U1.38':'ADC_START','U2.38':'ADC_START','U1.36':'ADC_RESET','U2.36':'ADC_RESET','U1.35':'ADC_PWDN','U2.35':'ADC_PWDN','U1.39':'ADC_CS_ADC1','U2.39':'ADC_CS_ADC2','U1.43':'ADC_DOUT1','U2.43':'ADC_DOUT2','U1.47':'ADC_DRDY1','TP2.1':'ADC_DRDY1'}
    result['external_connections']={p:net(n) for p,n in result['external_connections'].items()}
    result['notes']=[
      'U3.4 is the cached 44-pad DevKit header GPIO4. Remove its prior NC; do not change U3.13 GPIO3.',
      'Keep R33-R37 on ADC receiver-side START/RESET/PWDN/MOSI/SCLK nets, unchanged 10k values.',
      'Both supervisor RESET outputs share clean POWER_GOOD. U17/Q2 sink the separate CHIP_PU reset. U13 gates POWER_GOOD, READY and CHIP_PU. PRE/LDO use MAIN_PG, avoiding startup deadlock.',
      'GPIO4 is non-strapping and documented low-only powerup glitch (ESP32-S3 v2.2 Table2-2). Firmware must clear READY before intentional restart and avoid GPIO/RTC hold during resets. Verify watchdog/software reset waveform; no hardware-only claim about all reset kinds.',
      'Both MCU-side CS must be high before MCU_READY rises. Return /OE uses MCU-side CS to avoid both outputs briefly enabling while AXC receivers leave their low startup state. DOUT buffers share MISO as before; simultaneous selected ADCs still violate firmware exclusivity, so no hardware mutual-exclusion claim is made.',
      'TPS3808G01 threshold has +/-2% specified error; full divider/bias/hysteresis and response-time corners require root calculation. 2.80V AFE monitor is an electrical floor, not valid-data window.',
      'GPIO input-low startup and VCAP1/tPOR/clock/reference contract remains necessary. New buffering changes timing/load and needs conservative SPI verification.',
      'This generator never edits or activates any schematic. Root must validate exact candidate pin/net map, ERC and source preservation before implementation.'
    ]
    result['truth_table']=[{'POWER_GOOD':pg,'CHIP_PU':cp,'MCU_READY':ready,'CS1':cs1,'CS2':cs2,'AFE_BLOCK':int(not(pg and cp and ready)),'DOUT1_BLOCK':int((not(pg and cp and ready)) or cs1),'DOUT2_BLOCK':int((not(pg and cp and ready)) or cs2),'normal_protocol_allowed':bool(cs1 or cs2)} for pg in (0,1) for cp in (0,1) for ready in (0,1) for cs1 in (0,1) for cs2 in (0,1)]
    result['notes'].append('The Schmitt NAND has threshold tables at specified VCC points; qualify actual READY levels and reset edges at selected main voltage/temperature. No unmeasured noise or transient guarantee is claimed.')
    result['references']=sorted(result['components'])
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root-uuid',required=True);parser.add_argument('--project-name',default='open-semg-16-v1.3');parser.add_argument('--output',type=Path,default=HERE/'digital-blocks.json')
    args=parser.parse_args(); data=build(args.root_uuid,args.project_name)
    args.output.write_text(json.dumps(data,indent=2)+'\n')
    args.output.with_suffix('.lib.sexpr').write_text('\n'.join(data['lib_symbols'])+'\n')
    args.output.with_suffix('.objects.sexpr').write_text('\n'.join(data['objects'])+'\n')
    print(json.dumps({'output':str(args.output),'components':len(data['components']),'objects':len(data['objects']),'references':data['references']}))
