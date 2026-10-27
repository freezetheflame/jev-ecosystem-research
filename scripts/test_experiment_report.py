"""Offline arithmetic/provenance checks; fixtures are not research results."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiment_report import binary_metrics, build_report, monitor_records


def prediction(identifier, gold, predicted, **changes):
    row = {"prediction_id": identifier, "episode_id": "e1", "dataset_id": "fixture",
           "split": "test", "evaluation_mode": "B", "arm": "J", "condition": "attack",
           "classification_unit": "action", "target_event": "should_block",
           "gold_label": gold, "predicted_label": predicted,
           "gold_source": "synthetic_test_fixture", "prediction_status": "ok"}
    row.update(changes)
    return row


class ReportTests(unittest.TestCase):
    def test_confusion_counts_exclude_errors_and_do_not_mutate_inputs(self):
        rows = [prediction("1", "unsafe", "unsafe"), prediction("2", "safe", "unsafe"),
                prediction("3", "safe", "safe"), prediction("4", "unsafe", "safe"),
                prediction("5", "unsafe", "unsafe", prediction_status="timeout")]
        original = copy.deepcopy(rows)
        report = binary_metrics(rows, positive="unsafe", negative="safe")
        self.assertEqual([report[k] for k in ("TP", "FP", "TN", "FN")], [1, 1, 1, 1])
        self.assertEqual(report["valid_n"], 4)
        self.assertEqual(report["excluded"], {"timeout": 1})
        self.assertEqual(report["accuracy"], .5)
        self.assertEqual(report["coverage_of_recorded_rows"], .8)
        self.assertEqual(rows, original)

    def test_missing_gold_zero_denominators_and_inconsistent_stored_cells(self):
        report = binary_metrics([prediction("1", None, "safe")], positive="unsafe", negative="safe")
        self.assertEqual(report["valid_n"], 0)
        self.assertIsNone(report["accuracy"])
        self.assertIsNone(report["recall"])
        with self.assertRaisesRegex(ValueError, "confusion_cell"):
            binary_metrics([prediction("1", "unsafe", "safe", confusion_cell="TP")],
                           positive="unsafe", negative="safe")
        with self.assertRaisesRegex(ValueError, "gold_source"):
            binary_metrics([prediction("1", "unsafe", "safe", gold_source=None)],
                           positive="unsafe", negative="safe")

    def test_multiclass_and_invalid_prediction_rejected_in_binary_path(self):
        with self.assertRaisesRegex(ValueError, "Unexpected label"):
            binary_metrics([prediction("1", "hold", "safe")], positive="unsafe", negative="safe")
        with self.assertRaisesRegex(ValueError, "Unexpected label"):
            binary_metrics([prediction("1", "safe", "hold")], positive="unsafe", negative="safe")

    def make_run(self, directory):
        root = Path(directory)
        config = {"protocol_version": "0.4", "analysis": {"classification": {
            "unit": "action", "target_event": "should_block",
            "positive_label": "unsafe", "negative_label": "safe"}}}
        plan = [{"episode_id": name, "task_id": "original-task", "dataset_id": "fixture",
                 "split": "test", "evaluation_mode": "B", "arm": "J", "condition": "attack"} for name in ("e1", "e2")]
        (root / "effective-config.json").write_text(json.dumps(config), encoding="utf-8")
        (root / "plan.jsonl").write_text("\n".join(json.dumps(row) for row in plan), encoding="utf-8")
        episode = {**plan[0], "status": "completed", "grading_status": "valid",
                   "utility_success": True, "attack_success": False}
        (root / "episodes.jsonl").write_text(json.dumps(episode), encoding="utf-8")
        (root / "predictions.jsonl").write_text(json.dumps(prediction("p1", "unsafe", "safe")),
                                              encoding="utf-8")
        return root

    def test_partial_coverage_preserves_unstarted_tasks_and_raw_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            report = build_report(root, [])
            coverage = report["episode_groups"][0]
            self.assertEqual(coverage["planned_episodes"], 2)
            self.assertEqual(coverage["original_tasks"], 1)
            self.assertEqual(coverage["unrecorded_episodes"], 1)
            self.assertEqual(coverage["attack_success"]["unknown_of_planned"], 1)
            self.assertEqual(report["binary_classification"][0]["FN"], 1)
            self.assertTrue(report["issues"])
            self.assertEqual(before, {path.name: path.read_bytes() for path in root.iterdir()})

    def test_cli_generates_new_analysis_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            out = root / "analysis-test"
            command = [sys.executable, str(Path(__file__).with_name("experiment_report.py")),
                       "--run-dir", str(root), "--out-dir", str(out)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = (out / "summary.json").read_bytes()
            self.assertEqual(json.loads(summary)["binary_classification"][0]["FN"], 1)
            self.assertTrue((out / "audit-report.md").is_file())
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((out / "summary.json").read_bytes(), summary)

    def test_modes_are_separate_from_arms_and_not_merged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            plan_path = root / "plan.jsonl"
            plan = [json.loads(line) for line in plan_path.read_text(encoding="utf-8").splitlines()]
            plan[1]["evaluation_mode"] = "C"
            plan_path.write_text("\n".join(json.dumps(row) for row in plan), encoding="utf-8")
            report = build_report(root, [])
            self.assertEqual(len(report["episode_groups"]), 2)
            self.assertEqual({row["evaluation_mode"] for row in report["episode_groups"]}, {"B", "C"})
            self.assertEqual({row["arm"] for row in report["episode_groups"]}, {"J"})
            self.assertEqual(report["binary_classification"][0]["evaluation_mode"], "B")

    def test_mode_mismatch_and_unknown_mode_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            (root / "predictions.jsonl").write_text(json.dumps(
                prediction("p1", "safe", "safe", evaluation_mode="D")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pairing field: evaluation_mode"):
                build_report(root, [])
            (root / "predictions.jsonl").write_text("", encoding="utf-8")
            (root / "episodes.jsonl").write_text("", encoding="utf-8")
            plan_path = root / "plan.jsonl"
            plan = [json.loads(line) for line in plan_path.read_text(encoding="utf-8").splitlines()]
            plan[0]["evaluation_mode"] = "unknown_mode"
            plan_path.write_text("\n".join(json.dumps(row) for row in plan), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown evaluation_mode"):
                build_report(root, [])

    def test_duplicate_predictions_and_unplanned_episodes_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            path = root / "predictions.jsonl"
            line = path.read_text(encoding="utf-8")
            path.write_text(line + "\n" + line, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate prediction_id"):
                build_report(root, [])
            path.write_text(json.dumps(prediction("p1", "safe", "safe", episode_id="e999")),
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unplanned"):
                build_report(root, [])

    def test_wrong_arm_and_changed_target_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_run(directory)
            path = root / "predictions.jsonl"
            path.write_text(json.dumps(prediction("p1", "safe", "safe", arm="L")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pairing field"):
                build_report(root, [])
            path.write_text(json.dumps(prediction("p1", "safe", "safe", target_event="contains_attack")),
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "semantics"):
                build_report(root, [])
            path.write_text("", encoding="utf-8")
            episode_path = root / "episodes.jsonl"
            episode = json.loads(episode_path.read_text(encoding="utf-8"))
            episode["grading_status"] = "unknown"
            episode_path.write_text(json.dumps(episode), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "grading_status"):
                build_report(root, [])

    def test_monitor_unknown_cost_is_preserved_and_resume_not_double_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.run.json"
            source = {"run_id": "monitor-fixture", "wall_seconds": 1.0, "call_seconds": 3.0,
                      "known_estimated_cost_usd": .1, "estimated_cost_usd": None,
                      "unpriced_calls": 1, "status": "completed"}
            path.write_text(json.dumps(source), encoding="utf-8")
            before = path.read_bytes()
            records = monitor_records([path])
            self.assertIsNone(records[0]["estimated_cost_usd"])
            self.assertEqual(records[0]["call_seconds"], 3.0)
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaisesRegex(ValueError, "duplicate monitor"):
                monitor_records([path, path])
            root = self.make_run(directory)
            config_path = root / "effective-config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["measurement"] = {"monitor": {"run_ids": ["wrong-id"]}}
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invocation links"):
                build_report(root, [path])
            source["estimated_cost_usd"] = 0
            path.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unpriced"):
                monitor_records([path])


if __name__ == "__main__":
    unittest.main()
