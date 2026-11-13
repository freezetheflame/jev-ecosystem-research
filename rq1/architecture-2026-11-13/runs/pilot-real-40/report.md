# CCD pilot report

Split: test_holdout | items: 40 (20 rogue / 20 clean) | mode: real

## Main result (CCD, threshold 0.50)

| metric | value |
|---|---:|
| recall | 0.9000 |
| fpr | 0.3500 |
| eir3 | 0.7778 |
| ig | -1.2778 |
| calls | 449 |
| calls_per_traj | 11.2250 |
| in_tokens | 499322 |
| tokens_per_traj | 12483.0500 |
| seconds_per_traj | 13.3174 |

Confusion: TP 18 / FN 2 / FP 7 / TN 13

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.30 | 1.0000 | 0.7000 | 0.5000 | -2.7000 |
| 0.40 | 1.0000 | 0.5000 | 0.6500 | -1.9000 |
| 0.50 | 0.9000 | 0.3500 | 0.7778 | -1.2778 |
| 0.60 | 0.8500 | 0.1000 | 0.8235 | -1.0000 |
| 0.70 | 0.7500 | 0.1000 | 0.8667 | -1.0667 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 1.0000 | 0.1500 | 0.0000 | NA | 449 |
| regex monitor | 0.2000 | 0.2000 | 0.7500 | -2.0000 | 449 |
| random | 0.4500 | 0.6000 | 0.0000 | NA | 449 |
| CCD | 0.9000 | 0.3500 | 0.7778 | -1.2778 | 449 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 449 (11.22/trajectory); input tokens: 499322; estimated USD: 0.02097 (0.042 USD/M input, not an invoice). Wall: 142.7s with concurrency 4.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
