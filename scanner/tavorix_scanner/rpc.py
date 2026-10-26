import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Optional


def _http_post(url: str, payload: dict, timeout: int = 20, retries: int = 3) -> dict:
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # network hiccup: retry
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last


class RpcClient:
    """Minimal JSON-RPC client (standard library only). `transport` is injectable for tests."""

    def __init__(self, url: str, transport: Optional[Callable[[str, dict], dict]] = None):
        self.url = url
        self.transport = transport or _http_post
        self._id = 0

    def call(self, method: str, params: list) -> Any:
        self._id += 1
        out = self.transport(self.url, {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        if "error" in out:
            raise RuntimeError(out["error"])
        return out["result"]

    def eth_call(self, to: str, data: str) -> Optional[str]:
        try:
            return self.call("eth_call", [{"to": to, "data": data}, "latest"])
        except RuntimeError:
            return None

    def get_code(self, address: str) -> str:
        return self.call("eth_getCode", [address, "latest"])

    def get_storage(self, address: str, slot: str) -> str:
        return self.call("eth_getStorageAt", [address, slot, "latest"])


def pad_address(addr: str) -> str:
    return addr.lower().replace("0x", "").rjust(64, "0")


def decode_address(word: Optional[str]) -> Optional[str]:
    if not word or len(word) < 66:
        return None
    return "0x" + word[-40:]


def decode_uint(word: Optional[str]) -> Optional[int]:
    if not word or word == "0x":
        return None
    return int(word, 16)


def decode_string(word: Optional[str]) -> Optional[str]:
    """Decode an ABI-encoded string, or the bytes32 form used by some old tokens. None if unreadable."""
    if not word or word == "0x":
        return None
    try:
        raw = bytes.fromhex(word[2:] if word.startswith("0x") else word)
        if len(raw) == 32:
            text = raw.rstrip(b"\x00").decode("utf-8", "ignore")
        elif len(raw) >= 64:
            offset = int.from_bytes(raw[0:32], "big")
            length = int.from_bytes(raw[offset:offset + 32], "big")
            if length > 1000:
                return None
            text = raw[offset + 32:offset + 32 + length].decode("utf-8", "ignore")
        else:
            return None
    except (ValueError, OverflowError):
        return None
    return text.strip("\x00 \t\n") or None
