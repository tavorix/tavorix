"""Tavorix token-check demo: a tiny local web server around the scanner (standard library only).

Run from the scanner folder:   python demo/server.py
Then open:                     http://127.0.0.1:8000
Optional: set TAVORIX_RPC to your own BNB Chain RPC URL (keep it private). Default is the public endpoint.
The server listens on 127.0.0.1 only (your computer), never on the network.
"""
import argparse
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from tavorix_scanner import dexscreener, goplus, score_token  # noqa: E402
from tavorix_scanner.data import fetch_token_data  # noqa: E402
from tavorix_scanner.rpc import RpcClient  # noqa: E402

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
RPC_URL = os.environ.get("TAVORIX_RPC", "https://bsc-dataseed.bnbchain.org")
CACHE_SECONDS = 60
_cache = {}


def report_to_json(report, data) -> dict:
    return {
        "address": report.address,
        "scam_score": report.score, "scam_level": report.level,
        "control_score": report.control_score, "control_level": report.control_level,
        "scam_reasons": report.explain_scam(), "control_reasons": report.explain_control(),
        "unknown_checks": report.unknown_checks, "total_checks": len(report.results),
        "low_confidence": report.low_confidence,
        "facts": {
            "liquidity_usd": data.liquidity_usd, "trading_age_days": data.contract_age_days,
            "top_holder_pct": data.top_holder_pct, "buy_tax_pct": data.buy_tax_pct,
            "sell_tax_pct": data.sell_tax_pct, "lp_locked_pct": data.lp_locked_pct,
        },
    }


def scan(address: str) -> dict:
    key = address.lower()
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    data = fetch_token_data(address, RpcClient(RPC_URL),
                            dex_fetch=dexscreener.fetch_pairs, goplus_fetch=goplus.fetch)
    result = report_to_json(score_token(data), data)
    _cache[key] = (time.time(), result)
    return result


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif url.path == "/api/scan":
            address = (parse_qs(url.query).get("address") or [""])[0].strip()
            if not ADDRESS_RE.match(address):
                return self._json(400, {"error": "Enter a valid address: 0x followed by 40 hex characters."})
            try:
                self._json(200, scan(address))
            except ValueError as exc:
                self._json(404, {"error": str(exc)})
            except Exception:
                self._json(502, {"error": "Could not read data for this address right now. Try again in a moment."})
        else:
            self._json(404, {"error": "Not found"})

    def log_message(self, fmt, *args) -> None:  # keep the console quiet and never print query strings
        pass


def make_server(port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    server = make_server(args.port)
    print(f"Tavorix demo running at http://127.0.0.1:{args.port}  (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
