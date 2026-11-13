
import json, os, math, importlib.util, csv
ROOT=r"D:\projects\jev_research"
RUN=os.path.join(ROOT,"data","agent-security-study","runs","full-api-jev-packy-v1","jev","tsbench")
cases={}; eps={}
for line in open(os.path.join(RUN,"cases.jsonl"),encoding="utf-8"):
    line=line.strip()
    if line: c=json.loads(line); cases[c["item_id"]]=c
for line in open(os.path.join(RUN,"episodes.jsonl"),encoding="utf-8"):
    line=line.strip()
    if line: e=json.loads(line); eps[e["item_id"]]=e
print("cases",len(cases),"episodes",len(eps))
c=next(iter(cases.values()))
print("view keys:", list(c["view"].keys()))
print("example view:", json.dumps(c["view"], ensure_ascii=False)[:900])
# per-source metrics from shift.csv
sh=list(csv.DictReader(open(os.path.join(ROOT,"rq1","ext-2026-11-13","shift.csv"),encoding="utf-8")))
print("\n== per-source MCC (TS-Bench) ==")
for m in ["jev-packy-1.14.0","d3mini","gpt6luna","claudehaiku"]:
    rows=[r for r in sh if r["dataset"]=="tsbench" and r["model"]==m]
    if rows: print(m, "; ".join(f"{r['split']}: n={r['n']} TPR={float(r['tpr']):.3f} TNR={float(r['tnr']):.3f} MCC={float(r['mcc']):.3f}" for r in rows))
# Jev failure samples
fn=[(i,e) for i,e in eps.items() if e.get("gold")==1 and e.get("prediction")==0]
fp=[(i,e) for i,e in eps.items() if e.get("gold")==0 and e.get("prediction")==1]
print("\nFN",len(fn),"FP",len(fp))
for label, samples in [("FN",fn[:4]),("FP",fp[:2])]:
    for i,e in samples:
        v=cases[i]["view"]
        print(f"\n--- {label} {i} source={e.get('split')} gold={e.get('gold')}")
        txt=json.dumps(v,ensure_ascii=False)
        print(txt[:800])
# Jev ROC: TPR at GPT FPR
EXT=os.path.join(ROOT,"rq1","ext-2026-11-13")
spec=importlib.util.spec_from_file_location("dt",os.path.join(EXT,"derive_thresholds.py"))
dt=importlib.util.module_from_spec(spec); spec.loader.exec_module(dt)
cells=json.load(open(os.path.join(EXT,"cells.json"),encoding="utf-8"))
cell=[x for x in cells if x["model"]=="jev-packy-1.14.0" and x["dataset"]=="tsbench"][0]
rows=dt.load_cell(cell)
pts=[(g,p) for (_i,g,_s,p,_pred) in rows]
P=sum(1 for g,_ in pts if g==1); N=len(pts)-P
print("\nJev TS-Bench n=%d P=%d N=%d"%(len(pts),P,N))
for target in (0.05,0.10,0.141,0.20):
    best=0
    for thr in sorted({p for _,p in pts},reverse=True):
        tp=sum(1 for g,s in pts if s>=thr and g==1); fp=sum(1 for g,s in pts if s>=thr and g==0)
        if fp/N<=target: best=max(best,tp/P)
    print(f"TPR at FPR<={target}: {best:.3f}")
