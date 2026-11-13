
import csv, json, os, shutil, math

ROOT = r"D:\projects\jev_research"
RQ1 = os.path.join(ROOT, "rq1")
EXT = os.path.join(RQ1, "ext-2026-11-13")
ARCH = os.path.join(RQ1, "architecture-2026-11-13")
SUM = os.path.join(RQ1, "summary")
OUT = os.path.join(RQ1, "handoff-2026-11-13")
DATA = os.path.join(OUT, "data")
os.makedirs(DATA, exist_ok=True)

def load(p):
    with open(p, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))

MET = load(os.path.join(EXT, "metrics_ci.csv"))
FULL = load(os.path.join(SUM, "metrics_full.csv"))
TOP = load(os.path.join(EXT, "rank_top1.csv"))
SENS = load(os.path.join(EXT, "rank_by_metric.csv"))
SHIFT = load(os.path.join(EXT, "shift.csv"))
COST = load(os.path.join(EXT, "cost.csv"))
THR = load(os.path.join(EXT, "thresholds.csv"))
THRS = load(os.path.join(EXT, "thresholds_stepshield.csv"))
TT = load(os.path.join(SUM, "time_tokens.csv"))

DS_LABEL = {
 "agentharm": "User Request（AgentHarm）",
 "injecagent": "External Content（InjecAgent）",
 "tsbench": "Tool Call（TS-Bench）",
 "wildguard_response": "Response（WildGuard-E）",
 "stepshield_test": "In-flight Action（StepShield test）",
 "stepshield_test_holdout": "In-flight Action（StepShield holdout）",
}
ORDER = list(DS_LABEL)

def f3(x):
    try: return "%.3f" % float(x)
    except: return "—"
def pct(x):
    try: return "%.1f%%" % (100*float(x))
    except: return "—"

def metrow(ds, model):
    for r in MET:
        if r["dataset"] == ds and r["model"] == model:
            return r
    return None

def top1(ds):
    rows = [r for r in TOP if r["dataset"] == ds]
    rows.sort(key=lambda r: -float(r["p_top1"]))
    return rows[:3]

# ---------- RQ1 ----------
L = []
A = L.append
A("# RQ1：五个检查位置上的判官有效性（数据与结果）")
A("")
A("## 1. 问题与单位")
A("")
A("RQ1：在同一个执行链的不同检查位置上，12 种判官配置的有效性与错误方向如何变化？")
A("")
A("单位：request / item / step / trajectory / response（见 data-index.csv 与 position-mapping 文档）。")
A("所有指标为描述性：1 次 repeat、公开已暴露 split、阈值未预注册。")
A("")
A("## 2. 数据构成")
A("")
A("| 位置 | 数据集 | 可判分 n | 正类比例 | 内容族数 |")
A("|---|---|---:|---:|---:|")
for ds in ORDER:
    r = metrow(ds, "jev-packy-1.14.0")
    if r:
        A("| " + DS_LABEL[ds] + " | " + ds + " | " + r["n"] + " | " + pct(r["prev"]) + " | " + r["families"] + " |")
A("")
A("注：InjecAgent 全正类，MCC 无定义，只报 TPR；TS-Bench 的 1,781 条 gold=0.5 争议项不进二分类分母。")
A("")
A("## 3. 每位置前三名（MCC，括号内为族聚类 bootstrap 95% CI）")
A("")
A("| 位置 | 第 1 | 第 2 | 第 3 |")
A("|---|---|---|---|")
for ds in ORDER:
    cells = []
    if ds == "injecagent":
        rows = [r for r in MET if r["dataset"] == ds and r["tpr"] not in ("", "None")]
        rows.sort(key=lambda r: -float(r["tpr"]))
        for r in rows[:3]:
            cells.append(r["model"] + " TPR " + pct(r["tpr"]))
        label = DS_LABEL[ds] + "（按 TPR；MCC 无定义）"
    else:
        rows = [r for r in MET if r["dataset"] == ds and r["mcc"] not in ("", "None")]
        rows.sort(key=lambda r: -float(r["mcc"]))
        for r in rows[:3]:
            cells.append(r["model"] + " " + f3(r["mcc"]) + " [" + f3(r["mcc_lo"]) + ", " + f3(r["mcc_hi"]) + "]")
        label = DS_LABEL[ds]
    while len(cells) < 3: cells.append("—")
    A("| " + label + " | " + cells[0] + " | " + cells[1] + " | " + cells[2] + " |")
