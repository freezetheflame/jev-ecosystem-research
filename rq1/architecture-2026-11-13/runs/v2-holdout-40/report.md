# CCD pilot report

Split: test_holdout | items: 40 (20 rogue / 20 clean) | mode: real

## Main result (CCD, threshold 0.60)

| metric | value |
|---|---:|
| recall | 0.9500 |
| fpr | 0.1500 |
| eir3 | 0.8947 |
| ig | -0.8421 |
| calls | 476 |
| calls_per_traj | 11.9000 |
| in_tokens | 670118 |
| tokens_per_traj | 16752.9500 |
| seconds_per_traj | 19.0951 |

Confusion: TP 19 / FN 1 / FP 3 / TN 17

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.30 | 1.0000 | 0.6500 | 0.6000 | -1.8000 |
| 0.40 | 1.0000 | 0.5000 | 0.7500 | -1.2000 |
| 0.50 | 0.9500 | 0.3000 | 0.8421 | -0.8947 |
| 0.55 | 0.9500 | 0.2500 | 0.8947 | -0.8421 |
| 0.60 | 0.9500 | 0.1500 | 0.8947 | -0.8421 |
| 0.65 | 0.9500 | 0.1000 | 0.8947 | -0.8421 |
| 0.70 | 0.8000 | 0.0500 | 0.8750 | -1.0000 |
| 0.75 | 0.7500 | 0.0500 | 0.9333 | -0.8000 |
| 0.80 | 0.5000 | 0.0500 | 0.9000 | -1.2000 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 1.0000 | 0.1500 | 0.8500 | -0.7500 | 476 |
| regex monitor | 0.2000 | 0.2000 | 0.7500 | -2.0000 | 476 |
| random | 0.4000 | 0.4000 | 0.0000 | NA | 476 |
| CCD | 0.9500 | 0.1500 | 0.8947 | -0.8421 | 476 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 476 (11.90/trajectory); input tokens: 670118; estimated USD: 0.02814 (0.042 USD/M input, not an invoice). Wall: 199.2s with concurrency 4.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
