# Related-work overlap for RQ1–RQ4: Jev as an agent security component

Date: 2026-10-17 · lit-positioner · task-1. Scope: documents and arXiv snapshots already in this repo; no new model calls, no experiments, no edits to existing files.
Evidence rule: every number below is taken from a repo snapshot or repo note (path given where it matters). "Preprint" = not peer-reviewed in the snapshot. Vendor docs and the JevBench leaderboard are not evidence of safety. arXiv IDs are only stated when they appear in the repo.

## 0. Bottom line

- **RQ1 is already published as an offline-capability question** (four independent Jev studies). It cannot carry a novelty claim as stated.
- **RQ2 is already published at the decision level**; the trust-boundary variant is partly covered by an *unreviewed* Zenodo preprint. "First to study prompt injection / robustness / authorization gating of Jev" is false.
- **RQ3 is partly published**: fixed-policy failure, calibration/selective automation, escalation failure, and gate-cost accounting are all measured. Only closed-loop gating under attack + distribution shift is left, and it is crowded.
- **RQ4 is not published end-to-end** (no agent-level cost/latency ledger found locally), but every component is; weakest novelty, highest null-result risk.
- **The class claim is already taken**: Fast Models, Slow Evidence (2610.02267) evaluates a fast/small decision model as a harness security component at the static-decision level (details §7).

## 1. Verdict per RQ

| RQ | Already published? | Nearest work | Novelty left if stated as written |
|---|---|---|---|
| RQ1 capability boundaries | **Yes, as offline capability** | 2609.33401v3, 2610.02267, 2610.04985, 2609.34862 | None as "which judgments can Jev make"; only role- and execution-conditional behavior could be new |
| RQ2 robustness / trust boundary | **Yes at decision level; trust-boundary variant only partly** | 2609.28613v1, 2609.31142v1, 2609.30243v2, 2610.04985, Zenodo 22952571 | None as "can untrusted input flip Jev"; paired pseudo/real-authorization with execution consequences is the only sliver |
| RQ3 gating under attack/shift | **Partly** | 2609.33401v3, 2610.02267, 2610.12292v1, 2602.03117 (title only) | Closed-loop gating with frozen thresholds vs deterministic baseline; defense composition |
| RQ4 cost/latency under constraints | **No end-to-end; components yes** | 2610.02267, 2609.34862, 2609.26550/2609.26532 (bib only) | Agent-level ledger; likely small/negative effect |

## 2. Overlap matrix (RQ → neighbourhood → what is established → residual gap)

