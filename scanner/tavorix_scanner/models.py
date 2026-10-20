from dataclasses import dataclass, field, fields
from typing import List, Optional


@dataclass
class TokenData:
    """Facts about a token. None means 'unknown' (not fetched or not determinable)."""
    address: str = ""
    has_mint: Optional[bool] = None
    has_blacklist: Optional[bool] = None
    has_pause: Optional[bool] = None
    buy_tax_pct: Optional[float] = None
    sell_tax_pct: Optional[float] = None
    tax_mutable: Optional[bool] = None
    honeypot_sell_failed: Optional[bool] = None
    top_holder_pct: Optional[float] = None   # excluding LP and burn addresses
    top10_pct: Optional[float] = None        # excluding LP and burn addresses
    lp_locked_pct: Optional[float] = None
    lp_unlock_days: Optional[float] = None
    contract_age_days: Optional[float] = None
    source_verified: Optional[bool] = None
    owner_renounced: Optional[bool] = None
    is_proxy: Optional[bool] = None
    deployer_scam_links: Optional[int] = None


FEATURE_NAMES = [f.name for f in fields(TokenData) if f.name != "address"]


@dataclass
class CheckResult:
    name: str
    triggered: bool
    weight: int
    reason: str
    known: bool = True


@dataclass
class Report:
    address: str
    score: int
    level: str
    results: List[CheckResult] = field(default_factory=list)
    unknown_checks: int = 0

    def explain(self) -> List[str]:
        return [r.reason for r in self.results if r.triggered]
