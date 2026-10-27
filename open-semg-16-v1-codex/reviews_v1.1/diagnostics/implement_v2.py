"""Review-driven, source-span edits restricted to the explicitly authorized V2 schematic."""
from pathlib import Path
import json,re,sys,uuid,hashlib,shutil
from schematic_tools import read,one,all_,props,symbols,pin_positions
TARGET=Path('open-semg-16-v2.kicad_sch').resolve()
ROOT=Path.cwd().resolve()
assert TARGET.parent==ROOT and TARGET.name=='open-semg-16-v2.kicad_sch'
OUT=ROOT/'reviews_v2/diagnostics'
S,R=read(TARGET); changes=[]; edits=[]; additions=[]
def uid():return str(uuid.uuid4())
def num(v):return f'{v:.5f}'.rstrip('0').rstrip('.')
def emit(s):return json.dumps(s,ensure_ascii=False)
def replace(n,new,why):
    old=S[n.start:n.end];edits.append((n.start,n.end,new));changes.append({'reason':why,'before':old,'after':new})
def wire_at(a,b):
    wanted={tuple(round(z,5) for z in a),tuple(round(z,5) for z in b)}
    found=[]
    for n in all_(R,'wire'):
        ps={tuple(round(float(z),5) for z in a[1:]) for a in all_(one(n,'pts'),'xy')}
        if ps==wanted:found.append(n)
    assert len(found)==1,(a,b,len(found))
    return found[0]
def move_bus_wire(a,b,yold,ynew):
    n=wire_at(a,b);new=S[n.start:n.end]
    for pt in all_(one(n,'pts'),'xy'):
        xy=list(map(float,pt[1:]));newxy=(xy[0],ynew if abs(xy[1]-yold)<.0001 else xy[1])
        new=new.replace(S[pt.start:pt.end],f'(xy {num(newxy[0])} {num(newxy[1])})')
    replace(n,new,'F01/F02: move actual supply branch from capacitor return bus to supply bus')
def move_junction(x,yold,ynew):
    n=next(n for n in all_(R,'junction') if list(map(float,one(n,'at')[1:3]))==[round(x,5),round(yold,5)])
    a=one(n,'at');new=S[n.start:n.end].replace(S[a.start:a.end],f'(at {num(x)} {num(ynew)})')
    replace(n,new,'F01/F02: relocate junction with repaired supply branch')
def label(name,x,y,global_=False):
    extra='(shape input) ' if global_ else ''
    return f'({"global_label" if global_ else "label"} {emit(name)} {extra}(at {num(x)} {num(y)} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{uid()}"))'
def wire(x1,y1,x2,y2):
    return f'(wire (pts (xy {num(x1)} {num(y1)}) (xy {num(x2)} {num(y2)})) (stroke (width 0) (type default)) (uuid "{uid()}"))'
def text(t,x,y,size=1.27):
    return f'(text {emit(t)} (at {num(x)} {num(y)} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{uid()}"))'
def instance(lib,ref,value,x,y,pincount=1):
    return f'''(symbol (lib_id "{lib}") (at {num(x)} {num(y)} 0) (unit 1)
        (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")
        (property "Reference" "{ref}" (at {num(x+2.54)} {num(y-5.08)} 0) (effects (font (size 1.27 1.27)) (justify left)))
        (property "Value" {emit(value)} (at {num(x+2.54)} {num(y-2.54)} 0) (effects (font (size 1.27 1.27)) (justify left)))
        (property "Footprint" "" (at {num(x)} {num(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))
        (property "Datasheet" "" (at {num(x)} {num(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))
        {''.join(f'(pin "{p}" (uuid "{uid()}"))' for p in range(1,pincount+1))}
        (instances (project "open-semg-16-v2" (path "/{one(R,'uuid')[1]}" (reference "{ref}") (unit 1)))))'''
def power(value,x,y):
    global pwr_index
    lib='power:GND' if value=='AGND' else 'power:VDD'
    p=instance(lib,f'#PWR0{pwr_index}',value,x,y)
    # Power symbols are not physical BOM/board components.
    p=p.replace('(in_bom yes) (on_board yes)','(in_bom no) (on_board no)')
    pwr_index+=1
    return p
stage=sys.argv[1]
if stage=='power':
    baseline=json.loads((OUT/'pre-edit-hashes.json').read_text())['open-semg-16-v2.kicad_sch']
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==baseline, 'Power stage requires the untouched initial V2 input'
    shutil.copyfile(TARGET,OUT/'initial-v2.kicad_sch')
    for dx,dy in ((0,0),(227.33,-1.27)):
        points=[((166.37,93.98),(172.72,93.98)),((172.72,93.98),(177.8,93.98)),
                ((172.72,93.98),(172.72,101.6)),((177.8,101.6),(177.8,93.98)),
                ((182.88,93.98),(190.5,93.98)),((182.88,93.98),(182.88,101.6))]
        for a,b in points:
            move_bus_wire((round(a[0]+dx,5),round(a[1]+dy,5)),(round(b[0]+dx,5),round(b[1]+dy,5)),93.98+dy,86.36+dy)
        for x in (166.37,172.72,190.5):move_junction(x+dx,round(93.98+dy,5),round(86.36+dy,5))
    count=0
    for ref,n in symbols(R).items():
        if props(n).get('Value')=='DGND':
            p=next(p for p in all_(n,'property') if p[1]=='Value')
            replace(p,S[p.start:p.end].replace('"DGND"','"AGND"'),'F02: explicit common DC return; power symbol '+ref)
            count+=1
    assert count==9,count
