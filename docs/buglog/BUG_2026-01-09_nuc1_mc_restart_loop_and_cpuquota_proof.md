# BUG_2026-01-09_nuc1_mc_restart_loop_and_cpuquota_proof

## Step 0 - Initialize buglog

Timestamp: 2026-01-09T10:57:30+00:00

Symptom summary:
- mc-paper.service stuck in auto-restart loop (Active: activating (auto-restart) (Result: exit-code)).

Current observations:
- CPU cage appears installed via systemd drop-in(s) (to be proven with cgroup v2 cpu.max and systemd show fields).
- Existing drop-ins: /etc/systemd/system/mc-paper.service.d/{20-resources.conf,restart.conf}.

Planned actions:
- Capture evidence for CPU quota and restart loop symptoms (systemd show, cgroup v2 cpu.max, unit logs).
- Identify root cause (restart policy, ExecStop behavior, or other constraints).
- Apply safe restart override via 30-restart-sane.conf (minimal change).
- Re-verify service stability, CPU cage still applied, and healthcheck passes.
- Mirror the drop-in to repo templates if fix is effective and commit changes.

## Step 1 - Capture evidence (no changes)
### 2026-01-09T10:57:52+00:00
$ date -Is
2026-01-09T10:57:52+00:00
Exit status: 0

