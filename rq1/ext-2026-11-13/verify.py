
"""Independent verification: recompute counts and MCC for every cell without import from derive.py.

Merge rule (documented): files in cells.json sorted by mtime ascending; an ok row replaces a failed
row; between two ok rows the later file wins. This mirrors the documented rule, not derive.py's code.
"""
import csv, json, os, math, hashlib

ROOT = r"D:\projects\jev_research"
EXT = os.path.join(ROOT, "rq1", "ext-2026-11-13")
DS = {"agentharm": None, "injecagent": None, "tsbench": None, "wildguard_response": "test",
      "stepshield_test": "test", "stepshield_test_holdout": "test_holdout"}

def merged(files, split_filter):
    out = {}
    for rel in sorted(files, key=lambda f: os.path.getmtime(os.path.join(ROOT, f))):
        for line in open(os.path.join(ROOT, rel), encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if split_filter and r.get("split") != split_filter:
                continue
            k = (r.get("split"), r.get("item_id"))
            prev = out.get(k)
            ok_new = r.get("status") == "ok"
            if prev is None or (ok_new and (prev.get("status") != "ok" or True)):
                if prev is None or ok_new:
                    out[k] = r
    return out

def mcc(tp, fp, tn, fn):
    den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    return (tp * tn - fp * fn) / math.sqrt(den) if den else None

cells = json.load(open(os.path.join(EXT, "cells.json"), encoding="utf-8"))
met = list(csv.DictReader(open(os.path.join(EXT, "metrics_ci.csv"), encoding="utf-8")))
full = list(csv.DictReader(open(os.path.join(ROOT, "rq1", "summary", "metrics_full.csv"), encoding="utf-8-sig")))
ok = bad = 0
for c in cells:
    rows = merged(c["files"], DS[c["dataset"]])
    tp = fp = tn = fn = 0
    for r in rows.values():
        if r.get("status") != "ok":
            continue
        g, p = r.get("gold"), r.get("prediction")
        if g not in (0, 1) or p not in (0, 1):
            continue
        if g == 1:
            tp += 1 if p == 1 else 0; fn += 1 if p == 0 else 0
        else:
            fp += 1 if p == 1 else 0; tn += 1 if p == 0 else 0
    ref = next(r for r in met if r["model"] == c["model"] and r["dataset"] == c["dataset"])
    pub = next((r for r in full if r["model"] == c["model"] and r["dataset"] == c["dataset"]), None)
    got = (tp, fp, tn, fn)
    exp = (int(ref["tp"]), int(ref["fp"]), int(ref["tn"]), int(ref["fn"]))
    pubv = (int(pub["tp"]), int(pub["fp"]), int(pub["tn"]), int(pub["fn"])) if pub and pub["scorable"] else None
    if got == exp == pubv:
        ok += 1
    else:
        bad += 1
        print("MISMATCH", c["model"], c["dataset"], got, exp, pubv)
print("cells verified:", ok, "mismatch:", bad)
for m, ds in [("jev-packy-1.14.0", "agentharm"), ("d3mini", "stepshield_test"), ("claudehaiku", "tsbench")]:
    ref = next(r for r in met if r["model"] == m and r["dataset"] == ds)
    tp, fp, tn, fn = int(ref["tp"]), int(ref["fp"]), int(ref["tn"]), int(ref["fn"])
    print("%-22s %-20s n=%d MCC recomputed=%.6f reported=%s" % (m, ds, tp + fp + tn + fn, mcc(tp, fp, tn, fn), ref["mcc"]))
prov = json.load(open(os.path.join(EXT, "provenance.json"), encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
print("metrics_full hash match:", sha(os.path.join(ROOT, "rq1", "summary", "metrics_full.csv")) == prov["inputs"]["metrics_full_sha256"])
print("time_tokens hash match:", sha(os.path.join(ROOT, "rq1", "summary", "time_tokens.csv")) == prov["inputs"]["time_tokens_sha256"])
