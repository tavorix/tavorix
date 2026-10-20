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


def _unknown(name: str, weight: int) -> CheckResult:
    return CheckResult(name, False, weight, f"{name}: data not available", known=False)


def honeypot(d: TokenData) -> CheckResult:
    if d.honeypot_sell_failed is None:
        return _unknown("honeypot_simulation", 60)
    return CheckResult("honeypot_simulation", d.honeypot_sell_failed, 60,
                       "Selling this token failed or lost most value in simulation (possible honeypot).")


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
                       f"One wallet holds {d.top_holder_pct:.1f}% of supply.")


def top10(d: TokenData) -> CheckResult:
    if d.top10_pct is None:
        return _unknown("top10_concentration", 15)
    return CheckResult("top10_concentration", d.top10_pct > TOP10_PCT, 15,
                       f"The top 10 wallets hold {d.top10_pct:.1f}% of supply.")


def lp_unlocked(d: TokenData) -> CheckResult:
    if d.lp_locked_pct is None:
        return _unknown("lp_not_locked", 25)
    return CheckResult("lp_not_locked", d.lp_locked_pct < LP_LOCKED_MIN_PCT, 25,
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
                       f"The contract is only {d.contract_age_days:.0f} days old.")


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
                       f"The deployer is linked to {d.deployer_scam_links} earlier flagged token(s).")


ALL_CHECKS: List[Callable[[TokenData], CheckResult]] = [
    honeypot, hidden_mint, blacklist, pause, high_tax, mutable_tax, top_holder, top10,
    lp_unlocked, lp_unlock_soon, new_contract, unverified_source, owner_active,
    upgradeable, deployer_history,
]
