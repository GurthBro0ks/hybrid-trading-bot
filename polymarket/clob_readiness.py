import logging
import requests
import time
import random
import json
import os
from typing import Tuple, Optional, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

from polymarket.contract import ReadinessStatus, FailureReason, cache_ttl_for, is_retryable

# Configure logger
logger = logging.getLogger(__name__)

# Constants
CLOB_URL_BASE = "https://clob.polymarket.com"
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.25
MAX_BACKOFF_SECONDS = 2.0
MAX_PROBES_PER_RUN = 20
DEFAULT_MAX_PROBES = 20
MIN_HOURS_TO_EXPIRY = 24

# In-memory cache: string -> (timestamp, result_tuple)
_probe_cache: Dict[str, Tuple[float, Any]] = {}

@dataclass
class ProbeResult:
    status: ReadinessStatus
    reason: FailureReason
    meta: Dict[str, Any]

    def __iter__(self):
        return iter((self.status, self.reason, self.meta))

@dataclass
class SelectionResult:
    selected_market_id: Optional[str] = None
    selected_token_id: Optional[str] = None
    readiness_status: ReadinessStatus = ReadinessStatus.NOT_READY
    failure_reason: FailureReason = FailureReason.NO_READY_CANDIDATES
    meta: Dict[str, Any] = None
    probes_attempted: int = 0
    skipped_count: int = 0

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

    def __iter__(self):
        # Compatibility with legacy discovery which returned (ready_list, not_ready_list)
        # Wait, discover_and_filter_candidates used to return a DICT, not a tuple.
        # But some internal functions might have returned tuples.
        # For now, let's just support unpacking the core fields if needed.
        return iter((self.selected_market_id, self.selected_token_id, self.readiness_status, self.failure_reason, self.meta))

    @property
    def status(self):
        """Compatibility property for legacy tests."""
        return self.readiness_status

    @property
    def reason(self):
        """Compatibility property for legacy tests."""
        return self.failure_reason

def parse_gamma_yes_no_tokens(market_obj: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str], FailureReason]:
    """
    Parses a Gamma market object to extract YES/NO clobTokenIds safely.
    Strict fail-closed logic: any ambiguity or malformed data returns failure.
    
    Args:
        market_obj: Dictionary representing a market from Gamma.
        
    Returns:
        (success, yes_token_id, no_token_id, reason)
        If success is False, yes_token_id and no_token_id will be None.
    """
    try:
        # 1. Parse fields if they are JSON strings
        raw_outcomes = market_obj.get("outcomes")
        raw_token_ids = market_obj.get("clobTokenIds")
        
        if isinstance(raw_outcomes, str):
            outcomes = json.loads(raw_outcomes)
        else:
            outcomes = raw_outcomes
            
        if isinstance(raw_token_ids, str):
            token_ids = json.loads(raw_token_ids)
        else:
            token_ids = raw_token_ids

        # 2a. Validate types for outcomes
        if outcomes is None:
             return False, None, None, FailureReason.GAMMA_PARSE_ERROR

        if not isinstance(outcomes, list):
             return False, None, None, FailureReason.GAMMA_PARSE_ERROR

        # 2b. Validate token_ids specifically for "missing" error
        if token_ids is None:
             return False, None, None, FailureReason.MISSING_CLOB_TOKEN_IDS
             
        if not isinstance(token_ids, list):
             return False, None, None, FailureReason.GAMMA_PARSE_ERROR

        # 3. Check emptiness
        if not outcomes:
             return False, None, None, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE
             
        if not token_ids:
            return False, None, None, FailureReason.MISSING_CLOB_TOKEN_IDS

        # 4. Check length match
        if len(outcomes) != len(token_ids):
             return False, None, None, FailureReason.OUTCOME_TOKEN_LENGTH_MISMATCH
             
        # 5. Check exactly 2 outcomes (Binary)
        if len(outcomes) != 2:
             return False, None, None, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE
             
        # 6. Check for Yes/No existence (case-insensitive for safety)
        yes_idx = -1
        no_idx = -1
        
        for i, outcome in enumerate(outcomes):
            if not isinstance(outcome, str):
                 return False, None, None, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE
            
            s_out = outcome.strip().lower()
            if s_out == "yes":
                yes_idx = i
            elif s_out == "no":
                no_idx = i
                
        if yes_idx == -1 or no_idx == -1:
             return False, None, None, FailureReason.UNSUPPORTED_OUTCOMES_SHAPE
             
        # 7. Extract Token IDs
        yes_token = token_ids[yes_idx]
        no_token = token_ids[no_idx]
        
        # 8. Validate Token IDs are strings or convertible strings
        if not isinstance(yes_token, (str, int)) or not isinstance(no_token, (str, int)):
             return False, None, None, FailureReason.INVALID_TOKEN_ID
             
        return True, str(yes_token), str(no_token), FailureReason.OK

    except (json.JSONDecodeError, ValueError, TypeError):
        return False, None, None, FailureReason.GAMMA_PARSE_ERROR
    except Exception:
        return False, None, None, FailureReason.GAMMA_PARSE_ERROR

