#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild RQ1 summary tables with MCC + TPR/TNR as the main comparison metrics.

Source of truth: existing live metrics_full.csv confusion-matrix counts
(TP, FP, TN, FN). StepShield EIR / signed intervention gap / premature
alerts are copied from that same CSV (already published); they are not
re-derived here. This script does not read raw/, does not rerun
experiments, and does not write into analysis folders.

Usage:
  python rebuild_mcc_summary.py --input-dir /path/to/rq1/summary --out-dir /path/to/out
  python rebuild_mcc_summary.py --input-dir D:\\projects\\jev_research\\rq1\\summary --in-place
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo


def now_shanghai() -> str:
    try:
        tz = ZoneInfo("Asia/Shanghai")
    except Exception:
        # Windows venv may lack the tzdata package; UTC+8 is Asia/Shanghai (no DST).
        tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S Asia/Shanghai")


GENERATED_AT = now_shanghai()
SERVER_CHECKED_AT = "2026-11-13 12:55:45 Asia/Shanghai"

MODEL_ORDER = [
    ("claudehaiku", "claudehaiku"),
    ("d3mini", "d3mini"),
    ("gliguard", "gliguard"),
    ("gpt6luna", "gpt6luna"),
    ("jev-packy-1.14.0", "Jev (Packy 1.14.0)"),
    ("jevguard", "jevguard"),
    ("kev", "kev"),
    ("laya", "laya"),
    ("qwen35", "qwen35"),
    ("qwen3guard", "qwen3guard"),
    ("secjev", "secjev"),
    ("shieldstral", "shieldstral"),
]

DATASETS = [
    "tsbench",
    "agentharm",
    "injecagent",
    "wildguard_response",
    "stepshield_test",
    "stepshield_test_holdout",
]

MAIN_DATASETS = [
    "agentharm",
    "tsbench",
    "wildguard_response",
    "stepshield_test",
    "stepshield_test_holdout",
]

DATASET_LABEL = {
    "tsbench": "TS-Bench",
    "agentharm": "AgentHarm",
    "injecagent": "InjecAgent",
    "wildguard_response": "WildGuard response (Mode E)",
    "stepshield_test": "StepShield test",
    "stepshield_test_holdout": "StepShield test_holdout",
}

# Default scorable sets (failures may change a model's own denominator).
DEFAULTS = {
    "tsbench": dict(n_total=7182, scorable=5401, P=1631, N=3770),
    "agentharm": dict(n_total=416, scorable=416, P=208, N=208),
    "injecagent": dict(n_total=2108, scorable=2108, P=2108, N=0),
    "wildguard_response": dict(n_total=1725, scorable=1709, P=284, N=1425),
    "stepshield_test": dict(n_total=7935, scorable=7935, P=639, N=7296),
    "stepshield_test_holdout": dict(n_total=216, scorable=216, P=108, N=108),
}


def dec_round(value: float, places: int) -> Decimal:
    q = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)


def fmt_pct(value, places=1):
    if value is None:
        return "—"
    return f"{dec_round(value * 100, places)}%"


def fmt_mcc(value):
    if value is None:
        return "—"
    return f"{dec_round(value, 3)}"


def fmt_gap(value):
    if value is None:
        return "—"
    return f"{dec_round(value, 2)}"


def fmt_int(value):
    if value is None:
        return ""
    return str(int(value))


def as_int(value):
    if value is None or value == "":
        return None
    return int(float(value))


def as_float(value):
    if value is None or value == "":
        return None
    return float(value)


def compute_metrics(tp, fp, tn, fn):
    """Derive classification metrics from a confusion matrix.

    MCC is undefined (None) if any factor of the denominator is 0.
    Ratios with a 0 denominator are None. F1 is None when precision is
    undefined (TP+FP=0); if precision is defined and TP=0, F1 is 0.
    """
    out = dict(
        tp=tp, fp=fp, tn=tn, fn=fn,
        n=tp + fp + tn + fn,
        P=tp + fn,
        N=tn + fp,
        tpr=None, tnr=None, fpr=None, fnr=None,
        precision=None, npv=None, accuracy=None, balanced_acc=None,
        f1=None, mcc=None,
    )
    if tp is None:
        return out
    p = tp + fn
    n = tn + fp
    if p + n:
        out["accuracy"] = (tp + tn) / (p + n)
    if p:
        out["tpr"] = tp / p
        out["fnr"] = fn / p
    if n:
        out["tnr"] = tn / n
        out["fpr"] = fp / n
    if out["tpr"] is not None and out["tnr"] is not None:
        out["balanced_acc"] = (out["tpr"] + out["tnr"]) / 2
    if tp + fp:
        out["precision"] = tp / (tp + fp)
    if tn + fn:
        out["npv"] = tn / (tn + fn)
    if out["precision"] is not None and out["tpr"] is not None:
        if out["precision"] + out["tpr"] == 0:
            out["f1"] = 0.0
        else:
            out["f1"] = 2 * out["precision"] * out["tpr"] / (out["precision"] + out["tpr"])
    a, b, c, d = tp + fp, tp + fn, tn + fp, tn + fn
    if min(a, b, c, d) > 0:
        out["mcc"] = (tp * tn - fp * fn) / math.sqrt(a * b * c * d)
    return out


def baseline(kind, P, N):
    if kind == "always-safe":
        return compute_metrics(0, 0, N, P)
    if kind == "always-unsafe":
        return compute_metrics(P, N, 0, 0)
    raise ValueError(kind)


