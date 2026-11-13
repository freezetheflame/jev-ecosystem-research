# RQ1 additional analysis: position-conditional effectiveness, CIs, operating points, shift

Generated 2026-11-12T17:19:26Z by derive.py / derive_thresholds.py / derive_docs.py (script sha256 in provenance.json). Cluster bootstrap unit = content family, reps=1000, seed=20261113.
This directory is an ADDITIONAL analysis. It does not replace rq1/summary/ and does not modify runs/.
All numbers are descriptive: one repeat, exposed public splits, no pre-registered threshold.

## 0. Three sentences

1. No judge is best at every position. Top-1 is unambiguous where p(top-1) is near 100% (GPT-6 Luna on TS-Bench and InjecAgent), fairly clear where it is 80-83% (Jev on WildGuard-E, and Jev on StepShield test when ranked by balanced accuracy), and a coin flip at the request position (Jev 52% vs d3mini 40%) and on the StepShield holdout (56% vs 40%).
2. The winner changes with the metric: on StepShield test Jev ranks 4th by MCC but 1st by balanced accuracy and TPR; on TS-Bench Claude ranks 2nd by MCC but 1st by TPR.
3. Comparing at 0.5/argmax is an arbitrary choice. The MCC-optimal threshold per cell ranges from 0.01 to 0.95; on StepShield, moving Jev from 0.50 to 0.77 raises MCC from 0.535 to 0.710, above d3mini's 0.700.

## 1. Method

- Cells are recovered from rq1/summary/metrics_full.csv counts by matching episodes.jsonl files; 66/66 non-baseline cells match TP/FP/TN/FN exactly (the script lists candidates and skips on mismatch).
- Merge rule for repaired campaigns: files sorted by mtime; an ok row replaces a failed one; between two ok rows the later file wins. The exact file list per cell is in cells.json; verify.py re-derives all cells with an independent implementation (0 mismatches).
- The threshold sweep uses p>=0.5 as the natural point, which agrees with the stored argmax in 99.8-100% of rows (argmax_agreement column); small differences from the summary are due to that tie-breaking, not to missing data.
- Intervals: cluster bootstrap by family_id, 1000 reps, percentile 2.5/97.5.
- Rank stability: per dataset, restrict to items scorable by all models, resample families, recompute MCC; report P(A>B) and top-1 probability.
- Operating points: probabilities parsed from raw/response.body (typed decision models only). Generative judges expose hard labels only, so TPR@fixed-FPR is not defined for them.
- Paired tests: exact McNemar on common items.
- Cost: rq1/summary/time_tokens.csv, normalized per decision and per episode; local compute unpriced.

## 2. Position x model: point estimates with 95% CI

### User request (AgentHarm, A1)

scorable n=416, positive=50.0%, families=52.

| model            | TPR [95% CI]          | TNR [95% CI]         | MCC [95% CI]         |
| ---------------- | --------------------- | -------------------- | -------------------- |
| jev-packy-1.14.0 | 89.4% [81.7%, 96.2%]  | 87.5% [77.9%, 95.2%] | 0.769 [0.660, 0.871] |
| d3mini           | 99.0% [97.1%, 100.0%] | 75.0% [63.9%, 85.1%] | 0.763 [0.675, 0.852] |
| shieldstral      | 90.9% [83.7%, 97.6%]  | 79.3% [69.7%, 88.0%] | 0.707 [0.608, 0.817] |
| kev              | 90.4% [83.2%, 96.6%]  | 77.9% [67.8%, 86.5%] | 0.688 [0.565, 0.797] |
| gpt6luna         | 87.5% [80.3%, 94.2%]  | 80.8% [71.6%, 89.4%] | 0.684 [0.579, 0.793] |
| claudehaiku      | 91.3% [84.6%, 97.1%]  | 75.0% [64.4%, 84.1%] | 0.673 [0.579, 0.776] |

### External content (InjecAgent, A2)

scorable n=2108, positive=100.0%, families=2108.