| RQ | Neighbour (arXiv id) | What is already established (reported numbers) | Residual gap |
|---|---|---|---|
| RQ1 | Evaluating System One Models for Agent Security Decisions (2609.33401v3) | 1,612 WAInjectBench: Jev Macro-F1 0.756, FNR 0.599, FPR 0.001; misses all 130 unsafe no-EI inputs. R-Judge 236: 0.825 (FNR 0.056). AgentHarm 352: 0.840 (misses 14/176 harmful, flags 42/176 benign). 5 reasoning judges beat Jev on R-Judge (DeepSeek +0.140 [0.094,0.187]). Inputs with p<0.1: 1,446, of which 133 unsafe = 9.20% (mean predicted 0.205%). Under a 1% miss limit: WAInjectBench coverage 0%, R-Judge 7.63%; independent allow/block thresholds lift R-Judge coverage to 47.03% but via 1 allow vs 110 blocks. | Offline benchmark labels, no AgentDojo execution/utility; the "gate at a task action point" question is not run. |
| RQ1 | Fast Models, Slow Evidence (2610.02267) | 11 harness decision points, 7,283 base + 6,640 variants, byte-identical inputs to Jev and Laya; Jev 76.7% vs 63.1% on 2,100 cases, more accurate on 9/11 points (+10.8 to +46.0pp). Injection guard FNR 7.0%/FPR 7.0% (embedded payloads 90.8–93.3% detected, 0% FPR on native docs); tool-call guard 78.7%; pre-execution safety FNR 25.5%; PII egress FNR 15%/FPR 66%; RAG relevance tie (61.0 vs 60.5); zero-shot routing at chance (Jev answers "cheap" for 99.5%). | Static decisions, not execution; several judgments already bounded; wording band ±5pp admitted. |
| RQ1 | JEV as a Judge for Agent Trace Security (2609.34862) | 5,219 trajectories, 4 benchmarks: benchmark-avg positive-class F1 77.8 vs 74.1 for the strongest generative judge (GLM-5.2); valid-result coverage 95.5% vs 94.4%; median successful-call latency 0.99s; ~$0.000195/judgment; Jev wins ATBench500/MCPHunt, loses R-Judge/TraceSafe. | Retrospective trace classification; no pre-execution gating or execution effect. Preprint. |
| RQ1 | Hidden Risks of Jev (2610.04985) | Jev as detector ROC-AUC 0.95–1.0 across 8 benchmarks; calibrated accuracy 87–99% on 6 security benchmarks; clean accuracy 100% on 3 decision tasks | Detector performance only; paper is preprint; no single gate decision measured against execution. |
| RQ2 | Decision Hijacking (2609.28613v1) | 510 reconstructed InjecAgent cases, 54,060 calls; base attack selects attacker target in 9/510 = 1.8% and raises P_adv by +0.043; adaptive score access raises validated ASR to 3.5% (18 cases) and best-so-far P_adv 0.043→0.084; override markers lower P_adv; high-confidence (C≥0.7) hijack 0.2%. | Snapshot selection at first decision; no end-to-end harmful execution; one action-set family. |
| RQ2 | JevAdvBench (2609.31142v1) | 812 questions, 9,744 single-edit variants; identical re-run flips 1.0% (noise floor); paraphrase 1.5%; observer opinion appended to state flips 12.1% [8.5,15.5]; 38.0% [31.1,44.0] of 405 clean-confident Choice/Score answers fall below the 0.8 gate; 47.7% flip or shift. | Label-free flips against model-derived labels; question-side edits; no execution. Not comparable to JevOut. |
| RQ2 | JevOut v2 (2609.30243v2) | 508 initially correct Jev decisions; target-aware optimization flips 312 = 61.4% within ≤64 accepted target evaluations; budget-matched independent generation 244/508 = 48.0%; 91.6% (229/250) of sampled successful contexts judged valid by blinded humans; 2 additions cover 55.5%, ≤64 words 57.5%. | Adaptive context attack at decision level; no execution; validity of "answer-preserving" set still debated. |
| RQ2 | Hidden Risks of Jev (2610.04985) | Six input-manipulation attacks, no Jev feedback used: context ignoring 96.5% ASR, Jev-specific injection 100%, universal adversarial suffix 100% on support routing; role spoofing 93.5%. | Static routing/Noul/Score tasks; ASR is decision match, not executed harm. |
| RQ2 | Type-Safe Is Not Error-Free (2609.26758v3) + One Word Opens the Gate (2610.12292v1) | Name/definition rebinding: Jev yes/no flip 32.5% vs 2.08% for 0/1; balanced accuracy 71.3→51.6, AUC 81.5→58.1; retest floor ≤1.33%; 0% type-error. Option-channel: 93–100% fail-open on the four open-weight models that put the label in the input; Jev not measured; parsing fields + deterministic rule reaches 100% on all six policies; escalation fails because reversed decisions are no less confident. | Option attacks need attacker control of option construction; Jev untested in 2610.12292; deterministic rule removes the task. |
| RQ2 | Jev at the Agent Authorization Boundary (Zenodo 22952571; no arXiv id; unreviewed preprint) | 270 constructed cases, 30 families, 3 policy regimes, labels derived deterministically from authored policies (no independent human adjudication); Jev vs GPT-4.1 mini permission Brier 0.0263 vs 0.0555; fixed probability gate removes 6 false allows but withholds 29 correct allows; Jev denies 18/357 reference-hold proposals vs 1 for GPT-4.1 mini and 2 for DeepSeek; against DeepSeek, the common fixed gate permits 295/345 reference-authorized attempts for Jev vs 315/345 for DeepSeek, with no observed false allows for either. | Closest to "trust boundary" but offline, static proposals, authored labels; peer review absent. |
| RQ2 | The Argument and the Letterhead (2609.35286) | 2,976 evaluations; source attribution changes judgments (e.g. Sol 0.359 CODEPINK vs 0.639 College Republicans); Jev supplement: five interactions below 0.05 reference; interrupted collection, not comparable to chat systems. | Evaluative judgment, not authorization gating or execution; preprint. |
| RQ3 | Security Decisions (2609.33401v3) | Held-out policies fail: Laya 5.02% WAInjectBench coverage but allows 3/279 unsafe (1% limit); Nimble blocks 7/111 benign; Jev 1%-miss policy = 0% WAInject coverage; independent thresholds = 47.03% coverage but 1 allow / 110 blocks; Jev R-Judge 72.88% coverage at 5% budget but benign blocking 5.41% > limit. §7 recommends enforcing permissions independently of model judgments, and evaluating attacks + legitimate completion. | Offline labels; no executed agent and no deterministic-baseline run; recommendation not tested. |
| RQ3 | Fast Models, Slow Evidence (2610.02267) | Two-tier safety pre-screen: 4.3% cost saving at τ=0.1 (self-audit: first reported 23.9%), τ=0.05 costs 4.7% more; held-out FNR p95 6–17%, extra miss in 47% of splits; RAG skip-gate at 5% FNR keeps 79.8% of LLM calls (perfect gate ceiling 58%); Laya→Jev cascade saves 45% of Jev spend at 76.7→70.7 accuracy. | Gate in isolation, synthetic class mix; no attack outcome or agent utility. |
| RQ3 | One Word Opens the Gate (2610.12292v1) | Escalation does not rescue reversed decisions; deterministic parse + rule is exact (100% on six policies) and "makes the model unnecessary" on decidable fields; fail-open 100% under adaptive attack on some models. | Open-weight only, not Jev; no executed agent. |
| RQ3 | REFLEX (2609.26532; bib-only in repo) / JEV-as-a-judge (2609.26550; bib-only) | REFLEX places Jev in a selective-control cascade, confidence chooses fast decision vs stronger-LLM fallback (one sentence in 2609.30243v2 related work); JEV-as-a-judge is "accept when confident, escalate when unsure" (title only). | Numbers not in repo; must read before claiming anything about escalation/cascade novelty. |
| RQ3 | AgentDyn (2602.03117), Confidently Wrong (2606.22659), PIDS-Bench (title only) | Defense deployability in dynamic environments; PI-detector calibration under attack shift; PI detectors under over-defense/obfuscation/distribution shift. | Titles/IDs only in repo (no full text); likely direct overlap with "distribution shift" framing. |
| RQ4 | Fast Models, Slow Evidence (2610.02267) | Jev $0.042/M tokens, 759 tokens/decision ≈ $32/M decisions; p50 Jev 325ms or 83ms depending on client; pre-screen savings 4.3% or −4.7%; latency benefit: 34–41% released in ~0.3s; cascade saves $16/M decisions for −6pp accuracy. | Gate-level accounting only; no end-to-end agent task cost/latency and no reviewer/retry/recovery ledger in an executed loop. |
| RQ4 | JEV as a Judge for Agent Trace Security (2609.34862) | Median 0.99s per successful call, ~$0.000195 per valid judgment. | Retrospective; not agent-task cost. |
| RQ4 | JevBench leaderboard (community, not peer-reviewed) + repo notes | Jev 1.13.0: $0.0399 per 1,000 decisions, adjusted p50 0.652s, sealed-set accuracy 36.7% vs 86.6% public; vendor claim $0.042/M input, 70–500ms. | Per-decision, not task-level; leaderboard is not a controlled study; vendor latency unverified locally. |
| RQ4 | Local note docs/model-evaluation/benchmark-comparison.md | n=100 static paired (MSB 30, MCPTox 30, AgentDojo 40): Jev median 1.0–1.4s vs DeepSeek 2.1–2.2s; on the 40 AgentDojo static cases both 100% recall / 0% FPR. | Exploratory, static, historical predictions; no task loop, no cost ledger. |

