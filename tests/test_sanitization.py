import unittest
from polymarket.clob_readiness import sanitize_token_id, sanitize_market_id

class TestSanitization(unittest.TestCase):
    def test_sanitize_token_id(self):
        self.assertEqual(sanitize_token_id("1234567890"), "567890")
        self.assertEqual(sanitize_token_id("12345"), "12345")
        self.assertEqual(sanitize_token_id(""), "None")
        self.assertEqual(sanitize_token_id(None), "None")
        self.assertEqual(sanitize_token_id(1234567890), "567890")

    def test_sanitize_market_id(self):
        self.assertEqual(sanitize_market_id("12345"), "12345")
        self.assertEqual(sanitize_market_id(12345), "12345")
        self.assertEqual(sanitize_market_id(None), "None")

if __name__ == "__main__":
    unittest.main()