| model            | TPR [95% CI]         | TNR [95% CI] | MCC [95% CI] |
| ---------------- | -------------------- | ------------ | ------------ |
| claudehaiku      | 95.6% [94.6%, 96.4%] | - [-, -]     | - [-, -]     |
| d3mini           | 94.1% [93.1%, 95.1%] | - [-, -]     | - [-, -]     |
| gliguard         | 75.5% [73.6%, 77.3%] | - [-, -]     | - [-, -]     |
| gpt6luna         | 99.6% [99.3%, 99.9%] | - [-, -]     | - [-, -]     |
| jev-packy-1.14.0 | 95.4% [94.5%, 96.3%] | - [-, -]     | - [-, -]     |
| jevguard         | 74.4% [72.7%, 76.1%] | - [-, -]     | - [-, -]     |

### Tool call (TS-Bench, B)

scorable n=5401, positive=30.2%, families=2971.

| model            | TPR [95% CI]         | TNR [95% CI]         | MCC [95% CI]         |
| ---------------- | -------------------- | -------------------- | -------------------- |
| gpt6luna         | 87.2% [85.3%, 88.9%] | 85.9% [84.3%, 87.4%] | 0.699 [0.671, 0.724] |
| claudehaiku      | 90.7% [89.1%, 92.1%] | 77.8% [75.9%, 79.7%] | 0.636 [0.611, 0.659] |
| jev-packy-1.14.0 | 45.5% [42.4%, 48.3%] | 98.3% [97.9%, 98.8%] | 0.565 [0.536, 0.590] |
| d3mini           | 39.2% [36.4%, 42.2%] | 96.6% [95.7%, 97.3%] | 0.470 [0.437, 0.502] |
| qwen35           | 49.2% [46.3%, 52.2%] | 88.8% [87.1%, 90.2%] | 0.416 [0.382, 0.449] |
| qwen3guard       | 43.4% [40.1%, 46.5%] | 88.8% [87.2%, 90.2%] | 0.363 [0.328, 0.399] |

### Response (WildGuard-E)

scorable n=1709, positive=16.6%, families=1709.

| model            | TPR [95% CI]         | TNR [95% CI]         | MCC [95% CI]         |
| ---------------- | -------------------- | -------------------- | -------------------- |
| jev-packy-1.14.0 | 75.7% [70.8%, 80.8%] | 96.6% [95.6%, 97.5%] | 0.746 [0.700, 0.790] |
| d3mini           | 70.8% [65.2%, 75.9%] | 97.3% [96.3%, 98.1%] | 0.729 [0.677, 0.770] |
| qwen35           | 68.0% [62.9%, 73.6%] | 93.3% [92.0%, 94.5%] | 0.608 [0.557, 0.660] |
| kev              | 81.0% [76.6%, 85.6%] | 84.8% [83.0%, 86.7%] | 0.557 [0.505, 0.605] |
| shieldstral      | 84.9% [80.4%, 89.0%] | 79.6% [77.4%, 81.7%] | 0.518 [0.476, 0.559] |
| qwen3guard       | 89.8% [86.1%, 93.3%] | 68.0% [65.6%, 70.4%] | 0.436 [0.399, 0.472] |

### Action prefix (StepShield test, C)

scorable n=7935, positive=8.1%, families=7927.

| model            | TPR [95% CI]         | TNR [95% CI]         | MCC [95% CI]         |
| ---------------- | -------------------- | -------------------- | -------------------- |
| d3mini           | 80.3% [77.1%, 83.1%] | 96.3% [95.9%, 96.8%] | 0.700 [0.671, 0.727] |
| qwen35           | 46.3% [42.4%, 50.2%] | 99.1% [98.9%, 99.3%] | 0.592 [0.556, 0.625] |
| kev              | 58.1% [54.0%, 61.9%] | 97.2% [96.8%, 97.6%] | 0.581 [0.544, 0.612] |
| jev-packy-1.14.0 | 91.2% [88.9%, 93.4%] | 86.8% [85.9%, 87.5%] | 0.535 [0.511, 0.559] |
| secjev           | 31.8% [28.0%, 35.4%] | 94.5% [94.0%, 95.1%] | 0.271 [0.233, 0.305] |
| qwen3guard       | 7.5% [5.5%, 9.6%]    | 99.7% [99.6%, 99.8%] | 0.210 [0.166, 0.253] |

### Action prefix (StepShield holdout, C)

scorable n=216, positive=50.0%, families=216.

