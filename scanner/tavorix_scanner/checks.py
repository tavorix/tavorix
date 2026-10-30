"""Individual checks. Weights are initial heuristics and MUST be tuned on the
training split of the labeled dataset, then validated on a held-out test split."""
from typing import Callable, List
from .models import TokenData, CheckResult

TAX_HIGH_PCT = 10.0
TOP_HOLDER_PCT = 30.0
TOP10_PCT = 70.0
LP_LOCKED_MIN_PCT = 50.0
LP_UNLOCK_SOON_DAYS = 30.0
NEW_CONTRACT_DAYS = 7.0
LOW_LIQUIDITY_USD = 5000.0
ESTABLISHED_AGE_DAYS = 180.0
ESTABLISHED_LIQUIDITY_USD = 100_000.0


def _unknown(name: str, weight: int) -> CheckResult:
    return CheckResult(name, False, weight, f"{name}: data not available", known=False)


def honeypot(d: TokenData) -> CheckResult:
    if d.honeypot_sell_failed is None:
        return _unknown("honeypot_simulation", 60)
    return CheckResult("honeypot_simulation", d.honeypot_sell_failed, 60,
                       "Selling this token failed or lost most value in simulation (possible honeypot).")


def impersonation(d: TokenData) -> CheckResult:
    if d.impersonates_known_token is None:
        return _unknown("impersonation", 50)
    who = d.impersonated_symbol or "a well-known token"
    return CheckResult("impersonation", d.impersonates_known_token, 50,
                       f"This token uses the name or symbol of {who} but is not the official contract.")


def hidden_mint(d: TokenData) -> CheckResult:
    if d.has_mint is None:
        return _unknown("mint_function", 25)
    return CheckResult("mint_function", d.has_mint, 25,
                       "The contract can create new tokens, which can dilute holders.")


def blacklist(d: TokenData) -> CheckResult:
    if d.has_blacklist is None:
        return _unknown("blacklist_function", 15)
    return CheckResult("blacklist_function", d.has_blacklist, 15,
                       "The owner can block specific wallets from trading.")


def pause(d: TokenData) -> CheckResult:
    if d.has_pause is None:
        return _unknown("pause_function", 10)
    return CheckResult("pause_function", d.has_pause, 10,
                       "Trading or transfers can be paused by the owner.")


def high_tax(d: TokenData) -> CheckResult:
    if d.buy_tax_pct is None and d.sell_tax_pct is None:
        return _unknown("high_tax", 20)
    worst = max(x for x in (d.buy_tax_pct, d.sell_tax_pct) if x is not None)
    return CheckResult("high_tax", worst > TAX_HIGH_PCT, 20,
                       f"Buy/sell tax is high ({worst:.1f}%).")


def mutable_tax(d: TokenData) -> CheckResult:
    if d.tax_mutable is None:
        return _unknown("mutable_tax", 15)
    return CheckResult("mutable_tax", d.tax_mutable, 15,
                       "The owner can change the tax after you buy.")


def top_holder(d: TokenData) -> CheckResult:
    if d.top_holder_pct is None:
        return _unknown("top_holder", 15)
    return CheckResult("top_holder", d.top_holder_pct > TOP_HOLDER_PCT, 15,
                       f"One wallet holds {d.top_holder_pct:.1f}% of supply. It may be a treasury or vesting wallet; check who owns it.")


def top10(d: TokenData) -> CheckResult:
    if d.top10_pct is None:
        return _unknown("top10_concentration", 15)
    return CheckResult("top10_concentration", d.top10_pct > TOP10_PCT, 15,
                       f"The top 10 wallets hold {d.top10_pct:.1f}% of supply.")


def is_established(d: TokenData) -> bool:
    """Heuristic (to be validated on labeled data): old AND deep liquidity makes a rugpull less likely."""
    return (d.contract_age_days is not None and d.liquidity_usd is not None
            and d.contract_age_days >= ESTABLISHED_AGE_DAYS and d.liquidity_usd >= ESTABLISHED_LIQUIDITY_USD)


def lp_unlocked(d: TokenData) -> CheckResult:
    if d.lp_locked_pct is None:
        return _unknown("lp_not_locked", 25)
    weight = 5 if is_established(d) else 25
    return CheckResult("lp_not_locked", d.lp_locked_pct < LP_LOCKED_MIN_PCT, weight,
                       f"Only {d.lp_locked_pct:.0f}% of liquidity is locked, so it could be withdrawn.")


def lp_unlock_soon(d: TokenData) -> CheckResult:
    if d.lp_unlock_days is None:
        return _unknown("lp_unlock_soon", 15)
    return CheckResult("lp_unlock_soon", d.lp_unlock_days < LP_UNLOCK_SOON_DAYS, 15,
                       f"Liquidity unlocks in {d.lp_unlock_days:.0f} days.")


def new_contract(d: TokenData) -> CheckResult:
    if d.contract_age_days is None:
        return _unknown("new_contract", 10)
    return CheckResult("new_contract", d.contract_age_days < NEW_CONTRACT_DAYS, 10,
                       f"The token has only been trading for {d.contract_age_days:.0f} days.")


def unverified_source(d: TokenData) -> CheckResult:
    if d.source_verified is None:
        return _unknown("unverified_source", 15)
    return CheckResult("unverified_source", not d.source_verified, 15,
                       "Source code is not verified, so behavior cannot be audited.")


def owner_active(d: TokenData) -> CheckResult:
    if d.owner_renounced is None:
        return _unknown("owner_not_renounced", 5)
    return CheckResult("owner_not_renounced", not d.owner_renounced, 5,
                       "The owner still holds control over the contract.")


def upgradeable(d: TokenData) -> CheckResult:
    if d.is_proxy is None:
        return _unknown("upgradeable_proxy", 15)
    return CheckResult("upgradeable_proxy", d.is_proxy, 15,
                       "The contract logic can be changed after launch.")


def deployer_history(d: TokenData) -> CheckResult:
    if d.deployer_scam_links is None:
        return _unknown("deployer_history", 30)
    return CheckResult("deployer_history", d.deployer_scam_links >= 1, 30,
                       f"The deployer is linked to {d.deployer_scam_links} earlier flagged token(s) in third-party data (GoPlus). Shared deployers can cause false links.")


def owner_is_wallet(d: TokenData) -> CheckResult:
    if d.owner_renounced is None or d.owner_is_contract is None:
        return _unknown("owner_is_wallet", 15)
    return CheckResult("owner_is_wallet", (not d.owner_renounced) and (not d.owner_is_contract), 15,
                       "The owner is a single wallet, so one person controls the contract.")


def low_liquidity(d: TokenData) -> CheckResult:
    if d.liquidity_usd is None:
        return _unknown("low_liquidity", 20)
    return CheckResult("low_liquidity", d.liquidity_usd < LOW_LIQUIDITY_USD, 20,
                       f"Only about ${d.liquidity_usd:,.0f} of liquidity in the main pool, so the price is easy to move.")


ALL_CHECKS: List[Callable[[TokenData], CheckResult]] = [
    honeypot, impersonation, hidden_mint, blacklist, pause, high_tax, mutable_tax, top_holder, top10,
    lp_unlocked, lp_unlock_soon, new_contract, unverified_source, owner_active,
    upgradeable, deployer_history, owner_is_wallet, low_liquidity,
]
