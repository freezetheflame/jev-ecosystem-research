# rq1/ext-2026-11-13 - additional analysis (position-conditional effectiveness / CIs / operating points / shift)

ADDITIONAL, read-only derived analysis of the official summary in rq1/summary/.
It does not modify rq1/summary/ or data/agent-security-study/runs/, and it calls no model API.
Generated 2026-11-13. Scripts: derive.py (metrics/CIs/rank/McNemar/shift/cost), derive_thresholds.py (operating points),
derive_docs.py (documents), verify.py (independent re-derivation).

## Why this exists

The official table now uses MCC and TPR/TNR with trivial baselines (rebuilt 2026-11-13 00:56). Three things remain here:

1. Intervals and identifiability: family-cluster bootstrap, answering "is the top-1 real?".
2. Operating points: probabilities parsed from raw/response.body, answering "is 0.5/argmax a fair comparison?".
3. Within-position shift and cost: source-domain splits, plus O(steps) cost and its coupling to detection.
4. ANALYSIS_STATUS.md: evidence level, allowed/forbidden claims, pre-freeze checklist, unverified items.

## Headline results (details in RESULTS.md)

- Top-1 is unambiguous only where p(top-1) is near 100%: GPT-6 Luna on TS-Bench and InjecAgent.
- At the request position (Jev 52% vs d3mini 40%) and on the StepShield holdout (56% vs 40%) it is a coin flip.
- Change the metric and the winner changes: StepShield test ranks Jev 4th by MCC but 1st by balanced accuracy and TPR;
  TS-Bench ranks Claude 2nd by MCC but 1st by TPR.
- 0.5 is not neutral: MCC-optimal thresholds span 0.01-0.95; on StepShield, Jev at 0.50 -> 0.77 moves MCC 0.535 -> 0.710.
- TS-Bench source domains flip the ranking (agentharm-traj: Jev 0.554 > GPT 0.432; asb-traj: GPT 0.652 > Jev 0.455).
- StepShield needs 8.7-12.3 judgments per trajectory; Jev 6.36 s/episode vs 0.67 s on AgentHarm; cost is coupled to detection.

## Method notes

- Merge rule for repaired campaigns: files sorted by mtime; an ok row replaces a failed one; between two ok rows the later file wins.
  The exact file list for each cell is in cells.json.
- Family-cluster bootstrap, 1000 reps, seed 20261113; common-item restriction for rank comparisons.
- Threshold sweep uses p>=0.5 as the natural point; agreement with the stored argmax is 99.8-100% (argmax_agreement column).
- verify.py independently re-derives all 66 cells with a separate merge implementation (0 mismatches) and re-checks input hashes.

## Files

| file | content |
|---|---|
| RESULTS.md | generated results report with tables |
| ANALYSIS_STATUS.md | evidence level, allowed/forbidden claims, pre-freeze checklist, unverified items |
| metrics_ci.csv | 66 cells: counts + TPR/TNR/MCC + family-cluster bootstrap CI |
| rank_stability.csv / rank_top1.csv | pairwise P(A>B) and top-1 probability within each position |
| rank_by_metric.csv | ranks under MCC / BAcc / TPR |
| thresholds.csv / thresholds_stepshield.csv | operating points and per-prefix threshold sweep |
| paired_mcnemar.csv | exact McNemar on common items |
| shift.csv | metrics by split / source domain |
| cost.csv | calls, latency, tokens per decision and per episode |
| cells.json | episode files selected per cell and how they were matched |
| provenance.json | input/script sha256, seed, reps |
| verify.py | independent re-derivation and hash check |

## Rerun (PowerShell)

    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive.py
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_thresholds.py --stepshield
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/derive_docs.py
    .venv-benchmark/Scripts/python.exe rq1/ext-2026-11-13/verify.py

## Boundaries

- Every number is descriptive: one repeat, exposed public splits, no pre-registered threshold; not confirmatory.
- Claude/GPT StepShield and WildGuard-E are still being completed elsewhere; left blank, no in-progress numbers.
- Local models' WildGuard-E / StepShield raw files are not on this machine, so no operating-point analysis there.
- API fees are list-price estimates, not invoices; local compute is unpriced.