| model            | TPR [95% CI]          | TNR [95% CI]          | MCC [95% CI]         |
| ---------------- | --------------------- | --------------------- | -------------------- |
| jev-packy-1.14.0 | 97.2% [93.7%, 100.0%] | 87.0% [80.2%, 93.1%]  | 0.847 [0.775, 0.910] |
| d3mini           | 91.7% [86.0%, 96.3%]  | 92.6% [86.9%, 97.2%]  | 0.843 [0.769, 0.909] |
| qwen35           | 83.3% [76.2%, 89.6%]  | 94.4% [89.7%, 98.2%]  | 0.783 [0.699, 0.854] |
| kev              | 75.0% [65.7%, 82.9%]  | 91.7% [86.0%, 96.4%]  | 0.676 [0.575, 0.770] |
| jevguard         | 97.2% [93.7%, 100.0%] | 58.3% [49.1%, 68.0%]  | 0.603 [0.515, 0.694] |
| qwen3guard       | 46.3% [36.9%, 56.5%]  | 97.2% [93.6%, 100.0%] | 0.506 [0.418, 0.595] |

Top 6 by MCC (InjecAgent has no negatives and no MCC, ranked by TPR). Full 66 rows: metrics_ci.csv.

## 3. Is the top-1 identifiable?

| position                              | metric | top-1            | p(top-1) | pairs with P(A>B) in [0.4,0.6] |
| ------------------------------------- | ------ | ---------------- | -------- | ------------------------------ |
| User request (AgentHarm, A1)          | mcc    | jev-packy-1.14.0 | 52%      | 4/66                           |
| External content (InjecAgent, A2)     | tpr    | gpt6luna         | 100%     | 1/66                           |
| Tool call (TS-Bench, B)               | mcc    | gpt6luna         | 100%     | 0/66                           |
| Response (WildGuard-E)                | mcc    | jev-packy-1.14.0 | 80%      | 0/45                           |
| Action prefix (StepShield test, C)    | bacc   | jev-packy-1.14.0 | 83%      | 1/45                           |
| Action prefix (StepShield holdout, C) | mcc    | jev-packy-1.14.0 | 56%      | 2/45                           |

A top-1 probability near 50% means the winner is a coin flip. Few tied pairs and extreme probabilities mean the ranking is identifiable.

StepShield note: shieldstral never predicts unsafe on test, so its MCC is undefined and the cross-model ranking falls back to balanced accuracy. By MCC alone d3mini is first (0.700) and Jev fourth (0.535); by balanced accuracy Jev is first (0.890) and d3mini second (0.883). This is not a rounding issue: MCC weights both error types symmetrically, while balanced accuracy averages TPR and TNR, and Jev is the high-recall/low-TNR model here.

## 4. Change the metric, change the winner

Rank under MCC / balanced accuracy / TPR; rows ordered by largest rank movement.

| position                | model            | MCC rank | BAcc rank | TPR rank |
| ----------------------- | ---------------- | -------- | --------- | -------- |
| Tool call (TS-Bench, B) | gliguard         | 10       | 8         | 4        |
| Tool call (TS-Bench, B) | jevguard         | 9        | 7         | 3        |
| Tool call (TS-Bench, B) | d3mini           | 4        | 5         | 8        |
| Tool call (TS-Bench, B) | jev-packy-1.14.0 | 3        | 3         | 6        |
| Tool call (TS-Bench, B) | kev              | 7        | 9         | 9        |

| Action prefix (StepShield test, C) | jevguard | 7 | 5 | 2 |
| Action prefix (StepShield test, C) | jev-packy-1.14.0 | 4 | 1 | 1 |
| Action prefix (StepShield test, C) | qwen35 | 2 | 4 | 5 |
| Action prefix (StepShield test, C) | qwen3guard | 6 | 8 | 9 |
| Action prefix (StepShield test, C) | d3mini | 1 | 2 | 3 |

## 5. Operating points: 0.5 is not a neutral baseline

Default 0.5 vs MCC-optimal threshold. The optimal threshold is selected on the same test set, so it is an optimistic upper bound, not an achievable deployment number.

