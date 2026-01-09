# Verification Log - Phase 2.2 (RealWS + Soak)

## Execution Context

- **Date**: Fri Jan  9 12:52:38 PM UTC 2026
- **Git HEAD**: `5294075b463454c5ae49cbc497cd6124ef7e90f3`

## Healthcheck Output

```
[health] time: 2026-01-09T12:52:38+00:00
[health] db: /opt/hybrid-trading-bot/data/bot.db
...
[health] PASS
```

## RealWS Ingestion Verification

**Command**: `./target/debug/engine-rust --mode shadow --ingest realws --seconds 20`
**Source**: Gemini (Binance blocked)

**Logs**:

```
{"timestamp":"2026-01-09T12:59:21.542088Z","level":"INFO","fields":{"message":"ingest task started","mode":"REAL_WS"},"target":"engine_rust::ingest::realws"}
{"timestamp":"2026-01-09T12:59:21.543114Z","level":"INFO","fields":{"message":"connecting...","source":"gemini_btcusd","url":"wss://api.gemini.com/v1/marketdata/btcusd"},"target":"engine_rust::ingest::realws"}
{"timestamp":"2026-01-09T12:59:21.775576Z","level":"INFO","fields":{"message":"connected","source":"gemini_btcusd"},"target":"engine_rust::ingest::realws"}
{"timestamp":"2026-01-09T12:59:28.547656Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
```

## Fixtures

Captured 50 frames to `tests/fixtures/realws_frames_generic.jsonl`.
