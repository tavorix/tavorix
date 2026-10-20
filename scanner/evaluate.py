"""Measure scanner accuracy on a labeled CSV.

CSV columns: label (rugpull|honeypot|scam_other|healthy), address, plus any TokenData fields.
Usage: python evaluate.py features.csv --threshold 40
Scam = positive class. Report on the HELD-OUT test split only; tune thresholds/weights on train split.
"""
import argparse
import csv
from typing import Optional
from tavorix_scanner import TokenData, score_token
from tavorix_scanner.models import FEATURE_NAMES

SCAM_LABELS = {"rugpull", "honeypot", "scam_other"}
BOOL_FIELDS = {"has_mint", "has_blacklist", "has_pause", "tax_mutable", "honeypot_sell_failed",
               "source_verified", "owner_renounced", "is_proxy"}
INT_FIELDS = {"deployer_scam_links"}


def _parse(name: str, raw: str):
    raw = (raw or "").strip()
    if raw == "":
        return None
    if name in BOOL_FIELDS:
        return raw.lower() in ("1", "true", "yes", "y")
    if name in INT_FIELDS:
        return int(float(raw))
    return float(raw)


def row_to_token(row: dict) -> TokenData:
    kwargs = {n: _parse(n, row.get(n, "")) for n in FEATURE_NAMES}
    return TokenData(address=row.get("address", ""), **kwargs)


def metrics(tp: int, fp: int, tn: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return {"precision": precision, "recall": recall, "false_positive_rate": fpr,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def evaluate(rows, threshold: int) -> dict:
    tp = fp = tn = fn = 0
    for row in rows:
        is_scam = row["label"].strip().lower() in SCAM_LABELS
        flagged = score_token(row_to_token(row)).score >= threshold
        if is_scam and flagged: tp += 1
        elif is_scam: fn += 1
        elif flagged: fp += 1
        else: tn += 1
    return metrics(tp, fp, tn, fn)


def main(argv: Optional[list] = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--threshold", type=int, default=40)
    args = ap.parse_args(argv)
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    m = evaluate(rows, args.threshold)
    print(f"threshold={args.threshold} n={len(rows)}")
    for k, v in m.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
