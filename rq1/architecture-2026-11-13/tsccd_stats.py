
import json, os, math, importlib.util
ROOT=r"D:\projects\jev_research"
RES=os.path.join(ROOT,"rq1","architecture-2026-11-13","runs","tsccd-pilot-600","results.json")
d=json.load(open(RES,encoding="utf-8")); res=d["results"]
spec=importlib.util.spec_from_file_location("dt",os.path.join(ROOT,"rq1","ext-2026-11-13","derive_thresholds.py"))
dt=importlib.util.module_from_spec(spec); spec.loader.exec_module(dt)
cells=json.load(open(os.path.join(ROOT,"rq1","ext-2026-11-13","cells.json"),encoding="utf-8"))
cell=[x for x in cells if x["model"]=="jev-packy-1.14.0" and x["dataset"]=="tsbench"][0]
sq={iid:p for (iid,g,sp,p,pred) in dt.load_cell(cell)}
PROBES=["history_injection","goal_hijack","tool_purpose","argument_risk","direct_harm","not_justified"]
rows=[]
for r in res:
    if r["score"] is None or r["item_id"] not in sq: continue
    rows.append(dict(item=r["item_id"], gold=r["gold"], split=r["split"], single=sq[r["item_id"]], **{k:r["probs"].get(k) for k in PROBES}))
def is_dev(r): return int(r["item"].split(":")[-1][:2],16)%2==0
dev=[r for r in rows if is_dev(r)]; test=[r for r in rows if not is_dev(r)]
feats=["single"]+PROBES
def vec(r): return [r[f] for f in feats]
mu=[sum(vec(r)[i] for r in dev)/len(dev) for i in range(len(feats))]
sd=[max(1e-6,(sum((vec(r)[i]-mu[i])**2 for r in dev)/len(dev))**0.5) for i in range(len(feats))]
def z(r): return [(vec(r)[i]-mu[i])/sd[i] for i in range(len(feats))]
w=[0.0]*(len(feats)+1); lr=0.05; lam=0.01
for it in range(3000):
    g=[0.0]*(len(feats)+1)
    for r in dev:
        xs=z(r); s=w[-1]+sum(w[i]*xs[i] for i in range(len(xs))); p=1/(1+math.exp(-max(-30,min(30,s)))); err=p-r["gold"]
        for i in range(len(xs)): g[i]+=err*xs[i]
        g[-1]+=err
    for i in range(len(feats)): w[i]-=lr*(g[i]/len(dev)+lam*w[i])
    w[-1]-=lr*(g[-1]/len(dev))
def logit(r):
    xs=z(r); s=w[-1]+sum(w[i]*xs[i] for i in range(len(xs))); return 1/(1+math.exp(-max(-30,min(30,s))))
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn); return (tp*tn-fp*fn)/den**0.5 if den else None
def met(rs,dec):
    tp=sum(1 for r in rs if r["gold"]==1 and dec(r)); fn=sum(1 for r in rs if r["gold"]==1 and not dec(r))
    fp=sum(1 for r in rs if r["gold"]==0 and dec(r)); tn=sum(1 for r in rs if r["gold"]==0 and not dec(r))
    return dict(recall=tp/(tp+fn),fpr=fp/(fp+tn),mcc=mcc(tp,fp,tn,fn),tp=tp,fp=fp,fn=fn,tn=tn)
def best(rs,score):
    b=None
    for t in [i/1000 for i in range(1,1000)]:
        m=met(rs,lambda r:score(r)>=t)
        if m["mcc"] is None: continue
        if b is None or m["mcc"]>b[0]: b=(m["mcc"],t,m)
    return b
b1=best(dev,lambda r:r["single"]); b2=best(dev,logit)
print("single dev thr",b1[1],"MCC",round(b1[0],3)); print("logit dev thr",b2[1],"MCC",round(b2[0],3))
m1=met(test,lambda r:r["single"]>=b1[1]); m2=met(test,lambda r:logit(r)>=b2[1])
print("test single:",{k:(round(v,3) if isinstance(v,float) else v) for k,v in m1.items()})
print("test logit :",{k:(round(v,3) if isinstance(v,float) else v) for k,v in m2.items()})
# McNemar exact on test decisions
b=0;c=0
for r in test:
    a1=(r["single"]>=b1[1])==(r["gold"]==1); a2=(logit(r)>=b2[1])==(r["gold"]==1)
    if a1 and not a2: b+=1
    elif a2 and not a1: c+=1
n=b+c
p=1.0
if n:
    k=min(b,c); s=sum(math.comb(n,i) for i in range(k+1)); p=min(1.0,2*s/2**n)
print("McNemar single vs logit: b=%d c=%d n=%d p=%.4f"%(b,c,n,p))
# AUC diff bootstrap-ish: paired bootstrap on test
import random
rng=random.Random(20261113)
def auc(rs,score):
    pairs=sorted(((score(r),r["gold"]) for r in rs),reverse=True); P=sum(g for _,g in pairs); N=len(pairs)-P
    tp=fp=0; prev=None; prev_fp=prev_tp=0; a=0.0
    for s,g in pairs:
        if prev is not None and s!=prev: a+=(fp-prev_fp)*(tp+prev_tp)/2; prev_fp,prev_tp=fp,tp
        prev=s
        if g==1: tp+=1
        else: fp+=1
    a+=(fp-prev_fp)*(tp+prev_tp)/2
    return a/(P*N)
diffs=[]
for _ in range(2000):
    sample=[test[rng.randrange(len(test))] for _ in range(len(test))]
    if sum(r["gold"] for r in sample) in (0,len(sample)): continue
    diffs.append(auc(sample,logit)-auc(sample,lambda r:r["single"]))
diffs.sort()
print("AUC diff (logit-single) mean=%.3f 95%% CI=[%.3f,%.3f]"%(sum(diffs)/len(diffs),diffs[int(.025*len(diffs))],diffs[int(.975*len(diffs))]))