def sanitize_token_id(token_id: Any) -> str:
    """Returns a safe suffix of the token_id for logging."""
    if not token_id:
        return "None"
    s_token = str(token_id)
    if len(s_token) >= 6:
        return s_token[-6:]
    return s_token

def sanitize_market_id(market_id: Any) -> str:
    """Returns a safe string of the market_id for logging."""
    if not market_id:
        return "None"
    return str(market_id)

def probe_clob_readiness(token_id: str) -> ProbeResult:
    """
    Probes the Polymarket CLOB for orderbook readiness for a given token_id.
    
    Args:
        token_id: The token ID to probe.
        
    Returns:
        ProbeResult object.
    """
    
    # Check cache first
    cached_result = _get_from_cache(token_id)
    if cached_result:
        return ProbeResult(*cached_result)

    # Sanitize token_id for logging
    token_suffix = sanitize_token_id(token_id)
    
    status = ReadinessStatus.NOT_READY
    reason = FailureReason.NOT_FOUND_UNKNOWN
    meta = {}
    
    url = f"{CLOB_URL_BASE}/midpoint"
    params = {"token_id": token_id}
    
    for attempt in range(MAX_RETRIES + 1):
        try:
             # Check for fixture mode via env
            if os.environ.get("POLYMARKET_FIXTURE_MODE") == "1":
                 return _probe_clob_fixtures(token_id)

            resp = requests.get(url, params=params, timeout=5)
            
            # READY: 200 OK + payload has 'mid'
            if resp.status_code == 200:
                data = resp.json()
                if "mid" in data:
                    status = ReadinessStatus.READY
                    reason = FailureReason.OK
                    _log_probe(token_suffix, resp.status_code, status, reason)
                    _add_to_cache(token_id, (status, reason, meta), status, reason)
                    return ProbeResult(status, reason, meta)
                else:
                    # 200 but weird payload
                    status = ReadinessStatus.NOT_READY
                    reason = FailureReason.CLOB_INVALID_PAYLOAD
                    _log_probe(token_suffix, resp.status_code, status, reason)
                    _add_to_cache(token_id, (status, reason, meta), status, reason)
                    return ProbeResult(status, reason, meta)

            # NOT_READY: 404
            elif resp.status_code == 404:
                try:
                    err_data = resp.json()
                    err_msg = err_data.get("error", "") or err_data.get("message", "")
                except ValueError:
                    err_msg = resp.text

                if "No orderbook exists" in str(err_msg):
                    status = ReadinessStatus.NOT_READY
                    reason = FailureReason.CLOB_NO_ORDERBOOK
                else:
                    status = ReadinessStatus.NOT_READY
                    reason = FailureReason.NOT_FOUND_UNKNOWN

                _log_probe(token_suffix, resp.status_code, status, reason)
                _add_to_cache(token_id, (status, reason, meta), status, reason)
                return ProbeResult(status, reason, meta)

            # NONRETRYABLE: 400
            elif resp.status_code == 400:
                status = ReadinessStatus.NOT_READY
                reason = FailureReason.INVALID_TOKEN_ID
                _log_probe(token_suffix, resp.status_code, status, reason)
                _add_to_cache(token_id, (status, reason, meta), status, reason)
                return ProbeResult(status, reason, meta)
            
            # RETRYABLE: 429, 5XX
            elif resp.status_code in [429, 500, 502, 503, 504]:
                if attempt < MAX_RETRIES:
                    _backoff(attempt)
                    continue
                else:
                    status = ReadinessStatus.RETRYABLE_ERROR
                    if resp.status_code == 429:
                        reason = FailureReason.CLOB_RATE_LIMITED
                    else:
                        reason = FailureReason.CLOB_5XX
                    
                    _log_probe(token_suffix, resp.status_code, status, reason)
                    _add_to_cache(token_id, (status, reason, meta), status, reason)
                    return ProbeResult(status, reason, meta)
            
            # Other codes?
            else:
                 status = ReadinessStatus.RETRYABLE_ERROR
                 reason = FailureReason.CLOB_UNKNOWN_ERROR
                 _log_probe(token_suffix, resp.status_code, status, reason)
                 _add_to_cache(token_id, (status, reason, meta), status, reason)
                 return ProbeResult(status, reason, meta)

        except (requests.exceptions.RequestException, TimeoutError):
            if attempt < MAX_RETRIES:
                _backoff(attempt)
                continue
            else:
                status = ReadinessStatus.RETRYABLE_ERROR
                reason = FailureReason.CLOB_TIMEOUT
                _log_probe(token_suffix, "ERR", status, reason)
                _add_to_cache(token_id, (status, reason, meta), status, reason)
                return ProbeResult(status, reason, meta)

    # Fallback
    return ProbeResult(ReadinessStatus.NOT_READY, FailureReason.CLOB_UNKNOWN_ERROR, {})


