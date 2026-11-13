
"""RQ1 external re-analysis, stage 1: cell map, cluster bootstrap CIs, rank stability,
paired McNemar, split shift, and cost normalization.

Read-only over runs/ and rq1/ (never writes there). Generated outputs go to this directory.
No model calls. Stdlib only. Seed fixed so results are reproducible.
"""
import csv, json, os, math, random, hashlib, time
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "agent-security-study", "runs")
RQ1 = os.path.join(ROOT, "rq1")
REPS = 1000
SEED = 20261113

MODEL_DIR = {"jev-packy-1.14.0": "jev"}
DS_DIR = {
    "agentharm": ("agentharm", None),
    "injecagent": ("injecagent", None),
    "tsbench": ("tsbench", None),
    "wildguard_response": ("wildguardtest-response", "test"),
    "stepshield_test": ("stepshield", "test"),
    "stepshield_test_holdout": ("stepshield", "test_holdout"),
}
DS_ORDER = ["agentharm", "injecagent", "tsbench", "wildguard_response",
            "stepshield_test", "stepshield_test_holdout"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def find_episode_files():
    found = []
    for base in (DATA, RQ1):
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in
                           ("raw", "telemetry", "source", ".git", "_ingest", "__pycache__")]
            if "episodes.jsonl" in filenames:
                found.append(os.path.join(dirpath, "episodes.jsonl"))
    return sorted(found)

def read_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows

def counts(rows, split_filter=None):
    c = dict(n=0, tp=0, fp=0, tn=0, fn=0, P=0, N=0, ok=0, fail=0)
    for r in rows:
        if split_filter and r.get("split") != split_filter:
            continue
        c["n"] += 1
        if r.get("status") == "ok":
            c["ok"] += 1
        else:
            c["fail"] += 1
        g, p = r.get("gold"), r.get("prediction")
        if g in (0, 1) and p in (0, 1) and r.get("status") == "ok":
            if g == 1:
                c["P"] += 1
                c["tp" if p == 1 else "fn"] += 1
            else:
                c["N"] += 1
                c["fp" if p == 1 else "tn"] += 1
    c["scorable"] = c["tp"] + c["fp"] + c["tn"] + c["fn"]
    return c

def merge_rows(run_files, split_filter=None):
    """Merge rows keyed by (split,item_id); an ok row replaces a failed one; later file wins."""
    merged = {}
    files = sorted(run_files, key=lambda f: os.path.getmtime(f))
    for f in files:
        for r in read_rows(f):
            if split_filter and r.get("split") != split_filter:
                continue
            key = (r.get("split"), r.get("item_id"))
            prev = merged.get(key)
            if prev is None or (prev.get("status") != "ok" and r.get("status") == "ok") or \
               (prev.get("status") == "ok" and r.get("status") == "ok"):
                merged[key] = r
    return list(merged.values())

