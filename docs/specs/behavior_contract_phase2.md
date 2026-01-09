# Behavior Contract — Phase 2 Rust Backend (Ingest → Strategy → Execute → Persist)

Status: DRAFT v0.1 (Shadow-First)

This contract defines the exact behaviors the Rust backend must exhibit in Phase 2:

- Asynchronous Tokio runtime with separate tasks and channel communication.
- Market data ingestion via WebSocket (tokio-tungstenite).
- Strategy generates Signal events.
- Execution processes Signals (SHADOW/PAPER default; LIVE gated).
- Persistence is a dedicated async task writing to SQLite via SQLx.
(Architecture basis: task pipeline + ports/adapters + SQLx + WebSocket robustness.):contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}

---

## 0) Definitions

### Execution Modes

- SHADOW_MODE: Never sends real orders. Records “shadow orders” and simulated outcomes only.
- PAPER_MODE: Uses an execution simulator (fills modeled) but still never calls real exchange execution endpoints.
- LIVE_MODE: Real execution adapter enabled. Must be explicitly unlocked (see Gate G1).

### Core Events

- Tick: normalized market update (symbol, price, volume, timestamp).
- Signal: strategy output (symbol, side, confidence, reason, timestamp, desired size).
- Order: execution state machine record (submitted/ack/partial/filled/canceled/rejected).
- Trade: realized fill(s) for an order.

### Ports (Hexagonal)

- MarketDataStream (input): how ticks enter the system.
- OrderExecution (output): how orders are placed/canceled.
- Persistence (output): how data is stored.
(Adapters swap exchanges/DB without touching core logic.):contentReference[oaicite:4]{index=4}

---

## 1) Non-Negotiable Invariants (Must Always Hold)

I1 — Shadow safety

- In SHADOW_MODE and PAPER_MODE: 0 calls to real OrderExecution network endpoints.

I2 — Risk caps (configurable, default conservative)

- Total open exposure <= MAX_EXPOSURE_USD
- Per-symbol exposure <= MAX_SYMBOL_EXPOSURE_USD
- Max open orders <= MAX_OPEN_ORDERS
- If a new Signal would violate caps → veto with reason RISK_CAP.

I3 — Idempotency

- Re-processing the same Tick/Signal/Execution event (same event_id) does not change final state.

I4 — Accounting conservation

- For every filled Trade:
  cash_delta + position_delta * fill_price + fees == 0 (within rounding rules)
- No “phantom PnL”: all PnL must derive from persisted fills.

I5 — Storage performance + concurrency baseline

- SQLite must run in WAL mode and apply PRAGMAs at startup:
  - PRAGMA journal_mode=WAL
  - PRAGMA synchronous=NORMAL
  - PRAGMA busy_timeout >= 1000ms
  - PRAGMA temp_store=MEMORY
(Required to allow concurrent readers + writer and avoid lock-crash behavior.):contentReference[oaicite:5]{index=5}:contentReference[oaicite:6]{index=6}

I6 — Trading loop is never blocked by disk I/O

- Persistence happens in a dedicated task; strategy/execution must not wait on DB writes.

I7 — System health under CPU contention

- Given Minecraft (mc-paper.service) and pnpm development are active on the same NUC
- When CPU load is elevated and multiple services compete for resources
- Then healthcheck.sh must return PASS within timeout (< 30s)
- And dashboard HTTP remains responsive
- And SQLite WAL writes do not block (busy_timeout honored)
(Requirement: CPU cage (systemd cgroup CPUQuota) must prevent Minecraft from starving bot services.)

---

## 2) “Must Never Do” Limits

L1 — Must never place LIVE trades unless Gate G1 is satisfied.
L2 — Must never trade on stale data (see S7).
L3 — Must never crash the whole process due to a single malformed message or DB lock.
L4 — Must never silently swallow an execution error: every failure is logged + persisted.

---

## 3) Phase 2 Runtime Responsibilities (Task Pipeline)

The Rust backend is composed of these Tokio tasks:

1) Ingestion Task: connects to WebSocket and produces normalized Tick events.
2) Strategy Task: consumes Tick stream and produces Signal events.
3) Execution Task: consumes Signals and manages order state via OrderExecution port.
4) Persistence Task: batches and writes Ticks/Signals/Orders/Trades asynchronously.
(Exact pipeline described in the plan.):contentReference[oaicite:7]{index=7}:contentReference[oaicite:8]{index=8}

---

## 4) Database Requirements (SQLite + SQLx)

Schema must support time-series queries:

- ticks table (indexed on timestamp)
- signals table
- orders table tracking lifecycle
(Plan explicitly calls this out.):contentReference[oaicite:9]{index=9}

SQLx requirements:

- All queries should use SQLx facilities that prevent schema/type mismatch surprises.
(Plan highlights SQLx compile-time verification as a major correctness win.):contentReference[oaicite:10]{index=10}

---

## 5) Behavioral Scenarios (BDD: Given/When/Then)

S1 — Startup applies DB PRAGMAs and schema migration

- Given the backend starts
- When DB pool is created
- Then PRAGMAs are applied and verified, and migrations run successfully
- And the PRAGMA results are logged (journal_mode, synchronous, busy_timeout)

S2 — WebSocket connect + subscription

- Given valid WS endpoint and subscription params
- When ingestion starts
- Then it connects and begins emitting normalized Tick events

S3 — Automatic reconnection with exponential backoff

- Given the WS connection drops
- When reconnect logic triggers
- Then it retries with exponential backoff up to MAX_BACKOFF
- And resumes emitting Ticks without duplicating state
(Reconnection explicitly required.):contentReference[oaicite:11]{index=11}

