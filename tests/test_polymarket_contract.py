import pytest
from polymarket.contract import ReadinessStatus, FailureReason, is_retryable, cache_ttl_for

def test_is_retryable():
    # True positives
    assert is_retryable(FailureReason.CLOB_RATE_LIMITED) is True
    assert is_retryable(FailureReason.CLOB_TIMEOUT) is True
    assert is_retryable(FailureReason.CLOB_5XX) is True

    # True negatives
    assert is_retryable(FailureReason.CLOB_NO_ORDERBOOK) is False
    assert is_retryable(FailureReason.INVALID_TOKEN_ID) is False
    assert is_retryable(FailureReason.GAMMA_PARSE_ERROR) is False
    assert is_retryable(FailureReason.OK) is False

def test_cache_ttl_logic():
    # Ready -> 30 mins
    assert cache_ttl_for(FailureReason.OK, ReadinessStatus.READY) == 1800
    
    # Retryable -> 30s
    assert cache_ttl_for(FailureReason.CLOB_RATE_LIMITED, ReadinessStatus.RETRYABLE_ERROR) == 30
    
    # No Orderbook -> 5 mins
    assert cache_ttl_for(FailureReason.CLOB_NO_ORDERBOOK, ReadinessStatus.NOT_READY) == 300
    
    # Random Not Ready -> 5 mins
    # (Reason doesn't strictly matter if status is NOT_READY, but good to check)
    assert cache_ttl_for(FailureReason.NOT_FOUND_UNKNOWN, ReadinessStatus.NOT_READY) == 300
    
    # Permalink Error -> 1 hour
    assert cache_ttl_for(FailureReason.INVALID_TOKEN_ID, ReadinessStatus.PERM_ERROR) == 3600
