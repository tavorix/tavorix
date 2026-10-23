"""Collect on-chain facts for a BEP-20 token using plain JSON-RPC (needs a BSC RPC URL).

What this version CAN fill: mint/blacklist/pause/proxy hints (bytecode selector scan),
owner_renounced, owner type, LP locked percentage (dead + configured lockers), estimated USD liquidity of the biggest WBNB or USDT PancakeSwap v2 pool.
Optional (dex_fetch=DexScreener): liquidity across ALL DEX pools and trading age (oldest pool, used as a proxy for age).
What it CANNOT fill yet (stays None = unknown): honeypot simulation, taxes, holder concentration,
source verification, deployer history. These need an indexer/explorer API or a local
fork simulation, and are the next steps.
"""
from typing import Optional
from . import config
from .models import TokenData
from .rpc import RpcClient, pad_address, decode_address, decode_uint
from .dexscreener import summarize
from . import goplus as goplus_mod


def scan_selectors(bytecode_hex: str, selectors: list) -> bool:
    """True if the dispatcher pushes any selector (PUSH4 = 0x63 followed by the 4 bytes)."""
    code = bytecode_hex.lower().replace("0x", "")
    return any(("63" + s) in code for s in selectors)


def has_code(bytecode_hex: str) -> bool:
    return bytecode_hex not in ("0x", "0x0", "", None)


def _owner_info(rpc: RpcClient, token: str):
    """Return (owner_renounced, owner_is_contract); (None, None) if owner() is unavailable."""
    owner = decode_address(rpc.eth_call(token, "0x8da5cb5b"))  # owner()
    if owner is None:
        return None, None
    if owner.lower() in config.DEAD_ADDRESSES:
        return True, False
    return False, has_code(rpc.get_code(owner))


def _pair_for(rpc: RpcClient, token_a: str, token_b: str) -> Optional[str]:
    data = "0xe6a43905" + pad_address(token_a) + pad_address(token_b)  # getPair(a, b)
    pair = decode_address(rpc.eth_call(config.PANCAKE_V2_FACTORY, data))
    if not pair or int(pair, 16) == 0:
        return None
    return pair


def _pool_info(rpc: RpcClient, pair: str):
    """Return (token0, reserve0, reserve1) or None."""
    token0 = decode_address(rpc.eth_call(pair, "0x0dfe1681"))  # token0()
    res = rpc.eth_call(pair, "0x0902f1ac")                     # getReserves()
    if not token0 or not res or len(res) < 130:
        return None
    return token0.lower(), int(res[2:66], 16), int(res[66:130], 16)


def _bnb_price_usd(rpc: RpcClient) -> Optional[float]:
    pair = _pair_for(rpc, config.WBNB, config.USDT)
    info = _pool_info(rpc, pair) if pair else None
    if not info:
        return None
    token0, r0, r1 = info
    if r0 == 0 or r1 == 0:
        return None
    return (r1 / r0) if token0 == config.WBNB.lower() else (r0 / r1)  # both 18 decimals on BSC


def _main_pool(rpc: RpcClient, token: str):
    """Return (pair, estimated_usd_value) for the biggest token/WBNB or token/USDT pool, else (None, None)."""
    bnb_price = _bnb_price_usd(rpc)
    best_pair, best_value = None, None
    for quote in (config.WBNB, config.USDT):
        if quote == config.WBNB and bnb_price is None:
            continue
        pair = _pair_for(rpc, token, quote)
        info = _pool_info(rpc, pair) if pair else None
        if not info:
            continue
        token0, r0, r1 = info
        quote_reserve = r0 if token0 == quote.lower() else r1
        quote_amount = quote_reserve / 1e18
        value = 2 * quote_amount * (bnb_price if quote == config.WBNB else 1.0)
        if best_value is None or value > best_value:
            best_pair, best_value = pair, value
    return best_pair, best_value


def _lp_locked_pct(rpc: RpcClient, pair: str) -> Optional[float]:
    total = decode_uint(rpc.eth_call(pair, "0x18160ddd"))  # LP totalSupply
    if not total:
        return None
    safe = {a.lower() for a in config.DEAD_ADDRESSES | config.LP_LOCKER_ADDRESSES}
    locked = 0
    for holder in safe:
        bal = decode_uint(rpc.eth_call(pair, "0x70a08231" + pad_address(holder)))  # balanceOf
        locked += bal or 0
    return 100.0 * locked / total


def fetch_token_data(address: str, rpc: RpcClient, dex_fetch=None, goplus_fetch=None) -> TokenData:
    code = rpc.get_code(address)
    if not has_code(code):
        raise ValueError("No contract code at this address on this chain.")
    d = TokenData(address=address)
    d.has_mint = scan_selectors(code, config.SELECTORS["mint"])
    d.has_blacklist = scan_selectors(code, config.SELECTORS["blacklist"])
    d.has_pause = scan_selectors(code, config.SELECTORS["pause"])
    slot = rpc.get_storage(address, config.EIP1967_IMPL_SLOT)
    d.is_proxy = (int(slot, 16) != 0) or scan_selectors(code, config.SELECTORS["proxy"])
    d.owner_renounced, d.owner_is_contract = _owner_info(rpc, address)
    pair, value = _main_pool(rpc, address)
    if pair:
        d.lp_locked_pct = _lp_locked_pct(rpc, pair)
        d.liquidity_usd = value
    if dex_fetch is not None:  # optional: liquidity across ALL DEX pools and trading age (DexScreener)
        try:
            info = summarize(dex_fetch(address), address)
        except Exception:
            info = None
        if info:
            d.liquidity_usd = info["liquidity_usd"]
            if info["age_days"] is not None:
                d.contract_age_days = info["age_days"]  # proxy: age of the oldest trading pool
    if goplus_fetch is not None:  # optional: honeypot/tax/holders from GoPlus (third-party data, overrides when present)
        try:
            info = goplus_fetch(address)
        except Exception:
            info = None
        if info:
            for key, value in goplus_mod.to_features(info).items():
                setattr(d, key, value)
    return d
