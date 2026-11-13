
import json, os, math, importlib.util, csv
ROOT=r"D:\projects\jev_research"; EXT=os.path.join(ROOT,"rq1","ext-2026-11-13")
spec=importlib.util.spec_from_file_location("dt",os.path.join(EXT,"derive_thresholds.py")); dt=importlib.util.module_from_spec(spec); spec.loader.exec_module(dt)
cells=json.load(open(os.path.join(EXT,"cells.json"),encoding="utf-8"))
def load(model):
    c=[x for x in cells if x["model"]==model and x["dataset"]=="tsbench"]
    if not c: return None
    rows=dt.load_cell(c[0])
    return {iid:(g,p) for (iid,g,sp,p,pred) in rows}
jev=load("jev-packy-1.14.0"); d3=load("d3mini"); kev=load("kev")
print("available:", {k: (len(v) if v else 0) for k,v in [("jev",jev),("d3mini",d3),("kev",kev)]})
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn); return (tp*tn-fp*fn)/den**0.5 if den else None
def roc_points(pairs):  # list of (gold,p)
    P=sum(1 for g,_ in pairs if g==1); N=len(pairs)-P
    out=[]
    for thr in sorted({p for _,p in pairs},reverse=True):
        tp=sum(1 for g,s in pairs if s>=thr and g==1); fp=sum(1 for g,s in pairs if s>=thr and g==0)
        out.append((fp/N, tp/P, thr, tp, fp, N-fp, P-tp))
    return out
def summary(name, pairs):
    pts=roc_points(pairs)
    best=max(pts, key=lambda x: (mcc(int(x[3]),int(x[4]),int(x[5]),int(x[6])) if mcc(int(x[3]),int(x[4]),int(x[5]),int(x[6])) is not None else -9))
    # AUC
    auc=0; prev=(0,0)
    for x in pts: auc += (x[0]-prev[0])*(x[1]+prev[1])/2; prev=(x[0],x[1])
    auc=abs(auc)
    tpr141=None
    for x in pts:
        if x[0]<=0.141: tpr141=max(tpr141 or 0, x[1])
    print(f"{name:30s} AUC={auc:.3f} MCCopt={mcc(int(best[3]),int(best[4]),int(best[5]),int(best[6])):.3f} thr={best[2]:.3f} TPR@FPR14.1={tpr141:.3f}")
# common items
keys=set(jev) & set(d3) & set(kev)
print("common items jev/d3/kev:",len(keys))
jack=[]; d=[]; k=[]
for i in keys:
    jack.append(jev[i]); d.append(d3[i]); k.append(kev[i])
# ensure same gold
print("gold agreement jev/d3:", sum(1 for a,b in zip(jack,d) if a[0]==b[0]), "/", len(keys))
summary("Jev single", [(g,p) for g,p in jack])
summary("d3mini single", [(g,p) for g,p in d])
summary("kev single", [(g,p) for g,p in k])
summary("mean(Jev,d3mini)", [(jack[i][0],(jack[i][1]+d[i][1])/2) for i in range(len(keys))])
summary("mean(Jev,d3,kev)", [(jack[i][0],(jack[i][1]+d[i][1]+k[i][1])/3) for i in range(len(keys))])
summary("max(Jev,d3,kev)", [(jack[i][0],max(jack[i][1],d[i][1],k[i][1])) for i in range(len(keys))])
# rank-average
def ranks(vals):
    order=sorted(range(len(vals)), key=lambda i: vals[i]); r=[0]*len(vals)
    for pos,i in enumerate(order): r[i]=pos/(len(vals)-1)
    return r
rj=ranks([p for g,p in jack]); rd=ranks([p for g,p in d]); rk=ranks([p for g,p in k])
summary("rank-mean(Jev,d3,kev)", [(jack[i][0],(rj[i]+rd[i]+rk[i])/3) for i in range(len(keys))])
