import unittest
from tavorix_scanner import goplus
from tavorix_scanner.data import fetch_token_data


def holders(pcts):
    return [{"address": f"0x{i:040x}", "is_contract": "0", "percent": str(p)} for i, p in enumerate(pcts, 1)]


class FakeRpc:
    def __init__(self, slot):
        self.slot = slot

    def get_code(self, a):
        return "0x6080"

    def eth_call(self, *a, **k):
        return "0x"

    def get_storage(self, a, s):
        return self.slot


class TestGoplusFix(unittest.TestCase):
    def test_holder_over_100_is_unknown(self):
        out = goplus.to_features({"holders": holders([3999.338])})
        self.assertNotIn("top_holder_pct", out)
        self.assertNotIn("top10_pct", out)

    def test_top10_over_100_is_unknown(self):
        out = goplus.to_features({"holders": holders([0.478] + [0.06] * 9)})
        self.assertNotIn("top10_pct", out)

    def test_normal_holders_kept(self):
        out = goplus.to_features({"holders": holders([0.30, 0.10, 0.05])})
        self.assertAlmostEqual(out["top_holder_pct"], 30.0)
        self.assertAlmostEqual(out["top10_pct"], 45.0)

    def test_goplus_cannot_erase_chain_proxy(self):
        slot = "0x" + "0" * 63 + "1"
        d = fetch_token_data("0xabc", FakeRpc(slot), goplus_fetch=lambda a: {"is_proxy": "0"})
        self.assertTrue(d.is_proxy)

    def test_goplus_value_used_when_no_chain_proxy(self):
        slot = "0x" + "0" * 64
        d = fetch_token_data("0xabc", FakeRpc(slot), goplus_fetch=lambda a: {"is_proxy": "1"})
        self.assertTrue(d.is_proxy)


if __name__ == "__main__":
    unittest.main()
