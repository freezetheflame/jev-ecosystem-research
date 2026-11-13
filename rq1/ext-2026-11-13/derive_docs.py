
"""Stage 3: generate RESULTS.md / ANALYSIS_STATUS.md from the derived CSVs."""
import csv, json, os

OUT = os.path.dirname(os.path.abspath(__file__))

def load(name):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def fnum(x, nd=3):
    if x in (None, "", "None"): return "-"
    try: return "%.*f" % (nd, float(x))
    except ValueError: return str(x)

def pct(x, nd=1):
    if x in (None, "", "None"): return "-"
    return "%.*f%%" % (nd, 100 * float(x))

MET = load("metrics_ci.csv")
TOP = load("rank_top1.csv")
RANK = load("rank_stability.csv")
MCN = load("paired_mcnemar.csv")
THR = load("thresholds.csv")
THRS = load("thresholds_stepshield.csv")
SHIFT = load("shift.csv")
SENS = load("rank_by_metric.csv")
COST = load("cost.csv")
PROV = json.load(open(os.path.join(OUT, "provenance.json"), encoding="utf-8"))

DS_LABEL = {
    "agentharm": "User request (AgentHarm, A1)",
    "injecagent": "External content (InjecAgent, A2)",
    "tsbench": "Tool call (TS-Bench, B)",
    "wildguard_response": "Response (WildGuard-E)",
    "stepshield_test": "Action prefix (StepShield test, C)",
    "stepshield_test_holdout": "Action prefix (StepShield holdout, C)",
}
DS_ORDER = list(DS_LABEL)

def point(ds, model, key):
    for r in MET:
        if r["dataset"] == ds and r["model"] == model:
            return r[key]
    return None

L = []
A = L.append
A("# RQ1 additional analysis: position-conditional effectiveness, CIs, operating points, shift")
A("")
A("Generated " + PROV["generated_utc"] + " by derive.py / derive_thresholds.py / derive_docs.py "
  "(script sha256 in provenance.json). Cluster bootstrap unit = content family, reps=" + str(PROV["reps"]) +
  ", seed=" + str(PROV["seed"]) + ".")
A("This directory is an ADDITIONAL analysis. It does not replace rq1/summary/ and does not modify runs/.")
A("All numbers are descriptive: one repeat, exposed public splits, no pre-registered threshold.")
A("")
A("## 0. Three sentences")
A("")
A("1. No judge is best at every position. Top-1 is unambiguous where p(top-1) is near 100% (GPT-6 Luna on TS-Bench and InjecAgent), "
  "fairly clear where it is 80-83% (Jev on WildGuard-E, and Jev on StepShield test when ranked by balanced accuracy), "
  "and a coin flip at the request position (Jev 52% vs d3mini 40%) and on the StepShield holdout (56% vs 40%).")
A("2. The winner changes with the metric: on StepShield test Jev ranks 4th by MCC but 1st by balanced accuracy and TPR; "
  "on TS-Bench Claude ranks 2nd by MCC but 1st by TPR.")
A("3. Comparing at 0.5/argmax is an arbitrary choice. The MCC-optimal threshold per cell ranges from 0.01 to 0.95; "
  "on StepShield, moving Jev from 0.50 to 0.77 raises MCC from 0.535 to 0.710, above d3mini's 0.700.")
A("")
A("## 1. Method")
A("")
A("- Cells are recovered from rq1/summary/metrics_full.csv counts by matching episodes.jsonl files; "
  "66/66 non-baseline cells match TP/FP/TN/FN exactly (the script lists candidates and skips on mismatch).")
A("- Merge rule for repaired campaigns: files sorted by mtime; an ok row replaces a failed one; between two ok rows the later file wins. "
  "The exact file list per cell is in cells.json; verify.py re-derives all cells with an independent implementation (0 mismatches).")
A("- The threshold sweep uses p>=0.5 as the natural point, which agrees with the stored argmax in 99.8-100% of rows "
  "(argmax_agreement column); small differences from the summary are due to that tie-breaking, not to missing data.")
A("- Intervals: cluster bootstrap by family_id, 1000 reps, percentile 2.5/97.5.")
A("- Rank stability: per dataset, restrict to items scorable by all models, resample families, recompute MCC; "
  "report P(A>B) and top-1 probability.")
