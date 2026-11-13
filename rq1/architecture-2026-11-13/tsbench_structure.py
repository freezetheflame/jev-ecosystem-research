
import json, os, re, collections
ROOT=r"D:\projects\jev_research"
RUN=os.path.join(ROOT,"data","agent-security-study","runs","full-api-jev-packy-v1","jev","tsbench")
cases=[json.loads(l) for l in open(os.path.join(RUN,"cases.jsonl"),encoding="utf-8") if l.strip()]
print("items:",len(cases))
c=cases[0]
print("keys:", list(c.keys()))
print("sample item_id:", c["item_id"])
print("source_file:", c.get("source_file"))
print("source_split:", c.get("source_split"), "native_steps:", c.get("native_steps"), "gold:", c.get("gold"))
# group by source_file
g=collections.Counter(c.get("source_file") for c in cases)
print("\nunique source_file:",len(g))
print("top groups:", g.most_common(10))
# steps per group: parse item_id tail
def tail(i):
    parts=i.split(":")
    return parts[-4:]
print("\nexample tails:", [tail(c["item_id"]) for c in cases[:5]])
# For a few groups, list step numbers
for f,count in g.most_common(3):
    rows=[c for c in cases if c.get("source_file")==f]
    ids=[c["item_id"] for c in rows][:10]
    print("\ngroup",f,"count",count)
    print(" ids:", ids)
    # history lengths
    hs=[len(c["view"].get("history","")) for c in rows]
    print(" history len min/median/max:", min(hs), sorted(hs)[len(hs)//2], max(hs))
    print(" golds:", collections.Counter(c.get("gold") for c in rows))
# how many groups have >1 item and at least one unsafe
multi=[f for f,n in g.items() if n>1]
print("\ngroups >1 item:",len(multi))
mm=[]
for f,n in g.items():
    rows=[c for c in cases if c.get("source_file")==f]
    if any(c.get("gold")==1 for c in rows): mm.append((f,n))
print("groups with >=1 unsafe:",len(mm))
print("distribution of group sizes (with unsafe):", collections.Counter(n for _,n in mm).most_common(8))
