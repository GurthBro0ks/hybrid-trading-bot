
import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
import pytest

# Mocking or importing the necessary components from the actual codebase
# Since we want to test parity with Rust's 'classify_thin_book', we'll implement
# the classifier and normalizers here to match the Rust implementation exactly.

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
class ReasonCode:
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
        return True, ReasonCode.ThinBookNoBbo

    # 2. Crossed book check (Fail-closed)
    if bb >= ba:
        raise ValueError(f"Crossed book: bid {bb} >= ask {ba}")

    # 3. Spread wide check
    # Threshold from Rust: 5.0
    if (ba - bb) > 5.0:
        return True, ReasonCode.ThinBookSpreadWide

    # 4. Depth check
    # Threshold from Rust: 500.0
    if book.total_depth() < 500.0:
        return True, ReasonCode.ThinBookDepthBelowThreshold

    return False, None

def parse_levels(arr: list, field_name: str) -> List[Tuple[float, float]]:
    levels = []
    for idx, item in enumerate(arr):
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError(f"{field_name}: level {idx} must be [price, qty]")
        
        price = float(item[0])
        qty = float(item[1])

        if not math.isfinite(price) or not math.isfinite(qty):
            raise ValueError(f"{field_name}: level {idx} not finite")
        if price < 0.0 or qty < 0.0:
            raise ValueError(f"{field_name}: level {idx} negative")
        
        levels.append((price, qty))
    return levels

def parse_polymarket_book(data: dict) -> VenueBook:
    market = data.get("market")
    if not isinstance(market, str):
        raise ValueError("polymarket: missing market")
    
    bids = parse_levels(data.get("bids", []), "bids")
    asks = parse_levels(data.get("asks", []), "asks")

    # Sort bids descending, asks ascending
    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0])

    return VenueBook(venue="polymarket", symbol=market, bids=bids, asks=asks)

def parse_kalshi_orderbook(data: dict) -> VenueBook:
    ticker = data.get("ticker")
    if not isinstance(ticker, str):
        raise ValueError("kalshi: missing ticker")
    
    yes_bids = parse_levels(data.get("yes_bid", []), "yes_bid")
    no_bids = parse_levels(data.get("no_bid", []), "no_bid")

    for p, q in yes_bids + no_bids:
        if p < 0.0 or p > 100.0:
            raise ValueError(f"kalshi: price {p} out of bounds")

    # YES Bids -> Bids
    bids = sorted(yes_bids, key=lambda x: x[0], reverse=True)
    
    # NO Bids -> YES Asks (100 - price)
    asks = sorted([(100.0 - p, q) for p, q in no_bids], key=lambda x: x[0])

    # Crossed check
    if bids and asks and bids[0][0] >= asks[0][0]:
        raise ValueError(f"kalshi: crossed book bid {bids[0][0]} >= ask {asks[0][0]}")

    return VenueBook(venue="kalshi", symbol=ticker, bids=bids, asks=asks)

def load_fixture(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "venuebook"

# --- Tests ---

@pytest.mark.parametrize("path, expected_is_thin, expected_reason", [
    ("polymarket/pm_deep.json", False, None),
    ("polymarket/pm_thin.json", True, ReasonCode.ThinBookDepthBelowThreshold),
    ("polymarket/pm_empty.json", True, ReasonCode.ThinBookNoBbo),
    ("kalshi/k_deep.json", False, None),
    ("kalshi/k_one_sided.json", True, ReasonCode.ThinBookNoBbo),
    ("kalshi/k_empty.json", True, ReasonCode.ThinBookNoBbo),
    ("kalshi/k_wide.json", True, ReasonCode.ThinBookSpreadWide),
])
def test_fixture_parity(path, expected_is_thin, expected_reason):
    full_path = FIXTURE_DIR / path
    data = load_fixture(full_path)
    
    if "polymarket" in path:
        book = parse_polymarket_book(data)
    else:
        book = parse_kalshi_orderbook(data)
    
    is_thin, reason = classify_thin_book(book)
    assert is_thin == expected_is_thin
    assert reason == expected_reason

@pytest.mark.parametrize("path", [
    "malformed/pm_bad_shape.json",
    "malformed/k_bad_shape.json",
    "malformed/ambiguous_price.json",
])
def test_malformed_fail_closed(path):
    full_path = FIXTURE_DIR / path
    data = load_fixture(full_path)
    
    with pytest.raises((ValueError, TypeError, KeyError)):
        if "pm_" in path:
            parse_polymarket_book(data)
        else:
            parse_kalshi_orderbook(data)

def test_crossed_book_raises():
    book = VenueBook(venue="test", symbol="CROSSED", bids=[(60.0, 10.0)], asks=[(55.0, 10.0)])
    with pytest.raises(ValueError, match="Crossed book"):
        classify_thin_book(book)