def _probe_clob_fixtures(token_id: str) -> ProbeResult:
    """Helper for offline probe results based on fixtures."""
    # Simple mapping for verify_shadow_pipeline.py and tests
    s_token = str(token_id).lower()
    if "ready" in s_token or s_token == "1111":
         return ProbeResult(ReadinessStatus.READY, FailureReason.OK, {"mid": "0.5"})
    elif "rate" in s_token:
         return ProbeResult(ReadinessStatus.RETRYABLE_ERROR, FailureReason.CLOB_RATE_LIMITED, {})
    elif "none" in s_token or "not" in s_token or "404" in s_token:
         return ProbeResult(ReadinessStatus.NOT_READY, FailureReason.CLOB_NO_ORDERBOOK, {})
    
    return ProbeResult(ReadinessStatus.READY, FailureReason.OK, {"mid": "0.5"})


def _backoff(attempt: int):
    """Sleeps with exponential backoff and jitter."""
    sleep_time = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2 ** attempt))
    jitter = random.uniform(0, 0.1 * sleep_time)
    time.sleep(sleep_time + jitter)

def _log_probe(token_suffix: str, http_code: Any, status: ReadinessStatus, reason: FailureReason):
    """Logs a single line summary of the probe (token_id suffix only, no URLs)."""
    logger.info(f"CLOB_PROBE | token: ...{token_suffix} | code: {http_code} | status: {status.name} | reason: {reason.name}")

def _add_to_cache(token_id: str, result: Tuple[ReadinessStatus, FailureReason, Dict], status: ReadinessStatus, reason: FailureReason):
    """Adds a result to the cache with a TTL derived from status/reason."""
    ttl = cache_ttl_for(reason, status)
    expiry = time.time() + ttl
    _probe_cache[token_id] = (expiry, result)

