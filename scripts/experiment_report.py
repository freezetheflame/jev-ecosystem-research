"""Audit saved experiment records and derive a report without model calls.

Resource numbers come from the existing jev_skill.monitor files. This module
does not change telemetry, recalculate prices, or modify source artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import uuid


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Expected JSON objects: {path.name}")
    return rows


def unique_rows(rows: list[dict], key: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        identifier = row.get(key)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"Missing {key}")
        if identifier in result:
            raise ValueError(f"Duplicate {key}: {identifier}; select attempts explicitly")
        result[identifier] = row
    return result


def number(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def binary_metrics(rows: list[dict], *, positive: str, negative: str) -> dict:
    if not positive or not negative or positive == negative:
        raise ValueError("Distinct positive and negative labels are required")
    counts = Counter(TP=0, FP=0, TN=0, FN=0)
    excluded = Counter()
    for row in rows:
        status = row.get("prediction_status")
        if status != "ok":
            excluded[status or "missing_status"] += 1
            continue
        gold, predicted = row.get("gold_label"), row.get("predicted_label")
        if gold is None:
            excluded["missing_gold"] += 1
            continue
        if gold not in (positive, negative) or predicted not in (positive, negative):
            raise ValueError("Unexpected label in binary comparison")
        if not row.get("gold_source"):
            raise ValueError("A scored classification requires gold_source")
        cell = ("TP" if predicted == positive else "FN") if gold == positive else (
            "FP" if predicted == positive else "TN")
        if row.get("confusion_cell") not in (None, "", cell):
            raise ValueError("Stored confusion_cell disagrees with raw labels")
        counts[cell] += 1
    tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))
    valid = sum(counts.values())
    divide = lambda a, b: a / b if b else None
    return {
        "recorded_n": len(rows), "valid_n": valid, "excluded": dict(excluded),
        "coverage_of_recorded_rows": divide(valid, len(rows)),
        **counts, "accuracy": divide(tp + tn, valid),
        "precision": divide(tp, tp + fp), "recall": divide(tp, tp + fn),
        "F1": divide(2 * tp, 2 * tp + fp + fn), "FPR": divide(fp, fp + tn),
        "FNR": divide(fn, tp + fn), "specificity": divide(tn, tn + fp),
        "positive_support": tp + fn, "negative_support": tn + fp,
    }


def monitor_records(paths: list[Path]) -> list[dict]:
    """Link each monitor invocation once, including separate resume segments."""
    result, seen = [], set()
    for path in paths:
        source = json.loads(path.read_text(encoding="utf-8"))
        run_id = source.get("run_id")
        if not isinstance(run_id, str) or not run_id or run_id in seen:
            raise ValueError("Missing or duplicate monitor run_id")
        seen.add(run_id)
        for field in ("wall_seconds", "call_seconds", "known_estimated_cost_usd"):
            if not number(source.get(field)):
                raise ValueError(f"Invalid monitor field: {field}")
        cost = source.get("estimated_cost_usd")
        if cost is not None and not number(cost):
            raise ValueError("Invalid monitor estimated cost")
        if source.get("unpriced_calls", 0) and cost is not None:
            raise ValueError("Monitor claims complete pricing despite unpriced calls")
        result.append({"summary_path": str(path.resolve()), **{
            key: source.get(key) for key in (
                "run_id", "status", "started_at", "finished_at", "wall_seconds",
                "call_seconds", "calls", "failed_calls", "input_tokens", "output_tokens",
                "missing_usage_calls", "known_estimated_cost_usd", "estimated_cost_usd",
                "unpriced_calls", "pricing_snapshot", "calls_file", "metadata")}})
    return result


def build_report(run_dir: Path, monitor_paths: list[Path]) -> dict:
    run_dir = run_dir.resolve()
    config_path = run_dir / "effective-config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan_path = run_dir / "plan.jsonl"
    if not plan_path.exists():
        raise ValueError("plan.jsonl is required to account for unstarted episodes")
    plan = unique_rows(read_rows(plan_path), "episode_id")
    episodes = unique_rows(read_rows(run_dir / "episodes.jsonl"), "episode_id")
    predictions = read_rows(run_dir / "predictions.jsonl")
    unique_rows(predictions, "prediction_id")
    issues = []
    if not episodes and plan:
        issues.append("No episode results recorded")
    for row in [*episodes.values(), *predictions]:
        identifier = row.get("episode_id")
        if identifier not in plan:
            raise ValueError("Result or prediction references an unplanned episode")
        expected = plan[identifier]
        for key in ("dataset_id", "split", "arm", "condition"):
            if not expected.get(key) or row.get(key) != expected[key]:
                raise ValueError(f"Missing or mismatched pairing field: {key}")

    groups = defaultdict(list)
    for row in plan.values():
        keys = ("dataset_id", "split", "arm", "condition")
        if any(not row.get(key) for key in keys):
            raise ValueError("Plan must identify dataset_id, split, arm and condition")
        groups[tuple(row[key] for key in keys)].append(row)
    coverage = []
    for key, planned in sorted(groups.items()):
        present = [episodes[row["episode_id"]] for row in planned if row["episode_id"] in episodes]
        task_ids = {row.get("task_id") for row in planned}
        if None in task_ids or "" in task_ids:
            raise ValueError("Plan requires original task_id for unique task counts")
        result = dict(zip(("dataset_id", "split", "arm", "condition"), key))
        result.update(planned_episodes=len(planned), original_tasks=len(task_ids),
                      recorded_episodes=len(present), unrecorded_episodes=len(planned) - len(present),
                      statuses=dict(Counter(row.get("status", "unknown") for row in present)))
        for field in ("utility_success", "attack_success"):
            for row in present:
                if row.get(field) is not None and type(row[field]) is not bool:
                    raise ValueError(f"{field} must be boolean or null")
                if type(row.get(field)) is bool and row.get("grading_status") != "valid":
                    raise ValueError("Task outcomes require valid grading_status")
            positive = sum(row.get(field) is True for row in present)
            known = sum(type(row.get(field)) is bool for row in present)
            result[field] = {"true": positive, "false": known - positive,
                             "known": known, "unknown_of_planned": len(planned) - known}
        coverage.append(result)
    if len(episodes) < len(plan):
        issues.append("Planned episodes remain unrecorded; results are partial")

    classification = config.get("analysis", {}).get("classification", {})
    grouped_predictions = defaultdict(list)
    classification_keys = ("dataset_id", "split", "arm", "condition", "classification_unit", "target_event")
    for row in predictions:
        if any(not row.get(key) for key in classification_keys):
            raise ValueError("Predictions require dataset, split, arm, condition, unit and target")
        if (row["classification_unit"] != classification.get("unit") or
                row["target_event"] != classification.get("target_event")):
            raise ValueError("Prediction semantics differ from the frozen classification contract")
        grouped_predictions[tuple(row[key] for key in classification_keys)].append(row)
    matrices = []
    for key, rows in sorted(grouped_predictions.items()):
        metrics = binary_metrics(rows, positive=classification.get("positive_label"),
                                 negative=classification.get("negative_label"))
        matrices.append({**dict(zip(classification_keys, key)), **metrics})
    if not predictions:
        issues.append("No classification records; TP/FP/TN/FN are not computed")
    elif any(matrix["excluded"] for matrix in matrices):
        issues.append("Some classification records are unscorable; see exclusions and coverage")
    if predictions and not classification.get("planned_unit_manifest"):
        issues.append("Classification unit plan absent; coverage is only over recorded rows")

    monitors = monitor_records(monitor_paths)
    if not monitors:
        issues.append("Monitor summaries not linked; time and fees remain unknown")
    if any(row["status"] != "completed" for row in monitors):
        issues.append("Monitor has unfinished or error invocations; preserve partial telemetry")
    expected_monitor_ids = config.get("measurement", {}).get("monitor", {}).get("run_ids")
    if monitors and expected_monitor_ids is None:
        issues.append("Monitor run IDs not registered in config; association needs verification")
    elif monitors and set(expected_monitor_ids) != {row["run_id"] for row in monitors}:
        raise ValueError("Monitor run IDs differ from configured invocation links")
    required = ("dataset-manifest.json", "reproduce.txt", "report.md")
    for name in required:
        if not (run_dir / name).exists():
            issues.append(f"Required run artifact absent: {name}")
    for key in ("main_agent_config", "benchmark"):
        if not config.get(key):
            issues.append(f"Effective configuration unresolved: {key}")
    inputs = [config_path, plan_path, run_dir / "episodes.jsonl", run_dir / "predictions.jsonl", *monitor_paths]
    for row in monitors:
        calls_path = Path(row["calls_file"]) if row.get("calls_file") else None
        if calls_path is not None and calls_path.is_file():
            inputs.append(calls_path)
        else:
            issues.append(f"Monitor calls file unavailable for invocation {row['run_id']}")
    inputs.append(Path(__file__).resolve())
    return {
        "record_kind": "derived_offline_report_not_a_new_experiment",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_directory": str(run_dir), "protocol_version": config.get("protocol_version"),
        "audit_scope": "Record structure and arithmetic only; not scientific validity or run authenticity",
        "issues": issues, "episode_groups": coverage, "binary_classification": matrices,
        "monitor_invocations": monitors,
        "resource_policy": "Use original monitor estimates; local compute unpriced unless separately estimated",
        "time_policy": "Monitor wall time is per invocation; call_seconds is not end-to-end latency",
        "input_sha256": {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in inputs if path.exists()},
    }


def markdown(report: dict) -> str:
    lines = ["# 实验记录离线核对", "", "此文件从已有记录生成，没有发起新模型调用。", "",
             "## 记录缺口", ""]
    lines.extend([f"- {issue}" for issue in report["issues"]] or ["- 本工具检查范围内未发现缺口。"])
    lines += ["", "## 二分类基础计数", "",
              "| 数据集 / split / 组 / 条件 | 记录数 | 有效数 | TP | FP | TN | FN |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for row in report["binary_classification"]:
        name = "/".join(str(row[key]) for key in ("dataset_id", "split", "arm", "condition"))
        name = name.replace("|", "\\|").replace("\n", " ")
        lines.append("| " + name + " | " + " | ".join(str(row[key]) for key in
                     ("recorded_n", "valid_n", "TP", "FP", "TN", "FN")) + " |")
    lines += ["", "完整任务计数、派生指标、monitor 分段记录与输入 hash 见 summary.json。",
              "时间与费用沿用原 monitor；本工具不重新计价。", "",
              "本核对只检查记录结构与算术，不证明实验真实性、科学有效性或模型可替代性。", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--monitor-summary", action="append", default=[], type=Path,
                        help="Original monitor *.run.json; repeat for resume segments")
    parser.add_argument("--out-dir", type=Path, help="Must be a new directory")
    args = parser.parse_args()
    try:
        report = build_report(args.run_dir, args.monitor_summary)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = args.out_dir or args.run_dir / "analysis" / (stamp + "-" + uuid.uuid4().hex[:6])
        out.mkdir(parents=True, exist_ok=False)
        (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                                    allow_nan=False) + "\n", encoding="utf-8")
        (out / "audit-report.md").write_text(markdown(report), encoding="utf-8")
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Experiment report failed: {error}\n")
    print(json.dumps({"output": str(out.resolve()), "record_issues": len(report["issues"])}))


if __name__ == "__main__":
    main()