elif stage=='clock':
    n=wire_at((195.58,157.48),(210.82,157.48))
    replace(n,S[n.start:n.end].replace('(xy 210.82 157.48)','(xy 220.98 157.48)'), 'F06: connect existing CLK37 wire to existing ADC_CLK global label')
    for n in all_(R,'text'):
        if n[1].startswith('ADC1 provides the clock for ADC2'):
            replace(n,S[n.start:n.end].replace(emit(n[1]),emit('U1 CLK_EN=1 required; shared RESET clears clock output')), 'F06/F18: document clock-output firmware requirement')
elif stage=='controls_probes':
    pwr_index=81
    for i,(signal,x) in enumerate((('START',180.34),('RESET',205.74),('PWDN',231.14)),33):
        y=270.51
        additions.extend([instance('Device:R',f'R{i}','10k',x,y,2),label(signal,x,y-6.35),
                          wire(x,y-6.35,x,y-3.81),wire(x,y+3.81,x,y+6.35),power('AGND',x,y+6.35)])
    additions.append(text('F09: 10k defaults hold START, RESET and PWDN low.\nCS defaults / complete power sequencing remain unresolved.',171.45,288.29))
    # Cache the standard passive test-point symbol only in V2, never in shared libraries.
    libpath='/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Connector.kicad_sym'
    ls,lr=read(libpath);ln=next(n for n in all_(lr,'symbol') if n[1]=='TestPoint')
    libtext=ls[ln.start:ln.end].replace('(symbol "TestPoint"','(symbol "Connector:TestPoint"',1)
    libs=one(R,'lib_symbols')
    edits.append((libs.end-1,libs.end-1,'\n'+libtext+'\n'))
    changes.append({'reason':'F21: add V2-only embedded standard test-point symbol','before':None,'after':libtext})
    nc=next(n for n in all_(R,'no_connect') if list(map(float,one(n,'at')[1:3]))==[422.91,163.83])
    replace(nc,'','F21: replace U2 DRDY intentional NC with real probe connection')
    additions.extend([wire(422.91,163.83,436.88,163.83),label('DRDY_ADC2',436.88,163.83)])
    # Revise the old statement so the diagnostic net is not mistaken for a new MCU assignment.
    for n in all_(R,'text'):
        if n[1]=="We only use ADC1's DRDY":
            a=one(n,'at')
            new=S[n.start:n.end].replace(emit(n[1]),emit('U2 DRDY: test only; MCU still uses U1 DRDY'))
            new=new.replace(S[a.start:a.end],'(at 442.722 166.37 0)')
            replace(n,new,'F21: document probe-only slave DRDY and unchanged MCU mapping')
    specs=[('ADC_CLK','ADC_CLK',True),('DRDY_ADC1','DRDY_ADC1',False),('DRDY_ADC2','DRDY_ADC2',False),
           ('3V3','+3.3V',False),('BAT','+3.7V',False),('AGND','AGND',False)]
    for adc in ('U1','U2'):
        for name,pin in [('VREFP',24),('VCAP1',28),('VCAP2',30),('VCAP3',55),('VCAP4',26)]:
            netname=f'{name}_ADC{1 if adc=="U1" else 2}'
            cref={'U1':{24:'C19',28:'C23',30:'C24',55:'C25',26:'C26'},'U2':{24:'C45',28:'C49',30:'C50',55:'C51',26:'C52'}}[adc][pin]
            px,py=pin_positions(R,cref)['1']['pos']
            additions.append(label(netname,px,py).replace('(justify left bottom)','(justify right bottom)'))
            specs.append((netname,netname,False))
    for i,(value,name,global_) in enumerate(specs,1):
        x=(477.52,506.73,535.94,565.15)[(i-1)%4];y=185.42+22.86*((i-1)//4)
        additions.extend([instance('Connector:TestPoint',f'TP{i}',value,x,y),wire(x,y,x,y+2.54)])
        if name in ('+3.3V','+3.7V','AGND'):additions.append(label(name,x,y+2.54,True))
        else:additions.append(label(name,x,y+2.54,global_))
    additions.append(text('F21: probe access only; test-pad footprints/layout pending',477.52,170.18))
    additions.append(text('V2 PARTIAL CORRECTIONS - NOT READY FOR POWER-UP OR WEARER USE\nF04/F05: parallel LDO outputs and floating EN remain; power architecture requires approval.\nF06/F18: restore U1 CLK_EN after RESET; allow U2 clock/POR; configure both before shared START.\nF09: START/RESET/PWDN default low; CS defaults and full sequencing remain unresolved.\nEnable/settle 2.4V reference; verify gain/rate; keep PACE/RLD/WCT and RLD rerouting off.\nF07/F08: protected body bias and wearer protection remain unimplemented.',266.7,269.24))
else:raise SystemExit('Unknown stage')

if additions:
    edits.append((R.end-1,R.end-1,'\n\t'+'\n\t'.join(additions)+'\n'))
    changes.append({'reason':stage+': new V2 objects','before':None,'after':additions})
for a,b,new in sorted(edits,reverse=True):S=S[:a]+new+S[b:]
# Validate syntax before replacing the authorized file.
probe=OUT/f'{stage}-candidate.kicad_sch';probe.write_text(S);_,checked=read(probe)
assert checked[0]=='kicad_sch'
TARGET.write_text(S)
(OUT/f'{stage}-edit-log.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False))
print(stage,'applied:',len(changes),'logged changes; file',TARGET)
