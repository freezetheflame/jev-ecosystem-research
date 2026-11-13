
import json, os, collections
ROOT=r"D:\projects\jev_research"
RUN=os.path.join(ROOT,"data","agent-security-study","runs","full-api-jev-packy-v1","jev","tsbench")
cases=[json.loads(l) for l in open(os.path.join(RUN,"cases.jsonl"),encoding="utf-8") if l.strip()]
print("total steps:",len(cases))
print("source_segment_id examples:", [c.get("source_segment_id") for c in cases[:3]])
def group_key(c):
    return (c.get("source_file"), c.get("source_row_index"))
g=collections.defaultdict(list)
for c in cases: g[group_key(c)].append(c)
print("groups by (file,row):",len(g))
def parse_step(c):
    parts=c["item_id"].rsplit(":",3)
    try: return int(parts[1])
    except: return None
sizes=collections.Counter(len(v) for v in g.values())
print("group size distribution:", sorted(sizes.items())[:12])
# per source file: groups, multi-step groups, groups with unsafe among size>=2
byfile=collections.defaultdict(lambda: dict(groups=0,multi=0,multi_unsafe=0,multi_safe_only=0,steps=0,unsafe_steps=0))
for (f,row),rows in g.items():
    d=byfile[os.path.basename(f)]
    d["groups"]+=1; d["steps"]+=len(rows)
    d["unsafe_steps"]+=sum(1 for c in rows if c.get("gold")==1)
    if len(rows)>=2:
        d["multi"]+=1
        if any(c.get("gold")==1 for c in rows): d["multi_unsafe"]+=1
        elif all(c.get("gold")==0 for c in rows): d["multi_safe_only"]+=1
print("\nfile | groups | multi(>=2) | multi+unsafe | multi+safe-only | steps | unsafe-steps")
for f,d in sorted(byfile.items(), key=lambda x:-x[1]["groups"]):
    print(f"{f:28s} {d['groups']:6d} {d['multi']:6d} {d['multi_unsafe']:6d} {d['multi_safe_only']:6d} {d['steps']:6d} {d['unsafe_steps']:6d}")
# check step index contiguity within multi groups
multi=[(k,v) for k,v in g.items() if len(v)>=2]
print("\nmulti groups:",len(multi))
contig=0
for k,rows in multi[:2000]:
    idx=sorted(x for x in (parse_step(c) for c in rows) if x is not None)
    if idx==list(range(min(idx),min(idx)+len(idx))): contig+=1
print("contiguous step indices (sampled):",contig,"/",min(2000,len(multi)))
# example group
k,rows=max(multi,key=lambda kv:len(kv[1]))
print("\nexample largest group:",os.path.basename(k[0]),"row",k[1],"steps",len(rows))
for c in sorted(rows,key=parse_step):
    print(" step",parse_step(c),"gold",c.get("gold"),"| action:",str(c["view"].get("candidate_action",""))[:90].replace("\n"," "))
