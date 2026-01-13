"""Canonical reason codes for trading decisions."""

from enum import Enum

class ReasonCode(str, Enum):
    # Success
    EDGE_OK = "EDGE_OK"
    
    # Strategy Filters
    EDGE_TOO_SMALL = "EDGE_TOO_SMALL"
    BOOK_INCOMPLETE = "BOOK_INCOMPLETE"
    MODEL_WARMUP = "MODEL_WARMUP"
    
    # Staleness / Data Issues
    STALE_FEED = "STALE_FEED"
    STALE_BOOK = "STALE_BOOK"
    OFFICIAL_FEED_MISSING = "OFFICIAL_FEED_MISSING"
    BOOK_DATA_MISSING = "BOOK_DATA_MISSING"
    FEED_STALE_ABORT = "FEED_STALE_ABORT"
    
    # Safety / Risk
    END_TIME_ANOMALY = "END_TIME_ANOMALY"
    TIME_TO_END_CUTOFF = "TIME_TO_END_CUTOFF"
    RATE_LIMIT = "RATE_LIMIT"
    CANCEL_RATE_LIMIT = "CANCEL_RATE_LIMIT"
    EXPOSURE_CAP = "EXPOSURE_CAP"
    RESOLUTION_SOURCE_UNKNOWN = "RESOLUTION_SOURCE_UNKNOWN"
    
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_ 
