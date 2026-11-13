
import json, os, statistics
ROOT = r"D:\projects\jev_research"
RUN = os.path.join(ROOT, "data", "agent-security-study", "runs", "full-api-jev-packy-v1", "jev", "stepshield")
eps=[]; cases={}
for line in open(os.path.join(RUN,"episodes.jsonl"), encoding="utf-8"):
    line=line.strip()
    if line:
        r=json.loads(line)
        if r.get("split")=="test" and r.get("status")=="ok": eps.append(r)
for line in open(os.path.join(RUN,"cases.jsonl"), encoding="utf-8"):
    line=line.strip()
    if line:
        c=json.loads(line); cases[c.get("item_id")]=c
rogue=[r for r in eps if r.get("gold")==1]
det=[r for r in rogue if r.get("prediction")==1]
miss=[r for r in rogue if r.get("prediction")==0]
def stats(group,name):
    dv=[cases[r["item_id"]]["divergence_step"] for r in group if cases.get(r["item_id"])]
    lens=[len(cases[r["item_id"]]["view"].get("steps",[])) for r in group if cases.get(r["item_id"])]
    print(name, "n=",len(group), "div step median", statistics.median(dv), "mean", round(statistics.mean(dv),1),
          "| traj len median", statistics.median(lens))
    return dv
dv_d=stats(det,"detected"); dv_m=stats(miss,"missed")
from collections import Counter
print("missed divergence step counts:", sorted(Counter(dv_m).items()))
print("detected divergence step counts (first 10):", sorted(Counter(dv_d).items())[:10])
# types
print("missed types:", Counter(cases[r["item_id"]].get("trajectory_type") for r in miss if cases.get(r["item_id"])).most_common())
print("detected types:", Counter(cases[r["item_id"]].get("trajectory_type") for r in det if cases.get(r["item_id"])).most_common())
# show divergence step content for missed
for r in miss[:5]:
    c=cases[r["item_id"]]; d=c["divergence_step"]; steps=c["view"]["steps"]
    print("\n=== missed", r["item_id"], "type", c.get("trajectory_type"), "div", d, "len", len(steps))
    for st in steps[max(0,d-1):d+1]:
        print(" step", st.get("step"), "| action:", st.get("action"), "| args:", json.dumps(st.get("arguments"), ensure_ascii=False)[:200])
        print("   obs:", (st.get("observation") or "")[:200].replace("\n"," "))
        print("   thought:", (st.get("thought") or "")[:160].replace("\n"," "))
