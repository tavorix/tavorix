import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tavorix_scanner import config
from tavorix_scanner.data import scan_selectors, fetch_token_data
from tavorix_scanner.rpc import RpcClient, pad_address, decode_address, decode_uint

TOKEN = "0x" + "11" * 20
PAIR = "0x" + "22" * 20


def word(hexstr: str) -> str:
    return "0x" + hexstr.rjust(64, "0")


def fake_transport(code: str, owner: str, pair: str, lp_total: int, lp_dead: int, owner_code: str = "0x", r_quote: int = 20 * 10**18, r_other: int = 6000 * 10**18):
    def t(url, payload):
        m, p = payload["method"], payload["params"]
        if m == "eth_getCode": return {"result": code if p[0].lower() == TOKEN.lower() else owner_code}
        if m == "eth_getStorageAt": return {"result": word("0")}
        if m == "eth_call":
            to, data = p[0]["to"].lower(), p[0]["data"]
            if data.startswith("0x8da5cb5b"): return {"result": word(owner.replace("0x", ""))}
            if data.startswith("0xe6a43905"): return {"result": word(pair.replace("0x", ""))}
            if data.startswith("0x0dfe1681"): return {"result": word(config.WBNB.replace("0x", "").lower())}
            if data.startswith("0x0902f1ac"): return {"result": "0x" + word(format(r_quote, "x"))[2:] + word(format(r_other, "x"))[2:] + word("0")[2:]}
            if data.startswith("0x18160ddd"): return {"result": word(format(lp_total, "x"))}
            if data.startswith("0x70a08231"):
                holder = "0x" + data[-40:]
                return {"result": word(format(lp_dead if holder == "0x000000000000000000000000000000000000dead" else 0, "x"))}
        return {"error": {"message": "unsupported"}}
    return t


class DataTests(unittest.TestCase):
    def test_selector_scan(self):
        self.assertTrue(scan_selectors("0x6080" + "6340c10f19" + "00", config.SELECTORS["mint"]))
        self.assertFalse(scan_selectors("0x6080" + "40c10f19" + "00", config.SELECTORS["mint"]))  # no PUSH4

    def test_helpers(self):
        self.assertEqual(pad_address("0xAB"), "0" * 62 + "ab")
        self.assertEqual(decode_address(word("ab" * 20)), "0x" + "ab" * 20)
        self.assertEqual(decode_uint(word("ff")), 255)
        self.assertIsNone(decode_uint("0x"))

    def test_fetch_with_fake_rpc(self):
        code = "0x6080" + "6340c10f19" + "638456cb59"
        t = fake_transport(code, "0x" + "00" * 20, PAIR, lp_total=1000, lp_dead=900)
        d = fetch_token_data(TOKEN, RpcClient("http://x", transport=t))
        self.assertTrue(d.has_mint); self.assertTrue(d.has_pause); self.assertFalse(d.has_blacklist)
        self.assertTrue(d.owner_renounced); self.assertAlmostEqual(d.lp_locked_pct, 90.0)
        self.assertAlmostEqual(d.liquidity_usd, 12000.0); self.assertFalse(d.owner_is_contract)
        self.assertIsNone(d.honeypot_sell_failed)  # not determinable via plain RPC

    def test_wallet_owner_detected(self):
        wallet = "0x" + "33" * 20
        t = fake_transport("0x6080", wallet, PAIR, 1000, 0, owner_code="0x")
        d = fetch_token_data(TOKEN, RpcClient("http://x", transport=t))
        self.assertFalse(d.owner_renounced); self.assertFalse(d.owner_is_contract)

    def test_contract_owner_detected(self):
        owner = "0x" + "44" * 20
        t = fake_transport("0x6080", owner, PAIR, 1000, 0, owner_code="0x6080604052")
        d = fetch_token_data(TOKEN, RpcClient("http://x", transport=t))
        self.assertFalse(d.owner_renounced); self.assertTrue(d.owner_is_contract)

    def test_no_code_raises(self):
        t = fake_transport("0x", "0x" + "00" * 20, PAIR, 1, 0)
        with self.assertRaises(ValueError):
            fetch_token_data(TOKEN, RpcClient("http://x", transport=t))


if __name__ == "__main__":
    unittest.main()
