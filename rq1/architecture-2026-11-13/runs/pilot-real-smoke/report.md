# CCD pilot report

Split: test_holdout | items: 4 (2 rogue / 2 clean) | mode: real

## Main result (CCD, threshold 0.50)

| metric | value |
|---|---:|
| recall | 1.0000 |
| fpr | 0.0000 |
| eir3 | 0.5000 |
| ig | -6.0000 |
| calls | 40 |
| calls_per_traj | 10.0000 |
| in_tokens | 47298 |
| tokens_per_traj | 11824.5000 |
| seconds_per_traj | 13.0962 |

Confusion: TP 2 / FN 0 / FP 0 / TN 2

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.30 | 1.0000 | 0.5000 | 0.0000 | -6.5000 |
| 0.40 | 1.0000 | 0.0000 | 0.5000 | -6.0000 |
| 0.50 | 1.0000 | 0.0000 | 0.5000 | -6.0000 |
| 0.60 | 1.0000 | 0.0000 | 0.5000 | -6.0000 |
| 0.70 | 1.0000 | 0.0000 | 0.5000 | -6.0000 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 1.0000 | 0.0000 | 0.0000 | NA | 40 |
| regex monitor | 0.0000 | 0.0000 | NA | NA | 40 |
| random | 1.0000 | 1.0000 | 0.0000 | NA | 40 |
| CCD | 1.0000 | 0.0000 | 0.5000 | -6.0000 | 40 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 40 (10.00/trajectory); input tokens: 47298; estimated USD: 0.00199 (0.042 USD/M input, not an invoice). Wall: 29.9s with concurrency 2.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
