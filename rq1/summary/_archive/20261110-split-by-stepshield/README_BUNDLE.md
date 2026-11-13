# rq1 non-StepShield bundle

Includes:
- summary/*: consolidated metrics (accuracy/F1 and full rates incl. FNR/FPR/TNR/MCC), plus time/token summaries in non_stepshield_time_tokens.md and .csv (added 2026-11-11)
- episodes/<dataset>/<campaign>/<model>/<cell>/episodes.jsonl: per-episode raw results
- configs/<dataset>/<campaign>/<model>/<cell>/{effective-config.json,manifest.json,pricing-snapshot.json}: provenance/config snapshots

Datasets: TS-Bench, AgentHarm, InjecAgent, WildGuardTest. StepShield is NOT included (still running; will be bundled separately).
Raw request/response dirs (raw/) and events.jsonl are NOT included to keep the bundle small; they remain in the workspace runs/ tree.

Notes:
- TS-Bench scorable=5401 (1781 controversial 0.5 gold=None excluded). claudehaiku API 33 failed, secjev 124 failed (kept).
- AgentHarm 416 (208/208). jev API campaigns all failed; included as evidence.
- InjecAgent 2108 all-positive (accuracy=recall, precision trivially 1).
- WildGuard 1725; laya 11 failed, gpt6luna 5 failed.
