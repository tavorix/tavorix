from .checks import ALL_CHECKS
from .models import TokenData, Report

# Powers that give someone control (centralization risk). Many legitimate tokens have these,
# so they are reported separately from scam signals.
CONTROL_NAMES = {"mint_function", "blacklist_function", "pause_function",
                 "owner_not_renounced", "owner_is_wallet", "upgradeable_proxy"}

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
