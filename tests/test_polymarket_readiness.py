import unittest
from unittest.mock import patch, MagicMock
from venues.polymarket_discovery import (
    probe_clob_readiness,
    ReadinessStatus,
    FailureReason
)

class TestPolymarketReadiness(unittest.TestCase):

    @patch("polymarket.clob_readiness.requests.get")
    @patch("polymarket.clob_readiness.time.sleep") # Skip backoff
    def test_probe_ready(self, mock_sleep, mock_get):
        # Setup mock for success
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"mid": "0.5"}
        mock_get.return_value = mock_resp
        
        result = probe_clob_readiness("tok-1")
        
        self.assertEqual(result.status, ReadinessStatus.READY)
        self.assertEqual(result.reason, FailureReason.OK)

    @patch("polymarket.clob_readiness.requests.get")
    @patch("polymarket.clob_readiness.time.sleep")
    def test_probe_not_ready_404(self, mock_sleep, mock_get):
        # Setup mock for 404
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"error": "No orderbook exists"}
        mock_get.return_value = mock_resp
        
        result = probe_clob_readiness("tok-2")
        
        self.assertEqual(result.status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.reason, FailureReason.CLOB_NO_ORDERBOOK)

    @patch("polymarket.clob_readiness.requests.get")
    @patch("polymarket.clob_readiness.time.sleep")
    def test_probe_rate_limited(self, mock_sleep, mock_get):
        # Setup mock for 429
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp
        
        result = probe_clob_readiness("tok-3")
        
        self.assertEqual(result.status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(result.reason, FailureReason.CLOB_RATE_LIMITED)

    @patch("polymarket.clob_readiness.requests.get")
    @patch("polymarket.clob_readiness.time.sleep")
    def test_probe_http_error(self, mock_sleep, mock_get):
        # Setup mock for 500
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp
        
        result = probe_clob_readiness("tok-4")
        
        self.assertEqual(result.status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(result.reason, FailureReason.CLOB_5XX)

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
