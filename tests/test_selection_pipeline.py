import unittest
from unittest.mock import patch, MagicMock
import json
import os
from venues.polymarket_discovery import select_best_clob_candidate, SelectionResult
from polymarket.contract import ReadinessStatus, FailureReason

class TestSelectionPipeline(unittest.TestCase):
    def setUp(self):
        self.fixture_dir = "/opt/pm_updown_bot_bundle/tests/fixtures/polymarket"
        from polymarket.clob_readiness import _probe_cache
        _probe_cache.clear()

    def _load_fixture(self, name):
        path = os.path.join(self.fixture_dir, name)
        with open(path, 'r') as f:
            return json.load(f)

    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    @patch('polymarket.clob_readiness.probe_clob_readiness')
    def test_selection_success(self, mock_probe, mock_discover):
        # 1. Mock Gamma discovery to return one ready and one not ready candidate
        ready_market = self._load_fixture("gamma_ready_candidate.json")
        ready_market["id"] = "market_ready"
        
        not_ready_market = self._load_fixture("gamma_not_ready_candidate.json")
        not_ready_market["id"] = "market_not_eligible"
        
        mock_discover.return_value = [not_ready_market, ready_market]

        # 2. Mock CLOB probe to return READY for the ready_market's token
        mock_probe.return_value = (ReadinessStatus.READY, FailureReason.OK, {"mid": "0.47"})

        # 3. Run selection
        result = select_best_clob_candidate(max_probes=5)

        self.assertEqual(result.readiness_status, ReadinessStatus.READY)
        self.assertEqual(result.selected_market_id, "market_ready")
        self.assertEqual(result.selected_token_id, "1111")
        # should have skipped 1 (not eligible) and probed 1
        self.assertEqual(result.probes_attempted, 1)

    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    def test_selection_no_eligible_markets(self, mock_discover):
        not_ready_market = self._load_fixture("gamma_not_ready_candidate.json")
        mock_discover.return_value = [not_ready_market]

        result = select_best_clob_candidate(max_probes=5)

        self.assertEqual(result.readiness_status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.failure_reason, FailureReason.MARKET_FILTERED_OUT)

if __name__ == "__main__":
    unittest.main()
