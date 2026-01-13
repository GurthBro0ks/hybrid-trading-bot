
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from venues.polymarket_discovery import (
    select_best_clob_candidate, 
    _is_market_eligible,
    SelectionResult,
    discover_and_filter_candidates
)
from polymarket.contract import ReadinessStatus, FailureReason

# Mock Data
MOCK_GOOD_MARKET = {
    "id": "m1",
    "enableOrderBook": True,
    "acceptingOrders": True,
    "restricted": False,
    "endDateIso": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    "liquidityNum": 1000,
    "volume24hr": 500,
    "clobTokenIds": ["yes_123", "no_456"],
    "outcomes": ["Yes", "No"]
}

MOCK_BAD_FILTER_MARKET = {
    "id": "m2",
    "enableOrderBook": False, # Fail
    "acceptingOrders": True,
    "endDateIso": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
}

MOCK_SHORT_EXPIRY_MARKET = {
    "id": "m3",
    "enableOrderBook": True,
    "acceptingOrders": True,
    "endDateIso": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(), # Fail < 24h
}

class TestDiscoveryPipeline(unittest.TestCase):

    def test_filter_eligibility(self):
        # Good market
        ok, reason = _is_market_eligible(MOCK_GOOD_MARKET)
        self.assertTrue(ok)
        self.assertEqual(reason, FailureReason.OK)

        # Disabled orderbook
        ok, reason = _is_market_eligible(MOCK_BAD_FILTER_MARKET)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.ORDERBOOK_DISABLED)

        # Expiring soon
        ok, reason = _is_market_eligible(MOCK_SHORT_EXPIRY_MARKET)
        self.assertFalse(ok)
        self.assertEqual(reason, FailureReason.EXPIRING_SOON)
        
    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    @patch('polymarket.clob_readiness.parse_gamma_yes_no_tokens')
    @patch('polymarket.clob_readiness.probe_clob_readiness')
    def test_selection_pipeline_success(self, mock_probe, mock_parse, mock_discover):
        # Setup mocks
        mock_discover.return_value = [MOCK_GOOD_MARKET]
        mock_parse.return_value = (True, "yes_123", "no_456", FailureReason.OK)
        # Using correct Enum return
        mock_probe.return_value = (ReadinessStatus.READY, FailureReason.OK, {})
        
        result = select_best_clob_candidate()
        
        self.assertEqual(result.readiness_status, ReadinessStatus.READY)
        self.assertEqual(result.selected_market_id, "m1")
        self.assertEqual(result.selected_token_id, "yes_123")
        self.assertEqual(result.probes_attempted, 1)

    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    @patch('polymarket.clob_readiness.parse_gamma_yes_no_tokens')
    @patch('polymarket.clob_readiness.probe_clob_readiness')
    def test_pipeline_fail_parse_then_success(self, mock_probe, mock_parse, mock_discover):
        # Market 1: Parse Fail
        m1 = MOCK_GOOD_MARKET.copy()
        m1["id"] = "bad_parse"
        
        # Market 2: Success
        m2 = MOCK_GOOD_MARKET.copy()
        m2["id"] = "good_one"
        
        mock_discover.return_value = [m1, m2]
        
        # Side effects
        def parse_side_effect(m):
            if m["id"] == "bad_parse":
                return (False, None, None, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE)
            return (True, "yes_good", "no_good", FailureReason.OK)
            
        mock_parse.side_effect = parse_side_effect
        mock_probe.return_value = (ReadinessStatus.READY, FailureReason.OK, {})
        
        result = select_best_clob_candidate()
        
        self.assertEqual(result.readiness_status, ReadinessStatus.READY)
        self.assertEqual(result.selected_market_id, "good_one")
        # Probes attempted might be 1 (since parse fail doesn't count as full probe? Or does it?)
        # My implementation loops and Incrs probes_attempted inside loop.
        # If parse fails, it still increments probes_attempted.
        self.assertEqual(result.probes_attempted, 2) 

    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    @patch('polymarket.clob_readiness.parse_gamma_yes_no_tokens')
    @patch('polymarket.clob_readiness.probe_clob_readiness')
    def test_pipeline_fail_closed_no_ready(self, mock_probe, mock_parse, mock_discover):
        mock_discover.return_value = [MOCK_GOOD_MARKET]
        mock_parse.return_value = (True, "yes_fail", "no_fail", FailureReason.OK)
        mock_probe.return_value = (ReadinessStatus.NOT_READY, FailureReason.CLOB_NO_ORDERBOOK, {})
        
        result = select_best_clob_candidate()
        
        self.assertEqual(result.readiness_status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.failure_reason, FailureReason.NO_READY_CANDIDATES)
        self.assertEqual(result.probes_attempted, 1)

    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    def test_no_eligible_candidates(self, mock_discover):
        mock_discover.return_value = [MOCK_BAD_FILTER_MARKET] # Filtered out
        
        result = select_best_clob_candidate()
        
        self.assertEqual(result.readiness_status, ReadinessStatus.NOT_READY)
        self.assertEqual(result.failure_reason, FailureReason.MARKET_FILTERED_OUT)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(result.probes_attempted, 0)
        
    @patch('polymarket.clob_readiness.discover_gamma_candidates')
    @patch('polymarket.clob_readiness.parse_gamma_yes_no_tokens')
    @patch('polymarket.clob_readiness.probe_clob_readiness')
    def test_legacy_wrapper(self, mock_probe, mock_parse, mock_discover):
        mock_discover.return_value = [MOCK_GOOD_MARKET]
        mock_parse.return_value = (True, "yes_123", "no_456", FailureReason.OK)
        # Fix mock to return Enums
        mock_probe.return_value = (ReadinessStatus.READY, FailureReason.OK, {})
        
        res = discover_and_filter_candidates()
        
        self.assertEqual(len(res["ready"]), 1)
        self.assertEqual(len(res["not_ready"]), 0)
        self.assertEqual(res["ready"][0]["id"], "m1")

if __name__ == '__main__':
    unittest.main()
