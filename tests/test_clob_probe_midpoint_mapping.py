import unittest
from unittest.mock import patch, MagicMock
import json
import os
from pathlib import Path
from polymarket.clob_readiness import probe_clob_readiness
from polymarket.contract import ReadinessStatus, FailureReason

class TestClobProbeMidpointMapping(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.fixture_dir = self.root / "tests" / "fixtures" / "polymarket"
        # Clear cache between tests if necessary, but here we can just use unique token_ids
        from polymarket.clob_readiness import _probe_cache
        _probe_cache.clear()

    def _load_fixture(self, name):
        path = os.path.join(self.fixture_dir, name)
        with open(path, 'r') as f:
            return json.load(f)

    @patch('requests.get')
    def test_probe_ready(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = self._load_fixture("clob_midpoint_200.json")
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("token_ready")
        self.assertEqual(status, ReadinessStatus.READY)
        self.assertEqual(reason, FailureReason.OK)

    @patch('requests.get')
    def test_probe_no_orderbook_404(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = self._load_fixture("clob_no_orderbook_404.json")
        mock_get.return_value = mock_resp

        status, reason, meta = probe_clob_readiness("token_404")
        self.assertEqual(status, ReadinessStatus.NOT_READY)
        self.assertEqual(reason, FailureReason.CLOB_NO_ORDERBOOK)

    @patch('requests.get')
    def test_probe_rate_limit_429(self, mock_get):
        # We need to simulate multiple 429s until MAX_RETRIES (3) is exceeded
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json.return_value = self._load_fixture("clob_rate_limit_429.json")
        mock_get.return_value = mock_resp

        # Patch time.sleep to speed up tests
        with patch('time.sleep'):
            status, reason, meta = probe_clob_readiness("token_429")
            
        self.assertEqual(status, ReadinessStatus.RETRYABLE_ERROR)
        self.assertEqual(reason, FailureReason.CLOB_RATE_LIMITED)
        # Should have called requests.get 4 times (initial + 3 retries)
        self.assertEqual(mock_get.call_count, 4)

if __name__ == "__main__":
    unittest.main()
