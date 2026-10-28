"""Build a one-rail V1.3 candidate from the preserved pre-power baseline.

Existing 16-channel source spans are preserved. Writes to the active schematic
are allowed only after native export, ERC and independent pin-map verification.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,re,shutil,sys,uuid

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2];ACTIVE=REPO/'v1.3';SCH=ACTIVE/'open-semg-16-v1.3.kicad_sch'
BASE=HERE.parent/'power_implementation/baseline/open-semg-16-v1.3.kicad_sch'
PREVIOUS=HERE/'baseline/open-semg-16-v1.3.kicad_sch'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
def module(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
old=module('old_source_editor',REPO/'reviews_v1.2/diagnostics/erc_corrections/implement.py')
parse,all_,one,props,symbols=old.parse,old.all_,old.one,old.props,old.symbols
q=old.q
NS=uuid.UUID('eefc02f0-9605-4a5a-a392-f1d0e8bfed5b')
def uid(s):return str(uuid.uuid5(NS,s))
def wire(x,y,xx,yy,key):return f'(wire (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0) (type default)) (uuid {q(uid(key))}))'
def label(n,x,y,key,glob=False,angle=0):
    return f'({"global_label" if glob else "label"} {q(n)} {"(shape input)" if glob else ""} (at {x} {y} {angle}) (effects (font (size 1 1)) (justify left bottom)) (uuid {q(uid(key))}))'
def field(n,v,x,y):return f'(property {q(n)} {q(v)} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'
def note(s,x,y,key):return f'(text {q(s)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid {q(uid(key))}))'

def select_block(defs,items,refs):
    if isinstance(defs,list):defs={parse(s)[1]:s for s in defs}
    if isinstance(items,list):items='\n'.join(items)
    temp=parse('(kicad_sch (lib_symbols '+'\n'.join(defs.values())+') '+items+')')
    inst=symbols(temp);coordinates=set();keep=[];used={}
    for ref in refs:
        n=inst[ref];keep.append(n);used[one(n,'lib_id')[1]]=defs[one(n,'lib_id')[1]]
        coordinates.update(tuple(p['xy']) for p in old.pin_positions(temp,ref).values())
    ends=set(coordinates)
    for n in all_(temp,'wire'):
        pts=[tuple(map(float,z[1:3])) for z in all_(one(n,'pts'),'xy')]
        if any(p in coordinates for p in pts):keep.append(n);ends.update(pts)
    for kind in ['label','global_label','no_connect','junction']:
        for n in all_(temp,kind):
            if tuple(map(float,one(n,'at')[1:3])) in ends:keep.append(n)
    full='(kicad_sch (lib_symbols '+'\n'.join(defs.values())+') '+items+')'
    return used,[full[n.start:n.end] for n in sorted(keep,key=lambda n:n.start)]

def candidate():
    assert SCH.read_bytes()==PREVIOUS.read_bytes(),'Active source changed after simplification backup'
    source=BASE.read_text();root=parse(source,'kicad_sch');ss=symbols(root);rootid=one(root,'uuid')[1]
    pmod=module('prior_power_builder',HERE.parent/'power_implementation/build_power_blocks.py')
    imod=module('prior_input_builder',HERE.parent/'power_implementation/build_input_blocks.py')
    interface=module('minimal_interface',HERE/'build_interface.py')
    pb=pmod.build(rootid);ib=imod.build(rootid,'open-semg-16-v1.3');db=interface.build(rootid,'open-semg-16-v1.3')
    defs,objects=select_block(pb['lib_definitions'],pb['items'],{'U6','L1','C58','C59','R39','R40','R41','R42'})
    ld,ob=select_block(ib['lib_symbols'],ib['objects'],{'J17','F1','Q1','R52'})
    defs.update(ld);objects+=ob
    defs.update({parse(d)[1]:d for d in db['libdefs']});objects+=db['objects']
    expected={}
    for key,n in pb['pin_nets'].items():
        if key.split('.')[0] in {'U6','L1','C58','C59','R39','R40','R41','R42'}:expected[key]=n
    for ref,pm in ib['pin_map'].items():
        if ref in {'J17','F1','Q1','R52'}:
            for pn,net in pm.items():expected[ref+'.'+pn]=net.get('net') if isinstance(net,dict) else net
    for ref,pm in db['pinmap'].items():
        for pn,net in pm.items():expected[ref+'.'+pn]=net
    # PG is intentionally unused; remove its stub/label, then mark the real pin NC.
    extra='\n'.join(objects);tr=parse('(kicad_sch (lib_symbols '+'\n'.join(defs.values())+') '+extra+')')
    u6pin=old.pin_positions(tr,'U6')['5']['xy'];badpoints={tuple(u6pin)};remove=[]
    for n in all_(tr,'wire'):
        pts=[tuple(map(float,z[1:3])) for z in all_(one(n,'pts'),'xy')]
        if tuple(u6pin) in pts:remove.append(n);badpoints.update(pts)
    for n in all_(tr,'label')+all_(tr,'global_label'):
        if tuple(map(float,one(n,'at')[1:3])) in badpoints:remove.append(n)
    # Work on the wrapper so recorded source spans remain exact.
    wrapper='(kicad_sch (lib_symbols '+'\n'.join(defs.values())+') '+extra+')'
    wrapper=old.apply_edits(wrapper,[(n.start,n.end,'') for n in remove]);rr=parse(wrapper)
    extra='\n'.join(wrapper[n.start:n.end] for n in rr[2:] if isinstance(n,list) and n[0]!='lib_symbols')
    extra+=f'\n(no_connect (at {u6pin[0]} {u6pin[1]}) (uuid {q(uid("main.pg.nc"))}))';expected['U6.5']=None
    # Assign actual passive selections for the two buffer packages and series paths.
    t=parse('(root '+extra+')');ep=[]
    for n in all_(t,'symbol'):
        ref=props(n)['Reference'];pf=props(n);updates={}
        if ref in db['components'] and ref.startswith('R'):
            code={'10k':'10K0','3.6k':'3K60','1k':'1K00','100k':'100K'}[pf['Value']]
            updates={'MPN':'CRCW0603'+code+'FKEA','Manufacturer':'Vishay'}
        elif ref in db['components'] and ref.startswith('C'):
            updates={'MPN':'GRM188R71C104KA01D','Manufacturer':'Murata','Voltage rating':'16V'}
        for f in all_(n,'property'):
            if f[1] in updates:ep.append((f.start-6,f.end-6,extra[f.start-6:f.end-6].replace(q(f[2]),q(updates[f[1]]),1)))
    extra=old.apply_edits(extra,ep)
    # A separate filtered analog branch; digital supplies and all buffers use MAIN.
    def passive(ref,lib,value,x,y,n1,n2,mpn,footprint,qualification):
        nonlocal extra
        extra+=f'''\n(symbol (lib_id {q(lib)}) (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid(ref))})
        (property "Reference" {q(ref)} (at {x+3.81} {y-2.54} 0) (effects (font (size 1 1)) (justify left)))
        (property "Value" {q(value)} (at {x+3.81} {y} 0) (effects (font (size 1 1)) (justify left)))
        {field('Footprint',footprint,x,y)} {field('MPN',mpn,x,y)} {field('Qualification',qualification,x,y)}
        (pin "1" (uuid {q(uid(ref+'.1'))})) (pin "2" (uuid {q(uid(ref+'.2'))}))
        (instances (project "open-semg-16-v1.3" (path {q('/'+rootid)} (reference {q(ref)}) (unit 1)))))'''
        extra+='\n'+wire(x,y-3.81,x,y-8.89,ref+'.top')+'\n'+label(n1,x,y-8.89,ref+'.n1',n1 in ['MAIN_3V3','ADC_AVDD','AGND'])
        extra+='\n'+wire(x,y+3.81,x,y+8.89,ref+'.bottom')+'\n'+label(n2,x,y+8.89,ref+'.n2',n2 in ['MAIN_3V3','ADC_AVDD','AGND'])
        expected[ref+'.1']=n1;expected[ref+'.2']=n2
    passive('R78','Device:R','2.2',300.99,440.69,'MAIN_3V3','ADC_AVDD','CRCW06032R20FKEA','Resistor_SMD:R_0603_1608Metric','1%; >=0.1W; analog filter only, no independent regulator')
    for ref,x in [('C112',300.99),('C113',351.79)]:
        passive(ref,'Device:C','2.2uF 16V',x,549.91,'ADC_AVDD','AGND','GRM21BR71C225KA12L','Capacitor_SMD:C_0805_2012Metric','Place at respective U1/U2 AVDD1.54 to AVSS1.53; qualify effective C >=1uF')
    for ref,x in [('C114',402.59),('C115',453.39)]:
        passive(ref,'Device:C','100nF 16V',x,549.91,'ADC_AVDD','AGND','GRM188R71C104KA01D','Capacitor_SMD:C_0603_1608Metric','Respective AVDD1/AVSS1 local high-frequency bypass')
    patches=[];changes=[]
    def replace(n,new,why):
        patches.append((n.start,n.end,new));changes.append({'kind':n[0],'uuid':one(n,'uuid')[1] if one(n,'uuid') else None,'reason':why})
    removed={'U4','U5','C53','C54','C55','C56','R38','#PWR068','#PWR070','#PWR071','#PWR072','#PWR073','#PWR075','#PWR078','#PWR080'}
    for ref in removed:replace(ss[ref],'','Remove obsolete disabled LDO/temporary branch '+ref)
    r38ids={'e5573417-6666-45ee-bc68-d987fd230545','74388d83-4e1a-49ca-8f61-e8a7da3d3c6b','a4c57393-c0d0-45c9-bc94-65d0cc605125'}
    for n in all_(root,'wire'):
        pts=[list(map(float,z[1:3])) for z in all_(one(n,'pts'),'xy')]
        if all(70<=x<=167 and 255<=y<=340 for x,y in pts) or old.id_(n) in r38ids:replace(n,'','Remove only obsolete LDO/strap wire')
    for kind in ['junction','no_connect']:
        for n in all_(root,kind):
            x,y=map(float,one(n,'at')[1:3])
            if 70<=x<=167 and 255<=y<=340:replace(n,'','Remove obsolete power object')
    analog_power={'#PWR06','#PWR037'}
    for ref,n in ss.items():
        if ref in removed:continue
        if ref.startswith('#') and props(n).get('Value')=='+3.3V':
            p=next(x for x in all_(n,'property') if x[1]=='Value');net='ADC_AVDD' if ref in analog_power else 'MAIN_3V3'
            replace(p,source[p.start:p.end].replace(q(p[2]),q(net),1),'Assign analog filter or shared MAIN')
    analog_globals={'066ca9c8-7bd4-4f0b-92e4-56350bd7253c','3589528b-9c95-40c8-a912-f86516f6c24c','792ff479-7cd1-49c0-b4af-14b86c12e8f8','bd298a1f-5ec1-4f2d-a055-09b58728a7c2'}
    for n in all_(root,'global_label'):
        if n[1]=='+3.3V':
            net='ADC_AVDD' if old.id_(n) in analog_globals else 'MAIN_3V3'
            replace(n,source[n.start:n.end].replace(q(n[1]),q(net),1),'Preserve supply ownership with one filtered branch')
    mcu={'MOSI':'MCU_MOSI','SCLK':'MCU_SCLK','START':'MCU_START','RESET':'MCU_RESET','PWDN':'MCU_PWDN','CS_ADC1':'MCU_CS1','CS_ADC2':'MCU_CS2','DRDY_ADC1':'MCU_DRDY'}
    bias={('START',180.34,264.16),('RESET',205.74,264.16),('PWDN',231.14,264.16),('MOSI',180.34,302.26),('SCLK',205.74,302.26)}
    for n in all_(root,'label'):
        x,y=map(float,one(n,'at')[1:3]);name=n[1]
        if name in {'EN','LP2985_OUT_DISABLED'}:replace(n,'','Remove old power labels')
        elif ((x>560 and y<100) or (name,x,y) in bias) and name in mcu:
            replace(n,source[n.start:n.end].replace(q(name),q(mcu[name]),1),'Buffer MCU controls; reuse five10k biases on MCU side')
        elif name=='MISO' and x<470:
            net='DOUT_ADC1' if x<300 else 'DOUT_ADC2';replace(n,source[n.start:n.end].replace(q(name),q(net),1),'Separate series-limited DOUT branches before shared MISO')
    for n in all_(root,'text_box'):
        if n[1].strip() in ['MCU LDO Configuration','ADC LDO Configuration']:replace(n,'','Remove obsolete LDO boxes')
    for n in all_(root,'text'):
        if n[1].startswith('F04: U4 output isolated'):replace(n,'','Remove superseded disabled-LDO note')
        elif n[1].startswith('V1.2 PARTIAL CORRECTIONS'):
            txt='V1.3 SIMPLE POWER - BENCH VERIFICATION REQUIRED\nONE3.3V converter powers MCU, ADC DVDD and two interface buffers.\nADC AVDD/AVDD1 use2.2ohm RC branch; analog auxiliary pins follow actual AVDD.\nNo2.98V rail, second converter, LDO, READY gates or ADC power switch.\nKeep USB inaccessible while seated; unplug pack and unseat DevKit for USB.\nFirmware: outputsLOW, POR/VCAP1/reset, U1 CLK_EN then U2, references/config, common START.\nF07/F08 body bias and wearer protection remain open.'
            replace(n,source[n.start:n.end].replace(q(n[1]),q(txt),1),'Record simplified architecture')
        elif n[1].startswith('V1.2 F09:'):
            txt='V1.3: R33-R37 now bias244 INPUTS on MCU side; two CS input pulls added.\nDOUT series resistors limit cold-start output opposition; normal reads need exclusive CS.\nStart bench SPI at1MHz/2kSPS; validate2MHz, signal capacitance and4kSPS before relying on them.\nNo precision fault-survival or wearer readiness follows from this schematic.'
            replace(n,source[n.start:n.end].replace(q(n[1]),q(txt),1),'Replace obsolete R38/startup note')
        elif n[1].startswith('V1.2 F12/F14'):
            txt=n[1].replace('V1.2','V1.3').replace('C55 BP: 10nF unchanged; leakage <100nA at operating bias/temperature.','Old LDO/BP parts removed; complete component/PCB qualification before power.')
            replace(n,source[n.start:n.end].replace(q(n[1]),q(txt),1),'Preserve input/VCAP requirements; remove obsolete BP note')
    # Preserve the selected stock DevKit and specified bulk capacitor from the current revision.
    curr=PREVIOUS.read_text();currroot=parse(curr);currss=symbols(currroot)
    for ref in ['U3','C57']:
        n=currss[ref];snippet=curr[n.start:n.end]
        # Current U3 was wired through labels, not source-body changes; restore its unchanged instance/pins.
        replace(ss[ref],snippet,'Retain stock DevKit selection or specified220uF polarized MAIN bulk')
    defs['Device:C_Polarized']=pmod.installed('Device:C_Polarized')
    for ref in ['R33','R34','R35','R36','R37']:
        # Their actual pin-net changes are labels above; keep selected part/footprint metadata.
        n=currss[ref];replace(ss[ref],curr[n.start:n.end],'Retain10k input-bias MPN/footprint; route on MCU side')
    extra+='\n'+note('ONE-RAIL BRING-UP: protected1S battery -> single3.3V buck-boost.\nR78 is a passive analog supply filter, not another regulator.\nUSB only with pack disconnected and DevKit physically removed.',50.8,365.76,'simple.tree')
    extra+='\n'+note('SIMPLE INTERFACE: two buffer ICs total. No READY, ADC_ON or monitor tree.\nSeven MCU-side input pulldowns hold244 outputsLOW at boot.\nDOUT branches join through3.6k; return buffer regenerates MISO/DRDY.\nFirmware must reinitialize ADCs on every reset; on-board ESP reset/BOD remain in use.',600.71,365.76,'simple.interface')
    # Use global scope consistently only for rails shared with existing power symbols.
    t=parse('(root '+extra+')');ep=[]
    for n in all_(t,'label'):
        if n[1] in {'+3.7V','AGND','MAIN_3V3','SW_BAT_PROT','ADC_AVDD'}:
            start,end=n.start-6,n.end-6;snippet=extra[start:end].replace('(label ','(global_label ',1).replace('(at ','(shape input) (at ',1));ep.append((start,end,snippet))
    extra=old.apply_edits(extra,ep)
    libs=one(root,'lib_symbols');present={n[1] for n in all_(libs,'symbol')}
    patches.append((libs.end-1,libs.end-1,'\n'+'\n'.join(v for k,v in defs.items() if k not in present)+'\n'))
    replace(one(root,'paper'),'(paper "A0")','Keep new blocks on sheet, channel coordinates untouched')
    tb=one(root,'title_block');c=next(n for n in all_(tb,'comment') if n[1]=='1');replace(c,'(comment 1 "Version1.3 - simple shared3.3V power; bench validation pending")','Identify simpler revision')
    patches.append((root.end-1,root.end-1,'\n'+extra+'\n'))
    result=old.apply_edits(source,patches);rr=parse(result,'kicad_sch')
    assert len(symbols(rr))==len(all_(rr,'symbol'));ids=re.findall(r'\(uuid\s+"([^"]+)"\)',result);assert len(ids)==len(set(ids))
    (HERE/'simple-candidate.kicad_sch').write_text(result)
    # Candidate libraries: keep previous library files unchanged, add only the compact interface definitions.
    for name in ['V13_Power.kicad_sym','Power_Impl.kicad_sym']:shutil.copy2(HERE/'baseline'/name,HERE/name)
    entries=[]
    for k,v in defs.items():
        if k.startswith('V13_SimpleActive:'):
            name=k.split(':',1)[1];entries.append(v.replace('(symbol '+q(k),'(symbol '+q(name),1))
    (HERE/'V13_SimpleActive.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(entries)+'\n)\n')
    table=(HERE/'baseline/sym-lib-table').read_text();tr=parse(table);entry='(lib (name "V13_SimpleActive") (type "KiCad") (uri "${KIPRJMOD}/V13_SimpleActive.kicad_sym") (options "") (descr "V1.3 minimal common-rail interface"))'
    table=table[:tr.end-1]+'\n'+entry+'\n'+table[tr.end-1:];(HERE/'sym-lib-table').write_text(table)
    shutil.copy2(HERE/'baseline/open-semg-16-v1.3.kicad_pro',HERE/'simple-candidate.kicad_pro')
    (HERE/'expected-new-pins.json').write_text(json.dumps(expected,indent=2)+'\n')
    (HERE/'simplification-edit-plan.json').write_text(json.dumps({'changes':changes,'previous_components':204,'remove_complex_architecture':True,'source_from_preserved133_component_baseline':str(BASE),'candidate_sha256':hashlib.sha256(result.encode()).hexdigest()},indent=2)+'\n')
    print('Simplified candidate created')

def commit():
    assert SCH.read_bytes()==PREVIOUS.read_bytes(),'Active design changed concurrently'
    v=json.loads((HERE/'candidate-verification.json').read_text());assert v['passed'],v
    (ACTIVE/'V13_SimpleActive.kicad_sym').write_bytes((HERE/'V13_SimpleActive.kicad_sym').read_bytes())
    (ACTIVE/'sym-lib-table').write_bytes((HERE/'sym-lib-table').read_bytes())
    tmp=SCH.with_suffix('.kicad_sch.tmp');tmp.write_bytes((HERE/'simple-candidate.kicad_sch').read_bytes());tmp.replace(SCH)
    print('Applied simple design to',SCH)

if __name__=='__main__':{'candidate':candidate,'commit':commit}[sys.argv[1]]()
