"""Tavorix token-check demo: a tiny local web server around the scanner (standard library only).

Run from the scanner folder:   python demo/server.py
Then open:                     http://127.0.0.1:8000
Optional: set TAVORIX_RPC to your own BNB Chain RPC URL (keep it private). Default is the public endpoint.
By default the server listens on 127.0.0.1 only (your computer), never on the network.
On a hosting platform that sets PORT, the server listens publicly and trusts its proxy automatically (or set TAVORIX_HOST=0.0.0.0). Public use is rate limited:
TAVORIX_PER_IP_PER_MIN (default 6 scans per minute per visitor) and TAVORIX_GLOBAL_PER_MIN (default 60).
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from tavorix_scanner import dexscreener, goplus, score_token  # noqa: E402
from tavorix_scanner.scoring import check_matrix, coverage_pct  # noqa: E402
from tavorix_scanner.data import fetch_token_data  # noqa: E402
from tavorix_scanner.rpc import RpcClient  # noqa: E402

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
RPC_URL = os.environ.get("TAVORIX_RPC", "https://bsc-dataseed.bnbchain.org")
CACHE_SECONDS = 60
CACHE_MAX = 500
PER_IP_PER_MIN = int(os.environ.get("TAVORIX_PER_IP_PER_MIN", "6"))
GLOBAL_PER_MIN = int(os.environ.get("TAVORIX_GLOBAL_PER_MIN", "60"))
HOSTED = "PORT" in os.environ  # hosting platforms set PORT; then listen publicly and trust their proxy
TRUST_PROXY = os.environ.get("TAVORIX_TRUST_PROXY", "1" if HOSTED else "") == "1"
_cache = {}
_hits = {}          # visitor key -> list of recent scan timestamps
_all_hits = []      # recent scan timestamps, all visitors
_lock = threading.Lock()


def allow_request(visitor: str, now: float = None) -> int:
    """Return 0 if the scan is allowed, else the number of seconds to wait. Counts scans per visitor and overall."""
    now = time.time() if now is None else now
    with _lock:
        _all_hits[:] = [t for t in _all_hits if now - t < 60]
        mine = [t for t in _hits.get(visitor, []) if now - t < 60]
        if len(_all_hits) >= GLOBAL_PER_MIN:
            _hits[visitor] = mine
            return max(1, int(60 - (now - _all_hits[0])) + 1)
        if len(mine) >= PER_IP_PER_MIN:
            _hits[visitor] = mine
            return max(1, int(60 - (now - mine[0])) + 1)
        mine.append(now)
        _all_hits.append(now)
        _hits[visitor] = mine
        if len(_hits) > 5000:  # keep memory bounded
            for k in [k for k, v in _hits.items() if not v or now - v[-1] >= 60]:
                del _hits[k]
        return 0


def report_to_json(report, data, sources=None) -> dict:
    return {
        "meta": {
            "network": "BNB Smart Chain (chain id 56)", "sources_used": sources or [],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "tool": "Tavorix Token Check demo (unvalidated estimates)",
        },
        "evidence_coverage_pct": coverage_pct(report), "checks": check_matrix(report),
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
    trace = []
    data = fetch_token_data(address, RpcClient(RPC_URL), dex_fetch=dexscreener.fetch_pairs,
                            goplus_fetch=goplus.fetch, trace=trace)
    result = report_to_json(score_token(data), data, trace)
    with _lock:
        if len(_cache) >= CACHE_MAX:
            _cache.clear()
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

    def _visitor(self) -> str:
        if TRUST_PROXY:
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[-1].strip()  # last entry is the one our own proxy added
        return self.client_address[0]

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/healthz":
            self._json(200, {"ok": True})
        elif url.path in ("/", "/index.html"):
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif url.path == "/api/scan":
            address = (parse_qs(url.query).get("address") or [""])[0].strip()
            if not ADDRESS_RE.match(address):
                return self._json(400, {"error": "Enter a valid address: 0x followed by 40 hex characters."})
            wait = allow_request(self._visitor())
            if wait:
                body = json.dumps({"error": f"Too many checks right now. Please wait {wait} seconds and try again."}).encode()
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Retry-After", str(wait))
                self.end_headers()
                self.wfile.write(body)
                return
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


def make_server(port: int = 8000, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    ap.add_argument("--host", default=os.environ.get("TAVORIX_HOST", "0.0.0.0" if HOSTED else "127.0.0.1"))
    args = ap.parse_args()
    server = make_server(args.port, args.host)
    print(f"Tavorix demo running at http://{args.host}:{args.port}  (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