S4 — Ping/Pong keepalive

- Given low market activity
- When no messages arrive for KEEPALIVE_INTERVAL
- Then the client sends ping and expects pong
- And if pong is missed → reconnect is triggered
(Ping/pong management explicitly required.):contentReference[oaicite:12]{index=12}

S5 — Malformed message handling

- Given a malformed JSON payload arrives
- When serde parsing fails
- Then the message is rejected
- And an error counter + sample are logged
- And the system continues running

S6 — Channel backpressure behavior (bounded queues)

- Given the internal channel is at capacity
- When ingestion tries to enqueue another Tick
- Then the system increments BACKPRESSURE_DROP (or equivalent policy)
- And does not grow memory unbounded
(Note: policy must be deterministic and documented.)

S7 — Stale data veto

- Given data timestamp drift > MAX_STALENESS_MS (or local lag is detected)
- When strategy would emit a Signal
- Then the signal is vetoed with reason STALE_DATA
- And the veto is persisted for auditability

S8 — Strategy determinism (pure core)

- Given the same ordered sequence of Ticks
- When strategy runs twice (fresh process)
- Then it emits the same Signals (same timestamps/values within rounding rules)

S9 — Shadow mode “no real orders”

- Given SHADOW_MODE is enabled
- When execution receives a Signal
- Then it records a shadow order (desired size/price/fees/slippage assumptions)
- And no real OrderExecution endpoint is called (I1)

S10 — Order lifecycle persistence

- Given execution submits an order (or shadow order)
- When state transitions occur (submitted → ack → partial → filled/canceled/rejected)
- Then every transition is persisted in orders table with timestamp + reason
(Orders table tracking lifecycle is explicitly required.):contentReference[oaicite:13]{index=13}

S11 — Partial fill handling

- Given an order partially fills
- When remaining size is updated
- Then exposure + accounting update correctly
- And the system can cancel remaining size without double-counting fills

S12 — DB lock behavior uses busy_timeout (no crash)

- Given persistence attempts a write while DB is temporarily locked
- When busy_timeout is in effect
- Then the writer waits/retries rather than crashing
(Explicit rationale for busy_timeout.):contentReference[oaicite:14]{index=14}

S13 — Graceful shutdown drains + flushes

- Given SIGINT/CTRL-C
- When shutdown begins
- Then ingestion stops, channels stop accepting new work
- And persistence flushes final batch safely
- And a clean shutdown marker is logged

S14 — LIVE mode gating (explicit unlock)

- Given LIVE_MODE is requested
- When Gate G1 is not satisfied
- Then system refuses to start in LIVE_MODE (fails closed) and logs why

S15 — CPU contention resilience

- Given mc-paper.service is running with CPU cage (CPUQuota=150%) active
- When engine + dashboard services are running concurrently
- Then healthcheck.sh returns PASS
- And dashboard serves HTTP requests without stalling
- And tick generation continues without gaps
- And CPU pressure (PSI some/full) remains within operational bounds
(Context: BUG_2026-01-09_nuc1_mc_cpu_cage; CPU cage prevents Minecraft starvation of bot services.)

---

## 6) Gates

G1 — LIVE_MODE Unlock Gate (fail closed)
LIVE_MODE can only run when all are true:

- MODE=LIVE is explicitly set in config
- A second explicit “arm” flag is set (e.g., LIVE_ARMED=true)
- A “proof bundle” exists from recent SHADOW/PAPER runs:
  - invariant tests PASS
  - replay/sim PASS
  - risk caps validated
- Otherwise: refuse to start LIVE.

(Reason: current project stance is shadow-first: prove before risking capital.)

---

## 7) Verification Matrix (what proves what)

You must not claim a behavior is “done” without proof.

Automated tests (Rust):

- Unit tests:
  - parsing/normalization
  - strategy indicators (deterministic fixtures)
  - order state machine transitions
- Property tests (proptest/quickcheck):
  - I1 shadow safety (no execution calls)
  - I2 risk caps never exceeded under random sequences of signals/fills
  - I3 idempotency under duplicated events
  - I4 accounting conservation under randomized fills/fees
- Integration tests:
  - mock WS server: reconnect + ping/pong
  - SQLite WAL PRAGMA verification + lock simulation (busy_timeout)
- Replay tests:
  - recorded Tick stream → deterministic Signals and persisted state

Evidence artifacts:

- `docs/buglog/BUG_<date>_<slug>.md` includes:
  - commands run + outputs
  - test results
  - a short shadow run summary and invariant check stats

---

## 8) Phase 2 Completion Definition

Phase 2 is complete when:

- S1–S14 have proofs (tests/logs/replays), and
- I1–I6 are covered by automated tests (property tests for I1–I4 minimum), and
- SHADOW_MODE can run continuously without crash while persisting ticks/signals/orders.

## 9) Proof Pointers (Phase 2.1 - 2.2)

- **Phase 2.0 (Baseline)**: `docs/buglog/BUG_2026-01-08_phase2_0_baseline.md`
- **Phase 2.1 (Ingest Replay/Mock)**: `docs/buglog/BUG_2026-01-09_phase2_1_ingestion_replay_mockws.md`
- **Phase 2.2 (RealWS + Soak)**: `docs/buglog/BUG_2026-01-09_phase2_2_realws_ingestion.md` (RealWS) and `docs/buglog/BUG_2026-01-09_phase2_2h_soak_dynamic.md` (Soak)
- **Phase 3 (Dashboard Ops)**: `docs/buglog/BUG_2026-01-09_phase3_dashboard_readonly_delta.md`
