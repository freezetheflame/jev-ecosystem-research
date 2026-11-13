"""Bounded MMLU-Pro pilot using unmodified JevOut evaluation/optimization code.

Run baseline first. Optimization additionally needs an OpenAI-compatible proposer.
Never substitutes hand-authored attacks or synthetic target probabilities.
"""

import argparse
import hashlib
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from jev_api import load_config

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "data" / "JevOut"
OUTPUT = ROOT / "data" / "jevout-pilot"
SEED = 20260921
sys.path.insert(0, str(ROOT))

from data.JevOut.context_optimization.clients import OpenAICompatibleClient  # noqa: E402 - local vendor path is set above.


class NonThinkingClient(OpenAICompatibleClient):
    log_lock = threading.Lock()
    """Disable hidden reasoning and mirror schema for this DeepSeek endpoint.

    Original task prompts, sampling and token budgets are retained. Required
    checker fields are never filled in by guessing semantic acceptance.
    """

    def __init__(self, base_url: str, *, api_key: str, log_path: Path, item_id: str | None = None) -> None:
        super().__init__(base_url, api_key=api_key, timeout=90)
        self.log_path = log_path
        self.item_id = item_id

    def structured_chat(
        self,
        *,
        model: str,
        system: str,
        user: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        temperature: float,
        top_p: float,
        max_tokens: int,
        seed: int | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        contract = "\n\nOutput contract: Return only one JSON object matching the following schema. Include ALL required properties using exactly these property names. Do not rename, omit or add properties.\n"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system + contract + json.dumps(schema)},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            "temperature": temperature,
            "top_p": top_p,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "schema": schema}},
        }
        for attempt, budget in enumerate((max_tokens, max_tokens * 2)):
            payload["max_tokens"] = budget
            if seed is not None:
                payload["seed"] = seed + attempt
            response = self.client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
            with self.log_lock, self.log_path.open("a", encoding="utf-8") as log:
                log.write(json.dumps({"item_id": self.item_id, "schema": schema_name, "attempt": attempt, "budget": budget,
                                      "seed": payload.get("seed"), "thinking": "disabled", "schema_mirrored_in_prompt": True, "response": body}, ensure_ascii=False) + "\n")
            content = body["choices"][0]["message"].get("content") or ""
            try:
                return json.loads(content), body.get("usage", {})
            except json.JSONDecodeError:
                continue
        raise ValueError("structured response was invalid after retry; see response log")


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    global OUTPUT
    # Explicit local credentials file only; do not load the vendor's .env.
    load_dotenv(ROOT / ".env.local", override=False, encoding="utf-8-sig")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["baseline", "optimize", "retest"])
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--snapshot", type=Path, default=None)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--resume", action="store_true", help="Reuse completed item records only; rerun unfinished items")
    parser.add_argument("--allow-provider-switch", action="store_true", help="Exploratory resume assuming the two Jev providers equivalent; retain old records")
    parser.add_argument("--target-url", default=None, help="Explicit target endpoint; shared plugin config stays unchanged")
    parser.add_argument("--target-model", default=None)
    parser.add_argument("--target-key-env", default=None, help="Environment variable name, never a literal key")
    parser.add_argument("--proposer-url", default=os.getenv("DEEPSEEK_BASE_URL") or None)
    parser.add_argument("--proposer-model", default=os.getenv("DEEPSEEK_MODEL") or None)
    parser.add_argument("--proposer-key-env", default="DEEPSEEK_API_KEY" if os.getenv("DEEPSEEK_API_KEY") else None,
                        help="Name of an environment variable, not the key")
    parser.add_argument("--disable-thinking", action="store_true", help="DeepSeek compatibility: reserve output budget for JSON, not hidden reasoning")
    parser.add_argument("--strategy", choices=["adaptive", "targeted_one_shot", "neutral_one_shot"], default="adaptive")
    args = parser.parse_args()
    OUTPUT = args.output_dir.resolve()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.count < 1 or not 1 <= args.workers <= 4:
        parser.error("count must be positive and workers must be in [1, 4]")
    if args.mode == "optimize" and not (args.proposer_url and args.proposer_model):
        parser.error("optimize requires --proposer-url and --proposer-model")
    if args.mode == "optimize" and args.proposer_key_env and not os.getenv(args.proposer_key_env):
        parser.error("The named proposer key environment variable is empty or missing")
    if args.mode == "optimize" and args.proposer_url and args.proposer_url.startswith("https://") and not args.proposer_key_env:
        parser.error("Hosted proposer needs credentials: fill DEEPSEEK_API_KEY locally or use --proposer-key-env")
    if args.mode == "optimize" and not args.resume and (OUTPUT / f"{args.strategy}.jsonl").exists():
        parser.error("Existing experiment output: archive it before starting a new run; refusing to overwrite")

    from data.JevOut.context_optimization.evaluate import evaluate
    from data.JevOut.context_optimization.io import write_jsonl
    from data.JevOut.context_optimization.metrics import select_target_option
    from data.JevOut.context_optimization.render import prepare_item
    from data.JevOut.context_optimization.schema import ChoiceOption, DecisionItem
    from data.JevOut.context_optimization.targets import CachedTarget, JevTarget

    raw_path = args.snapshot or OUTPUT / "mmlu-pro-first30-raw.json"
    try:
        raw_bytes = raw_path.read_bytes()
        raw = json.loads(raw_bytes)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot load public dataset snapshot: {error}\n")
    rows = [entry["row"] for entry in raw["rows"]]
    rows.sort(key=lambda row: hashlib.sha256(f"{SEED}:{row['question_id']}".encode()).hexdigest())
    if args.count > len(rows):
        parser.error("Requested count exceeds frozen snapshot; do not silently shrink sample")
    items = []
    for row in rows[:args.count]:
        keys = [chr(65 + index) for index in range(len(row["options"]))]
        assert keys[row["answer_index"]] == row["answer"]
        items.append(prepare_item(DecisionItem(
            item_id=f"mmlu-pro-test-{row['question_id']}", context_kind="question_only",
            source=row["question"], question=row["question"],
            choices=[ChoiceOption(key=key, text=text) for key, text in zip(keys, row["options"], strict=True)],
            gold_keys=[row["answer"]],
            metadata={"dataset": "TIGER-Lab/MMLU-Pro", "split": "test", "category": row["category"], "src": row["src"]},
        )))
    write_jsonl(OUTPUT / "subset.jsonl", items)
    if args.target_url or args.target_model or args.target_key_env:
        if not (args.target_url and args.target_model and args.target_key_env):
            parser.error("Explicit target requires URL, model and key environment variable name")
        if not args.target_url.startswith("https://") or not os.getenv(args.target_key_env):
            parser.error("Explicit target requires HTTPS and a nonempty local key variable")
        config = {"endpoint": args.target_url, "model": args.target_model, "apiKey": os.environ[args.target_key_env]}
    else:
        config = load_config()
    # Separate env name: never silently inherit a different private key.
    os.environ["JEVOUT_PILOT_KEY"] = config["apiKey"]
    target = JevTarget(base_url=config["endpoint"], model=config["model"], api_key_env="JEVOUT_PILOT_KEY", timeout=30)
    target.client.headers["User-Agent"] = "jev-research/1.0"
    cache_key = hashlib.sha256(f"{config['endpoint']}:{config['model']}".encode()).hexdigest()[:16]
    cached = CachedTarget(target, OUTPUT / ".cache" / cache_key)
    code_files = sorted((VENDOR / "context_optimization").rglob("*.py")) + sorted((VENDOR / "context_optimization" / "prompts").glob("*.txt"))
    manifest = {
        "dataset_url": raw.get("dataset_url", "https://datasets-server.huggingface.co/rows?dataset=TIGER-Lab%2FMMLU-Pro&config=default&split=test&offset=0&length=30"),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(), "seed": SEED,
        "selection": raw.get("selection", "lowest SHA256(seed:question_id) ranks from the first 30 test rows; no outcome selection"),
        "items": [item.item_id for item in items], "category_counts": raw.get("category_counts", {"business": len(items)}),
        "population": "Frozen MMLU-Pro subset; NOT representative of the paper's seven datasets",
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "target_endpoint": config["endpoint"], "requested_model": config["model"],
        "vendor_sha256": {str(path.relative_to(VENDOR)): hashlib.sha256(path.read_bytes()).hexdigest() for path in code_files},
        "deviations": [f"{len(items)} MMLU-Pro questions, not the paper's 7 datasets / 700 held-out sources", f"target provider/model: {config['endpoint']} / {config['model']} (see observed revision)", "optimization: 4 particles x 2 rounds, not 16 x 4; proposer/checker specified by caller, not frozen Gemma4-12B"],
    }
    if args.resume:
        try:
            recorded = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            parser.exit(1, f"Cannot verify resume manifest: {error}\n")
        for field in ("raw_sha256", "items", "target_endpoint", "requested_model", "vendor_sha256"):
            if args.allow_provider_switch and field in ("target_endpoint", "requested_model"):
                continue
            if recorded[field] != manifest[field]:
                parser.error(f"Resume manifest mismatch: {field}")
        if args.allow_provider_switch:
            manifest["exploratory_provider_switch"] = {"previous_endpoint": recorded["target_endpoint"],
                                                       "previous_model": recorded["requested_model"],
                                                       "assumption": "user accepts providers as equivalent; not verified"}
    save(OUTPUT / "manifest.json", manifest)
    if args.mode == "baseline":
        records = []
        for item in items:
            record = evaluate([item], cached)[0]
            records.append(record)
            write_jsonl(OUTPUT / "clean.jsonl", records)
            print(f"{item.item_id}: gold={record.unit.gold_branch} selected={record.result.selected} correct={record.initially_correct}", flush=True)
        eligible = [{"item_id": r.item_id, "gold": r.unit.gold_branch, "fixed_wrong_target": select_target_option(r.unit, r.result)} for r in records if r.initially_correct]
        summary = {"items": len(items), "initially_correct": len(eligible), "accuracy": len(eligible) / len(items), "eligible": eligible,
                   "response_models": sorted({r.result.model_revision for r in records}), "cache": str(OUTPUT / ".cache" / cache_key),
                   "note": "clean eligibility only; no attack TFR measured; reruns may reuse cached responses"}
        save(OUTPUT / "baseline-summary.json", summary)
    elif args.mode == "retest":
        from data.JevOut.context_optimization.repeatability import retest_context
        from data.JevOut.context_optimization.schema import OptimizationResult

        if (OUTPUT / "repeatability.jsonl").exists():
            parser.error("Archive existing repeatability results before starting new fresh calls")
        try:
            saved = [OptimizationResult.model_validate_json(line) for line in (OUTPUT / "adaptive.jsonl").read_text(encoding="utf-8").splitlines()]
        except (OSError, ValueError) as error:
            parser.exit(1, f"Cannot load completed adaptive results: {error}\n")
        by_item = {item.item_id: item for item in items}
        repeated = []
        for discovery in saved:
            if not discovery.targeted_flip:
                continue
            # Upstream picks the highest-probability successful context before fresh calls.
            result = retest_context(discovery, by_item[discovery.item_id], target, repetitions=10, minimum_hits=8)
            repeated.append(result)
            write_jsonl(OUTPUT / "repeatability.jsonl", repeated)
        summary = {"cases": len(repeated), "repetitions": 10, "minimum_hits": 8,
                   "clean_gold_hits": {r.item_id: r.clean_gold_hits for r in repeated},
                   "target_hits": {r.item_id: r.target_hits for r in repeated},
                   "target_calls": 20 * len(repeated), "local_cache_bypassed": True,
                   "note": "repeatability is not proof of gold-answer preservation"}
        save(OUTPUT / "repeatability-summary.json", summary)
    else:
        from data.JevOut.context_optimization.checker import OpenAIContextChecker
        from data.JevOut.context_optimization.io import content_hash
        from data.JevOut.context_optimization.optimize import (
            IneligibleDecisionError,
            optimize_context,
        )
        from data.JevOut.context_optimization.proposer import OpenAIContextProposer
        from data.JevOut.context_optimization.schema import (
            OptimizationConfig,
            OptimizationResult,
        )

        key = os.environ[args.proposer_key_env] if args.proposer_key_env else "local"
        policy = OptimizationConfig(strategy=args.strategy, particles=4, rounds=2, proposal_retries=0 if args.strategy != "adaptive" else 1, seed=SEED)
        result_path = OUTPUT / f"{args.strategy}.jsonl"
        try:
            baseline = json.loads((OUTPUT / "baseline-summary.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            parser.exit(1, f"Run and freeze baseline first: {error}\n")
        eligible_ids = {entry["item_id"] for entry in baseline["eligible"]}
        completed, skipped = [], [item.item_id for item in items if item.item_id not in eligible_ids]
        if args.resume and result_path.exists():
            try:
                completed = [OptimizationResult.model_validate_json(line) for line in result_path.read_text(encoding="utf-8").splitlines()]
            except (OSError, ValueError) as error:
                parser.exit(1, f"Cannot resume recorded items: {error}\n")
            expected = {item.item_id: content_hash(item) for item in items}
            if any(r.item_id not in expected or r.config != policy or
                   (r.metadata.get("input_hash") is not None and r.metadata["input_hash"] != expected[r.item_id]) for r in completed):
                parser.error("Resume input or policy mismatch")
            # Legacy records have no input_hash: verify every stored rendered context.
            from data.JevOut.context_optimization.render import render_additions

            by_item = {item.item_id: item for item in items}
            if any(a.source_hash is not None and a.source_hash != content_hash(render_additions(by_item[r.item_id], a.additions))
                   for r in completed for a in r.attempts):
                parser.error("Resume recorded context hash mismatch")
        outside_cohort = [r for r in completed if r.item_id not in eligible_ids]
        if outside_cohort:
            write_jsonl(OUTPUT / f"{args.strategy}-outside-frozen-cohort.jsonl", outside_cohort)
            completed = [r for r in completed if r.item_id in eligible_ids]
            write_jsonl(result_path, completed)
        done = {r.item_id for r in completed}
        order = {item.item_id: index for index, item in enumerate(items)}

        def run_item(item):
            if args.disable_thinking:
                client = NonThinkingClient(args.proposer_url, api_key=key, log_path=OUTPUT / f"{args.strategy}-chat-calls.jsonl", item_id=item.item_id)
            else:
                client = OpenAICompatibleClient(args.proposer_url, api_key=key, timeout=90)
            try:
                result = optimize_context(item, cached, OpenAIContextProposer(client, args.proposer_model),
                                          OpenAIContextChecker(client, args.proposer_model), config=policy)
                result.metadata.update({"input_hash": content_hash(item), "proposer_model": args.proposer_model,
                                        "proposer_url": args.proposer_url, "thinking_disabled": args.disable_thinking,
                                        "schema_mirrored_in_prompt": args.disable_thinking})
                return result
            finally:
                client.client.close()

        errors = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(run_item, item): item.item_id for item in items if item.item_id in eligible_ids and item.item_id not in done}
            for future in as_completed(futures):
                item_id = futures[future]
                try:
                    result = future.result()
                except IneligibleDecisionError:
                    errors.append({"item_id": item_id, "error_type": "FrozenEligibilityChanged"})
                    save(OUTPUT / f"{args.strategy}-errors.json", errors)
                    continue
                except Exception as error:
                    # Do not convert request errors to negative attack outcomes.
                    errors.append({"item_id": item_id, "error_type": type(error).__name__,
                                   "http_status": getattr(getattr(error, "response", None), "status_code", None),
                                   "request_host": getattr(getattr(getattr(error, "request", None), "url", None), "host", None)})
                    save(OUTPUT / f"{args.strategy}-errors.json", errors)
                    continue
                completed.append(result)
                completed.sort(key=lambda r: order[r.item_id])
                write_jsonl(result_path, completed)
                print(f"{item_id}: flip={result.targeted_flip} accepted_calls={result.target_calls} completed={len(completed)}", flush=True)
        if errors:
            parser.exit(1, "Incomplete experiment: recorded errors; resume unfinished items before reporting rates\n")
        eligible_count = len(completed)
        summary = {"strategy": args.strategy, "eligible": eligible_count, "skipped": skipped,
                   "flips": sum(r.targeted_flip for r in completed),
                   "tfr": sum(r.targeted_flip for r in completed) / eligible_count if eligible_count else None,
                   "proposal_attempts": sum(r.proposal_calls for r in completed), "accepted_target_calls": sum(r.target_calls for r in completed),
                   "target_endpoint": config["endpoint"], "requested_target_model": config["model"],
                   "proposer_url": args.proposer_url, "proposer_model": args.proposer_model, "checker_model": args.proposer_model, "thinking_disabled": args.disable_thinking, "schema_mirrored_in_prompt": args.disable_thinking,
                   "provider_equivalence_assumed": args.allow_provider_switch,
                   "workers": args.workers, "policy": policy.model_dump(), "response_models": sorted({r.clean_result.model_revision for r in completed}),
                   "note": "rejected proposals remain in eligible denominator; API exceptions abort; same clean cache fixes units and targets"}
        save(OUTPUT / f"{args.strategy}-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
