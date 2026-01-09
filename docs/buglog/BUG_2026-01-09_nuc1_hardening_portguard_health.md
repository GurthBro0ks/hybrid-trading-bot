# Flight Recorder — NUC1 Hardening (portguard + health)

**Flight Recorder ON** | TARGET: NUC1 only | Date: 2026-01-09T10:00:22+00:00

## PHASE 0 — Context Snapshot

### System
```
2026-01-09T10:00:22+00:00
slimy-nuc1
slimy
/opt/hybrid-trading-bot
```

### Git Status
```
## main...origin/main
?? docs/buglog/BUG_2026-01-08_nuc1_systemd_services.md
?? docs/buglog/BUG_2026-01-09_nuc1_hardening_portguard_health.md
?? docs/buglog/BUG_2026-01-09_nuc1_load_triage_with_minecraft_alloc.md
```

### Current Services
```
=== hybrid-engine ===
● hybrid-engine.service - Hybrid Trading Bot Engine
     Loaded: loaded (/etc/systemd/system/hybrid-engine.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:18 UTC; 14h ago
   Main PID: 2610247 (engine)
      Tasks: 6 (limit: 18964)
     Memory: 10.6M (peak: 11.0M)
        CPU: 38.053s
     CGroup: /system.slice/hybrid-engine.service
             └─2610247 /opt/hybrid-trading-bot/engine/target/release/engine

Jan 09 10:00:18 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:18.125738Z  INFO tick saved: SOL/USDC price=5432.2500 ts=1767952818
Jan 09 10:00:18 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:18.626273Z  INFO tick saved: SOL/USDC price=5432.3000 ts=1767952818
Jan 09 10:00:19 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:19.127169Z  INFO tick saved: SOL/USDC price=5432.3500 ts=1767952819
Jan 09 10:00:19 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:19.628449Z  INFO tick saved: SOL/USDC price=5432.4000 ts=1767952819
Jan 09 10:00:20 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:20.129398Z  INFO tick saved: SOL/USDC price=5432.4500 ts=1767952820
Jan 09 10:00:20 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:20.630371Z  INFO tick saved: SOL/USDC price=5432.5000 ts=1767952820
Jan 09 10:00:21 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:21.131339Z  INFO tick saved: SOL/USDC price=5432.5500 ts=1767952821
Jan 09 10:00:21 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:21.632218Z  INFO tick saved: SOL/USDC price=5432.6000 ts=1767952821
Jan 09 10:00:22 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:22.134564Z  INFO tick saved: SOL/USDC price=5432.6500 ts=1767952822
Jan 09 10:00:22 slimy-nuc1 engine[2610247]: 2026-01-09T10:00:22.635510Z  INFO tick saved: SOL/USDC price=5432.7000 ts=1767952822

=== hybrid-dashboard ===
● hybrid-dashboard.service - Hybrid Trading Bot Dashboard
     Loaded: loaded (/etc/systemd/system/hybrid-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-01-08 19:09:49 UTC; 14h ago
   Main PID: 2611036 (streamlit)
      Tasks: 1 (limit: 18964)
     Memory: 38.4M (peak: 38.7M)
        CPU: 1.066s
     CGroup: /system.slice/hybrid-dashboard.service
             └─2611036 /opt/hybrid-trading-bot/dashboard/.venv/bin/python /opt/hybrid-trading-bot/dashboard/.venv/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Failed with result 'exit-code'.
Jan 08 19:09:47 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Consumed 1.061s CPU time.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: hybrid-dashboard.service: Scheduled restart job, restart counter is at 8.
Jan 08 19:09:49 slimy-nuc1 systemd[1]: Started hybrid-dashboard.service - Hybrid Trading Bot Dashboard.
Jan 08 19:09:50 slimy-nuc1 streamlit[2611036]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   You can now view your Streamlit app in your browser.
Jan 08 19:09:51 slimy-nuc1 streamlit[2611036]:   URL: http://0.0.0.0:8501
```

## PHASE 4 — Systemd Unit Patch (MANUAL)

❌ **Automated sudo access not available in non-interactive session**

The following patch needs to be applied manually with sudo:

### Option A: Replace entire unit file
```bash
sudo cp /tmp/hybrid-dashboard.service /etc/systemd/system/hybrid-dashboard.service
sudo systemctl daemon-reload
```

### Option B: Edit interactively
```bash
sudo systemctl edit --full hybrid-dashboard.service
```

Then add this line in the [Service] section before ExecStart:
```
ExecStartPre=/opt/hybrid-trading-bot/scripts/port_guard_8501.sh
```

### Prepared patch file location
```
/tmp/hybrid-dashboard.service
```

The patch adds a pre-startup port guard that safely clears any stray Streamlit
process on 8501 before dashboard service starts, preventing restart loops.

## PHASE 5 — Healthcheck Script Test

### Running healthcheck
```
[health] time: 2026-01-09T10:01:57+00:00
[health] db: /opt/hybrid-trading-bot/data/bot.db
[health] port: 8501
[health] ticks: 106843
[health] checking http://127.0.0.1:8501...
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Fri, 09 Jan 2026 10:01:57 GMT
Accept-Ranges: bytes
[health] PASS
```

## PHASE 6 — Commit & Push

### Commit
```
5f99b27 ops: hardening dashboard reliability (telemetry, healthcheck, port guard)
```

### Files Committed
```
dashboard/.streamlit/config.toml       (disable telemetry)
scripts/healthcheck.sh                 (health check)
scripts/port_guard_8501.sh             (port guard helper)
```

### Push Status
```
Everything up-to-date
```

## Summary

### ✅ Completed
1. Streamlit telemetry disabled
2. Healthcheck script created and tested
3. Port guard helper deployed
4. All repo files committed and pushed

### ⚠️ Manual Action Required
Apply systemd unit patch with sudo:
```bash
sudo cp /tmp/hybrid-dashboard.service /etc/systemd/system/hybrid-dashboard.service
sudo systemctl daemon-reload
sudo systemctl restart hybrid-dashboard.service
```

### Test Commands
```bash
# Run healthcheck
/opt/hybrid-trading-bot/scripts/healthcheck.sh

# Check dashboard
curl -I http://127.0.0.1:8501

# Check systemd status
systemctl status hybrid-dashboard.service
```

---
Flight Recorder OFF. Report complete.
