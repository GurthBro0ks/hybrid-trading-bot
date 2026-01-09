# Flight Recorder — nuc1 systemd
## main...origin/main
?? docs/buglog/BUG_2026-01-08_nuc1_systemd_services.md
From github.com:GurthBro0ks/hybrid-trading-bot
   79e8b6f..57a73b3  main       -> origin/main
Updating 79e8b6f..57a73b3
Fast-forward
 Makefile                                           |  10 ++
 config/config.toml                                 |  14 +++
 dashboard/app.py                                   |  28 +++++-
 docs/buglog/BUG_2026-01-08_laptop_apt_cdrom_fix.md |  25 +++++
 .../buglog/BUG_2026-01-08_laptop_proof_loop_run.md | 101 +++++++++++++++++++++
 ...UG_2026-01-08_repo-ergonomics_config-scripts.md |  46 ++++++++++
 engine/Cargo.lock                                  |  61 +++++++++++++
 engine/Cargo.toml                                  |   2 +
 engine/src/main.rs                                 |  63 ++++++++++---
 scripts/proof_check.sh                             |   6 ++
 scripts/run_dashboard.sh                           |   8 ++
 scripts/run_engine.sh                              |   7 ++
 12 files changed, 355 insertions(+), 16 deletions(-)
 create mode 100644 Makefile
 create mode 100644 config/config.toml
 create mode 100644 docs/buglog/BUG_2026-01-08_laptop_apt_cdrom_fix.md
 create mode 100644 docs/buglog/BUG_2026-01-08_laptop_proof_loop_run.md
 create mode 100644 docs/buglog/BUG_2026-01-08_repo-ergonomics_config-scripts.md
 create mode 100755 scripts/proof_check.sh
 create mode 100755 scripts/run_dashboard.sh
 create mode 100755 scripts/run_engine.sh
