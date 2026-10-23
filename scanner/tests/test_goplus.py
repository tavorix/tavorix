import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tavorix_scanner.goplus import to_features
from tavorix_scanner.data import fetch_token_data
from tavorix_scanner.rpc import RpcClient
from test_data import fake_transport, TOKEN, PAIR

SAMPLE = {
    "is_honeypot": "1", "buy_tax": "0", "sell_tax": "0.99", "is_open_source": "0", "is_mintable": "1",
    "is_blacklisted": "0", "transfer_pausable": "1", "is_proxy": "0", "slippage_modifiable": "1",
    "honeypot_with_same_creator": "1",
    "holders": [
        {"address": "0x000000000000000000000000000000000000dead", "percent": "0.4", "is_contract": "0"},
        {"address": "0xaaa", "percent": "0.30", "is_contract": "0"},
        {"address": "0xbbb", "percent": "0.20", "is_contract": "1"},
        {"address": "0xccc", "percent": "0.05", "is_contract": "0"},
    ],
    "lp_holders": [
        {"address": "0xlocker", "percent": "0.6", "is_locked": "1"},
        {"address": "0xperson", "percent": "0.4", "is_locked": "0"},
    ],
}


class GoplusTests(unittest.TestCase):
    def test_mapping(self):
        f = to_features(SAMPLE)
        self.assertTrue(f["honeypot_sell_failed"]); self.assertAlmostEqual(f["sell_tax_pct"], 99.0)
        self.assertAlmostEqual(f["buy_tax_pct"], 0.0); self.assertFalse(f["source_verified"])
        self.assertTrue(f["has_mint"]); self.assertTrue(f["has_pause"]); self.assertFalse(f["has_blacklist"])
        self.assertTrue(f["tax_mutable"]); self.assertEqual(f["deployer_scam_links"], 1)
        self.assertAlmostEqual(f["top_holder_pct"], 30.0)            # dead + contract holders excluded
        self.assertAlmostEqual(f["top10_pct"], 35.0)
        self.assertAlmostEqual(f["lp_locked_pct"], 60.0)

    def test_missing_values_are_omitted(self):
        f = to_features({"buy_tax": "", "is_honeypot": None})
        self.assertNotIn("buy_tax_pct", f); self.assertNotIn("honeypot_sell_failed", f)

    def test_fetch_applies_goplus_and_survives_errors(self):
        t = fake_transport("0x6080", "0x" + "00" * 20, PAIR, 1000, 0)
        d = fetch_token_data(TOKEN, RpcClient("http://x", transport=t), goplus_fetch=lambda a: SAMPLE)
        self.assertTrue(d.honeypot_sell_failed); self.assertAlmostEqual(d.lp_locked_pct, 60.0)

        def boom(a):
            raise RuntimeError("down")
        d2 = fetch_token_data(TOKEN, RpcClient("http://x", transport=t), goplus_fetch=boom)
        self.assertIsNone(d2.honeypot_sell_failed)


if __name__ == "__main__":
    unittest.main()
