
import csv, os, collections
base=r"D:\projects\jev_research\rq1\summary"
outdir=r"D:\projects\jev_research\paper\tables"
MET=list(csv.DictReader(open(os.path.join(base,"metrics_full.csv"),encoding="utf-8-sig")))
TIM=list(csv.DictReader(open(os.path.join(base,"time_tokens.csv"),encoding="utf-8-sig")))
models=[("jev-packy-1.14.0","Jev-1.14.0"),("laya","Laya"),("kev","Kev"),("d3mini","D3-Mini"),("secjev","SecJev"),("jevguard","Jev-Guard"),("gliguard","GLiGuard"),("shieldstral","Shieldstral"),("qwen3guard","Qwen3Guard-Gen"),("qwen35","Qwen3.5-4B"),("gpt6luna","GPT-6 Luna"),("claudehaiku","Claude Haiku 5.5")]
datasets=["agentharm","injecagent","tsbench","stepshield_test","wildguard_response"]
def get(m,ds):
    rs=[r for r in MET if r["model"]==m and r["dataset"]==ds]
    return rs[0] if rs else None
def ints(r): return int(float(r["tp"] or 0)),int(float(r["fp"] or 0)),int(float(r["tn"] or 0)),int(float(r["fn"] or 0))
def mf1(tp,fp,tn,fn):
    f1p=2*tp/(2*tp+fp+fn) if (2*tp+fp+fn)>0 else 0.0
    f1n=2*tn/(2*tn+fn+fp) if (2*tn+fn+fp)>0 else 0.0
    if tn+fp==0: return f1p
    if tp+fn==0: return f1n
    return (f1p+f1n)/2.0
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return (tp*tn-fp*fn)/den**0.5 if den else None
with open(os.path.join(outdir,"rq1-effectiveness.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["model","task","MF1_percent","MCC_percent","FNR_percent","FPR_percent","tp","fp","tn","fn"])
    for m,label in models:
        for ds in datasets:
            r=get(m,ds); tp,fp,tn,fn=ints(r); mc=mcc(tp,fp,tn,fn)
            fnrv=fn/(tp+fn) if (tp+fn)>0 else None; fprv=fp/(fp+tn) if (fp+tn)>0 else None
            w.writerow([label,ds,"%.2f"%(100*mf1(tp,fp,tn,fn)),"" if mc is None else "%.2f"%(100*mc),"" if fnrv is None else "%.2f"%(100*fnrv),"" if fprv is None else "%.2f"%(100*fprv),tp,fp,tn,fn])
prices={"jev-packy-1.14.0":(0.042,0.0),"gpt6luna":(0.044,0.22),"claudehaiku":(0.008824,0.04412)}
by=collections.defaultdict(list)
for r in TIM:
    if r["dataset"] in datasets and r["model"] in dict(models): by[(r["model"],r["dataset"])].append(r)
with open(os.path.join(outdir,"rq2-cost-latency.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["model","task","episode_mean_s","call_mean_s","calls_per_item","input_tokens_per_item","cost_usd_per_1k_items"])
    for m,label in models:
        for ds in datasets:
            rs=by.get((m,ds),[])
            if not rs: continue
            r=max(rs,key=lambda x: float(x["n_ok"] or 0)); n=float(r["n_ok"] or 0)
            t=float(r["episode_mean_seconds"] or 0); calls=float(r["call_n"] or 0)/n if n else 0
            inp=float(r["input_tokens_per_ok"] or 0)
            if m in prices:
                pin,pout=prices[m]; out=r["output_tokens_known"]
                outp=(float(out)/n) if out not in ("","None") and n else None
                cost=inp*pin/1000 + ((outp*pout/1000) if outp is not None else 0)
                cs="%.3f"%cost
            else: cs=""
            w.writerow([label,ds,"%.3f"%t,"%.3f"%calls,"%.2f"%calls,"%.1f"%inp,cs])
readme="""# RQ1/RQ2 tables

Generated 2026-11-18 from rq1/summary/metrics_full.csv and rq1/summary/time_tokens.csv.
Generation scripts: gen_rq1_table.py, gen_rq2_table.py.

## RQ1 rq1-effectiveness.tex

- MF1 = macro-F1 computed from official TP/FP/TN/FN.
- MCC = Matthews correlation coefficient, reported x100.
- FNR and FPR are included as requested.
- InjecAgent (External Content) is positives-only: MCC undefined; MF1 is positive-class F1.
- Shieldstral on StepShield test is a constant (all-safe) predictor: MCC undefined.
- Action uses StepShield test (7,935); StepShield holdout (216) is not in this table.
- Values match metrics_full.csv counts; no estimates.

## RQ2 rq2-cost-latency.tex

- Time = episode_mean_seconds per evaluated item; for Action it is per trajectory (the judge is called once per visible prefix, 5.9-10.1 calls/trajectory).
- Cost per 1,000 items = input tokens x input price + output tokens x output price.
- Prices: Jev 0.042 USD/M input, 0 output; GPT-6 Luna 0.044/0.22; Claude Haiku 5.5 0.008824/0.04412.
- Local models are unpriced (local compute is not zero cost).
- List-price estimates, not invoices.

## Columns

See the .csv companions for machine-readable values.
"""
open(os.path.join(outdir,"README.md"),"w",encoding="utf-8").write(readme)
print("wrote README and CSV files")