57a73b3 chore: config + scripts + makefile for proof loop
rustc 1.92.0 (ded5c06cf 2025-12-08)
cargo 1.92.0 (344c4567c 2025-10-21)
    Updating crates.io index
 Downloading crates ...
  Downloaded serde_spanned v0.6.9
  Downloaded toml_write v0.1.2
  Downloaded toml v0.8.23
  Downloaded toml_datetime v0.6.11
  Downloaded toml_edit v0.22.27
  Downloaded winnow v0.7.14
   Compiling proc-macro2 v1.0.105
   Compiling unicode-ident v1.0.22
   Compiling quote v1.0.43
   Compiling libc v0.2.180
   Compiling serde_core v1.0.228
   Compiling syn v2.0.114
   Compiling typenum v1.19.0
   Compiling version_check v0.9.5
   Compiling generic-array v0.14.7
   Compiling serde v1.0.228
   Compiling icu_properties_data v2.1.2
   Compiling icu_normalizer_data v2.1.1
   Compiling stable_deref_trait v1.2.1
   Compiling crossbeam-utils v0.8.21
   Compiling parking_lot_core v0.9.12
   Compiling smallvec v1.15.1
   Compiling zmij v1.0.12
   Compiling synstructure v0.13.2
   Compiling litemap v0.8.1
   Compiling writeable v0.6.2
   Compiling autocfg v1.5.0
   Compiling num-traits v0.2.19
   Compiling zerofrom-derive v0.1.6
   Compiling yoke-derive v0.8.1
   Compiling zerovec-derive v0.11.2
   Compiling displaydoc v0.2.5
   Compiling zerofrom v0.1.6
   Compiling yoke v0.8.1
   Compiling serde_derive v1.0.228
   Compiling zerovec v0.11.5
   Compiling tinystr v0.8.2
   Compiling icu_locale_core v2.1.1
   Compiling potential_utf v0.1.4
   Compiling zerotrie v0.2.3
   Compiling futures-core v0.3.31
   Compiling serde_json v1.0.149
   Compiling thiserror v2.0.17
   Compiling pin-project-lite v0.2.16
   Compiling shlex v1.3.0
   Compiling find-msvc-tools v0.1.6
   Compiling cfg-if v1.0.4
   Compiling cc v1.2.51
   Compiling icu_provider v2.1.1
   Compiling icu_collections v2.1.1
   Compiling tracing-attributes v0.1.31
   Compiling scopeguard v1.2.0
   Compiling vcpkg v0.2.15
   Compiling pkg-config v0.3.32
   Compiling lock_api v0.4.14
   Compiling libsqlite3-sys v0.30.1
   Compiling thiserror-impl v2.0.17
   Compiling futures-sink v0.3.31
   Compiling icu_normalizer v2.1.1
   Compiling icu_properties v2.1.2
   Compiling equivalent v1.0.2
   Compiling memchr v2.7.6
   Compiling percent-encoding v2.3.2
   Compiling form_urlencoded v1.2.2
   Compiling idna_adapter v1.2.1
   Compiling crypto-common v0.1.7
   Compiling block-buffer v0.10.4
   Compiling socket2 v0.6.1
   Compiling mio v1.1.1
   Compiling slab v0.4.11
   Compiling foldhash v0.1.5
   Compiling futures-task v0.3.31
   Compiling itoa v1.0.17
   Compiling allocator-api2 v0.2.21
   Compiling once_cell v1.21.3
   Compiling futures-io v0.3.31
   Compiling utf8_iter v1.0.4
   Compiling pin-utils v0.1.0
   Compiling bytes v1.11.0
   Compiling tracing-core v0.1.36
   Compiling tokio v1.49.0
   Compiling idna v1.1.0
   Compiling futures-util v0.3.31
   Compiling hashbrown v0.15.5
   Compiling digest v0.10.7
   Compiling parking_lot v0.12.5
   Compiling concurrent-queue v2.5.0
   Compiling errno v0.3.14
   Compiling cpufeatures v0.2.17
   Compiling hashbrown v0.16.1
   Compiling crc-catalog v2.4.0
   Compiling log v0.4.29
   Compiling parking v2.2.1
   Compiling tracing v0.1.44
   Compiling indexmap v2.13.0
   Compiling event-listener v5.4.1
   Compiling crc v3.4.0
   Compiling sha2 v0.10.9
   Compiling signal-hook-registry v1.4.8
   Compiling futures-intrusive v0.5.0
   Compiling hashlink v0.10.0
   Compiling tokio-stream v0.1.18
   Compiling url v2.5.8
   Compiling either v1.15.0
   Compiling crossbeam-queue v0.3.12
   Compiling spin v0.9.8
   Compiling tokio-macros v2.6.0
   Compiling base64 v0.22.1
   Compiling ryu v1.0.22
   Compiling serde_urlencoded v0.7.1
   Compiling sqlx-core v0.8.6
   Compiling flume v0.11.1
   Compiling atoi v2.0.0
   Compiling futures-executor v0.3.31
   Compiling futures-channel v0.3.31
   Compiling sqlx-sqlite v0.8.6
   Compiling dotenvy v0.15.7
   Compiling hex v0.4.3
   Compiling regex-syntax v0.8.8
   Compiling heck v0.5.0
   Compiling sqlx-macros-core v0.8.6
   Compiling regex-automata v0.4.13
   Compiling toml_datetime v0.6.11
   Compiling serde_spanned v0.6.9
   Compiling winnow v0.7.14
   Compiling toml_write v0.1.2
   Compiling lazy_static v1.5.0
   Compiling anyhow v1.0.100
   Compiling sharded-slab v0.1.7
   Compiling toml_edit v0.22.27
Build failed or interrupted. Retrying with CARGO_BUILD_JOBS=1...
   Compiling libsqlite3-sys v0.30.1
   Compiling toml_edit v0.22.27
   Compiling sqlx-sqlite v0.8.6
   Compiling matchers v0.2.0
   Compiling sqlx-macros v0.8.6
   Compiling tracing-log v0.2.0
   Compiling thread_local v1.1.9
   Compiling nu-ansi-term v0.50.3
   Compiling tracing-subscriber v0.3.22
   Compiling sqlx v0.8.6
   Compiling anyhow v1.0.100
   Compiling toml v0.8.23
   Compiling engine v0.1.0 (/opt/hybrid-trading-bot/engine)
    Finished `release` profile [optimized] target(s) in 6m 46s