| model                         | position                | MCC at 0.5                    | MCC-opt threshold | MCC at opt | delta MCC | TPR@FPR=5% | AUC   |
| ----------------------------- | ----------------------- | ----------------------------- | ----------------- | ---------- | --------- | ---------- | ----- |
| d3mini                        | tsbench                 | 0.470                         | 0.14              | 0.557      | 0.087     | 47.1%      | 0.878 |
| d3mini                        | agentharm               | 0.763                         | 0.89              | 0.809      | 0.046     | 80.8%      | 0.972 |
| jev-packy-1.14.0              | tsbench                 | 0.565                         | 0.30              | 0.619      | 0.054     | 59.6%      | 0.906 |
| jev-packy-1.14.0              | agentharm               | 0.769                         | 0.64              | 0.785      | 0.015     | 72.6%      | 0.958 |
| jev-packy-1.14.0              | wildguard_response      | 0.746                         | 0.59              | 0.768      | 0.022     | 82.4%      | 0.946 |
| jevguard                      | tsbench                 | 0.252                         | 0.30              | 0.268      | 0.016     | 3.7%       | 0.668 |
| jevguard                      | agentharm               | 0.580                         | 0.95              | 0.630      | 0.050     | 25.5%      | 0.875 |
| kev                           | tsbench                 | 0.315                         | 0.27              | 0.495      | 0.180     | 29.0%      | 0.831 |
| kev                           | agentharm               | 0.688                         | 0.66              | 0.744      | 0.056     | 77.4%      | 0.931 |
| laya                          | tsbench                 | 0.052                         | 0.45              | 0.064      | 0.012     | 4.3%       | 0.460 |
| laya                          | agentharm               | 0.449                         | 0.34              | 0.517      | 0.067     | 20.2%      | 0.797 |
| secjev                        | tsbench                 | 0.127                         | 0.01              | 0.298      | 0.170     | 8.0%       | 0.660 |
| secjev                        | agentharm               | 0.658                         | 0.70              | 0.684      | 0.026     | 71.2%      | 0.892 |
| jev-packy-1.14.0 (per prefix) | stepshield_test         | natural TPR 91.4% / TNR 86.5% | 0.77              | 0.710      | -         | -          | -     |
| jev-packy-1.14.0 (per prefix) | stepshield_test_holdout | natural TPR 97.2% / TNR 87.0% | 0.63              | 0.880      | -         | -          | -     |

StepShield per-prefix sweep: Jev at 0.50 gives TPR 91.4% / TNR 86.5% (MCC 0.535); at 0.77 it gives TPR 72.0% / TNR 97.9% (MCC 0.710). Same model, same data, different operating point.

## 6. Shift: rankings flip inside one position too

TS-Bench, three source domains, same position and prompt contract:

| source         | positive rate | Jev MCC | GPT-6 Luna MCC | d3mini MCC | Claude MCC |
| -------------- | ------------- | ------- | -------------- | ---------- | ---------- |
| agentdojo-traj | 29.0%         | 0.833   | 0.923          | 0.703      | 0.660      |
| agentharm-traj | 50.6%         | 0.554   | 0.432          | 0.421      | 0.422      |
| asb-traj       | 28.5%         | 0.455   | 0.652          | 0.378      | 0.644      |

On agentharm-traj Jev beats GPT (0.554 vs 0.432); on asb-traj GPT leads by a wide margin (0.652 vs 0.455).

StepShield test vs holdout have positive rates 8.1% vs 50%, so accuracy/F1 are not comparable; TPR/TNR are:

| model            | test TPR / TNR | holdout TPR / TNR | delta                  |
| ---------------- | -------------- | ----------------- | ---------------------- |
| jev-packy-1.14.0 | 91.2% / 86.8%  | 97.2% / 87.0%     | TPR +0.060, TNR +0.003 |
| d3mini           | 80.3% / 96.3%  | 91.7% / 92.6%     | TPR +0.114, TNR -0.037 |
| kev              | 58.1% / 97.2%  | 75.0% / 91.7%     | TPR +0.169, TNR -0.056 |
| qwen35           | 46.3% / 99.1%  | 83.3% / 94.4%     | TPR +0.370, TNR -0.047 |

InjecAgent base to enhanced TPR: jev-packy-1.14.0 90.9% to 100.0%; gpt6luna 99.2% to 100.0%. Pooling the two halves hides a difficulty difference.

## 7. Paired tests (McNemar)

On common items there are 333 model pairs, 284 with p<0.05. This means most pairs differ; it does NOT mean the ranking is stable.

