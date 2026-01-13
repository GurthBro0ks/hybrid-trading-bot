"""
Polymarket Discovery & CLOB Readiness Probing

Implements a typed readiness model to filter candidates based on actual CLOB orderbook availability.
Probes the /book endpoint to distinguish between truly ready markets and those that are
uninitialized or missing orderbooks.
"""

import time
import logging
import requests
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Dict, Any

def discover_gamma_candidates(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetches active markets from Polymarket Gamma API.
    Returns list of market dictionaries.
    """
    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={limit}&offset=0"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Gamma discovery failed: {resp.status_code}")
            return []
        
        data = resp.json()
        candidates = []
        for m in data:
            # We need markets with CLOB token IDs
            if not m.get("active") or m.get("closed"):
                continue
                
            clob_ids = m.get("clobTokenIds")
            if not clob_ids:
                continue
                
            # Parse clobTokenIds if it's a string (seen in gamma_discovery.py)
            if isinstance(clob_ids, str):
                import json
                try:
                    clob_ids = json.loads(clob_ids)
                except Exception:
                    continue
            
            if isinstance(clob_ids, list) and len(clob_ids) > 0:
                # Normalize candidate structure
                m["clobTokenIds"] = clob_ids
                # Ensure we have an 'id'
                if "id" not in m:
                    # Some endpoints use 'market_id', others 'id'. Gamma uses 'id'.
                    if "market_id" in m:
                        m["id"] = m["market_id"]
                candidates.append(m)
                
        return candidates
    except Exception as e:
        logger.error(f"Gamma discovery error: {e}")
        return []

from venues.polymarket_fetch import fetch_book, PolymarketFetchError

logger = logging.getLogger("pm_discovery")


class ReadinessStatus(Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class NotReadyReason(Enum):
    CLOB_NOT_INITIALIZED = "CLOB_NOT_INITIALIZED"  # 404 or known empty response
    NO_ORDERBOOK = "NO_ORDERBOOK"                  # Explicit "no book" signal
    HTTP_ERROR = "HTTP_ERROR"                      # 5xx or connection error
    RATE_LIMITED = "RATE_LIMITED"                  # 429
    UNKNOWN = "UNKNOWN"


@dataclass
class CandidateReadiness:
    market_id: str
    token_id: str
    status: ReadinessStatus
    reason: Optional[NotReadyReason] = None
    http_status: Optional[int] = None
    detail: Optional[str] = None


class RateLimiter:
    """Simple token bucket or sleep-based limiter for probes."""
    def __init__(self, calls_per_second: float = 2.0):
        self.interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.time()


# Global limiter for probes
_PROBE_LIMITER = RateLimiter(calls_per_second=2.0)


def probe_clob_readiness(market_id: str, token_id: str) -> CandidateReadiness:
    """
    Probes CLOB readiness for a single candidate.
    Uses HEAD/GET on the book endpoint.
    """
    _PROBE_LIMITER.wait()
    
    # We use the existing fetch logic but catch errors to map to readiness
    # Using fetch_book from polymarket_fetch which does GET
    # We could optimize to HEAD if we implemented a specialized probe, 
    # but fetch_book is robust and what we use for trading.
    
    try:
        # We assume fetch_book raises PolymarketFetchError on failure
        # and returns a dict on success.
        book = fetch_book(token_id, timeout_s=4.0)
        
        # If we got a book, is it structurally valid?
        # Even an empty book is "initialized" enough to return 200, 
        # so we mark it READY. VenueBook parser will decide if it's NO_BBO later.
        if isinstance(book, dict):
             return CandidateReadiness(
                market_id=market_id,
                token_id=token_id,
                status=ReadinessStatus.READY
            )
        else:
            # Should not happen with fetch_book, but just in case
            return CandidateReadiness(
                market_id=market_id,
                token_id=token_id,
                status=ReadinessStatus.NOT_READY,
                reason=NotReadyReason.NO_ORDERBOOK,
                detail="Invalid response type"
            )

    except PolymarketFetchError as e:
        reason = NotReadyReason.UNKNOWN
        if e.status_code == 404:
            reason = NotReadyReason.NO_ORDERBOOK
        elif e.status_code == 429:
            reason = NotReadyReason.RATE_LIMITED
        elif e.status_code and 500 <= e.status_code < 600:
            reason = NotReadyReason.HTTP_ERROR
        # Map specific reasons from PolymarketFetchError string if needed
        # e.g. "TIMEOUT" -> HTTP_ERROR
        
        if "TIMEOUT" in str(e) or "CONNECTION_ERROR" in str(e):
            reason = NotReadyReason.HTTP_ERROR
            
        return CandidateReadiness(
            market_id=market_id,
            token_id=token_id,
            status=ReadinessStatus.NOT_READY,
            reason=reason,
            http_status=e.status_code,
            detail=str(e)
        )
    except Exception as e:
        return CandidateReadiness(
            market_id=market_id,
            token_id=token_id,
            status=ReadinessStatus.NOT_READY,
            reason=NotReadyReason.HTTP_ERROR,
            detail=f"Unexpected: {str(e)}"
        )


def discover_and_filter_candidates(max_candidates: int = 10) -> Dict[str, List[Any]]:
    """
    1. Discover candidates (via Gamma).
    2. Probe each for readiness.
    3. Return buckets: ready, not_ready.
    """
    candidates = discover_gamma_candidates(limit=max_candidates)
    
    ready = []
    not_ready = []
    
    # Simple cache to avoid reprobing same token_id in one run
    # (Though list should be unique usually)
    probed_tokens = set()

    for cand in candidates:
        # Expecting candidate to have 'market_id' and 'token_id' (or 'clobTokenIds')
        # We need to adapt based on what gamma_discovery returns.
        # Assuming cand is a dict with 'id' (market_id) and 'clobTokenIds' list.
        # For simple binary, we check the first token (YES) or we iterate?
        # Let's assume we want the YES token readiness.
        
        market_id = cand.get("id") or cand.get("market_id")
        
        # Handle different token structures
        token_id = None
        if "token_id" in cand:
            token_id = cand["token_id"]
        elif "clobTokenIds" in cand and isinstance(cand["clobTokenIds"], list) and len(cand["clobTokenIds"]) > 0:
            token_id = cand["clobTokenIds"][0] # Usually YES token
        
        if not market_id or not token_id:
             not_ready.append({
                "candidate": cand, 
                "reason": "MISSING_ID_OR_TOKEN"
            })
             continue

        if token_id in probed_tokens:
            continue
            
        result = probe_clob_readiness(market_id, token_id)
        probed_tokens.add(token_id)
        
        if result.status == ReadinessStatus.READY:
            # Enrich candidate with probing details if needed?
            # For now just pass the candidate object through
            ready.append(cand)
        else:
            not_ready.append({
                "candidate": cand,
                "readiness_detail": {
                    "status": result.status.value,
                    "reason": result.reason.value if result.reason else None,
                    "http_status": result.http_status,
                    "detail": result.detail
                }
            })
            
    return {"ready": ready, "not_ready": not_ready}
