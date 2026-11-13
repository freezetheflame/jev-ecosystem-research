"""Campaign-local launcher for full-api-jev-packy-v1.

Wires the existing security_bench Jev choice adapter to Packy
(https://slb-v1.api.fan/v1/systemone, PACKY_AI_KEY) without rewriting
the shared OpenLux defaults in configs/full-suite-models.v1.json.
Clears HTTP(S) proxies for this process only.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import sys
import traceback
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from security_bench.common import read, write, file_hash, now, rows, digest, sources
from security_bench.config import inspect
from security_bench.runner import execute, data_hashes, verify_inputs
from security_bench.full_suite import configuration, inventory, KNOWN_DATASETS
from scripts.machine_benchmark import load_key
from security_bench import models as models_mod
from security_bench.models import NoRedirect

BASE = ROOT / "data/agent-security-study"
MODELS_OVERLAY = ROOT / "configs/full-suite-models.packy-v1.json"
PRICING_OVERLAY = ROOT / "configs/full-suite-pricing.packy-v1.json"
ENV_FILE = ROOT / ".env.local"
KEY_NAME = "PACKY_AI_KEY"
CAMPAIGN = "full-api-jev-packy-v1"
SMOKE_CAMPAIGN = "smoke-api-jev-packy-v1"
MODELS = ["jev"]
DATASETS = [
    "agentharm",
    "injecagent",
    "tsbench",
    "stepshield",
    "wildguardtest-response",
]
DEFAULT_MAX_API_USD = 250.0
DEFAULT_MAX_HOURS = 72.0


def clear_proxy() -> None:
    for key in list(os.environ):
        if "PROXY" in key.upper():
            os.environ.pop(key, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    urllib.request.getproxies = lambda: {}
    urllib.request.getproxies_environment = lambda: {}
    if hasattr(urllib.request, "getproxies_registry"):
        urllib.request.getproxies_registry = lambda: {}

    original_init = models_mod.Transport.__init__

    def _init(self, config, run_dir, monitor, opener=None):
        if opener is None:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
        original_init(self, config, run_dir, monitor, opener=opener)

    models_mod.Transport.__init__ = _init


def apply_packy(config: dict) -> dict:
    overlay = copy.deepcopy(read(MODELS_OVERLAY)["models"]["jev"])
    current = config["models"]["jev"]
    overlay["input_field"] = current.get("input_field")
    config["models"]["jev"] = overlay
    try:
        pricing_rel = str(PRICING_OVERLAY.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        pricing_rel = str(PRICING_OVERLAY)
    config["pricing_file"] = pricing_rel
    return config


def proxy_env_names() -> list[str]:
    return sorted(k for k in os.environ if "PROXY" in k.upper())


def ensure_key() -> None:
    if os.environ.get(KEY_NAME):
        return
    if not ENV_FILE.is_file():
        raise ValueError(f"{KEY_NAME} missing and {ENV_FILE} not found; value never logged")
    load_key(str(ENV_FILE), KEY_NAME)
    if not os.environ.get(KEY_NAME):
        raise ValueError(f"{KEY_NAME} is missing from environment/key file; value never logged")


def build_cell(model: str, dataset: str, repeats: int, max_api_usd: float, max_hours: float, cached_cases=None):
    config, cases = configuration(model, dataset, repeats, max_api_usd, max_hours, cached_cases=cached_cases)
    apply_packy(config)
    return config, cases


def preflight_or_cells(action: str, campaign: str, datasets: list[str], repeats: int,
                       max_api_usd: float, max_hours: float, resume: bool, smoke_one: bool = False):
    if set(datasets) - set(KNOWN_DATASETS):
        raise ValueError("Unknown dataset in campaign selection")
    remote = list(MODELS)
    per_api = max_api_usd / (len(remote) * len(datasets) or 1)
    cells = []
    fingerprints = {}
    for dataset in datasets:
        stats = None
        native_cases = None
        for model in MODELS:
            config, cases = build_cell(model, dataset, repeats, per_api, max_hours, cached_cases=native_cases)
            native_cases = cases
            if smoke_one:
                cases = cases[:1]
                config["datasets"][dataset]["item_ids"] = [case["item_id"] for case in cases]
                config.update(record_kind="full_suite_integration_smoke", repeats=1)
                config["budget"]["max_calls"] = sum(case.get("native_steps", 1) for case in cases) * config.get("retry_policy", {}).get("max_attempts", 1)
            checked = inspect(config, check_keys=(action == "run"))
            if checked["issues"]:
                raise ValueError("; ".join(checked["issues"]))
            if dataset not in fingerprints:
                fingerprints[dataset] = data_hashes(config)
            if stats is None:
                stats = inventory(cases)
            cells.append((model, dataset, config))
        print(json.dumps({"dataset": dataset, **stats, "models": len(MODELS), "repeats": repeats,
                          "mode": cells[-1][2]["datasets"][dataset]["mode_code"],
                          "contract": cells[-1][2]["datasets"][dataset]["contract"],
                          "endpoint": cells[-1][2]["models"]["jev"]["endpoint"],
                          "api_key_env": cells[-1][2]["models"]["jev"]["api_key_env"]},
                         ensure_ascii=False), flush=True)
    if action == "preflight":
        print("PACKY PREFLIGHT PASSED; 0 model/API calls.", flush=True)
        return cells, {}
    prep = BASE / "preparations" / campaign
    signature = {
        "models": MODELS,
        "datasets": datasets,
        "repeats": repeats,
        "smoke": bool(smoke_one),
        "api_ceiling_usd": max_api_usd,
        "hours_per_cell": max_hours,
        "configs": {f"{model}/{dataset}": digest(config) for model, dataset, config in cells},
        "launcher_sha256": file_hash(Path(__file__)),
        "models_overlay_sha256": file_hash(MODELS_OVERLAY),
        "pricing_overlay_sha256": file_hash(PRICING_OVERLAY),
        "source_hashes": sources(),
        "data_hashes": fingerprints,
        "route": {
            "provider": "packy",
            "endpoint": "https://slb-v1.api.fan/v1/systemone",
            "model_id": "jev-1.14.0",
            "api_key_env": KEY_NAME,
            "env_file": str(ENV_FILE),
            "no_proxy": True,
            "shared_default_untouched": "configs/full-suite-models.v1.json",
        },
        "server_hashes": {},
    }
    if (prep / "campaign.json").exists():
        if not resume or read(prep / "campaign.json") != signature:
            raise ValueError("Campaign already exists or frozen inputs changed; use exact --resume or a new campaign ID")
    else:
        if resume:
            raise ValueError("Cannot resume a nonexistent campaign")
        write(prep / "campaign.json", signature)
        for path in [
            Path(__file__),
            MODELS_OVERLAY,
            PRICING_OVERLAY,
            ROOT / "scripts/full_benchmark.py",
            ROOT / "scripts/machine_benchmark.py",
            ROOT / "security_bench/config.py",
            ROOT / "security_bench/full_suite.py",
            ROOT / "security_bench/adapters.py",
            ROOT / "configs/full-suite-models.v1.json",
            ROOT / "configs/full-suite-pricing.v1.json",
        ]:
            target = prep / "source" / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    return cells, signature


def run_cells(campaign: str, cells, resume: bool) -> None:
    prep = BASE / "preparations" / campaign
    runroot = BASE / "runs" / campaign
    for model, dataset, config in cells:
        directory = runroot / model / dataset
        if directory.exists():
            verify_inputs(config, directory)
            if len(rows(directory / "episodes.jsonl")) == len(rows(directory / "plan.jsonl")):
                print(model, dataset, "already complete; not rerun", flush=True)
                continue
        write(
            prep / "deployments" / f"{model}-{dataset}-{now().replace(':', '-')}.json",
            {"time": now(), "health": None, "route": config["models"][model]["endpoint"],
             "api_key_env": config["models"][model]["api_key_env"], "provider": config["models"][model]["provider"],
             "no_proxy": True},
        )
        result = execute(config, directory, resume=resume)
        print(model, dataset, result, flush=True)
        if result["status"] != "finished":
            raise RuntimeError("Partial cell retained; inspect report before resume. Campaign stopped.")


def status(campaign: str, datasets: list[str]) -> None:
    runroot = BASE / "runs" / campaign
    print(json.dumps([
        {
            "model": model,
            "dataset": dataset,
            "planned": (runroot / model / dataset / "manifest.json").exists(),
            "completed_episodes": len(rows(runroot / model / dataset / "episodes.jsonl")),
            "assigned_episodes": len(rows(runroot / model / dataset / "plan.jsonl")),
        }
        for model in MODELS for dataset in datasets
    ], indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preflight", "run", "status", "smoke-one"])
    parser.add_argument("--campaign", default=CAMPAIGN)
    parser.add_argument("--datasets", default=",".join(DATASETS))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--max-api-usd", type=float, default=DEFAULT_MAX_API_USD)
    parser.add_argument("--max-hours-per-cell", type=float, default=DEFAULT_MAX_HOURS)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.action == "smoke-one":
        if args.campaign == CAMPAIGN:
            args.campaign = SMOKE_CAMPAIGN
        if args.campaign == CAMPAIGN:
            raise SystemExit("Refusing to write smoke results into the full campaign directory")
    datasets = args.datasets.split(",") if args.action != "smoke-one" else ["agentharm"]
    clear_proxy()
    print(json.dumps({
        "event": "launcher_start",
        "action": args.action,
        "campaign": args.campaign,
        "datasets": datasets,
        "models": MODELS,
        "endpoint": "https://slb-v1.api.fan/v1/systemone",
        "model_id": "jev-1.14.0",
        "api_key_env": KEY_NAME,
        "env_file": str(ENV_FILE),
        "proxy_env": proxy_env_names(),
        "no_proxy": os.environ.get("NO_PROXY"),
        "time": now(),
    }, ensure_ascii=False), flush=True)
    if args.action == "status":
        status(args.campaign, datasets)
        return
    if args.action in ("run", "smoke-one"):
        ensure_key()
        print(json.dumps({"event": "key_loaded", "name": KEY_NAME, "length": len(os.environ[KEY_NAME])},
                         ensure_ascii=False), flush=True)
    if args.action == "run" and (args.max_api_usd is None or args.max_api_usd <= 0):
        raise SystemExit("API execution requires explicit --max-api-usd total ceiling")
    if args.repeats < 1 or args.max_hours_per_cell <= 0:
        raise SystemExit("repeats/hours must be positive")
    try:
        cells, _signature = preflight_or_cells(
            action="run" if args.action in ("run", "smoke-one") else "preflight",
            campaign=args.campaign,
            datasets=datasets,
            repeats=args.repeats,
            max_api_usd=(1.0 if args.action == "smoke-one" else args.max_api_usd),
            max_hours=(1.0 if args.action == "smoke-one" else args.max_hours_per_cell),
            resume=args.resume,
            smoke_one=(args.action == "smoke-one"),
        )
        if args.action in ("run", "smoke-one"):
            run_cells(args.campaign, cells, resume=args.resume)
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
