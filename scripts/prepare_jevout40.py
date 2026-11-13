"""Freeze 40 public MMLU-Pro questions before evaluating any model outputs."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import httpx
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "jevout-40"
SEED = 20260921
URL = "https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/resolve/refs%2Fconvert%2Fparquet/default/test/0000.parquet"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = OUT / "frozen40-raw.json"
    if snapshot.exists():
        raise SystemExit("Snapshot already frozen; do not resample after seeing results")
    parquet = OUT / "mmlu-pro-test.parquet"
    if not parquet.exists():
        response = httpx.get(URL, follow_redirects=True, timeout=90)
        response.raise_for_status()
        parquet.write_bytes(response.content)
    rows = pq.read_table(parquet).to_pylist()
    try:
        old = [json.loads(line) for line in (ROOT / "data" / "jevout-pilot" / "subset.jsonl").read_text(encoding="utf-8").splitlines()]
    except (OSError, ValueError) as error:
        raise SystemExit(f"Cannot read frozen pilot questions: {error}") from error
    by_id = {f"mmlu-pro-test-{row['question_id']}": row for row in rows}
    selected = [by_id[item["item_id"]] for item in old]
    for item, row in zip(old, selected, strict=True):
        assert row["question"] == item["question"]
        assert row["answer"] == item["gold_keys"][0]
        assert row["options"] == [choice["text"] for choice in item["choices"]]
    # Preserve the 8 pilot questions. Add 32 from other native categories, not
    # chosen by outputs. Round-robin gives each of the other 13 categories 2–3.
    categories = sorted({row["category"] for row in rows} - {row["category"] for row in selected})
    categories.sort(key=lambda category: hashlib.sha256(f"{SEED}:category:{category}".encode()).hexdigest())
    pools = {category: sorted([row for row in rows if row["category"] == category],
                             key=lambda row: hashlib.sha256(f"{SEED}:{row['question_id']}".encode()).hexdigest()) for category in categories}
    index = 0
    while len(selected) < 40:
        for category in categories:
            if len(selected) == 40:
                break
            selected.append(pools[category][index])
        index += 1
    assert len({row["question_id"] for row in selected}) == 40
    frozen = {"dataset_url": URL, "parquet_sha256": hashlib.sha256(parquet.read_bytes()).hexdigest(),
              "source_rows": len(rows), "seed": SEED,
              "selection": "Retain 8 pilot questions; add 32 via seeded category-round-robin and SHA256(seed:question_id) ranks in the other 13 categories; frozen before outcomes",
              "category_counts": dict(Counter(row["category"] for row in selected)),
              "rows": [{"row": row} for row in selected]}
    snapshot.write_text(json.dumps(frozen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in frozen.items() if key != "rows"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
