"""GoPlus Security public API (free, no key per its public docs; rate limits are not documented).
GET https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses=0x...
GoPlus does its own honeypot/tax simulation and holder analysis, which fills most of our 'unknown' checks.
Treat it as a third-party DATA SOURCE: results can be wrong or missing, so keep verifying against labeled data."""
import json
import time
import urllib.error
import urllib.request
from typing import Optional
from . import config

BASE = "https://api.gopluslabs.io/api/v1/token_security/56"


def fetch(address: str, timeout: int = 20, retries: int = 3) -> Optional[dict]:
    addr = address.lower()
    url = f"{BASE}?contract_addresses={addr}"
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tavorix-scanner/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode())
            result = body.get("result") or {}
            return result.get(addr) or (next(iter(result.values())) if result else None)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


def _flag(value) -> Optional[bool]:
    if value in ("1", 1, True):
        return True
    if value in ("0", 0, False):
        return False
    return None


def _pct(value) -> Optional[float]:
    try:
        return float(value) * 100.0  # GoPlus gives fractions as strings, e.g. "0.05" = 5%
    except (TypeError, ValueError):
        return None


def to_features(info: dict) -> dict:
    """Map a GoPlus token_security record to TokenData fields. Unknown values are omitted."""
    out = {}

    def put(key, value):
        if value is not None:
            out[key] = value

    put("honeypot_sell_failed", _flag(info.get("is_honeypot")))
    put("buy_tax_pct", _pct(info.get("buy_tax")))
    put("sell_tax_pct", _pct(info.get("sell_tax")))
    mod = [_flag(info.get("slippage_modifiable")), _flag(info.get("personal_slippage_modifiable"))]
    if any(m is not None for m in mod):
        out["tax_mutable"] = any(m is True for m in mod)
    put("source_verified", _flag(info.get("is_open_source")))
    put("has_mint", _flag(info.get("is_mintable")))
    put("has_blacklist", _flag(info.get("is_blacklisted")))
    put("has_pause", _flag(info.get("transfer_pausable")))
    put("is_proxy", _flag(info.get("is_proxy")))
    same = _flag(info.get("honeypot_with_same_creator"))
    if same is not None:
        out["deployer_scam_links"] = 1 if same else 0

    dead = {a.lower() for a in config.DEAD_ADDRESSES}
    holders = info.get("holders") or []
    people = [h for h in holders
              if (h.get("address") or "").lower() not in dead and str(h.get("is_contract")) != "1"]
    pcts = sorted([p for p in (_pct(h.get("percent")) for h in people) if p is not None], reverse=True)
    if pcts:
        out["top_holder_pct"] = pcts[0]
        out["top10_pct"] = sum(pcts[:10])

    lp = info.get("lp_holders") or []
    if lp:
        locked = 0.0
        for h in lp:
            p = _pct(h.get("percent")) or 0.0
            if str(h.get("is_locked")) == "1" or (h.get("address") or "").lower() in dead:
                locked += p
        out["lp_locked_pct"] = min(100.0, locked)
    return out


def in_dex(info: Optional[dict]) -> Optional[bool]:
    """True/False if GoPlus says the token trades on a DEX, None if it does not say."""
    return _flag((info or {}).get("is_in_dex"))
