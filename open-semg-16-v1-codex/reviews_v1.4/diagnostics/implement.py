"""Build V1.4 candidate from the task-start backup; never touch history.

Preserve embedded library pin types, component UUIDs and procurement fields.
Replace sheet wiring/placement explicitly, export candidate before installation.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess, sys, uuid
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ACTIVE = REPO / 'v1.4'
TARGET = ACTIVE / 'open-semg-16-v1.4.kicad_sch'
BASE = HERE / 'before-implementation' / TARGET.name
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
spec = importlib.util.spec_from_file_location('reader', REPO / 'reviews_v1.2/diagnostics/erc_corrections/implement.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
q, parse, one, all_, props = t.q, t.parse, t.one, t.all_, t.props
source = BASE.read_text(); root = parse(source); ss = t.symbols(root)
namespace = uuid.UUID('f9ed91c0-9db1-4bf0-98ab-215a914b2924')
def uid(key): return str(uuid.uuid5(namespace, key))
def num(n): return f'{n:.5f}'.rstrip('0').rstrip('.') if float(n) else '0'
def snap(n): return round(round(n/1.27)*1.27,5)
objects = []
def wire(x,y,xx,yy,key):
    x,y,xx,yy=map(snap,(x,y,xx,yy))
    if (x,y)==(xx,yy): return
    objects.append(f'(wire (pts (xy {num(x)} {num(y)}) (xy {num(xx)} {num(yy)})) (stroke (width 0) (type default)) (uuid {q(uid(key))}))')
def label(net,x,y,key,side='R'):
    x,y=map(snap,(x,y))
    angle = 90 if side in ('T','B') else 0
    justify = 'right bottom' if side=='L' else 'left bottom'
    objects.append(f'(label {q(net)} (at {num(x)} {num(y)} {angle}) (effects (font (size 1 1)) (justify {justify})) (uuid {q(uid(key))}))')
def note(text,x,y,key,size=1.5):
    x,y=map(snap,(x,y))
    objects.append(f'(text {q(text)} (at {num(x)} {num(y)} 0) (effects (font (size {size} {size})) (justify left top)) (uuid {q(uid(key))}))')
def instance(ref,x,y,template=None,value=None,fields=None):
    x,y=map(snap,(x,y))
    n=ss[template or ref]; raw=source[n.start:n.end]
    oldx,oldy,ang=map(float,one(n,'at')[1:]); dx,dy=x-oldx,y-oldy
    patches=[]
    at=one(n,'at'); patches.append((at.start-n.start,at.end-n.start,f'(at {num(x)} {num(y)} {num(ang)})'))
    for p in all_(n,'property'):
        a=one(p,'at'); ax,ay,aa=map(float,a[1:])
        if p[1] in ('Reference','Value') and ref[0] in ('R','C'):
            if ang==90: ax,ay,aa=x,y+(-3.8 if p[1]=='Reference' else 3.8),90
            else: ax,ay,aa=x+2.54,y+(-1.2 if p[1]=='Reference' else 1.2),0
        else: ax,ay=ax+dx,ay+dy
        patches.append((a.start-n.start,a.end-n.start,f'(at {num(ax)} {num(ay)} {num(aa)})'))
        if p[1]=='Value' and value is not None:
            # Keep replacement within the property, excluding its nested position patch.
            start=p.start-n.start; atom=q(p[2]); loc=raw.index(atom,start)
            patches.append((loc,loc+len(atom),q(value)))
    raw=t.apply_edits(raw,patches)
    for project in re.findall(r'\(project\s+"([^"]+)"',raw): raw=raw.replace('(project '+q(project),'(project "open-semg-16-v1.4"')
    if template:
        raw=raw.replace(q(template),q(ref))
        raw=re.sub(r'\(uuid\s+"([^"]+)"\)',lambda m:'(uuid '+q(uid(ref+':'+m[1]))+')',raw)
    for name,val in (fields or {}).items():
        raw=raw[:-1]+f' (property {q(name)} {q(val)} (at {num(x)} {num(y)} 0) (effects (font (size 1 1)) (hide yes))))'
    objects.append(raw)

retained={f'C{i}' for i in range(1,53)}|{f'R{i}' for i in range(1,38)}|{f'E{i}' for i in range(1,17)}|{'U1','U2','U3'}
added={f'C{i}' for i in range(58,64)}|{'R39','R40','R41'}
netroot=ET.parse(HERE/'initial-netlist.xml').getroot()
pinmap={}
for net in netroot.find('nets'):
    name=net.get('name').lstrip('/')
    if name=='AGND':name='GND'
    if name=='MOSI':name='SPI_MOSI'
    if name=='MISO':name='SPI_MISO'
    if name=='SCLK':name='SPI_SCLK'
    for p in net:
        if p.get('ref') in retained:
            pinmap[(p.get('ref'),p.get('pin'))]=None if name.startswith('unconnected-') else name
for ch in range(1,17):
    adc='U1' if ch<=8 else 'U2'; local=(ch-1)%8+1
    for pol,ep,r,pn in [('P','1',2*ch-1,18-2*local),('N','2',2*ch,17-2*local)]:
        old=pinmap[(adc,str(pn))]
        for node in list(pinmap):
            if pinmap[node]==old:pinmap[node]=f'CH{ch:02}_{pol}'
        pinmap[(f'E{ch}',ep)]=pinmap[(f'R{r}','1')]=f'CH{ch:02}_{pol}_IN'
for p in ('19','16','20','15'):pinmap[('U3',p)]=None
for p,n in {'37':'SPI_MISO','27':'CS_ADC1','36':'CS_ADC2','38':'DRDY_ADC1','39':'DRDY_ADC2','13':'GPIO3_STRAP'}.items():pinmap[('U3',p)]=n
pinmap[('U3','21')]=None # USB-fed 5V remains internal to the stock DevKit.
for ref,n in [('R39','CS_ADC1'),('R40','CS_ADC2'),('R41','GPIO3_STRAP')]:
    pinmap[(ref,'1')]=n; pinmap[(ref,'2')]='+3.3V'
for ref,n in [('C58','VCAP3_ADC1'),('C59','VCAP3_ADC2'),('C60','+3.3V'),('C61','+3.3V'),('C62','+3.3V'),('C63','+3.3V')]:
    pinmap[(ref,'1')]=n;pinmap[(ref,'2')]='GND'

note('OPEN-sEMG-16 V1.4  |  USB power / Wi-Fi data  |  16 x 24-bit channels at target 2 kSPS',20,14,'title',2.5)
note('BENCH ONLY: simulated, non-human-connected signals. Never attach a person while laptop USB is connected.\nUSB supplies power/programming/debug; acquisition frames go over built-in Wi-Fi. Firmware and hardware remain untested.',20,25,'bench',1.8)

# Preserve and lay out all 16 differential input networks with explicit local wiring.
input_refs=set()
for bank in range(2):
    b=20+bank*290
    note(f'ADS1298 #{bank+1} / channels {1+8*bank}-{8+8*bank}',b,45,f'area{bank}',2)
    for local in range(8):
        ch=bank*8+local+1;y=65+25.4*local
        er=f'E{ch}'; instance(er,b+10,y);input_refs.add(er)
        note(f'CH{ch:02}',b+2,y-8,f'channel{ch}',1.2)
        for pol,ep,ri,yy,cx in [('P','1',2*ch-1,y,b+55),('N','2',2*ch,y+10.16,b+78)]:
            rr=f'R{ri}';instance(rr,b+35,yy);input_refs.add(rr)
            cn=next(p.get('ref') for net in netroot.find('nets') for p in net if p.get('ref','').startswith('C') and p.get('pin')=='1' and any(x.get('ref')==('U1' if bank==0 else 'U2') and x.get('pin')==str(18-2*(local+1) if pol=='P' else 17-2*(local+1)) for x in net))
            instance(cn,cx,yy+3.81);input_refs.add(cn)
            # Connector pin2 fans down to the independent negative input path.
            ey=y+(2.54 if ep=='2' else 0)
            wire(b+15.08,ey,b+21.59,ey,f'{er}{pol}:1')
            wire(b+21.59,ey,b+21.59,yy,f'{er}{pol}:2')
            wire(b+21.59,yy,b+31.19,yy,f'{er}{pol}:3')
            wire(b+38.81,yy,cx,yy,f'{rr}:cap')
            wire(cx,yy,b+101.6,yy,f'{rr}:label')
            label(f'CH{ch:02}_{pol}',b+101.6,yy,f'{rr}:net')
            wire(cx,yy+7.62,cx,yy+8.89,f'{cn}:gnd')
            label('GND',cx,yy+8.89,f'{cn}:gndlabel')
            objects.append(f'(junction (at {num(snap(cx))} {num(snap(yy))}) (diameter 0) (color 0 0 0 0) (uuid {q(uid(cn+":junction"))}))')
    instance('U'+str(bank+1),b+220,132)
    # Three local supply domains, still one electrical 3.3V net.
    for i,ref in enumerate(['C6','C7','C8','C9'] if bank==0 else ['C32','C33','C34','C35']):instance(ref,b+20+i*35,300)
    for i,ref in enumerate(['C60','C61'] if bank==0 else ['C62','C63']):
        instance(ref,b+175+i*35,300,template='C6',value='1uF' if ref in ('C60','C62') else '0.1uF',fields={'Voltage rating':'>=10V','Purpose':f'ADC{bank+1} AVDD1 pin54 / AVSS1 pin53 local charge-pump bypass; same 3V3/GND nets','Qualification':'Effective ceramic capacitance, bias, temperature and short star return must be verified'})
    note('AVDD local             DVDD local                  AVDD1 local\nRoute each bypass at its pins; star AVDD1/AVSS1 to AVDD/AVSS.\nAll three domains use the SAME DevKit 3.3V rail and common return.',b,270,f'power{bank}',1.3)
    for i,ref in enumerate(['C19','C20','C23','C24','C25','C26'] if bank==0 else ['C45','C46','C49','C50','C51','C52']):instance(ref,b+20+i*43,355)
    extra='C58' if bank==0 else 'C59'
    instance(extra,b+200,395,template='C6',value='0.1uF',fields={'Voltage rating':'>=10V','Purpose':'VCAP3 high-frequency bypass parallel to retained 1uF, ADS1298 Figure106','Qualification':'Qualify effective C at approximately5.2V; internal node must not power loads'})
    note('Reference / internal bypass nodes: separate per ADC; never join VCAPs.\nVREFP: 10uF || 100nF to VREFN/GND; enable internal 2.4V reference.\nVCAP1=22uF, VCAP2=1uF, VCAP3=1uF || 100nF, VCAP4=1uF.\nVCAP3 is about5.2V on3.3V supply: >=10V rated, bias-qualified parts.',b,325,f'ref{bank}',1.3)
    note('Input pairs: 2k per leg (0.1%, >=0.1W), 620pF to GND (C0G,1%).\nPreserved RC topology; no added human-contact protection.\nUnused PACE/RLDIN17/18/62 tied to AVDD: keep PACE/rerouting OFF.\nRLDREF/RLDINV/RLDOUT/WCT unconnected; keep RLD/WCT OFF.\nGPIO1-4, DAISY_IN and RESV1 grounded; configure GPIO1-4 as inputs.',b,425,f'unused{bank}',1.3)

instance('U3',730,115)
note('ESP32-S3 DevKitC-1 / USB power',620,45,'esp-area',2)
note('Use a complete stock DevKitC-1, not a bare module.\nLaptop USB -> onboard regulator -> 3V3 header pins1/2.\nNo battery, external regulator or other3V3 source.\n5V and CHIP_PU header branches have no carrier connection;\nonboard USB, reset, boot and UART circuits remain in DevKit.',620,175,'devkit',1.4)
for i,ref in enumerate(['R33','R34','R35','R36','R37']):instance(ref,630+i*36,245)
for i,ref in enumerate(['R39','R40','R41']):
    purpose={'R39':'CS1 HIGH while MCU high-Z; GPIO21 avoids documented boot LOW glitch','R40':'CS2 HIGH while MCU high-Z; GPIO39 avoids documented boot LOW glitch','R41':'Define GPIO3 HIGH for strap-selected USB JTAG; verify eFuses allow GPIO39-42'}[ref]
    instance(ref,640+i*62,285,template='R33',fields={'Tolerance':'1%','Rated power':'>=0.1W','Purpose':purpose})
note('Shared communication / startup (F06/F09/F18)',620,215,'comms-title',1.8)
note('Direct MOSI=GPIO11; SCLK=GPIO12; MISO=GPIO40.\nCS1=GPIO21 / CS2=GPIO39: HIGH at boot; select ONE ADC only.\nDOUT is high-Z with CS HIGH (TI9.4.2.1). No external MISO gate.\nDRDY1=GPIO41 / DRDY2=GPIO42, input-only, pulls disabled.\nUse GPIO mux, disable pad JTAG; verify eFuses before assembly.\nGPIO3 HIGH selects USB JTAG only in strap-controlled modes.',620,310,'comms',1.4)
note('START=GPIO8; RESET=GPIO6; PWDN=GPIO7.\n10k pulldowns retain LOW while MCU high-Z (also DIN/SCLK).\nBoot/warm reset: initialize LOW forward latches; CS both HIGH.\nRelease PWDN; wait U1POR/VCAP1>1.1V; pulse shared RESET,\nthen hold RESET HIGH. SDATAC/configure U1 with CLK_EN=1.\nU1CLKSEL=HIGH, U2CLKSEL=LOW; U1CLK drives both CLK pins.\nWait U2POR on valid clock; use CS2-only SPI RESET command.\nKeep shared RESET HIGH, or restart entire clock initialization!\nConfigure both: 2.4V reference enable/settle/readback, then START.\nPOR >=2^18 clocks per ADC; observe TI11.1 timing.\nTI low-input ramp wording vs CS pullups needs bench review.',620,350,'startup',1.4)
note('Acquisition / wireless target (firmware required)',620,410,'wifi-title',1.8)
note('HR mode2kSPS nominal: CONFIG1 HR=1, DR=100, both ADCs.\n2 x (24-bit status +8x24-bit data) =54 bytes/sample pair.\n2k pairs/s =108kB/s;2MHz SPI takes216us of each500us.\nSPI mode1, short traces; verify measured loaded logic/edges.\nExample Wi-Fi:10 pairs +16B header/UDP =116.8kB/s at IP layer.\nUse SPI DMA, separate Wi-Fi task, ring buffer, sequence IDs.\nBounded RF outages need buffering/retry; no lossless claim tested.',620,422,'wifi',1.4)
note('Electrical limits / bench prerequisites',20,475,'limits-title',1.9)
note('Power budget NOT verified: identify fitted DevKit/regulator, USB current authorization, 3V3 droop, capacitor stability and temperature.\nReference DevKit v1.1 regulator: SGM2212,800mA rating; not a guaranteed available header current. 500mA USB has no full worst-case margin.\nWi-Fi355mA is a characterized TX peak at3.3V/25C, not a complete-system maximum. No external power source may join the3V3 rail.\nNo external analog source before rails are valid. Begin with ADC internal-short/test mux, then a grounded simulator near1.65V common mode.\nAt gain6 and2.4V reference: |VD|<0.4V and0.2+G|VD|/2<VCM<3.3-0.2-G|VD|/2. Keep each input within rails;2k is not a clamp.\nDirect ESP->ADS VIH/VOH limits meet only at0.8xVDD; loaded HIGH margin/startup ramps require scope checks. Keep RF returns away from ADC loops.\nF07/F08 body bias, wearer protection and isolation remain unimplemented. Bench power-up requires the checks in reviews_v1.4/implementation.md.',20,487,'limits',1.5)

# Generate short pin-label connections, preserving only established/explicitly unused NCs.
usedlibs={one(ss[r],'lib_id')[1] for r in retained}
defs='\n'.join(source[n.start:n.end] for n in all_(one(root,'lib_symbols'),'symbol') if n[1] in usedlibs)
wrapper='(kicad_sch (lib_symbols '+defs+') '+'\n'.join(objects)+')'
wr=parse(wrapper)
existing_nc={tuple(map(float,one(n,'at')[1:3])) for n in all_(root,'no_connect')}
oldpins={r:t.pin_positions(root,r) for r in retained}
for ref in sorted(retained|added):
    if ref in input_refs:continue
    pins=t.pin_positions(wr,ref); inst=t.symbols(wr)[ref];x,y=map(float,one(inst,'at')[1:3]);seen=set()
    for pn,info in pins.items():
        px,py=info['xy']; net=pinmap[(ref,pn)]
        if (px,py) in seen:continue
        seen.add((px,py));key=ref+'.'+pn
        if net is None:
            # No arbitrary new NCs: reuse prior intentional carrier/unused ADC decisions.
            old=oldpins.get(ref,{}).get(pn)
            if old and (tuple(old['xy']) in existing_nc or (ref=='U3' and pn in ('15','16','19','20'))):
                objects.append(f'(no_connect (at {num(px)} {num(py)}) (uuid {q(uid(key+":nc"))}))')
            continue
        if ref in ('U1','U2','U3'):
            side='L' if px<x-8 else 'R' if px>x+8 else 'T' if py<y else 'B'
        else:side='T' if py<y else 'B'
        ex,ey=px,py
        if side=='L':ex-=7.62
        if side=='R':ex+=7.62
        if side=='T':ey-=7.62
        if side=='B':ey+=7.62
        wire(px,py,ex,ey,key+':wire');label(net,ex,ey,key+':label',side)

header='(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") '+source[one(root,'uuid').start:one(root,'uuid').end]
header+=' (paper "A1") (title_block (title "Open-sEMG-16 USB / Wi-Fi bench prototype") (date "2026-10-28") (rev "1.4") (company "McGill AI Lab") (comment 1 "Simulated signals only - no human connection with laptop USB"))'
sheet=one(root,'sheet_instances'); extra=source[sheet.start:sheet.end] if sheet else ''
candidate=header+'\n(lib_symbols\n'+defs+'\n)\n'+'\n'.join(objects)+'\n'+extra+'\n)\n'
cr=parse(candidate,'kicad_sch');assert set(t.symbols(cr))==retained|added
ids=re.findall(r'\(uuid\s+"([^"]+)"\)',candidate); assert len(ids)==len(set(ids)),'duplicate UUID'
dest=HERE/'candidate.kicad_sch';dest.write_text(candidate)
r=subprocess.run([CLI,'sch','export','netlist','--format','kicadxml','-o',str(HERE/'candidate-netlist.xml'),str(dest)],capture_output=True,text=True)
assert r.returncode==0,r.stderr
components=ET.parse(HERE/'candidate-netlist.xml').getroot().find('components')
assert {c.get('ref') for c in components}==retained|added
(HERE/'modifications.json').write_text(json.dumps({'before_sha256':hashlib.sha256(source.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'removed':sorted(set(ss)-retained),'retained':sorted(retained),'added':sorted(added),'physical_count_before':133,'physical_count_after':len(components),'pinmap':{r+'.'+p:n for (r,p),n in sorted(pinmap.items())},'method':'Retained embedded symbol definitions/pin types and original component identities/fields; explicit schematic layout and net labels; candidate native export before install'},indent=2)+'\n')
print('Candidate exported:',len(components),'components;',dest)

if '--install' in sys.argv:
    assert TARGET.read_bytes()==BASE.read_bytes(),'Active source changed since backup'
    tmp=TARGET.with_suffix('.kicad_sch.tmp');tmp.write_text(candidate);tmp.replace(TARGET)
    print('Installed candidate in V1.4 only')
