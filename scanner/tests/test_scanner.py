import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tavorix_scanner import TokenData, score_token
from evaluate import evaluate, metrics, row_to_token


class ScoringTests(unittest.TestCase):
    def test_clean_token_is_low(self):
        d = TokenData("0xA", has_mint=False, has_blacklist=False, has_pause=False, buy_tax_pct=0, sell_tax_pct=0,
                      tax_mutable=False, honeypot_sell_failed=False, top_holder_pct=5, top10_pct=30,
                      lp_locked_pct=100, lp_unlock_days=400, contract_age_days=300, source_verified=True,
                      owner_renounced=True, owner_is_contract=False, liquidity_usd=500000, is_proxy=False, deployer_scam_links=0)
        r = score_token(d)
        self.assertEqual(r.score, 0); self.assertEqual(r.level, "low"); self.assertEqual(r.unknown_checks, 0)

    def test_honeypot_is_high(self):
        r = score_token(TokenData("0xB", honeypot_sell_failed=True, has_mint=True, lp_locked_pct=0))
        self.assertEqual(r.level, "high"); self.assertGreaterEqual(r.score, 60)

    def test_unknown_data_does_not_trigger(self):
        r = score_token(TokenData("0xC"))
        self.assertEqual(r.score, 0); self.assertEqual(r.unknown_checks, 17)

    def test_low_confidence_flag(self):
        self.assertTrue(score_token(TokenData("0xF")).low_confidence)
        full = TokenData("0xG", has_mint=False, has_blacklist=False, has_pause=False, buy_tax_pct=0, sell_tax_pct=0,
                         tax_mutable=False, honeypot_sell_failed=False, top_holder_pct=5, top10_pct=30,
                         lp_locked_pct=100, lp_unlock_days=400, contract_age_days=300, source_verified=True,
                         owner_renounced=True, owner_is_contract=False, liquidity_usd=500000, is_proxy=False, deployer_scam_links=0)
        self.assertFalse(score_token(full).low_confidence)

    def test_score_capped_at_100(self):
        d = TokenData("0xD", honeypot_sell_failed=True, has_mint=True, has_blacklist=True, deployer_scam_links=3,
                      lp_locked_pct=0, source_verified=False, is_proxy=True)
        self.assertEqual(score_token(d).score, 100)

    def test_control_and_scam_are_separate(self):
        r = score_token(TokenData("0xH", owner_renounced=False, owner_is_contract=False, liquidity_usd=2000.0,
                                  has_mint=True))
        names = [x.name for x in r.results if x.triggered]
        self.assertIn("owner_is_wallet", names); self.assertIn("low_liquidity", names)
        self.assertEqual(r.score, 20)            # scam: low liquidity only
        self.assertEqual(r.control_score, 25 + 15 + 5)  # mint + wallet owner + owner not renounced
        self.assertEqual(r.level, "low"); self.assertEqual(r.control_level, "high")

    def test_established_token_downweights_unlocked_lp(self):
        young = score_token(TokenData("0xI", lp_locked_pct=0, contract_age_days=3, liquidity_usd=500000))
        old = score_token(TokenData("0xJ", lp_locked_pct=0, contract_age_days=400, liquidity_usd=500000))
        self.assertEqual(young.score, 25 + 10)  # unlocked LP + new token
        self.assertEqual(old.score, 5)

    def test_explanations_present(self):
        r = score_token(TokenData("0xE", has_mint=True))
        self.assertEqual(len(r.explain()), 1)
        self.assertEqual(len(r.explain_control()), 1); self.assertEqual(len(r.explain_scam()), 0)


class EvalTests(unittest.TestCase):
    def test_metrics_math(self):
        m = metrics(tp=8, fp=2, tn=18, fn=2)
        self.assertAlmostEqual(m["precision"], 0.8); self.assertAlmostEqual(m["recall"], 0.8)
        self.assertAlmostEqual(m["false_positive_rate"], 0.1)

    def test_evaluate_on_rows(self):
        rows = [
            {"label": "honeypot", "address": "1", "honeypot_sell_failed": "true", "deployer_scam_links": "2"},
            {"label": "healthy", "address": "2", "honeypot_sell_failed": "false", "lp_locked_pct": "100"},
            {"label": "rugpull", "address": "3", "lp_locked_pct": "0", "has_mint": "true", "source_verified": "false"},
            {"label": "healthy", "address": "4", "has_mint": "false", "lp_locked_pct": "95"},
        ]
        m = evaluate(rows, threshold=40)
        self.assertEqual((m["tp"], m["fp"], m["tn"], m["fn"]), (2, 0, 2, 0))

    def test_row_parsing(self):
        t = row_to_token({"address": "x", "has_mint": "TRUE", "buy_tax_pct": "5.5", "deployer_scam_links": "2"})
        self.assertTrue(t.has_mint); self.assertEqual(t.buy_tax_pct, 5.5); self.assertEqual(t.deployer_scam_links, 2)
        self.assertIsNone(t.sell_tax_pct)


if __name__ == "__main__":
    unittest.main()