def _get_from_cache(token_id: str) -> Optional[Tuple[ReadinessStatus, FailureReason, Dict]]:
    """Retrieves a result from cache if valid."""
    if token_id in _probe_cache:
        expiry, result = _probe_cache[token_id]
        if time.time() < expiry:
            return result
        else:
            del _probe_cache[token_id]
    return None


def discover_gamma_candidates(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches active markets from Polymarket Gamma API.
    """
    if os.environ.get("POLYMARKET_FIXTURE_MODE") == "1":
         # Load from gamma_ready_candidate.json
         fix_path = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "polymarket" / "gamma_ready_candidate.json"
         if fix_path.exists():
             with open(fix_path, 'r') as f:
                 return [json.load(f)]
         return []

    url = f"https://gamma-api.polymarket.com/markets?active=true&closed=false&limit={limit}&offset=0"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Gamma discovery failed: {resp.status_code}")
            return []
        return resp.json()
    except Exception as e:
        logger.error(f"Gamma discovery error: {e}")
        return []


def _is_market_eligible(m: Dict[str, Any]) -> Tuple[bool, FailureReason]:
    """Strict eligibility filters for a candidate market."""
    if not m.get("enableOrderBook"):
        return False, FailureReason.ORDERBOOK_DISABLED
    if not m.get("acceptingOrders"):
        return False, FailureReason.NOT_ACCEPTING_ORDERS
    if m.get("closed"):
        return False, FailureReason.MARKET_FILTERED_OUT
    if m.get("restricted"):
        return False, FailureReason.RESTRICTED
    
    end_date_str = m.get("endDateIso")
    if not end_date_str:
        return False, FailureReason.NO_END_DATE
    
    try:
        dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if dt < now + timedelta(hours=MIN_HOURS_TO_EXPIRY):
             return False, FailureReason.EXPIRING_SOON
    except ValueError:
        return False, FailureReason.BAD_DATE_FORMAT

    return True, FailureReason.OK


def select_best_clob_candidate(max_probes: int = DEFAULT_MAX_PROBES) -> SelectionResult:
    """
    Main pipeline to select a trading candidate.
    """
    result = SelectionResult()
    
    candidates = discover_gamma_candidates(limit=100)
    if not candidates:
        result.readiness_status = ReadinessStatus.NOT_READY
        result.failure_reason = FailureReason.EXHAUSTED_PROBES_OR_CANDIDATES
        return result
        
    filtered_candidates = []
    
    for m in candidates:
        eligible, reason = _is_market_eligible(m)
        if eligible:
            filtered_candidates.append(m)
        else:
            result.skipped_count += 1
            
    if not filtered_candidates:
        result.readiness_status = ReadinessStatus.NOT_READY
        result.failure_reason = FailureReason.MARKET_FILTERED_OUT
        return result
        
    def get_sort_key(m):
        liq = float(m.get("liquidityNum") or 0)
        vol = float(m.get("volume24hr") or 0)
        return (liq, vol)
        
    filtered_candidates.sort(key=get_sort_key, reverse=True)
    
    probes_left = max_probes
    
    for m in filtered_candidates:
        if probes_left <= 0:
            break
            
        probes_left -= 1
        result.probes_attempted += 1
        
        success, yes_token, no_token, parse_reason = parse_gamma_yes_no_tokens(m)
        if not success:
            continue
            
        target_token = yes_token
        status, reason, meta = probe_clob_readiness(target_token)
        
        if status == ReadinessStatus.READY:
            result.selected_market_id = m.get("id")
            result.selected_token_id = target_token
            result.readiness_status = ReadinessStatus.READY
            result.failure_reason = FailureReason.OK
            result.meta = {
                "no_token_id": no_token,
                "gamma_data": {k: m.get(k) for k in ["question", "slug"]},
                "probe_meta": meta
            }
            return result
        
    result.readiness_status = ReadinessStatus.NOT_READY
    result.failure_reason = FailureReason.NO_READY_CANDIDATES
    return result
