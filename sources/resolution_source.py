"""Resolution source resolver for market rules/metadata."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Optional


@dataclass(frozen=True)
class ResolutionSource:
    venue: str
    symbol: str
    endpoint_type: str
    allowed_fallbacks: list[str]


UNKNOWN = ResolutionSource("unknown", "", "unknown", [])

_BINANCE_SPOT_RE = re.compile(
    r"\bBinance\s+([A-Z0-9]{2,10})\s*/\s*([A-Z0-9]{2,10})\b",
    re.IGNORECASE,
)

# Kalshi often phrasing: "Resolved by ... Coinbase ... BTC/USD" or similar.
# We need to be permissive enough for known formats but strict on the venue/symbol.
# Example: "Resolved by the Coinbase BTC/USD spot price"
# Example: "Resolved by the Gemini BTC/USD spot price"
_COINBASE_SPOT_RE = re.compile(
    r"\bCoinbase\s+([A-Z0-9]{2,10})\s*[/-]?\s*([A-Z0-9]{2,10})\b",
    re.IGNORECASE,
)
_GEMINI_SPOT_RE = re.compile(
    r"\bGemini\s+([A-Z0-9]{2,10})\s*[/-]?\s*([A-Z0-9]{2,10})\b",
    re.IGNORECASE,
)


def _normalize_symbol(base: str, quote: str) -> str:
    return f"{base.upper()}/{quote.upper()}"


def parse_rules_text(rules_text: str) -> ResolutionSource:
    # Coinbase
    match = _COINBASE_SPOT_RE.search(rules_text or "")
    if match:
        base, quote = match.group(1), match.group(2)
        return ResolutionSource(
            venue="coinbase",
            symbol=_normalize_symbol(base, quote),
            endpoint_type="spot",
            allowed_fallbacks=["gemini", "binance"],
        )

    # Gemini
    match = _GEMINI_SPOT_RE.search(rules_text or "")
    if match:
        base, quote = match.group(1), match.group(2)
        return ResolutionSource(
            venue="gemini",
            symbol=_normalize_symbol(base, quote),
            endpoint_type="spot",
            allowed_fallbacks=["coinbase", "binance"],
        )

    # Binance
    match = _BINANCE_SPOT_RE.search(rules_text or "")
    if match:
        base, quote = match.group(1), match.group(2)
        return ResolutionSource(
            venue="binance",
            symbol=_normalize_symbol(base, quote),
            endpoint_type="spot",
            allowed_fallbacks=[],
        )
    return UNKNOWN


def resolution_source_from_metadata(metadata: Dict[str, str]) -> ResolutionSource:
    rules_text = (
        metadata.get("resolution_rules")
        or metadata.get("rules_text")
        or metadata.get("rules")
        or ""
    )
    if rules_text:
        return parse_rules_text(rules_text)
    return UNKNOWN


def is_unknown(source: ResolutionSource) -> bool:
    return source.venue == "unknown"


def _self_test() -> None:
    sample = "Resolved by Binance BTC/USDT spot price"
    source = parse_rules_text(sample)
    assert source.venue == "binance"
    assert source.symbol == "BTC/USDT"
    assert source.endpoint_type == "spot"
    assert not source.allowed_fallbacks
    assert is_unknown(parse_rules_text("Unknown"))


if __name__ == "__main__":
    _self_test()
    print("resolution_source: self-test ok")
