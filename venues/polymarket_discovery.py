"""
Polymarket Discovery
Lightweight wrapper around polymarket.clob_readiness for backward compatibility.
"""

import logging
from typing import Dict, Any

from polymarket.clob_readiness import (
    ReadinessStatus,
    FailureReason,
    SelectionResult,
    select_best_clob_candidate,
    discover_gamma_candidates,
    probe_clob_readiness,
    parse_gamma_yes_no_tokens,
    _is_market_eligible
)

# Aliases for backward compatibility with tests
NotReadyReason = FailureReason
CandidateReadiness = SelectionResult

logger = logging.getLogger("pm_discovery")

def discover_and_filter_candidates(max_candidates: int = 20) -> Dict[str, Any]:
    """
    Legacy wrapper to maintain compatibility with verify_shadow_pipeline.py.
    Returns dict format with 'ready' and 'not_ready' buckets.
    """
    sel = select_best_clob_candidate(max_probes=max_candidates)
    
    if sel.readiness_status == ReadinessStatus.READY:
        # Construct a synthetic candidate object that looks like what callers expect
        cand = {
            "id": sel.selected_market_id,
            "token_id": sel.selected_token_id,
            "clobTokenIds": [sel.selected_token_id, sel.meta.get("no_token_id")] if sel.meta.get("no_token_id") else [sel.selected_token_id],
            **sel.meta.get("gamma_data", {})
        }
        return {"ready": [cand], "not_ready": []}
    else:
        # We fill 'not_ready' with a dummy if needed, or just return empty
        return {
            "ready": [], 
            "not_ready": [{"reason": sel.failure_reason.name if sel.failure_reason else "UNKNOWN"}]
        }
