# RQ v2 evidence audit — 2026-11-12

Auditor: evidence-auditor (read-only). Check time 2026-11-12 02:38–03:05 Asia/Shanghai. Method: inspected derived summaries, manifests, effective configs, campaign logs and docs; **no model/API calls, no raw JSONL dumps**; numbers copied from existing derived artifacts, not recomputed. Labels: *measured* = recorded wall-clock/usage in runs; *estimated* = repo list-price/price-estimate fields; *unpriced* = local compute (protocol says unpriced by default). 209 derived group rows were scanned across `data/agent-security-study/runs/`: **all are `"phase":"pilot"`; none has a scorable agent episode (`episode_results.scorable=0`); no `traces/` directory exists.**

**Bottom line.** The repo has a large *descriptive pilot* campaign, but no frozen/confirmatory run, no agent-loop execution, no ATBench D run, and no robustness experiment. RQ1 is partially answerable at the component-classification level; RQ2 only descriptively; RQ3 and RQ4 require new runs. The paper draft itself says isolated classification "cannot determine which outcome occurs during execution" (`paper/main.tex:36`), which bounds every current result below.

## 1. Verdict per proposed RQ

| RQ | Verdict | Evidence in repo today (all pilot) | Exact missing cells |
|---|---|---|---|
| RQ1 effectiveness as security judges | **Partially answerable (component-level only)** | AgentHarm A1 416×1 for 12 models; InjecAgent A2 2108×1 for 12 (positives only); TS-Bench B 7182×1 for Jev/GPT/Claude + Gliguard 1129; WildGuard A1 1725 for 11; WildGuard E 1725 for Jev | ATBench D (n=2 smoke); TS-Bench for 8 local models + Jev-Guard; StepShield complete 12-model table; WildGuard E for 11 models; agent-loop utility/ASR = zero |
| RQ2 runtime efficiency & cost | **Descriptively only; comparative claim inadmissible** | Per-call/per-episode p50/p95 + usage/cost fields for pilots and full cells; API fee estimates only for Jev/GPT/Claude | Measured bills; local compute pricing; same-hardware controlled track; main-agent+reviewer+retry task-level cost; equal-call-count comparisons |
| RQ3 robustness under attack | **Not answerable — requires new runs** | Historical Jev-only JevOut pilots (8 items; 40 items; 2/32 iterative flips, semantic validity unconfirmed; Jev **1.13.0**, MMLU-Pro, not these benchmarks) | Any perturbation/adaptive/threshold attack on the 12-model matrix or 4 benchmarks; clean-correct conditioning; attack budget; frozen protocol |
| RQ4 effect of configurations | **Descriptive post-hoc only; no causal design** | Levels actually observed (see §6): model class, wrapper/contract, thresholds, repeats, retry policy, provider, hardware | Crossed/factorial manipulation; per-model `type`/`criteria`/`temperature` ablations; pre-registered factor levels |

## 2. Status per benchmark

