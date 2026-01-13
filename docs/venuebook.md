## VenueBook contract
- Required JSON keys: venue, ts, best_bid, best_ask, depth_qty_total, status, fail_reason.
- Optional keys: depth_notional_total_usd, raw.
- status is a string enum: OK or NO_TRADE.
- fail_reason is null or a BookFailReason enum name.
- best_bid/best_ask are numbers when status=OK, null when status=NO_TRADE.
- depth_qty_total is always numeric (0.0 allowed); ts is numeric epoch seconds.

## Env overrides
- Polymarket: PM_DEPTH_QTY_MIN, PM_SPREAD_MAX (validated at import; invalid => hard fail).
- Kalshi base URL: KALSHI_API_BASE (default https://trading-api.kalshi.com).
- Kalshi: KALSHI_DEPTH_NOTIONAL_MIN / K_DEPTH_NOTIONAL_MIN, KALSHI_SPREAD_MAX / K_SPREAD_MAX (validated at import; invalid => hard fail).
- These thresholds only affect NO_TRADE gating; ambiguous parse always fails closed (PARSE_AMBIGUOUS).
