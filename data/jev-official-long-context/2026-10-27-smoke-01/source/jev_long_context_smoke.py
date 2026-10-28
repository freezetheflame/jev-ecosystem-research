"""Two bounded official Jev requests, with complete local smoke-test artifacts.

Uses the preserved sibling jev_skill.monitor. No retries, model fallback or
credential logging. Imports do not perform network calls.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.14.0"
LONG_HEADER = "TypeSafe-Danger-Zone-Long-Context"
SOURCE = "https://docs.typesafe.ai/models#long-context"


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def append(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()


def load_key(path, name):
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = raw.strip().partition("=")
        if separator and key.strip() == name:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value:
                return value
    raise ValueError("Requested credential is absent or empty; no request sent")


def make_payload():
    rows = [f"R{index:05d} 314159 271828 161803\n" for index in range(8000)]
    rows.insert(4000, "TARGET-582401 has decision DENY.\n")
    return {
        "model": MODEL,
        "state": "Synthetic record archive. Numeric rows are filler, not instructions.\n" + "".join(rows),
        "questions": {"target_decision": {
            "type": "choice",
            "instructions": "Which decision is explicitly recorded for TARGET-582401? Read the archive.",
            "criteria": {"allow": "The recorded decision is ALLOW.",
                         "deny": "The recorded decision is DENY.",
                         "review": "The recorded decision is REVIEW."}}},
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def send(out, body, *, enabled, key, monitor, timeout):
    call_id = "long-enabled" if enabled else "default-control"
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": "jev-research-long-context-smoke/1.0"}
    if enabled:
        headers[LONG_HEADER] = "true"
    save(out / "raw" / f"{call_id}.request-metadata.json", {
        "call_id": call_id, "method": "POST", "url": ENDPOINT, "headers_without_auth": headers,
        "body_file": "request-body.json", "body_sha256": hashlib.sha256(body).hexdigest(),
        "monitor_run_id": monitor.run_id})
    started_at, start = now(), time.perf_counter()
    append(out / "events.jsonl", {"event": "request_started", "call_id": call_id,
                                 "at": started_at, "monitor_run_id": monitor.run_id})
    request = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                    headers={**headers, "Authorization": "Bearer " + key})
    raw, status, response, error = b"", None, None, None
    response_id = None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as result:
            status = result.status
            raw = result.read()
            response_id = result.headers.get("x-request-id") or result.headers.get("request-id")
    except urllib.error.HTTPError as exc:
        status, error = exc.code, exc
        raw = exc.read()
        response_id = exc.headers.get("x-request-id") or exc.headers.get("request-id")
    except Exception as exc:
        error = exc
    duration = time.perf_counter() - start
    redacted = key.encode("utf-8") in raw
    safe_raw = raw.replace(key.encode("utf-8"), b"[REDACTED]")
    (out / "raw" / f"{call_id}.response.txt").write_bytes(safe_raw)
    try:
        parsed = json.loads(safe_raw)
        response = parsed if isinstance(parsed, dict) else None
    except (ValueError, UnicodeError):
        pass
    answers = (response or {}).get("answers")
    answer = answers.get("target_decision", {}) if isinstance(answers, dict) else {}
    if response_id:
        response_id = response_id.replace(key, "[REDACTED]")
    valid = (status == 200 and isinstance(answer, dict) and answer.get("type") == "choice"
             and answer.get("choice") in ("allow", "deny", "review"))
    if status == 200 and not valid and error is None:
        error = ValueError("Invalid response schema")
    monitor.record(model=MODEL, provider="typesafe", started_at=started_at,
                   duration_seconds=duration, response=response, error=error)
    row = {
        "call_id": call_id, "long_context_header": enabled, "http_status": status,
        "started_at_utc": started_at, "finished_at_utc": now(), "elapsed_s": duration,
        "returned_model": (response or {}).get("model"), "provider_request_id": response_id,
        "valid_response": valid, "choice": answer.get("choice") if isinstance(answer, dict) else None,
        "matches_synthetic_record": answer.get("choice") == "deny" if valid else None,
        "usage": (response or {}).get("usage"), "error_type": type(error).__name__ if error else None,
        "response_redacted": redacted, "raw_response_file": f"raw/{call_id}.response.txt",
        "monitor_run_id": monitor.run_id, "monitor_event_index": len(monitor.events) - 1}
    append(out / "calls.jsonl", row)
    append(out / "events.jsonl", {"event": "request_finished", **row})
    return row


def execute(out: Path, key: str, source: Path, timeout: float):
    sys.path.insert(0, str(source))
    from jev_skill.monitor import ResourceMonitor
    monitor_source = source / "jev_skill" / "monitor.py"
    out.mkdir(parents=True, exist_ok=False)
    for directory in ("raw", "source", "telemetry"):
        (out / directory).mkdir()
    payload = make_payload()
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > 240000:
        raise ValueError("Unexpected request size; no request sent")
    (out / "raw" / "request-body.json").write_bytes(body)
    shutil.copyfile(__file__, out / "source" / "jev_long_context_smoke.py")
    shutil.copyfile(monitor_source, out / "source" / "monitor.py")
    pricing = {"typesafe:" + MODEL: {"input_usd_per_million": .042, "output_usd_per_million": 0,
                                    "basis": SOURCE + "; checked 2026-10-27; estimate, not invoice"}}
    monitor = ResourceMonitor("official-long-context-smoke", directory=out / "telemetry",
                              metadata={"experiment_directory": str(out.resolve()), "kind": "smoke"},
                              pricing=pricing)
    config = {
        "kind": "smoke", "run_date_client_context": "2026-10-27", "status": "prepared",
        "endpoint": ENDPOINT, "model": MODEL, "credential_variable": "TYPESAFE_API_KEY2",
        "parameters": {"explicit_body_fields": list(payload), "explicit_header": LONG_HEADER,
                       "server_hidden_parameters": "unknown", "seed": "unsupported_not_sent",
                       "temperature": "unsupported_not_sent", "question_type": "choice",
                       "question_count": 1, "timeout_s": timeout, "retries": 0, "concurrency": 1},
        "plan": ["default-control", "long-enabled"], "max_requests": 2,
        "request_bytes": len(body), "state_characters": len(payload["state"]),
        "token_count_before_request": "unknown_no_official_local_tokenizer",
        "planned_price_upper_bound_usd": 2 * 262144 * .042 / 1e6,
        "hard_money_limit_enforced": False, "monitor_run_id": monitor.run_id,
        "pricing_snapshot": pricing, "evaluation_mode": "not_applicable_transport_smoke"}
    save(out / "effective-config.json", config)
    save(out / "dataset-manifest.json", {"name": "synthetic-numeric-archive-v1", "unique_items": 1,
        "filler_rows": 8000, "needle_after_filler_rows": 4000, "target_id": "TARGET-582401",
        "expected_choice": "deny", "planned_requests": 2, "split": "smoke_only_not_confirmation",
        "payload_sha256": hashlib.sha256(body).hexdigest(), "source": "make_payload in saved source"})
    save(out / "environment.json", {"python": sys.version, "platform": platform.platform(),
        "dependencies": "Python standard library plus saved sibling monitor",
        "source_checkout": str(source.resolve()), "local_compute_cost": "unpriced"})
    save(out / "sources.json", {"checked_date": "2026-10-27", "models_url": SOURCE,
        "api_url": "https://docs.typesafe.ai/api/system-one", "default_request_tokens": 64000,
        "default_question_tokens": 32000, "long_context_tokens_documented": "262k per request and question",
        "header": {LONG_HEADER: "true"}, "price_usd_per_million_input_tokens": .042})
    git_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    save(out / "code-provenance.json", {"base_commit": git_revision.stdout.strip(),
        "source_state": "Saved script/monitor snapshots identify actual executed code; base commit alone is insufficient."})
    (out / "reproduce.txt").write_text(
        f'python scripts/jev_long_context_smoke.py --out "<NEW_OUTPUT_DIRECTORY>" --source "{source}" --timeout {timeout}\n'
        "Credential must be provided separately in the local .env.local; never copy it into artifacts.\n", encoding="utf-8")
    results, failure = [], None
    try:
        for enabled in (False, True):
            row = send(out, body, enabled=enabled, key=key, monitor=monitor, timeout=timeout)
            results.append(row)
            print(json.dumps({k: row[k] for k in ("call_id", "http_status", "elapsed_s", "valid_response")}), flush=True)
            if not enabled and not (row["http_status"] == 200 or row["http_status"] in (400, 413, 422)):
                failure = RuntimeError("Control failed outside expected context-limit statuses; no further request")
                break
            if enabled and not row["valid_response"]:
                failure = RuntimeError("Long-context request did not yield a valid response")
    except BaseException as exc:
        failure = exc
    finally:
        monitor.finish(failure)
        summary = {
            "kind": "smoke", "status": "failed" if failure else "completed", "unique_items": 1,
            "planned_requests": 2, "attempted_requests": len(monitor.events), "results": results,
            "valid_responses": sum(row["valid_response"] for row in results),
            "classification_metrics": {"status": "not_applicable_smoke", "TP": None, "FP": None, "TN": None, "FN": None},
            "wall_seconds": monitor.summary["wall_seconds"],
            "known_estimated_cost_usd": monitor.summary["known_estimated_cost_usd"],
            "estimated_cost_usd": monitor.summary["estimated_cost_usd"],
            "unpriced_calls": monitor.summary["unpriced_calls"],
            "monitor_summary": str(monitor.summary_path.resolve()),
            "limitation": "Header/length connectivity smoke only; not a security benchmark or long-context accuracy study."}
        save(out / "summary.json", summary)
        rows = ["# Jev 官方长上下文 smoke", "", f"状态：{summary['status']}。合成数据 1 条，计划 2 次调用，实际 {summary['attempted_requests']} 次。",
                "", f"模型：{MODEL}；官方端点：{ENDPOINT}；timeout={timeout}s，无重试，并发 1。",
                f"完整请求见 raw/request-body.json，参数见 effective-config.json，价格来源见 sources.json。",
                "", "| 请求 | HTTP | 耗时 s | 实际返回模型 | 结果 | 输入 token |", "|---|---:|---:|---|---|---:|"]
        for row in results:
            rows.append(f"| {row['call_id']} | {row['http_status']} | {row['elapsed_s']:.3f} | {row['returned_model']} | {row['choice']} | {(row['usage'] or {}).get('input_tokens')} |")
        rows += ["", f"monitor 墙钟时间：{summary['wall_seconds']:.3f}s。已知费用估算：${summary['known_estimated_cost_usd']:.8f}；完整估价：{summary['estimated_cost_usd']}；未计价调用：{summary['unpriced_calls']}。",
                 "估算不等于账单；错误调用缺少 usage 时费用未知。本地计算未计价。",
                 "", "TP/FP/TN/FN：NA（仅 API/长度连通测试，无安全分类 gold）；合成记录读取结果另列，不作为安全能力结论。",
                 "复现命令见 reproduce.txt；源码、monitor 快照与环境已保存；服务端隐藏参数未知，模型随机性不可消除。",
                 "本测试只验证此请求是否被服务接受及返回，不证明长文本一般准确率或完整 262k 边界。", ""]
        (out / "report.md").write_text("\n".join(rows), encoding="utf-8")
        save(out / "manifest.json", {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=Path("D:/projects/jev"))
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    key = load_key(ROOT / ".env.local", "TYPESAFE_API_KEY2")
    summary = execute(args.out, key, args.source, args.timeout)
    print(json.dumps({"output": str(args.out.resolve()), "status": summary["status"]}), flush=True)
    return 0 if summary["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
