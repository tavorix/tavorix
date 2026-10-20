from .checks import ALL_CHECKS
from .models import TokenData, Report

LOW_MAX = 29
MEDIUM_MAX = 59


def level_for(score: int) -> str:
    if score <= LOW_MAX:
        return "low"
    if score <= MEDIUM_MAX:
        return "medium"
    return "high"


def score_token(data: TokenData) -> Report:
    """Return a risk estimate (0-100). This is NOT a guarantee of safety."""
    results = [check(data) for check in ALL_CHECKS]
    score = min(100, sum(r.weight for r in results if r.triggered))
    unknown = sum(1 for r in results if not r.known)
    return Report(data.address, score, level_for(score), results, unknown)
