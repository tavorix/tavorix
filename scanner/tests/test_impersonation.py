import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tavorix_scanner import config, TokenData, score_token
from tavorix_scanner.impersonation import find_impersonation
from tavorix_scanner.rpc import RpcClient, decode_string
from tavorix_scanner.data import fetch_token_data
from test_data import fake_transport, TOKEN, PAIR

NO_POOL = "0x" + "00" * 20


def abi_string(text):
    b = text.encode()
    return "0x" + (32).to_bytes(32, "big").hex() + len(b).to_bytes(32, "big").hex() + b.ljust(32, b"\0").hex()


def with_text(inner, symbol=None, name=None):
    def t(url, payload):
        if payload["method"] == "eth_call":
            data = payload["params"][0]["data"]
            if data.startswith("0x95d89b41") and symbol: return {"result": abi_string(symbol)}
            if data.startswith("0x06fdde03") and name: return {"result": abi_string(name)}
        return inner(url, payload)
    return t


def fetch(goplus=None, pair=PAIR, symbol=None, name=None):
    t = with_text(fake_transport("0x6080", "0x" + "00" * 20, pair, 1000, 0), symbol, name)
    return fetch_token_data(TOKEN, RpcClient("http://x", transport=t), goplus_fetch=(lambda a: goplus) if goplus else None)


class ImpersonationTests(unittest.TestCase):
    def test_find_impersonation(self):
        self.assertEqual(find_impersonation("USDT", "Tether USD", config.USDT), (False, None))   # the official contract
        self.assertEqual(find_impersonation("USDT", "x", TOKEN), (True, "USDT"))
        self.assertEqual(find_impersonation("ABC", "Tether USD", TOKEN), (True, "USDT"))          # copied by name
        self.assertEqual(find_impersonation("USD\u0422", "x", TOKEN), (True, "USDT"))            # Cyrillic look-alike T
        self.assertEqual(find_impersonation("CAKE", "PancakeSwap Token", TOKEN), (False, None))
        self.assertEqual(find_impersonation(None, None, TOKEN), (None, None))

    def test_decode_string(self):
        self.assertEqual(decode_string(abi_string("USDT")), "USDT")
        self.assertEqual(decode_string("0x" + b"MKR".ljust(32, b"\0").hex()), "MKR")
        self.assertIsNone(decode_string("0x")); self.assertIsNone(decode_string("0x1234"))

    def test_fetch_flags_fake_and_unknown(self):
        d = fetch(symbol="USDT", name="Tether USD")
        self.assertTrue(d.impersonates_known_token); self.assertEqual(d.impersonated_symbol, "USDT")
        self.assertIsNone(fetch().impersonates_known_token)   # name/symbol unreadable -> unknown, never "clear"

    def test_scoring(self):
        r = score_token(TokenData("0xF", impersonates_known_token=True, impersonated_symbol="USDT"))
        self.assertEqual(r.score, 50); self.assertTrue(any("USDT" in x for x in r.explain_scam()))
        self.assertEqual(r.unknown_checks, 17)
        self.assertEqual(score_token(TokenData("0xG")).unknown_checks, 18)


class SimulationGuardTests(unittest.TestCase):
    CLEAR = {"is_honeypot": "0", "buy_tax": "0", "sell_tax": "0"}

    def test_no_pool_means_no_data(self):
        d = fetch(dict(self.CLEAR, is_in_dex="0"))
        self.assertIsNone(d.honeypot_sell_failed); self.assertIsNone(d.buy_tax_pct); self.assertIsNone(d.sell_tax_pct)
        self.assertIsNone(fetch(self.CLEAR, pair=NO_POOL).honeypot_sell_failed)   # no flag, no pool found either

    def test_pool_keeps_clear_result(self):
        self.assertIs(fetch(dict(self.CLEAR, is_in_dex="1"), pair=NO_POOL).honeypot_sell_failed, False)
        d = fetch(self.CLEAR)   # liquidity found on chain
        self.assertIs(d.honeypot_sell_failed, False); self.assertEqual(d.sell_tax_pct, 0.0)

    def test_flagged_honeypot_is_kept(self):
        self.assertIs(fetch(dict(self.CLEAR, is_honeypot="1", is_in_dex="0")).honeypot_sell_failed, True)

    def test_fake_usdt_scenario(self):
        holders = [{"address": "0x%x" % (i + 1), "percent": p, "is_contract": "0"}
                   for i, p in enumerate(["0.569", "0.07", "0.05", "0.03", "0.02"])]
        info = dict(self.CLEAR, is_in_dex="0", holders=holders)
        r = score_token(fetch(info, pair=NO_POOL, symbol="USDT", name="Tether USD"))
        by = {x.name: x for x in r.results}
        self.assertFalse(by["honeypot_simulation"].known)           # no pool: honeypot test is "No data"
        self.assertTrue(by["impersonation"].triggered)
        self.assertEqual(r.score, 15 + 15 + 50); self.assertEqual(r.level, "high")


if __name__ == "__main__":
    unittest.main()
