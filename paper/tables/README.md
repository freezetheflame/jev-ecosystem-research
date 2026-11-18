# RQ1/RQ2 tables

Generated 2026-11-18 from rq1/summary/metrics_full.csv and rq1/summary/time_tokens.csv.
Generation scripts: gen_rq1_table.py, gen_rq2_table.py.

## RQ1 rq1-effectiveness.tex

- MF1 = macro-F1 computed from official TP/FP/TN/FN.
- MCC = Matthews correlation coefficient, reported x100.
- FNR and FPR are included as requested.
- InjecAgent (External Content) is positives-only: MCC undefined; MF1 is positive-class F1.
- Shieldstral on StepShield test is a constant (all-safe) predictor: MCC undefined.
- Action uses StepShield test (7,935); StepShield holdout (216) is not in this table.
- Values match metrics_full.csv counts; no estimates.

## RQ2 rq2-cost-latency.tex

- Time columns are episode_mean_seconds and episode_p95_seconds per evaluated item; for Action they are per trajectory (the judge is called once per visible prefix, 5.9-10.1 calls/trajectory).
- Cost per 1,000 items = input tokens x input price + output tokens x output price.
- Prices: Jev 0.042 USD/M input, 0 output; GPT-6 Luna 0.044/0.22; Claude Haiku 5.5 0.008824/0.04412.
- Local models are unpriced (local compute is not zero cost).
- List-price estimates, not invoices.

## Columns

See the .csv companions for machine-readable values.