### 2026-01-09T10:57:52+00:00
$ systemctl status mc-paper.service --no-pager
● mc-paper.service - Paper Minecraft Server
     Loaded: loaded (/etc/systemd/system/mc-paper.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/mc-paper.service.d
             └─20-resources.conf, restart.conf
     Active: activating (auto-restart) (Result: exit-code) since Fri 2026-01-09 10:57:32 UTC; 20s ago
    Process: 961089 ExecStart=/usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui (code=exited, status=0/SUCCESS)
    Process: 965840 ExecStop=/bin/kill -SIGTERM $MAINPID (code=exited, status=1/FAILURE)
   Main PID: 961089 (code=exited, status=0/SUCCESS)
        CPU: 2min 32.746s
Exit status: 3

### 2026-01-09T10:57:53+00:00
$ systemctl show mc-paper.service -p CPUAccounting -p CPUQuota -p CPUQuotaPerSecUSec -p CPUQuotaPeriodUSec -p Nice -p IOSchedulingClass -p IOSchedulingPriority --no-pager
CPUAccounting=yes
CPUQuotaPerSecUSec=1.500000s
CPUQuotaPeriodUSec=infinity
Nice=10
IOSchedulingClass=3
IOSchedulingPriority=7
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ systemctl cat mc-paper.service
# /etc/systemd/system/mc-paper.service
[Unit]
Description=Paper Minecraft Server
After=network.target

[Service]
WorkingDirectory=/opt/slimy/minecraft
User=slimy
Group=slimy
# JVM flags: good defaults for ~10-12G heaps; adjust Xmx after monitoring
ExecStart=/usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED \
  -Xms4G -Xmx8G \
  -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 \
  -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch \
  -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M \
  -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 \
  -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 \
  -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 \
  -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 \
  -Dfile.encoding=UTF-8 \
  --add-opens=java.base/java.net=ALL-UNNAMED \
  --add-opens=java.base/java.lang.ref=ALL-UNNAMED \
  -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
ExecStop=/bin/kill -SIGTERM $MAINPID
Restart=on-failure
TimeoutStopSec=180

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/mc-paper.service.d/20-resources.conf
[Service]
CPUAccounting=yes
CPUQuota=150%
Nice=10
IOSchedulingClass=idle
IOSchedulingPriority=7

# Purpose: Cage Minecraft CPU usage to protect Hybrid Trading Bot services
# CPUQuota=150%: Caps mc-paper to ~1.5 cores on this NUC (prevents full saturation)
# Nice=10: Lower CPU scheduling priority (yielding to dashboard/engine)
# IOSchedulingClass=idle: Only use I/O when system is otherwise idle
# IOSchedulingPriority=7: Lowest I/O priority within idle class
#
# Context: BUG_2026-01-09_nuc1_mc_cpu_cage.md
# Date: 2026-01-09

# /etc/systemd/system/mc-paper.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=30
StartLimitIntervalSec=300
StartLimitBurst=5
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ sudo ls -la /etc/systemd/system/mc-paper.service.d
[sudo] password for slimy: total 16
drwxr-xr-x  2 root root 4096 Jan  9 10:39 .
drwxr-xr-x 30 root root 4096 Jan  9 10:14 ..
-rw-r--r--  1 root root  528 Jan  9 10:39 20-resources.conf
-rw-r--r--  1 root root   87 Dec  4 21:13 restart.conf
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ sudo sed -n '1,200p' /etc/systemd/system/mc-paper.service.d/20-resources.conf
[Service]
CPUAccounting=yes
CPUQuota=150%
Nice=10
IOSchedulingClass=idle
IOSchedulingPriority=7

# Purpose: Cage Minecraft CPU usage to protect Hybrid Trading Bot services
# CPUQuota=150%: Caps mc-paper to ~1.5 cores on this NUC (prevents full saturation)
# Nice=10: Lower CPU scheduling priority (yielding to dashboard/engine)
# IOSchedulingClass=idle: Only use I/O when system is otherwise idle
# IOSchedulingPriority=7: Lowest I/O priority within idle class
#
# Context: BUG_2026-01-09_nuc1_mc_cpu_cage.md
# Date: 2026-01-09
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ sudo sed -n '1,200p' /etc/systemd/system/mc-paper.service.d/restart.conf
[Service]
Restart=on-failure
RestartSec=30
StartLimitIntervalSec=300
StartLimitBurst=5
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ cat /sys/fs/cgroup/system.slice/mc-paper.service/cpu.max || true
cat: /sys/fs/cgroup/system.slice/mc-paper.service/cpu.max: No such file or directory
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ cat /sys/fs/cgroup/system.slice/mc-paper.service/cpu.weight 2>/dev/null || true
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ cat /sys/fs/cgroup/system.slice/mc-paper.service/cpu.stat 2>/dev/null || true
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ systemctl show mc-paper.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus -p ExecMainCode -p MainPID --no-pager
MainPID=0
NRestarts=6
ExecMainCode=1
ExecMainStatus=0
ActiveState=activating
SubState=auto-restart
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ journalctl -u mc-paper.service -n 120 --no-pager
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]: [10:57:26 ERROR]: [org.bukkit.craftbukkit.CraftServer] null loading VeinMiner v1.0.3 (Is it up to date?)
Jan 09 10:57:27 slimy-nuc1 java[961089]: java.lang.StackOverflowError: null
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at java.base/java.util.HashMap.hash(HashMap.java:338) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at java.base/java.util.HashMap.put(HashMap.java:618) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at java.base/java.util.HashSet.add(HashSet.java:229) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at java.base/java.util.Collections$SynchronizedCollection.add(Collections.java:2325) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at me.lucko.luckperms.bukkit.inject.server.LuckPermsSubscriptionMap.subscribe(LuckPermsSubscriptionMap.java:96) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at me.lucko.luckperms.bukkit.inject.server.LuckPermsSubscriptionMap$ValueMap.put(LuckPermsSubscriptionMap.java:175) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at me.lucko.luckperms.bukkit.inject.server.LuckPermsSubscriptionMap$ValueMap.put(LuckPermsSubscriptionMap.java:164) ~[?:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at io.papermc.paper.plugin.manager.PaperPermissionManager.subscribeToPermission(PaperPermissionManager.java:113) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at io.papermc.paper.plugin.manager.PaperPluginManagerImpl.subscribeToPermission(PaperPluginManagerImpl.java:183) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.plugin.SimplePluginManager.subscribeToPermission(SimplePluginManager.java:850) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:204) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:27 slimy-nuc1 java[961089]:         at org.bukkit.permissions.PermissibleBase.calculateChildPermissions(PermissibleBase.java:207) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:57:32 slimy-nuc1 (kill)[965840]: mc-paper.service: Referenced but unset environment variable evaluates to an empty string: MAINPID
Jan 09 10:57:32 slimy-nuc1 systemd[1]: mc-paper.service: Control process exited, code=exited, status=1/FAILURE
Jan 09 10:57:32 slimy-nuc1 systemd[1]: mc-paper.service: Failed with result 'exit-code'.
Jan 09 10:57:32 slimy-nuc1 systemd[1]: mc-paper.service: Consumed 2min 32.746s CPU time.
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ /opt/hybrid-trading-bot/scripts/healthcheck.sh
[health] time: 2026-01-09T10:57:53+00:00
[health] db: /opt/hybrid-trading-bot/data/bot.db
[health] port: 8501
[health] ticks: 113536
[health] checking http://127.0.0.1:8501...
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Fri, 09 Jan 2026 10:57:53 GMT
Accept-Ranges: bytes
[health] PASS
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ uptime
 10:57:53 up 14 days,  8:36,  2 users,  load average: 4.89, 4.67, 4.65
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ cat /proc/pressure/cpu
some avg10=7.06 avg60=26.91 avg300=28.97 total=381384071680
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ cat /proc/pressure/memory
some avg10=0.00 avg60=0.00 avg300=0.00 total=11326160
full avg10=0.00 avg60=0.00 avg300=0.00 total=6348264
Exit status: 0

