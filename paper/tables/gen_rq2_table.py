
import csv, os, collections
base=r"D:\projects\jev_research\rq1\summary"
outdir=r"D:\projects\jev_research\paper\tables"
TIM=list(csv.DictReader(open(os.path.join(base,"time_tokens.csv"),encoding="utf-8-sig")))
models=[("jev-packy-1.14.0","Jev-1.14.0"),("laya","Laya"),("kev","Kev"),("d3mini","D3-Mini"),
        ("secjev","SecJev"),("jevguard","Jev-Guard"),("gliguard","GLiGuard"),
        ("shieldstral","Shieldstral"),("qwen3guard","Qwen3Guard-Gen"),
        ("qwen35","Qwen3.5-4B"),("gpt6luna","GPT-6 Luna"),("claudehaiku","Claude Haiku 5.5")]
datasets=["agentharm","injecagent","tsbench","stepshield_test","wildguard_response"]
labels=["User Request","External Content","Tool Call","Action","Response"]
prices={"jev-packy-1.14.0":(0.042,0.0),"gpt6luna":(0.044,0.22),"claudehaiku":(0.008824,0.04412)}
by=collections.defaultdict(list)
for r in TIM:
    if r["dataset"] in datasets and r["model"] in dict(models):
        by[(r["model"],r["dataset"])].append(r)
def pick(m,ds):
    rs=by.get((m,ds),[])
    return max(rs,key=lambda x: float(x["n_ok"] or 0)) if rs else None
def fnum(v,nd=2):
    return "--" if v in (None,"") else (("%."+str(nd)+"f") % float(v))
rows=[]
for m,label in models:
    cells=[]
    for ds in datasets:
        r=pick(m,ds)
        if not r: cells += [("--","--","--")]; continue
        n=float(r["n_ok"] or 0)
        mean=r["episode_mean_seconds"]; p95=r["episode_p95_seconds"]
        inp=float(r["input_tokens_per_ok"] or 0)
        out=r["output_tokens_known"]
        outp=(float(out)/n) if out not in ("","None") and n else None
        if m in prices:
            pin,pout=prices[m]
            cost=inp*pin/1000 + ((outp*pout/1000) if outp is not None else 0)
            cs="%.3f"%cost
        else:
            cs="--"
        cells.append((fnum(mean),fnum(p95),cs))
    rows.append((label,cells))
lines=[]
lines.append(r"\begin{table*}[t]")
lines.append(r"    \centering")
lines.append(r"    \scriptsize")
lines.append(r"    \setlength{\tabcolsep}{1.0pt}")
lines.append(r"    \caption{Latency and estimated cost across five tasks. Each task reports mean wall-clock time, 95th-percentile wall-clock time (seconds), and estimated cost per 1,000 items (USD). Action is per trajectory.}")
lines.append(r"    \label{tab:rq2_cost_latency}")
lines.append(r"    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}l*{15}{c}@{}}")
lines.append(r"        \toprule")
lines.append(r"        \multirow{2}{*}{\textbf{Model}}")
lines.append(r"        & \multicolumn{3}{c}{\textbf{User Request}}")
lines.append(r"        & \multicolumn{3}{c}{\textbf{External Content}}")
lines.append(r"        & \multicolumn{3}{c}{\textbf{Tool Call}}")
lines.append(r"        & \multicolumn{3}{c}{\textbf{Action}}")
lines.append(r"        & \multicolumn{3}{c}{\textbf{Response}} \\")
lines.append(r"        \cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10}")
lines.append(r"        \cmidrule(lr){11-13} \cmidrule(lr){14-16}")
lines.append(r"        & Mean$\downarrow$ & P95$\downarrow$ & Cost$\downarrow$ & Mean$\downarrow$ & P95$\downarrow$ & Cost$\downarrow$ & Mean$\downarrow$ & P95$\downarrow$ & Cost$\downarrow$ & Mean$\downarrow$ & P95$\downarrow$ & Cost$\downarrow$ & Mean$\downarrow$ & P95$\downarrow$ & Cost$\downarrow$ \\")
lines.append(r"        \midrule")
for label,cells in rows:
    cs=[]
    for mean,p95,cost in cells:
        cs += [mean, p95, ("--" if cost=="--" else "\\$"+cost)]
    lines.append("        %s & %s \\\\" % (label," & ".join(cs)))
lines.append(r"        \bottomrule")
lines.append(r"    \end{tabular*}")
lines.append(r"    \vspace{3pt}")
lines.append(r"    \begin{minipage}{\textwidth}")
lines.append(r"        \footnotesize")
lines.append(r"        \textit{Notes.} Mean and P95 are episode-level wall-clock seconds per evaluated item; for action inspection they are per trajectory, since StepShield calls the judge once per visible prefix (5.9--10.1 calls per trajectory). Cost is an estimated USD per 1,000 evaluated items (per 1,000 trajectories for action), not an invoice: Jev-1.14.0 at \$0.042/M input and \$0 output; GPT-6 Luna at \$0.044/M input and \$0.22/M output; Claude Haiku 5.5 at \$0.008824/M input and \$0.04412/M output. Local models are unpriced (local compute, not zero cost). \texttt{--} marks unavailable or undefined values.")
lines.append(r"    \end{minipage}")
lines.append(r"\end{table*}")
open(os.path.join(outdir,"rq2-cost-latency.tex"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
for l in lines:
    if "&" in l: print(l)