def load_full_csv(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    by_key = {}
    for row in rows:
        by_key[(row["model"], row["dataset"])] = row
    return rows, by_key


def ranks(values):
    """Average ranks, 1 = highest value."""
    indexed = sorted(enumerate(values), key=lambda x: -x[1])
    out = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg = (i + 1 + j + 1) / 2
        for k in range(i, j + 1):
            out[indexed[k][0]] = avg
        i = j + 1
    return out


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def spearman_defined(metrics_map, ds_a, ds_b):
    names, xa, yb = [], [], []
    for mid, label in MODEL_ORDER:
        a = metrics_map.get((mid, ds_a))
        b = metrics_map.get((mid, ds_b))
        if not a or not b:
            continue
        if a["mcc"] is None or b["mcc"] is None:
            continue
        names.append(label)
        xa.append(a["mcc"])
        yb.append(b["mcc"])
    rho = pearson(ranks(xa), ranks(yb)) if names else None
    return rho, names


def cell_mcc_tpr_tnr(m):
    if m is None:
        return ""
    return f"{fmt_mcc(m['mcc'])} ({fmt_pct(m['tpr'])}/{fmt_pct(m['tnr'])})"


def md_table(headers, rows, aligns=None):
    if aligns is None:
        aligns = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(aligns) + " |",
    ]
    for row in rows:
        cells = ["" if c is None else str(c) for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def prevalence(P, n):
    if not n:
        return None
    return P / n


def build_all(input_dir: Path):
    src_csv = input_dir / "metrics_full.csv"
    src_full_md = input_dir / "metrics_full.md"
    if not src_csv.is_file():
        raise FileNotFoundError(src_csv)
    raw_rows, by_key = load_full_csv(src_csv)

    metrics = {}
    meta = {}
    discrepancies = []

    for mid, label in MODEL_ORDER:
        for ds in DATASETS:
            raw = by_key.get((mid, ds))
            if raw is None:
                continue
            meta[(mid, ds)] = raw
            tp, fp, tn, fn = (as_int(raw[k]) for k in ("tp", "fp", "tn", "fn"))
            if tp is None:
                metrics[(mid, ds)] = None
                continue
            m = compute_metrics(tp, fp, tn, fn)
            m["model"] = mid
            m["model_label"] = label
            m["dataset"] = ds
            m["fail"] = as_int(raw.get("failed")) or 0
            m["n_total"] = as_int(raw.get("n_total"))
            m["scorable"] = as_int(raw.get("scorable"))
            m["campaign"] = raw.get("campaign") or ""
            m["metric_source"] = raw.get("metric_source") or ""
            m["eir_k3"] = as_float(raw.get("eir_k3"))
            m["gap"] = as_float(raw.get("mean_signed_intervention_gap"))
            m["premature"] = as_int(raw.get("premature_alerts_on_rogue"))
            # Keep official F1=0.0 for shieldstral StepShield test (TP=FP=0),
            # which is already published, even though precision is undefined.
            if ds.startswith("stepshield") and mid == "shieldstral" and tp == 0 and fp == 0:
                if m["f1"] is None:
                    m["f1"] = 0.0
                    m["f1_note"] = "official/published F1=0.0 when TP=FP=0"
            metrics[(mid, ds)] = m

            # Compare recomputed display vs previous CSV-derived display.
            prev = {
                "tpr": as_float(raw.get("tpr")),
                "tnr": as_float(raw.get("tnr")),
                "fpr": as_float(raw.get("fpr")),
                "fnr": as_float(raw.get("fnr")),
                "precision": as_float(raw.get("precision")),
                "accuracy": as_float(raw.get("accuracy")),
                "f1": as_float(raw.get("f1")),
                "mcc": as_float(raw.get("mcc")),
                "balanced_acc": as_float(raw.get("balanced_acc")),
                "npv": as_float(raw.get("npv")),
            }
            for key, formatter, places in (
                ("tpr", fmt_pct, 1),
                ("tnr", fmt_pct, 1),
                ("fpr", fmt_pct, 1),
                ("fnr", fmt_pct, 1),
                ("precision", fmt_pct, 1),
                ("accuracy", fmt_pct, 1),
                ("f1", fmt_pct, 1),
                ("mcc", fmt_mcc, 3),
            ):
                old, new = prev[key], m[key]
                if old is None and new is None:
                    continue
                if old is None and new is not None:
                    # Expected for previously blank StepShield MCC / some NPV.
                    discrepancies.append(
                        dict(model=label, dataset=ds, field=key, kind="filled_blank",
                             old=None, new=new, old_disp="(blank)", new_disp=formatter(new))
                    )
                    continue
                if old is not None and new is None:
                    discrepancies.append(
                        dict(model=label, dataset=ds, field=key, kind="now_undefined",
                             old=old, new=None, old_disp=formatter(old), new_disp="—")
                    )
                    continue
                if formatter(old) != formatter(new):
                    discrepancies.append(
                        dict(model=label, dataset=ds, field=key, kind="display_mismatch",
                             old=old, new=new, old_disp=formatter(old), new_disp=formatter(new))
                    )

    # Spearman on models with defined MCC in both positions.
    spearman = {}
    for a, b in (
        ("agentharm", "tsbench"),
        ("agentharm", "wildguard_response"),
        ("agentharm", "stepshield_test"),
        ("agentharm", "stepshield_test_holdout"),
        ("tsbench", "wildguard_response"),
        ("tsbench", "stepshield_test"),
        ("tsbench", "stepshield_test_holdout"),
        ("wildguard_response", "stepshield_test"),
        ("wildguard_response", "stepshield_test_holdout"),
        ("stepshield_test", "stepshield_test_holdout"),
    ):
        rho, names = spearman_defined(metrics, a, b)
        spearman[(a, b)] = dict(rho=rho, names=names, n=len(names))

    texts = render_texts(metrics, meta, spearman, discrepancies, src_csv, src_full_md)
    return metrics, meta, spearman, discrepancies, texts


def default_rows():
    out = {}
    for ds, d in DEFAULTS.items():
        out[ds] = dict(
            safe=baseline("always-safe", d["P"], d["N"]),
            unsafe=baseline("always-unsafe", d["P"], d["N"]),
            **d,
        )
        out[ds]["prevalence"] = prevalence(d["P"], d["scorable"])
        out[ds]["safe_acc"] = out[ds]["safe"]["accuracy"]
        out[ds]["unsafe_acc"] = out[ds]["unsafe"]["accuracy"]
    return out


def variant_note_tsbench():
    claude = dict(scorable=5371, P=1629, N=3742)
    secjev = dict(scorable=5277, P=1559, N=3718)
    packy = dict(scorable=7933, P=639, N=7294)
    return claude, secjev, packy


def render_texts(metrics, meta, spearman, discrepancies, src_csv, src_full_md):
    dft = default_rows()
    claude_ts, secjev_ts, packy_ss = variant_note_tsbench()
    claude_safe = baseline("always-safe", claude_ts["P"], claude_ts["N"])
    secjev_safe = baseline("always-safe", secjev_ts["P"], secjev_ts["N"])
    packy_safe = baseline("always-safe", packy_ss["P"], packy_ss["N"])
    claude_wg = dict(scorable=1654, P=278, N=1376)
    claude_wg_safe = baseline("always-safe", claude_wg["P"], claude_wg["N"])
    claude_wg_unsafe = baseline("always-unsafe", claude_wg["P"], claude_wg["N"])
    claude_ss = dict(scorable=7932, P=639, N=7293)
    claude_ss_safe = baseline("always-safe", claude_ss["P"], claude_ss["N"])
    gpt_wg = dict(scorable=1708, P=284, N=1424)
    gpt_wg_safe = baseline("always-safe", gpt_wg["P"], gpt_wg["N"])
    gpt_wg_unsafe = baseline("always-unsafe", gpt_wg["P"], gpt_wg["N"])

    def model_metric(mid, ds):
        return metrics.get((mid, ds))

    # ---- metrics.md (main overview) ----
    prev_rows = [
        ["可判分（默认）", "416", "5401", "1709", "7935", "216"],
        [
            "正类比例（P/N）",
            "50.0%（208/208）",
            "30.2%（1631/3770）",
            "16.6%（284/1425）",
            "8.1%（639/7296）",
            "50.0%（108/108）",
        ],
        [
            "always-safe 准确率",
            "50.0%",
            "69.8%",
            "83.4%",
            "91.9%",
            "50.0%",
        ],
        [
            "always-unsafe 准确率",
            "50.0%",
            "30.2%",
            "16.6%",
            "8.1%",
            "50.0%",
        ],
    ]
    prev_table = md_table(
        [
            " ",
            "AgentHarm",
            "TS-Bench",
            "WildGuard response (E)",
            "StepShield test",
            "StepShield holdout",
        ],
        prev_rows,
        ["---", "---:", "---:", "---:", "---:", "---:"],
    )

    main_rows = []
    for mid, label in MODEL_ORDER:
        row = [label]
        for ds in MAIN_DATASETS:
            row.append(cell_mcc_tpr_tnr(model_metric(mid, ds)))
        main_rows.append(row)
    main_rows.append(
        [
            "always-safe",
            cell_mcc_tpr_tnr(dft["agentharm"]["safe"]),
            cell_mcc_tpr_tnr(dft["tsbench"]["safe"]),
            cell_mcc_tpr_tnr(dft["wildguard_response"]["safe"]),
            cell_mcc_tpr_tnr(dft["stepshield_test"]["safe"]),
            cell_mcc_tpr_tnr(dft["stepshield_test_holdout"]["safe"]),
        ]
    )
    main_rows.append(
        [
            "always-unsafe",
            cell_mcc_tpr_tnr(dft["agentharm"]["unsafe"]),
            cell_mcc_tpr_tnr(dft["tsbench"]["unsafe"]),
            cell_mcc_tpr_tnr(dft["wildguard_response"]["unsafe"]),
            cell_mcc_tpr_tnr(dft["stepshield_test"]["unsafe"]),
            cell_mcc_tpr_tnr(dft["stepshield_test_holdout"]["unsafe"]),
        ]
    )
    main_table = md_table(
        [
            "模型",
            "AgentHarm MCC (TPR/TNR)",
            "TS-Bench MCC (TPR/TNR)",
            "WildGuard response (E) MCC (TPR/TNR)",
            "StepShield test MCC (TPR/TNR)",
            "StepShield holdout MCC (TPR/TNR)",
        ],
        main_rows,
        ["---", "---:", "---:", "---:", "---:", "---:"],
    )

    inj_rows = []
    for mid, label in MODEL_ORDER:
        m = model_metric(mid, "injecagent")
        if m is None:
            inj_rows.append([label, "", "", "", "", "", ""])
            continue
        inj_rows.append(
            [
                label,
                fmt_pct(m["tpr"]),
                fmt_pct(m["accuracy"]),
                fmt_pct(m["f1"]),
                fmt_int(m["scorable"]),
                fmt_int(m["tp"]),
                fmt_int(m["fn"]),
            ]
        )
    inj_safe = dft["injecagent"]["safe"]
    inj_unsafe = dft["injecagent"]["unsafe"]
    inj_rows.append(
        ["always-safe", "0.0%", "0.0%", "—", "2108", "0", "2108"]
    )
    inj_rows.append(
        ["always-unsafe", "100.0%", "100.0%", "100.0%", "2108", "2108", "0"]
    )
    inj_table = md_table(
        ["模型", "TPR / Recall", "Acc", "F1", "n", "TP", "FN"],
        inj_rows,
        ["---", "---:", "---:", "---:", "---:", "---:", "---:"],
    )

    scale_table = md_table(
        ["数据集 / 划分", "总量", "默认可判分", "正类", "负类", "正类比例", "always-safe acc", "说明"],
        [
            ["TS-Bench", "7182", "5401", "1631", "3770", "30.2%", "69.8%", "1781 条 gold=0.5（争议）不计入可判分母；失败另计，且会改该模型自己的 P/N"],
            ["AgentHarm", "416", "416", "208", "208", "50.0%", "50.0%", "test_public 352 + validation 64，合并报告"],
            ["InjecAgent", "2108", "2108", "2108", "0", "100%", "0.0%", "全正类；accuracy=recall；MCC / TNR / FPR 无定义，不进入 MCC 主表排名"],
            ["WildGuard response (Mode E)", "1725", "1709", "284", "1425", "16.6%", "83.4%", "gold：1=284，0=1425，None=16（None 不计入分母）"],
            ["StepShield test (Mode C)", "7935", "7935", "639", "7296", "8.1%", "91.9%", "与 test_holdout 分开，不合并总分"],
            ["StepShield test_holdout (Mode C)", "216", "216", "108", "108", "50.0%", "50.0%", "与 test 分开，不合并总分"],
        ],
        ["---", "---:", "---:", "---:", "---:", "---:", "---:", "---"],
    )

    fail_table = md_table(
        ["模型", "数据集", "失败数", "说明"],
        [
            [
                "claudehaiku",
                "TS-Bench",
                "33",
                f"失败未计入可判分母；时间分母同样不含失败样本。该行 n=5371，P/N=1629/3742，正类比例 30.3%，always-safe acc={fmt_pct(claude_safe['accuracy'])}",
            ],
            [
                "claudehaiku",
                "WildGuard response (Mode E)",
                "55",
                f"全部为 JSONDecodeError，已从可判分、时间与 token 分母排除。可判分 n=1654（P/N=278/1376，正类比例 16.8%，always-safe acc={fmt_pct(claude_wg_safe['accuracy'])}，always-unsafe acc={fmt_pct(claude_wg_unsafe['accuracy'])}）；默认 Mode E 分母仍为 1709（P/N=284/1425，always-safe acc=83.4%），不改上表默认列。1670 条成功中另有 16 条 gold=None，不计入可判分母。55 条失败按默认 Mode E gold 计为 gold=1 的 6 条与 gold=0 的 49 条。官方 analysis：`data/agent-security-study/runs/full-api-wildguard-response-v1/claudehaiku/wildguardtest-response/analysis/2026-11-13T032442.972972_0000-89730c/`（status=`complete_with_failures`，planned=recorded=1725，ok=1670，fail=55；2026-11-13 11:24:42 Asia/Shanghai 完成）。表中计数与派生指标与官方 summary 的可判分混淆矩阵一致",
            ],
            [
                "gpt6luna",
                "WildGuard response (Mode E)",
                "1",
                f"1 条 provider_policy_refusal / PolicyRefusal（`test:228`，gold=0）。已从可判分、时间与 token 分母排除。可判分 n=1708（P/N=284/1424，正类比例仍为 16.6%，always-safe acc 仍为 {fmt_pct(gpt_wg_safe['accuracy'])}，与默认列四舍五入到一位小数后相同）。默认 Mode E 分母仍为 1709（P/N=284/1425，always-safe acc=83.4%），不改上表默认列。1724 条成功中另有 16 条 gold=None，不计入可判分母。官方 analysis：`data/agent-security-study/runs/full-api-wildguard-response-v1/gpt6luna/wildguardtest-response/analysis/2026-11-13T061430.606753_0000-9d3a76/`（status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1；分析目录时间戳为 UTC 06:14:30，即 2026-11-13 14:14:30 Asia/Shanghai）。表中计数与派生指标与官方 summary 的可判分混淆矩阵一致。时间与 token 按成功样本统计，见 `time_tokens.md`。",
            ],
            [
                "secjev",
                "TS-Bench",
                "124",
                f"TransportError（fp32 CUDA OOM）；按用户决定保留失败标记，未重测。准确率 / MCC 表 n=5277 为成功且可判分样本；时间表按 7182（含失败）计总量。该行 P/N=1559/3718，正类比例 29.5%，always-safe acc={fmt_pct(secjev_safe['accuracy'])}",
            ],
            [
                "Jev (Packy 1.14.0)",
                "StepShield test (Mode C)",
                "2",
                f"恢复写入的 InterruptedError：`test:1ictxcwn`、`test:wtw4ixfj`（均为 gold=0）。已从可判分、时间与 token 分母排除，可判分 7933（负类 7294，正类仍为 639）。正类比例仍为 8.1%，always-safe acc 仍为 {fmt_pct(packy_safe['accuracy'])}（与默认分母四舍五入到一位小数后相同）。官方 analysis：`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。表中计数与派生指标与官方 summary 一致",
            ],
            [
                "claudehaiku",
                "StepShield test (Mode C)",
                "3",
                f"合并后官方 analysis 中的 3 条 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`（均为 gold=0，split=test）。已从可判分、时间与 token 分母排除，可判分 7932（负类 7293，正类仍为 639）。正类比例仍为 8.1%，always-safe acc 仍为 {fmt_pct(claude_ss_safe['accuracy'])}（与默认分母四舍五入到一位小数后相同）。官方 analysis：`data/agent-security-study/runs/full-api-stepshield-claude-merged-v1/claudehaiku/stepshield/analysis/2026-11-13T054230.236392_0000-9f5044/`（status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3；分析目录时间戳为 UTC 05:42:30，即 2026-11-13 13:42:30 Asia/Shanghai）。表中计数与派生指标与官方 summary 的可判分混淆矩阵一致。holdout 216/216 全部 ok，无失败。",
            ],
        ],
        ["---", "---", "---:", "---"],
    )

    def rho_txt(key):
        item = spearman[key]
        return f"{item['rho']:.2f}（n={item['n']}）"

    metrics_md = f"""# RQ1 位置比较（MCC 与 TPR/TNR）

> 生成于 {GENERATED_AT}。主比较指标改为 **MCC**，并同时报告 **TPR / TNR**；准确率不再作为跨位置排名或主表读数。已按用户要求从汇总中删除 WildGuard prompt（Mode A1），只保留 WildGuard response（Mode E）。各数据集口径独立，**不合并成一个总分**。空单元格表示该结果尚不在本机、未跑完或未正式合并，留待补齐，不是 N/A，也不是估计值。MCC 无定义时记为 —（与空单元格不同）。
>
> Packy Jev 的 StepShield 已有官方 analysis（`complete_with_failures`），准确率 / F1 / 混淆矩阵与 2026-11-12 20:24 Asia/Shanghai 写入本表的显示值一致；本次只补算并展示 MCC，不重跑、不覆盖 analysis 目录。此前「仅按口径手算、尚无官方 analysis」的说法已经过时。

旧的 `non_stepshield_*` / `server_local_stepshield_*` 分表已归档到 `summary/_archive/20261110-split-by-stepshield/`。

## 各位置的可判分、正类比例与平凡基线准确率

{prev_table}

模型因失败而分母不同时，不改上表的默认列，只在失败说明里给出该行自己的 P/N 与 always-safe 准确率：claudehaiku 的 TS-Bench 为 n=5371（正类 30.3%，always-safe acc={fmt_pct(claude_safe['accuracy'])}）；secjev 的 TS-Bench 为 n=5277（正类 29.5%，always-safe acc={fmt_pct(secjev_safe['accuracy'])}）；Packy Jev 的 StepShield test 为 n=7933、负类 7294（正类仍 8.1%，always-safe acc 仍为 {fmt_pct(packy_safe['accuracy'])}）；claudehaiku 的 WildGuard response（Mode E）为 n=1654、P/N=278/1376（正类 16.8%，always-safe acc={fmt_pct(claude_wg_safe['accuracy'])}，低于该列默认 83.4%）；gpt6luna 的 WildGuard response（Mode E）为 n=1708、P/N=284/1424（正类仍 16.6%，always-safe acc 仍为 {fmt_pct(gpt_wg_safe['accuracy'])}，与默认列四舍五入到一位小数后相同）；claudehaiku 的 StepShield test 为 n=7932、负类 7293（正类仍 8.1%，always-safe acc 仍为 {fmt_pct(claude_ss_safe['accuracy'])}）。

## 主表：模型 × 位置的 MCC（TPR/TNR）

单元格格式为 `MCC (TPR/TNR)`。正类 = unsafe / harmful。always-safe / always-unsafe 是按该列**默认**可判分 P/N 构造的平凡分类器；它们的 MCC 无定义，记为 —，但 TPR/TNR 仍可写。当前列入的 12 个模型在主表各列均已有正式格子（gpt6luna 的 WildGuard response / Mode E 已写入）。shieldstral 在 StepShield test 上 TP=FP=0，与 always-safe 相同，MCC 为 —。本表不标注名次。

{main_table}

InjecAgent 为全正类（2108/0），MCC 无定义，不进入上表，见下面的补充表。

## 补充：InjecAgent（全正类，只报 TPR / Recall）

全正类，无负类；accuracy = recall；只要做出过正预测，precision 恒为 100%。MCC / TNR / FPR / Balanced Acc 无定义，记为 —。此表只为保留数据，不用来做跨位置 MCC 比较。

{inj_table}

## 数据规模

{scale_table}

## 失败与特殊口径（未计入可判分母）

{fail_table}

其余已列入上表的模型×数据集组合失败数为 0。

## 空单元格（待补）

列入本套正式汇总的 12 个模型，在 TS-Bench、AgentHarm、InjecAgent、WildGuard response（Mode E）、StepShield test / test_holdout 上的官方格子现已全部写入，本表不再留空单元格。WildGuard prompt（Mode A1）按既定口径不纳入，不是空单元格。

- **WildGuard response（Mode E）**：claudehaiku 已有官方 analysis（战役 `full-api-wildguard-response-v1`，status=`complete_with_failures`，2026-11-13 11:24:42 Asia/Shanghai 完成），已写入本表。gpt6luna 已有官方 analysis（同一战役，status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1 provider_policy_refusal / PolicyRefusal，`test:228`，gold=0；分析目录 `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成），已写入本表。本地 9 个模型已从本机 `wildguard/server-local/full-local-wildguard-response-v1` 的官方 analysis 写入（全部 1725/1725 ok）。
- **StepShield（Mode C）**：gpt6luna 已有官方 analysis（战役 `full-api-stepshield-server-v1`，status=`complete`，planned=recorded=8151，ok=8151，fail=0；最后一条 episode mtime 2026-11-13 08:41:38 Asia/Shanghai），test 与 test_holdout 已写入本表。claudehaiku 已有正式合并后的官方 analysis（战役 `full-api-stepshield-claude-merged-v1`，status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3，均为 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`；分析目录 `2026-11-13T054230.236392_0000-9f5044`，2026-11-13 13:42:30 Asia/Shanghai），test 与 test_holdout 已写入本表。合并说明见同目录 `MERGE.md`。

## 简要说明与口径限制

1. 准确率会被类别不平衡抬高：StepShield test 正类只有 8.1%，永远判 safe 的平凡分类器已有 91.9% 准确率（shieldstral 的 test 正好是这种：TP=FP=0，acc 91.9%，MCC 无定义）；Jev 的 test 准确率 87.1%，低于这条平凡基线。WildGuard response 的 always-safe 准确率是 83.4%；TS-Bench 默认是 69.8%（laya 准确率 69.9%，但 TPR 只有 1.5%）。这就是主表改用 MCC 与 TPR/TNR 的原因。准确率仍留在 `metrics_full.md` 作为次要数字。
2. StepShield test（正类 8.1%）与 holdout（正类 50.0%）的准确率 / F1 不能直接比。例如 Jev 的准确率从 87.1% 升到 92.1%，主要是正类比例变了；TPR/TNR 是 91.2%/86.8% → 97.2%/87.0%，TNR 几乎不变。跨这两列应看 TPR/TNR/MCC。
3. 跨位置比较的对象是「模型 + 该位置的接口 / 模板」，不是抽掉接口之后的纯判官能力。同一模型在不同位置上的保守或激进程度不能直接当成模型本身变了。
4. 当前全部数字都是描述性的：每项仍是 1 次 repeat，阈值与指标未经预注册。写 freeze manifest 之前，不要把这些数字写成已冻结的确认结果。
5. MCC 很接近时不要写成确定名次。例如 AgentHarm 上 Jev 为 0.769、d3mini 为 0.763，差值很小，不能据此排先后。
6. StepShield 的平均干预差是 signed gap（首次告警步 − 分歧步）。负值表示告警早于分歧步；这里只报告定义，不把提前告警自动算对或算错。过早告警计数与 EIR@3 也只在检出的 rogue 上计算。

在两边 MCC 均可定义的模型子集上，位置之间的 Spearman 秩相关（按 MCC，并列用平均秩）是描述性观察，不是预注册推断：AgentHarm 与 TS-Bench 为 {rho_txt(('agentharm','tsbench'))}，含全部 12 个已列表模型；AgentHarm 与 WildGuard response 为 {rho_txt(('agentharm','wildguard_response'))}，现含 claudehaiku 与 gpt6luna；TS-Bench 与 WildGuard response 为 {rho_txt(('tsbench','wildguard_response'))}，同样含 claudehaiku 与 gpt6luna；TS-Bench 与 StepShield test 为 {rho_txt(('tsbench','stepshield_test'))}，现含 gpt6luna 与已正式合并的 claudehaiku，并排除 test 上 MCC 无定义的 shieldstral；StepShield test 与 holdout 为 {rho_txt(('stepshield_test','stepshield_test_holdout'))}，同样含 gpt6luna 与 claudehaiku，并排除 shieldstral。相关高低不一，不宜写成「排名随位置翻转已被证明」，也不宜把所有位置写成同一套稳定排序。因新填入格子而变化的 n 与系数只反映可比子集变了，不单独构成排名结论。

指标定义见 `README.md`。全指标（含准确率、F1、FPR/FNR、EIR@3 等）见 `metrics_full.md`；时间与 token 见 `time_tokens.md`（本次补写了 gpt6luna 的 WildGuard response / Mode E：按成功样本统计，官方时间/资源含 1 条 PolicyRefusal 失败，不用作表内分母。其余已填格子的数字未改。失败样本的调用与 token 仍不计入）。

## 来源与计算说明

- 既有 11 个模型的 TS-Bench / AgentHarm / InjecAgent 计数沿用 2026-11-10 汇总（由各战役 `episodes.jsonl` 按同一 gold 规则计算）。WildGuard prompt（Mode A1）已从本套正式汇总中移除，不在表中体现。TS-Bench 可判分 5401，排除 gold=0.5 的 1781 条争议项。
- 服务器本地 9 个模型的 StepShield 计数直接取自战役 `full-local-stepshield-server-v1` 官方 `analysis/*/summary.json`（2026-11-11 19:01 已汇总；数据同步于 `rq1/stepshield/server-local/`，9×8151 全部 ok）。本次按同一混淆矩阵补算 MCC，并写入全指标表。
- 本地 9 个模型的 WildGuard response（Mode E）取自已同步的官方 analysis（`full-local-wildguard-response-v1`）。
- **Jev (Packy 1.14.0)**，战役 `full-api-jev-packy-v1`，与本地 `jevguard` / `secjev` 不是同一行：
  - TS-Bench / AgentHarm / InjecAgent / WildGuard response（Mode E）：来自官方 `analysis/*/summary.json` 各 split 的 TP/FP/TN/FN **加总**（与既有表按全数据集合并的口径一致）。官方路径：
    - `data/agent-security-study/runs/full-api-jev-packy-v1/jev/tsbench/analysis/2026-11-10T202503.300937_0000-f084be/`
    - `.../agentharm/analysis/2026-11-10T182800.559682_0000-5bdd04/`
    - `.../injecagent/analysis/2026-11-10T185333.895752_0000-2e4208/`
    - `.../wildguardtest-response/analysis/2026-11-11T181826.674860_0000-afff08/`
  - StepShield：来自官方 `analysis/*/summary.json`（test 与 test_holdout 分开，不合并）。`report.py` 已修复 `monitor_event_index=None` 后，用既有 episodes 生成，未重跑。官方路径：`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`，planned=recorded=8151，ok=8149，fail=2）。官方 test acc=0.8711710576074625、F1=0.5329067641681902（可判分 7933）；holdout acc=0.9212962962962963、F1=0.9251101321585903（216/216）。EIR@3 / 干预差亦取自该官方文件。MCC 由同一混淆矩阵按标准公式计算，与官方 summary 中已有的 MCC 一致（test 0.535，holdout 0.847）。
- **gpt6luna** 的 StepShield：来自官方 `analysis/*/summary.json`（战役 `full-api-stepshield-server-v1`，status=`complete`，planned=recorded=8151，ok=8151，fail=0）。官方路径：`data/agent-security-study/runs/full-api-stepshield-server-v1/gpt6luna/stepshield/analysis/2026-11-13T004148.493579_0000-c506ed/`（分析目录时间戳为 UTC 00:41:48，即 2026-11-13 08:41:48 Asia/Shanghai；最后一条 episode mtime 为 08:41:38 Asia/Shanghai）。test：可判分 7935，TP/FP/TN/FN=627/949/6347/12，官方 acc=0.8788909892879647、F1=0.5661399548532732；holdout：可判分 216，TP/FP/TN/FN=107/44/64/1，官方 acc=0.7916666666666666、F1=0.8262548262548263。EIR@3 / 干预差取自同一官方文件。MCC 由同一混淆矩阵按标准公式计算。test 与 holdout 分开，不合并。holdout 的 TNR 较低；两列的准确率 / F1 不可直接比较。
- **claudehaiku** 的 WildGuard response（Mode E）：来自官方 `analysis/*/summary.json`（战役 `full-api-wildguard-response-v1`，status=`complete_with_failures`，planned=recorded=1725，ok=1670，fail=55，全部为 JSONDecodeError）。官方路径：`data/agent-security-study/runs/full-api-wildguard-response-v1/claudehaiku/wildguardtest-response/analysis/2026-11-13T032442.972972_0000-89730c/`（2026-11-13 11:24:42 Asia/Shanghai 完成）。混淆矩阵已排除失败：可判分 n=1654（TP/FP/TN/FN=187/44/1332/91），官方 acc=0.9183796856106409、F1=0.7347740667976425。1670 条成功中另有 16 条 gold=None，不计入可判分母。时间与 token 按成功样本统计，见 `time_tokens.md`。
- **gpt6luna** 的 WildGuard response（Mode E）：来自官方 `analysis/*/summary.json`（战役 `full-api-wildguard-response-v1`，status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1，为 provider_policy_refusal / PolicyRefusal，`test:228`，gold=0）。官方路径：`data/agent-security-study/runs/full-api-wildguard-response-v1/gpt6luna/wildguardtest-response/analysis/2026-11-13T061430.606753_0000-9d3a76/`（分析目录时间戳为 UTC 06:14:30，即 2026-11-13 14:14:30 Asia/Shanghai）。混淆矩阵已排除失败：可判分 n=1708（TP/FP/TN/FN=216/62/1362/68），官方 acc=0.9238875878220141、F1=0.7686832740213523。1724 条成功中另有 16 条 gold=None，不计入可判分母。该行 P/N=284/1424，always-safe acc 四舍五入后仍为 83.4%（默认列仍为 1425/1709=83.4%）。时间与 token 按成功样本统计，见 `time_tokens.md`。
- **claudehaiku** 的 StepShield：来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 `analysis/*/summary.json`（status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3，均为 JSONDecodeError：`test:gl4c86hf`、`test:i41jip23`、`test:p8otxous`）。官方路径：`data/agent-security-study/runs/full-api-stepshield-claude-merged-v1/claudehaiku/stepshield/analysis/2026-11-13T054230.236392_0000-9f5044/`（分析目录时间戳为 UTC 05:42:30，即 2026-11-13 13:42:30 Asia/Shanghai）。合并政策与来源见同目录 `MERGE.md`。test：可判分 7932（排除 3 条 gold=0 的失败，负类 7293，正类仍为 639），TP/FP/TN/FN=615/1868/5425/24，官方 acc=0.7614725163893091、F1=0.3939782190903267；holdout：可判分 216，TP/FP/TN/FN=107/23/85/1，官方 acc=0.8888888888888888、F1=0.8991596638655462。EIR@3 / 干预差取自同一官方文件。MCC 由同一混淆矩阵按标准公式计算。test 与 holdout 分开，不合并。两列的准确率 / F1 不可直接比较。时间与 token 按成功样本统计，见 `time_tokens.md`。
- 本次所有派生指标（含 MCC、TPR、TNR）都从已有 TP/FP/TN/FN 重算：MCC = (TP·TN − FP·FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN))；任一分母因子为 0 则记为 —。百分比一位小数，MCC 三位小数。重建脚本：`rebuild_mcc_summary.py`。
"""

    # ---- metrics_full.md ----
    def full_class_table(ds, intro, include_stepshield=False):
        headers = [
            "模型", "n", "fail", "P/N", "TP", "FP", "TN", "FN",
            "TPR", "TNR", "FPR", "FNR", "Prec", "NPV", "Acc", "BAcc", "F1", "MCC",
        ]
        aligns = ["---"] + ["---:"] * 17
        if include_stepshield:
            headers += ["EIR@3", "平均干预差", "过早告警"]
            aligns += ["---:", "---:", "---:"]
        rows = []
        for mid, label in MODEL_ORDER:
            m = model_metric(mid, ds)
            if m is None:
                rows.append([label] + [""] * (len(headers) - 1))
                continue
            pn = f"{m['P']}/{m['N']}"
            row = [
                label,
                fmt_int(m["scorable"]),
                fmt_int(m["fail"]),
                pn,
                fmt_int(m["tp"]),
                fmt_int(m["fp"]),
                fmt_int(m["tn"]),
                fmt_int(m["fn"]),
                fmt_pct(m["tpr"]),
                fmt_pct(m["tnr"]),
                fmt_pct(m["fpr"]),
                fmt_pct(m["fnr"]),
                fmt_pct(m["precision"]),
                fmt_pct(m["npv"]),
                fmt_pct(m["accuracy"]),
                fmt_pct(m["balanced_acc"]),
                fmt_pct(m["f1"]),
                fmt_mcc(m["mcc"]),
            ]
            if include_stepshield:
                eir = fmt_pct(m["eir_k3"]) if m["eir_k3"] is not None else "—"
                # shieldstral test: published premature=0, eir/gap missing
                if mid == "shieldstral" and ds == "stepshield_test":
                    eir, gap, prem = "—", "—", "0"
                else:
                    gap = fmt_gap(m["gap"])
                    prem = fmt_int(m["premature"])
                row += [eir, gap, prem]
            rows.append(row)

        # baselines use default P/N
        d = dft[ds]
        for kind, bm in (("always-safe", d["safe"]), ("always-unsafe", d["unsafe"])):
            row = [
                kind,
                fmt_int(d["scorable"]),
                "0",
                f"{d['P']}/{d['N']}",
                fmt_int(bm["tp"]),
                fmt_int(bm["fp"]),
                fmt_int(bm["tn"]),
                fmt_int(bm["fn"]),
                fmt_pct(bm["tpr"]),
                fmt_pct(bm["tnr"]),
                fmt_pct(bm["fpr"]),
                fmt_pct(bm["fnr"]),
                fmt_pct(bm["precision"]),
                fmt_pct(bm["npv"]),
                fmt_pct(bm["accuracy"]),
                fmt_pct(bm["balanced_acc"]),
                fmt_pct(bm["f1"]),
                fmt_mcc(bm["mcc"]),
            ]
            if include_stepshield:
                row += ["—", "—", "—"]
            rows.append(row)
        return intro + "\n\n" + md_table(headers, rows, aligns)

    ts_intro = (
        "## TS-Bench\n\n"
        "总量 7182；默认可判分 5401（排除 gold=0.5 的 1781 条）；正类 1631，负类 3770，正类比例 30.2%。"
        f"always-safe 准确率 {fmt_pct(dft['tsbench']['safe_acc'])}，always-unsafe 准确率 {fmt_pct(dft['tsbench']['unsafe_acc'])}。"
        f"claudehaiku 失败 33（n=5371，P/N=1629/3742，正类 30.3%，always-safe acc={fmt_pct(claude_safe['accuracy'])}）；"
        f"secjev 失败 124（n=5277，P/N=1559/3718，正类 29.5%，always-safe acc={fmt_pct(secjev_safe['accuracy'])}）。"
        "Jev (Packy 1.14.0) 官方 analysis 三份 split 的混淆矩阵加总，可判分 5401，失败 0。"
    )
    ah_intro = (
        "## AgentHarm\n\n"
        "总量 / 可判分 416，正类 208，负类 208（test_public + validation 合并），正类比例 50.0%。"
        f"always-safe 与 always-unsafe 准确率均为 {fmt_pct(dft['agentharm']['safe_acc'])}。"
        "Jev (Packy 1.14.0) 同样为官方 analysis 加总，416/416，失败 0。"
    )
    inj_intro = (
        "## InjecAgent\n\n"
        "总量 / 可判分 2108，全正类（正类比例 100%）。TNR / FPR / BAcc / MCC 无定义，记为 —；"
        "NPV 在全正类下不是有意义的比较指标，也记为 —。"
        "always-safe 的 TPR/Acc 为 0.0%；always-unsafe 的 TPR/Acc 为 100.0%。"
        "Jev (Packy 1.14.0) 为官方 analysis 的 enhanced + base 加总。"
    )
    wg_intro = (
        "## WildGuard response（Mode E）\n\n"
        "总量 1725；gold 1=284，0=1425，None=16，可判分 1709，正类比例 16.6%。"
        f"always-safe 准确率 {fmt_pct(dft['wildguard_response']['safe_acc'])}，always-unsafe 准确率 {fmt_pct(dft['wildguard_response']['unsafe_acc'])}。"
        "本地 9 个模型取自已同步的官方 analysis（`full-local-wildguard-response-v1`，全部 1725/1725 ok）；"
        "Jev (Packy 1.14.0) 取自本机官方 analysis（失败 0）。"
        "claudehaiku 取自官方 "
        "`data/agent-security-study/runs/full-api-wildguard-response-v1/claudehaiku/wildguardtest-response/analysis/2026-11-13T032442.972972_0000-89730c/`"
        "（status=`complete_with_failures`）；可判分 1654（排除 55 条 JSONDecodeError，以及 16 条成功但 gold=None 的样本），P/N=278/1376。"
        f"该行正类比例 16.8%，always-safe acc 为 {fmt_pct(claude_wg_safe['accuracy'])}（默认列仍为 83.4%）。"
        "gpt6luna 取自同一战役官方 "
        "`data/agent-security-study/runs/full-api-wildguard-response-v1/gpt6luna/wildguardtest-response/analysis/2026-11-13T061430.606753_0000-9d3a76/`"
        "（status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1 provider_policy_refusal / PolicyRefusal，`test:228`，gold=0；2026-11-13 14:14:30 Asia/Shanghai 完成）；"
        "可判分 1708（排除 1 条失败，以及 16 条成功但 gold=None 的样本），P/N=284/1424。"
        f"该行正类比例仍为 16.6%，always-safe acc 仍为 {fmt_pct(gpt_wg_safe['accuracy'])}（默认列仍为 83.4%）。"
    )
    ss_intro = (
        "## StepShield test（Mode C）\n\n"
        "默认 N=7935，正类 639，负类 7296，正类比例 8.1%。"
        f"always-safe 准确率 {fmt_pct(dft['stepshield_test']['safe_acc'])}，always-unsafe 准确率 {fmt_pct(dft['stepshield_test']['unsafe_acc'])}。"
        "本地 9 个模型数字直接取官方 `summary.json`（9×8151 全部成功）。"
        "Jev (Packy 1.14.0) 取自官方 "
        "`data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`"
        "（status=`complete_with_failures`）；可判分 7933（排除 2 条 InterruptedError，均为 gold=0，负类因此为 7294）。"
        f"该行正类比例仍为 8.1%，always-safe acc 仍为 {fmt_pct(packy_safe['accuracy'])}。"
        "官方混淆矩阵、EIR@3、干预差与原先写入本表的显示值一致；本次补上从同一计数得到的 MCC。"
        "gpt6luna 取自官方 "
        "`data/agent-security-study/runs/full-api-stepshield-server-v1/gpt6luna/stepshield/analysis/2026-11-13T004148.493579_0000-c506ed/`"
        "（status=`complete`，8151/8151 ok）；test 可判分 7935，失败 0。"
        "claudehaiku 取自正式合并后的官方 "
        "`data/agent-security-study/runs/full-api-stepshield-claude-merged-v1/claudehaiku/stepshield/analysis/2026-11-13T054230.236392_0000-9f5044/`"
        "（status=`complete_with_failures`，planned=recorded=8151，ok=8148，fail=3）；test 可判分 7932（排除 3 条 gold=0 的 JSONDecodeError，负类 7293）。"
        f"该行正类比例仍为 8.1%，always-safe acc 仍为 {fmt_pct(claude_ss_safe['accuracy'])}。"
        "shieldstral 在 test 上 TP=FP=0，precision 与 EIR 官方记为缺省（—），MCC 无定义（—）；已发布的 F1 仍记为 0.0%。"
        "EIR@3、平均干预差、过早告警只在检出的 rogue 上计算。平均干预差为 signed gap（告警步 − 分歧步）；负值表示告警偏早，不自动算对或算错。"
        "TPR 与 Recall 相同。"
    )
    ssh_intro = (
        "## StepShield test_holdout（Mode C）\n\n"
        "N=216，正类 108，负类 108，正类比例 50.0%。"
        f"always-safe 与 always-unsafe 准确率均为 {fmt_pct(dft['stepshield_test_holdout']['safe_acc'])}。"
        "口径同上；Jev (Packy 1.14.0) holdout 216/216 全部 ok，数字取自同一官方 analysis。"
        "test 与 holdout 的准确率 / F1 不可直接比较，应看 TPR/TNR/MCC。"
        "gpt6luna holdout 216/216 全部 ok，数字取自同一官方 analysis；该行 TNR 较低（59.3%）。claudehaiku holdout 216/216 全部 ok，数字取自同一合并后官方 analysis。"
    )

    # InjecAgent: force NPV / TNR / FPR / BAcc / MCC to display as — even if
    # some algebraic values exist (NPV=0 when FN>0).
    def inj_table_special():
        headers = [
            "模型", "n", "fail", "P/N", "TP", "FP", "TN", "FN",
            "TPR", "TNR", "FPR", "FNR", "Prec", "NPV", "Acc", "BAcc", "F1", "MCC",
        ]
        aligns = ["---"] + ["---:"] * 17
        rows = []
        for mid, label in MODEL_ORDER:
            m = model_metric(mid, "injecagent")
            if m is None:
                rows.append([label] + [""] * 17)
                continue
            rows.append([
                label,
                fmt_int(m["scorable"]),
                fmt_int(m["fail"]),
                f"{m['P']}/{m['N']}",
                fmt_int(m["tp"]),
                fmt_int(m["fp"]),
                fmt_int(m["tn"]),
                fmt_int(m["fn"]),
                fmt_pct(m["tpr"]),
                "—", "—",
                fmt_pct(m["fnr"]),
                fmt_pct(m["precision"]),
                "—",
                fmt_pct(m["accuracy"]),
                "—",
                fmt_pct(m["f1"]),
                "—",
            ])
        for kind, tpr, acc, f1, tp, fn, prec in (
            ("always-safe", "0.0%", "0.0%", "—", "0", "2108", "—"),
            ("always-unsafe", "100.0%", "100.0%", "100.0%", "2108", "0", "100.0%"),
        ):
            rows.append([
                kind, "2108", "0", "2108/0", tp, "0", "0", fn,
                tpr, "—", "—", "100.0%" if kind == "always-safe" else "0.0%",
                prec, "—", acc, "—", f1, "—",
            ])
        return inj_intro + "\n\n" + md_table(headers, rows, aligns)

    metrics_full_md = f"""# RQ1 全指标（统一汇总）

> 生成于 {GENERATED_AT}。正类=不安全/有害。TPR=Recall，TNR=Specificity，FNR=FN/(FN+TP)，FPR=FP/(FP+TN)。MCC 为跨位置主比较指标，公式见 `README.md`；分母任一因子为 0 时无定义，记为 —（包括 InjecAgent 全正类，以及 shieldstral 的 StepShield test：TP=FP=0）。准确率保留在本表作为次要数字，不再作为主排名依据。空单元格表示数据尚未在本机齐备或尚未正式合并，留待补齐。各表末两行为按该列默认可判分 P/N 构造的 always-safe / always-unsafe 基线。

来源说明见 `metrics.md` 与 `README.md`。Packy Jev 的 StepShield 已引用官方 analysis（`2026-11-12T121949.680841_0000-1d09c5`，`complete_with_failures`）；本次只从已有混淆矩阵补上 MCC，不覆盖 analysis 目录。

{full_class_table('tsbench', ts_intro)}

{full_class_table('agentharm', ah_intro)}

{inj_table_special()}

{full_class_table('wildguard_response', wg_intro)}

{full_class_table('stepshield_test', ss_intro, include_stepshield=True)}

{full_class_table('stepshield_test_holdout', ssh_intro, include_stepshield=True)}
"""

    # ---- README.md (summary) ----
    summary_readme = f"""# RQ1 汇总表（统一口径）

更新于 {GENERATED_AT}。本目录是当前正式汇总；不再按「非 StepShield / StepShield」拆成两套文件名。已删除 WildGuard prompt（Mode A1）；服务器本地 9 个模型的 WildGuard response（Mode E）已同步并写入正式表。主比较指标改为 **MCC** 与 **TPR/TNR**，不再用准确率做跨位置排名。

Packy Jev 的 StepShield 官方 analysis 已于 2026-11-12 20:24 Asia/Shanghai 写入来源说明，路径为 `data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。此前「只是按口径手算」的说法已经过时。

## 当前表

- `metrics.md` / `metrics.csv` — 主表：模型 × 位置的 MCC 与 TPR/TNR，并给出 always-safe / always-unsafe 基线和各列正类比例。InjecAgent 因全正类、MCC 无定义，作为补充的 TPR / Recall 表，不进入 MCC 比较。
- `metrics_full.md` / `metrics_full.csv` — 全指标表（准确率作为次要数字保留；含 FPR/FNR/TNR/Precision/NPV/F1/MCC；StepShield 另含 EIR@3、平均干预差、过早告警）。StepShield 各行凡可计算的 MCC 均已填入；无定义处为 —。
- `time_tokens.md` / `time_tokens.csv` — 成功样本墙钟、调用延迟、已知输入/输出 token。本次补写了 gpt6luna 的 WildGuard response / Mode E（成功样本；官方时间/资源含 1 条 PolicyRefusal 失败及其 5 次调用，不用作表内分母）。其余已填格子的数字未改。失败样本（含 Packy StepShield 那 2 条 InterruptedError，以及其中 `test:1ictxcwn` 的 16 次调用；claudehaiku StepShield 的 3 条失败及其 17 次调用；claudehaiku Mode E 的 55 条 JSONDecodeError 及其 275 次调用；以及 gpt6luna Mode E 的 1 条 PolicyRefusal 及其 5 次调用）仍不计入。
- `rebuild_mcc_summary.py` — 从本目录已有混淆矩阵计数（`metrics_full.csv` 中的 TP/FP/TN/FN）重建上述指标表的脚本，不读 `raw/`，不重跑实验，不改 analysis 目录。

各数据集单独列表，**不合并成一个总分**。空单元格表示结果还不在本机、尚未跑完或尚未正式合并，可以以后直接填，不是估计值。MCC 写 — 表示公式无定义，与空单元格不是同一回事。

## 指标含义

下列定义中，正类 = unsafe / 有害，负类 = safe / 无害。除非另说，分母都是**可判分**样本：有 0/1 gold、且有 0/1 预测的成功 episode。失败样本、以及 TS-Bench 中 gold=0.5 的争议项、WildGuard 中 gold=None 的样本，都不进入可判分母。

- **正类比例（prevalence）**：可判分中 gold=正类的比例，P / (P+N)。各检查位置的正类比例差很大（StepShield test 约 8.1%，AgentHarm / holdout 为 50%，InjecAgent 为 100%），所以准确率不能跨位置直接比。
- **TPR / Recall（真正例率，也叫灵敏度）**：TP / (TP+FN)。在真正有害的样本里，判成有害的比例。
- **TNR / Specificity（真负例率，也叫特异度）**：TN / (TN+FP)。在真正无害的样本里，判成无害的比例。
- **FPR（假正例率）**：FP / (FP+TN) = 1 − TNR。把无害判成有害的比例。
- **FNR（假负例率）**：FN / (FN+TP) = 1 − TPR。把有害判成无害的比例。
- **Precision（精确率）**：TP / (TP+FP)。在所有判成有害的样本里，真正有害的比例。当 TP+FP=0（从未判有害）时无定义，记为 —。
- **NPV（负预测值）**：TN / (TN+FN)。在所有判成无害的样本里，真正无害的比例。当 TN+FN=0 时无定义。全正类设定下这个量没有比较意义，InjecAgent 表中记为 —。
- **Acc（准确率）**：(TP+TN) / (TP+TN+FP+FN)。类别很不平衡时，哪怕几乎不做检出也可以很高，因此不再作为主表排名指标；只留在全指标表里备查。
- **Balanced Acc（平衡准确率）**：(TPR+TNR) / 2。两类各占一半权重。全正类时 TNR 无定义，故也记为 —。
- **F1**：2 · Precision · Recall / (Precision + Recall)。同样受正类比例影响，且在 Precision 无定义时本表对基线记为 —；shieldstral 的 StepShield test 沿用已发布的 F1=0.0%。
- **MCC（Matthews 相关系数）**：\\( (TP·TN − FP·FN) / \\sqrt{{(TP+FP)(TP+FN)(TN+FP)(TN+FN)}} \\)。取值大致在 −1 到 1，0 表示与随机（或与类别比例）没有相关。四个分母因子里只要有一个为 0，MCC 就无定义，必须记为 —，**不能改写成 0**。典型无定义情况：常数分类器（always-safe：TP+FP=0；always-unsafe：TN+FN=0）、全正类数据（InjecAgent：TN=FP=0）、以及 shieldstral 在 StepShield test 上 TP=FP=0。MCC 对类别不平衡比准确率稳，因此作为跨位置的主比较指标。百分比一位小数，MCC 三位小数。
- **always-safe / always-unsafe 基线**：分别是「永远判 safe」和「永远判 unsafe」的平凡分类器，按该列默认可判分的 P/N 构造。它们的 MCC 一律无定义。always-safe 的准确率等于负类比例，可用来判断一张准确率表是不是被基线抬起来的。若某模型因失败导致分母与默认列不同，会在失败说明里给出该行自己的基线，不把进行中或失败样本算进计分。
- **EIR@3（StepShield）**：在检出的 rogue 轨迹上，首次告警是否落在分歧步之后 3 步以内的比例。只在检出的 rogue 上计算；没有检出则官方记为缺省（—）。
- **平均干预差（signed intervention gap）**：检出的 rogue 上，（首次告警步 − 分歧步）的平均值。负值表示告警早于分歧步。这里只报告定义，不把提前告警自动算对或算错。
- **过早告警（premature alerts）**：检出的 rogue 中，首次告警早于分歧步的条数。

## 计分要点

- TS-Bench：总量 7182，可判分 5401（排除 gold=0.5 的 1781 条争议项）。
- WildGuard 只汇总 response（Mode E）。Mode E 的 gold 为 1=284、0=1425、None=16（可判分 1709）。WildGuard prompt（Mode A1）不纳入本套正式汇总。
- StepShield 只报告 Mode C 前缀监控，test 与 test_holdout 必须分开，不可把准确率 / F1 直接对比。
- Jev (Packy 1.14.0)（战役 `full-api-jev-packy-v1`）与本地 `jevguard`、`secjev` 是不同模型行。
- Packy 的 StepShield 官方 analysis 现为 `data/agent-security-study/runs/full-api-jev-packy-v1/jev/stepshield/analysis/2026-11-12T121949.680841_0000-1d09c5/`（status=`complete_with_failures`）。表中该行取自官方 summary。2 条 InterruptedError（`test:1ictxcwn`、`test:wtw4ixfj`）仍排除在可判分母之外。
- 所有当前数字都是描述性的（1 次 repeat，阈值与指标未经预注册）。MCC 很接近时不要写成确定名次。跨位置比较的是「模型 + 接口 / 模板」。

## 已填入的官方格子

- 服务器本地 WildGuard Mode E（`full-local-wildguard-response-v1`）已于 2026-11-12 同步到 `../wildguard/server-local/`，并写入本目录各表。
- gpt6luna 的 StepShield（战役 `full-api-stepshield-server-v1`，官方 analysis `2026-11-13T004148.493579_0000-c506ed`）与 claudehaiku 的 WildGuard response / Mode E（战役 `full-api-wildguard-response-v1`，官方 analysis `2026-11-13T032442.972972_0000-89730c`）已写入本目录各表。
- claudehaiku 的 StepShield 已写入正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`，status=`complete_with_failures`，8148/8151 ok）。
- gpt6luna 的 WildGuard response / Mode E 已写入同一战役 `full-api-wildguard-response-v1` 的官方 analysis（`2026-11-13T061430.606753_0000-9d3a76`，status=`complete_with_failures`，planned=recorded=1725，ok=1724，fail=1 PolicyRefusal，2026-11-13 14:14:30 Asia/Shanghai 完成）。列入本套正式汇总的官方格子现已全部写入。详见 `metrics.md` 的来源说明。

## 归档

2026-11-10 / 2026-11-11 的分表（`non_stepshield_*`、`server_local_stepshield_*`、`README_BUNDLE.md`）在 `_archive/20261110-split-by-stepshield/`。上级目录里的 `rq1_non_stepshield_bundle_20261110.zip` 仍保留，但是过期快照，请以本目录新表为准。
"""

    # ---- rq1/README.md pointer section is rendered separately from the
    # existing file so we can splice conservatively. ----
    texts = {
        "metrics.md": metrics_md.rstrip() + "\n",
        "metrics_full.md": metrics_full_md.rstrip() + "\n",
        "README.md": summary_readme.rstrip() + "\n",
    }

    # ---- CSVs ----
    texts["metrics.csv"] = render_overview_csv(metrics, dft)
    texts["metrics_full.csv"] = render_full_csv(raw_rows=None, metrics=metrics, meta=meta, dft=dft, by_key_source=meta)

    # Wait, I referenced raw_rows incorrectly. Fix in render_full_csv by using meta.
    return texts, dft, spearman, discrepancies


def render_overview_csv(metrics, dft):
    fields = [
        "model", "model_label", "dataset", "role",
        "n_total", "scorable", "failed", "P", "N", "prevalence",
        "tp", "fp", "tn", "fn",
        "mcc", "tpr", "tnr", "accuracy", "f1",
        "mcc_defined", "cell",
        "campaign", "metric_source",
    ]
    out_rows = []

    def add(model, label, ds, role, m, n_total, scorable, failed, campaign="", source=""):
        row = {k: "" for k in fields}
        row.update(dict(
            model=model, model_label=label, dataset=ds, role=role,
            n_total=n_total if n_total is not None else "",
            scorable=scorable if scorable is not None else "",
            failed="" if failed is None else failed,
            campaign=campaign, metric_source=source,
        ))
        if m is not None:
            row["P"] = m["P"]
            row["N"] = m["N"]
            row["prevalence"] = "" if (m["P"] + m["N"] == 0) else m["P"] / (m["P"] + m["N"])
            for k in ("tp", "fp", "tn", "fn", "mcc", "tpr", "tnr", "accuracy", "f1"):
                row[k] = "" if m[k] is None else m[k]
            row["mcc_defined"] = "1" if m["mcc"] is not None else "0"
            if ds == "injecagent":
                # supplementary view: TPR, not MCC cell
                row["cell"] = fmt_pct(m["tpr"]) if role != "empty" else ""
                row["mcc"] = ""
                row["tnr"] = ""
                row["mcc_defined"] = "0"
            else:
                row["cell"] = cell_mcc_tpr_tnr(m)
        out_rows.append(row)

    for mid, label in MODEL_ORDER:
        for ds in DATASETS:
            m = metrics.get((mid, ds))
            if m is None:
                d = DEFAULTS[ds]
                add(mid, label, ds, "model", None, d["n_total"], "", "", "", "")
                continue
            add(
                mid, label, ds, "model", m,
                m.get("n_total"), m.get("scorable"), m.get("fail"),
                m.get("campaign") or "", m.get("metric_source") or "",
            )
    for ds in DATASETS:
        d = dft[ds]
        add("always-safe", "always-safe", ds, "always-safe", d["safe"],
            d["n_total"], d["scorable"], 0, "", "baseline_from_default_scorable_PN")
        add("always-unsafe", "always-unsafe", ds, "always-unsafe", d["unsafe"],
            d["n_total"], d["scorable"], 0, "", "baseline_from_default_scorable_PN")

    from io import StringIO
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    for row in out_rows:
        w.writerow(row)
    return buf.getvalue()


def render_full_csv(raw_rows, metrics, meta, dft, by_key_source):
    fields = [
        "model", "model_label", "dataset", "campaign", "metric_source",
        "n_total", "scorable", "failed", "P", "N",
        "tp", "fp", "tn", "fn",
        "tpr", "tnr", "fpr", "fnr", "precision", "npv",
        "accuracy", "balanced_acc", "f1", "mcc",
        "detected_rogue_denominator", "eir_k3",
        "mean_signed_intervention_gap", "premature_alerts_on_rogue",
    ]
    from io import StringIO
    buf = StringIO()
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()

    def write_model(mid, label, ds, m, raw):
        row = {k: "" for k in fields}
        row["model"] = mid
        row["model_label"] = label
        row["dataset"] = ds
        if raw:
            row["campaign"] = raw.get("campaign") or ""
            row["metric_source"] = raw.get("metric_source") or ""
            row["detected_rogue_denominator"] = raw.get("detected_rogue_denominator") or ""
        if m is None:
            w.writerow(row)
            return
        row["n_total"] = m.get("n_total") if m.get("n_total") is not None else ""
        row["scorable"] = m.get("scorable") if m.get("scorable") is not None else ""
        row["failed"] = m.get("fail") if m.get("fail") is not None else ""
        row["P"] = m["P"]
        row["N"] = m["N"]
        for k in ("tp", "fp", "tn", "fn", "tpr", "tnr", "fpr", "fnr",
                  "precision", "accuracy", "balanced_acc", "f1", "mcc"):
            row[k] = "" if m[k] is None else m[k]
        # InjecAgent: keep TNR/FPR/BAcc/MCC/NPV blank (undefined / not meaningful)
        if ds == "injecagent":
            for k in ("tnr", "fpr", "npv", "balanced_acc", "mcc"):
                row[k] = ""
        else:
            row["npv"] = "" if m["npv"] is None else m["npv"]
        if ds.startswith("stepshield"):
            row["eir_k3"] = "" if m.get("eir_k3") is None else m["eir_k3"]
            row["mean_signed_intervention_gap"] = "" if m.get("gap") is None else m["gap"]
            row["premature_alerts_on_rogue"] = "" if m.get("premature") is None else m["premature"]
        w.writerow(row)

    for mid, label in MODEL_ORDER:
        for ds in DATASETS:
            raw = by_key_source.get((mid, ds), {})
            write_model(mid, label, ds, metrics.get((mid, ds)), raw)

    for ds in DATASETS:
        d = dft[ds]
        for kind, key in (("always-safe", "safe"), ("always-unsafe", "unsafe")):
            m = dict(d[key])
            m["n_total"] = d["n_total"]
            m["scorable"] = d["scorable"]
            m["fail"] = 0
            m["eir_k3"] = None
            m["gap"] = None
            m["premature"] = None
            raw = {"campaign": "", "metric_source": "baseline_from_default_scorable_PN",
                   "detected_rogue_denominator": ""}
            write_model(kind, kind, ds, m, raw)

    return buf.getvalue()


def patch_rq1_readme(existing: str) -> str:
    """Update file-list bullets and add a short metrics pointer; keep the rest."""
    # Fix leftover form-feed typo if present.
    text = existing.replace("\x0cull-local-wildguard-response-v1", "full-local-wildguard-response-v1")
    text = text.replace("ull-local-wildguard-response-v1", "full-local-wildguard-response-v1")

    # Prepend / adjust the dating sentence at the top, and replace the 汇总表 section.
    header_note = (
        f"MCC 主表重建于 {GENERATED_AT}：`summary/metrics.md` 现以 MCC 与 TPR/TNR 为跨位置主比较，准确率不再作为排名指标；"
        "指标含义见 `summary/README.md`。"
    )

    # Update first paragraph dating if it starts with 整理时间
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        # insert a short update after the title / first paragraph
        pass

    # Replace the 汇总表 section (from '## 汇总表' up to next '## ')
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == "## 汇总表":
            start = i
        elif start is not None and i > start and line.startswith("## "):
            end = i
            break
    new_section = [
        "## 汇总表",
        "",
        "位于 `summary/`，现在是一套统一文件，不再按「非 StepShield / StepShield」分文件名：",
        "",
        "- `summary/README.md` — 表目录、计分说明，以及各指标（MCC、TPR/TNR、准确率、F1、EIR@3、干预差、平凡基线等）的含义",
        "- `summary/metrics.md` / `.csv` — 主表：模型 × 位置的 MCC 与 TPR/TNR（含 always-safe / always-unsafe 与正类比例）；InjecAgent 因全正类、MCC 无定义，作为补充 TPR 表",
        "- `summary/metrics_full.md` / `.csv` — 全指标（准确率作为次要数字保留；含 FPR/FNR/TNR/MCC，以及 StepShield 的 EIR@3、干预差）。StepShield 可计算的 MCC 已补齐",
        "- `summary/time_tokens.md` / `.csv` — 时间与 token（成功样本墙钟、调用延迟、已知输入/输出 token；本次补写了 gpt6luna 的 WildGuard Mode E，其余已填行未改）",
        "- `summary/rebuild_mcc_summary.py` — 从已有混淆矩阵计数重建指标表，不读 `raw/`，不重跑",
        "",
        "2026-11-10 / 2026-11-11 的旧分表已移到 `summary/_archive/20261110-split-by-stepshield/`。根目录的 `rq1_non_stepshield_bundle_20261110.zip` 仍保留，但是过期快照，请以 `summary/` 新表为准。",
        "",
        "空单元格表示该结果还不在本机、尚未完成或尚未正式合并，不是估计值，也不写入进行中数字。现已写入 gpt6luna 的 StepShield、claudehaiku 的 WildGuard Mode E、claudehaiku 的 StepShield（正式合并战役 `full-api-stepshield-claude-merged-v1`），以及 gpt6luna 的 WildGuard Mode E（战役 `full-api-wildguard-response-v1`，官方 analysis `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成）。列入本套正式汇总的官方格子现已全部写入。",
        "",
        "## 主指标（简要）",
        "",
        "正类 = unsafe / 有害。跨位置主比较用 MCC，并同时看 TPR（=Recall）和 TNR（=Specificity）。准确率会被正类比例抬高（例如 StepShield test 正类 8.1% 时，永远判 safe 已有 91.9% 准确率），只留在全指标表里备查。MCC 在分母任一因子为 0 时无定义，记为 —，不能写成 0（InjecAgent 全正类、常数分类器、shieldstral 的 StepShield test 都属于这种情况）。完整定义、平凡基线、可判分母与干预差的含义见 `summary/README.md`。当前数字都是描述性的（1 次 repeat，阈值未经预注册）；MCC 很接近时不要写成确定名次。",
        "",
    ]
    if start is None:
        # append
        if text and not text.endswith("\n"):
            text += "\n"
        text += "\n" + "\n".join(new_section)
    else:
        if end is None:
            end = len(lines)
        lines = lines[:start] + new_section + lines[end:]
        text = "\n".join(lines)
        if not text.endswith("\n"):
            text += "\n"

    # Refresh the opening dating sentence by appending an update clause
    # after the first paragraph, if not already present.
    if "MCC 主表重建于" not in text:
        paras = text.split("\n")
        # Find the first non-title, non-empty line block: line 3 in original is the long paragraph
        for i, line in enumerate(paras):
            if line.startswith("整理时间："):
                # prepend the MCC note at the beginning of this paragraph.
                paras[i] = line.rstrip() + " " + header_note
                break
        else:
            # insert after title
            for i, line in enumerate(paras):
                if line.startswith("# "):
                    paras.insert(i + 2, header_note)
                    break
        text = "\n".join(paras)
        if not text.endswith("\n"):
            text += "\n"

    leftover = [
        (
            "各 50 条/2 条的 pilot、smoke、relay 等开发期小规模记录，以及当时仍在跑的 gpt6luna WildGuard Mode E。",
            "各 50 条/2 条的 pilot、smoke、relay 等开发期小规模记录。",
        ),
        (
            "- 汇总表中的 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1` 的官方 analysis；claudehaiku 的 StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`）。claudehaiku 的 WildGuard Mode E 已写入；gpt6luna 的 Mode E 截至 "
            + SERVER_CHECKED_AT
            + " 仍在跑，正式格子留空。",
            "- 汇总表中的 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1` 的官方 analysis；claudehaiku 的 StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`）。claudehaiku 与 gpt6luna 的 WildGuard Mode E 均已写入（gpt6luna 官方 analysis `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成）。",
        ),
        (
            "- 汇总表中的 gpt6luna StepShield 已改从服务器战役 `full-api-stepshield-server-v1` 的官方 analysis 写入；claudehaiku 的 StepShield 正式格子仍留空（尚未正式合并）。claudehaiku 的 WildGuard Mode E 已写入；gpt6luna 的 Mode E 截至 "
            + SERVER_CHECKED_AT
            + " 仍在跑，正式格子留空。",
            "- 汇总表中的 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1` 的官方 analysis；claudehaiku 的 StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1` 的官方 analysis（`2026-11-13T054230.236392_0000-9f5044`）。claudehaiku 与 gpt6luna 的 WildGuard Mode E 均已写入（gpt6luna 官方 analysis `2026-11-13T061430.606753_0000-9d3a76`，2026-11-13 14:14:30 Asia/Shanghai 完成）。",
        ),
        (
            "各 50 条/2 条的 pilot、smoke、relay 等开发期小规模记录，以及尚未正式合并的 claudehaiku StepShield 与当时仍在跑的 gpt6luna WildGuard Mode E。",
            "各 50 条/2 条的 pilot、smoke、relay 等开发期小规模记录。",
        ),
        (
            "- `stepshield/api/` — 本机 API StepShield 快照目录（战役 `full-api-stepshield-v1`）。汇总表新写入的 gpt6luna StepShield 数字来自服务器战役 `full-api-stepshield-server-v1` 的官方 analysis，不是此目录",
            "- `stepshield/api/` — 本机 API StepShield 快照目录（战役 `full-api-stepshield-v1`）。汇总表中 gpt6luna StepShield 来自服务器战役 `full-api-stepshield-server-v1`；claudehaiku StepShield 来自正式合并战役 `full-api-stepshield-claude-merged-v1`，都不是此目录",
        ),
    ]
    for src, dest in leftover:
        text = text.replace(src, dest)
    return text



OFFICIAL_CELLS = {
    ("gpt6luna", "stepshield_test"): (627, 949, 6347, 12),
    ("gpt6luna", "stepshield_test_holdout"): (107, 44, 64, 1),
    ("gpt6luna", "wildguard_response"): (216, 62, 1362, 68),
    ("claudehaiku", "wildguard_response"): (187, 44, 1332, 91),
    ("claudehaiku", "stepshield_test"): (615, 1868, 5425, 24),
    ("claudehaiku", "stepshield_test_holdout"): (107, 23, 85, 1),
}
MUST_STAY_EMPTY = [
]


def assert_required_cells(metrics):
    problems = []
    for key, cm in OFFICIAL_CELLS.items():
        m = metrics.get(key)
        if m is None:
            problems.append(f"{key[0]} {key[1]} missing")
        elif (m["tp"], m["fp"], m["tn"], m["fn"]) != cm:
            got = (m["tp"], m["fp"], m["tn"], m["fn"])
            problems.append(f"{key[0]} {key[1]} CM {got} != official {cm}")
    for mid, ds in MUST_STAY_EMPTY:
        if metrics.get((mid, ds)) is not None:
            problems.append(f"{mid} {ds} was not empty")
    if problems:
        raise SystemExit("ERROR: " + "; ".join(problems))


def write_verification(path: Path, discrepancies, spearman, metrics, texts, out_dir: Path, edited):
    lines = []
    lines.append("# RQ1 官方格子补齐核对")
    lines.append("")
    lines.append(f"生成于 {GENERATED_AT}。脚本：`rebuild_mcc_summary.py`。")
    lines.append("计数来源：在 2026-11-13 13:46 Asia/Shanghai 的 live `metrics_full.csv` 上填入 gpt6luna WildGuard response（Mode E）的官方 TP/FP/TN/FN，再按同一公式重算 MCC / TPR / TNR。不读 `raw/`，不重跑，不改源战役 analysis 目录。未触碰 vLLM PID 773641。")
    lines.append("")
    lines.append("## 编辑的文件")
    lines.append("")
    for p in edited:
        lines.append(f"- `{p}`")
    lines.append("- `time_tokens.md` / `time_tokens.csv` 由随后步骤在同一输出目录单独补写（只填上述新格子；其余行数字保持不变）。")
    lines.append("")
    lines.append("## StepShield MCC（由混淆矩阵重算，三位小数）")
    lines.append("")
    lines.append("| 模型 | test MCC | test TP/FP/TN/FN | holdout MCC | holdout TP/FP/TN/FN |")
    lines.append("| --- | ---: | --- | ---: | --- |")
    for mid, label in MODEL_ORDER:
        a = metrics.get((mid, "stepshield_test"))
        b = metrics.get((mid, "stepshield_test_holdout"))
        if a is None and b is None:
            lines.append(f"| {label} |  |  |  |  |")
            continue
        def side(m):
            if m is None:
                return "", ""
            return fmt_mcc(m["mcc"]), f"{m['tp']}/{m['fp']}/{m['tn']}/{m['fn']}"
        am, ac = side(a)
        bm, bc = side(b)
        lines.append(f"| {label} | {am} | {ac} | {bm} | {bc} |")
    lines.append("")
    lines.append("无定义（—）：")
    lines.append("")
    lines.append("- 所有 InjecAgent 行的 MCC（全正类，TN=FP=0）")
    lines.append("- shieldstral 的 StepShield test（TP=FP=0，与 always-safe 同类）")
    lines.append("- 各位置 always-safe（TP+FP=0）与 always-unsafe（TN+FN=0）基线的 MCC")
    lines.append("- 列入本套正式汇总的官方格子现已全部写入；不再有空单元格（— 仍表示 MCC 无定义，不是空格）")
    lines.append("- laya 的 StepShield holdout MCC 为 0.000（有定义：分子为 0，分母不为 0），不要写成 —")
    lines.append("- laya 的 StepShield test MCC 为 −0.001")
    lines.append("")
    lines.append("Packy Jev StepShield 的 MCC 与 CSV 中已有官方值一致：test 0.5354442402079949 → 0.535，holdout 0.8469973362226254 → 0.847。")
    lines.append("")
    lines.append("## 与旧全指标表的差异")
    lines.append("")
    display_mismatch = [d for d in discrepancies if d["kind"] == "display_mismatch"]
    now_undef = [d for d in discrepancies if d["kind"] == "now_undefined"]
    filled = [d for d in discrepancies if d["kind"] == "filled_blank"]
    if not display_mismatch and not now_undef:
        lines.append("已有显示值（准确率 / F1 / TPR / TNR / FPR / FNR / Precision，以及非 StepShield 的 MCC，按一位小数或 MCC 三位小数）与从 TP/FP/TN/FN 重算后的显示完全一致，没有改动已公布的读数。")
    else:
        lines.append("发现显示不一致（需人工检查）：")
        for d in display_mismatch + now_undef:
            lines.append(f"- {d['model']} {d['dataset']} {d['field']}: old={d['old_disp']} new={d['new_disp']}")
    lines.append("")
    lines.append("本次有意补上的空白（不算错误）：")
    lines.append("")
    # summarize filled
    ss_mcc = [d for d in filled if d["field"] == "mcc" and "stepshield" in d["dataset"]]
    other = [d for d in filled if d not in ss_mcc]
    lines.append(f"- StepShield 原先在 `metrics_full.csv` 中 MCC 为空、且公式可计算的行：已填 {len(ss_mcc)} 个（本地 9 个模型的 test / holdout，除 shieldstral test 无定义外）。Packy 两行原先已有 MCC，未改显示。")
    if other:
        lines.append(f"- 其它由计数补上的空白派生量（例如部分 StepShield 行原先没有 NPV / Balanced Acc）：{len(other)} 项。这不改变混淆矩阵，也不改变已公布的 acc/F1/TPR/TNR。")
    lines.append("- 主表 `metrics.md` 不再以 acc/F1 为标题指标；acc/F1 仍在 `metrics_full.md`。")
    lines.append("- 删除了旧 `metrics.md` 失败表里一行残缺的 `gpt6luna | 5 | 可判分 1694…`（那是已移除的 WildGuard prompt / Mode A1 残留，本次没有把 Mode A1 加回）。")
    lines.append("- 各全指标表末尾增加 always-safe / always-unsafe 行；`metrics_full.csv` / `metrics.csv` 也写入了这两条基线。")
    lines.append("")
    lines.append("## 新写入的官方格子")
    lines.append("")
    official = [
        ("gpt6luna", "stepshield_test", (627, 949, 6347, 12), 0.8788909892879647, 0.5661399548532732, 0, 7935),
        ("gpt6luna", "stepshield_test_holdout", (107, 44, 64, 1), 0.7916666666666666, 0.8262548262548263, 0, 216),
        ("claudehaiku", "wildguard_response", (187, 44, 1332, 91), 0.9183796856106409, 0.7347740667976425, 55, 1654),
        ("claudehaiku", "stepshield_test", (615, 1868, 5425, 24), 0.7614725163893091, 0.3939782190903267, 3, 7932),
        ("claudehaiku", "stepshield_test_holdout", (107, 23, 85, 1), 0.8888888888888888, 0.8991596638655462, 0, 216),
        ("gpt6luna", "wildguard_response", (216, 62, 1362, 68), 0.9238875878220141, 0.7686832740213523, 1, 1708),
    ]
    lines.append("| 模型 × 数据集 | 单元格 | Acc | F1 | n / fail | 官方 acc / F1 是否与重算显示一致 |")
    lines.append("| --- | ---: | ---: | ---: | --- | --- |")
    for mid, ds, cm, oacc, of1, fail, n in official:
        m = metrics.get((mid, ds))
        ok = m is not None and (m["tp"], m["fp"], m["tn"], m["fn"]) == cm
        acc_ok = ok and fmt_pct(m["accuracy"]) == fmt_pct(oacc)
        f1_ok = ok and fmt_pct(m["f1"]) == fmt_pct(of1)
        cell = cell_mcc_tpr_tnr(m) if m else ""
        lines.append(
            f"| {mid} × {ds} | {cell} | {fmt_pct(m['accuracy']) if m else ''} | {fmt_pct(m['f1']) if m else ''} | {n} / {fail} | acc={'是' if acc_ok else '否'}; F1={'是' if f1_ok else '否'} |"
        )
    lines.append("")
    lines.append("官方 test acc/F1 与由混淆矩阵重算的值完全一致。holdout 的官方 F1=0.8262548262548263 与重算值相差 1 ulp（约 1e-16），一位小数显示同为 82.6%。")
    lines.append("")
    lines.append("## 仍为空的格子")
    lines.append("")
    lines.append("已确认列入本套正式汇总的官方格子均已写入（不是 —，也没有填入进行中数字）：")
    lines.append("")
    lines.append("- （无）gpt6luna × WildGuard response (Mode E) 已写入官方 analysis `2026-11-13T061430.606753_0000-9d3a76`（2026-11-13 14:14:30 Asia/Shanghai 完成；ok=1724，fail=1 PolicyRefusal）")
    lines.append("")
    lines.append("未触碰源战役目录或 vLLM PID 773641。")
    lines.append("")
    lines.append("## Spearman（描述性，仅两边 MCC 都有定义的子集）")
    lines.append("")
    lines.append("| 位置对 | Spearman | n | 子集 |")
    lines.append("| --- | ---: | ---: | --- |")
    labels = {
        "agentharm": "AgentHarm",
        "tsbench": "TS-Bench",
        "wildguard_response": "WildGuard-E",
        "stepshield_test": "StepShield test",
        "stepshield_test_holdout": "StepShield holdout",
    }
    for key, item in spearman.items():
        a, b = key
        names = ", ".join(item["names"])
        lines.append(f"| {labels[a]} ~ {labels[b]} | {item['rho']:.2f} | {item['n']} | {names} |")
    lines.append("")
    lines.append("上表为本次从当前可定义 MCC 子集重新计算的结果，不沿用上一版或批评稿里的旧系数。AgentHarm~TS-Bench 仍为全部 12 个模型。AgentHarm~WildGuard 与 TS-Bench~WildGuard 现含 claudehaiku 与 gpt6luna（n 由此增加）。TS-Bench~StepShield test 与 StepShield test~holdout 现含 gpt6luna 与已正式合并的 claudehaiku，并排除 test 上 MCC 无定义的 shieldstral。n 与系数因可比子集变化而变化，只是描述性观察，不单独构成排名结论，也不宜写成「排名随位置翻转已被证明」。")
    lines.append("")
    lines.append("主表没有加 (1)(2)(3) 名次。正式汇总中没有纳入 WildGuard prompt（Mode A1）。")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing live metrics_full.csv")
    parser.add_argument("--out-dir", type=Path, help="Where to write rebuilt files")
    parser.add_argument("--in-place", action="store_true", help="Write into --input-dir")
    parser.add_argument("--rq1-readme", type=Path, help="Optional path to rq1/README.md to patch")
    parser.add_argument("--verification", type=Path, help="Path for the verification note")
    args = parser.parse_args(argv)

    input_dir = args.input_dir.resolve()
    if args.in_place:
        out_dir = input_dir
    else:
        if not args.out_dir:
            raise SystemExit("--out-dir is required unless --in-place is set")
        out_dir = args.out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    metrics, meta, spearman, discrepancies, payload = build_all(input_dir)
    texts, dft, spearman, discrepancies = payload if isinstance(payload, tuple) else (payload, None, spearman, discrepancies)
    # build_all currently returns texts as last element; handle both
    if isinstance(payload, tuple):
        texts, dft, spearman, discrepancies = payload

    edited = []
    for name in ("metrics.md", "metrics.csv", "metrics_full.md", "metrics_full.csv", "README.md"):
        dest = out_dir / name
        dest.write_text(texts[name], encoding="utf-8")
        edited.append(str(dest))

    if args.rq1_readme:
        src = args.rq1_readme
        existing = src.read_text(encoding="utf-8")
        patched = patch_rq1_readme(existing)
        if args.in_place:
            dest = src
        else:
            dest = out_dir / "rq1_README.md"
        dest.write_text(patched, encoding="utf-8")
        edited.append(str(dest))

    ver_path = args.verification
    if ver_path is None:
        ver_path = out_dir / "mcc_summary_rebuild.md"
    write_verification(ver_path, discrepancies, spearman, metrics, texts, out_dir, edited)

    assert_required_cells(metrics)
    print(f"Wrote {len(edited)} files to {out_dir}")
    print(f"Verification: {ver_path}")


# Fix build_all return to be consistent
def _build_all_fixed(input_dir: Path):
    result = build_all(input_dir)
    metrics, meta, spearman, discrepancies, payload = result
    if isinstance(payload, tuple):
        texts, dft, spearman2, discrepancies2 = payload
        return metrics, meta, spearman2, discrepancies2, texts, dft
    return metrics, meta, spearman, discrepancies, payload, None


if __name__ == "__main__":
    # Rebind main to use the fixed unpack once, inlined here.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--rq1-readme", type=Path)
    parser.add_argument("--verification", type=Path)
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    if args.in_place:
        out_dir = input_dir
    else:
        if not args.out_dir:
            raise SystemExit("--out-dir is required unless --in-place is set")
        out_dir = args.out_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    metrics, meta, spearman, discrepancies, texts, dft = _build_all_fixed(input_dir)
    edited = []
    for name in ("metrics.md", "metrics.csv", "metrics_full.md", "metrics_full.csv", "README.md"):
        dest = out_dir / name
        dest.write_text(texts[name], encoding="utf-8")
        edited.append(str(dest))

    if args.rq1_readme:
        existing = args.rq1_readme.read_text(encoding="utf-8")
        patched = patch_rq1_readme(existing)
        dest = args.rq1_readme if args.in_place else (out_dir / "rq1_README.md")
        dest.write_text(patched, encoding="utf-8")
        edited.append(str(dest))

    ver_path = args.verification or (out_dir / "mcc_summary_rebuild.md")
    write_verification(ver_path, discrepancies, spearman, metrics, texts, out_dir, edited)

    assert_required_cells(metrics)
    print(f"Wrote {len(edited)} files to {out_dir}")
    print(f"Verification: {ver_path}")
