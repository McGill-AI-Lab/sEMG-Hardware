"""Bounded V1.3-only source edits; candidate first, commit only after verification.

Helpers generate new blocks, never mutate the active schematic. Existing objects
outside the explicitly recorded power/control changes retain their source bytes.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess, sys, uuid
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
ACTIVE=REPO/'v1.3'
SCH=ACTIVE/'open-semg-16-v1.3.kicad_sch'
BASE=OUT/'baseline/open-semg-16-v1.3.kicad_sch'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

# Read-only reuse of the previously validated parser/source-span implementation.
old=module('prior_editor',REPO/'reviews_v1.2/diagnostics/erc_corrections/implement.py')
parse,all_,one,props,symbols=old.parse,old.all_,old.one,old.props,old.symbols
q=old.q
NS=uuid.UUID('218b5fb6-b544-4ad9-b5e7-6110214bdc38')
def uid(k):return str(uuid.uuid5(NS,k))
def wire(x,y,xx,yy,key):return f'(wire (pts (xy {x} {y}) (xy {xx} {yy})) (stroke (width 0) (type default)) (uuid {q(uid(key))}))'
def label(net,x,y,key,global_=False):
    head='global_label' if global_ else 'label';shape=' (shape input)' if global_ else ''
    return f'({head} {q(net)}{shape} (at {x} {y} 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid {q(uid(key))}))'
def note(text,x,y,key):return f'(text {q(text)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid {q(uid(key))}))'
def property_(name,val,x,y):return f'(property {q(name)} {q(val)} (at {x} {y} 0) (effects (font (size 1.0 1.0)) (hide yes)))'

def normalize_block(b):
    defs=b.get('lib_definitions',b.get('lib_symbols',{}))
    if isinstance(defs,list):defs={parse(s)[1]:s for s in defs}
    items=b.get('items',b.get('objects',[]))
    if isinstance(items,list):items='\n'.join(items)
    return defs,items

def create_candidate():
    source=BASE.read_text();root=parse(source,'kicad_sch');ss=symbols(root);root_id=one(root,'uuid')[1]
    allowed=[BASE.read_bytes()]
    if (OUT/'before-bias-refinement.kicad_sch').exists():allowed.append((OUT/'before-bias-refinement.kicad_sch').read_bytes())
    assert SCH.read_bytes() in allowed,'Active source differs from saved checkpoints'
    assert SCH.parent.resolve()==ACTIVE.resolve()
    defs={};items=[];block_records={}
    for name in ['power','input','digital']:
        mod=module('new_'+name,OUT/('build_'+name+'_blocks.py'))
        b=mod.build(root_id,'open-semg-16-v1.3');ld,it=normalize_block(b)
        for k,v in ld.items():
            if k in defs:assert parse(defs[k])==parse(v),(name,k)
            defs[k]=v
        items.append(it);block_records[name]=b
    (OUT/'assembled-block-data.json').write_text(json.dumps(block_records,indent=2)+'\n')
    patches=[];changes=[]
    def replace(n,text,why):
        patches.append((n.start,n.end,text));changes.append({'object':n[0],'uuid':one(n,'uuid')[1] if one(n,'uuid') else None,'change':why})
    removed_refs={'U4','U5','C53','C54','C55','C56','R38','#PWR068','#PWR070','#PWR071','#PWR072','#PWR073','#PWR075','#PWR078','#PWR080'}
    for ref in removed_refs:replace(ss[ref],'','Remove obsolete disabled LDO/EN branch: '+ref)
    r38_wires={'e5573417-6666-45ee-bc68-d987fd230545','74388d83-4e1a-49ca-8f61-e8a7da3d3c6b','a4c57393-c0d0-45c9-bc94-65d0cc605125'}
    for n in all_(root,'wire'):
        pts=[list(map(float,z[1:3])) for z in all_(one(n,'pts'),'xy')]
        if all(70<=x<=167 and 255<=y<=340 for x,y in pts) or old.id_(n) in r38_wires:
            replace(n,'','Remove wire belonging only to obsolete LDO/EN branch')
        elif pts==[[180.34,322.58],[205.74,322.58]]:
            replace(n,'','Separate DIN/SCLK switched-bias returns')
    for n in all_(root,'junction'):
        x,y=map(float,one(n,'at')[1:3])
        if 70<=x<=167 and 255<=y<=340:replace(n,'','Remove obsolete power-branch junction')
        elif (x,y)==(205.74,322.58):replace(n,'','Separate switched-bias returns')
    for ref,net in [('#PWR081','CLAMP_START'),('#PWR082','CLAMP_RESET'),('#PWR083','CLAMP_PWDN')]:
        n=ss[ref];x,y=one(n,'at')[1:3]
        replace(n,label(net,x,y,'bias.'+ref),'Connect individual existing10k bias to active clamp, not fixed ground')
    for n in all_(root,'global_label'):
        if n[1]=='AGND' and one(n,'at')[1:3]==['180.34','322.58']:
            replace(n,label('CLAMP_MOSI',180.34,322.58,'bias.MOSI'),'Switch DIN low bias')
            items.append(label('CLAMP_SCLK',205.74,322.58,'bias.SCLK'))
    gpio4=old.pin_positions(root,'U3')['4']['xy']
    for n in all_(root,'no_connect'):
        xy=list(map(float,one(n,'at')[1:3]));x,y=xy
        if (70<=x<=167 and 255<=y<=340) or xy==gpio4:
            replace(n,'','Remove old U5 NC, or connect GPIO4 as explicit MCU_READY')
    main_power_refs={'#PWR064','#PWR076'}
    for ref,n in ss.items():
        if ref in removed_refs:continue
        if props(n).get('Value')=='+3.3V' and ref.startswith('#'):
            p=next(z for z in all_(n,'property') if z[1]=='Value');new='MAIN_3V3' if ref in main_power_refs else 'AFE_2V98'
            replace(p,source[p.start:p.end].replace(q('+3.3V'),q(new),1),'Assign existing supply symbol to '+new)
    for n in all_(root,'global_label'):
        if n[1]=='+3.3V':
            x,y=map(float,one(n,'at')[1:3]);new='MAIN_3V3' if x>470 else 'AFE_2V98'
            replace(n,source[n.start:n.end].replace(q('+3.3V'),q(new),1),'Assign existing supply label to '+new)
    rename_mcu={'MOSI':'MCU_MOSI','SCLK':'MCU_SCLK','START':'MCU_START','RESET':'MCU_RESET','PWDN':'MCU_PWDN','CS_ADC1':'MCU_CS1','CS_ADC2':'MCU_CS2','DRDY_ADC1':'MCU_DRDY'}
    for n in all_(root,'label'):
        x,y=map(float,one(n,'at')[1:3]);name=n[1]
        if name in ('EN','LP2985_OUT_DISABLED'):
            replace(n,'','Remove obsolete regulator label');continue
        if x>560 and y<100 and name in rename_mcu:
            replace(n,source[n.start:n.end].replace(q(name),q(rename_mcu[name]),1),'Separate MCU control side from receiver-powered buffer')
        elif name=='MISO' and x<470:
            new='DOUT_ADC1' if x<300 else 'DOUT_ADC2'
            replace(n,source[n.start:n.end].replace(q(name),q(new),1),'Separate DOUT source before shared-MISO tri-state isolation')
    for n in all_(root,'text_box'):
        if n[1].strip() in ['MCU LDO Configuration','ADC LDO Configuration']:replace(n,'','Remove obsolete LDO box')
    for n in all_(root,'text'):
        if n[1].startswith('F04: U4 output isolated'):
            replace(n,'','Remove superseded isolated-LDO annotation')
        elif n[1].startswith('V1.2 PARTIAL CORRECTIONS'):
            new='V1.3 POWER IMPLEMENTED IN SCHEMATIC - BENCH QUALIFICATION REQUIRED\nMAIN 3.3V for stock DevKit; independent4.0V PRE -> quiet2.98V AVDD+DVDD.\nBattery-only while seated: both USB sockets physically blocked; unplug pack/unseat U3 for USB service.\nGPIO4 READY + power monitors isolate ADC controls/DOUT during reset or rail faults.\nF06/F18: initialize U1/CLK_EN then U2; enable/settle2.4V references before common START.\nF07/F08: protected body bias and wearer fault-current protection remain open.'
            replace(n,source[n.start:n.end].replace(q(n[1]),q(new),1),'Replace obsolete power summary with current architecture and limits')
        elif n[1].startswith('V1.2 F09:'):
            new='V1.3 F09: receiver-side DIN/SCLK/START/RESET/PWDN pulldowns retained; CS pulldowns added.\nOld U4/U5/R38 removed after candidate rail/control validation. New EN has defined UVLO and inhibit link.\nNo mounted USB mode: mechanical connector exclusion is required, not electrical USB hotplug protection.'
            replace(n,source[n.start:n.end].replace(q(n[1]),q(new),1),'Replace stale R38 note')
        elif n[1].startswith('V1.2 F12/F14'):
            new=n[1].replace('V1.2','V1.3').replace('C55 BP: 10nF unchanged; leakage <100nA at operating bias/temperature.','C55/BP obsolete regulator removed; qualify new SET leakage/microphonics.').replace('No MPN, footprint, physical performance or wearer-safety qualification is implied.','New MPNs are schematic selections; effective C, footprints/layout and physical tests remain required.')
            replace(n,source[n.start:n.end].replace(q(n[1]),q(new),1),'Retain input passive requirements; remove obsolete BP requirement')
    # Preserve the original DevKit functional symbol and all its existing pin UUIDs.
    n=ss['U3'];x,y=one(n,'at')[1:3]
    extra={'MPN':'ESP32-S3-DevKitC-1-N8R2','Board requirement':'Genuine Espressif Rev1.1 matching official 20221130 schematic; verify actual assembly before power',
           'Power modes':'External nominal3.3V via pins1/2 only while seated. Both USB ports physically inaccessible. Unplug pack and unseat for USB service.'}
    patches.append((n.end-1,n.end-1,'\n'+'\n'.join(property_(k,v,x,y) for k,v in extra.items())+'\n'))
    for ref in ['R33','R34','R35','R36','R37']:
        n=ss[ref];x,y=one(n,'at')[1:3];fields=props(n)
        pp=next(z for z in all_(n,'property') if z[1]=='Footprint')
        replace(pp,source[pp.start:pp.end].replace(q(pp[2]),q('Resistor_SMD:R_0603_1608Metric'),1),'Specify switched-bias resistor footprint')
        add={'MPN':'CRCW060310K0FKEA','Manufacturer':'Vishay'}
        if 'Tolerance' not in fields:add['Tolerance']='1%'
        patches.append((n.end-1,n.end-1,'\n'+'\n'.join(property_(k,v,x,y) for k,v in add.items())+'\n'))
    n=ss['TP4'];v=next(z for z in all_(n,'property') if z[1]=='Value');replace(v,source[v.start:v.end].replace(q(v[2]),q('MAIN_3V3'),1),'Identify main test rail')
    # C57 is now a specified polarized bulk part on MAIN, retaining its pin polarity.
    n=ss['C57'];bulk=block_records['input']['bulk_c57_recommendation']
    li=one(n,'lib_id');replace(li,'(lib_id "Device:C_Polarized")','Show selected bulk capacitor polarity explicitly')
    defs['Device:C_Polarized']=module('power_library_source',OUT/'build_power_blocks.py').installed('Device:C_Polarized')
    for pname,new in [('Value',bulk['value']),('Footprint',bulk['footprint_candidate']),('Datasheet',bulk['source'])]:
        pp=next(z for z in all_(n,'property') if z[1]==pname)
        replace(pp,source[pp.start:pp.end].replace(q(pp[2]),q(new),1),'Select specified MAIN bulk capacitor: '+pname)
    x,y=one(n,'at')[1:3]
    fields={'MPN':bulk['mpn'],'Manufacturer':bulk['manufacturer'],'Voltage rating':bulk['voltage'],'Tolerance':bulk['tolerance'],
            'ESR':bulk['esr'],'Qualification':bulk['qualification']+' Pin1 positive; pin2 negative. No wearer qualification.'}
    patches.append((n.end-1,n.end-1,'\n'+'\n'.join(property_(k,v,x,y) for k,v in fields.items())+'\n'))
    # Block generators use local net names; power names shared with original global power symbols must be global.
    extra_text='\n'.join(items)
    pr=parse('(root '+extra_text+')')
    ep=[]
    for n in all_(pr,'label'):
        if n[1] in {'AGND','+3.7V','MAIN_3V3','AFE_2V98','AFE_PRE_4V0','SW_BAT_PROT','MAIN_ENABLE'}:
            ep.append((n.start-6,n.end-6,extra_text[n.start-6:n.end-6].replace('(label ','(global_label ',1).replace('(at ','(shape input) (at ',1)))
    extra_text=old.apply_edits(extra_text,ep)
    # Keep converter labels outside their symbols, especially closely spaced top pins.
    tmp=parse('(root '+extra_text+')');ep=[];stub_ends={}
    pmod=module('power_geometry',OUT/'build_power_blocks.py')
    regpins=set()
    for n in all_(tmp,'symbol'):
        if props(n).get('Reference') in {'U6','U7','U8'}:
            xx,yy=map(float,one(n,'at')[1:3])
            for _,(px,py,_,_) in pmod.pins(defs[one(n,'lib_id')[1]]).items():regpins.add((round(xx+px,5),round(yy-py,5)))
    for n in all_(tmp,'wire'):
        a,b=[tuple(map(float,z[1:3])) for z in all_(one(n,'pts'),'xy')]
        if a in regpins:stub_ends[b]=a
    for n in all_(tmp,'label')+all_(tmp,'global_label'):
        at=one(n,'at');xy=tuple(map(float,at[1:3]));a=stub_ends.get(xy)
        if a is None:continue
        angle=180 if xy[0]<a[0] else (90 if xy[1]<a[1] else (270 if xy[1]>a[1] else 0))
        start,end=n.start-6,n.end-6;snippet=extra_text[start:end]
        snippet=snippet.replace(extra_text[at.start-6:at.end-6],f'(at {at[1]} {at[2]} {angle})',1)
        if angle==180:snippet=snippet.replace('(justify left bottom)','(justify right bottom)',1)
        ep.append((start,end,snippet))
    # Specify stronger passive defaults without exceeding ADS 500uA output characterization.
    for n in all_(tmp,'symbol'):
        ref=props(n).get('Reference')
        if ref in {'R81','R82','R83','R84'}:
            val=next(z for z in all_(n,'property') if z[1]=='Value')
            ep.append((val.start-6,val.end-6,extra_text[val.start-6:val.end-6].replace(q('100k'),q('10k'),1)))
        if ref in block_records['digital']['components']:
            fields=props(n);target_fields={}
            if ref.startswith('R'):
                value='10k' if ref in {'R81','R82','R83','R84'} else fields['Value']
                part={'10k':'CRCW060310K0FKEA','100k':'CRCW0603100KFKEA','36.0k':'CRCW060336K0FKEA','67.8k':'TNPW060367K8BYTA','59.1k':'TNPW060359K1BYTA','2.2':'CRCW08052R20FKEAHP'}[value]
                if ref in {'R78','R80'}:part='TNPW060310K0BYTA'
                target_fields={'MPN':part,'Manufacturer':'Vishay'}
                if ref=='R86':target_fields['Footprint']='Resistor_SMD:R_0805_2012Metric'
            elif ref.startswith('C'):
                target_fields={'MPN':'GRM188R71C104KA01D','Manufacturer':'Murata','Voltage rating':'16V'}
            for pp in all_(n,'property'):
                if pp[1] in target_fields:
                    ep.append((pp.start-6,pp.end-6,extra_text[pp.start-6:pp.end-6].replace(q(pp[2]),q(target_fields[pp[1]]),1)))
    extra_text=old.apply_edits(extra_text,ep)
    # Additional source-side GPIO wires are in the active root sheet only.
    extra_text+='\n'+wire(562.61,71.12,576.58,71.12,'gpio4.ready.wire')+'\n'+label('MCU_READY',576.58,71.12,'gpio4.ready.label')
    extra_text+='\n'+wire(511.81,43.18,499.11,43.18,'chippu.powergood.wire')+'\n'+label('CHIP_PU',499.11,43.18,'chippu.powergood.label')
    extra_text+='\n'+note('V1.3 RUN: nominal3.3V header supply. NO USB / external5V while seated.\nPOWER_GOOD holds CHIP_PU low until both monitored rails stabilize.\nGPIO4 READY must remain0 until all MCU ADC-side output values are initialized.',600,40,'mcu.mode.note')
    # Independent VCAP3 HF bypasses match ADS1298 Fig106; original 1uF parts remain.
    # The two local AVDD1 banks provide additional nominal bypassing at the charge-pump pins.
    for ref,x,net,purpose in [('C110',50.8,'VCAP3_ADC1','U1.55 to AVSS; parallel existing C25'),('C111',101.6,'VCAP3_ADC2','U2.55 to AVSS; parallel existing C51'),
                              ('C114',254.0,'AFE_2V98','Place at U1.54 AVDD1 / U1.53 AVSS1'),('C115',304.8,'AFE_2V98','Place at U2.54 AVDD1 / U2.53 AVSS1')]:
        y=688.34
        extra_text+=f'''\n(symbol (lib_id "Device:C") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid(ref))})
        (property "Reference" "{ref}" (at {x+3.81} {y-2.54} 0) (effects (font (size 1 1)) (justify left)))
        (property "Value" "100nF 50V C0G" (at {x+3.81} {y} 0) (effects (font (size 1 1)) (justify left)))
        {property_('Footprint','Capacitor_SMD:C_1206_3216Metric',x,y)}
        {property_('MPN','GRM31C5C1H104JA01L',x,y)} {property_('Voltage rating','50V',x,y)} {property_('Tolerance','5%',x,y)}
        {property_('Datasheet','https://www.murata.com/en-us/products/productdetail?partno=GRM31C5C1H104JA01L',x,y)}
        {property_('Purpose',purpose+'; TI ADS1298 Figure106; placement and qualification required',x,y)}
        (pin "1" (uuid {q(uid(ref+'.pin1'))})) (pin "2" (uuid {q(uid(ref+'.pin2'))}))
        (instances (project "open-semg-16-v1.3" (path {q('/'+root_id)} (reference "{ref}") (unit 1)))))'''
        extra_text+='\n'+wire(x,y-3.81,x,y-8.89,ref+'.top')+'\n'+label(net,x,y-8.89,ref+'.net',net=='AFE_2V98')
        extra_text+='\n'+wire(x,y+3.81,x,y+8.89,ref+'.bottom')+'\n'+label('AGND',x,y+8.89,ref+'.ground',True)
    for ref,x,source_ref,purpose in [('C112',152.4,'C64','Place next to U1.54 AVDD1 / U1.53 AVSS1; effective C >=1uF'),('C113',203.2,'C64','Place next to U2.54 AVDD1 / U2.53 AVSS1; effective C >=1uF')]:
        # Reuse the specified 10uF/16V part from the qualified candidate class.
        y=688.34
        extra_text+=f'''\n(symbol (lib_id "Device:C") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid(ref))})
        (property "Reference" "{ref}" (at {x+3.81} {y-2.54} 0) (effects (font (size 1 1)) (justify left)))
        (property "Value" "10u 16V" (at {x+3.81} {y} 0) (effects (font (size 1 1)) (justify left)))
        {property_('Footprint','Capacitor_SMD:C_0805_2012Metric',x,y)} {property_('MPN','GRM21BR61C106KE15L',x,y)}
        {property_('Qualification',purpose+'; verify effective C at3.05V before assembly',x,y)}
        (pin "1" (uuid {q(uid(ref+'.pin1'))})) (pin "2" (uuid {q(uid(ref+'.pin2'))}))
        (instances (project "open-semg-16-v1.3" (path {q('/'+root_id)} (reference "{ref}") (unit 1)))))'''
        extra_text+='\n'+wire(x,y-3.81,x,y-8.89,ref+'.top')+'\n'+label('AFE_2V98',x,y-8.89,ref+'.net',True)
        extra_text+='\n'+wire(x,y+3.81,x,y+8.89,ref+'.bottom')+'\n'+label('AGND',x,y+8.89,ref+'.ground',True)
    extra_text+='\n'+note('Local ADC bypass parts: place C112/C114 at U1 AVDD1/AVSS1 and C113/C115 at U2.\nC110/C111 add100nF at VCAP3 in parallel with retained1uF. C57 is polarized220uF MAIN bulk.\nPhysical placement, effective capacitance and startup/noise remain PCB/bench release gates.',50.8,710,'new.bypass.note')
    # Append only libraries not already embedded; preserve original cached definitions byte-for-byte.
    cached=one(root,'lib_symbols');existing={n[1] for n in all_(cached,'symbol')}
    new_defs={k:v for k,v in defs.items() if k not in existing}
    patches.append((cached.end-1,cached.end-1,'\n'+'\n'.join(new_defs.values())+'\n'))
    paper=one(root,'paper');replace(paper,'(paper "A0")','Expand sheet for explicit new power/interface blocks; original channels stay in place')
    title=one(root,'title_block');c=next(z for z in all_(title,'comment') if z[1]=='1');replace(c,'(comment 1 "Version 1.3 - power implementation; bench qualification pending")','Update revision title')
    patches.append((root.end-1,root.end-1,'\n'+extra_text+'\n'))
    candidate=old.apply_edits(source,patches)
    rr=parse(candidate,'kicad_sch');assert len(symbols(rr))==len(all_(rr,'symbol')),'Duplicate references'
    ids=re.findall(r'\(uuid\s+"([^"]+)"\)',candidate);assert len(ids)==len(set(ids)),'Duplicate UUIDs'
    target=OUT/'power-candidate.kicad_sch';target.write_text(candidate)
    (OUT/'edit-plan.json').write_text(json.dumps({'target':str(SCH),'changes':changes,'removed_references':sorted(removed_refs),'source_hash':hashlib.sha256(source.encode()).hexdigest(),'candidate_hash':hashlib.sha256(candidate.encode()).hexdigest()},indent=2)+'\n')
    # Local libraries for verified custom definitions. Existing historical/global libraries are never edited.
    local_libraries={}
    for key,val in new_defs.items():
        lib,name=key.split(':',1)
        if lib.startswith('V13_') or lib=='Power_Impl':
            local_libraries.setdefault(lib,[]).append(val.replace('(symbol '+q(key),'(symbol '+q(name),1))
    for lib,entries in local_libraries.items():
        (OUT/(lib+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(entries)+'\n)\n')
    table=(OUT/'before-sym-lib-table').read_text() if (OUT/'before-sym-lib-table').exists() else (ACTIVE/'sym-lib-table').read_text();tr=parse(table)
    additions=[f'(lib (name {q(lib)}) (type "KiCad") (uri {q("${KIPRJMOD}/"+lib+".kicad_sym")}) (options "") (descr "V1.3 candidate custom symbols"))' for lib in local_libraries]
    (OUT/'sym-lib-table').write_text(table[:tr.end-1]+'\n'+'\n'.join(additions)+'\n'+table[tr.end-1:])
    (OUT/'power-candidate.kicad_pro').write_bytes((ACTIVE/'open-semg-16-v1.3.kicad_pro').read_bytes())
    (OUT/'candidate-metadata.json').write_text(json.dumps({'local_libraries':list(local_libraries),'new_definitions':list(new_defs),'candidate_only':True},indent=2)+'\n')
    print('Candidate created:',target)

def commit():
    allowed=[BASE.read_bytes()]
    if (OUT/'before-bias-refinement.kicad_sch').exists():allowed.append((OUT/'before-bias-refinement.kicad_sch').read_bytes())
    assert SCH.read_bytes() in allowed,'Source changed after saved checkpoints'
    verification=json.loads((OUT/'candidate-verification.json').read_text());assert verification['passed'],verification
    candidate=(OUT/'power-candidate.kicad_sch').read_text();parse(candidate,'kicad_sch')
    md=json.loads((OUT/'candidate-metadata.json').read_text())
    table_path=ACTIVE/'sym-lib-table';table=(OUT/'before-sym-lib-table').read_text() if (OUT/'before-sym-lib-table').exists() else table_path.read_text();tr=parse(table)
    added=[]
    for lib in md['local_libraries']:
        name=lib+'.kicad_sym';data=(OUT/name).read_bytes();(ACTIVE/name).write_bytes(data)
        added.append(f'(lib (name {q(lib)}) (type "KiCad") (uri {q("${KIPRJMOD}/"+name)}) (options "") (descr "V1.3 verified local power/control symbols"))')
    (OUT/'before-sym-lib-table').write_text(table)
    newtable=table[:tr.end-1]+'\n'+'\n'.join(added)+'\n'+table[tr.end-1:];parse(newtable)
    table_path.write_text(newtable)
    temporary=SCH.with_suffix('.kicad_sch.tmp');temporary.write_text(candidate);temporary.replace(SCH)
    (OUT/'commit.json').write_text(json.dumps({'method':'bounded source spans; saved baseline; native candidate export/ERC; explicit pin/net assertions; atomic active schematic replace','target':str(SCH),'candidate_verification':verification,'new_libraries':md['local_libraries']},indent=2)+'\n')
    print('Committed verified candidate to',SCH)

if __name__=='__main__':
    {'candidate':create_candidate,'commit':commit}[sys.argv[1]]()
