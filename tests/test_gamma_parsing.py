import unittest
import json
from polymarket.clob_readiness import parse_gamma_yes_no_tokens
from polymarket.contract import FailureReason

class TestGammaParsing(unittest.TestCase):
    def test_good_yes_no_market(self):
        """Test a clean, happy-path binary market."""
        market = {
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["1001", "1002"]'
        }
        ok, yes_id, no_id, reason = parse_gamma_yes_no_tokens(market)
        self.assertTrue(ok)
        self.assertEqual(yes_id, "1001")
        self.assertEqual(no_id, "1002")
        self.assertEqual(reason, FailureReason.OK)

    def test_good_yes_no_market_inverted_order(self):
        """Test that order doesn't matter, we match by string."""
        market = {
            "outcomes": '["No", "Yes"]',
            "clobTokenIds": '["2002", "2001"]'
        }
        ok, yes_id, no_id, reason = parse_gamma_yes_no_tokens(market)
        self.assertTrue(ok)
        self.assertEqual(yes_id, "2001")  # Yes matches 2001
        self.assertEqual(no_id, "2002")   # No matches 2002
        
    def test_native_list_inputs(self):
        """Test when inputs are already lists, not JSON strings."""
        market = {
            "outcomes": ["Yes", "No"],
            "clobTokenIds": ["3001", "3002"]
        }
        ok, yes_id, no_id, reason = parse_gamma_yes_no_tokens(market)
        self.assertTrue(ok)
        self.assertEqual(yes_id, "3001")
        
    def test_malformed_json(self):
        """Test bad JSON string."""
        market = {
            "outcomes": '["Yes", "No"',  # Missing closing bracket
            "clobTokenIds": '["1", "2"]'
        }
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.GAMMA_PARSE_ERROR)
        
    def test_missing_fields(self):
        """Test missing keys."""
        market = {"outcomes": '["Yes", "No"]'} # Missing clobTokenIds
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.MISSING_CLOB_TOKEN_IDS)
        
    def test_length_mismatch(self):
        """Test outcomes vs tokenIds length mismatch."""
        market = {
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["1"]'
        }
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.OUTCOME_TOKEN_LENGTH_MISMATCH)
        
    def test_non_binary_length(self):
        """Test 3 outcomes."""
        market = {
            "outcomes": '["Yes", "No", "Maybe"]',
            "clobTokenIds": '["1", "2", "3"]'
        }
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE)
        
    def test_missing_yes_or_no(self):
        """Test 2 outcomes but not Yes/No."""
        market = {
            "outcomes": '["High", "Low"]',
            "clobTokenIds": '["1", "2"]'
        }
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE)
        
    def test_int_token_ids(self):
        """Test that integer token IDs get converted to strings safely."""
        market = {
            "outcomes": ["Yes", "No"],
            "clobTokenIds": [123456, 789012]
        }
        ok, yes_id, no_id, reason = parse_gamma_yes_no_tokens(market)
        self.assertTrue(ok)
        self.assertEqual(yes_id, "123456")
        self.assertEqual(no_id, "789012")

    def test_invalid_token_type(self):
        """Test complex object in token ID slot."""
        market = {
            "outcomes": ["Yes", "No"],
            "clobTokenIds": ["1", {"wtf": "is_this"}]
        }
        ok, yes, no, reason = parse_gamma_yes_no_tokens(market)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.INVALID_TOKEN_ID)

if __name__ == "__main__":
    unittest.main()