total 5.7M
drwxrwxr-x   7 slimy slimy 4.0K Jan  8 19:07 .
drwxrwxr-x   4 slimy slimy 4.0K Jan  8 18:49 ..
drwxrwxr-x  50 slimy slimy 4.0K Jan  8 18:49 build
-rw-rw-r--   1 slimy slimy    0 Jan  8 18:49 .cargo-lock
drwxrwxr-x   2 slimy slimy  44K Jan  8 19:07 deps
-rwxrwxr-x   2 slimy slimy 5.6M Jan  8 19:07 engine
-rw-rw-r--   1 slimy slimy   97 Jan  8 19:07 engine.d
drwxrwxr-x   2 slimy slimy 4.0K Jan  8 18:49 examples
drwxrwxr-x 271 slimy slimy  20K Jan  8 18:49 .fingerprint
drwxrwxr-x   2 slimy slimy 4.0K Jan  8 18:49 incremental
Requirement already satisfied: pip in ./dashboard/.venv/lib/python3.12/site-packages (25.3)
Requirement already satisfied: streamlit in ./dashboard/.venv/lib/python3.12/site-packages (1.52.2)
Requirement already satisfied: pandas in ./dashboard/.venv/lib/python3.12/site-packages (2.3.3)
Requirement already satisfied: altair!=5.4.0,!=5.4.1,<7,>=4.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (6.0.0)
Requirement already satisfied: blinker<2,>=1.5.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (1.9.0)
Requirement already satisfied: cachetools<7,>=4.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (6.2.4)
Requirement already satisfied: click<9,>=7.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (8.3.1)
Requirement already satisfied: numpy<3,>=1.23 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (2.4.0)
Requirement already satisfied: packaging>=20 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (25.0)
Requirement already satisfied: pillow<13,>=7.1.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (12.1.0)
Requirement already satisfied: protobuf<7,>=3.20 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (6.33.2)
Requirement already satisfied: pyarrow>=7.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (22.0.0)
Requirement already satisfied: requests<3,>=2.27 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (2.32.5)
Requirement already satisfied: tenacity<10,>=8.1.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (9.1.2)
Requirement already satisfied: toml<2,>=0.10.1 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (0.10.2)
Requirement already satisfied: typing-extensions<5,>=4.4.0 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (4.15.0)
Requirement already satisfied: watchdog<7,>=2.1.5 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (6.0.0)
Requirement already satisfied: gitpython!=3.1.19,<4,>=3.0.7 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (3.1.46)
Requirement already satisfied: pydeck<1,>=0.8.0b4 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (0.9.1)
Requirement already satisfied: tornado!=6.5.0,<7,>=6.0.3 in ./dashboard/.venv/lib/python3.12/site-packages (from streamlit) (6.5.4)
Requirement already satisfied: python-dateutil>=2.8.2 in ./dashboard/.venv/lib/python3.12/site-packages (from pandas) (2.9.0.post0)
Requirement already satisfied: pytz>=2020.1 in ./dashboard/.venv/lib/python3.12/site-packages (from pandas) (2025.2)
Requirement already satisfied: tzdata>=2022.7 in ./dashboard/.venv/lib/python3.12/site-packages (from pandas) (2025.3)
Requirement already satisfied: jinja2 in ./dashboard/.venv/lib/python3.12/site-packages (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (3.1.6)
Requirement already satisfied: jsonschema>=3.0 in ./dashboard/.venv/lib/python3.12/site-packages (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (4.26.0)
Requirement already satisfied: narwhals>=1.27.1 in ./dashboard/.venv/lib/python3.12/site-packages (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (2.15.0)
Requirement already satisfied: gitdb<5,>=4.0.1 in ./dashboard/.venv/lib/python3.12/site-packages (from gitpython!=3.1.19,<4,>=3.0.7->streamlit) (4.0.12)
Requirement already satisfied: smmap<6,>=3.0.1 in ./dashboard/.venv/lib/python3.12/site-packages (from gitdb<5,>=4.0.1->gitpython!=3.1.19,<4,>=3.0.7->streamlit) (5.0.2)
Requirement already satisfied: charset_normalizer<4,>=2 in ./dashboard/.venv/lib/python3.12/site-packages (from requests<3,>=2.27->streamlit) (3.4.4)
Requirement already satisfied: idna<4,>=2.5 in ./dashboard/.venv/lib/python3.12/site-packages (from requests<3,>=2.27->streamlit) (3.11)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./dashboard/.venv/lib/python3.12/site-packages (from requests<3,>=2.27->streamlit) (2.6.3)
Requirement already satisfied: certifi>=2017.4.17 in ./dashboard/.venv/lib/python3.12/site-packages (from requests<3,>=2.27->streamlit) (2026.1.4)
Requirement already satisfied: MarkupSafe>=2.0 in ./dashboard/.venv/lib/python3.12/site-packages (from jinja2->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (3.0.3)
Requirement already satisfied: attrs>=22.2.0 in ./dashboard/.venv/lib/python3.12/site-packages (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (25.4.0)
Requirement already satisfied: jsonschema-specifications>=2023.03.6 in ./dashboard/.venv/lib/python3.12/site-packages (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (2025.9.1)
Requirement already satisfied: referencing>=0.28.4 in ./dashboard/.venv/lib/python3.12/site-packages (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (0.37.0)
Requirement already satisfied: rpds-py>=0.25.0 in ./dashboard/.venv/lib/python3.12/site-packages (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit) (0.30.0)
Requirement already satisfied: six>=1.5 in ./dashboard/.venv/lib/python3.12/site-packages (from python-dateutil>=2.8.2->pandas) (1.17.0)
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:18 UTC; 10s ago
   Main PID: 2610247 (engine)
      Tasks: 7 (limit: 18964)
     Memory: 1.3M (peak: 1.5M)
        CPU: 23ms
     CGroup: /system.slice/hybrid-engine.service
             └─2610247 /opt/hybrid-trading-bot/engine/target/release/engine

Jan 08 19:09:24 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:24.978139Z  INFO tick saved: SOL/USDC price=100.6500 ts=1767899364
Jan 08 19:09:25 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:25.480244Z  INFO tick saved: SOL/USDC price=100.7000 ts=1767899365
Jan 08 19:09:25 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:25.988417Z  INFO tick saved: SOL/USDC price=100.7500 ts=1767899365
Jan 08 19:09:26 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:26.485247Z  INFO tick saved: SOL/USDC price=100.8000 ts=1767899366
Jan 08 19:09:26 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:26.987274Z  INFO tick saved: SOL/USDC price=100.8500 ts=1767899366
Jan 08 19:09:27 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:27.487663Z  INFO tick saved: SOL/USDC price=100.9000 ts=1767899367
Jan 08 19:09:27 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:27.991564Z  INFO tick saved: SOL/USDC price=100.9500 ts=1767899367
Jan 08 19:09:28 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:28.492849Z  INFO tick saved: SOL/USDC price=101.0000 ts=1767899368
Jan 08 19:09:28 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:28.994372Z  INFO tick saved: SOL/USDC price=101.0500 ts=1767899368
Jan 08 19:09:29 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:29.494363Z  INFO tick saved: SOL/USDC price=101.1000 ts=1767899369
Jan 08 19:09:29 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:29.995383Z  INFO tick saved: SOL/USDC price=101.1500 ts=1767899369
● hybrid-dashboard.service - Hybrid Trading Bot Dashboard
     Loaded: loaded (/etc/systemd/system/hybrid-dashboard.service; enabled; preset: enabled)
     Active: activating (auto-restart) (Result: exit-code) since Thu 2026-01-08 19:09:28 UTC; 1s ago
    Process: 2610458 ExecStart=/opt/hybrid-trading-bot/dashboard/.venv/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501 (code=exited, status=1/FAILURE)
   Main PID: 2610458 (code=exited, status=1/FAILURE)
        CPU: 1.045s

Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.045s CPU time.
Jan 08 19:09:18 slimy-nuc1 systemd[1]: Started hybrid-engine.service - Hybrid Trading Bot Engine.
Jan 08 19:09:18 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:18.901475Z  INFO starting engine; symbol=SOL/USDC db=data/bot.db
Jan 08 19:09:18 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:18.956230Z  INFO schema ensured
Jan 08 19:09:18 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:18.956986Z  INFO tick saved: SOL/USDC price=100.0500 ts=1767899358
Jan 08 19:09:19 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:19.458260Z  INFO tick saved: SOL/USDC price=100.1000 ts=1767899359
Jan 08 19:09:19 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:19.959896Z  INFO tick saved: SOL/USDC price=100.1500 ts=1767899359
Jan 08 19:09:20 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:20.460332Z  INFO tick saved: SOL/USDC price=100.2000 ts=1767899360
Jan 08 19:09:20 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:20.961256Z  INFO tick saved: SOL/USDC price=100.2500 ts=1767899360
Jan 08 19:09:21 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:21.464216Z  INFO tick saved: SOL/USDC price=100.3000 ts=1767899361
Jan 08 19:09:21 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:21.966282Z  INFO tick saved: SOL/USDC price=100.3500 ts=1767899361
Jan 08 19:09:22 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:22.468559Z  INFO tick saved: SOL/USDC price=100.4000 ts=1767899362
Jan 08 19:09:22 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:22.970748Z  INFO tick saved: SOL/USDC price=100.4500 ts=1767899362
Jan 08 19:09:23 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:23.473748Z  INFO tick saved: SOL/USDC price=100.5000 ts=1767899363
Jan 08 19:09:23 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:23.973493Z  INFO tick saved: SOL/USDC price=100.5500 ts=1767899363
Jan 08 19:09:24 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:24.475228Z  INFO tick saved: SOL/USDC price=100.6000 ts=1767899364
Jan 08 19:09:24 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:24.978139Z  INFO tick saved: SOL/USDC price=100.6500 ts=1767899364
Jan 08 19:09:25 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:25.480244Z  INFO tick saved: SOL/USDC price=100.7000 ts=1767899365
Jan 08 19:09:25 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:25.988417Z  INFO tick saved: SOL/USDC price=100.7500 ts=1767899365
Jan 08 19:09:26 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:26.485247Z  INFO tick saved: SOL/USDC price=100.8000 ts=1767899366
Jan 08 19:09:26 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:26.987274Z  INFO tick saved: SOL/USDC price=100.8500 ts=1767899366
Jan 08 19:09:27 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:27.487663Z  INFO tick saved: SOL/USDC price=100.9000 ts=1767899367
Jan 08 19:09:27 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:27.991564Z  INFO tick saved: SOL/USDC price=100.9500 ts=1767899367
Jan 08 19:09:28 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:28.492849Z  INFO tick saved: SOL/USDC price=101.0000 ts=1767899368
Jan 08 19:09:28 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:28.994372Z  INFO tick saved: SOL/USDC price=101.0500 ts=1767899368
Jan 08 19:09:29 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:29.494363Z  INFO tick saved: SOL/USDC price=101.1000 ts=1767899369
Jan 08 19:09:29 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:29.995383Z  INFO tick saved: SOL/USDC price=101.1500 ts=1767899369
Jan 08 19:09:30 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:30.496446Z  INFO tick saved: SOL/USDC price=101.2000 ts=1767899370
Jan 08 19:09:18 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:20 slimy-nuc1 streamlit[2610248]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:20 slimy-nuc1 streamlit[2610248]: 2026-01-08 19:09:20.665 Port 8501 is already in use
Jan 08 19:09:20 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:20 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:20 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.221s CPU time.
Jan 08 19:09:22 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 1.
Jan 08 19:09:22 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:24 slimy-nuc1 streamlit[2610351]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:24 slimy-nuc1 streamlit[2610351]: 2026-01-08 19:09:24.551 Port 8501 is already in use
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.059s CPU time.
Jan 08 19:09:26 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 2.
Jan 08 19:09:26 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:28 slimy-nuc1 streamlit[2610458]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:28 slimy-nuc1 streamlit[2610458]: 2026-01-08 19:09:28.534 Port 8501 is already in use
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.045s CPU time.
24
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0  1522    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Thu, 08 Jan 2026 19:09:30 GMT
Accept-Ranges: bytes
Etag: "7c4233bbfa23a23484cee74d3acdd552ab463803b8cf432c1c1dd47ea7a07b3287eb08a0353f28010b7cb4e56c6cdc510096ff493bbfb6898658b96801f4cf07"
Last-Modified: Thu, 08 Jan 2026 18:14:47 GMT
Cache-Control: no-cache
Content-Length: 1522
Vary: Accept-Encoding

COMMAND       PID  USER   FD   TYPE    DEVICE SIZE/OFF NODE NAME
streamlit 2525058 slimy    6u  IPv4 160610755      0t0  TCP *:8501 (LISTEN)
● hybrid-dashboard.service - Hybrid Trading Bot Dashboard
     Loaded: loaded (/etc/systemd/system/hybrid-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:49 UTC; 4s ago
   Main PID: 2611036 (streamlit)
      Tasks: 1 (limit: 18964)
     Memory: 35.7M (peak: 35.9M)
        CPU: 923ms
     CGroup: /system.slice/hybrid-dashboard.service
             └─2611036 /opt/hybrid-trading-bot/dashboard/.venv/bin/python /opt/hybrid-trading-bot/dashboard/.venv/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.061s CPU time.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 8.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:50 slimy-nuc1 streamlit[2611036]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   You can now view your Streamlit app in your browser.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   URL: http://0.0.0.0:8501
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:18 UTC; 43s ago
   Main PID: 2610247 (engine)
      Tasks: 7 (limit: 18964)
     Memory: 1.5M (peak: 1.8M)
        CPU: 50ms
     CGroup: /system.slice/hybrid-engine.service
             └─2610247 /opt/hybrid-trading-bot/engine/target/release/engine

Jan 08 19:09:58 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:58.102867Z  INFO tick saved: SOL/USDC price=103.9500 ts=1767899398
Jan 08 19:09:58 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:58.606180Z  INFO tick saved: SOL/USDC price=104.0000 ts=1767899398
Jan 08 19:09:59 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:59.104972Z  INFO tick saved: SOL/USDC price=104.0500 ts=1767899399
Jan 08 19:09:59 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:59.607529Z  INFO tick saved: SOL/USDC price=104.1000 ts=1767899399
Jan 08 19:10:00 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:00.111130Z  INFO tick saved: SOL/USDC price=104.1500 ts=1767899400
Jan 08 19:10:00 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:00.612854Z  INFO tick saved: SOL/USDC price=104.2000 ts=1767899400
Jan 08 19:10:01 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:01.110408Z  INFO tick saved: SOL/USDC price=104.2500 ts=1767899401
Jan 08 19:10:01 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:01.611362Z  INFO tick saved: SOL/USDC price=104.3000 ts=1767899401
Jan 08 19:10:02 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:02.112480Z  INFO tick saved: SOL/USDC price=104.3500 ts=1767899402
Jan 08 19:10:02 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:02.614353Z  INFO tick saved: SOL/USDC price=104.4000 ts=1767899402
● hybrid-dashboard.service - Hybrid Trading Bot Dashboard
     Loaded: loaded (/etc/systemd/system/hybrid-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:49 UTC; 13s ago
   Main PID: 2611036 (streamlit)
      Tasks: 1 (limit: 18964)
     Memory: 38.5M (peak: 38.7M)
        CPU: 1.063s
     CGroup: /system.slice/hybrid-dashboard.service
             └─2611036 /opt/hybrid-trading-bot/dashboard/.venv/bin/python /opt/hybrid-trading-bot/dashboard/.venv/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.061s CPU time.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 8.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:50 slimy-nuc1 streamlit[2611036]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   You can now view your Streamlit app in your browser.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   URL: http://0.0.0.0:8501
Jan 08 19:09:38 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:38.035502Z  INFO tick saved: SOL/USDC price=101.9500 ts=1767899378
Jan 08 19:09:38 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:38.537095Z  INFO tick saved: SOL/USDC price=102.0000 ts=1767899378
Jan 08 19:09:39 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:39.039518Z  INFO tick saved: SOL/USDC price=102.0500 ts=1767899379
Jan 08 19:09:39 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:39.542454Z  INFO tick saved: SOL/USDC price=102.1000 ts=1767899379
Jan 08 19:09:40 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:40.043298Z  INFO tick saved: SOL/USDC price=102.1500 ts=1767899380
Jan 08 19:09:40 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:40.544718Z  INFO tick saved: SOL/USDC price=102.2000 ts=1767899380
Jan 08 19:09:41 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:41.047791Z  INFO tick saved: SOL/USDC price=102.2500 ts=1767899381
Jan 08 19:09:41 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:41.552147Z  INFO tick saved: SOL/USDC price=102.3000 ts=1767899381
Jan 08 19:09:42 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:42.053020Z  INFO tick saved: SOL/USDC price=102.3500 ts=1767899382
Jan 08 19:09:42 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:42.553735Z  INFO tick saved: SOL/USDC price=102.4000 ts=1767899382
Jan 08 19:09:43 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:43.055146Z  INFO tick saved: SOL/USDC price=102.4500 ts=1767899383
Jan 08 19:09:43 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:43.557019Z  INFO tick saved: SOL/USDC price=102.5000 ts=1767899383
Jan 08 19:09:44 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:44.057844Z  INFO tick saved: SOL/USDC price=102.5500 ts=1767899384
Jan 08 19:09:44 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:44.558950Z  INFO tick saved: SOL/USDC price=102.6000 ts=1767899384
Jan 08 19:09:45 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:45.060739Z  INFO tick saved: SOL/USDC price=102.6500 ts=1767899385
Jan 08 19:09:45 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:45.561488Z  INFO tick saved: SOL/USDC price=102.7000 ts=1767899385
Jan 08 19:09:46 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:46.062721Z  INFO tick saved: SOL/USDC price=102.7500 ts=1767899386
Jan 08 19:09:46 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:46.563834Z  INFO tick saved: SOL/USDC price=102.8000 ts=1767899386
Jan 08 19:09:47 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:47.064639Z  INFO tick saved: SOL/USDC price=102.8500 ts=1767899387
Jan 08 19:09:47 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:47.567094Z  INFO tick saved: SOL/USDC price=102.9000 ts=1767899387
Jan 08 19:09:48 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:48.066465Z  INFO tick saved: SOL/USDC price=102.9500 ts=1767899388
Jan 08 19:09:48 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:48.568166Z  INFO tick saved: SOL/USDC price=103.0000 ts=1767899388
Jan 08 19:09:49 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:49.069457Z  INFO tick saved: SOL/USDC price=103.0500 ts=1767899389
Jan 08 19:09:49 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:49.570915Z  INFO tick saved: SOL/USDC price=103.1000 ts=1767899389
Jan 08 19:09:50 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:50.071593Z  INFO tick saved: SOL/USDC price=103.1500 ts=1767899390
Jan 08 19:09:50 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:50.573108Z  INFO tick saved: SOL/USDC price=103.2000 ts=1767899390
Jan 08 19:09:51 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:51.073562Z  INFO tick saved: SOL/USDC price=103.2500 ts=1767899391
Jan 08 19:09:51 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:51.575071Z  INFO tick saved: SOL/USDC price=103.3000 ts=1767899391
Jan 08 19:09:52 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:52.075786Z  INFO tick saved: SOL/USDC price=103.3500 ts=1767899392
Jan 08 19:09:52 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:52.586384Z  INFO tick saved: SOL/USDC price=103.4000 ts=1767899392
Jan 08 19:09:53 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:53.080418Z  INFO tick saved: SOL/USDC price=103.4500 ts=1767899393
Jan 08 19:09:53 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:53.582191Z  INFO tick saved: SOL/USDC price=103.5000 ts=1767899393
Jan 08 19:09:54 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:54.085942Z  INFO tick saved: SOL/USDC price=103.5500 ts=1767899394
Jan 08 19:09:54 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:54.586397Z  INFO tick saved: SOL/USDC price=103.6000 ts=1767899394
Jan 08 19:09:55 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:55.090225Z  INFO tick saved: SOL/USDC price=103.6500 ts=1767899395
Jan 08 19:09:55 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:55.592178Z  INFO tick saved: SOL/USDC price=103.7000 ts=1767899395
Jan 08 19:09:56 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:56.096464Z  INFO tick saved: SOL/USDC price=103.7500 ts=1767899396
Jan 08 19:09:56 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:56.599208Z  INFO tick saved: SOL/USDC price=103.8000 ts=1767899396
Jan 08 19:09:57 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:57.100514Z  INFO tick saved: SOL/USDC price=103.8500 ts=1767899397
Jan 08 19:09:57 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:57.601430Z  INFO tick saved: SOL/USDC price=103.9000 ts=1767899397
Jan 08 19:09:58 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:58.102867Z  INFO tick saved: SOL/USDC price=103.9500 ts=1767899398
Jan 08 19:09:58 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:58.606180Z  INFO tick saved: SOL/USDC price=104.0000 ts=1767899398
Jan 08 19:09:59 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:59.104972Z  INFO tick saved: SOL/USDC price=104.0500 ts=1767899399
Jan 08 19:09:59 slimy-nuc1 engine[2610247]: 2026-01-08T19:09:59.607529Z  INFO tick saved: SOL/USDC price=104.1000 ts=1767899399
Jan 08 19:10:00 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:00.111130Z  INFO tick saved: SOL/USDC price=104.1500 ts=1767899400
Jan 08 19:10:00 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:00.612854Z  INFO tick saved: SOL/USDC price=104.2000 ts=1767899400
Jan 08 19:10:01 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:01.110408Z  INFO tick saved: SOL/USDC price=104.2500 ts=1767899401
Jan 08 19:10:01 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:01.611362Z  INFO tick saved: SOL/USDC price=104.3000 ts=1767899401
Jan 08 19:10:02 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:02.112480Z  INFO tick saved: SOL/USDC price=104.3500 ts=1767899402
Jan 08 19:10:02 slimy-nuc1 engine[2610247]: 2026-01-08T19:10:02.614353Z  INFO tick saved: SOL/USDC price=104.4000 ts=1767899402
Jan 08 19:09:24 slimy-nuc1 streamlit[2610351]: 2026-01-08 19:09:24.551 Port 8501 is already in use
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:24 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.059s CPU time.
Jan 08 19:09:26 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 2.
Jan 08 19:09:26 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:28 slimy-nuc1 streamlit[2610458]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:28 slimy-nuc1 streamlit[2610458]: 2026-01-08 19:09:28.534 Port 8501 is already in use
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:28 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.045s CPU time.
Jan 08 19:09:30 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 3.
Jan 08 19:09:30 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:32 slimy-nuc1 streamlit[2610593]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:32 slimy-nuc1 streamlit[2610593]: 2026-01-08 19:09:32.470 Port 8501 is already in use
Jan 08 19:09:32 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:32 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:32 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.051s CPU time.
Jan 08 19:09:34 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 4.
Jan 08 19:09:34 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:36 slimy-nuc1 streamlit[2610663]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:36 slimy-nuc1 streamlit[2610663]: 2026-01-08 19:09:36.350 Port 8501 is already in use
Jan 08 19:09:36 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:36 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:36 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.135s CPU time.
Jan 08 19:09:38 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 5.
Jan 08 19:09:38 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:39 slimy-nuc1 streamlit[2610769]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:39 slimy-nuc1 streamlit[2610769]: 2026-01-08 19:09:39.939 Port 8501 is already in use
Jan 08 19:09:40 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:40 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:42 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 6.
Jan 08 19:09:42 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:43 slimy-nuc1 streamlit[2610854]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:43 slimy-nuc1 streamlit[2610854]: 2026-01-08 19:09:43.617 Port 8501 is already in use
Jan 08 19:09:43 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:43 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:43 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.176s CPU time.
Jan 08 19:09:45 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 7.
Jan 08 19:09:45 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:46 slimy-nuc1 streamlit[2610946]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:47 slimy-nuc1 streamlit[2610946]: 2026-01-08 19:09:47.382 Port 8501 is already in use
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Main process exited, code=exited, status=1/FAILURE
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.061s CPU time.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 8.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:50 slimy-nuc1 streamlit[2611036]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   You can now view your Streamlit app in your browser.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   URL: http://0.0.0.0:8501
89
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0  0  1522    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Thu, 08 Jan 2026 19:10:03 GMT
Accept-Ranges: bytes
Etag: "7c4233bbfa23a23484cee74d3acdd552ab463803b8cf432c1c1dd47ea7a07b3287eb08a0353f28010b7cb4e56c6cdc510096ff493bbfb6898658b96801f4cf07"
Last-Modified: Thu, 08 Jan 2026 18:14:47 GMT
Cache-Control: no-cache
Content-Length: 1522
Vary: Accept-Encoding

