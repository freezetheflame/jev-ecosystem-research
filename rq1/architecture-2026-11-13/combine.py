
import json, os
ROOT=r"D:\projects\jev_research"
RUN=os.path.join(ROOT,"rq1","architecture-2026-11-13","runs","v2-prefixmiss-census")
eps=json.load(open(os.path.join(RUN,"episodes.jsonl"),encoding="utf-8"))
# baseline prefix on full test split (from main summary: TP=584,FN=55,FP=966,TN=6328)
TP0,FN0,FP0,TN0=584,55,966,6328
print("baseline prefix: recall=%.4f fpr=%.4f"%(TP0/(TP0+FN0), FP0/(FP0+TN0)))
print("census items:",len(eps),"rogue",sum(e['gold']==1 for e in eps),"clean",sum(e['gold']==0 for e in eps))
def decide(e,thr):
    return any((s['score'] or 0)>=thr for s in e['step_scores'])
print("\nthreshold | catch/55 | addedFP/55 | combined recall | combined FPR")
for thr in [0.4,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9]:
    catch=sum(1 for e in eps if e['gold']==1 and decide(e,thr))
    addfp=sum(1 for e in eps if e['gold']==0 and decide(e,thr))
    # extrapolate added FP to all prefix-clean (TN0) and add TP to combined
    addFP_all=FP0+addfp/55*TN0
    rec=(TP0+catch)/(TP0+FN0); fpr=addFP_all/(FP0+TN0)
    print(f"{thr:5.2f} | {catch:2d}/55 | {addfp:2d}/55 | {rec:.3f} | {fpr:.3f}")
# per-item: which missed rogues CCD catches; divergence step distribution
import statistics
caught=[e for e in eps if e['gold']==1 and decide(e,0.6)]
missed=[e for e in eps if e['gold']==1 and not decide(e,0.6)]
def mx(e): return max((s['score'] or 0) for s in e['step_scores'])
print("\ncaught n=%d, missed n=%d; missed max scores:"%(len(caught),len(missed)), sorted(round(mx(e),2) for e in missed))
# detection step vs divergence for caught
gaps=[]
for e in caught:
    s=next((s['step'] for s in e['step_scores'] if (s['score'] or 0)>=0.6), None)
    if s and e.get('divergence_step'): gaps.append(s-e['divergence_step'])
print("gap (alert - divergence) for caught:", gaps)
