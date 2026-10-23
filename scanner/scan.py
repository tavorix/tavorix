"""Usage: python scan.py 0xTOKEN --rpc https://YOUR_BSC_RPC_URL"""
import argparse
from tavorix_scanner import score_token
from tavorix_scanner import dexscreener, goplus
from tavorix_scanner.data import fetch_token_data
from tavorix_scanner.rpc import RpcClient


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("--rpc", required=True, help="BNB Smart Chain JSON-RPC URL (keep it private)")
    a = ap.parse_args()
    report = score_token(fetch_token_data(a.address, RpcClient(a.rpc), dex_fetch=dexscreener.fetch_pairs, goplus_fetch=goplus.fetch))
    print(f"Scam-risk score: {report.score}/100 ({report.level})")
    for line in report.explain_scam():
        print("  -", line)
    print(f"Centralization (control) score: {report.control_score}/100 ({report.control_level})")
    for line in report.explain_control():
        print("  -", line)
    print(f"Checks with unknown data: {report.unknown_checks} of {len(report.results)}")
    if report.low_confidence:
        print("LOW CONFIDENCE: most checks had no data, so this score may UNDERSTATE the real risk. Do not read it as safe.")
    print("This is a risk estimate, not a guarantee of safety.")


if __name__ == "__main__":
    main()