A("")
A("## 4. 第一名是否可识别")
A("")
A("| 位置 | 排名指标 | 第一名 | top-1 概率 |")
A("|---|---|---|---:|")
for ds in ORDER:
    t = top1(ds)
    if t:
        A("| " + DS_LABEL[ds] + " | " + t[0]["metric"] + " | " + t[0]["model"] + " | " + pct(t[0]["p_top1"]) + " |")
A("")
A("top-1 概率接近 50% 表示“第一名”只是掷硬币；AgentHarm 与 StepShield holdout 属于这种情况。InjecAgent 的 100% 只是“正例全部被检出”的平凡结果，不代表可识别性。")
A("")
A("## 5. 指标敏感性（换指标换冠军）")
A("")
A("| 位置 | 模型 | MCC 名次 | BAcc 名次 | TPR 名次 |")
A("|---|---|---|---|---|")
for ds in ["tsbench", "stepshield_test"]:
    rows = [r for r in SENS if r["dataset"] == ds]
    rows.sort(key=lambda r: int(r["rank_mcc"]))
    for r in rows:
        A("| " + DS_LABEL[ds] + " | " + r["model"] + " | " + r["rank_mcc"] + " | " + r["rank_bacc"] + " | " + r["rank_tpr"] + " |")
A("")
A("最典型：StepShield test 上 Jev 按 MCC 第 4、按 balanced accuracy 第 1；TS-Bench 上 Claude 按 MCC 第 2、按 TPR 第 1。")
A("")
A("## 6. 位置内部的分布迁移")
A("")
A("TS-Bench 三个来源域（同位置、同合同）：")
A("")
A("| 来源 | 正类比例 | Jev MCC | GPT-6 Luna MCC | Claude MCC |")
A("|---|---:|---:|---:|---:|")
for s in ["agentdojo-traj", "agentharm-traj", "asb-traj"]:
    row = {}; prev = ""
    for m in ["jev-packy-1.14.0", "gpt6luna", "claudehaiku"]:
        for r in SHIFT:
            if r["dataset"] == "tsbench" and r["split"] == s and r["model"] == m:
                row[m] = r["mcc"]; prev = r["prev"]
    A("| " + s + " | " + pct(prev) + " | " + f3(row.get("jev-packy-1.14.0")) + " | " + f3(row.get("gpt6luna")) + " | " + f3(row.get("claudehaiku")) + " |")
