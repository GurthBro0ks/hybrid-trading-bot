from sources.resolution_source import parse_rules_text

def test_parse_coinbase_btc():
    txt = "Resolved by the Coinbase BTC/USD spot price"
    src = parse_rules_text(txt)
    assert src.venue == "coinbase"
    assert src.symbol == "BTC/USD"
    assert "gemini" in src.allowed_fallbacks

def test_parse_gemini_eth():
    txt = "Resolved by the Gemini ETH-USD spot price"
    src = parse_rules_text(txt)
    assert src.venue == "gemini"
    assert src.symbol == "ETH/USD" # logic normalizes - to / potentially? Let's check impl.
    # _normalize_symbol "base/quote".
    # Regex groups: ([A-Z0-9]+) [/-]? ([A-Z0-9]+)
    # so "ETH-USD" -> group1=ETH, group2=USD -> ETH/USD. Correct.

def test_parse_kalshi_style_variation():
    txt = "Resolved by the Coinbase BTC-USD spot price daily close"
    src = parse_rules_text(txt)
    assert src.venue == "coinbase"
    assert src.symbol == "BTC/USD"
