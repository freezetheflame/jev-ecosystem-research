# Feasibility audit — closed-loop AgentDojo × Jev experiment

- **Date / author:** 2026-10-17, feasibility-auditor (shared task-2).
- **Question:** what can actually be *executed* for the proposed Jev-in-LLM-agent study, at what cost, and what is missing.
- **Method:** read-only inspection of this repo (`data/`, `scripts/`, `paper/`, `docs/`, `.pi/pi-jev.json`, `.env.local` key names only) plus the referenced local snapshot `D:/projects/jev` (`inventory.json.source_root`). No model API calls. The 7 offline client tests in `scripts/test_jev_api.py` pass. **[M]** = measured/read from a file here; **[E]** = estimate or assumption (stated). No invented numbers.

## Verdict by working RQ (`paper/README.md:20-23`)

| RQ | Executable today? | Blocking gap |
|---|---|---|
| RQ1 security effect & applicable role | **No** | no AgentDojo runtime and no LLM agent loop (§2); no audited task–attack pairs |
| RQ2 robustness & failure mechanisms | **No** | same, plus repeated runs / variants; only analog JevOut evidence exists |
| RQ3 integration & composition strategies | **No** | the four arms need a pipeline to attach to |
| RQ4 cost & efficiency (secondary) | **Partial** | Jev-side arithmetic possible now (§5); end-to-end accounting needs the pipeline and generator price |
| **Overall** | **Not executable as designed** | client works; closed loop does not exist. MVP after 14–22 person-days (§6). |

## 1. Jev client contract (Q1)

Working clients: `scripts/jev_api.py` (stdlib, no retry) and vendored `data/JevOut/context_optimization/targets.py::JevTarget` (httpx). Both POST JSON. A real 200 response is archived: `data/jev-zen-smoke.json` (model `jev-1.13-free`, elapsed 2.9918 s, three answer types) and `data/jevout-typesafe/connectivity.json` (official endpoint, model `jev-1.13.0`, usage 331/31 tokens).

| Element | What the source/records show | Evidence |
|---|---|---|
| Endpoint / provider | official `POST https://api.typesafe.ai/v1/systemone` (Bearer). Free test proxy: `POST https://opencode.ai/zen/v1/systemone` (documented public placeholder key, no SLA). Vercel gateway attempt returned HTTP 403. | targets.py:57-65; docs/applications/products-and-request-design.md:116; .pi/pi-jev.json; docs/infrastructure/opencode-zen-jev-testing.md:3-10; data/jevout-gateway/connectivity.json |
| Model version pin | request field `model`: official default `jev-1.13.0`, free `jev-1.13-free`; response field `model` is recorded as the served revision. | targets.py:60, 89-92, 136; jev_api.py:51, 86-88 |
| Requested ≠ served | `data/jevout-40/manifest.json` requests `jev-1.13.0` over api.typesafe.ai, yet `baseline-summary.json` records response_models `["jev-1.13-free"]`; neutral arm mixes `["jev-1.13-free","jev-1.13.0"]` with `provider_equivalence_assumed: true` (not verified). | data/jevout-40/{manifest,baseline-summary,exploratory-summary}.json; docs/adversarial-robustness/jevout-40-results.md:83-84 |
| temperature / n | **not sent, not documented, not configurable**: no temperature, top_p, max_tokens, reasoning_effort or n in the wire payload or official schema; one request = one pass. Multiple questions can share one `state` but are evaluated independently. | targets.py:88-95; products-and-request-design.md:183, 209 |
| Output types | `choice`, `noul`, `score` (client validation); JevOut decision units use `choice` and binary membership→`noul`. | jev_api.py:49, 95-109; schema.py:55-58, 249-284 |
| Probability / confidence | choice → `answers[k].probabilities` dict (normalized to sum 1) + native `choice` + `confidence`; noul → `answers[k].noul` = P(true) only, no separate confidence; score → `score` + `probabilities` + `confidence` + `legend`. `confidence` is a distribution-shape quantity, not P(selected is correct). | targets.py:113-126; schema.py:75-100; data/jev-zen-smoke.json:11-39; data/jev-zen-rag-screen.json:11-35; products-and-request-design.md:187-191 |
| System prompt / state | **no system prompt and no chat messages.** One required `state` (string or JSON object) plus a `questions` map whose `instructions`/`criteria` carry the task; tool schemas, trust labels and history must be serialized into `state` by the caller. | jev_api.py:42-51; targets.py:81-95; products-and-request-design.md:169-173; D:/projects/jev/harness/README.md:26-37 |
| Per-call latency | not in the response body; measured client-side around the HTTP call (`latency_ms`). | targets.py:107-109; jev_api.py:74, 90 |
| Limits / timeout / retries | state+questions ≤64k tokens, state+longest question ≤32k, choice ≤255; documented rate limit 80 req/s and 100k tok/s (dynamic). Free config: timeout 10 s, 0 retries; `JevTarget` retries 429/5xx up to 3 times. | products-and-request-design.md:174, 180, 211; .pi/pi-jev.json; targets.py:23-41 |

