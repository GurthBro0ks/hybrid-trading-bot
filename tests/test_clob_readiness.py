import unittest
from unittest.mock import patch, MagicMock
import requests
import time
from polymarket.clob_readiness import probe_clob_readiness, _probe_cache
from polymarket.contract import ReadinessStatus, FailureReason

class TestClobReadiness(unittest.TestCase):
    def setUp(self):
        # Clear cache before each test
        _probe_cache.clear()

    @patch('polymarket.clob_readiness.requests.get')
    def test_ready_200(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"mid": 0.5}
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("1234567890")
        
        self.assertEqual(status, ReadinessStatus.READY)
        self.assertEqual(reason, FailureReason.OK)
        # Check cache
        self.assertIn("1234567890", _probe_cache)

    @patch('polymarket.clob_readiness.requests.get')
    def test_not_ready_404_no_orderbook(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"message": "No orderbook exists"}
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("1234567890")
        
        self.assertEqual(status, ReadinessStatus.NOT_READY)
        self.assertEqual(reason, FailureReason.CLOB_NO_ORDERBOOK)

    @patch('polymarket.clob_readiness.requests.get')
    def test_retryable_429(self, mock_get):
        # Mock 429 response
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        # Patch sleep to speed up test
        with patch('polymarket.clob_readiness.time.sleep'):
             status, reason, meta = probe_clob_readiness("123456")

        self.assertEqual(status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(reason, FailureReason.CLOB_RATE_LIMITED)
        # Should have retried 4 times (1 initial + 3 retries)
        self.assertEqual(mock_get.call_count, 4)

    @patch('polymarket.clob_readiness.requests.get')
    def test_retryable_500(self, mock_get):
        # Mock 500 response
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        # Patch sleep to speed up test
        with patch('polymarket.clob_readiness.time.sleep'):
             status, reason, meta = probe_clob_readiness("123456")

        self.assertEqual(status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(reason, FailureReason.CLOB_5XX)
        self.assertEqual(mock_get.call_count, 4)

    @patch('polymarket.clob_readiness.requests.get')
    def test_timeout(self, mock_get):
        # Mock timeout
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        # Patch sleep
        with patch('polymarket.clob_readiness.time.sleep'):
             status, reason, meta = probe_clob_readiness("123456")

        self.assertEqual(status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(reason, FailureReason.CLOB_TIMEOUT)
        self.assertEqual(mock_get.call_count, 4)

    @patch('polymarket.clob_readiness.requests.get')
    def test_invalid_400(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("invalid_token")
        
        self.assertEqual(status, ReadinessStatus.NOT_READY)
        self.assertEqual(reason, FailureReason.INVALID_TOKEN_ID)
        # Should not retry
        self.assertEqual(mock_get.call_count, 1)

    @patch('polymarket.clob_readiness.requests.get')
    def test_unknown_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 418 # I'm a teapot
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("123456")
        
        self.assertEqual(status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(reason, FailureReason.CLOB_UNKNOWN_ERROR)

    @patch('polymarket.clob_readiness.requests.get')
    def test_caching(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"mid": 0.5}
        mock_get.return_value = mock_resp

        # First call hits network
        status, reason, meta = probe_clob_readiness("cache_token")
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(status, ReadinessStatus.READY)

        # Second call hits cache
        status, reason, meta = probe_clob_readiness("cache_token")
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(status, ReadinessStatus.READY)

if __name__ == "__main__":
    unittest.main()
