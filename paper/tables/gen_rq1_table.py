
import csv, os
base=r"D:\projects\jev_research\rq1\summary"
outdir=r"D:\projects\jev_research\paper\tables"
os.makedirs(outdir, exist_ok=True)

MET=list(csv.DictReader(open(os.path.join(base,"metrics_full.csv"),encoding="utf-8-sig")))
TIM=list(csv.DictReader(open(os.path.join(base,"time_tokens.csv"),encoding="utf-8-sig")))

models=[("jev-packy-1.14.0","Jev-1.14.0"),("laya","Laya"),("kev","Kev"),("d3mini","D3-Mini"),
        ("secjev","SecJev"),("jevguard","Jev-Guard"),("gliguard","GLiGuard"),
        ("shieldstral","Shieldstral"),("qwen3guard","Qwen3Guard-Gen"),
        ("qwen35","Qwen3.5-4B"),("gpt6luna","GPT-6 Luna"),("claudehaiku","Claude Haiku 5.5")]
datasets=[("agentharm","agentharm"),("injecagent","injecagent"),("tsbench","tsbench"),
          ("stepshield_test","stepshield_test"),("wildguard_response","wildguard_response")]
def row_for(m,ds):
    rs=[r for r in MET if r["model"]==m and r["dataset"]==ds]
    return rs[0] if rs else None
def ints(r):
    return int(float(r["tp"] or 0)),int(float(r["fp"] or 0)),int(float(r["tn"] or 0)),int(float(r["fn"] or 0))
def macro_f1(tp,fp,tn,fn):
    f1p=2*tp/(2*tp+fp+fn) if (2*tp+fp+fn)>0 else 0.0
    f1n=2*tn/(2*tn+fn+fp) if (2*tn+fn+fp)>0 else 0.0
    if tn+fp==0:  # positives-only
        return f1p
    if tp+fn==0:  # negatives-only
        return f1n
    return (f1p+f1n)/2.0
def mcc(tp,fp,tn,fn):
    den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
    return (tp*tn-fp*fn)/den**0.5 if den else None
def pct(v): return ("%.2f"%(100*v)) if v is not None else "--"

lines=[]
lines.append(r"\begin{table*}[t]")
lines.append(r"    \centering")
lines.append(r"    \small")
lines.append(r"    \setlength{\tabcolsep}{2pt}")
lines.append(r"    \caption{Security judgment effectiveness across five tasks. Values are percentages; MF1 is macro-F1 and MCC is Matthews correlation coefficient.}")
lines.append(r"    \label{tab:rq1_effectiveness}")
lines.append(r"    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}l*{10}{c}@{}}")
lines.append(r"        \toprule")
lines.append(r"        \multirow{2}{*}{\textbf{Model}}")
lines.append(r"        & \multicolumn{2}{c}{\textbf{User Request}}")
lines.append(r"        & \multicolumn{2}{c}{\textbf{External Content}}")
lines.append(r"        & \multicolumn{2}{c}{\textbf{Tool Call}}")
lines.append(r"        & \multicolumn{2}{c}{\textbf{Action}}")
lines.append(r"        & \multicolumn{2}{c}{\textbf{Response}} \\")
lines.append(r"        \cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}")
lines.append(r"        \cmidrule(lr){8-9} \cmidrule(lr){10-11}")
lines.append(r"        & MF1$\uparrow$ & MCC$\uparrow$ & MF1$\uparrow$ & MCC$\uparrow$ & MF1$\uparrow$ & MCC$\uparrow$ & MF1$\uparrow$ & MCC$\uparrow$ & MF1$\uparrow$ & MCC$\uparrow$ \\")
lines.append(r"        \midrule")
for i,(m,label) in enumerate(models):
    if i in (6,9): lines.append(r"        \midrule")
    cells=[]
    for ds,_ in datasets:
        r=row_for(m,ds)
        if not r:
            cells += ["--","--"]; continue
        tp,fp,tn,fn=ints(r)
        mf=macro_f1(tp,fp,tn,fn)
        mc=mcc(tp,fp,tn,fn)
        cells += [pct(mf), pct(mc)]
    lines.append("        %s & %s \\\\" % (label," & ".join(cells)))
lines.append(r"        \bottomrule")
lines.append(r"    \end{tabular*}")
lines.append(r"    \vspace{3pt}")
lines.append(r"    \begin{minipage}{\textwidth}")
lines.append(r"        \footnotesize")
lines.append(r"        \textit{Notes.} MF1 is macro-F1 computed from the official confusion counts; MCC is reported $\times100$ for readability. External content (InjecAgent) is positives-only, so MCC is undefined and MF1 is the positive-class F1. \texttt{--} marks undefined or unavailable values (e.g., MCC for a constant predictor). User request: AgentHarm public test (416); external content: InjecAgent (2,108 positives); tool call: TS-Bench (5,401 scorable; 1,781 controversial items excluded; SecJev 124 and Claude Haiku 30 invalid predictions); action: StepShield test (7,935); response: WildGuardTest response-harm (Mode E). Jev is jev-1.14.0 via Packy; all judgments use the official contract thresholds.")
lines.append(r"    \end{minipage}")
lines.append(r"\end{table*}")
open(os.path.join(outdir,"rq1-effectiveness.tex"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
print("\n".join(lines[:18]))
print("...")
for l in lines[18:]:
    if "&" in l: print(l)