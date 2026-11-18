
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
def fmt_time(v): return "--" if v in (None,"") else ("%.2f"%float(v))
def fmt_cost(v): return "--" if v is None else ("%.3f"%v)
rows=[]
for m,label in models:
    cells=[]
    for ds in datasets:
        r=pick(m,ds)
        if not r: cells.append(("--","--")); continue
        n=float(r["n_ok"] or 0)
        t=float(r["episode_mean_seconds"] or 0)
        inp=float(r["input_tokens_per_ok"] or 0)
        out_total=r["output_tokens_known"]
        out=None
        if out_total not in ("","None") and n>0:
            out=float(out_total)/n
        if m in prices:
            pin,pout=prices[m]
            cost=inp*pin/1000.0 + (out*pout/1000.0 if out is not None else 0.0)
            star = "*" if (out is None and m in ("gpt6luna","claudehaiku")) else ""
            cells.append((fmt_time(t), fmt_cost(cost)+star))
        else:
            cells.append((fmt_time(t), "--"))
    rows.append((label,cells))
lines=[]
lines.append(r"\begin{table*}[t]")
lines.append(r"    \centering")
lines.append(r"    \small")
lines.append(r"    \setlength{\tabcolsep}{3pt}")
lines.append(r"    \caption{Latency per evaluated item (seconds) and estimated cost per 1,000 items (USD) across five tasks. Action is per trajectory.}")
lines.append(r"    \label{tab:rq2_cost_latency}")
lines.append(r"    \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}l*{5}{c}@{}}")
lines.append(r"        \toprule")
lines.append(r"        \textbf{Model} & \textbf{User Request} & \textbf{External Content} & \textbf{Tool Call} & \textbf{Action} & \textbf{Response} \\")
lines.append(r"        \midrule")
for label,cells in rows:
    cs=["%s\\,s / %s"%(t, ("--" if c=="--" else "\\$"+c)) for t,c in cells]
    lines.append("        %s & %s \\\\" % (label," & ".join(cs)))
lines.append(r"        \bottomrule")
lines.append(r"    \end{tabular*}")
lines.append(r"    \vspace{3pt}")
lines.append(r"    \begin{minipage}{\textwidth}")
lines.append(r"        \footnotesize")
lines.append(r"        \textit{Notes.} Time is the mean wall-clock time per evaluated item; for action inspection it is per trajectory, since StepShield invokes the judge once per visible prefix (5.9--10.1 calls per trajectory). Costs are list-price estimates, not invoices: Jev-1.14.0 at \$0.042/M input and \$0 output; GPT-6 Luna at \$0.044/M input and \$0.22/M output; Claude Haiku 5.5 at \$0.008824/M input and \$0.04412/M output. Local models are unpriced (local compute, not zero cost). No FNR/FPR columns are included; see Table~\ref{tab:rq1_effectiveness} for effectiveness. The action column uses StepShield test.")
lines.append(r"    \end{minipage}")
lines.append(r"\end{table*}")
open(os.path.join(outdir,"rq2-cost-latency.tex"),"w",encoding="utf-8").write("\n".join(lines)+"\n")
for l in lines:
    if "&" in l: print(l)