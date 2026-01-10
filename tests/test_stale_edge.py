
import unittest
from strategies.stale_edge import StaleEdgeStrategy, BookTop
from risk.rules import RiskRules

class TestStaleEdgeThinBook(unittest.TestCase):
    def setUp(self):
        self.rules = RiskRules()
        self.rules.thin_book_threshold_depth_usd = 20.0
        self.rules.thin_book_threshold_qty = 5.0
        self.rules.spread_max = 0.05
        # Ensure other rules don't block
        self.rules.book_stale_sec = 100
        self.rules.official_stale_sec = 100
        
        self.strategy = StaleEdgeStrategy(self.rules)
        # Mock model warmup
        for i in range(10):
            self.strategy.model.update(1000 + i*1000, 0.5)

    def test_no_bbo(self):
        book = BookTop(None, None, None, None, ts_ms=1000)
        d = self.strategy.evaluate("mkt", 0.5, 1000, book, 999999, 1000)
        self.assertEqual(d.reason, "THIN_BOOK")
        self.assertEqual(d.thin_book_reason, "NO_BBO")

    def test_one_sided(self):
        book = BookTop(0.5, 0.55, None, None, ts_ms=1000)
        d = self.strategy.evaluate("mkt", 0.5, 1000, book, 999999, 1000)
        self.assertEqual(d.reason, "THIN_BOOK")
        self.assertEqual(d.thin_book_reason, "ONE_SIDED")

    def test_depth_below_threshold(self):
        # 0.5 * 4.0 = 2.0 USD < 20.0 USD
        book = BookTop(0.5, 0.55, 0.45, 0.5, 
                       yes_bid_qty=4.0, yes_ask_qty=100.0,
                       no_bid_qty=100.0, no_ask_qty=100.0,
                       ts_ms=1000)
        d = self.strategy.evaluate("mkt", 0.5, 1000, book, 999999, 1000)
        self.assertEqual(d.reason, "THIN_BOOK")
        self.assertEqual(d.thin_book_reason, "DEPTH_BELOW_THRESHOLD")
        self.assertEqual(d.thin_book_threshold_qty, 5.0)

    def test_spread_wide(self):
        # Spread 0.10 > 0.05
        book = BookTop(0.40, 0.50, 0.50, 0.60, 
                       yes_bid_qty=100.0, yes_ask_qty=100.0,
                       no_bid_qty=100.0, no_ask_qty=100.0,
                       ts_ms=1000)
        d = self.strategy.evaluate("mkt", 0.5, 1000, book, 999999, 1000)
        self.assertEqual(d.reason, "THIN_BOOK")
        self.assertEqual(d.thin_book_reason, "SPREAD_WIDE")

if __name__ == '__main__':
    unittest.main()
