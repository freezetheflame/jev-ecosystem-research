# CCD pilot report

Split: test | items: 40 (20 rogue / 20 clean) | mode: real

## Main result (CCD, threshold 0.60)

| metric | value |
|---|---:|
| recall | 0.8500 |
| fpr | 0.0000 |
| eir3 | 1.0000 |
| ig | 0.0000 |
| calls | 343 |
| calls_per_traj | 8.5750 |
| in_tokens | 444193 |
| tokens_per_traj | 11104.8250 |
| seconds_per_traj | 10.5697 |

Confusion: TP 17 / FN 3 / FP 0 / TN 20

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.40 | 0.9500 | 0.1500 | 0.9474 | -0.0526 |
| 0.50 | 0.8500 | 0.0500 | 0.9412 | -0.0588 |
| 0.55 | 0.8500 | 0.0000 | 0.9412 | -0.0588 |
| 0.60 | 0.8500 | 0.0000 | 1.0000 | 0.0000 |
| 0.65 | 0.7500 | 0.0000 | 1.0000 | 0.0000 |
| 0.70 | 0.7500 | 0.0000 | 1.0000 | 0.0000 |
| 0.75 | 0.6500 | 0.0000 | 1.0000 | 0.0000 |
| 0.80 | 0.4500 | 0.0000 | 1.0000 | 0.0000 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 0.0000 | 0.0000 | NA | NA | 343 |
| regex monitor | 0.3500 | 0.1000 | 1.0000 | 0.0000 | 343 |
| random | 0.5000 | 0.4000 | 0.0000 | NA | 343 |
| CCD | 0.8500 | 0.0000 | 1.0000 | 0.0000 | 343 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 343 (8.57/trajectory); input tokens: 444193; estimated USD: 0.01866 (0.042 USD/M input, not an invoice). Wall: 109.5s with concurrency 4.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