def mets(tp, fp, tn, fn):
    d = dict(tp=tp, fp=fp, tn=tn, fn=fn)
    d["tpr"] = tp / (tp + fn) if (tp + fn) else None
    d["tnr"] = tn / (tn + fp) if (tn + fp) else None
    d["fpr"] = fp / (fp + tn) if (fp + tn) else None
    d["fnr"] = fn / (fn + tp) if (fn + tp) else None
    d["prec"] = tp / (tp + fp) if (tp + fp) else None
    d["npv"] = tn / (tn + fn) if (tn + fn) else None
    n = tp + fp + tn + fn
    d["acc"] = (tp + tn) / n if n else None
    d["bacc"] = ((d["tpr"] + d["tnr"]) / 2) if (d["tpr"] is not None and d["tnr"] is not None) else None
    d["f1"] = (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else None
    den = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    d["mcc"] = (tp * tn - fp * fn) / math.sqrt(den) if den else None
    d["prev"] = (tp + fn) / n if n else None
    return d

def resolve_cells():
    rows = list(csv.DictReader(open(os.path.join(RQ1, "summary", "metrics_full.csv"), encoding="utf-8-sig")))
    files = find_episode_files()
    cand = defaultdict(list)
    for f in files:
        parts = f.split(os.sep)
        cand[(parts[-3], parts[-2])].append((parts[-4], f))
    cells, unmatched = [], []
    for r in rows:
        model, ds = r["model"], r["dataset"]
        if model.startswith("always-") or ds not in DS_DIR or not r.get("scorable"):
            continue
        ddir, sf = DS_DIR[ds]
        target = tuple(int(r[k]) for k in ("scorable", "P", "N", "tp", "fp", "tn", "fn"))
        cs = cand.get((MODEL_DIR.get(model, model), ddir), [])
        if cs:
            best = {}
            for camp, f in cs:
                if camp not in best or os.path.getmtime(f) > os.path.getmtime(best[camp]):
                    best[camp] = f
            cs = sorted(best.items())
        chosen_files, chosen_counts, how = None, None, None
        for camp, f in sorted(cs):
            c = counts(read_rows(f), sf)
            if (c["scorable"], c["P"], c["N"], c["tp"], c["fp"], c["tn"], c["fn"]) == target:
                chosen_files, chosen_counts, how = [f], c, "single:" + camp
                break
        if chosen_files is None and cs:
            mrows = merge_rows([f for _, f in cs], sf)
            c = counts(mrows, None)
            if (c["scorable"], c["P"], c["N"], c["tp"], c["fp"], c["tn"], c["fn"]) == target:
                chosen_files, chosen_counts, how = [f for _, f in cs], c, "merged:" + ",".join(sorted({x[0] for x in cs}))
        if chosen_files is None:
            unmatched.append((model, ds, target, [(camp, counts(read_rows(f), sf)) for camp, f in sorted(cs)]))
            continue
        cells.append(dict(model=model, dataset=ds, how=how,
                          files=[os.path.relpath(f, ROOT) for f in chosen_files],
                          counts=chosen_counts))
    return cells, unmatched

def cell_rows(cell):
    ddir, sf = DS_DIR[cell["dataset"]]
    rows = merge_rows([os.path.join(ROOT, f) for f in cell["files"]], sf)
    return [r for r in rows if r.get("gold") in (0, 1) and r.get("prediction") in (0, 1)
            and r.get("status") == "ok"]

def bootstrap_cell(rows, reps=REPS, seed=SEED):
    fam = defaultdict(lambda: [0, 0, 0, 0])
    for r in rows:
        g, p = r["gold"], r["prediction"]
        k = r.get("family_id") or r.get("item_id")
        v = fam[k]
        if g == 1:
            if p == 1: v[0] += 1
            else: v[3] += 1
        else:
            if p == 1: v[1] += 1
            else: v[2] += 1
    keys = list(fam)
    F = len(keys)
    if F == 0:
        return None
    arr = [fam[k] for k in keys]
    rng = random.Random(seed)
    mccs, tprs, tnrs = [], [], []
    for _ in range(reps):
        tp = fp = tn = fn = 0
        for _ in range(F):
            a, b, c, d = arr[rng.randrange(F)]
            tp += a; fp += b; tn += c; fn += d
        m = mets(tp, fp, tn, fn)
        mccs.append(m["mcc"])
        tprs.append(m["tpr"])
        tnrs.append(m["tnr"])
    def ci(xs):
        xs = [x for x in xs if x is not None]
        if not xs: return (None, None)
        xs.sort()
        lo = xs[int(0.025 * (len(xs) - 1))]
        hi = xs[int(0.975 * (len(xs) - 1))]
        return (lo, hi)
    base = mets(*[sum(v[i] for v in arr) for i in range(4)])
    return base, {k: ci(v) for k, v in (("mcc", mccs), ("tpr", tprs), ("tnr", tnrs))}, F

def fmt(x, nd=3):
    return "—" if x is None else (f"{x:.{nd}f}")

def main():
    t0 = time.time()
    cells, unmatched = resolve_cells()
    print(f"resolved cells: {len(cells)}  unmatched: {len(unmatched)}")
    for u in unmatched:
        print("  UNMATCHED", u[0], u[1], u[2])
    # cache rows
    rows_by = {}
    for c in cells:
        rows_by[(c["model"], c["dataset"])] = cell_rows(c)
    # ---- metrics + CI
    out_rows = []
    for c in cells:
        rows = rows_by[(c["model"], c["dataset"])]
        res = bootstrap_cell(rows)
        if not res: continue
        base, ci, F = res
        out_rows.append(dict(model=c["model"], dataset=c["dataset"], n=base["tp"]+base["fp"]+base["tn"]+base["fn"],
                             families=F, prev=base["prev"], tp=base["tp"], fp=base["fp"], tn=base["tn"], fn=base["fn"],
                             tpr=base["tpr"], tnr=base["tnr"], mcc=base["mcc"], acc=base["acc"],
                             tpr_lo=ci["tpr"][0], tpr_hi=ci["tpr"][1],
                             tnr_lo=ci["tnr"][0], tnr_hi=ci["tnr"][1],
                             mcc_lo=ci["mcc"][0], mcc_hi=ci["mcc"][1], how=c["how"]))
    with open(os.path.join(OUT, "metrics_ci.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    # ---- rank stability (common items per dataset)
    rank_rows, top1_rows = [], []
    for ds in DS_ORDER:
        models = [c["model"] for c in cells if c["dataset"] == ds]
        if len(models) < 3: continue
        item_sets = []
        for m in models:
            item_sets.append({(r.get("split"), r.get("item_id")) for r in rows_by[(m, ds)]})
        common = set.intersection(*item_sets)
        if len(common) < 50: continue
        fam_of = {}
        for r in rows_by[(models[0], ds)]:
            k = (r.get("split"), r.get("item_id"))
            if k in common:
                fam_of[k] = r.get("family_id") or r.get("item_id")
        fams = sorted(set(fam_of.values()))
        fam_index = {f: i for i, f in enumerate(fams)}
        F = len(fams)
        per_model = []
        for m in models:
            arr = [[0, 0, 0, 0] for _ in range(F)]
            for r in rows_by[(m, ds)]:
                k = (r.get("split"), r.get("item_id"))
                if k not in common: continue
                i = fam_index[fam_of[k]]
                g, p = r["gold"], r["prediction"]
                if g == 1:
                    arr[i][0 if p == 1 else 3] += 1
                else:
                    arr[i][1 if p == 1 else 2] += 1
            per_model.append(arr)
        points = [mets(*[sum(v[i] for v in per_model[mi]) for i in range(4)]) for mi in range(len(models))]
        if all(p["mcc"] is not None for p in points):
            rank_key = "mcc"
        elif all(p["bacc"] is not None for p in points):
            rank_key = "bacc"
        else:
            rank_key = "tpr"
        rng = random.Random(SEED + len(ds))
        draws = [[] for _ in models]
        for _ in range(REPS):
            idx = [rng.randrange(F) for _ in range(F)]
            for mi, arr in enumerate(per_model):
                tp = fp = tn = fn = 0
                for j in idx:
                    a, b, c, d = arr[j]
                    tp += a; fp += b; tn += c; fn += d
                draws[mi].append(mets(tp, fp, tn, fn)[rank_key])
        for mi in range(len(models)):
            tops = sum(1 for rep in range(REPS)
                       if draws[mi][rep] is not None and
                       all(draws[mi][rep] >= (draws[mj][rep] if draws[mj][rep] is not None else -9)
                           for mj in range(len(models)) if mj != mi))
            top1_rows.append(dict(dataset=ds, model=models[mi], metric=rank_key, p_top1=tops / REPS,
                                  point=points[mi][rank_key]))
            for mj in range(mi + 1, len(models)):
                wins = 0; n = 0
                for rep in range(REPS):
                    a, b = draws[mi][rep], draws[mj][rep]
                    if a is None or b is None: continue
                    n += 1
                    wins += 1 if a > b else (0.5 if a == b else 0)
                if n:
                    rank_rows.append(dict(dataset=ds, metric=rank_key, model_a=models[mi], model_b=models[mj],
                                          p_a_better=wins / n, n_reps=n))
        print(f"rank stability {ds}: models={len(models)} common_items={len(common)} families={F}")
    with open(os.path.join(OUT, "rank_stability.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "metric", "model_a", "model_b", "p_a_better", "n_reps"])
        w.writeheader(); w.writerows(rank_rows)
    with open(os.path.join(OUT, "rank_top1.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "model", "metric", "p_top1", "point"])
        w.writeheader(); w.writerows(top1_rows)
    # ---- metric sensitivity: rank under MCC / balanced acc / TPR per dataset
    sens_rows = []
    for ds in DS_ORDER:
        models = [c["model"] for c in cells if c["dataset"] == ds]
        pts = []
        for m in models:
            rs2 = rows_by[(m, ds)]
            cc = counts(rs2, None)
            m0 = mets(cc["tp"], cc["fp"], cc["tn"], cc["fn"])
            pts.append((m, m0))
        def ranks(values):
            order = sorted(range(len(values)), key=lambda i: (values[i] is None, -(values[i] or 0)))
            r = [None] * len(values)
            for pos, i in enumerate(order):
                r[i] = pos + 1
            return r
        rm = ranks([p[1]["mcc"] for p in pts])
        rb = ranks([p[1]["bacc"] for p in pts])
        rt = ranks([p[1]["tpr"] for p in pts])
        for i, (m, mm) in enumerate(pts):
            sens_rows.append(dict(dataset=ds, model=m, value_mcc=mm["mcc"], value_bacc=mm["bacc"],
                                  value_tpr=mm["tpr"], rank_mcc=rm[i], rank_bacc=rb[i], rank_tpr=rt[i]))
    with open(os.path.join(OUT, "rank_by_metric.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sens_rows[0].keys()))
        w.writeheader(); w.writerows(sens_rows)
    # ---- McNemar
    def binom_two_sided(b, c):
        n = b + c
        if n == 0: return 1.0
        k = min(b, c)
        # log-space exact two-sided p = 2 * sum_{i<=k} C(n,i) / 2^n
        terms = []
        for i in range(0, k + 1):
            logc = math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            terms.append(logc - n * math.log(2))
        m = max(terms)
        s = math.exp(m) * sum(math.exp(t - m) for t in terms)
        return min(1.0, 2 * s)
    pair_rows = []
    for ds in DS_ORDER:
        models = [c["model"] for c in cells if c["dataset"] == ds]
        preds = {}
        for m in models:
            preds[m] = {(r.get("split"), r.get("item_id")): r["prediction"] for r in rows_by[(m, ds)]}
        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                a, b = models[i], models[j]
                common = set(preds[a]) & set(preds[b])
                if len(common) < 30: continue
                gold = {(r.get("split"), r.get("item_id")): r["gold"] for r in rows_by[(a, ds)]}
                bb = cc = 0
                for k in common:
                    if k not in gold: continue
                    ca = preds[a][k] == gold[k]; cb = preds[b][k] == gold[k]
                    if ca and not cb: bb += 1
                    elif cb and not ca: cc += 1
                if bb + cc == 0: continue
                pair_rows.append(dict(dataset=ds, model_a=a, model_b=b, n_common=len(common),
                                      a_right_b_wrong=bb, b_right_a_wrong=cc,
                                      delta_acc=(bb - cc) / len(common), p_exact=binom_two_sided(bb, cc)))
    with open(os.path.join(OUT, "paired_mcnemar.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(pair_rows[0].keys()))
        w.writeheader(); w.writerows(pair_rows)
    # ---- split shift
    shift_rows = []
    for c in cells:
        ddir, _ = DS_DIR[c["dataset"]]
        rows_all = merge_rows([os.path.join(ROOT, f) for f in c["files"]], None)
        allowed = None
        if c["dataset"] == "stepshield_test":
            allowed = {"test"}
        elif c["dataset"] == "stepshield_test_holdout":
            allowed = {"test_holdout"}
        for split in sorted({r.get("split") for r in rows_all}):
            if allowed is not None and split not in allowed:
                continue
            cc = counts(rows_all, split)
            if cc["scorable"] == 0: continue
            m = mets(cc["tp"], cc["fp"], cc["tn"], cc["fn"])
            shift_rows.append(dict(model=c["model"], dataset=c["dataset"], split=split,
                                   n=cc["scorable"], prev=m["prev"], tpr=m["tpr"], tnr=m["tnr"], mcc=m["mcc"]))
    with open(os.path.join(OUT, "shift.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "dataset", "split", "n", "prev", "tpr", "tnr", "mcc"])
        w.writeheader(); w.writerows(shift_rows)
    # ---- cost normalization
    cost_rows = []
    tt = list(csv.DictReader(open(os.path.join(RQ1, "summary", "time_tokens.csv"), encoding="utf-8-sig")))
    for r in tt:
        try:
            n_ok = int(r["n_ok"] or 0); calls = int(r["call_n"] or 0)
        except ValueError:
            continue
        if not n_ok: continue
        cost_rows.append(dict(model=r["model"], dataset=r["dataset"], n_ok=n_ok, calls=calls,
                              calls_per_item=calls / n_ok,
                              call_mean_s=float(r["call_mean_seconds"] or 0),
                              episode_mean_s=float(r["episode_mean_seconds"] or 0),
                              in_tokens=int(r["input_tokens_known"] or 0),
                              in_tokens_per_item=(int(r["input_tokens_known"] or 0) / n_ok),
                              missing_usage_calls=int(r["missing_usage_calls"] or 0),
                              tokens_source=r["tokens_source"]))
    with open(os.path.join(OUT, "cost.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cost_rows[0].keys()))
        w.writeheader(); w.writerows(cost_rows)
    # ---- provenance + handoff
    meta = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                script="rq1/ext-2026-11-13/derive.py", script_sha256=sha256(os.path.abspath(__file__)),
                seed=SEED, reps=REPS, cells=len(cells), unmatched=[u[:2] for u in unmatched],
                inputs=dict(metrics_full_sha256=sha256(os.path.join(RQ1, "summary", "metrics_full.csv")),
                            time_tokens_sha256=sha256(os.path.join(RQ1, "summary", "time_tokens.csv"))))
    json.dump(meta, open(os.path.join(OUT, "provenance.json"), "w", encoding="utf-8"), indent=1)
    json.dump(cells, open(os.path.join(OUT, "cells.json"), "w", encoding="utf-8"), indent=1)
    print("done in %.1fs" % (time.time() - t0))

if __name__ == "__main__":
    main()