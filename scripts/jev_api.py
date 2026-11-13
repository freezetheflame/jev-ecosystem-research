"""Run explicit Jev test requests using the project's Pi Jev configuration.

No network calls on import; no retry or paid fallback. Run without a request
file for a synthetic smoke test. Supplied payload models are replaced with the
configured model so archived examples can be tested without editing them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".pi" / "pi-jev.json"


def load_config(path: Path = DEFAULT_CONFIG) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"Cannot load Jev configuration: {path}") from error
    if not isinstance(config, dict):
        raise ValueError("Jev configuration must be a JSON object")
    for field in ("endpoint", "model", "apiKey"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f"Missing configuration field: {field}")
    if not config["endpoint"].startswith("https://"):
        raise ValueError("The test endpoint must use HTTPS")
    if config.get("timeoutMs", 10000) <= 0:
        raise ValueError("timeoutMs must be positive")
    # Deliberately do not inherit TYPESAFE_API_KEY: it may be a private key
    # for a different service. This runner has its own explicit override.
    config["apiKey"] = os.environ.get("JEV_TEST_API_KEY") or config["apiKey"]
    return config


def prepare_request(payload: dict, config: dict) -> dict:
    if not isinstance(payload, dict) or "state" not in payload:
        raise ValueError("A request must contain state")
    questions = payload.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise ValueError("A request must contain a nonempty questions object")
    for question in questions.values():
        if not isinstance(question, dict) or question.get("type") not in ("choice", "noul", "score"):
            raise ValueError("Unknown question type")
    return {**payload, "model": config["model"]}


def validate_response(response: dict, payload: dict) -> None:
    if not isinstance(response, dict) or not isinstance(response.get("answers"), dict):
        raise ValueError("Response is missing the answers object")
    for key, question in payload["questions"].items():
        answer = response["answers"].get(key)
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise ValueError(f"Missing or mismatched answer: {key}")


def evaluate(payload: dict, config: dict) -> dict:
    # HTTPS-only even for callers supplying config directly; no file:// input.
    if not config["endpoint"].startswith("https://"):
        raise ValueError("The test endpoint must use HTTPS")
    request = prepare_request(payload, config)
    body = json.dumps(request, ensure_ascii=False).encode("utf-8")
    wire = urllib.request.Request(  # nosec B310: endpoint is explicitly restricted to HTTPS above.
        config["endpoint"], data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {config['apiKey']}",
                 "User-Agent": "jev-research/1.0", "Accept": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(wire, timeout=config.get("timeoutMs", 10000) / 1000) as result:  # nosec B310: HTTPS-only request.

            response = json.loads(result.read().decode("utf-8"))
            status = result.status
    except urllib.error.HTTPError as error:
        # Avoid logging a server body which might echo sensitive input.
        raise RuntimeError(f"Jev endpoint returned HTTP {error.code}; no fallback attempted") from None
    validate_response(response, request)
    return {
        "endpoint": config["endpoint"],
        "requested_model": config["model"],
        "source_model": payload.get("model"),
        "request_sha256": hashlib.sha256(body).hexdigest(),
        "http_status": status,
        "elapsed_s": round(time.perf_counter() - started, 4),
        "response": response,
    }


def smoke_request() -> dict:
    return {
        "state": "A customer was charged twice and requests a refund.",
        "questions": {
            "department": {
                "type": "choice", "instructions": "Which department should handle this?",
                "criteria": {"billing": "Payments and refunds", "technical": "Software issues", "sales": "New purchases"},
            },
            "refund": {"type": "noul", "instructions": "Does the customer request a refund?"},
            "severity": {
                "type": "score", "instructions": "How severe is the issue?",
                "criteria": ["No issue", "One customer's payment issue", "A service-wide outage"],
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", nargs="?", type=Path, help="JSON payload; omit for a synthetic smoke test")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out", type=Path, help="Save response and provenance (never the API key)")
    args = parser.parse_args()
    try:
        payload = json.loads(args.request.read_text(encoding="utf-8")) if args.request else smoke_request()
        report = evaluate(payload, load_config(args.config))
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Jev test failed: {error}\n")
    print(text)


if __name__ == "__main__":
    main()
