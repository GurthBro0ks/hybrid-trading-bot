## Phase 4: Verification Proofs
### Proof 1: PSI Integrity
```
2026-01-09T15:06:06.342322Z	STARTUP		
2026-01-09T15:06:06.431069Z	ENGINE_RESTART	55.91	some avg10=55.91 avg60=55.68 avg300=53.05 total=387140017927
```
### Proof 5: Throttling Reduction
```
Rate@1 (20s delta): 42 ticks
Rate@10 (20s delta): 4 ticks
```
### Proof 2: Stall Detection
### Proof 3: Typed Exit Codes
```
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-01-09 15:09:05 UTC; 5s ago
   Main PID: 1642702 (engine-rust)
      Tasks: 8 (limit: 18964)
     Memory: 4.5M (peak: 4.5M)
        CPU: 47ms
     CGroup: /system.slice/hybrid-engine.service
             └─1642702 /opt/hybrid-trading-bot/engine-rust/target/debug/engine-rust

Jan 09 15:09:05 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:05.695421Z","level":"INFO","fields":{"message":"persist task started (dedicated, non-blocking - I6)","batch_size":100,"flush_interval_ms":1000},"target":"engine_rust::persist"}
Jan 09 15:09:05 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:05.696409Z","level":"INFO","fields":{"message":"HEARTBEAT (G4)","tick_count":0,"signal_count":0,"shadow_orders":0,"trade_count":0,"persist_count":0,"persist_errors":0,"bp_drops_tick":0,"bp_drops_signal":0,"bp_drops_persist":0,"risk_vetoes":0},"target":"engine_rust"}
Jan 09 15:09:05 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:05.698054Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 15:09:06 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:06.696882Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 15:09:07 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:07.697783Z","level":"INFO","fields":{"message":"batch flushed","persisted":2,"errors":0},"target":"engine_rust::persist"}
Jan 09 15:09:08 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:08.697844Z","level":"INFO","fields":{"message":"batch flushed","persisted":3,"errors":0},"target":"engine_rust::persist"}
Jan 09 15:09:09 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:09.696847Z","level":"INFO","fields":{"message":"batch flushed","persisted":1,"errors":0},"target":"engine_rust::persist"}
Jan 09 15:09:10 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:10.196391Z","level":"INFO","fields":{"message":"signal generated","event_id":"0926acaf-39ba-410d-a392-4535291e99e4","symbol":"SOL/USDC","side":"SELL","reason_code":"PERIODIC_TRIGGER","confidence":0.75,"desired_size":0.1,"tick_count":10},"target":"engine_rust::strategy"}
Jan 09 15:09:10 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:10.196550Z","level":"INFO","fields":{"message":"shadow order executed (I1: no network call)","order_id":"7cbee940-970f-40e5-adb5-9cab6e2050a7","signal_id":"0926acaf-39ba-410d-a392-4535291e99e4","symbol":"SOL/USDC","side":"SELL","qty":0.1,"fill_price":100.0,"fees":0.01,"reason_code":"SHADOW_RECORDED","is_shadow":true},"target":"engine_rust::execution"}
Jan 09 15:09:10 slimy-nuc1 engine-rust[1642702]: {"timestamp":"2026-01-09T15:09:10.708344Z","level":"INFO","fields":{"message":"batch flushed","persisted":6,"errors":0},"target":"engine_rust::persist"}
```
### Proof 4: Concurrency
```
]633;E;for i in {1..5}\x3b do sqlite3 data/bot.db "SELECT COUNT(*), MAX(ts) FROM ticks\x3b"\x3b sleep 1\x3b done >> docs/buglog/BUG_2026-01-09_phase2_2_1_reliability_metric_integrity.md 2>&1;018bdd6f-fd42-40d0-934c-abc224b8e4db]633;C148052|1767971350
148054|1767971351
148055|1767971352
148058|1767971353
148059|1767971354
```
