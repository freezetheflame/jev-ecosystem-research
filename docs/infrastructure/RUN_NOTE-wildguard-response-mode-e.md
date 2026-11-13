# RUN_NOTE — WildGuardTest Mode E (Response Inspection)

Prepared: 2026-11-10 17:33:54 Asia/Shanghai. Code and docs are on the hecPC working tree only. This campaign was NOT launched: local StepShield (`full-local-stepshield-server-v1`) was still running (secjev in progress; jevguard and kev still queued). The live server pack was not updated, so a later auto_resume cannot pick up a hash or contract change mid-campaign.

## Contract (additive; A1 path unchanged)

- Dataset key: `wildguardtest-response` (not in `--datasets all`).
- Mode code: `E`. Contract: `response_risk_classification`.
- Model input: official WildGuardTest `prompt` (as `user_request`) and `response` (as `assistant_response`). Gold labels and refusal fields are not in the view.
- Gold: native `response_harm_label` (`harmful`=1, `unharmful`=0, `null`=unknown). Official test parquet on this machine: 1,725 rows; 284 / 1,425 / 16. All 1,725 are planned and called; the 16 unknowns stay out of the binary confusion matrix.
- Frozen `wildguardtest` remains Mode A1 prompt-harm (`prompt_harm_label` 754 / 945 / 26). Do not overwrite `full-local-wildguard-tsbench-v1` or any server copy of that cell.
- Same official files: `data/agent-security-study/datasets/full-suite-v1/wildguardtest/` (no second download).

## When GPU is free (after local StepShield 9/9)

Suggested command, new campaign only:

```
.venv/bin/python scripts/full_benchmark.py run --models local --datasets wildguardtest-response --campaign full-local-wildguard-response-v1
```

Copy the hecPC code/docs into the server pack only after StepShield no longer needs the frozen pack scripts for resume. Leave vLLM `:18080` alone unless a later start doc says otherwise. Preserve all finished cells, including old laya TS-Bench numbers and the old WildGuard prompt-harm run. Defer `full-local-laya-longsplit-tsbench-v1` until after this WildGuard response rerun.

## Docs

- `docs/infrastructure/full-benchmark-operations.md` — five-row mapping, LaTeX draft with TODO cite keys, Mode E row counts.
- `docs/model-evaluation/agent-security-evaluation-modes.md` — 2026-11-10 Mode E addendum.
- Unit tests: `security_bench/tests/test_full_suite.py` (5 tests OK, including A1 regression).