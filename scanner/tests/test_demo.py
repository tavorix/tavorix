import json, os, sys, threading, unittest, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo"))
import server
from tavorix_scanner import TokenData, score_token


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = server.make_server(0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def get(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            body = e.read()
            e.close()
            return e.code, body

    def test_index_served(self):
        code, body = self.get("/")
        self.assertEqual(code, 200); self.assertIn(b"Tavorix", body)

    def test_bad_address_rejected(self):
        for bad in ("", "0x123", "0x" + "g" * 40, "javascript:alert(1)"):
            code, body = self.get("/api/scan?address=" + bad)
            self.assertEqual(code, 400, bad)
            self.assertIn("error", json.loads(body))

    def test_unknown_path(self):
        self.assertEqual(self.get("/nope")[0], 404)

    def test_report_json_shape(self):
        d = TokenData("0x" + "11" * 20, honeypot_sell_failed=True, has_mint=True, has_blacklist=False, liquidity_usd=1000.0)
        j = server.report_to_json(score_token(d), d)
        self.assertGreaterEqual(j["scam_score"], 60); self.assertEqual(j["scam_level"], "high")
        self.assertEqual(j["facts"]["liquidity_usd"], 1000.0)
        self.assertEqual(len(j["control_reasons"]), 1)
        self.assertEqual(len(j["checks"]), 18)
        self.assertEqual({c["status"] for c in j["checks"]}, {"flagged", "clear", "no_data"})
        self.assertEqual(j["evidence_coverage_pct"], round(100 * (18 - j["unknown_checks"]) / 18))
        self.assertIn("generated_at", j["meta"]); self.assertEqual(j["meta"]["sources_used"], [])
        json.dumps(j)  # must be serializable

    def test_server_error_is_generic(self):
        original = server.fetch_token_data
        def boom(*a, **k):
            raise RuntimeError("secret internal detail https://rpc.example/KEY")
        server.fetch_token_data = boom
        try:
            code, body = self.get("/api/scan?address=0x" + "ab" * 20)
        finally:
            server.fetch_token_data = original
        self.assertEqual(code, 502)
        self.assertNotIn(b"secret", body); self.assertNotIn(b"Traceback", body)

    def test_no_data_returns_404_message(self):
        original = server.fetch_token_data
        def nocode(*a, **k):
            raise ValueError("No contract code at this address on this chain.")
        server.fetch_token_data = nocode
        try:
            code, body = self.get("/api/scan?address=0x" + "cd" * 20)
        finally:
            server.fetch_token_data = original
        self.assertEqual(code, 404); self.assertIn(b"No contract code", body)


if __name__ == "__main__":
    unittest.main()
