
import math
from typing import List, Tuple
from shared.venue_book import VenueBook

def parse_levels(arr: list, field_name: str) -> List[Tuple[float, float]]:
    levels = []
    if not isinstance(arr, list):
         raise ValueError(f"{field_name}: must be a list")
    for idx, item in enumerate(arr):
        if isinstance(item, dict):
             # Live API format: {"price": "0.1", "size": "100"}
             try:
                 price = float(item.get("price", 0))
                 qty = float(item.get("size", 0))
             except (ValueError, TypeError):
                 raise ValueError(f"{field_name}: level {idx} price/size must be numeric")
        elif isinstance(item, list) and len(item) == 2:
            # Fixture format: [price, qty]
            try:
                price = float(item[0])
                qty = float(item[1])
            except (ValueError, TypeError):
                 raise ValueError(f"{field_name}: level {idx} price/qty must be numeric")
        else:
            raise ValueError(f"{field_name}: level {idx} invalid shape")
        
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