### 2026-01-09T10:57:53+00:00
$ top -b -n1 | head -n 30
top - 10:57:53 up 14 days,  8:36,  2 users,  load average: 4.89, 4.67, 4.65
Tasks: 172 total,   3 running, 169 sleeping,   0 stopped,   0 zombie
%Cpu(s): 52.4 us,  7.1 sy,  0.0 ni, 40.5 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
MiB Mem :  15883.3 total,   7841.7 free,    976.6 used,   7406.6 buff/cache     
MiB Swap:   4096.0 total,   3868.0 free,    228.0 used.  14906.6 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 967201 slimy     20   0 1018460  62024  45952 R 130.0   0.4   0:00.15 node
 967127 slimy     20   0 1291900 108808  51072 S  80.0   0.7   0:00.75 node /h+
 881250 root      20   0       0      0      0 I  10.0   0.0   0:00.58 kworker+
 960765 slimy     20   0   87448  42936  31232 S  10.0   0.3   0:02.21 codex
 967198 slimy     20   0   11932   5504   3456 R  10.0   0.0   0:00.01 top
 967209 slimy     20   0  746120  32980  28544 R  10.0   0.2   0:00.01 node
      1 root      20   0   22872  12688   8976 S   0.0   0.1  26:24.78 systemd
      2 root      20   0       0      0      0 S   0.0   0.0   0:00.62 kthreadd
      3 root      20   0       0      0      0 S   0.0   0.0   0:00.00 pool_wo+
      4 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      5 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      6 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      7 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      9 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     12 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     13 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     14 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     15 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     16 root      20   0       0      0      0 S   0.0   0.0   2:45.88 ksoftir+
     17 root      20   0       0      0      0 I   0.0   0.0  61:13.38 rcu_pre+
     18 root      rt   0       0      0      0 S   0.0   0.0   0:20.65 migrati+
     19 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     20 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/0
Exit status: 0


## Step 2 - Root cause hypothesis
### 2026-01-09T10:58:26+00:00
Hypothesis: Java process is crashing during plugin init (StackOverflowError from VeinMiner/LuckPerms), which triggers Restart=on-failure. Additionally, ExecStop uses $MAINPID and fails when MAINPID is unset after crash, adding a control-process failure.

Evidence excerpts (from Step 1 logs):
- journalctl shows StackOverflowError during plugin loading and repeated PermissibleBase recursion (VeinMiner/LuckPerms).
- journalctl shows: 'mc-paper.service: Referenced but unset environment variable evaluates to an empty string: MAINPID' followed by 'Control process exited, status=1/FAILURE'.
- restart.conf sets Restart=on-failure (not Restart=always), so the loop is consistent with repeated failures during startup.

## Step 3 - Apply restart sane drop-in
### 2026-01-09T10:58:44+00:00
$ sudo tee /etc/systemd/system/mc-paper.service.d/30-restart-sane.conf >/dev/null <<'EOF'
[Service]
Restart=on-failure
RestartSec=5

