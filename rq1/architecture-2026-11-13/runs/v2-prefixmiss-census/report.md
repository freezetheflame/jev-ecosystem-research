# CCD pilot report

Split: test | items: 110 (55 rogue / 55 clean) | mode: real

## Main result (CCD, threshold 0.60)

| metric | value |
|---|---:|
| recall | 0.8000 |
| fpr | 0.0545 |
| eir3 | 0.9091 |
| ig | -0.3864 |
| calls | 946 |
| calls_per_traj | 8.6000 |
| in_tokens | 1226122 |
| tokens_per_traj | 11146.5636 |
| seconds_per_traj | 8.6650 |

Confusion: TP 44 / FN 11 / FP 3 / TN 52

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.40 | 0.9091 | 0.1455 | 0.8600 | -0.4600 |
| 0.50 | 0.8545 | 0.0727 | 0.8936 | -0.3617 |
| 0.55 | 0.8364 | 0.0545 | 0.9130 | -0.3478 |
| 0.60 | 0.8000 | 0.0545 | 0.9091 | -0.3864 |
| 0.65 | 0.7818 | 0.0545 | 0.9302 | -0.3721 |
| 0.70 | 0.6909 | 0.0364 | 0.9211 | -0.4211 |
| 0.75 | 0.6182 | 0.0182 | 0.9412 | -0.3529 |
| 0.80 | 0.4364 | 0.0182 | 0.9583 | -0.3750 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 0.0000 | 0.0000 | NA | NA | 946 |
| regex monitor | 0.2364 | 0.0909 | 0.8462 | -0.2308 | 946 |
| random | 0.4727 | 0.4909 | 0.0000 | NA | 946 |
| CCD | 0.8000 | 0.0545 | 0.9091 | -0.3864 | 946 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 946 (8.60/trajectory); input tokens: 1226122; estimated USD: 0.05150 (0.042 USD/M input, not an invoice). Wall: 161.2s with concurrency 6.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