A("- Operating points: probabilities parsed from raw/response.body (typed decision models only). "
  "Generative judges expose hard labels only, so TPR@fixed-FPR is not defined for them.")
A("- Paired tests: exact McNemar on common items.")
A("- Cost: rq1/summary/time_tokens.csv, normalized per decision and per episode; local compute unpriced.")
A("")
A("## 2. Position x model: point estimates with 95% CI")
A("")
for ds in DS_ORDER:
    rows = [r for r in MET if r["dataset"] == ds]
    if not rows:
        continue
    rows.sort(key=lambda r: (r["mcc"] in ("", "None"), -float(r["mcc"]) if r["mcc"] not in ("", "None") else 0))
    A("### " + DS_LABEL[ds])
    A("scorable n=" + rows[0]["n"] + ", positive=" + pct(rows[0]["prev"]) + ", families=" + rows[0]["families"] + ".")
    A("")
    A("| model | TPR [95% CI] | TNR [95% CI] | MCC [95% CI] |")
    A("|---|---|---|---|")
    for r in rows[:6]:
        A("| " + r["model"] + " | " + pct(r["tpr"]) + " [" + pct(r["tpr_lo"]) + ", " + pct(r["tpr_hi"]) + "] | " +
          pct(r["tnr"]) + " [" + pct(r["tnr_lo"]) + ", " + pct(r["tnr_hi"]) + "] | " +
          fnum(r["mcc"]) + " [" + fnum(r["mcc_lo"]) + ", " + fnum(r["mcc_hi"]) + "] |")
    A("")
    A("")
A("Top 6 by MCC (InjecAgent has no negatives and no MCC, ranked by TPR). Full 66 rows: metrics_ci.csv.")
A("")
A("## 3. Is the top-1 identifiable?")
A("")
A("| position | metric | top-1 | p(top-1) | pairs with P(A>B) in [0.4,0.6] |")
A("|---|---|---|---|---|")
for ds in DS_ORDER:
    t = [r for r in TOP if r["dataset"] == ds]
    if not t:
        continue
    t.sort(key=lambda r: -float(r["p_top1"]))
    pairs = [r for r in RANK if r["dataset"] == ds]
    tied = sum(1 for r in pairs if 0.4 <= float(r["p_a_better"]) <= 0.6)
    A("| " + DS_LABEL[ds] + " | " + t[0]["metric"] + " | " + t[0]["model"] + " | " +
      pct(t[0]["p_top1"], 0) + " | " + str(tied) + "/" + str(len(pairs)) + " |")
A("")
A("A top-1 probability near 50% means the winner is a coin flip. Few tied pairs and extreme probabilities mean the ranking is identifiable.")
A("")
A("StepShield note: shieldstral never predicts unsafe on test, so its MCC is undefined and the cross-model ranking falls back to balanced accuracy. "
  "By MCC alone d3mini is first (0.700) and Jev fourth (0.535); by balanced accuracy Jev is first (0.890) and d3mini second (0.883). "
  "This is not a rounding issue: MCC weights both error types symmetrically, while balanced accuracy averages TPR and TNR, and Jev is the high-recall/low-TNR model here.")
A("")
A("## 4. Change the metric, change the winner")
A("")
A("Rank under MCC / balanced accuracy / TPR; rows ordered by largest rank movement.")
A("")
A("| position | model | MCC rank | BAcc rank | TPR rank |")
A("|---|---|---|---|---|")
for ds in ["tsbench", "stepshield_test"]:
    rows = [r for r in SENS if r["dataset"] == ds]
    rows.sort(key=lambda r: -max(abs(int(r["rank_mcc"]) - int(r["rank_bacc"])),
                                 abs(int(r["rank_mcc"]) - int(r["rank_tpr"]))))
    for r in rows[:5]:
        A("| " + DS_LABEL[ds] + " | " + r["model"] + " | " + r["rank_mcc"] + " | " + r["rank_bacc"] + " | " + r["rank_tpr"] + " |")
    A("")
