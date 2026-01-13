import unittest
from unittest.mock import patch, MagicMock
from venues.polymarket_discovery import (
    probe_clob_readiness,
    ReadinessStatus,
    NotReadyReason
)
from venues.polymarket_fetch import PolymarketFetchError

class TestPolymarketReadiness(unittest.TestCase):

    @patch("venues.polymarket_discovery.fetch_book")
    @patch("venues.polymarket_discovery._PROBE_LIMITER.wait") # Skip delay
    def test_probe_ready(self, mock_wait, mock_fetch):
        # Setup mock for success
        mock_fetch.return_value = {"market": "foo", "bids": [], "asks": []}
        
        result = probe_clob_readiness("mkt-1", "tok-1")
        
        self.assertEqual(result.status, ReadinessStatus.READY)
        self.assertIsNone(result.reason)
        self.assertEqual(result.market_id, "mkt-1")
        self.assertEqual(result.token_id, "tok-1")

    @patch("venues.polymarket_discovery.fetch_book")
    @patch("venues.polymarket_discovery._PROBE_LIMITER.wait")
    def test_probe_not_ready_404(self, mock_wait, mock_fetch):
        # Setup mock for 404
        mock_fetch.side_effect = PolymarketFetchError("HTTP_404", status_code=404)
        
        result = probe_clob_readiness("mkt-2", "tok-2")
        
        self.assertEqual(result.status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.reason, NotReadyReason.NO_ORDERBOOK)
        self.assertEqual(result.http_status, 404)

    @patch("venues.polymarket_discovery.fetch_book")
    @patch("venues.polymarket_discovery._PROBE_LIMITER.wait")
    def test_probe_rate_limited(self, mock_wait, mock_fetch):
        # Setup mock for 429
        mock_fetch.side_effect = PolymarketFetchError("HTTP_429", status_code=429)
        
        result = probe_clob_readiness("mkt-3", "tok-3")
        
        self.assertEqual(result.status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.reason, NotReadyReason.RATE_LIMITED)
        self.assertEqual(result.http_status, 429)

    @patch("venues.polymarket_discovery.fetch_book")
    @patch("venues.polymarket_discovery._PROBE_LIMITER.wait")
    def test_probe_http_error(self, mock_wait, mock_fetch):
        # Setup mock for 500
        mock_fetch.side_effect = PolymarketFetchError("HTTP_500", status_code=500)
        
        result = probe_clob_readiness("mkt-4", "tok-4")
        
        self.assertEqual(result.status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.reason, NotReadyReason.HTTP_ERROR)
        self.assertEqual(result.http_status, 500)

    @patch("venues.polymarket_discovery.fetch_book")
    @patch("venues.polymarket_discovery._PROBE_LIMITER.wait")
    def test_probe_timeout(self, mock_wait, mock_fetch):
        # Setup mock for timeout
        mock_fetch.side_effect = PolymarketFetchError("TIMEOUT")
        
        result = probe_clob_readiness("mkt-5", "tok-5")
        
        self.assertEqual(result.status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.reason, NotReadyReason.HTTP_ERROR)
        self.assertIn("TIMEOUT", str(result.detail))

if __name__ == "__main__":
    unittest.main()
