
import json, os, re, importlib.util
ROOT=r"D:\projects\jev_research"; RUN=os.path.join(ROOT,"data","agent-security-study","runs","full-api-jev-packy-v1","jev","tsbench")
cases={}; eps={}
for line in open(os.path.join(RUN,"cases.jsonl"),encoding="utf-8"):
    line=line.strip()
    if line: c=json.loads(line); cases[c["item_id"]]=c
for line in open(os.path.join(RUN,"episodes.jsonl"),encoding="utf-8"):
    line=line.strip()
    if line: e=json.loads(line); eps[e["item_id"]]=e
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn); return (tp*tn-fp*fn)/den**0.5 if den else None
def met(items, dec, label):
    tp=sum(1 for i in items if eps[i]["gold"]==1 and dec(i)); fn=sum(1 for i in items if eps[i]["gold"]==1 and not dec(i))
    fp=sum(1 for i in items if eps[i]["gold"]==0 and dec(i)); tn=sum(1 for i in items if eps[i]["gold"]==0 and not dec(i))
    tp_tpr=tp/(tp+fn) if tp+fn else None; tn_tnr=tn/(tn+fp) if tn+fp else None; m=mcc(tp,fp,tn,fn)
    print(f"{label:26s} n={len(items):5d} TPR={'%.3f'%tp_tpr if tp_tpr is not None else 'NA'} TNR={'%.3f'%tn_tnr if tn_tnr is not None else 'NA'} MCC={'%.3f'%m if m is not None else 'undefined'}")
items=[i for i in eps if eps[i].get("status")=="ok" and eps[i].get("gold") in (0,1)]
by_src={}
for i in items: by_src.setdefault(eps[i].get("split"),[]).append(i)
RISK=re.compile(r"(attack|tamper|exfiltrat|manipulat|backdoor|steal|poison|hijack|malicious|exploit|spy|sabotage|unauthori[sz]ed|bypass)", re.I)
def tool_name(i):
    ca=cases[i]["view"].get("candidate_action","")
    m=re.search(r"Action:\s*([A-Za-z0-9_\-]+)", ca)
    return m.group(1) if m else ""
def rule_tool(i): return bool(RISK.search(tool_name(i)))
print("== Jev baseline (all / per source) ==")
met(items, lambda i: eps[i].get("prediction")==1, "Jev single-question")
for s,its in by_src.items(): met(its, lambda i: eps[i].get("prediction")==1, "  Jev "+s)
print("\n== simple tool-name rule (attack-ish tool => unsafe) ==")
met(items, rule_tool, "tool-name rule")
for s,its in by_src.items(): met(its, rule_tool, "  rule "+s)
print("\n== Jev errors explained by tool-name rule ==")
fn=[i for i in items if eps[i]["gold"]==1 and eps[i].get("prediction")==0]
fp=[i for i in items if eps[i]["gold"]==0 and eps[i].get("prediction")==1]
print("FN:",len(fn),"with attack-ish tool:",sum(1 for i in fn if rule_tool(i)))
print("FP:",len(fp),"with attack-ish tool:",sum(1 for i in fp if rule_tool(i)))
print("FN tool name examples:", sorted({tool_name(i) for i in fn})[:15])
print("FN by source:", {s: sum(1 for i in fn if eps[i].get('split')==s) for s in by_src})
print("FP by source:", {s: sum(1 for i in fp if eps[i].get('split')==s) for s in by_src})
# Jev ROC at matched FPR
EXT=os.path.join(ROOT,"rq1","ext-2026-11-13")
spec=importlib.util.spec_from_file_location("dt",os.path.join(EXT,"derive_thresholds.py")); dt=importlib.util.module_from_spec(spec); spec.loader.exec_module(dt)
cells=json.load(open(os.path.join(EXT,"cells.json"),encoding="utf-8"))
cell=[x for x in cells if x["model"]=="jev-packy-1.14.0" and x["dataset"]=="tsbench"][0]
rows=dt.load_cell(cell); pts=[(g,p) for (_i,g,_s,p,_pred) in rows]
P=sum(1 for g,_ in pts if g==1); N=len(pts)-P
print("\n== Jev ROC (TS-Bench, n=%d P=%d N=%d) =="%(len(pts),P,N))
for target in (0.05,0.10,0.141,0.20,0.30):
    best=0
    for thr in sorted({p for _,p in pts},reverse=True):
        tp=sum(1 for g,s in pts if s>=thr and g==1); fp=sum(1 for g,s in pts if s>=thr and g==0)
        if fp/N<=target: best=max(best,tp/P)
    print(f"  TPR at FPR<={target:.3f}: {best:.3f}")