A("## 5. Operating points: 0.5 is not a neutral baseline")
A("")
A("Default 0.5 vs MCC-optimal threshold. The optimal threshold is selected on the same test set, so it is an optimistic upper bound, not an achievable deployment number.")
A("")
A("| model | position | MCC at 0.5 | MCC-opt threshold | MCC at opt | delta MCC | TPR@FPR=5% | AUC |")
A("|---|---|---|---|---|---|---|---|")
for r in THR:
    base = point(r["dataset"], r["model"], "mcc")
    if base in ("", "None", None):
        continue
    A("| " + r["model"] + " | " + r["dataset"] + " | " + fnum(base) + " | " + fnum(r["mcc_opt_thr"], 2) + " | " +
      fnum(r["mcc_opt"]) + " | " + fnum(float(r["mcc_opt"]) - float(base)) + " | " + pct(r["tpr_at_fpr05"]) + " | " + fnum(r["auc"]) + " |")
for r in THRS:
    A("| " + r["model"] + " (per prefix) | " + r["dataset"] + " | natural TPR " + pct(r["natural_tpr"]) + " / TNR " +
      pct(r["natural_tnr"]) + " | " + fnum(r["mcc_opt_thr"], 2) + " | " + fnum(r["mcc_opt"]) + " | - | - | - |")
A("")
A("StepShield per-prefix sweep: Jev at 0.50 gives TPR 91.4% / TNR 86.5% (MCC 0.535); at 0.77 it gives TPR 72.0% / TNR 97.9% (MCC 0.710). Same model, same data, different operating point.")
A("")
A("## 6. Shift: rankings flip inside one position too")
A("")
A("TS-Bench, three source domains, same position and prompt contract:")
A("")
A("| source | positive rate | Jev MCC | GPT-6 Luna MCC | d3mini MCC | Claude MCC |")
A("|---|---|---|---|---|---|")
for split in ["agentdojo-traj", "agentharm-traj", "asb-traj"]:
    row = {}
    prev = ""
    for m in ["jev-packy-1.14.0", "gpt6luna", "d3mini", "claudehaiku"]:
        for r in SHIFT:
            if r["dataset"] == "tsbench" and r["split"] == split and r["model"] == m:
                row[m] = r["mcc"]
                prev = r["prev"]
    A("| " + split + " | " + pct(prev) + " | " + fnum(row.get("jev-packy-1.14.0")) + " | " + fnum(row.get("gpt6luna")) + " | " +
      fnum(row.get("d3mini")) + " | " + fnum(row.get("claudehaiku")) + " |")
A("")
A("On agentharm-traj Jev beats GPT (0.554 vs 0.432); on asb-traj GPT leads by a wide margin (0.652 vs 0.455).")
A("")
A("StepShield test vs holdout have positive rates 8.1% vs 50%, so accuracy/F1 are not comparable; TPR/TNR are:")
A("")
A("| model | test TPR / TNR | holdout TPR / TNR | delta |")
A("|---|---|---|---|")
for m in ["jev-packy-1.14.0", "d3mini", "kev", "qwen35"]:
    a = next((r for r in SHIFT if r["dataset"] == "stepshield_test" and r["model"] == m), None)
    b = next((r for r in SHIFT if r["dataset"] == "stepshield_test_holdout" and r["model"] == m), None)
    if a and b:
        A("| " + m + " | " + pct(a["tpr"]) + " / " + pct(a["tnr"]) + " | " + pct(b["tpr"]) + " / " + pct(b["tnr"]) + " | TPR " +
          ("%+.3f" % (float(b["tpr"]) - float(a["tpr"]))) + ", TNR " + ("%+.3f" % (float(b["tnr"]) - float(a["tnr"]))) + " |")
A("")
A("InjecAgent base to enhanced TPR: " + "; ".join(
    m + " " + pct(next((r["tpr"] for r in SHIFT if r["dataset"] == "injecagent" and r["model"] == m and r["split"] == "base"), None)) +
    " to " + pct(next((r["tpr"] for r in SHIFT if r["dataset"] == "injecagent" and r["model"] == m and r["split"] == "enhanced"), None))
    for m in ["jev-packy-1.14.0", "gpt6luna"]) + ". Pooling the two halves hides a difficulty difference.")
