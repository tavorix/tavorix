from .checks import ALL_CHECKS
from .models import TokenData, Report

# Powers that give someone control (centralization risk). Many legitimate tokens have these,
# so they are reported separately from scam signals.
CONTROL_NAMES = {"mint_function", "blacklist_function", "pause_function",
                 "owner_not_renounced", "owner_is_wallet", "upgradeable_proxy"}

CHECK_LABELS = {
    "honeypot_simulation": "Honeypot (sell) test", "mint_function": "Can mint new tokens",
    "blacklist_function": "Can blacklist wallets", "pause_function": "Can pause transfers",
    "high_tax": "High buy/sell tax", "mutable_tax": "Tax can be changed",
    "top_holder": "Single large holder", "top10_concentration": "Top-10 holder concentration",
    "lp_not_locked": "Liquidity not locked", "lp_unlock_soon": "Liquidity unlocks soon",
    "new_contract": "Recently launched", "unverified_source": "Source code not verified",
    "owner_not_renounced": "Owner not renounced", "upgradeable_proxy": "Upgradeable contract",
    "deployer_history": "Deployer linked to scams", "owner_is_wallet": "Owner is a single wallet",
    "low_liquidity": "Thin liquidity", "impersonation": "Impersonates a known token",
}

LOW_MAX = 29
MEDIUM_MAX = 59
CONTROL_LOW_MAX = 14
CONTROL_MEDIUM_MAX = 39


def level_for(score: int) -> str:
    if score <= LOW_MAX:
        return "low"
    if score <= MEDIUM_MAX:
        return "medium"
    return "high"


def control_level_for(score: int) -> str:
    if score <= CONTROL_LOW_MAX:
        return "low"
    if score <= CONTROL_MEDIUM_MAX:
        return "medium"
    return "high"


def score_token(data: TokenData) -> Report:
    """Return risk estimates (0-100). `score` is the SCAM-risk score; `control_score` is separate.
    These are estimates, NOT a guarantee of safety."""
    results = [check(data) for check in ALL_CHECKS]
    scam = min(100, sum(r.weight for r in results if r.triggered and r.name not in CONTROL_NAMES))
    control = min(100, sum(r.weight for r in results if r.triggered and r.name in CONTROL_NAMES))
    unknown = sum(1 for r in results if not r.known)
    low_conf = unknown * 2 > len(results)
    return Report(data.address, scam, level_for(scam), results, unknown, low_conf,
                  control, control_level_for(control))


def check_matrix(report) -> list:
    """One row per check: flagged, clear, or no_data (we could not read the data)."""
    rows = []
    for r in report.results:
        status = "no_data" if not r.known else ("flagged" if r.triggered else "clear")
        rows.append({
            "id": r.name, "label": CHECK_LABELS.get(r.name, r.name),
            "category": "control" if r.name in CONTROL_NAMES else "scam",
            "status": status, "weight": r.weight, "detail": r.reason if r.triggered else "",
        })
    return rows


def coverage_pct(report) -> int:
    total = len(report.results)
    return round(100 * (total - report.unknown_checks) / total) if total else 0