## 3. Claims the draft must not make

- RQ1: "first to evaluate Jev's security judgments / capability boundaries"; "Jev is accurate enough to be a security gate" (offline accuracy is high but no gate execution result); "high confidence can be used as an allow signal" (9.20% of WAInjectBench inputs with p<0.1 are unsafe in 2609.33401; 38.0% of confident clean answers cross the 0.8 gate in 2609.31142).
- RQ2: "first to study prompt injection / robustness / option attacks / authorization gating on Jev"; "typed output makes Jev injection-resistant"; treating JevOut 61.4%, JevAdvBench 12.1% or Decision Hijacking 1.8%/3.5% as attack success on execution. They are conditional flips/selection/probability shifts with different denominators and budgets; do not compare them.
- RQ3: "first to study thresholding / selective automation / escalation of Jev"; "escalating low-confidence cases fixes high-confidence errors" (contradicted by 2609.33401's reviewer analysis, 2610.12292's escalation result, and 2610.02267's held-out miss rates); "a calibrated threshold transfers to shifted data".
- RQ4: "first to evaluate Jev cost/latency"; "lower unit price implies lower total agent cost"; "Jev reduces cost" without a matched (security, utility) operating point and a reviewer/retry/recovery ledger. The honest finding may be a null or negative saving.

## 4. Strongest defensible delta (falsifiable)

**Claim.** For an executable AgentDojo agent whose hard permissions are enforced outside the model by deterministic checks, the end-to-end security effect of a Jev component is predicted by its integration role and by the trust source of the text it judges — not by its offline judgment accuracy or calibration. Concretely: (i) no frozen Jev gate configuration (any allow/block threshold, with or without an LLM reviewer) strictly beats the deterministic baseline + no gate on the joint (attack success, legitimate-task completion) operating point at matched utility; and (ii) the only configuration with a non-zero security delta is a source-constrained semantic check (pseudo vs real authorization), where a trust-tagging rule already matches Jev's security at lower cost.

**Why it is still defensible.** No repo document measures a Jev gate's effect on actual unauthorized tool executions in an executable agent; 2610.02267 evaluates gates in isolation, the Zenodo boundary study is static, and the Jev attack papers stop at decisions. The claim is a two-sided measurement, not a promise of a defense.

**Refutation.** The claim is false if any Jev configuration, at equal task utility (pre-registered non-inferiority margin, e.g. 5pp), lowers attack success by a pre-registered margin (e.g. ≥10pp absolute, CI excluding 0) over the deterministic baseline, or if a semantic task exists where the Jev gate beats the trust-tagging rule at equal cost. Either outcome is publishable; the current draft has no operationalization for either.

## 5. Must-cite works the draft omits (priority order)

| # | Work | arXiv id | Repo evidence | Why it matters |
|---|---|---|---|---|
| 1 | Fast Models, Slow Evidence | 2610.02267 | full text snapshot | Closest class-level study; defines the static-vs-execution gap the draft must claim |
| 2 | Evaluating System One Models for Agent Security Decisions | 2609.33401v3 | full text snapshot (already cited in draft, under-used) | RQ3 policy/calibration/selective automation; §7 recommendation is the deterministic-baseline argument |
| 3 | JevAdvBench | 2609.31142v1 | full text | Single-edit flips, confidence-gate effect |
| 4 | JevOut | 2609.30243v2 | full text (v2) | Adaptive natural-context attack, 61.4%/48.0% |
| 5 | Hidden Risks of Jev | 2610.04985 | full text | Injection ASR up to 100%; Jev as detector; mitigation proposals |
| 6 | Decision Hijacking | 2609.28613v1 | full text (already cited; must be repositioned) | 1.8%→3.5% probability-vs-selection gap |
| 7 | Type-Safe Is Not Error-Free | 2609.26758v3 | full text (v3) | Option-name channel, 32.5% Jev flip |
| 8 | One Word Opens the Gate | 2610.12292v1 | full text | Option-channel attack + deterministic-rule and escalation negatives |
| 9 | Jev at the Agent Authorization Boundary | none (Zenodo 22952571) | abstract | Closest trust-boundary study; unreviewed, must cite as preprint |
| 10 | The Argument and the Letterhead | 2609.35286 | abstract | Source/position effects; nearest "trust source" evidence |
| 11 | JEV as a Judge for Agent Trace Security | 2609.34862 | abstract | General-LLM-judge comparison, F1 77.8 vs 74.1, cost/latency |
| 12 | Beyond Calibration | 2609.33209 | full text | Probability-axiom coherence; thresholds must not mix question forms |
| 13 | REFLEX with Jev | 2609.26532 | bibliography only (2609.33401v1 + 2609.30243v2) | Jev + fallback cascade: direct RQ3/RQ4 overlap; no numbers locally |
| 14 | JEV-as-a-judge | 2609.26550 | bibliography only | Confidence accept/escalate: direct RQ3 overlap |
| 15 | JEV vs LLMs as rubric judges | 2609.29769 | bibliography only (2609.30243v2) | "cheaper, faster, wrong in same places": direct RQ1/RQ4 overlap |
| 16 | Just Ask Jev | 2609.29429 | bibliography only | Jev as zero-shot alignment-failure detector |
| 17 | WAInjectBench | 2510.01354v2 | bibliography only | Benchmark used by 2609.33401; needed for denominators |
| 18 | AgentDyn / Confidently Wrong / PIDS-Bench | 2602.03117 / 2606.22659 / no id | bibliography/title only | Distribution-shift and over-defense prior work |
| 19 | Defeating prompt injections by design (CaMeL) | 2503.18813 | bibliography only (in 2609.33401v1) | Canonical deterministic information-flow baseline |
| 20 | CheckList / TextFlint | 2005.04118 / 2103.11441 | abstract snapshots | Behavioural-test methodology for invariance/directional sets |

Also already cited and fine to keep: AgentDojo (2406.13352v3), TypeSafe vendor blog (must remain labelled vendor claim). Not of Jev-specific relevance but present in bibliography: Guo et al. calibration, Ovadia et al. shift, Angelopoulos et al. conformal risk control — cite only if the methods are actually used.

## 6. Baselines and defences the draft currently lacks

| Baseline | Concrete comparator | Repo evidence | Usable now? |
|---|---|---|---|
| No defence | AgentDojo attack run without any guard | draft cites AgentDojo; repo has only 83 user-task + 63 inbound static extractions and no confirmed environment.yaml | Required; needs upstream pinned AgentDojo install first |
| Deterministic permission/taint | Harness-enforced capability/argument allow/deny; information-flow (CaMeL) | CaMeL 2503.18813 bib only; AgentSpec title only; 2610.12292 deterministic parse+rule = 100% on six policies (full text); 2609.33401 §7 recommendation | Implementable in harness; the strongest and mandatory baseline |
| General LLM judge | GPT-4.1 (2609.33401 primary), five reasoning judges (DeepSeek-V4.1-Flash, GLM, Kimi, Qwen), four generative judges (2609.34862), local DeepSeek V4.1 Flash | full texts + local docs/model-evaluation/benchmark-comparison.md (n=100 static; AgentDojo 40: both 100%/0%) | Yes; also the cost side of RQ4 |
| Jev + LLM reviewer / cascade | Two-tier pre-screen (2610.02267); REFLEX (2609.26532); JEV-as-a-judge (2609.26550) | 2610.02267 full text; others bib only | Yes; must count reviewer calls, latency, retries |
| Threshold policies | Symmetric vs independent allow/block thresholds; coverage, missed-unsafe, blocked-benign separately | 2609.33401v3 full text | Yes, once labelled dev data exists |
| Prompt-injection defenses used by AgentDojo | AgentDojo's built-in defense components | **Not evidenced locally** (no named/documented defence in repo) | Must obtain upstream docs/paper; do not guess names or numbers |
| Standard PI training defences | StruQ / SecAlign | named only in 2609.28613v1 text, no IDs in repo | **Not usable from repo**; cite only after reading originals |

Blunt note: the draft currently has zero defence/baseline programme. Without no-defence, deterministic-rule, and LLM-judge arms, no security claim in RQ2/RQ3 is testable, and a Jev "improvement" cannot be separated from the baseline.

## 7. Class coverage: what 2610.02267 did and did not do

Did:
- Paired evaluation of two System-1 models (hosted Jev, open-weight Laya) as harness components on 11 agent decision points (routing, tool selection, tool-call guard, RAG relevance, injection guard, groundedness, pre-execution safety, PII egress, hard distractors, embedded injections, two-tier safety), 7,283 base + 6,640 robustness variants, byte-identical inputs, paired McNemar, cross-day/cross-hardware reproducibility.
- Quantified gates directly: call rate, miss rate, held-out threshold stability, two-tier pre-screen cost and latency, and a Jev/Laya cascade.
- Used 60 AgentDojo injection goals embedded in carrier templates in control G2 — but as static detector inputs, not agent runs.
- Self-audited its own pipeline and corrected 4 accounting/design errors (23.9%→4.3% saving; 58% vs 98% mislabelling; in-sample thresholds; vanishing channel effect).

Did not:
- Run an agent: no tool execution, no AgentDojo task utility, no attack-to-action causality. "We evaluate the detector in isolation" (§2).
- Test the trust-source boundary: only delivery channel (user turn vs tool output) and content style; no authorization claims, no pseudo vs real authorization.
- Test across task families for distribution shift; single versions, English-centric, wording band ±5pp.
- Include a deterministic permission/taint baseline or any AgentDojo defence.
- Produce an end-to-end task cost/latency ledger (only gate-component accounting).
- Test Jev gating outcomes under adaptive attack (the attack literatures' budgeted attacks are not combined with the gate).

Conclusion: "fast/small decision model as an agent security component" is covered as a class at static-decision level; the uncovered remainder is execution-level consequence, trust-source authorization, deterministic-baseline comparison, and end-to-end cost/latency. RQ1 and RQ2 must be re-scoped to that remainder or dropped as novelty claims.

## 8. Evidence caveats

- All Jev-specific works in the repo are arXiv preprints or one Zenodo preprint; none is peer-reviewed in the snapshots. AgentDojo itself is published (NeurIPS, per 2609.33401 bibliography). Do not describe preprints as "established".
- Vendor claims (typesafe.ai blog/docs: $0.042/M input, output free, 70–500ms) are vendor claims only; measured latency in repo ranges from 83ms to ~1.4s depending on client/site; JevBench is a third-party community leaderboard, not a controlled study.
- Repo's own local results are exploratory: docs/adversarial-robustness/jevout-40-results.md observes 2/32 (6.25%) but both cases add answer-bearing evidence ("语义有效性未确认"), so it cannot be cited as a valid attack rate or used against 61.4%.
- "Not evidenced locally": any AgentDojo defence implementation or attack-success number; REFLEX/JEV-as-a-judge/AgentDyn/PIDS-Bench numbers; option-channel results for Jev (Jev untested there); any cost/latency measurement of a closed-loop Jev-gated agent.
- Key repo paths: docs/semantic-robustness/2026-10-13-robustness-security-review.md; data/jev-robustness-literature/2026-10-13-review/ (sources.json, *.txt, abs-*.html); data/jev-robustness-literature/ (sources.json, supplemental-sources.json, jevbench.md, awesome.md); docs/model-evaluation/empirical-study-assets-and-benchmarks.md; docs/model-evaluation/benchmark-comparison.md; docs/semantic-robustness/robustness-security-pilot-protocol.md; docs/ecosystem/open-ecosystem.md.
