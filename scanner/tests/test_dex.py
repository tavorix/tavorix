import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tavorix_scanner.dexscreener import summarize
from tavorix_scanner.data import fetch_token_data
from tavorix_scanner.rpc import RpcClient
from test_data import fake_transport, TOKEN, PAIR

DAY = 86_400_000
NOW = 1_800_000_000_000


def pair(chain="bsc", liq=1000.0, age_days=10, base=TOKEN, quote="0x" + "99" * 20):
    return {"chainId": chain, "baseToken": {"address": base}, "quoteToken": {"address": quote},
            "liquidity": {"usd": liq}, "volume": {"h24": 50.0}, "pairCreatedAt": NOW - age_days * DAY}


class DexTests(unittest.TestCase):
    def test_summarize_sums_bsc_pools_and_finds_oldest(self):
        pairs = [pair(liq=1000, age_days=10), pair(liq=2500, age_days=400), pair(chain="ethereum", liq=999999, age_days=900)]
        s = summarize(pairs, TOKEN, now_ms=NOW)
        self.assertAlmostEqual(s["liquidity_usd"], 3500.0); self.assertAlmostEqual(s["age_days"], 400.0)
        self.assertEqual(s["pairs"], 2)

    def test_summarize_none_when_no_bsc_pair(self):
        self.assertIsNone(summarize([pair(chain="solana")], TOKEN))
        self.assertIsNone(summarize([], TOKEN))

    def test_fetch_uses_dex_data_and_survives_errors(self):
        t = fake_transport("0x6080", "0x" + "00" * 20, PAIR, 1000, 0)
        ok = fetch_token_data(TOKEN, RpcClient("http://x", transport=t),
                              dex_fetch=lambda a: [pair(liq=250000, age_days=500)])
        self.assertAlmostEqual(ok.liquidity_usd, 250000.0)

        def boom(a):
            raise RuntimeError("network down")
        bad = fetch_token_data(TOKEN, RpcClient("http://x", transport=t), dex_fetch=boom)
        self.assertAlmostEqual(bad.liquidity_usd, 12000.0)  # falls back to the on-chain estimate


if __name__ == "__main__":
    unittest.main()
