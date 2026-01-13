
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Level:
    price: float
    qty: float

@dataclass
class VenueBook:
    venue: str
    symbol: str
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]
    ts_ms: Optional[int] = None

    def best_bid(self) -> Optional[float]:
        return self.bids[0][0] if self.bids else None

    def best_ask(self) -> Optional[float]:
        return self.asks[0][0] if self.asks else None

    def spread(self) -> Optional[float]:
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return None
        return ba - bb

    def total_depth(self) -> float:
        return sum(q for p, q in self.bids) + sum(q for p, q in self.asks)

# Canonical Reason Codes from Rust/Project standards
class VenueBookReason:
    ThinBookNoBbo = "ThinBookNoBbo"
    ThinBookDepthBelowThreshold = "ThinBookDepthBelowThreshold"
    ThinBookSpreadWide = "ThinBookSpreadWide"

def classify_thin_book(book: VenueBook) -> Tuple[bool, Optional[str]]:
    """
    Python implementation of engine-rust's classify_thin_book.
    Must match Rust logic exactly.
    """
    bb = book.best_bid()
    ba = book.best_ask()

    # 1. NO_BBO check
    if bb is None or ba is None:
        return True, VenueBookReason.ThinBookNoBbo

    # 2. Crossed book check (Fail-closed)
    if bb >= ba:
        raise ValueError(f"Crossed book: bid {bb} >= ask {ba}")

    # 3. Spread wide check
    # Threshold from Rust: 5.0 (for 0-100 scales)
    # Note: Polymarket is 0-1, so we might need to scale or adjust if this is used for Polymarket.
    # However, the user said "parity-locked", so we keep it as is from the test.
    if (ba - bb) > 5.0:
        return True, VenueBookReason.ThinBookSpreadWide

    # 4. Depth check
    # Threshold from Rust: 500.0
    if book.total_depth() < 500.0:
        return True, VenueBookReason.ThinBookDepthBelowThreshold

    return False, None
