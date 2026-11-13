"""Inventory existing research artifacts without importing or running benchmark code."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def counts(rows: list[dict], key: str) -> dict:
    return dict(sorted(Counter(str(r.get(key)) for r in rows).items()))


def file_info(path: Path) -> dict:
    return {"path": path.as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    out = args.out.resolve()
    # Keep the audit output separate from the source project.
    if out == source or source in out.parents:
        raise ValueError("Output must be outside the source project")
    unified_path = source / "bench/data/unified.jsonl"
    rows = read_rows(unified_path)
    by_corpus = defaultdict(list)
    for row in rows:
        by_corpus[row["corpus"]].append(row)
    corpus_summary = {}
    for corpus, items in sorted(by_corpus.items()):
        corpus_summary[corpus] = {
            "rows": len(items), "labels": counts(items, "label"),
            "stages": counts(items, "text_stage"),
            "label_semantics": counts(items, "label_semantics"),
            "source_ids": counts(items, "source_id"),
        }
    scans = []
    unified_uids = {r["uid"] for r in rows}
    for path in sorted((source / "bench/data/scans").rglob("*.jsonl")):
        items = read_rows(path)
        uids = [r.get("uid") for r in items]
        scans.append({
            **file_info(path), "rows": len(items),
            "unique_nonnull_uids": len({u for u in uids if u is not None}),
            "rows_with_uid_outside_current_unified": sum(u not in unified_uids for u in uids),
            "rows_with_numeric_score": sum(type(r.get("score")) in (int, float) for r in items),
            "rows_with_error": sum(bool(r.get("error")) for r in items),
            "models": counts(items, "model"), "profiles": counts(items, "profile"),
            "fingerprints": counts(items, "fingerprint"), "corpora": counts(items, "corpus"),
            "rows_with_latency_ms": sum(r.get("latency_ms") is not None for r in items),
            "rows_with_nonempty_usage": sum(bool(r.get("usage")) for r in items),
            "field_names": sorted({k for r in items for k in r}),
        })
    raw_files = []
    for name in ("agentdojo", "tsbench"):
        raw_files.extend(file_info(p) for p in sorted((source / "bench/raw" / name).rglob("*")) if p.is_file())
    episodes_path = source / "harness/runs/gate-placement/episodes.jsonl"
    episodes = read_rows(episodes_path)
    inventory = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": source.as_posix(),
        "scope": "Local inventory, not a rerun or validation of labels/model performance",
        "unified": {**file_info(unified_path), "rows": len(rows),
                    "unique_uids": len(unified_uids), "labels": counts(rows, "label"),
                    "corpora": corpus_summary},
        "scans": scans, "raw_source_files": raw_files,
        "agentdojo_static_variants": dict(Counter(str(r.get("meta", {}).get("variant")) for r in by_corpus["agentdojo"])),
        "tsbench_groups": dict(Counter(str(r.get("meta", {}).get("tsbench_group")) for r in by_corpus["ts_bench"])),
        "scripted_harness": {**file_info(episodes_path), "rows": len(episodes),
            "unique_task_ids": len({r["taskId"] for r in episodes}),
            "guards": counts(episodes, "guard"),
            "evidence_boundary": "Scripted policy and simulated tools; not a live LLM-agent evaluation"},
    }
    # A development audit queue, selected without looking at model predictions.
    # The extracted prompt is not a complete executable scenario or a gold label.
    grouped = defaultdict(list)
    for row in by_corpus["agentdojo_user"]:
        grouped[row["meta"]["agentdojo_suite"]].append(row)
    candidates = []
    for suite, items in sorted(grouped.items()):
        selected = sorted(items, key=lambda r: hashlib.sha256(("audit-20261015:" + r["uid"]).encode()).hexdigest())[:6]
        for row in selected:
            meta = row["meta"]
            raw_path = source / "bench/raw/agentdojo" / f"{meta['agentdojo_version']}.{suite}.user_tasks.py"
            candidates.append({
                "uid": row["uid"], "suite": suite, "task_class": meta["agentdojo_task"],
                "local_patch_version": meta["agentdojo_version"],
                "raw_task_definition": raw_path.as_posix(),
                "raw_task_definition_exists": raw_path.exists(),
                "raw_task_definition_sha256": digest(raw_path) if raw_path.exists() else None,
                "text_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
                "status": "pending_manual_audit", "purpose": "development_only",
                "injection_task_id": None, "attack_payload": None,
                "executable_environment_verified": False, "action_gold": None,
            })
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    queue = {"selection": "Up to six per suite, SHA-256 order of audit-20261015:<uid>; no prediction filtering",
             "source_unified_sha256": inventory["unified"]["sha256"],
             "limitations": "Local extracted prompts only; not a random sample of the full upstream benchmark; task families must remain outside final confirmation data once used for development.",
             "candidates": candidates}
    (out / "review-candidates.json").write_text(json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"unified_rows": len(rows), "unique_uids": len(unified_uids),
        "corpora": {k: v["rows"] for k, v in corpus_summary.items()},
        "scans": [{"name": Path(s["path"]).relative_to(source).as_posix(), "rows": s["rows"],
                   "scored": s["rows_with_numeric_score"], "errors": s["rows_with_error"]} for s in scans],
        "variants": inventory["agentdojo_static_variants"], "tsbench_groups": inventory["tsbench_groups"],
        "scripted_tasks": inventory["scripted_harness"]["unique_task_ids"],
        "audit_candidates": len(candidates)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
