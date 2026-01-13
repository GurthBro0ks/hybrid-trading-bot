import time
from eligibility.kalshi_rules import is_market_open

def test_is_market_open_simple():
    close = 1000.0
    buffer = 5.0
    
    # Well before
    assert is_market_open(900.0, close, buffer) is True
    
    # Exactly at buffer boundary (fail closed: expected < close - buffer)
    # 995 < 995 is False.
    assert is_market_open(995.0, close, buffer) is False
    
    # After
    assert is_market_open(1001.0, close, buffer) is False

def test_is_market_open_no_buffer():
    close = 1000.0
    assert is_market_open(999.9, close) is True
    assert is_market_open(1000.0, close) is False