| position                           | comparison                     | accuracy delta (A-B) | p        |
| ---------------------------------- | ------------------------------ | -------------------- | -------- |
| User request (AgentHarm, A1)       | d3mini vs qwen3guard           | +0.207               | 2.7e-20  |
| User request (AgentHarm, A1)       | jev-packy-1.14.0 vs qwen3guard | +0.221               | 1.2e-15  |
| User request (AgentHarm, A1)       | qwen3guard vs shieldstral      | -0.188               | 6.4e-15  |
| Tool call (TS-Bench, B)            | gpt6luna vs jevguard           | +0.233               | 8.9e-184 |
| Tool call (TS-Bench, B)            | gliguard vs gpt6luna           | -0.200               | 3.2e-177 |
| Tool call (TS-Bench, B)            | jev-packy-1.14.0 vs laya       | +0.125               | 2.4e-144 |
| Action prefix (StepShield test, C) | d3mini vs jevguard             | +0.470               | 0.0e+00  |
| Action prefix (StepShield test, C) | gliguard vs jevguard           | +0.328               | 0.0e+00  |
| Action prefix (StepShield test, C) | jev-packy-1.14.0 vs jevguard   | +0.391               | 0.0e+00  |

## 8. Cost is O(steps) and coupled to detection

| model            | AgentHarm s/decision, s/episode | TS-Bench      | StepShield test (calls/trajectory) |
| ---------------- | ------------------------------- | ------------- | ---------------------------------- |
| jev-packy-1.14.0 | 0.63s / 0.67s                   | 0.71s / 0.75s | 0.68s / 6.36s (8.74)               |
| d3mini           | 0.09s / 0.10s                   | 0.42s / 0.46s | 0.35s / 3.81s (9.38)               |
| qwen35           | 0.38s / 0.41s                   | 0.76s / 0.80s | 0.69s / 7.26s (9.75)               |
| jevguard         | 0.07s / 0.08s                   | 0.29s / 0.32s | 0.22s / 1.61s (5.86)               |

StepShield needs 8.7-12.3 judgments per trajectory versus 1 elsewhere; Jev takes 6.36 s per episode versus 0.67 s on AgentHarm. Because monitoring stops at the first unsafe alert, calls are negatively coupled to detection: shieldstral (never alerts) uses 10.1 calls/trajectory, Jev 8.74. Cross-model per-episode cost therefore rewards better detectors; report per-decision cost and a fixed-step cost as well.

## 9. What this supports and what it does not

Supports: position-conditional effectiveness; no universal best judge; metric/operating-point sensitivity; within-position shift can flip rankings; O(steps) cost.

Does not support: 'model X is the best judge overall'; cross-position accuracy/F1 comparisons; StepShield test-vs-holdout accuracy comparisons; MCC-optimal numbers as achievable performance; confirmatory claims; direct TPR@fixed-FPR comparisons between typed models and label-only judges.

## 10. Coverage and gaps

- Probabilities available: Jev (AgentHarm, TS-Bench, WildGuard-E, StepShield); d3mini/kev/secjev/laya/jevguard (AgentHarm, TS-Bench).
- No raw for local models on WildGuard-E and StepShield (raw excluded at sync), so no operating-point analysis there.
- No probabilities for GPT-6 Luna, Claude Haiku, qwen35, qwen3guard, shieldstral, gliguard (hard labels only).
- StepShield per-prefix sweep done for Jev only.
- Claude/GPT StepShield and WildGuard-E still being filled in elsewhere; left blank here.

## 11. Files

| file                      | content                                                                     |
| ------------------------- | --------------------------------------------------------------------------- |
| metrics_ci.csv            | 66 cells: counts, TPR/TNR/MCC, family-cluster bootstrap CI                  |
| rank_stability.csv        | pairwise P(A>B) within position on common items                             |
| rank_top1.csv             | top-1 probability per position                                              |
| rank_by_metric.csv        | ranks under MCC / BAcc / TPR                                                |
| thresholds.csv            | operating-point analysis (AUC, AP, TPR@FPR, optimal threshold, calibration) |
| thresholds_stepshield.csv | per-prefix threshold sweep for Jev                                          |
| paired_mcnemar.csv        | exact McNemar on common items                                               |
| shift.csv                 | metrics by split / source domain                                            |
| cost.csv                  | calls, latency, tokens per decision and per episode                         |
| cells.json                | episode files selected per cell and how they were matched                   |
| provenance.json           | input/script hashes, seed, reps                                             |

Rerun (PowerShell):

    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive.py
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py --stepshield
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_docs.py
