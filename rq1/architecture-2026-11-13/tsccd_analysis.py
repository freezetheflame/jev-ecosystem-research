
import json, os, math, importlib.util
ROOT=r"D:\projects\jev_research"
RES=os.path.join(ROOT,"rq1","architecture-2026-11-13","runs","tsccd-pilot-600","results.json")
d=json.load(open(RES,encoding="utf-8"))
res=d["results"]
# single-question p
spec=importlib.util.spec_from_file_location("dt",os.path.join(ROOT,"rq1","ext-2026-11-13","derive_thresholds.py"))
dt=importlib.util.module_from_spec(spec); spec.loader.exec_module(dt)
cells=json.load(open(os.path.join(ROOT,"rq1","ext-2026-11-13","cells.json"),encoding="utf-8"))
cell=[x for x in cells if x["model"]=="jev-packy-1.14.0" and x["dataset"]=="tsbench"][0]
sq={iid:p for (iid,g,sp,p,pred) in dt.load_cell(cell)}
PROBES=["history_injection","goal_hijack","tool_purpose","argument_risk","direct_harm","not_justified"]
rows=[]
for r in res:
    if r["score"] is None or r["item_id"] not in sq: continue
    rows.append(dict(item=r["item_id"], gold=r["gold"], split=r["split"],
                     single=sq[r["item_id"]], **{k:r["probs"].get(k) for k in PROBES}))
def is_dev(r): return int(r["item"].split(":")[-1][:2],16)%2==0
dev=[r for r in rows if is_dev(r)]; test=[r for r in rows if not is_dev(r)]
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn); return (tp*tn-fp*fn)/den**0.5 if den else None
def met(rs, dec):
    tp=sum(1 for r in rs if r["gold"]==1 and dec(r)); fn=sum(1 for r in rs if r["gold"]==1 and not dec(r))
    fp=sum(1 for r in rs if r["gold"]==0 and dec(r)); tn=sum(1 for r in rs if r["gold"]==0 and not dec(r))
    return dict(recall=tp/(tp+fn) if tp+fn else None, fpr=fp/(fp+tn) if fp+tn else None, mcc=mcc(tp,fp,tn,fn), tp=tp,fp=fp,fn=fn,tn=tn)
def auc(rs, score):
    pairs=sorted(((score(r), r["gold"]) for r in rs), reverse=True)
    P=sum(g for _,g in pairs); N=len(pairs)-P
    tp=fp=0; prev_fp=prev_tp=0; a=0.0; prev=None
    for s,g in pairs:
        if prev is not None and s!=prev: a += (fp-prev_fp)*(tp+prev_tp)/2; prev_fp,prev_tp=fp,tp
        prev=s
        if g==1: tp+=1
        else: fp+=1
    a += (fp-prev_fp)*(tp+prev_tp)/2
    return a/(P*N) if P and N else None
def best(rs, score, target=None):
    b=None
    for t in [i/1000 for i in range(1,1000)]:
        m=met(rs, lambda r: score(r)>=t)
        if m["mcc"] is None: continue
        if target is not None and m["fpr"]>target: continue
        k=m["mcc"] if target is None else m["recall"]
        if b is None or k>b[0]: b=(k,t,m)
    return b
print("dev/test:",len(dev),len(test))
print("\n== AUC (dev / test) ==")
for name,score in [("single",lambda r:r["single"]),
                   ("max-probe",lambda r:max(r[k] for k in PROBES)),
                   ("mean-probe",lambda r:sum(r[k] for k in PROBES)/len(PROBES)),
                   ("single+mean",lambda r:(r["single"]+sum(r[k] for k in PROBES)/len(PROBES))/2),
                   ("single+inj",lambda r:(r["single"]+r["history_injection"])/2)]:
    print(f"{name:14s} dev AUC={auc(dev,score):.3f} test AUC={auc(test,score):.3f}")
# logistic fit on dev (pure python, 7 features + bias), standardize
feats=["single"]+PROBES
def vec(r): return [r[f] for f in feats]
mu=[sum(vec(r)[i] for r in dev)/len(dev) for i in range(len(feats))]
sd=[max(1e-6,(sum((vec(r)[i]-mu[i])**2 for r in dev)/len(dev))**0.5) for i in range(len(feats))]
def z(r): return [(vec(r)[i]-mu[i])/sd[i] for i in range(len(feats))]
w=[0.0]*(len(feats)+1)
lr=0.05; lam=0.01
for it in range(3000):
    g=[0.0]*(len(feats)+1)
    for r in dev:
        xs=z(r); s=w[-1]+sum(w[i]*xs[i] for i in range(len(xs)))
        p=1/(1+math.exp(-max(-30,min(30,s))))
        err=p-r["gold"]
        for i in range(len(xs)): g[i]+=err*xs[i]
        g[-1]+=err
    for i in range(len(feats)): w[i]-=lr*(g[i]/len(dev)+lam*w[i])
    w[-1]-=lr*(g[-1]/len(dev))
def logit(r):
    xs=z(r); s=w[-1]+sum(w[i]*xs[i] for i in range(len(xs))); return 1/(1+math.exp(-max(-30,min(30,s))))
print("\nlogistic AUC dev=%.3f test=%.3f"%(auc(dev,logit),auc(test,logit)))
for name,score in [("single",lambda r:r["single"]),("logistic",logit),("max-probe",lambda r:max(r[k] for k in PROBES))]:
    b=best(dev,score)
    if not b: continue
    m=met(test,lambda r: score(r)>=b[1])
    print(f"{name:10s} thr={b[1]:.3f} devMCC={b[0]:.3f} -> testMCC={m['mcc']:.3f} TPR={m['recall']:.3f} FPR={m['fpr']:.3f}")
# per-source logistic vs single
for s in ("asb-traj","agentdojo-traj","agentharm-traj"):
    print("\n--",s)
    for name,score in [("single",lambda r:r["single"]),("logistic",logit)]:
        b=best([r for r in dev if r["split"]==s],score)
        if not b: continue
        m=met([r for r in test if r["split"]==s],lambda r: score(r)>=b[1])
        print(f"  {name:9s} test n={sum(1 for r in test if r['split']==s)} MCC={m['mcc'] if m['mcc'] is None else round(m['mcc'],3)} TPR={m['recall']:.3f} FPR={m['fpr']:.3f}")
