from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BookStatus(Enum):
    OK = "OK"
    NO_TRADE = "NO_TRADE"


class BookFailReason(Enum):
    NO_BBO = "NO_BBO"
    DEPTH_BELOW_THRESHOLD = "DEPTH_BELOW_THRESHOLD"
    SPREAD_WIDE = "SPREAD_WIDE"
    BOOK_UNAVAILABLE = "BOOK_UNAVAILABLE"
    PARSE_AMBIGUOUS = "PARSE_AMBIGUOUS"


@dataclass(frozen=True)
class VenueBook:
    venue: str
    ts: float
    best_bid: Optional[float]
    best_ask: Optional[float]
    depth_qty_total: float
    depth_notional_total_usd: Optional[float]
    status: BookStatus
    fail_reason: Optional[BookFailReason]
    raw: Optional[dict] = None

    def to_json_dict(self) -> dict:
        payload = {
            "venue": self.venue,
            "ts": float(self.ts),
            "best_bid": float(self.best_bid) if self.best_bid is not None else None,
            "best_ask": float(self.best_ask) if self.best_ask is not None else None,
            "depth_qty_total": float(self.depth_qty_total),
            "depth_notional_total_usd": (
                float(self.depth_notional_total_usd)
                if self.depth_notional_total_usd is not None
                else None
            ),
            "status": self.status.name,
            "fail_reason": self.fail_reason.name if self.fail_reason is not None else None,
        }
        if self.raw is not None:
            payload["raw"] = self.raw
        return payload
