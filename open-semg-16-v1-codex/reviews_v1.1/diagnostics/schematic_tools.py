"""Read KiCad S-expressions with source spans; explicit V2-only edits are applied separately."""
import json,re,math
from pathlib import Path
class Node(list):
    pass

def read(path):
    source=Path(path).read_text();stack=[]
    for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',source):
        t=m.group()
        if t=='(':
            n=Node();n.start=m.start();stack.append(n)
        elif t==')':
            n=stack.pop();n.end=m.end()
            if stack:stack[-1].append(n)
            else:root=n
        else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
    return source,root

def all_(node,key):return [x for x in node if isinstance(x,list) and x and x[0]==key]
def one(node,key):return next(iter(all_(node,key)),None)
def props(node):return {x[1]:x[2] for x in all_(node,'property')}
def symbols(root):return {props(s)['Reference']:s for s in all_(root,'symbol')}
def pin_positions(root,ref):
    inst=symbols(root)[ref];at=one(inst,'at');x,y,ang=map(float,at[1:]);libid=one(inst,'lib_id')[1];unit=one(inst,'unit')[1]
    lib=next(s for s in all_(one(root,'lib_symbols'),'symbol') if s[1]==libid)
    out={}
    for group in all_(lib,'symbol'):
        if group[1].split('_')[-2] not in ('0',unit):continue
        for p in all_(group,'pin'):
            a=one(p,'at');px,py=map(float,a[1:3]);theta=math.radians(ang)
            out[one(p,'number')[1]]={'name':one(p,'name')[1], 'pos':[round(x+px*math.cos(theta)-py*math.sin(theta),5),round(y-py*math.cos(theta)-px*math.sin(theta),5)],'type':p[1]}
    return out

if __name__=='__main__':
    path='open-semg-16-v2.kicad_sch';s,r=read(path)
    out={'symbols':{ref:{'props':props(n),'at':one(n,'at')[1:]} for ref,n in symbols(r).items()},'pins':{ref:pin_positions(r,ref) for ref in ('U1','U2','U3','U4','U5')}}
    Path('reviews_v2/diagnostics/initial-geometry.json').write_text(json.dumps(out,indent=2))
    for ref in ('U1','U2','U3','U4','U5'):
        print(ref,out['symbols'][ref]['at'])
        print({p:v for p,v in out['pins'][ref].items() if ref not in ('U1','U2') or int(p)>=17})
    print('WIRES/labels NEAR U1 POWER')
    for n in r:
        if isinstance(n,list) and n and n[0] in ('wire','label','global_label','junction','symbol'):
            if n[0]=='wire':pts=all_(one(n,'pts'),'xy');xy=[list(map(float,a[1:])) for a in pts]
            elif one(n,'at'):xy=[list(map(float,one(n,'at')[1:3]))]
            else:continue
            if any(130<=x<=220 and 75<=y<=105 for x,y in xy):print(s[n.start:n.end][:380].replace('\n',' '))
