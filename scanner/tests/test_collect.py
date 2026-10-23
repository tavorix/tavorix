import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from collect import collect
from tavorix_scanner.rpc import RpcClient
from test_data import fake_transport, TOKEN, PAIR


class CollectTests(unittest.TestCase):
    def test_collect_filters_and_labels(self):
        t = fake_transport("0x6080" + "6340c10f19", "0x" + "00" * 20, PAIR, 1000, 900)
        rows = [
            {"token_address": TOKEN, "label": "HEALTHY"},
            {"token_address": "0x" + "00" * 20, "label": "healthy"},  # template example row
            {"token_address": TOKEN, "label": ""},                     # no label
            {"token_address": TOKEN, "label": "unknown_label"},        # bad label
        ]
        out = collect(rows, RpcClient("http://x", transport=t), delay=0, log=lambda *_: None)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["label"], "healthy")
        self.assertEqual(out[0]["has_mint"], True)
        self.assertEqual(out[0]["honeypot_sell_failed"], "")  # unknown stays empty


if __name__ == "__main__":
    unittest.main()
