import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from venues.kalshi_fetch import fetch_market
from eligibility.kalshi_rules import check_kalshi_eligibility, EligibilityResult

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "kalshi"

def _load_fixture(name):
    with (FIXTURE_DIR / name).open("r") as f:
        return json.load(f)

def test_fetch_market_fixture(monkeypatch):
    data = _load_fixture("market_metadata.json")
    
    # Mock requests.get
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"market": data}
    
    with patch("requests.get", return_value=mock_resp):
        meta = fetch_market("KXBTC-25DEC31")
        assert meta["ticker"] == "KXBTC-25DEC31"
        assert "Coinbase" in meta["rules_primary"]

def test_eligibility_with_fixture():
    data = _load_fixture("market_metadata.json")
    res, source = check_kalshi_eligibility(data, now_ts=1700000000) # Past compared to 2030
    assert res == EligibilityResult.ELIGIBLE
    assert source.venue == "coinbase"
