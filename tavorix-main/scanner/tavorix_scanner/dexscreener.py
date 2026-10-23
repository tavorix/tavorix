"""DexScreener public API (no key): liquidity across ALL DEX pools and trading age for a BSC token.
Docs: GET https://api.dexscreener.com/latest/dex/tokens/{address}  (published limit ~300 requests/min)."""
import json
import time
import urllib.request
from typing import Optional

URL = "https://api.dexscreener.com/latest/dex/tokens/{}"
MS_PER_DAY = 86_400_000


def fetch_pairs(address: str, timeout: int = 15) -> list:
    req = urllib.request.Request(URL.format(address), headers={"User-Agent": "tavorix-scanner/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode()).get("pairs") or []


def summarize(pairs: list, address: str, now_ms: Optional[float] = None) -> Optional[dict]:
    """Aggregate BSC pools that contain the token. Returns None if there are none."""
    addr = address.lower()
    bsc = []
    for p in pairs or []:
        if p.get("chainId") != "bsc":
            continue
        base = ((p.get("baseToken") or {}).get("address") or "").lower()
        quote = ((p.get("quoteToken") or {}).get("address") or "").lower()
        if addr in (base, quote):
            bsc.append(p)
    if not bsc:
        return None
    liquidity = sum(float((p.get("liquidity") or {}).get("usd") or 0) for p in bsc)
    volume = sum(float((p.get("volume") or {}).get("h24") or 0) for p in bsc)
    created = [p["pairCreatedAt"] for p in bsc if p.get("pairCreatedAt")]
    age_days = None
    if created:
        now_ms = now_ms if now_ms is not None else time.time() * 1000
        age_days = (now_ms - min(created)) / MS_PER_DAY
    return {"liquidity_usd": liquidity, "age_days": age_days, "volume_24h_usd": volume, "pairs": len(bsc)}
