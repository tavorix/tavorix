"""Turn a labeled address list into a features CSV, so accuracy can be measured.

Input CSV needs columns: token_address, label (rugpull|honeypot|scam_other|healthy).
Usage: python collect.py dataset_template.csv features.csv --rpc $env:RPC
Then:  python evaluate.py features.csv --threshold 40
"""
import argparse
import csv
import time
from tavorix_scanner import dexscreener, goplus
from tavorix_scanner.data import fetch_token_data
from tavorix_scanner.models import FEATURE_NAMES
from tavorix_scanner.rpc import RpcClient

VALID_LABELS = {"rugpull", "honeypot", "scam_other", "healthy"}


def collect(rows, rpc: RpcClient, delay: float = 0.5, log=print, dex_fetch=None, goplus_fetch=None) -> list:
    out = []
    for row in rows:
        addr = (row.get("token_address") or row.get("address") or "").strip()
        label = (row.get("label") or "").strip().lower()
        if not addr or label not in VALID_LABELS:
            continue
        try:
            if int(addr, 16) == 0:
                continue  # skip the template's example row
            addr = addr.lower()
            data = fetch_token_data(addr, rpc, dex_fetch=dex_fetch, goplus_fetch=goplus_fetch)
        except Exception as exc:  # keep going; report the problem
            log(f"skip {addr}: {exc}")
            continue
        rec = {"label": label, "address": addr}
        for name in FEATURE_NAMES:
            value = getattr(data, name)
            rec[name] = "" if value is None else value
        out.append(rec)
        time.sleep(delay)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset_csv")
    ap.add_argument("features_csv")
    ap.add_argument("--rpc", required=True)
    a = ap.parse_args()
    with open(a.dataset_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    recs = collect(rows, RpcClient(a.rpc), dex_fetch=dexscreener.fetch_pairs, goplus_fetch=goplus.fetch)
    with open(a.features_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "address"] + FEATURE_NAMES)
        w.writeheader()
        w.writerows(recs)
    print(f"Wrote {len(recs)} of {len(rows)} rows to {a.features_csv}")


if __name__ == "__main__":
    main()
