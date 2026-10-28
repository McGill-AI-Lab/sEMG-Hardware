"""Bounded V1.2 schematic edits, preserving untouched source spans.

Only the V1.2 schematic is a design-write target. Candidate files, backups and
operation evidence stay beside this script. No shared libraries are modified.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import sys
import uuid

OUT=Path(__file__).resolve().parent
ACTIVE=OUT.parents[2]/'v1.2'
SCH=ACTIVE/'open-semg-16-v1.2.kicad_sch'
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym')
NC_PINS=[8,9,36,37,38,39,43,42,26,25,31,41,40,4,5,10,11,27,32,33,34,35,30,14,28,29]
SHORT_WIRES=['e8554e5f-764e-4ed9-b3b5-af17444eaea4','a1d6f88d-0e8a-413e-a213-337d5f4dfb8c',
'b9ec5222-9de5-4232-ac72-616ed32d16fa','fed4f893-2155-4132-a14d-83d66da5026f',
'd5e72200-7740-47f6-bcd1-166d3890ab1a','13c6d5b3-2529-4363-adf9-c4bf92ed6b75',
'7629d020-a15b-4a11-a0da-525dc621807c','1944fad2-2fdc-4b3d-bc63-86c9cadeb58c',
'921c1c3f-7201-4f7d-b96d-27f51fc32b80','8928b8b2-a15b-4448-9ee8-2288aad4981d',
'9bb1d07d-9b6b-4b89-b88f-7bd033c17f63','d7e9643c-0720-4f66-9307-e79118aac293',
'7ecfa58c-ad63-49c8-a47a-781baca645b6','b6acd6a4-9497-49d0-8aa5-178ccdce006e',
'a88e4c81-bd1e-4997-b072-fb203d08f059','b8457160-69b9-41fc-8320-2b8cf245d5cd',
'917266e2-ea46-48be-8937-e23d14e2e70e','b88d0700-d107-4800-a4a8-d3b91c190de7']
CS_WIRE='34341901-2092-4668-89af-eb552c157d44'
AVDD_LABELS=['066ca9c8-7bd4-4f0b-92e4-56350bd7253c','3589528b-9c95-40c8-a912-f86516f6c24c',
'792ff479-7cd1-49c0-b4af-14b86c12e8f8','bd298a1f-5ec1-4f2d-a055-09b58728a7c2']
DVDD_LABELS=['3be50cba-7e40-47bb-8d96-339bceed5caa','75fc8b9d-1b77-49f1-bb82-13b6eff87138',
'96726343-f5a2-426c-a935-6769c922104b','a495d871-c532-473d-aa7f-0b108779b50c']


class Node(list): pass


def parse(source, expected=None):
    stack=[];roots=[]
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',source):
        token=m.group()
        if token=='(':
            n=Node();n.start=m.start();stack.append(n)
        elif token==')':
            assert stack,'unbalanced close'
            n=stack.pop();n.end=m.end()
            (stack[-1] if stack else roots).append(n)
        else:
            assert stack,'atom outside root'
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and len(roots)==1
    assert expected is None or roots[0][0]==expected
    return roots[0]


def all_(n,key):return [c for c in n if isinstance(c,list) and c and c[0]==key]
def one(n,key):return next(iter(all_(n,key)),None)
def props(n):return {p[1]:p[2] for p in all_(n,'property')}
def symbols(r):return {props(n)['Reference']:n for n in all_(r,'symbol')}
def id_(n):return one(n,'uuid')[1]
def q(s):return json.dumps(str(s),ensure_ascii=False)
def uid():return str(uuid.uuid4())
def digest(s):return hashlib.sha256(s.encode()).hexdigest()


def pin_positions(root,ref):
    inst=symbols(root)[ref];x,y,angle=map(float,one(inst,'at')[1:]);theta=math.radians(angle)
    assert one(inst,'mirror') is None,'unsupported mirrored instance'
    lib=next(n for n in all_(one(root,'lib_symbols'),'symbol') if n[1]==one(inst,'lib_id')[1])
    unit=one(inst,'unit')[1];positions={}
    for group in all_(lib,'symbol'):
        if group[1].split('_')[-2] not in ('0',unit):continue
        for p in all_(group,'pin'):
            px,py=map(float,one(p,'at')[1:3]);num=one(p,'number')[1]
            instance_pin=next(i for i in all_(inst,'pin') if i[1]==num)
            positions[num]={'name':one(p,'name')[1],'type':p[1],
                'xy':[round(x+px*math.cos(theta)-py*math.sin(theta),5),round(y-py*math.cos(theta)-px*math.sin(theta),5)],
                'pin_uuid':id_(instance_pin)}
    return positions


def replace_atom(source,node,key,new):
    old=source[node.start:node.end]
    old_atom=q(node[2]);assert old.count(old_atom)>=1
    return old.replace(old_atom,q(new),1)


def note_replace(source,n,text):
    old=source[n.start:n.end]
    assert q(n[1]) in old
    return old.replace(q(n[1]),q(text),1)


def apply_edits(source,patches):
    end=len(source)+1
    for start,stop,text in sorted(patches,reverse=True):
        assert 0<=start<=stop<=end,'overlapping source patches'
        source=source[:start]+text+source[stop:];end=start
    return source


def commit(source,updated,phase,changes):
    assert SCH.resolve().parent==ACTIVE.resolve() and SCH.read_text()==source
    root=parse(updated,'kicad_sch');ss=symbols(root)
    assert len(ss)==len(all_(root,'symbol')),'duplicate reference'
    ids=re.findall(r'\(uuid\s+"([^"]+)"\)',updated)
    assert len(ids)==len(set(ids)),'duplicate UUID'
    (OUT/f'before-{phase}.kicad_sch').write_text(source)
    candidate=OUT/f'{phase}-candidate.kicad_sch';candidate.write_text(updated)
    command=[CLI,'sch','export','netlist','--format','kicadxml','--output',str(OUT/f'{phase}-candidate-netlist.xml'),str(candidate)]
    result=subprocess.run(command,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    # Require the deliberate F04 partition before replacing the active design.
    import xml.etree.ElementTree as ET
    tree=ET.parse(OUT/f'{phase}-candidate-netlist.xml').getroot()
    nets={n.get('name'):{(p.get('ref'),p.get('pin')) for p in n.findall('node')} for n in tree.findall('./nets/net')}
    assert nets['/LP2985_OUT_DISABLED']=={('U4','5'),('C54','1')}
    assert ('U5','5') in nets['+3.3V'] and ('U4','5') not in nets['+3.3V']
    temp=SCH.with_suffix('.kicad_sch.tmp');temp.write_text(updated);temp.replace(SCH)
    (OUT/f'{phase}-edit-log.json').write_text(json.dumps({'phase':phase,
        'target':str(SCH),'method':'controlled KiCad-aware source-span edits; strict parse, unique UUID/reference checks, native candidate netlist validation, atomic replace',
        'before_sha256':digest(source),'after_sha256':digest(updated),'changes':changes,
        'candidate_cli':{'argv':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}},indent=2)+'\n')


def power():
    source=SCH.read_text();r=parse(source,'kicad_sch');ss=symbols(r);n=ss['#PWR069']
    assert props(n)['Value']=='+3.3V' and id_(n)=='899e2864-2071-420a-97ee-909270af09ae'
    new_id=uid()
    label=f'(label "LP2985_OUT_DISABLED" (at 147.32 269.24 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "{new_id}"))'
    patches=[(n.start,n.end,label)]
    changes=[{'finding':'F04','removed_global_supply_symbol':'#PWR069','removed_symbol_uuid':id_(n),
              'added_local_label_uuid':new_id,'at_mm':[147.32,269.24],
              'before':'U4.5 and C54.1 directly on common +3.3V',
              'after':'U4.5 and C54.1 alone on /LP2985_OUT_DISABLED; U5.5 remains on main +3.3V; both EN held OFF by unchanged R38',
              'consequence':'main nominal C 242.6→240.4uF; local C54 remains2.2uF; no operating-source or stability qualification'}]
    for n in all_(r,'text'):
        if n[1].startswith('V1.2 PARTIAL CORRECTIONS'):
            text=n[1].replace('F04: LDO outputs remain parallel. F05: fitted R38 holds EN low; power architecture unresolved.',
                'F04: U4/C54 isolated from main rail. F05: R38 holds both LDOs OFF; operating power unqualified.')
            assert text!=n[1];patches.append((n.start,n.end,note_replace(source,n,text)))
            changes.append({'finding':'F04/F05','annotation_uuid':id_(n),'change':'replace stale parallel-output statement with actual isolated/development-OFF state'})
        if 'Do not remove R38 or drive EN until F04/F13/F15/F16/F17 are resolved.' in n[1]:
            text=n[1].replace('Do not remove R38 or drive EN until F04/F13/F15/F16/F17 are resolved.',
                'Keep R38 fitted until functional EN, F13/F15/F16/F17 qualification is complete.')
            patches.append((n.start,n.end,note_replace(source,n,text)))
            changes.append({'finding':'F04/F05','annotation_uuid':id_(n),'change':'retain OFF inhibit; remove obsolete open-F04 wording'})
    added_note=f'(text {q("F04: U4 output isolated with C54; no system load.\nBoth LDOs remain OFF. Qualify LP silicon/C54 before enable.")} (at 75 287.02 0) (effects (font (size 1.27 1.27)) (justify left top)) (uuid "{uid()}"))'
    patches.append((r.end-1,r.end-1,'\n'+added_note+'\n'))
    changes.append({'finding':'F04/F13','change':'add local isolated-output/qualification annotation','at_mm':[75,287.02]})
    commit(source,apply_edits(source,patches),'power',changes)


def unused():
    source=SCH.read_text();r=parse(source,'kicad_sch');positions=pin_positions(r,'U3')
    old_points={tuple(map(float,one(n,'at')[1:3])) for n in all_(r,'no_connect')}
    extra=[];changes=[]
    plan=json.loads((OUT/'modification-plan.json').read_text())
    assert plan['gpio3_efuse_status']=='Unknown / needs checking' and 13 not in NC_PINS
    for num in NC_PINS:
        p=positions[str(num)];x,y=p['xy'];assert (x,y) not in old_points
        marker_id=uid();extra.append(f'(no_connect (at {x} {y}) (uuid "{marker_id}"))')
        decision=next(d for d in plan['unused_pin_decisions'] if d['pin']==num)
        assert decision['approved']
        changes.append({'finding':'F19','reference':'U3','pin':num,**p,'marker_uuid':marker_id,
                        'verification':decision['verification'],'sources':decision['sources'],
                        'meaning':'unused external carrier terminal; no change to DevKit internal circuits or MCU firmware'})
    commit(source,source[:r.end-1]+'\n'+'\n'.join(extra)+'\n'+source[r.end-1:],'unused',changes)


def cleanup():
    source=SCH.read_text();r=parse(source,'kicad_sch');patches=[];changes=[]
    wires={id_(n):n for n in all_(r,'wire')}
    for u in SHORT_WIRES:
        n=wires[u];xy=[list(map(float,p[1:3])) for p in all_(one(n,'pts'),'xy')]
        assert math.isclose(math.dist(*xy),1.27,abs_tol=1e-6)
        patches.append((n.start,n.end,''));changes.append({'finding':'F19; preserve F07/F09/F12/F18','operation':'remove redundant tail','wire_uuid':u,'endpoints_mm':xy,'length_mm':1.27})
    n=wires[CS_WIRE];xy=all_(one(n,'pts'),'xy');assert xy[0][1:]==['562.61','96.52'] and xy[1][1:]==['576.58','96.52']
    endpoint=xy[1];patches.append((endpoint.start,endpoint.end,'(xy 568.96 96.52)'))
    changes.append({'finding':'F09/F19','operation':'trim only excess CS_ADC2 tail','wire_uuid':CS_WIRE,'before':[[562.61,96.52],[576.58,96.52]],'after':[[562.61,96.52],[568.96,96.52]],'retained_label_uuid':'f775580c-f47c-4bc7-a9f8-15143a81985e'})
    labels={id_(n):n for n in all_(r,'label')}
    for u in AVDD_LABELS+DVDD_LABELS:
        n=labels[u];assert n[1] in ('AVDD','DVDD');at=one(n,'at')[1:]
        justification='right' if float(at[2])==180 else 'left';size='1.27'
        if u=='75fc8b9d-1b77-49f1-bb82-13b6eff87138':at=[*at[:2],'0'];justification='left';size='1.0'
        replacement=f'(global_label "+3.3V" (shape input) (at {" ".join(at)}) (effects (font (size {size} {size})) (justify {justification})) (uuid "{u}"))'
        patches.append((n.start,n.end,replacement));changes.append({'finding':'F19; preserve F01/F02/F03','operation':f'replace local {n[1]} alias with global +3.3V on same node','uuid':u,'at_mm':at})
    ground_instances=[]
    for ref,n in symbols(r).items():
        if one(n,'lib_id')[1]=='power:GND' and props(n)['Value']=='GND':
            p=next(p for p in all_(n,'property') if p[1]=='Value')
            patches.append((p.start,p.end,replace_atom(source,p,'Value','AGND')))
            ground_instances.append(ref)
            changes.append({'finding':'F02/F19','operation':'normalize existing GND instance value to common AGND','reference':ref,'symbol_uuid':id_(n),'at_mm':one(n,'at')[1:],'pin_type':'power input unchanged'})
    assert len(ground_instances)==43
    lib_source=LIB.read_text();library=parse(lib_source,'kicad_symbol_lib')
    installed=next(n for n in all_(library,'symbol') if n[1]=='Battery')
    cached=next(n for n in all_(one(r,'lib_symbols'),'symbol') if n[1]=='Device:Battery')
    fields=[p for p in all_(installed,'property') if p[1].startswith('Sim.')]
    assert {p[1]:p[2] for p in fields}=={'Sim.Device':'V','Sim.Type':'DC','Sim.Pins':'1=+ 2=-'}
    expected=list(installed);expected[1]='Device:Battery'
    without=[p for p in expected if not (isinstance(p,list) and p and p[0]=='property' and p[1].startswith('Sim.'))]
    assert list(cached)==without,'unexpected installed Battery difference'
    # Preserve installed-library property order: simulation metadata precedes
    # ki_keywords. The strict structural check also verifies this ordering.
    insertion=next(p for p in all_(cached,'property') if p[1]=='ki_keywords').start
    patches.append((insertion,insertion,'\n'+'\n'.join(lib_source[p.start:p.end] for p in fields)+'\n'))
    changes.append({'finding':'F19','operation':'reconcile embedded Device:Battery cache with installed simulation metadata only','source':str(LIB),'added_fields':{p[1]:p[2] for p in fields},'pins_and_geometry':'unchanged','BT1_instance':'unchanged'})
    updated=apply_edits(source,patches)
    rr=parse(updated,'kicad_sch');now=next(n for n in all_(one(rr,'lib_symbols'),'symbol') if n[1]=='Device:Battery')
    assert list(now)==expected,'cache reconciliation failed'
    commit(source,updated,'cleanup',changes)


def remaining_supply_aliases():
    """Complete the DVDD alias revealed by the first native cleanup ERC run."""
    source=SCH.read_text();r=parse(source,'kicad_sch');patches=[];changes=[]
    labels={id_(n):n for n in all_(r,'label')}
    for u in DVDD_LABELS:
        n=labels[u];assert n[1]=='DVDD';at=one(n,'at')[1:]
        justification='right' if float(at[2])==180 else 'left';size='1.27'
        if u=='75fc8b9d-1b77-49f1-bb82-13b6eff87138':at=[*at[:2],'0'];justification='left';size='1.0'
        replacement=f'(global_label "+3.3V" (shape input) (at {" ".join(at)}) (effects (font (size {size} {size})) (justify {justification})) (uuid "{u}"))'
        patches.append((n.start,n.end,replacement))
        changes.append({'finding':'F19; preserve F02','operation':'normalize additional DVDD alias on same common +3.3V rail','uuid':u,'at_mm':at,'reason':'initial alias diagnostic reported AVDD only; after AVDD consolidation native ERC exposed remaining DVDD name'})
    commit(source,apply_edits(source,patches),'supply-alias-completion',changes)


def label_presentation():
    source=SCH.read_text();r=parse(source,'kicad_sch');u='75fc8b9d-1b77-49f1-bb82-13b6eff87138'
    n=next(n for n in all_(r,'global_label') if id_(n)==u)
    assert one(n,'at')[1:3]==['209.55','160.02']
    text=f'(global_label "+3.3V" (shape input) (at 209.55 160.02 0) (effects (font (size 1.0 1.0)) (justify left)) (uuid "{u}"))'
    commit(source,apply_edits(source,[(n.start,n.end,text)]),'label-presentation',
        [{'finding':'F19','operation':'rotate compact CLKSEL supply-label presentation away from START text; attachment and net unchanged','uuid':u,'anchor_mm':[209.55,160.02],'angle_before':180,'angle_after':0,'font_mm':1.0}])


if __name__=='__main__':{'power':power,'unused':unused,'cleanup':cleanup,'supply-alias-completion':remaining_supply_aliases,'label-presentation':label_presentation}[sys.argv[1]]()
