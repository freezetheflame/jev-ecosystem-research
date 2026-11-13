# CCD pilot report

Split: test | items: 40 (20 rogue / 20 clean) | mode: real

## Main result (CCD, threshold 0.50)

| metric | value |
|---|---:|
| recall | 1.0000 |
| fpr | 0.1000 |
| eir3 | 0.5000 |
| ig | -2.4500 |
| calls | 319 |
| calls_per_traj | 7.9750 |
| in_tokens | 382520 |
| tokens_per_traj | 9563.0000 |
| seconds_per_traj | 6.8792 |

Confusion: TP 20 / FN 0 / FP 2 / TN 18

## Threshold sweep (no extra calls)

| thr | recall | fpr | eir3 | ig |
|---:|---:|---:|---:|---:|
| 0.20 | 1.0000 | 0.6500 | 0.3000 | -3.9000 |
| 0.30 | 1.0000 | 0.2500 | 0.5000 | -2.8500 |
| 0.40 | 1.0000 | 0.2000 | 0.5000 | -2.7000 |
| 0.50 | 1.0000 | 0.1000 | 0.5000 | -2.4500 |
| 0.55 | 0.9000 | 0.0000 | 0.5556 | -2.1111 |
| 0.60 | 0.8500 | 0.0000 | 0.5294 | -2.2353 |
| 0.65 | 0.7000 | 0.0000 | 0.5714 | -1.4286 |
| 0.70 | 0.7000 | 0.0000 | 0.5714 | -1.4286 |
| 0.75 | 0.6500 | 0.0000 | 0.6154 | -1.1538 |
| 0.80 | 0.6500 | 0.0000 | 0.6154 | -1.1538 |

## Baselines on the same items

| system | recall | fpr | eir3 | ig | calls |
|---|---:|---:|---:|---:|---:|
| prefix (existing Jev) | 0.9500 | 0.1000 | 0.7895 | -1.1053 | 319 |
| regex monitor | 0.1000 | 0.1500 | 0.0000 | -2.0000 | 319 |
| random | 0.7000 | 0.4000 | 0.0000 | NA | 319 |
| CCD | 1.0000 | 0.1000 | 0.5000 | -2.4500 | 319 |

## Official StepShield reference (test_holdout, published)

| detector | EIR@3 | recall | FPR | F1 | IG |
|---|---:|---:|---:|---:|---:|
| llm_judge | 0.890 | 0.954 | 0.056 | 0.950 | -0.4 |
| static_guard | 0.230 | 0.861 | 0.778 | 0.650 | -5.0 |
| constraint_guard | 0.080 | 0.241 | 0.250 | 0.320 | -5.3 |
| hybrid_guard | 0.400 | 0.759 | 0.444 | 0.690 | -2.7 |
| random | 0.120 | 0.500 | 0.500 | 0.500 | -3.0 |

## Cost and speed

Jev calls: 319 (7.97/trajectory); input tokens: 382520; estimated USD: 0.01607 (0.042 USD/M input, not an invoice). Wall: 75.4s with concurrency 4.
LLM calls in this run: 0. Official LLMJudge uses one LLM call per step (~n_steps per trajectory).

## Caveats

- Pilot, not confirmatory: threshold not tuned on dev; small n; no paired test.
- CCD probes reuse task.constraints from StepShield, so no checklist-extraction LLM call was needed for this dataset.
- Compare against official numbers only on the same split; official LLMJudge is GPT-4.1-mini, not our models.
