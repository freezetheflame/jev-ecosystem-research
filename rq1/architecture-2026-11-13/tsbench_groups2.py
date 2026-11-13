
import json, os, collections
ROOT=r"D:\projects\jev_research"
RUN=os.path.join(ROOT,"data","agent-security-study","runs","full-api-jev-packy-v1","jev","tsbench")
cases=[json.loads(l) for l in open(os.path.join(RUN,"cases.jsonl"),encoding="utf-8") if l.strip()]
def parse(i):
    p=i.rsplit(":",3)
    if len(p)!=4: return None
    f=p[0]; a,b,c=(int(p[1]),int(p[2]),int(p[3]))
    return f,a,b,c
g=collections.defaultdict(list)
for c in cases:
    p=parse(c["item_id"])
    if p: g[(p[0],p[1])].append((p[2],p[3],c))
print("total items:",len(cases),"groups by (file,trajectory A):",len(g))
sizes=collections.Counter(len(v) for v in g.values())
print("group size distribution:", sorted(sizes.items())[:12])
# per file
byfile=collections.defaultdict(lambda: dict(groups=0,multi=0,multi_unsafe=0,multi_safe=0,steps=0,unsafe=0,unk=0))
for (f,a),rows in g.items():
    d=byfile[os.path.basename(f)]; d["groups"]+=1; d["steps"]+=len(rows)
    d["unsafe"]+=sum(1 for _,_,c in rows if c.get("gold")==1)
    d["unk"]+=sum(1 for _,_,c in rows if c.get("gold") is None)
    if len(rows)>=2:
        d["multi"]+=1
        if any(c.get("gold")==1 for _,_,c in rows): d["multi_unsafe"]+=1
        elif all(c.get("gold")==0 for _,_,c in rows): d["multi_safe"]+=1
print("\nfile | groups | multi>=2 | multi+unsafe | multi+safe-only | steps | unsafe | unknown")
for f,d in sorted(byfile.items(),key=lambda x:-x[1]["groups"]):
    print(f"{f:26s} {d['groups']:6d} {d['multi']:8d} {d['multi_unsafe']:11d} {d['multi_safe']:13d} {d['steps']:6d} {d['unsafe']:6d} {d['unk']:6d}")
# contiguity of step index B within multi groups
multi=[(k,v) for k,v in g.items() if len(v)>=2]
contig=0; gaps=0; examples=[]
for k,rows in multi:
    idx=sorted(b for b,_,_ in rows)
    if idx==list(range(0,len(idx))): contig+=1
    else: gaps+=1; examples.append((k,idx))
print("\nmulti groups:",len(multi),"contiguous from 0:",contig,"non-contiguous:",gaps)
print("non-contiguous examples:",examples[:5])
# total steps in multi groups
tot=sum(len(v) for _,v in multi)
print("steps in multi groups:",tot,"of",len(cases))
# how many multi_unsafe groups have an unsafe step and are long enough
mu=[(k,v) for k,v in multi if any(c.get("gold")==1 for _,_,c in v)]
print("multi+unsafe groups:",len(mu),"steps:",sum(len(v) for _,v in mu))
# example
k,rows=mu[0]
print("\nexample group:",k)
for b,cidx,c in sorted(rows):
    print(" step",b,"gold",c.get("gold"),"| action:",str(c["view"].get("candidate_action",""))[:100].replace("\n"," "))