| Benchmark (Mode) | Dataset n / gold | Executed runs | Models completed | n per model | Phase label | Primary evidence |
|---|---|---|---|---|---|---|
| AgentHarm **A1** | 416: validation 64 (32/32), test_public 352 (176/176); 52 families (8+44) | 12 models × full 416 × 1 repeat **plus** 12-model 50-item ×3 pilot (25/25, 8 families) | 12/12 full | 416 (val 64, test 352) | pilot, exposed public data, not frozen | `runs/full-api-jev-packy-v1/jev/agentharm`, `runs/full-api-agentharm-{claude,gpt}-v5`, `runs/full-local-agentharm-v1`, `summary/agentharm/README.md` |
| InjecAgent **A2** | 2108 (base 1054 + enhanced 1054); **all gold=1, zero native negatives**; 2108 "families" (no clustering) | 12 models × 2108 × 1 | 12/12 | 2108 | pilot | `runs/full-api-jev-packy-v1/jev/injecagent`, `runs/full-api-wg-injec-tsbench-v1/*/injecagent`, `runs/full-local-injecagent-v1` |
| TS-Bench **B** | 7182 steps (safe 3770 / unsafe 1631 / controversial 1781); 3376 families; splits 731/1220/5231 | Jev, GPT, Claude full 7182; Gliguard partial (latest 1129 recorded); 8 local models + Jev-Guard not started | 3/12 complete, 1 partial | Jev/GPT/Claude 7182 planned; binary-valid N=416/1220/3765 per split | pilot | `runs/full-api-jev-packy-v1/jev/tsbench`, `runs/full-api-tsbench-v1`, `runs/full-local-wildguard-tsbench-v1/gliguard/tsbench` |
| ATBench **D** | 1000 (503 safe / 497 unsafe); long views median ~7.5k, p95 ~26k, max ~365k chars | Only smoke n=2 (`2026-10-30-smoke-02`: 1 TN, 1 FN); `smoke-01` failed HTTP 451 | **0/12** | 2 | smoke only; no long-context/truncation policy frozen | `docs/model-evaluation/2026-10-30-aabd-adaptation.md` §8; `runs/2026-10-30-smoke-02` |
| StepShield **C** (exists, outside stated 4) | 8151 (test 7935 / holdout 216; 747 rogue / 7404 non-rogue); 8143 families; up to 83194 prefix calls/model | Claude: 4719/8151 in `full-api-stepshield-v1` + continuations (1510+4+1919 planned, no merged analysis); Jev: episodes complete 8151 (8149 ok / 2 InterruptedError) but **no `analysis/` (report.py TypeError)**; GPT/local StepShield absent from repo | 0 complete | Claude 4591 test + 127 holdout scored | pilot/partial | `runs/full-api-stepshield-v1`, `…-cont*-v1`, `runs/full-api-jev-packy-v1/jev/stepshield` |
| WildGuardTest **A1** (exists) | 1725 (prompt_harm 754/945/26) | 11 models × 1725 × 1 (no Jev) | 11/12 | 1725 | pilot | `runs/full-api-wg-injec-tsbench-v1`, `runs/full-local-wildguard-tsbench-v1/*/wildguardtest` |
| WildGuardTest **E** (exists) | 1725 (response_harm 284/1425/16) | Jev only, finished 2026-11-12 02:18 CST | 1/12 | 1725 (N=1709 valid) | pilot | `runs/full-api-jev-packy-v1/jev/wildguardtest-response` |