## 2. Closed-loop readiness (Q2)

| Component | Present locally? | Evidence | Missing for a closed loop |
|---|---|---|---|
| Jev client | **Yes, exercised [M]** | two working clients; archived HTTP 200s; 7/7 offline tests | batching / queue / retry policy for an experiment |
| AgentDojo runtime | **No [M]** | `D:/projects/jev/bench/raw/agentdojo/` holds 31 static files = task-definition **patches** for 7 versions (v1…v1_2_2). They `from agentdojo.base_tasks import …`; no `environment.yaml`; `agentdojo` is absent from `D:/projects/jev/.venv` (207 packages) and from system Python 3.11.15 (`find_spec → None`). | pinned AgentDojo install; 4 task suites, initial states, 74 tool implementations, injection-vector placement, evaluation functions |
| LLM agent pipeline / tool loop | **No [M]** | nothing in this repo; the adjacent `D:/projects/jev/harness/agb/` is a **scripted** simulator: `policy.py` "Deliberately not an LLM agent", `worlds.py` simulated tools; 13 episodes / 5 attacks; its README grades this "evidence grade C". | LLM agent loop, model adapter, tool executor, defence hook points, episode log schema |
| Static task/attack extraction | **Yes [M]** | 83 user-task prompts (banking 16, slack 15, travel 20, workspace 32); 63 inbound items (35 injection GOAL, 21 clean default, 7 unlabeled); 1,220 AgentDojo-derived TS-Bench action rows. Adapter docstring: "只做静态抽取，不搭环境、不跑 agent". | attack payloads, valid task↔injection pairing, environments |
| Audited task–attack pairs | **No [M]** | `review-candidates.json`: 24 candidates (6/suite), **all** `pending_manual_audit`, `development_only`, with `injection_task_id/attack_payload/action_gold = null` and `executable_environment_verified=false`. | full-text audit, matched injection task, payload, utility/security checks, action-level gold |
| Scoring | **Fragments only [M]** | patch files carry some `utility()` bodies, but task suites and most user tasks' utility/security checks are imported from the package; no runnable checker locally | package + verified judge semantics |

**Missing pieces, in dependency order:** (1) pinned AgentDojo package + task suites/environments/tools; (2) LLM agent pipeline with model adapter and tool executor; (3) Jev gate and context-selector as pipeline components; (4) audited user-task↔injection-task pairs and payloads; (5) task utility + targeted-ASR checkers; (6) episode-level logging of tokens/latency/cost; (7) frozen provider/model revision.

## 3. Per-call accounting and price (Q3)

| Item | Present? | Where / value |
|---|---|---|
| `latency_ms` per Jev call | **Yes [M]** | `DecisionResult.latency_ms` (schema.py:81) beside every record. Historical official scans n=13,173: p50 **1,067 ms**, p95 **1,728 ms**, mean 1,145. JevOut official (n=295): p50 547, p95 1,451. Free endpoint (n=167): p50 705, p95 2,019. Client-side, includes network. |
| `input_tokens` | **Yes [M]** | `DecisionResult.input_tokens` from response `usage.input_tokens` (targets.py:135). Historical mean 1,038 (n=13,173); JevOut mean ≈625 (n=462). AgentDojo-text scans: 381–981. |
| `output_tokens` | **Not in DecisionResult** | raw response `usage.output_tokens` exists (data/jev-zen-smoke.json:41-44) but is dropped by the record model; historical scan records keep `usage:{input_tokens,output_tokens}`. |
| generator latency | **Not recorded per call** | `*-chat-calls.jsonl` holds `response.usage` (799 calls: mean prompt 912 / completion 54 tokens) but no latency field. Proxies only: DeepSeek v2 median **2.1–2.2 s** (docs/model-evaluation/benchmark-comparison.md:33); response `created` gaps in the sequential run p50 **2 s** (n=562). |
| price / cost | **No manifest, summary or env record [M]** | only docs: **$0.042 per M input tokens, output free** (950 input tokens/decision → $0.0399/1,000 decisions), citing docs.typesafe.ai/models — recorded in `data/jev-robustness-literature/jevbench.md:96` and `data/jevbench-v1.4.2.2-results.json:196`. No local snapshot of the official page; the same $0.042 figure also appears as the Microsoft-Decision-1 price (docs/ecosystem/microsoft-decision-1.md:17), so re-verify before budgeting. |
| experiment-level total | **Partial [M]** | `data/jevout-pilot/experiment-audit.json`: 116,352 tokens across the three final arms (not per call, no latency, no price). |