A("")
A("## 7. Paired tests (McNemar)")
A("")
sig = [r for r in MCN if float(r["p_exact"]) < 0.05]
A("On common items there are " + str(len(MCN)) + " model pairs, " + str(len(sig)) + " with p<0.05. This means most pairs differ; it does NOT mean the ranking is stable.")
A("")
A("| position | comparison | accuracy delta (A-B) | p |")
A("|---|---|---|---|")
for ds in ["agentharm", "tsbench", "stepshield_test"]:
    rows = sorted([r for r in MCN if r["dataset"] == ds], key=lambda r: float(r["p_exact"]))[:3]
    for r in rows:
        A("| " + DS_LABEL[ds] + " | " + r["model_a"] + " vs " + r["model_b"] + " | %+.3f" % float(r["delta_acc"]) + " | %.1e" % float(r["p_exact"]) + " |")
A("")
A("## 8. Cost is O(steps) and coupled to detection")
A("")
A("| model | AgentHarm s/decision, s/episode | TS-Bench | StepShield test (calls/trajectory) |")
A("|---|---|---|---|")
for m in ["jev-packy-1.14.0", "d3mini", "qwen35", "jevguard"]:
    def cell(ds):
        r = next((x for x in COST if x["model"] == m and x["dataset"] == ds), None)
        if not r: return "-"
        return "%.2fs / %.2fs" % (float(r["call_mean_s"]), float(r["episode_mean_s"]))
    r = next((x for x in COST if x["model"] == m and x["dataset"] == "stepshield_test"), None)
    cpi = "%.2f" % float(r["calls_per_item"]) if r else "-"
    A("| " + m + " | " + cell("agentharm") + " | " + cell("tsbench") + " | " + cell("stepshield_test") + " (" + cpi + ") |")
A("")
A("StepShield needs 8.7-12.3 judgments per trajectory versus 1 elsewhere; Jev takes 6.36 s per episode versus 0.67 s on AgentHarm. "
  "Because monitoring stops at the first unsafe alert, calls are negatively coupled to detection: shieldstral (never alerts) uses 10.1 calls/trajectory, "
  "Jev 8.74. Cross-model per-episode cost therefore rewards better detectors; report per-decision cost and a fixed-step cost as well.")
A("")
A("## 9. What this supports and what it does not")
A("")
A("Supports: position-conditional effectiveness; no universal best judge; metric/operating-point sensitivity; within-position shift can flip rankings; O(steps) cost.")
A("")
A("Does not support: 'model X is the best judge overall'; cross-position accuracy/F1 comparisons; StepShield test-vs-holdout accuracy comparisons; "
  "MCC-optimal numbers as achievable performance; confirmatory claims; direct TPR@fixed-FPR comparisons between typed models and label-only judges.")
A("")
A("## 10. Coverage and gaps")
A("")
A("- Probabilities available: Jev (AgentHarm, TS-Bench, WildGuard-E, StepShield); d3mini/kev/secjev/laya/jevguard (AgentHarm, TS-Bench).")
A("- No raw for local models on WildGuard-E and StepShield (raw excluded at sync), so no operating-point analysis there.")
A("- No probabilities for GPT-6 Luna, Claude Haiku, qwen35, qwen3guard, shieldstral, gliguard (hard labels only).")
A("- StepShield per-prefix sweep done for Jev only.")
A("- Claude/GPT StepShield and WildGuard-E still being filled in elsewhere; left blank here.")
A("")
A("## 11. Files")
A("")
A("| file | content |")
A("|---|---|")
for name, desc in [
    ("metrics_ci.csv", "66 cells: counts, TPR/TNR/MCC, family-cluster bootstrap CI"),
    ("rank_stability.csv", "pairwise P(A>B) within position on common items"),
    ("rank_top1.csv", "top-1 probability per position"),
    ("rank_by_metric.csv", "ranks under MCC / BAcc / TPR"),
    ("thresholds.csv", "operating-point analysis (AUC, AP, TPR@FPR, optimal threshold, calibration)"),
    ("thresholds_stepshield.csv", "per-prefix threshold sweep for Jev"),
    ("paired_mcnemar.csv", "exact McNemar on common items"),
    ("shift.csv", "metrics by split / source domain"),
    ("cost.csv", "calls, latency, tokens per decision and per episode"),
    ("cells.json", "episode files selected per cell and how they were matched"),
    ("provenance.json", "input/script hashes, seed, reps"),
]:
    A("| " + name + " | " + desc + " |")