Note: the RQ-v2 four-benchmark framing (A1/A2/B/**D**) is **not** the set the campaign ran (A1/A2/B/**C/E**). ATBench was re-assigned D→excluded on 2026-11-10; "C 暂时空缺" was replaced by StepShield, and WildGuard A1/E coexist as two contracts on one file (`docs/model-evaluation/agent-security-evaluation-modes.md`:62–74).

## 3. Model roster and the category problem

The 12 runs are **not one comparable judge category**. Evidence: the selection doc's own `类别` column labels them 决策模型 / 通用 LLM / 专用安全模型 (`docs/model-evaluation/2026-10-27-study-selection.md` §1), and the model-selection design doc groups A "专用决策模型", B "通用 LLM", C "专用安全判别器" and states these judge classes differ in task and interface (`docs/model-evaluation/empirical-study-model-selection.md`). Jev-Guard is described as a *system* (policy tree + execution gate) and only its safety-only head was run (`docs/model-evaluation/2026-11-03-jevguard-agentharm.md`).

| Model key | Category (per repo docs) | Deployment / route | Request & output contract (effective) | Priced? | Cells run |
|---|---|---|---|---|---|
| jev | typed decision model (System One, closed API) | OpenLux relay (pilot); **Packy relay** (full campaign) | `/v1/systemone` choice safe/unsafe; server defaults unknown | OpenLux est. 0.0168/M in; Packy overlay 0.042/M in (budget-stop est., 7× multiplier note); output 0 | A1, A2, B, C (unscored), E |
| d3mini | open decision model (vLLM-SR) | local WSL, port 8014, BF16 | native choice; context 262144; load-bearing params none | unpriced | A1, A2, WG-A1 |
| laya | small encoder decision model | local WSL, 8002, 421M | native choice; context 512 | unpriced | A1, A2, WG-A1 |
| secjev | safety-specialised decision model (LoRA+head) | local WSL, 8026, FP32 LoRA unmerged | native choice; calibration temperature 1.3526 | unpriced | A1, A2, WG-A1 |
| jevguard | safety classifier head (Jev-Guard system; safety-only) | local WSL, 8027, BF16 | `/predict` safety head; full policy tree not run | unpriced | A1, A2, WG-A1 |
| kev | decision model (pointer head) | local WSL, 8028, BF16 unmerged | native choice; calibration temperature 2.406 | unpriced | A1, A2, WG-A1 |
| gliguard | safety classifier (non-autoregressive) | local WSL, 8001, gliner2 | native `prompt_safety`; threshold 0.5; context 512; no usage | unpriced | A1, A2, B partial, WG-A1 |
| shieldstral | safety classifier (generative yes/no) | local WSL, 8013, BF16 | yes/no, max_tokens 1, temp 0, context 32768 | unpriced | A1, A2, WG-A1 |
| qwen3guard | guard classifier (generative) | local WSL, 8000, BF16 | native Safety line; max_tokens 64, no sampling; Controversial→unsafe; context 32768 | unpriced | A1, A2, WG-A1 |
| qwen35 | general LLM | local WSL, 8015, BF16 | strict `{"risk":boolean}`, max_tokens 64, temp 0, thinking off | unpriced | A1, A2, WG-A1 |
| gpt6luna | general LLM judge | OpenLux chat completions | system+user prompt, strict risk JSON, max_tokens 2000 | list-price estimate; refusals unpriced | A1, A2, B, WG-A1 |
| claudehaiku | general LLM judge | OpenLux chat completions | same, max_tokens 1500 | list-price estimate | A1, A2, B, C partial, WG-A1 |

Config evidence: `configs/full-suite-models.v1.json` (packy overlay `configs/full-suite-models.packy-v1.json`); per-cell `effective-config.json`; pilot params in `summary/agentharm/model-parameters.csv`. Native guard templates vs System One choice vs JSON boolean mean the models do **not** receive equivalent prompts (`docs/infrastructure/full-benchmark-operations.md` §4: "不能声称它们接收了同样的任务指令").

## 4. Frozen vs pilot vs smoke (what the labels say)

- Every derived summary in `runs/` is `phase=pilot` (209/209 groups); full campaigns carry `record_kind=full_public_descriptive_evaluation_v1`, `confirmation_protocol_manifest=null`, `repeats=1`. The handbook calls it "描述性评估…不能改称独立盲测或 confirmatory" and the config "12 模型冻结前部署配置" (`docs/infrastructure/full-benchmark-operations.md`).
- The only consolidated public table (`summary/agentharm/README.md`) is the **50-item ×3** exposed-validation pilot, 12 models, 8 families; it says "科学确认配置仍未冻结", "Wilson fields are descriptive and not family-cluster corrected".
- Smokes are separately labelled (`SMOKE-REPORT.md`, smoke dirs, 2–8 items). ATBench beyond smoke: none.
- No confirmation protocol, no freeze manifest, no pre-registered thresholds/samples exist for any RQ (`data/agent-security-study/protocol.template.json` still null; decisions log ends 2026-11-05 and does not cover the 11-06→11-12 full runs).

## 5. RQ1 numbers that exist (pilot, 1 repeat unless stated)

AgentHarm accuracy is split-specific; **the 50-item validation pilot does not represent test_public** (e.g., GLiGuard 0.980 pilot → 0.984 validation 64 → **0.741** test_public 352).

| Model | AH val/test (N=64/352) | IA base/enh (N=1054 each) | TS asb/ah/dojo acc (valid N) | StepShield | WG-A1 acc (N=1699) | WG-E |
|---|---|---|---|---|---|---|
| jev | .906/.881 | .909/1.000 | .796/.755/.932 (3765/416/1220) | episodes done, no report | — | .9315 (N=1709) |
| d3mini | .969/.852 | .882/1.000 | — | — | .9011 | — |
| laya | .719/.722 | .159/.249 | — | — | .6392 | — |
| secjev | .828/.821 | .570/.861 | — | — | .7404 | — |
| jevguard | .906/.736 | .584/.904 | — | — | .7828 | — |
| kev | .984/.815 | .827/.999 | — | — | .8752 | — |
| gliguard | .984/.741 | .683/.826 | partial: .678(N=605)/.710(N=62)/.697(N=185) | — | .8764 | — |
| shieldstral | .938/.835 | .139/.828 | — | — | .8999 | — |
| qwen3guard | .813/.636 | .484/.668 | — | — | .9023 | — |
| qwen35 | .875/.796 | .762/1.000 | — | — | .7987 | — |
| gpt6luna | .953/.821 | .992/1.000 | .847/.702/.967 (3765/416/1220) | — | .8719 | — |
| claudehaiku | .875/.824 | .912/1.000 | .835/.682/.808 (3746/415/1210) | .693 acc, prec .192, F1 .321; EIR(k=3)=.550; N=4591/7935 (57.9%) | .8434 | — |

InjecAgent has **no negative class** (`negative_policy: positives_only`, `effective-config.json`), so TN=FP=0 for all 12; the reported "accuracy" is detection rate/recall and F1 is inflated. Five of the six decision/LLM arms reach 1.000 on the "enhanced" split (Jev, GPT, Claude, D3, Qwen35; Kev 0.999) while guard models stay far below on "base" (Shieldstral .139, Laya .159, Qwen3Guard .484, SecJev .570, JevGuard .584): this is split/data-composition variance, not robustness evidence. TS-Bench excludes the 1781 `0.5` items (`controversial_policy: unknown`), so coverage differs by source (57% / 100% / 72%).

## 6. RQ2 evidence and confounds

| Quantity | Present for | Where | Admissible? |
|---|---|---|---|
| p50/p95 per episode (measured wall-clock, includes failures) | 12-model AH pilot; full cells | `summary/agentharm/README.md`; per-cell `summary.json` | descriptive only |
| tokens/usage | 12 models AH pilot except GLiGuard (unknown); full cells | `summary/agentharm/tokens.csv`; `telemetry/run.json` | different tokenizers/templates |
| API fee estimates | Jev, GPT, Claude only (e.g. Jev AH 0.001083 pilot; Packy full AH .00751, IA .04714, TB .35860 known, SS ≈2.819 known, WG-E .06216) | `configs/full-suite-pricing.*.json`, `run.json` | **estimates, not bills**; unknown-cost calls exist; Packy 7× multiplier note |
| Local compute cost | no model | `configs/full-*`; local campaigns | protocol: unpriced, do not zero-fill |

The repo's own rules make cross-model cost comparison inadmissible as a single number: API fees vs unpriced local compute must stay separate (`docs/model-evaluation/agent-security-experiment-protocol.md` §4; `AGENTS.md`), and the ops handbook says interfaces "不能夸大成完全等价的训练语义". Observed confounds: RTX 3050 Ti Laptop 4GB (Laya, Qwen3Guard, GLiGuard pilots) vs RTX 4070 SUPER 12GB (others) vs unknown server hardware (API); OpenLux vs Packy relay; VPN vs direct path (StepShield `NETWORK_NOTE.md`); retries included in timing; StepShield issues ~7 calls/episode (32,020 calls / 4,592 episodes) vs 1 call/item elsewhere. Task-level cost (main agent + judge + reviewers + retries, `paper/main.tex:42`) has **never** been measured.

## 7. RQ3 evidence (robustness under attack)

No attack/perturbation run exists for any of the 12 models on any of the six dataset contracts. The only related evidence is historical and Jev-only: JevOut 8-item method pilot (6 eligible) and 40-item exploration (32 eligible; 2/32 iterative flips, both with semantic-validity doubts; Jev **1.13.0**; MMLU-Pro; `docs/adversarial-robustness/jevout-40-results.md`), plus a 60-scenario semantic-robustness protocol that was never executed (`docs/semantic-robustness/robustness-security-pilot-protocol.md`). InjecAgent "enhanced" is a harder data variant, not an attack on the judge; TS-Bench controversial items are label ambiguity, not adversarial input.

## 8. RQ4 factor space actually observed (not designed)

| Factor | Levels observed in repo | Where | Manipulated for inference? |
|---|---|---|---|
| Evaluation mode / target event | A1, A2, B, C, E (+ D prepared only) | per-cell `effective-config.json` | no (different benchmark) |
| Model class | 6 decision models, 3 guard classifiers, 3 general LLMs | roster above | no |
| Prompt/input wrapping | native text; structured JSON state; native guard template | ops handbook §4; effective configs | partly (Qwen3Guard raw vs JSON pilot) |
| Output contract | System One choice; strict JSON boolean; native label (yes/no, Safety line, safety head) | same | no |
| Threshold / label mapping | GLiGuard 0.5; Qwen3Guard Controversial→unsafe; TS 0.5→unknown(excluded) | effective configs; decisions 2026-11-01 | Qwen3Guard sensitivity only |
| Repeats | 3 (50-item pilot) vs 1 (full campaigns) | manifests | no |
| Retry policy | none → `bounded_first_valid_v1` (5 attempts) | effective configs; decisions 2026-11-05 | no |
| Provider / route | OpenLux vs Packy; official TypeSafe (historical) | pricing/model overlays | no |
| Hardware / context limit | 3050 Ti 4GB vs 4070 SUPER 12GB; 512–262144 context | summary; model configs | no |
| Jev question type | only `choice` (no `noul`/`score` runs) | model configs | no |

## 9. Internal-validity threats (each with evidence)

1. **No execution evidence at all.** All 209 group summaries have `episode_results.scorable=0`, `attack_success_rate=null`; no `traces/` dirs. Everything is static view classification. The paper draft itself (line 36) says isolated classification cannot determine execution outcomes.
2. **Category conflation.** "12 models" = 6 typed decision models + 3 guard classifiers + 3 LLM judges; prompts/outputs differ (native guard templates quoted). A single ranking would compare interfaces, not judge quality.
3. **InjecAgent has no negatives.** `negative_policy: positives_only`; TN=FP=0 for all 12; "accuracy"=recall; no FPR/specificity; the contract's label text still says a paired negative exists (stale text) while execution has none.
4. **TS-Bench label ambiguity is differentially dropped.** 1781/7182 `0.5` items excluded under `unknown`: valid N 416/731 (57%) for AgentHarm-traj, 3765/5231 (72%) ASB, 1220/1220 AgentDojo. Pooling or comparing "accuracy" across sources is confounded by exclusion.
5. **Pilot sample ≠ full sample.** The 50-item 8-family pilot (e.g., GLiGuard .980) diverges sharply from 352-item test_public (.741); no evidence the pilot validation ranking generalises.
6. **Clustering ignored.** AgentHarm 416 items in 52 families; TS-Bench 7182 steps in 3376 families; StepShield 8143 families over 8151 items; repeated WildGuard prompts. No family-cluster CIs or paired cluster analysis; "3 repeats" are not independent samples.
7. **Different target events cannot be pooled.** AgentHarm input-harm, InjecAgent third-party instruction, TS pre-action safety, StepShield prefix violation, WildGuard response harm, ATBench trajectory safety are six gold definitions; protocol forbids one matrix/one score (`agent-security-experiment-protocol.md` §5; handbook: "no pooled benchmark score").
8. **No negatives / no utility / no ASR.** No clean-vs-attacked episodes, no task completion, no utility; "security judge for LLM agents" is therefore untested in an agent.
9. **Cost/latency not comparable.** Local unpriced; API list estimates (not bills); GPT unknown-cost refusals; Packy vs OpenLux; VPN vs direct; 4GB vs 12GB GPUs; different call counts per item. Latency includes failures/retries.
10. **Provider/route and version drift.** All run configs pin `jev-1.14.0` (0 mention 1.13 in run configs), but pilot Jev = OpenLux, full Jev = Packy (different endpoint/key/pricing); papers and JevOut used 1.13.0. No same-sample 1.13-vs-1.14 or OpenLux-vs-Packy bridge; relay returns `jev-1.14.0` but serving parity is unverified.
11. **Thresholds/criteria/retry choices not pre-registered.** GLiGuard 0.5, Qwen3Guard Controversial→unsafe, TS `unknown`, retry-to-first-valid (5 attempts) were chosen during execution; "first valid prediction" can select on format/refusal behaviour.
12. **Failure/refusal handling changes denominators.** GPT AH pilot: 11 provider refusals unpriced; full v2: 37 refusals + 1 disconnect; Claude v2: 295 JSONDecodeErrors; v5 re-run after fence fix. Refusals/parse failures are excluded (correctly) but shift coverage and can correlate with harmful content (GPT family-8 triple refusal).
13. **StepShield C incomplete and unconsolidated.** Claude v1 4719/8151 + continuation runs 1510/4/(1919 planned) with no merged analysis; Jev 8151 episodes complete but no `analysis/` (report.py `TypeError` on two `monitor_event_index=None`); GPT/local StepShield absent from repo (external server not reachable). No complete C table exists.
14. **ATBench D claim unsupported.** Only n=2 smoke; no long-context policy (median 7.5k / p95 26k / max ~365k chars vs Jev 64k/request, 32k/question) and handbook forbids silent truncation; so no D result, no feasibility evidence for D.
15. **Namespace/selection drift.** Selection v1→v2→v3→v4→2026-11-10 five-set changes datasets (AgentDojo→MSB→InjecAgent; MCPHunt removed; ATBench C→D→excluded; WildGuard A1→E added). "Same" dataset keys may denote different contracts (`wildguardtest` A1 vs `wildguardtest-response` E); old ATBench/AgentDojo results are historical and must not be spliced.
16. **Reproducibility provenance gaps.** Decision log (`decisions.md`) stops at 2026-11-05; full runs (11-05→11-12) are documented only in run-dir HANDOFF/launcher logs; no versioned cross-benchmark consolidation script output for the five-set; local StepShield runs on a second machine absent here.

## 10. What is "paper-ready today" vs "needs new runs"

| Status | Content | Required wording |
|---|---|---|
| Paper-ready today (as exploratory evidence) | AgentHarm A1 12-model full-416 table + 50×3 pilot; InjecAgent A2 12-model detection-rate table; TS-Bench B 3-model table by source with unknown excluded; WildGuard A1 11-model and E Jev-only tables; descriptive latency/token appendix | "descriptive pilot on exposed public splits, 1 repeat, no family-cluster CIs, no execution, not confirmatory"; no pooled score; no model ranking claims |
| Needs new runs | ATBench D full matrix with frozen long-context policy (or drop D); TS-Bench 8 local models + Jev-Guard; StepShield 12-model complete + consolidated report (fix report.py); WildGuard E other 11 models; 12-model clean-vs-attacked task-level runs (agent loop) for utility/ASR; controlled same-hardware cost/latency track with measured pricing; RQ3 attack experiments with fixed budgets/semantic audit; RQ4 crossed configuration design | freeze manifest, pre-registered thresholds/samples/retry/budget, cluster-robust CIs, noninferiority bounds, measured bills, energy/rental assumptions separated from API fees |

## 11. Could not verify

- Local StepShield 9-model campaign (`full-local-stepshield-server-v1`) and gpt6luna StepShield: referenced in run logs as running on server 172.17.210.135, **no artifacts in this repo**.
- Jev StepShield scores: episodes exist but no report; numbers cannot be quoted until report.py is fixed and the analysis re-derived with versioned code.
- Whether Packy (`slb-v1.api.fan`) serves the same Jev weights/behaviour as OpenLux or official TypeSafe; only the returned model id `jev-1.14.0` is recorded.
- Actual invoices/bills: all fee fields are price estimates; local compute is unpriced; budget ceilings (20/30/80/250 USD) are launcher settings, not recorded user approvals.
- Whether the four proposed RQs (vs the paper draft's action-gating/context-selector framing) are final; the draft states no RQs and no findings.

*Audit sources: `data/agent-security-study/{README.md,decisions.md,summary/**}`, `data/agent-security-study/runs/**/{manifest,effective-config,summary,report,HANDOFF}`, `docs/model-evaluation/**`, `docs/infrastructure/full-benchmark-operations.md`, `configs/full-suite-*`, `paper/main.tex`. No files were modified except this deliverable.*