## 4. Sample-size reality (Q4)

| Local asset | Count [M] | Usable as closed-loop episodes? |
|---|---|---|
| Unified static corpus | 27,230 rows / 27,230 UIDs, 20 corpora (14,476 pos / 10,966 neg / 1,788 unlabeled) | **No** — static texts with three incompatible label semantics (`artifact_threat` / `should_refuse` / `outcome_unsafe`), not agent runs |
| AgentDojo user-task prompts | 83 built (97 upstream) | not yet — 83 prompts, no environments |
| AgentDojo inbound items | 63 (35 injection GOAL / 21 clean default / 7 unlabeled) | **No** — GOAL is the attacker objective, not a full payload |
| AgentDojo static task definitions | 31 files, patch chain v1…v1_2_2; upstream 27 injection tasks, 629 security cases, 74 tools | **No** — patches import a package that is not installed |
| Review candidates | 24 (6/suite), 24 pending audit, 0 verified pairs | no — development audit queue only |
| TS-Bench AgentDojo rows | 1,220 S4 action snapshots | no — not full task instances |

**Unit of analysis:** task-episode = one user task × one injection task × one pipeline configuration × one seed, paired across arms. Corpus rows are not independent episodes. Realistic main-study n is therefore ≤97 user tasks if the complete upstream suite is installed and audited; the ready pool is 24 prompts with 0 verified pairs.

**Detectable effect sizes [E] (paired McNemar, α=.05 two-sided, power=.8; δ = |p_b−p_c|, p_d = discordant-pair rate).** No observed closed-loop rates exist, so these are planning bounds, not precision claims:

| n episodes | p_d=.2 | p_d=.3 | p_d=.4 | p_d=.5 |
|---|---|---|---|---|
| 24 (ready candidates) | 24.3 pp | 29.8 pp | 34.4 pp | 38.5 pp |
| 80 | 13.8 | 16.9 | 19.5 | 21.8 |
| 97 (all upstream) | 12.6 | 15.4 | 17.8 | 19.9 |
| 100 | 12.4 | 15.2 | 17.5 | 19.6 |

A 95% Wilson interval at n=100, p=.5 is ±9.6 pp (n=80: ±10.7 pp). Unpaired planning needs ≈93 episodes/arm for 50%→30%. With 9 arm-vs-control tests (3 attacks × 3 Jev arms) a Bonferroni α=.0056 lifts the n=100 detectable δ to ≈19.5–22.5 pp. Subgroup comparisons (4 suites, n≈24 each) detect only ≈25–35 pp. **Verdict:** n=24 is a mechanism/audit pilot; n≈97–100 can support only large (≥15–20 pp) paired effects and cannot support calibration, subgroup or <10 pp claims. Repeats are needed anyway: the simulator measured identical-payload Jev score drift mean |Δp|=.0097, max .05, 1/33 action flips (D:/projects/jev/harness/README.md:115-123).

## 5. Cost / time arithmetic for the plausible main experiment (Q5)

Setup: **100 task-episodes × 3 attack configurations × 4 system configurations = 1,200 episode-runs** (no defence / Jev gate / Jev context selector / gate+selector); 900 runs are Jev arms. **[E]** assumptions: 3, 4 and 6 Jev calls/episode for gate, selector, gate+selector (range 2–10; AgentDojo tasks make a handful of tool calls); 8 generator turns/episode (range 5–12); 25k prompt tokens/episode. Measured inputs: Jev input tokens/call mean 1,038 [M]; Jev latency p50 1,067 ms / p95 1,728 ms [M]; generator latency proxy 2.15 s/call [M]; Jev price $0.042/M input, output free [M-doc].

