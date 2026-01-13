import unittest
import json
import os
from polymarket.clob_readiness import parse_gamma_yes_no_tokens
from polymarket.contract import FailureReason

class TestGammaParseYesNoTokens(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = "/opt/pm_updown_bot_bundle/tests/fixtures/polymarket"

    def _load_fixture(self, name):
        path = os.path.join(self.fixture_dir, name)
        with open(path, 'r') as f:
            return json.load(f)

    def test_parse_ready_candidate(self):
        market = self._load_fixture("gamma_ready_candidate.json")
        success, yes_token, no_token, reason = parse_gamma_yes_no_tokens(market)
        self.assertTrue(success)
        self.assertEqual(yes_token, "1111")
        self.assertEqual(no_token, "2222")
        self.assertEqual(reason, FailureReason.OK)

    def test_parse_malformed(self):
        market = self._load_fixture("gamma_malformed.json")
        success, yes_token, no_token, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(success)
        self.assertIsNone(yes_token)
        self.assertIsNone(no_token)
        self.assertEqual(reason, FailureReason.GAMMA_PARSE_ERROR)

    def test_parse_missing_tokens(self):
        market = {
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": None
        }
        success, yes_token, no_token, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(success)
        self.assertEqual(reason, FailureReason.MISSING_CLOB_TOKEN_IDS)

if __name__ == "__main__":
    unittest.main()
