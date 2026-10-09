#!/usr/bin/env python3
"""Fetch JevBench result JSON and render the full leaderboard as Markdown.

JevBench (github.com/fstandhartinger/jevbench) is the only independent
benchmark that pulls open-weight decision models into a network-isolated
container and re-runs them on the evaluator's own hardware. All rankings in
this repo are derived from its raw result JSON, never from secondary articles.

Usage:
    python scripts/fetch_jevbench.py                 # default v1.4.2.2
    python scripts/fetch_jevbench.py --version v1.4.2.1

Known pitfall: a single curl/python download is frequently truncated by the
proxy (observed: 80 KB instead of 622 KB), which silently breaks json.load.
This script retries until the payload parses and reports the byte count.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request

RAW_BASE = (
    "https://raw.githubusercontent.com/fstandhartinger/jevbench/main"
    "/results/{v}/jevbench-{v}-results.json"
)
# gh api is the most reliable transport: raw.githubusercontent.com is frequently
# blocked by proxies, and the contents endpoint is authenticated + untruncated.
GH_CONTENTS = "repos/fstandhartinger/jevbench/contents/results/{v}/jevbench-{v}-results.json"

OPEN_MARK = {"yes": "yes", "true": "yes", "weights": "weights", "no": "no", "false": "no"}


def _via_gh(version: str) -> bytes:
    """Primary transport: `gh api` contents endpoint (base64 payload)."""
    import base64
    import subprocess

    path = GH_CONTENTS.format(v=version)
    proc = subprocess.run(
        ["gh", "api", path, "--jq", ".content"],
        capture_output=True, check=True, text=True,
    )
    return base64.b64decode(proc.stdout.strip())


def _via_urllib(version: str) -> bytes:
    with urllib.request.urlopen(RAW_BASE.format(v=version), timeout=120) as resp:
        return resp.read()


def _via_curl(version: str) -> bytes:
    """Last resort. urllib raises SSL: UNEXPECTED_EOF behind some HTTP proxies."""
    import subprocess

    proc = subprocess.run(
        ["curl", "-sL", "--max-time", "180", RAW_BASE.format(v=version)],
        capture_output=True, check=True,
    )
    return proc.stdout


TRANSPORTS = (_via_gh, _via_urllib, _via_curl)


def fetch(version: str, tries: int = 6) -> dict:
    last: Exception | None = None
    for attempt in range(1, tries + 1):
        transport = TRANSPORTS[(attempt - 1) % len(TRANSPORTS)]
        try:
            raw = transport(version)
            data = json.loads(raw.decode("utf-8"))
            if "systems" not in data:
                raise ValueError("payload parsed but has no 'systems' key")
            print(f"[ok] {version}: {len(raw)} bytes, {len(data['systems'])} systems "
                  f"via {transport.__name__}", file=sys.stderr)
            return data
        except Exception as exc:  # truncated payload / proxy hiccup
            last = exc
            print(f"[retry {attempt}/{tries}] {transport.__name__}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            time.sleep(2 * attempt)
    raise RuntimeError(f"failed to fetch JevBench {version}: {last}")


def to_board(data: dict) -> str:
    rows = []
    for s in data["systems"]:
        ax = s.get("axes") or {}
        cost = s.get("cost") or {}
        sp = s.get("speed") or {}
        rows.append({
            "rank": s.get("rank"),
            "name": s.get("display"),
            "author": s.get("author"),
            "cls": s.get("class"),
            "open": OPEN_MARK.get(str(s.get("open")).lower(), str(s.get("open"))),
            "score": round(s.get("jevbench_score") or 0, 2),
            "I": round(ax.get("intelligence") or 0, 1),
            "C": round(ax.get("calibration") or 0, 1),
            "S": round(ax.get("speed") or 0, 1),
            "K": round(ax.get("cost") or 0, 1),
            "pub": round((s.get("public_accuracy") or 0) * 100, 1),
            "seal": round((s.get("sealed_accuracy") or 0) * 100, 1),
            "p50": round(sp.get("p50_s_adjusted") or sp.get("p50_s_raw") or 0, 3),
            "usd": round(cost.get("usd_per_1000") or 0, 4),
            "repo": s.get("repo") or "",
            "licence": (s.get("licence") or "").replace("|", "/"),
            "link": f"[repo]({s['repo']})" if s.get("repo") else "",
        })
    rows.sort(key=lambda r: (r["rank"] is None, r["rank"] or 999))

    out = [
        "| # | 系统 | 作者 | 类别 | 开源 | 总分 | I | C | S | K | 公开% | 密封% | p50(s) | $/千次 | 许可证 | 链接 |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        r = dict(r)
        rank = r.pop("rank") or "—"
        out.append(
            "| {rank} | {name} | {author} | {cls} | {open} | {score} | {I} | {C} | {S} | {K} "
            "| {pub} | {seal} | {p50} | {usd} | {licence} | {link} |".format(rank=rank, **r)
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v1.4.2.2")
    ap.add_argument("--out-json", default="data/jevbench-{v}-results.json")
    ap.add_argument("--out-md", default="data/jevbench-{v}-leaderboard.md")
    args = ap.parse_args()

    data = fetch(args.version)
    json_path = args.out_json.format(v=args.version)
    md_path = args.out_md.format(v=args.version)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(
            f"# JevBench {args.version} 全量榜单\n\n"
            f"自动生成，请勿手工编辑。数据源：JevBench 原始结果 JSON。\n\n"
            f"随机基线（密封集）= {data.get('sealed_chance')}；"
            f"已排名系统 = {sum(1 for s in data['systems'] if s.get('rank'))} / "
            f"{len(data['systems'])}\n\n"
        )
        f.write(to_board(data))
        f.write("\n")
    print(f"wrote {json_path} and {md_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
