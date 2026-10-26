"""Detect tokens that copy the name or symbol of a famous token (for example a fake USDT).
Rule-based and simple: it only knows the tokens listed in config.KNOWN_TOKENS."""
import unicodedata
from typing import Optional, Tuple
from . import config

# A few look-alike letters (Cyrillic/Greek) mapped to Latin, so "USD\u0422" (Cyrillic T) still matches USDT.
_LOOKALIKES = {"\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0445": "x",
               "\u0443": "y", "\u0456": "i", "\u0455": "s", "\u0442": "t", "\u0432": "b", "\u043d": "h",
               "\u043a": "k", "\u043c": "m", "\u03bf": "o", "\u03c4": "t", "\u03b9": "i"}


def normalize(text: Optional[str]) -> str:
    s = unicodedata.normalize("NFKC", text or "").casefold()
    s = "".join(_LOOKALIKES.get(c, c) for c in s)
    return "".join(c for c in s if c.isalnum())


def find_impersonation(symbol: Optional[str], name: Optional[str], address: str) -> Tuple[Optional[bool], Optional[str]]:
    """Return (flag, copied_symbol). flag is None when the name and symbol could not be read."""
    if not symbol and not name:
        return None, None
    addr = (address or "").lower()
    if any(addr == v["address"].lower() for v in config.KNOWN_TOKENS.values()):
        return False, None  # this IS the official contract
    sym, nam = normalize(symbol), normalize(name)
    for known, v in config.KNOWN_TOKENS.items():
        if sym == normalize(known) or (nam and nam in {normalize(n) for n in v["names"]}):
            return True, known
    return False, None