A("")
A("agentharm-traj 上 Jev 反超 GPT；asb-traj 上 GPT 大幅领先——所以“LLM 更强”是来源依赖的。")
A("")
A("## 7. 写论文前必须补的数据/声明")
A("")
A("1. Frozen protocol：样本、阈值、指标、停止规则；当前全部是 descriptive。")
A("2. 逐条目预测（LLM 的 Claude/GPT 在 StepShield 上）用于配对 McNemar；当前只有聚合指标。")
A("3. 聚类 CI 已做（family bootstrap），但需在论文中说明族数与设计效应。")
A("4. InjecAgent 需要配对负例才能报 FPR；或者明确只报检出率。")
A("5. position mapping 的 unit/attacker/label 限定必须写进表。")
A("")
open(os.path.join(OUT, "RQ1-data.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------- RQ2 ----------
L = []
A = L.append
A("# RQ2：成本与效率（数据与结果）")
A("")
A("## 1. 问题与口径")
A("")
A("RQ2：在满足既定安全/效用要求时，引入判官组件的现金成本、延迟与调用量是多少？何时值得？")
A("")
A("口径：API 费用为 list-price 估算（非账单）；本地计算未计价；延迟取成功 episode 的客户端墙钟；")
A("分别报每判定（per decision）与每 episode（per trajectory），因为 StepShield 是 O(steps)。")
A("")
A("## 2. 每位置成本结构（选 4 个代表模型）")
A("")
A("| 模型 | 位置 | 调用/条目 | 单次调用均时 | episode 均时 | 输入 token/条目 |")
A("|---|---|---:|---:|---:|---:|")
for m in ["jev-packy-1.14.0", "d3mini", "gpt6luna", "claudehaiku"]:
    for ds in ["agentharm", "tsbench", "stepshield_test"]:
        r = next((x for x in COST if x["model"] == m and x["dataset"] == ds), None)
        if not r: continue
        A("| " + m + " | " + DS_LABEL[ds] + " | " + f3(r["calls_per_item"]) + " | " + f3(r["call_mean_s"]) + " s | " + f3(r["episode_mean_s"]) + " s | " + str(int(float(r["in_tokens_per_item"]))) + " |")
A("")
A("关键：StepShield 每轨迹 8.7–10.1 次判断（cost.csv；部分旧 run 到 12.3），其他位置 1 次；O(steps) 是成本结构的主因。")
A("")
A("缺口：Claude/GPT 的 StepShield 行在 cost.csv 与 time_tokens.csv 为空，未列入；需要补跑或标 N/A，不能用别的行替代。")
A("")
A("## 3. 成本与检出耦合")
A("")
A("“每轨迹首个 unsafe 后停止”意味着检出越好调用越少：")
A("")
A("| 模型 | StepShield test 调用/轨迹 | TPR |")
A("|---|---:|---:|")
pairs = []
for m in ["shieldstral", "qwen3guard", "qwen35", "kev", "d3mini", "laya", "secjev", "gliguard", "jev-packy-1.14.0", "jevguard"]:
    c = next((x for x in COST if x["model"] == m and x["dataset"] == "stepshield_test"), None)
    t = next((x for x in MET if x["model"] == m and x["dataset"] == "stepshield_test"), None)
    if c and t: pairs.append((m, float(c["calls_per_item"]), float(t["tpr"])))
pairs.sort(key=lambda x: -x[1])
for m, cpi, tpr in pairs:
    A("| " + m + " | " + f3(cpi) + " | " + pct(tpr) + " |")
A("")
A("读法：从不告警的 shieldstral 调用最多（10.1/轨迹），Jev 8.74；跨模型比每 episode 成本会奖励好模型。")
A("")
A("## 4. 操作点也是成本（同一模型不同阈值）")
A("")
A("| 模型 | 位置 | 默认阈值 MCC | MCC 最优阈值 | 最优阈值下 MCC | TPR@FPR=5% | AUC |")
A("|---|---|---|---:|---|---:|---:|")
for r in THR:
    base = metrow(r["dataset"], r["model"])
    if not base or base["mcc"] in ("", "None"): continue
    A("| " + r["model"] + " | " + r["dataset"] + " | " + f3(base["mcc"]) + " | " + f3(r["mcc_opt_thr"]) + " | " + f3(r["mcc_opt"]) + " | " + pct(r["tpr_at_fpr05"]) + " | " + f3(r["auc"]) + " |")
for r in THRS:
    A("| " + r["model"] + "（逐前缀） | " + r["dataset"] + " | TPR " + pct(r["natural_tpr"]) + " / TNR " + pct(r["natural_tnr"]) + " | " + f3(r["mcc_opt_thr"]) + " | " + f3(r["mcc_opt"]) + " | — | — |")
A("")
A("StepShield 上 Jev 0.50→0.77：MCC 0.535→0.710——同一模型、同一数据，只换操作点。")
A("")
A("## 5. 写论文前必须补的数据")
A("")
A("1. 价格快照：Jev 列表价 0.042 USD/M 输入；GPT/Claude 的 relay 价目表未记录；本地计算未计价。")
A("2. 主 Agent 与 reviewer 的成本/延迟需分列；当前只有判官组件。")
A("3. 等调用数对照（Jev vs LLM judge）与等成本对照。")
A("4. 真实账单 vs 估算：当前全部是估算。")
A("5. 延迟来源（网络/队列/推理）未拆分。")
A("")
open(os.path.join(OUT, "RQ2-data.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------- README ----------
L = []
A = L.append
A("# RQ1/RQ2 审阅包（2026-11-13）")
A("")
A("给学长审阅用：一页结论 + 数据清单 + 补充 insight。全部数字来自仓库内可复现产物；本包不修改正式汇总。")
A("")
A("## 1. 三分钟结论")
A("")
A("**RQ1（五位置 × 12 判官）**")
A("- 没有通吃的判官：AgentHarm 上 Jev top-1 概率 52%（d3mini 40%），StepShield holdout 56% vs 40%，都是掷硬币。")
A("- 可识别的第一名只有三处：TS-Bench（GPT-6 Luna 100%）、Response（Jev 80%）、StepShield test（Jev 83%，按 balanced accuracy）；InjecAgent 的 100% 是正例检测的平凡结果。")
A("- 换指标就换冠军：StepShield test 上 Jev 按 MCC 第 4、按 balanced accuracy 第 1。")
A("- 位置内部也会翻转：TS-Bench 的 agentharm-traj 上 Jev 反超 GPT，asb-traj 上 GPT 大幅领先。")
A("")
A("**RQ2（成本与效率）**")
A("- 成本结构是 O(steps)：StepShield 每轨迹 8.7–10.1 次判断，其他位置 1 次；Jev 6.36 s/episode vs AgentHarm 0.67 s。")
A("- 0.5/argmax 不是中立基准：MCC 最优阈值从 0.01 到 0.95；Jev 在 StepShield 上 0.50→0.77 使 MCC 从 0.535 升到 0.710。")
A("- 成本与检出耦合：从不告警的模型调用最多；跨模型比每 episode 成本会奖励好模型。")
A("")
A("**补充 insight（不在 RQ1/RQ2 主表，但决定结论强度）**")
A("- ConstraintGuard 只覆盖 12.9% 的任务约束；覆盖子集上 CG 召回 100% 但 FPR 100%，CCD 同召回 FPR 5.3%。")
A("- CCD（轨迹分解）补回 prefix 漏检的 44/55（80%），新增误报 3/55（5.5%）；TS-Bench 单步口径下分解无显著收益。")
A("- 五位置映射有 unit/attacker/label 三类不可比，必须写进论文表。")
A("")
A("## 2. 文件")
A("")
A("| 文件 | 内容 |")
A("|---|---|")
A("| RQ1-data.md | RQ1 数据构成、每位置前三、可识别性、指标敏感性、来源迁移、缺口 |")
A("| RQ2-data.md | RQ2 成本结构、O(steps)、操作点成本、检出耦合、缺口 |")
A("| SUPPLEMENTARY-INSIGHTS.md | 其他文件夹里的补充 insight（阈值/MCC/CG/CCD/TS-Bench/位置映射） |")
A("| data/ | 关键表副本（metrics_ci、metrics_full、time_tokens、thresholds、shift、cost、rank_*） |")
A("| data-index.csv | 每个数据文件的路径、口径、状态 |")
A("")
A("## 3. 请学长重点把关的五件事")
A("")
A("1. RQ1 的主表是否应按位置分栏、用 MCC + matched-FPR recall 双指标（避免 MCC 掩盖召回）。")
A("2. “第一名不可识别”是否足以支撑论文的核心 claim（还需要冻结协议/更多样本？）。")
A("3. InjecAgent 的 positives-only 与位置映射的 unit/attacker 限定，是否按当前写法可接受。")
A("4. RQ2 是否应降级为“成本结构”而非“成本结论”（价格快照、主 Agent/reviewer 成本仍缺）。")
A("5. 补充 insight 是否进正文（CG 基线、CCD、TS-Bench 负结果），还是放附录。")
A("")
A("## 4. 已知限制（务必随包转发）")
A("")
A("- 全部为 descriptive：1 次 repeat、公开已暴露 split、无 freeze manifest、无预注册。")
A("- 个别人工/自动口径未统一：LLM 判官无概率，只能 native 点；本地模型未计价。")
A("- 部分 cell 仍在补（Claude/GPT 的 WildGuard-E；Claude/GPT 的 StepShield 成本行在 time_tokens/cost 为空）。")
A("- RQ1 的 CI 是按内容族 bootstrap 的（1000 次），跨族设计效应未额外建模。")
A("")
open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------- SUPPLEMENTARY ----------
L = []
A = L.append
A("# 补充 insight（来自其他文件夹，按相关性排序）")
A("")
A("这些分析不属于 RQ1/RQ2 主表，但决定了主表结论能不能站住；每条给出处。本包 insights/ 下附了原文副本，仓库路径一并保留。")
A("")
A("| # | Insight | 一句话结论 | 出处 |")
A("|---|---|---|---|")
A("| 1 | 操作点敏感性 | 0.5/argmax 不是中立基准；MCC 最优阈值 0.01–0.95；Jev StepShield 0.50→0.77 使 MCC 0.535→0.710 | rq1/ext-2026-11-13/thresholds.csv, thresholds_stepshield.csv |")
A("| 2 | 排名不可识别性 | 多数位置 top-1 概率 52–56%，是掷硬币；只有 TS-Bench 与 StepShield test 可识别 | rq1/ext-2026-11-13/rank_top1.csv, rank_stability.csv |")
A("| 3 | 指标敏感性 | MCC / BAcc / TPR 给出不同冠军；单指标排名不可用 | rq1/ext-2026-11-13/rank_by_metric.csv |")
A("| 4 | 来源迁移 | TS-Bench 三来源排名翻转；StepShield test vs holdout 是 8.1% vs 50% prevalence，acc/F1 不可比 | rq1/ext-2026-11-13/shift.csv |")
A("| 5 | MCC 对照 | 全 test：GPT .5805 > CCD 组合 .543–.552 > prefix .536 > Claude .414 > CG+ .266 > CG −.033 | rq1/architecture-2026-11-13/MCC-TABLE.md |")
A("| 6 | ConstraintGuard 基线 | 覆盖率 12.9%，69% 任务零覆盖；覆盖子集 CG 100%/100% vs CCD 100%/5.3%；CG 叠加 CCD 只增 FP | rq1/architecture-2026-11-13/BASELINE-CONSTRAINTGUARD.md |")
A("| 7 | CCD 轨迹分解 | 补回 prefix 漏检 44/55（80%），新增 FP 3/55（5.5%）；组合 recall 91.4%→96.7%（@.75），FPR 13.2%→14.8% | rq1/architecture-2026-11-13/RESULTS-PILOT.md |")
A("| 8 | TS-Bench 诊断 | Jev 的原始差距一半是操作点；剩余集中在 ASB 合成轨迹；AgentHarm-traj 上 Jev 赢 GPT | rq1/architecture-2026-11-13/TS-BENCH-RESULT.md |")
A("| 9 | TS-CCD 负结果 | 单步口径下探针分解无显著收益（AUC CI 含 0，McNemar p=0.54）；轨迹口径尚未测 | rq1/architecture-2026-11-13/TS-BENCH-RESULT.md |")
A("| 10 | 位置映射限定 | 五位置是五类适配数据，unit/attacker/label 不同；StepShield 应改名 In-flight/Prefix monitoring | paper/review/position-mapping-2026-11-13.md |")
A("")
A("## 与 RQ3 的关系")
A("")
A("CCD、ConstraintGuard、TS-CCD 这些属于 RQ3（攻击/架构），不在 RQ1/RQ2 主表；但 CG 基线是 RQ1 的必要对照，CCD 是 RQ3 的主线。")
A("")
open(os.path.join(OUT, "SUPPLEMENTARY-INSIGHTS.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------- data copies ----------
copies = [
 (os.path.join(EXT,"metrics_ci.csv"), "metrics_ci.csv"),
 (os.path.join(SUM,"metrics_full.csv"), "metrics_full.csv"),
 (os.path.join(SUM,"time_tokens.csv"), "time_tokens.csv"),
 (os.path.join(EXT,"thresholds.csv"), "thresholds.csv"),
 (os.path.join(EXT,"thresholds_stepshield.csv"), "thresholds_stepshield.csv"),
 (os.path.join(EXT,"rank_top1.csv"), "rank_top1.csv"),
 (os.path.join(EXT,"rank_by_metric.csv"), "rank_by_metric.csv"),
 (os.path.join(EXT,"shift.csv"), "shift.csv"),
 (os.path.join(EXT,"cost.csv"), "cost.csv"),
]
for src,dst in copies:
    if os.path.exists(src): shutil.copy2(src, os.path.join(DATA,dst))

# data index
L = []
A = L.append
A("file,role,unit,status")
rows = [
 ("data/metrics_ci.csv","RQ1 主表：TP/FP/TN/FN + TPR/TNR/MCC + 族聚类 CI","cell","derived; descriptive"),
 ("data/metrics_full.csv","正式汇总全指标（含 acc/F1/EIR/IG）","cell","official summary snapshot"),
 ("data/time_tokens.csv","RQ2 时间/token 汇总","cell","derived; local unpriced"),
 ("data/thresholds.csv","操作点分析（AUC/TPR@FPR/最优阈值）","cell","exploratory; post-hoc"),
 ("data/thresholds_stepshield.csv","Jev 逐前缀阈值扫描","cell","exploratory; post-hoc"),
 ("data/rank_top1.csv","各位置 top-1 概率","position","derived"),
 ("data/rank_by_metric.csv","MCC/BAcc/TPR 三种口径名次","position","derived"),
 ("data/shift.csv","按来源/split 的指标","split","derived"),
 ("data/cost.csv","每判定/episode 调用、时延、token","cell","derived; estimates flagged"),
]
for r in rows: A(",".join(r))
open(os.path.join(OUT,"data-index.csv"),"w",encoding="utf-8").write("\n".join(L)+"\n")
# copies of insight docs
INS = os.path.join(OUT, "insights")
os.makedirs(INS, exist_ok=True)
for src, dst in [
 (os.path.join(ARCH, "MCC-TABLE.md"), "MCC-TABLE.md"),
 (os.path.join(ARCH, "BASELINE-CONSTRAINTGUARD.md"), "BASELINE-CONSTRAINTGUARD.md"),
 (os.path.join(ARCH, "RESULTS-PILOT.md"), "RESULTS-PILOT.md"),
 (os.path.join(ARCH, "TS-BENCH-RESULT.md"), "TS-BENCH-RESULT.md"),
 (os.path.join(ROOT, "paper", "review", "position-mapping-2026-11-13.md"), "position-mapping.md"),
]:
    if os.path.exists(src): shutil.copy2(src, os.path.join(INS, dst))

# adjusted summary for review
SUM_L = []
S = SUM_L.append
S("# RQ1/RQ2 总结（对外审阅版，2026-11-13）")
S("")
S("这份总结只做两件事：把 12 判官 × 5 位置的结果压成可判断的结论；把结论成立所依赖的限定写清楚。")
S("正式表格与逐格数字见 rq1/summary/metrics_full.csv；完整审阅包见 rq1/handoff-2026-11-13/。")
S("")
S("## 一句话")
S("")
S("**RQ1：没有通吃的判官；多数位置的“第一名”不可识别，换指标会换冠军。RQ2：成本结构由 O(steps) 决定，操作点选择与成本同等重要。**")
S("")
S("## RQ1：有效性")
S("")
S("1. 五位置第一名：AgentHarm=Jev（MCC .769，但 top-1 概率 52%）、InjecAgent=GPT（TPR 100%，正例检测平凡）、TS-Bench=GPT（MCC .699，100%）、WildGuard-E=Jev（MCC .746，80%）、StepShield test=Jev（BAcc 最高，83%）、StepShield holdout=Jev（MCC .847，56%）。")
S("2. 只有 TS-Bench、WildGuard-E、StepShield test 三个位置的第一名可识别；AgentHarm 与 StepShield holdout 是掷硬币。")
S("3. 指标敏感性是结构性的：StepShield test 上 Jev 按 MCC 第 4、按 BAcc 第 1；TS-Bench 上 Claude 按 MCC 第 2、按 TPR 第 1。")
S("4. 位置内部会迁移：TS-Bench 的 agentharm-traj 上 Jev 反超 GPT；StepShield test 8.1% vs holdout 50% prevalence，acc/F1 不可比。")
S("")
S("## RQ2：成本与效率")
S("")
S("1. 成本结构 O(steps)：StepShield 每轨迹 8.7–10.1 次判断，其他位置 1 次；Jev 6.36 s/episode vs AgentHarm 0.67 s。")
S("2. 操作点是成本：MCC 最优阈值 0.01–0.95；Jev StepShield 0.50→0.77 使 MCC .535→.710。")
S("3. 成本与检出耦合：不告警的模型调用最多；跨模型比每 episode 成本会奖励好模型。")
S("4. 缺口：Claude/GPT 的 StepShield 成本行未记录；价格快照与主 Agent/reviewer 成本未拆。")
S("")
S("## 能写 / 不能写")
S("")
S("能写：五位置描述性对比、排名不可识别性、指标敏感性、O(steps) 成本结构、操作点效应。")
S("不能写：谁是“最佳判官”、跨位置总分、部署成本结论、任何 confirmatory 声明。")
S("")
S("## 必补")
S("")
S("1. 冻结协议（样本/阈值/指标/停止规则）。2. Claude/GPT 的 StepShield 逐条预测与成本。3. InjecAgent 配对负例或明确只报检出率。4. 位置映射的 unit/attacker/label 限定。")
open(os.path.join(SUM, "SUMMARY-2026-11-13.md"), "w", encoding="utf-8").write("\n".join(SUM_L) + "\n")
print("handoff docs written")