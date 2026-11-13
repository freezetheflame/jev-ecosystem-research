
import csv, math, os, json
ROOT=r"D:\projects\jev_research"
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return (tp*tn-fp*fn)/math.sqrt(den) if den else None
def show(name, tp,fp,tn,fn, note=""):
    print(f"{name:34s} TP={tp:5.0f} FN={fn:5.0f} FP={fp:6.0f} TN={tn:6.0f}  MCC={('%.4f'%mcc(tp,fp,tn,fn)) if mcc(tp,fp,tn,fn) is not None else 'undefined'}  {note}")

# exact LLM counts from the official summary
rows=list(csv.DictReader(open(os.path.join(ROOT,"rq1","summary","metrics_full.csv"),encoding="utf-8-sig")))
def get(model, ds):
    r=[x for x in rows if x["model"]==model and x["dataset"]==ds]
    return r[0] if r else None
print("=== full test split (7,933; 639 rogue / 7,294 clean) ===")
show("Jev prefix", 584,966,6328,55)
show("ConstraintGuard (rerun)", 155,2170,5124,484)
show("ConstraintGuard+ (ours)", 102,84,7210,537)
for m,label in [("gpt6luna","GPT-6 Luna"),("claudehaiku","Claude Haiku")]:
    r=get(m,"stepshield_test")
    if r: show(label, int(r["tp"]),int(r["fp"]),int(r["tn"]),int(r["fn"]))
# combined prefix+CCD estimates (added FP extrapolated from 55 prefix-clean)
TP0,FN0,FP0,TN0=584,55,966,6328
for thr,add_tp,add_fp_sample in [(0.60,44,3),(0.75,34,1),(0.90,17,0)]:
    add_fp=add_fp_sample/55*TN0
    show(f"prefix+CCD @{thr} (estimate)", TP0+add_tp, FP0+add_fp, TN0-add_fp, FN0-add_tp)
print("\n=== held-out 216 (108 rogue / 108 clean) ===")
show("Jev prefix", 105,14,94,3)
show("GPT-6 Luna", 107,44,64,1)
show("Claude Haiku", 107,23,85,1)
show("Official LLMJudge (GPT-4.1-mini)", 103,6,102,5)
show("ConstraintGuard (published)", 26,27,81,82)
print("\n=== census 110 (55 prefix-missed rogue / 55 prefix-clean) ===")
show("Jev prefix (constant-negative)", 0,0,55,55, "MCC undefined: no positive predictions")
show("ConstraintGuard", 16,19,36,39)
show("ConstraintGuard+", 7,0,55,48)
show("CCD @0.60", 44,3,52,11)
print("\n=== random holdout 20/20 (CCD v2) ===")
show("CCD v2 @0.60", 19,3,17,1)