ExecStop=
KillSignal=SIGTERM
TimeoutStopSec=60

SuccessExitStatus=143
EOF
Exit status: 0

### 2026-01-09T10:58:44+00:00
$ sudo systemctl daemon-reload
Exit status: 0

### 2026-01-09T10:58:45+00:00
$ sudo systemctl restart mc-paper.service
Exit status: (command timed out in harness; service state verified in Step 4)

### 2026-01-09T10:59:16+00:00
Note: The previous 'sudo systemctl restart mc-paper.service' command exceeded the harness timeout (10s). Service state and logs are verified below.


## Step 4 - Verify fix
### 2026-01-09T10:59:29+00:00
$ systemctl status mc-paper.service --no-pager
● mc-paper.service - Paper Minecraft Server
     Loaded: loaded (/etc/systemd/system/mc-paper.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/mc-paper.service.d
             └─20-resources.conf, 30-restart-sane.conf, restart.conf
     Active: deactivating (stop-sigterm) since Fri 2026-01-09 10:58:45 UTC; 43s ago
   Main PID: 967807 (java)
      Tasks: 65 (limit: 18964)
     Memory: 4.5G (peak: 4.5G)
        CPU: 2min 9.180s
     CGroup: /system.slice/mc-paper.service
             └─967807 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui

Jan 09 10:59:28 slimy-nuc1 java[967807]:         at net.minecraft.server.MinecraftServer.lambda$spin$2(MinecraftServer.java:384) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at java.base/java.lang.Thread.run(Thread.java:1583) ~[?:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]: Caused by: java.lang.ClassNotFoundException: com.ssomar.score.features.types.DetailedInputFeature
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.java.PluginClassLoader.loadClass0(PluginClassLoader.java:208) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.java.PluginClassLoader.loadClass(PluginClassLoader.java:175) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:526) ~[?:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         ... 21 more
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: [ExecutableItems] Disabling ExecutableItems v7.25.11.26
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: Injector com.ssomar.score.pack.custom.PackHttpInjector unregistered (TPack selfhosting)
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: [floodgate] Enabling floodgate v2.2.5-SNAPSHOT (b121-55a85ec)
Exit status: 3

### 2026-01-09T10:59:29+00:00
$ systemctl show mc-paper.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus -p MainPID --no-pager
MainPID=967807
NRestarts=7
ExecMainStatus=0
ActiveState=deactivating
SubState=stop-sigterm
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ systemctl show mc-paper.service -p CPUAccounting -p CPUQuotaPerSecUSec -p CPUQuotaPeriodUSec -p Nice -p IOSchedulingClass -p IOSchedulingPriority --no-pager
CPUAccounting=yes
CPUQuotaPerSecUSec=1.500000s
CPUQuotaPeriodUSec=infinity
Nice=10
IOSchedulingClass=3
IOSchedulingPriority=7
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ cat /sys/fs/cgroup/system.slice/mc-paper.service/cpu.max || true
150000 100000
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ journalctl -u mc-paper.service -n 80 --no-pager
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [WolfyUtilities] init PAPI event
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [WolfyUtilities] Enabled plugin integration for PlaceholderAPI
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [NBTAPI] Enabling NBTAPI v2.15.3
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [NBTAPI] Checking bindings...
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [NBTAPI] All Classes were able to link!
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [NBTAPI] All Methods were able to link!
Jan 09 10:59:19 slimy-nuc1 java[967807]: [10:59:19 INFO]: [NBTAPI] Running NBT reflection test...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: [NBTAPI] Success! This version of NBT-API is compatible with your server.
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: [SCore] Enabling SCore v5.25.11.17
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore The library part of SCore is initializing ... (by SCore)
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore ExecutableItems hooked !  (7.25.11.26) Load After
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore PlaceholderAPI hooked !  (2.11.7)  Load Before
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Vault hooked !  (1.7.3-b131)  Load Before
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore ProtocolLib hooked !
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Locale setup: EN
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore NBTAPI hooked !  (2.15.3)  Load Before
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore WorldEdit hooked !  (7.3.17+7262-c7fbe08)  Load Before
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Language of the editor setup on EN
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore will connect to the database hosted: In Local
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Connection to the db...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore will connect to the database hosted: In Local
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table SecurityOP if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table Commands if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table Cooldowns if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table Commands Player if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table Commands Entity if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table Commands Block if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table UsePerDay if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table AbsorptionQuery if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Creating table ATemporaryAttributesQuery if not exists...
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore SCore loaded 0 delayed commands saved
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: ================ SCore ================
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore is running on Folia
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore is running on Paper or fork
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Version of the server 1.21.10-108-97452e1 (MC: 1.21.10) !
Jan 09 10:59:25 slimy-nuc1 java[967807]: [10:59:25 INFO]: SCore Language for in-game messages setup on EN
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: SCore SCore loaded 1 variables from local files !
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [SCore] CustomListsManager: Loaded entity list 'ANNOYING_MOBS' with 3 entries
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [SCore] CustomListsManager: Loaded entity list 'HOSTILE_MOBS' with 4 entries
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [SCore] CustomListsManager: Loaded block list 'STUPID_BLOCKS' with 3 entries
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [SCore] CustomListsManager: Loaded block list 'ORES' with 5 entries
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [SCore] CustomListsManager: Loaded 2 entity lists and 2 block lists
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [PlaceholderAPI] Successfully registered internal expansion: SCore [1.0.0]
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: ================ SCore ================
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: [ExecutableItems] Enabling ExecutableItems v7.25.11.26
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 INFO]: ================ ExecutableItems ================
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 ERROR]: [ExecutableItems] To make this version of EI work you may need to update SCore !
Jan 09 10:59:27 slimy-nuc1 java[967807]: [10:59:27 ERROR]: [ExecutableItems] Example if you have EI version X.25.7.23 you need SCore Y.25.7.23 or higher
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: Injector com.ssomar.score.pack.custom.PackHttpInjector registered (TPack selfhosting)
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 ERROR]: Error occurred while enabling ExecutableItems v7.25.11.26 (Is it up to date?)
Jan 09 10:59:28 slimy-nuc1 java[967807]: java.lang.NoClassDefFoundError: com/ssomar/score/features/types/DetailedInputFeature
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.activators.ActivatorEIFeature.reset(ActivatorEIFeature.java:1245) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.activators.ActivatorEIFeature.<init>(ActivatorEIFeature.java:159) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.ExecutableItem.reset(ExecutableItem.java:576) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.ExecutableItem.<init>(ExecutableItem.java:241) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.ExecutableItemLoader.getObject(ExecutableItemLoader.java:162) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at SCore-5.25.11.17.jar/com.ssomar.score.sobject.SObjectWithFileLoader.getDefaultObject(SObjectWithFileLoader.java:515) ~[SCore-5.25.11.17.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at SCore-5.25.11.17.jar/com.ssomar.score.sobject.SObjectWithFileLoader.getObjectByReader(SObjectWithFileLoader.java:493) ~[SCore-5.25.11.17.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at SCore-5.25.11.17.jar/com.ssomar.score.sobject.SObjectWithFileLoader.loadDefaultPremiumObjects(SObjectWithFileLoader.java:288) ~[SCore-5.25.11.17.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.executableitems.ExecutableItemLoader.load(ExecutableItemLoader.java:48) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at ExecutableItems-7.25.11.26.jar/com.ssomar.executableitems.ExecutableItems.onEnable(ExecutableItems.java:236) ~[ExecutableItems-7.25.11.26.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.java.JavaPlugin.setEnabled(JavaPlugin.java:279) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at io.papermc.paper.plugin.manager.PaperPluginInstanceManager.enablePlugin(PaperPluginInstanceManager.java:202) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at io.papermc.paper.plugin.manager.PaperPluginManagerImpl.enablePlugin(PaperPluginManagerImpl.java:109) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.SimplePluginManager.enablePlugin(SimplePluginManager.java:520) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.craftbukkit.CraftServer.enablePlugin(CraftServer.java:639) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.craftbukkit.CraftServer.enablePlugins(CraftServer.java:596) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at net.minecraft.server.MinecraftServer.initPostWorld(MinecraftServer.java:637) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at net.minecraft.server.dedicated.DedicatedServer.initServer(DedicatedServer.java:368) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at net.minecraft.server.MinecraftServer.runServer(MinecraftServer.java:1257) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at net.minecraft.server.MinecraftServer.lambda$spin$2(MinecraftServer.java:384) ~[paper-1.21.10.jar:1.21.10-108-97452e1]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at java.base/java.lang.Thread.run(Thread.java:1583) ~[?:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]: Caused by: java.lang.ClassNotFoundException: com.ssomar.score.features.types.DetailedInputFeature
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.java.PluginClassLoader.loadClass0(PluginClassLoader.java:208) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at org.bukkit.plugin.java.PluginClassLoader.loadClass(PluginClassLoader.java:175) ~[paper-api-1.21.10-R0.1-SNAPSHOT.jar:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         at java.base/java.lang.ClassLoader.loadClass(ClassLoader.java:526) ~[?:?]
Jan 09 10:59:28 slimy-nuc1 java[967807]:         ... 21 more
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: [ExecutableItems] Disabling ExecutableItems v7.25.11.26
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: Injector com.ssomar.score.pack.custom.PackHttpInjector unregistered (TPack selfhosting)
Jan 09 10:59:28 slimy-nuc1 java[967807]: [10:59:28 INFO]: [floodgate] Enabling floodgate v2.2.5-SNAPSHOT (b121-55a85ec)
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ /opt/hybrid-trading-bot/scripts/healthcheck.sh
[health] time: 2026-01-09T10:59:29+00:00
[health] db: /opt/hybrid-trading-bot/data/bot.db
[health] port: 8501
[health] ticks: 113728
[health] checking http://127.0.0.1:8501...
HTTP/1.1 200 OK
Server: TornadoServer/6.5.4
Content-Type: text/html
Date: Fri, 09 Jan 2026 10:59:29 GMT
Accept-Ranges: bytes
[health] PASS
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ uptime
 10:59:29 up 14 days,  8:38,  2 users,  load average: 5.22, 4.77, 4.69
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ cat /proc/pressure/cpu
some avg10=44.89 avg60=34.54 avg300=30.18 total=381416098775
full avg10=0.00 avg60=0.00 avg300=0.00 total=0
Exit status: 0

### 2026-01-09T10:59:29+00:00
$ top -b -n1 | head -n 30
top - 10:59:29 up 14 days,  8:38,  2 users,  load average: 5.22, 4.77, 4.69
Tasks: 172 total,   4 running, 168 sleeping,   0 stopped,   0 zombie
%Cpu(s): 42.2 us,  4.4 sy, 42.2 ni, 11.1 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
MiB Mem :  15883.3 total,   3206.1 free,   5611.8 used,   7407.1 buff/cache     
MiB Swap:   4096.0 total,   3868.0 free,    228.0 used.  10271.4 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 967807 slimy     30  10   11.8g   4.5g  29000 S 154.5  29.2   2:09.87 java
 971887 slimy     20   0 1024936  70132  48768 R 100.0   0.4   0:00.30 node
 971862 slimy     20   0 1291124 108316  50944 S  81.8   0.7   0:00.79 node /h+
    324 root      19  -1  461912 196520 195800 S   9.1   1.2 186:09.77 systemd+
 960765 slimy     20   0   90264  46584  31232 S   9.1   0.3   0:06.23 codex
 971927 slimy     20   0   11932   5504   3456 R   9.1   0.0   0:00.01 top
      1 root      20   0   22872  12688   8976 S   0.0   0.1  26:25.41 systemd
      2 root      20   0       0      0      0 S   0.0   0.0   0:00.62 kthreadd
      3 root      20   0       0      0      0 S   0.0   0.0   0:00.00 pool_wo+
      4 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      5 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      6 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      7 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
      9 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     12 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     13 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     14 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     15 root      20   0       0      0      0 I   0.0   0.0   0:00.00 rcu_tas+
     16 root      20   0       0      0      0 S   0.0   0.0   2:45.89 ksoftir+
     17 root      20   0       0      0      0 I   0.0   0.0  61:13.67 rcu_pre+
     18 root      rt   0       0      0      0 S   0.0   0.0   0:20.65 migrati+
     19 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     20 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/0
Exit status: 0


## Step 4b - Post-restart stabilization check
### 2026-01-09T11:00:10+00:00
$ systemctl status mc-paper.service --no-pager
● mc-paper.service - Paper Minecraft Server
     Loaded: loaded (/etc/systemd/system/mc-paper.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/mc-paper.service.d
             └─20-resources.conf, 30-restart-sane.conf, restart.conf
     Active: active (running) since Fri 2026-01-09 10:59:46 UTC; 24s ago
   Main PID: 972748 (java)
      Tasks: 27 (limit: 18964)
     Memory: 4.2G (peak: 4.2G)
        CPU: 35.256s
     CGroup: /system.slice/mc-paper.service
             └─972748 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui

Jan 09 10:59:46 slimy-nuc1 systemd[1]: Started mc-paper.service - Paper Minecraft Server.
Jan 09 11:00:09 slimy-nuc1 systemd-journald[324]: Suppressed 8209 messages from mc-paper.service
Jan 09 11:00:09 slimy-nuc1 java[972748]: [11:00:09 INFO]: Environment: Environment[sessionHost=https://sessionserver.mojang.com, servicesHost=https://api.minecraftservices.com, profilesHost=https://api.mojang.com, name=PROD]
Exit status: 0

### 2026-01-09T11:00:10+00:00
$ systemctl show mc-paper.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus -p MainPID --no-pager
MainPID=972748
NRestarts=0
ExecMainStatus=0
ActiveState=active
SubState=running
Exit status: 0


## Step 5 - Mirror drop-in to repo templates
### 2026-01-09T11:00:23+00:00
$ cat <<'EOF' > /opt/hybrid-trading-bot/ops/systemd/mc-paper.service.d/30-restart-sane.conf
[Service]
Restart=on-failure
RestartSec=5

ExecStop=
KillSignal=SIGTERM
TimeoutStopSec=60

SuccessExitStatus=143
EOF
Exit status: 0

### 2026-01-09T11:00:34+00:00
Git operations
### 2026-01-09T11:00:34+00:00
$ cd /opt/hybrid-trading-bot && git status -sb
## main...origin/main
?? docs/buglog/BUG_2026-01-08_nuc1_systemd_services.md
?? docs/buglog/BUG_2026-01-09_nuc1_hardening_portguard_health.md
?? docs/buglog/BUG_2026-01-09_nuc1_load_triage_with_minecraft_alloc.md
?? docs/buglog/BUG_2026-01-09_nuc1_mc_restart_loop_and_cpuquota_proof.md
?? ops/systemd/mc-paper.service.d/30-restart-sane.conf
Exit status: 0

### 2026-01-09T11:00:34+00:00
$ cd /opt/hybrid-trading-bot && git add docs/buglog/BUG_2026-01-09_nuc1_mc_restart_loop_and_cpuquota_proof.md ops/systemd/mc-paper.service.d/30-restart-sane.conf
Exit status: 0

### 2026-01-09T11:00:34+00:00
$ cd /opt/hybrid-trading-bot && git commit -m "ops: stabilize mc-paper restart behavior + prove CPU quota"
[main a195519] ops: stabilize mc-paper restart behavior + prove CPU quota
 2 files changed, 657 insertions(+)
 create mode 100644 docs/buglog/BUG_2026-01-09_nuc1_mc_restart_loop_and_cpuquota_proof.md
 create mode 100644 ops/systemd/mc-paper.service.d/30-restart-sane.conf
Exit status: 0

### 2026-01-09T11:00:34+00:00
$ cd /opt/hybrid-trading-bot && git push
To github.com:GurthBro0ks/hybrid-trading-bot.git
   422fc10..a195519  main -> main
Exit status: 0

