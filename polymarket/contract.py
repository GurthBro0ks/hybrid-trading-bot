from enum import Enum, auto

class ReadinessStatus(Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"
    PERM_ERROR = "PERM_ERROR"

class FailureReason(Enum):
    # Success
    OK = "OK"

    # Retryable CLOB Errors
    CLOB_NO_ORDERBOOK = "CLOB_NO_ORDERBOOK"  # Often transient initial state, can become ready
    CLOB_RATE_LIMITED = "CLOB_RATE_LIMITED"
    CLOB_TIMEOUT = "CLOB_TIMEOUT"
    CLOB_5XX = "CLOB_5XX"
    CLOB_INVALID_PAYLOAD = "CLOB_INVALID_PAYLOAD"
    CLOB_UNKNOWN_ERROR = "CLOB_UNKNOWN_ERROR"

    # Non-Retryable / Permanent Errors
    INVALID_TOKEN_ID = "INVALID_TOKEN_ID"
    NOT_FOUND_UNKNOWN = "NOT_FOUND_UNKNOWN"  # 404 but not specific "No orderbook"
    
    # Gamma Parsing Errors (Non-Retryable)
    GAMMA_PARSE_ERROR = "GAMMA_PARSE_ERROR"
    MISSING_CLOB_TOKEN_IDS = "MISSING_CLOB_TOKEN_IDS"
    UNSUPPORTED_OUTCOMES_SHAPE = "UNSUPPORTED_OUTCOMES_SHAPE"
    OUTCOME_TOKEN_LENGTH_MISMATCH = "OUTCOME_TOKEN_LENGTH_MISMATCH"
    
    # Eligibility Filters (Non-Retryable)
    MARKET_FILTERED_OUT = "MARKET_FILTERED_OUT"
    ORDERBOOK_DISABLED = "ORDERBOOK_DISABLED"
    NOT_ACCEPTING_ORDERS = "NOT_ACCEPTING_ORDERS"
    RESTRICTED = "RESTRICTED"
    NO_END_DATE = "NO_END_DATE"
    EXPIRING_SOON = "EXPIRING_SOON"
    BAD_DATE_FORMAT = "BAD_DATE_FORMAT"
    
    # Pipeline Errors
    NO_READY_CANDIDATES = "NO_READY_CANDIDATES"
    EXHAUSTED_PROBES_OR_CANDIDATES = "EXHAUSTED_PROBES_OR_CANDIDATES"

def is_retryable(reason: FailureReason) -> bool:
    """
    Returns True if the failure reason is transient and should trigger a retry
    (e.g., rate limits, timeouts, server errors).
    Detailed note: CLOB_NO_ORDERBOOK is historically 'not ready', but technically could be 'retryable' 
    if we wait for it to be created. However, in the context of 'is this market ready *right now* to break a loop?', 
    it is usually treated as a soft failure (NOT_READY). 
    
    Here 'retryable' means 'should we use exponential backoff and retry the HTTP request IMMEDIATELY?'.
    """
    return reason in {
        FailureReason.CLOB_RATE_LIMITED,
        FailureReason.CLOB_TIMEOUT,
        FailureReason.CLOB_5XX,
    }

def cache_ttl_for(reason: FailureReason, status: ReadinessStatus) -> int:
    """
    Returns the cache TTL in seconds based on reason and status.
    """
    if status == ReadinessStatus.READY:
        return 1800  # 30 minutes

    if status == ReadinessStatus.RETRYABLE_ERROR:
        return 30    # Short TTL for transient errors
        
    if reason == FailureReason.CLOB_NO_ORDERBOOK:
        return 300   # 5 minutes - expensive to check constantly, but might appear later
        
    if status == ReadinessStatus.NOT_READY:
        return 300   # 5 minutes default for soft failures
        
    if status == ReadinessStatus.PERM_ERROR:
        return 3600  # 1 hour - likely won't change soon

    return 60 # Default fallback
