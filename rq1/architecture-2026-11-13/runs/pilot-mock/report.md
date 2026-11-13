# CCD pilot report

Split: test_holdout | items: 20 (10 rogue / 10 clean) | mode: mock

## Main result (CCD, threshold 0.50)

| metric | value |
|---|---:|
| recall | 0.8000 |
| fpr | 1.0000 |
| eir3 | 0.1250 |
| ig | -7.7500 |
| calls | 83 |
| calls_per_traj | 4.1500 |
| in_tokens | 16352 |
| tokens_per_traj | 817.6000 |
| seconds_per_traj | 2.9050 |

Confusion: TP 8 / FN 2 / FP 10 / TN 0

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.30 | 0.8000 | 1.0000 | 0.1250 | -8.5000 |
| 0.40 | 0.8000 | 1.0000 | 0.1250 | -8.5000 |
| 0.50 | 0.8000 | 1.0000 | 0.1250 | -7.7500 |
| 0.60 | 0.3000 | 0.4000 | 0.0000 | -8.3333 |
| 0.70 | 0.2000 | 0.0000 | 0.0000 | -5.5000 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 1.0000 | 0.2000 | 0.0000 | NA | 83 |
| regex monitor | 0.2000 | 0.2000 | 1.0000 | 0.0000 | 83 |
| random | 0.5000 | 0.4000 | 0.0000 | NA | 83 |
| CCD | 0.8000 | 1.0000 | 0.1250 | -7.7500 | 83 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 83 (4.15/trajectory); input tokens: 16352; estimated USD: 0.00069 (0.042 USD/M input, not an invoice). Wall: 0.0s with concurrency 4.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