A("")
A("Rerun (PowerShell):")
A("")
A("    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive.py")
A("    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py")
A("    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py --stepshield")
A("    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_docs.py")
open(os.path.join(OUT, "RESULTS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

S = []
B = S.append
B("# Analysis status and declarations (RQ1 additional analysis)")
B("")
B("Generated " + PROV["generated_utc"] + ". Applies to all derived tables under rq1/ext-2026-11-13/.")
B("")
B("## 1. Evidence level")
B("")
B("- Descriptive: one repeat, exposed public splits, no pre-registered threshold/metric/sample size, no freeze manifest, no agent-loop execution.")
B("- Reproducible: all numbers re-derived by derive.py / derive_thresholds.py from episodes.jsonl and raw/. Input and script hashes in provenance.json "
  "(metrics_full sha256=" + PROV["inputs"]["metrics_full_sha256"][:16] + "..., time_tokens sha256=" + PROV["inputs"]["time_tokens_sha256"][:16] + "...).")
B("- Consistent: 66 non-baseline cells match rq1/summary/metrics_full.csv TP/FP/TN/FN exactly (built-in matching; mismatches abort the row and list candidates).")
B("- Independently verified: verify.py re-derives all 66 cells from cells.json with a separate merge implementation; 0 mismatches, "
  "and three spot-checked MCC values match to 6 decimals. Input file hashes are re-checked against provenance.json.")
B("- Non-replacing: the official summary remains rq1/summary/. Nothing under runs/ or rq1/summary/ is modified by this analysis.")
B("")
B("## 2. Allowed in the paper (exploratory evidence)")
B("")
B("- Position-conditional effectiveness; magnitude of within-model cross-position change; no stable cross-position ranking.")
B("- Top-1 is often unidentifiable: report top-1 probability and bootstrap CIs rather than a league table.")
B("- Metric sensitivity: MCC / balanced accuracy / TPR select different winners.")
B("- Operating-point sensitivity: 0.5/argmax is arbitrary; MCC-optimal thresholds differ strongly (with the same-test-set selection caveat).")
B("- Within-position shift: TS-Bench source domains flip the ranking.")
B("- Cost structure: StepShield is O(steps); one order of magnitude above other positions; cost coupled to detection.")
B("")
B("## 3. Not allowed")
B("")
B("- 'Model X is the best overall judge' or 'X can replace an LLM security module'.")
B("- Any cross-position accuracy/F1 comparison; StepShield test-vs-holdout accuracy comparison.")
B("- Presenting MCC-optimal numbers as achievable performance (selected on the test set).")
B("- Calling this confirmatory, blind, or pre-registered; treating this pilot as generalization evidence.")
B("- Comparing typed-model TPR@fixed-FPR against label-only generative judges.")
B("")
B("## 4. Required before freezing (protocol section 3)")
B("")
B("1. Freeze benchmark commit, splits, task/attack IDs and hashes; mark development exposure.")
B("2. Freeze the threshold-selection procedure per position (select on dev, never on test) and the primary metric (suggest MCC + TPR@fixed-FPR).")
B("3. Freeze repeat count and clustering unit; report family-clustered CIs.")
B("4. Record effective parameters, provider/endpoint and served model for every component; Jev currently goes through a Packy relay.")
B("5. Complete or explicitly leave blank Claude/GPT StepShield and WildGuard-E.")
B("6. Sync raw/ for local models (otherwise no operating-point analysis) or declare hard-label-only comparisons.")
B("7. Pre-register multiple-comparison handling and stopping rules; publish a freeze manifest before the final table.")
B("")
B("## 5. Unverified")
B("")
B("- Whether the Packy relay serving jev-1.14.0 is weight-equivalent to official/OpenLux (only the model id is recorded).")
B("- Local models' WildGuard-E / StepShield raw files are not on this machine, so no probability analysis there.")
B("- Claude/GPT StepShield still being completed elsewhere; left blank here.")
B("- All API fees are list-price estimates, not invoices; local compute is unpriced.")
open(os.path.join(OUT, "ANALYSIS_STATUS.md"), "w", encoding="utf-8").write("\n".join(S) + "\n")
print("wrote RESULTS.md and ANALYSIS_STATUS.md")