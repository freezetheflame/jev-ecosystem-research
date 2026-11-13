# Analysis status and declarations (RQ1 additional analysis)

Generated 2026-11-12T17:19:26Z. Applies to all derived tables under rq1/ext-2026-11-13/.

## 1. Evidence level

- Descriptive: one repeat, exposed public splits, no pre-registered threshold/metric/sample size, no freeze manifest, no agent-loop execution.
- Reproducible: all numbers re-derived by derive.py / derive_thresholds.py from episodes.jsonl and raw/. Input and script hashes in provenance.json (metrics_full sha256=0b7490e0d2eeeb82..., time_tokens sha256=29aa81ffbf0e83f1...).
- Consistent: 66 non-baseline cells match rq1/summary/metrics_full.csv TP/FP/TN/FN exactly (built-in matching; mismatches abort the row and list candidates).
- Independently verified: verify.py re-derives all 66 cells from cells.json with a separate merge implementation; 0 mismatches, and three spot-checked MCC values match to 6 decimals. Input file hashes are re-checked against provenance.json.
- Non-replacing: the official summary remains rq1/summary/. Nothing under runs/ or rq1/summary/ is modified by this analysis.

## 2. Allowed in the paper (exploratory evidence)

- Position-conditional effectiveness; magnitude of within-model cross-position change; no stable cross-position ranking.
- Top-1 is often unidentifiable: report top-1 probability and bootstrap CIs rather than a league table.
- Metric sensitivity: MCC / balanced accuracy / TPR select different winners.
- Operating-point sensitivity: 0.5/argmax is arbitrary; MCC-optimal thresholds differ strongly (with the same-test-set selection caveat).
- Within-position shift: TS-Bench source domains flip the ranking.
- Cost structure: StepShield is O(steps); one order of magnitude above other positions; cost coupled to detection.

## 3. Not allowed

- 'Model X is the best overall judge' or 'X can replace an LLM security module'.
- Any cross-position accuracy/F1 comparison; StepShield test-vs-holdout accuracy comparison.
- Presenting MCC-optimal numbers as achievable performance (selected on the test set).
- Calling this confirmatory, blind, or pre-registered; treating this pilot as generalization evidence.
- Comparing typed-model TPR@fixed-FPR against label-only generative judges.

## 4. Required before freezing (protocol section 3)

1. Freeze benchmark commit, splits, task/attack IDs and hashes; mark development exposure.
2. Freeze the threshold-selection procedure per position (select on dev, never on test) and the primary metric (suggest MCC + TPR@fixed-FPR).
3. Freeze repeat count and clustering unit; report family-clustered CIs.
4. Record effective parameters, provider/endpoint and served model for every component; Jev currently goes through a Packy relay.
5. Complete or explicitly leave blank Claude/GPT StepShield and WildGuard-E.
6. Sync raw/ for local models (otherwise no operating-point analysis) or declare hard-label-only comparisons.
7. Pre-register multiple-comparison handling and stopping rules; publish a freeze manifest before the final table.

## 5. Unverified

- Whether the Packy relay serving jev-1.14.0 is weight-equivalent to official/OpenLux (only the model id is recorded).
- Local models' WildGuard-E / StepShield raw files are not on this machine, so no probability analysis there.
- Claude/GPT StepShield still being completed elsewhere; left blank here.
- All API fees are list-price estimates, not invoices; local compute is unpriced.
