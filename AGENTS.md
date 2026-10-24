# Research execution rules

For Jev / LLM agent-security experiments, first read
`docs/model-evaluation/agent-security-experiment-protocol.md` and the selected
study's current config and decision log. Follow `docs/organization.md`.

- Never invent measurements, executions, references, labels, or reviewer approval.
- Keep raw requests, responses, traces, failures and prior runs; derive reported
  numbers with versioned code. Do not hand-edit generated results.
- Distinguish planning, mock, smoke, pilot, partial, failed and confirmatory work.
- Freeze the comparison before confirmatory execution. Do not silently change
  models, prompts, thresholds, samples, seeds, budgets, parsers or graders.
- Existing exposed samples are development evidence unless an exposure audit
  establishes otherwise. Never tune on confirmation results.
- Missing parameters remain unresolved; do not invent an approved configuration.
- Preserve unrelated workspace edits. Never include credentials in artifacts.
- Report what actually executed, its evidence paths, and what remains unverified.
- Every experiment, including pilot and smoke runs, must produce the required
  record in `data/agent-security-study/report.template.md`: dataset identity and
  exact item counts/IDs, time and API fees, applicable TP/FP/TN/FN with label
  semantics and coverage, full effective model/run parameters, exact prompts or
  request structures, raw outputs, and a rerun command/environment reference.
  Mark unavailable or inapplicable fields with a reason; never invent values.
  Local compute is unpriced by default; any estimate must be separate and state
  its pricing assumptions. Do not present API fees as total compute cost.
- Preserve the existing `D:/projects/jev/jev_skill/monitor.py` implementation and
  interface. Reuse its telemetry and pricing snapshots; never double-instrument
  calls or replace unknown costs with zero. Read
  `docs/infrastructure/experiment-framework.md` before connecting a new runner.
  Keep request construction, gold/graders, analysis, and resource monitoring in
  separate responsibilities. Do not claim this monitor enforces budget limits.