- **Jev calls:** 300×3 + 300×4 + 300×6 = **3,900 calls**; tokens = 3,900 × 1,038 = **4.05 M**; cost = 4.05 × $0.042 = **$0.17**. High sensitivity (10 calls/episode × 3,000 tokens): 9,000 calls × 3,000 = 27 M → **$1.13**. Add ≈10% for retries: **$0.19–1.24**.
- **Main agent:** 1,200 × 8 = **9,600 generator calls**; at 25k prompt tokens/episode → **30 M prompt tokens**; completion ≈1.4 M. Cost formula, coefficient not recorded anywhere: **C_main ≈ 30 · p_in + 1.4 · p_out USD**, p in US$/M tokens. Jev is therefore 13% of generated prompt-token volume in the base case (90% in the high case); its cash cost is negligible but its **latency is not**: 3 Jev calls add 3.2 s per gate episode (+19% over ~17.2 s of generator time), 6 calls add 6.4 s (+37%).
- **Wall clock [E]:** Jev 3,900 × 1.067 s = 4,161 s = **69 min** sequential (112 min at p95). Generator 9,600 × 2.15 s = 20,640 s = **5.7 h**. Sequential total ≈ **7 h**; at 8 workers ≈ 52 min, ×1.5 for tool execution/retries/logging → ≈**1.3 h**. Cross-check with the largest recorded sequential run: 32 items, 564 chat + 253 Jev calls in 39.2 min [M] (2.87 s/call) → 13,500 calls ≈ 10.8 h sequential ≈ 1.35 h at 8 workers. Planning figure: **1.5–2.5 h wall at 8 workers, 7–11 h sequential**, excluding one-off environment setup. Rate limits (80 req/s, 100k tok/s) do not bind at 8 workers.
- **Free endpoint:** removes the $0.17–1.24 Jev cash cost but has no SLA and serves a different revision (`jev-1.13-free`) from the official `jev-1.13.0`; `data/jevout-40/manifest.json` already disagrees with its own baseline records on the served model [M] — pilots only, not the main table.

## 6. Top 5 blockers and minimum-viable closed loop (Q6)

| # | Blocker | Evidence | Unblock |
|---|---|---|---|
| B1 | No executable AgentDojo environment | package absent; only 31 static patch files importing it; no `environment.yaml` | pin + install one AgentDojo version; smoke one suite/tool; freeze task list |
| B2 | No LLM agent / tool-loop / defence pipeline | only a scripted simulator in the adjacent project; no LLM pipeline in this repo | build agent loop + model adapter + tool executor + gate/selector hooks + episode logging |
| B3 | No audited task–injection pairs or gold | 24/24 candidates pending; injection_task_id, attack_payload, action_gold all null | audit 4 cards (one/suite) then 12–20 pairs; derive payloads from the important_instructions template + injection vectors |
| B4 | Accounting gaps | no price in manifests/env; no output tokens in DecisionResult; no generator latency; no episode cost/latency log | instrument a schema: episode id, arm, seed, Jev calls, tokens in/out, latency, retries, end-to-end time, frozen price snapshot |
| B5 | Provider / version / non-determinism | free endpoint no SLA and model-name drift; official key name present (`TYPESAFE_API_KEY2`) but validity and tariff not re-verified; identical payloads drift ≤.05 with 1/33 action flips | use official pinned `jev-1.13.0` for the main table, record served model every call, repeat seeds ≥3, keep thresholds ≥.1 from score clusters |

**Minimum-viable closed loop [E]:** one or two suites; 12–20 audited user tasks, each with one matched injection task; 1 attack configuration (`important_instructions`) plus optionally a second; 3 arms (no defence / Jev gate / gate+selector); 3 seeds → 108–180 episodes. Jev calls ≈ 72–120 × 4 ≈ 300–500 → Jev cash cost **<$0.10**; generator cost per §5 formula; wall time ≈ 3–6 h at 4 workers. It can answer "does a Jev gate change ASR and utility at a large-effect scale", not RQ2 mechanisms.

**Effort [E], person-days:** AgentDojo install/pin + suite smoke 2–3; agent pipeline + model adapter + tool loop + logging 3–5; Jev gate/selector components and question contracts 2–3; task/attack audit cards (4 full → 12–20) 3–5; utility/security checker verification 1–2; MVP run + analysis + write-up 3–4 → **14–22 pd** (main-scale study adds ≈4–6 pd compute/analysis). These are planning estimates, not recorded effort.

**Evidence boundary:** nothing in this audit is evidence about Jev's security effect inside an agent; it is evidence about client capability, local assets, accounting and cost. The only closed-loop numbers on disk come from a scripted simulator (13 episodes, 5 attacks) and must stay labelled as such.
