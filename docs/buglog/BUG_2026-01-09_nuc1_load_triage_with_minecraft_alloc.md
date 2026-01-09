# Flight Recorder — NUC1 Load Triage (Minecraft alloc)

**Flight Recorder ON** | TARGET: NUC1 only

## PHASE 0 — System Snapshot

### Date & Host
```
2026-01-09T09:53:03+00:00
 Static hostname: slimy-nuc1
       Icon name: computer-desktop
         Chassis: desktop 🖥️
      Machine ID: e1fa5740cad849859d544880d4181bcf
         Boot ID: 0b1750f734f24abf8566b67f4deee1b6
Operating System: Ubuntu 24.04.3 LTS
          Kernel: Linux 6.8.0-90-generic
    Architecture: x86-64
 Hardware Vendor: Intel corporation
  Hardware Model: NUC6i5SYB
Firmware Version: SYSKLi35.86A.0057.2017.0119.1758
   Firmware Date: Thu 2017-01-19
    Firmware Age: 8y 11month 2w 6d
```

### Load & Memory
```
 09:53:03 up 14 days,  7:31,  1 user,  load average: 5.56, 5.35, 5.16
               total        used        free      shared  buff/cache   available
Mem:            15Gi       5.6Gi       4.3Gi       528Ki       6.0Gi         9Gi
Swap:          4.0Gi       228Mi       3.8Gi
```

### Disk Usage
```
Filesystem                        Type   Size  Used Avail Use% Mounted on
tmpfs                             tmpfs  1.6G  1.5M  1.6G   1% /run
/dev/mapper/ubuntu--vg-ubuntu--lv ext4   233G  140G   83G  63% /
tmpfs                             tmpfs  7.8G     0  7.8G   0% /dev/shm
tmpfs                             tmpfs  5.0M     0  5.0M   0% /run/lock
/dev/nvme0n1p2                    ext4   2.0G  197M  1.6G  11% /boot
tmpfs                             tmpfs  1.6G   16K  1.6G   1% /run/user/1000
```

### Pressure Stall Information (PSI)
```
=== CPU PSI ===
some avg10=22.28 avg60=29.49 avg300=31.06 total=380143538019
full avg10=0.00 avg60=0.00 avg300=0.00 total=0

=== Memory PSI ===
some avg10=0.00 avg60=0.00 avg300=0.00 total=11325335
full avg10=0.00 avg60=0.00 avg300=0.00 total=6348231

=== I/O PSI ===
some avg10=0.01 avg60=0.12 avg300=0.07 total=1981386201
full avg10=0.00 avg60=0.00 avg300=0.00 total=422941563
```

### Top Processes (load snapshot)
```
top - 09:53:03 up 14 days,  7:31,  1 user,  load average: 5.56, 5.35, 5.16
Tasks: 170 total,   3 running, 167 sleeping,   0 stopped,   0 zombie
%Cpu(s): 89.4 us,  8.5 sy,  0.0 ni,  2.1 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st 
MiB Mem :  15883.3 total,   4366.1 free,   5705.0 used,   6154.1 buff/cache     
MiB Swap:   4096.0 total,   3867.5 free,    228.5 used.  10178.2 avail Mem 

    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 788225 slimy     20   0   11.1g   4.1g  24008 S 154.5  26.7   0:06.76 java
 788366 slimy     20   0 1290844 107284  50816 S  72.7   0.7   0:00.86 node /h+
 783844 slimy     20   0   72.2g 465224  53120 R  54.5   2.9   0:42.87 claude
 788354 slimy     20   0 1356928 108396  50944 S  18.2   0.7   0:00.88 node /h+
    992 slimy     20   0 1322456  77064  49408 S   9.1   0.5 270:54.63 PM2 v6.+
 788422 slimy     20   0   11932   5504   3456 R   9.1   0.0   0:00.01 top
      1 root      20   0   22748  12688   8976 S   0.0   0.1  26:13.14 systemd
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
     16 root      20   0       0      0      0 S   0.0   0.0   2:45.31 ksoftir+
     17 root      20   0       0      0      0 I   0.0   0.0  61:01.75 rcu_pre+
     18 root      rt   0       0      0      0 S   0.0   0.0   0:20.59 migrati+
     19 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     20 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/0
     21 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/1
     22 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     23 root      rt   0       0      0      0 S   0.0   0.0   0:21.13 migrati+
     24 root      20   0       0      0      0 S   0.0   0.0   2:41.20 ksoftir+
     26 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     27 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/2
     28 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     29 root      rt   0       0      0      0 S   0.0   0.0   0:13.18 migrati+
     30 root      20   0       0      0      0 S   0.0   0.0   2:40.80 ksoftir+
     32 root       0 -20       0      0      0 I   0.0   0.0   0:07.97 kworker+
     33 root      20   0       0      0      0 S   0.0   0.0   0:00.00 cpuhp/3
     34 root     -51   0       0      0      0 S   0.0   0.0   0:00.00 idle_in+
     35 root      rt   0       0      0      0 S   0.0   0.0   0:13.32 migrati+
     36 root      20   0       0      0      0 S   0.0   0.0   2:39.89 ksoftir+
     38 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     39 root      20   0       0      0      0 S   0.0   0.0   0:00.00 kdevtmp+
     40 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     41 root      20   0       0      0      0 S   0.0   0.0   0:00.02 kauditd
     42 root      20   0       0      0      0 S   0.0   0.0   0:00.44 khungta+
     43 root      20   0       0      0      0 S   0.0   0.0   0:00.00 oom_rea+
     45 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     47 root      20   0       0      0      0 S   0.0   0.0  10:00.86 kcompac+
     48 root      25   5       0      0      0 S   0.0   0.0   0:00.00 ksmd
     49 root      39  19       0      0      0 S   0.0   0.0   0:00.00 khugepa+
     50 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     51 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     52 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     54 root     -51   0       0      0      0 S   0.0   0.0   0:01.56 irq/9-a+
     57 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
     58 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 kworker+
```

### Top CPU Consumers
```
    PID    PPID USER      NI PRI STAT %CPU %MEM   RSS     ELAPSED CMD
 788225       1 slimy      0  19 Ssl   145 26.6 4339684     00:04 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
 788366     992 slimy      0  19 Ssl  85.1  0.6 107284      00:01 node /home/slimy/.npm-global/bin/pnpm
 788354     992 slimy      0  19 Ssl  71.5  0.6 108396      00:01 node /home/slimy/.npm-global/bin/pnpm
 783844  782337 slimy      0  19 Rl+  38.0  2.8 465216      01:52 claude --dangerously-skip-permissions
 788407       1 root       0  19 Ss   17.9  0.0  7680       00:00 /usr/lib/systemd/systemd-hostnamed
    992       1 slimy      0  19 Ssl   1.3  0.4 77064 14-07:31:48 PM2 v6.0.13: God Daemon (/home/slimy/.pm2)
    324       1 root      -1  20 S<s   0.9  0.8 140680 14-07:31:52 /usr/lib/systemd/systemd-journald
    834       1 syslog     0  19 Ssl   0.3  0.0  5096 14-07:31:49 /usr/sbin/rsyslogd -n -iNONE
     17       2 root       0  19 I     0.2  0.0     0 14-07:31:55 [rcu_preempt]
   1012     992 slimy      0  19 Ssl   0.1  0.4 80444 14-07:31:47 node /home/slimy/.npm-global/bin/pnpm
 782188       1 slimy      0  19 Ss    0.1  0.0 11008       02:18 /usr/lib/systemd/systemd --user
 782325  782169 slimy      0  19 S     0.1  0.0  6816       02:17 sshd: slimy@pts/0
      1       0 root       0  19 Ss    0.1  0.0 12688 14-07:31:55 /sbin/init
    849       1 root       0  19 Ssl   0.0  0.2 35168 14-07:31:49 /usr/bin/python3 /usr/bin/fail2ban-server -xf start
2610247       1 slimy     10   9 SNsl  0.0  0.0  7168    14:43:44 /opt/hybrid-trading-bot/engine/target/release/engine
     47       2 root       0  19 S     0.0  0.0     0 14-07:31:55 [kcompactd0]
    854       1 root       0  19 Ssl   0.0  0.0 14208 14-07:31:49 /usr/bin/containerd
 782337  782325 slimy      0  19 Ss    0.0  0.0  5760       02:17 -bash
    714       1 message+   0  19 Ss    0.0  0.0  5376 14-07:31:50 @dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
 712627       2 root       0  19 I     0.0  0.0     0       28:09 [kworker/u8:2-iou_exit]
 744815       2 root       0  19 I     0.0  0.0     0       16:12 [kworker/u8:1-iou_exit]
    827       1 root       0  19 Ssl   0.0  0.1 17700 14-07:31:49 /usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock --port=41641
 381164       2 root       0  19 I     0.0  0.0     0    02:31:44 [kworker/u8:5-flush-252:0]
 744821       2 root       0  19 I     0.0  0.0     0       16:12 [kworker/u8:3-events_unbound]
 574269       2 root       0  19 I     0.0  0.0     0    01:19:47 [kworker/u8:4-iou_exit]
 765479       2 root       0  19 I     0.0  0.0     0       08:28 [kworker/0:2-events]
 779385       2 root       0  19 I     0.0  0.0     0       03:22 [kworker/0:0-events]
 718571       2 root       0  19 I     0.0  0.0     0       26:02 [kworker/u8:7-events_unbound]
 779163       2 root       0  19 I     0.0  0.0     0       03:28 [kworker/u8:6-iou_exit]
```

### Top Memory Consumers
```
    PID    PPID USER      NI PRI STAT %CPU %MEM   RSS     ELAPSED CMD
 788225       1 slimy      0  19 Ssl   145 26.6 4341220     00:04 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
 783844  782337 slimy      0  19 Rl+  38.0  2.8 465216      01:52 claude --dangerously-skip-permissions
    324       1 root      -1  20 S<s   0.9  0.8 140680 14-07:31:52 /usr/lib/systemd/systemd-journald
 788366     992 slimy      0  19 Ssl  83.4  0.6 107284      00:01 node /home/slimy/.npm-global/bin/pnpm
   1012     992 slimy      0  19 Ssl   0.1  0.4 80444 14-07:31:47 node /home/slimy/.npm-global/bin/pnpm
    992       1 slimy      0  19 Ssl   1.3  0.4 77064 14-07:31:48 PM2 v6.0.13: God Daemon (/home/slimy/.pm2)
2611036       1 slimy      0  19 Ss    0.0  0.3 50600    14:43:13 /opt/hybrid-trading-bot/dashboard/.venv/bin/python /opt/hybrid-trading-bot/dashboard/.venv/bin/streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
   1097    1096 slimy      0  19 Sl    0.0  0.3 49332 14-07:31:46 next-server (v16.0.1)
    847       1 slimy      0  19 Ssl   0.0  0.2 48636 14-07:31:49 npm run start
   1014    1013 slimy      0  19 Sl    0.0  0.2 47984 14-07:31:47 next-server (v14.2.5)
    849       1 root       0  19 Ssl   0.0  0.2 35168 14-07:31:49 /usr/bin/python3 /usr/bin/fail2ban-server -xf start
1049170       1 root       0  19 Ssl   0.0  0.2 32884  2-03:12:10 /usr/libexec/fwupd/fwupd
 788430  788429 slimy      0  19 Rl    0.0  0.1 29952       00:00 node /opt/slimy/slimy-monorepo/apps/admin-ui/node_modules/.bin/../next/dist/bin/next start -p 3081
    360       1 root       - 139 SLsl  0.0  0.1 26880 14-07:31:52 /sbin/multipathd -d -s
   1337       1 root       0  19 Ssl   0.0  0.1 25808 14-07:31:41 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
    827       1 root       0  19 Ssl   0.0  0.1 17700 14-07:31:49 /usr/sbin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock --port=41641
   1336       1 caddy      0  19 Ssl   0.0  0.0 15204 14-07:31:41 /usr/bin/caddy run --environ --config /etc/caddy/Caddyfile
    854       1 root       0  19 Ssl   0.0  0.0 14208 14-07:31:49 /usr/bin/containerd
      1       0 root       0  19 Ss    0.1  0.0 12688 14-07:31:55 /sbin/init
 782188       1 slimy      0  19 Ss    0.1  0.0 11008       02:18 /usr/lib/systemd/systemd --user
   1339       1 ollama     0  19 Ssl   0.0  0.0 10496 14-07:31:41 /usr/local/bin/ollama serve
 782169    1362 root       0  19 Ss    0.0  0.0 10112       02:18 sshd: slimy [priv]
    549       1 systemd+   0  19 Ss    0.0  0.0  8960 14-07:31:51 /usr/lib/systemd/systemd-resolved
    825       1 systemd+   0  19 Ss    0.0  0.0  8192 14-07:31:49 /usr/lib/systemd/systemd-networkd
    731       1 root       0  19 Ss    0.0  0.0  7808 14-07:31:50 /usr/lib/systemd/systemd-logind
 788407       1 root       0  19 Ss   17.0  0.0  7680       00:00 /usr/lib/systemd/systemd-hostnamed
1049172       1 root       0  19 Ssl   0.0  0.0  7680  2-03:12:10 /usr/libexec/udisks2/udisksd
2610247       1 slimy     10   9 SNsl  0.0  0.0  7168    14:43:44 /opt/hybrid-trading-bot/engine/target/release/engine
1049323       1 root       0  19 Ssl   0.0  0.0  7040  2-03:12:08 /usr/sbin/thermald --systemd --dbus-enable --adaptive
```

## PHASE 1 — Minecraft Candidate Detection

### Candidate Services (systemd units)
```
mc-backup.service                            static          -
mc-paper.service                             enabled         enabled
mc-restart.service                           static          -
```

### Running Services (filtered)
```
  mc-paper.service            loaded active running Paper Minecraft Server
```

### Candidate Java Processes
```
 788225       1 slimy     140 26.8 4367588     00:06 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
 788380  783844 slimy     0.0  0.0  3840       00:02 /bin/bash -c -l source /home/slimy/.claude/shell-snapshots/snapshot-bash-1767952272690-l2zmnm.sh && { shopt -u extglob || setopt NO_EXTENDED_GLOB; } 2>/dev/null || true && eval ' # Determine working directory and set up buglog if [ -d "/opt/hybrid-trading-bot" ]; then   BASE_DIR="/opt/hybrid-trading-bot" else   BASE_DIR="$HOME/hybrid_trading_flightrec" fi  mkdir -p "$BASE_DIR/docs/buglog" 2>/dev/null BUGLOG="$BASE_DIR/docs/buglog/BUG_2026-01-09_nuc1_load_triage_with_minecraft_alloc.md"  # Initialize buglog echo "# Flight Recorder — NUC1 Load Triage (Minecraft alloc)" > "$BUGLOG" echo "" >> "$BUGLOG" echo "**Flight Recorder ON** | TARGET: NUC1 only" >> "$BUGLOG" echo "" >> "$BUGLOG"  # PHASE 0 — Snapshot (no changes) {   echo "## PHASE 0 — System Snapshot"   echo ""   echo "### Date & Host"   echo '"'"'```'"'"'   date -Is   hostnamectl   echo '"'"'```'"'"'   echo ""   echo "### Load & Memory"   echo '"'"'```'"'"'   uptime   free -h   echo '"'"'```'"'"'   echo ""   echo "### Disk Usage"   echo '"'"'```'"'"'   df -hT   echo '"'"'```'"'"'   echo ""   echo "### Pressure Stall Information (PSI)"   echo '"'"'```'"'"'   echo "=== CPU PSI ==="   cat /proc/pressure/cpu 2>/dev/null || echo "N/A"   echo ""   echo "=== Memory PSI ==="   cat /proc/pressure/memory 2>/dev/null || echo "N/A"   echo ""   echo "=== I/O PSI ==="   cat /proc/pressure/io 2>/dev/null || echo "N/A"   echo '"'"'```'"'"'   echo ""   echo "### Top Processes (load snapshot)"   echo '"'"'```'"'"'   top -b -n 1 | head -n 60   echo '"'"'```'"'"'   echo ""   echo "### Top CPU Consumers"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,ni,pri,stat,%cpu,%mem,rss,etime,cmd --sort=-%cpu | head -n 30   echo '"'"'```'"'"'   echo ""   echo "### Top Memory Consumers"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,ni,pri,stat,%cpu,%mem,rss,etime,cmd --sort=-%mem | head -n 30   echo '"'"'```'"'"' } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 1 — Detect Minecraft candidates {   echo "## PHASE 1 — Minecraft Candidate Detection"   echo ""   echo "### Candidate Services (systemd units)"   echo '"'"'```'"'"'   systemctl list-unit-files --type=service --no-pager | egrep -i "mine|minecraft|paper|spigot|bukkit|mc" || echo "No matches"   echo '"'"'```'"'"'   echo ""   echo "### Running Services (filtered)"   echo '"'"'```'"'"'   systemctl list-units --type=service --state=running --no-pager | egrep -i "mine|minecraft|paper|spigot|bukkit|mc|java" || echo "No matches"   echo '"'"'```'"'"'   echo ""   echo "### Candidate Java Processes"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,%cpu,%mem,rss,etime,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" || echo "No matches"   echo '"'"'```'"'"' } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 2 — Detect MC service and dump systemd config {   echo "## PHASE 2 — Minecraft systemd Configuration"   echo ""      MC_UNIT=$(systemctl list-unit-files --type=service --no-pager | awk '"'"'{print $1}'"'"' | egrep -i "minecraft|paper|spigot|mc" | head -n 1 || true)   echo "### Detected MC Unit: \`$MC_UNIT\`"   echo ""      if [ -n "${MC_UNIT:-}" ]; then     echo '"'"'```'"'"'     echo "=== systemctl cat $MC_UNIT ==="     systemctl cat "$MC_UNIT" --no-pager || true     echo '"'"'```'"'"'     echo ""     echo "### Resource Limits"     echo '"'"'```'"'"'     systemctl show "$MC_UNIT" --no-pager \       -p CPUQuota -p CPUQuotaPerSecUSec -p AllowedCPUs \       -p MemoryMax -p MemoryHigh -p MemorySwapMax \       -p TasksMax -p LimitNOFILE -p LimitNPROC \       -p Nice -p OOMScoreAdjust -p Restart \       -p ExecStart -p ExecStop || true     echo '"'"'```'"'"'     echo ""     echo "### Control Group Path"     echo '"'"'```'"'"'     systemctl show "$MC_UNIT" --no-pager -p ControlGroup || true     echo '"'"'```'"'"'   else     echo "⚠️ No Minecraft service unit detected"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 3 — JVM flags and live Java stats {   echo "## PHASE 3 — JVM Allocation Flags & Live Stats"   echo ""      MC_PID=$(ps -eo pid,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" | awk '"'"'NR==1{print $1}'"'"' || true)   echo "### Detected MC PID: \`$MC_PID\`"   echo ""      if [ -n "${MC_PID:-}" ]; then     echo "### Command Line (JVM flags)"     echo '"'"'```'"'"'     tr '"'"'\0'"'"' '"'"' '"'"' < /proc/$MC_PID/cmdline 2>/dev/null; echo     echo '"'"'```'"'"'     echo ""     echo "### Virtual Memory & Threads"     echo '"'"'```'"'"'     egrep "VmRSS|VmSize|VmPeak|Threads|voluntary_ctxt_switches|nonvoluntary_ctxt_switches" /proc/$MC_PID/status 2>/dev/null || true     echo '"'"'```'"'"'     echo ""     echo "### Resource Limits (ulimits)"     echo '"'"'```'"'"'     cat /proc/$MC_PID/limits 2>/dev/null || true     echo '"'"'```'"'"'     echo ""     echo "### Process Snapshot"     echo '"'"'```'"'"'     ps -p $MC_PID -o pid,%cpu,%mem,rss,etime,cmd --no-headers 2>/dev/null || true     echo '"'"'```'"'"'     echo ""          # Optional: jcmd     if command -v jcmd >/dev/null 2>&1; then       echo "### JVM VM Flags"       echo '"'"'```'"'"'       jcmd "$MC_PID" VM.flags 2>/dev/null || echo "jcmd failed"       echo '"'"'```'"'"'       echo ""     else       echo "⚠️ jcmd not available (non-fatal)"       echo ""     fi   else     echo "⚠️ No Minecraft Java process detected"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 4 — Docker snapshot (if applicable) {   echo "## PHASE 4 — Docker Status (if applicable)"   echo ""      if command -v docker >/dev/null 2>&1; then     echo "### Docker Stats"     echo '"'"'```'"'"'     docker stats --no-stream 2>/dev/null || echo "docker stats failed"     echo '"'"'```'"'"'     echo ""     echo "### Docker Containers"     echo '"'"'```'"'"'     docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "docker ps failed"     echo '"'"'```'"'"'   else     echo "⚠️ Docker not available"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 5 — Summary {   echo "## PHASE 5 — Summary"   echo ""      MC_UNIT=$(systemctl list-unit-files --type=service --no-pager | awk '"'"'{print $1}'"'"' | egrep -i "minecraft|paper|spigot|mc" | head -n 1 || true)   MC_PID=$(ps -eo pid,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" | awk '"'"'NR==1{print $1}'"'"' || true)      echo "### Minecraft Status"   if [ -n "${MC_UNIT:-}" ] || [ -n "${MC_PID:-}" ]; then     echo "✅ **Minecraft appears to be running or installed**"     if [ -n "${MC_UNIT:-}" ]; then       echo "- Service: \`$MC_UNIT\`"     fi     if [ -n "${MC_PID:-}" ]; then       echo "- Process PID: \`$MC_PID\`"     fi   else     echo "❌ **No Minecraft service or process detected**"   fi   echo ""      echo "### Top 3 CPU Offenders"   echo '"'"'```'"'"'   ps -eo pid,user,%cpu,%mem,rss,cmd --sort=-%cpu | head -n 4   echo '"'"'```'"'"'   echo ""      echo "### Top 3 Memory Offenders"   echo '"'"'```'"'"'   ps -eo pid,user,%cpu,%mem,rss,cmd --sort=-%mem | head -n 4   echo '"'"'```'"'"'   echo ""      echo "### System Resource Status"   echo '"'"'```'"'"'   echo "Memory: $(free -h | awk '"'"'/^Mem:/{print $3 " / " $2}'"'"')"   echo "Load Avg: $(uptime | awk -F'"'"'load average:'"'"' '"'"'{print $2}'"'"')"   echo '"'"'```'"'"'   echo ""   echo "---"   echo "📋 Full diagnostic logged to: \`$BUGLOG\`" } | tee -a "$BUGLOG"  echo "" echo "✅ Flight Recorder Complete!" echo "📄 Report saved to: $BUGLOG" ' && pwd -P >| /tmp/claude-b22c-cwd
 788447  788380 slimy     0.0  0.0  2004       00:01 /bin/bash -c -l source /home/slimy/.claude/shell-snapshots/snapshot-bash-1767952272690-l2zmnm.sh && { shopt -u extglob || setopt NO_EXTENDED_GLOB; } 2>/dev/null || true && eval ' # Determine working directory and set up buglog if [ -d "/opt/hybrid-trading-bot" ]; then   BASE_DIR="/opt/hybrid-trading-bot" else   BASE_DIR="$HOME/hybrid_trading_flightrec" fi  mkdir -p "$BASE_DIR/docs/buglog" 2>/dev/null BUGLOG="$BASE_DIR/docs/buglog/BUG_2026-01-09_nuc1_load_triage_with_minecraft_alloc.md"  # Initialize buglog echo "# Flight Recorder — NUC1 Load Triage (Minecraft alloc)" > "$BUGLOG" echo "" >> "$BUGLOG" echo "**Flight Recorder ON** | TARGET: NUC1 only" >> "$BUGLOG" echo "" >> "$BUGLOG"  # PHASE 0 — Snapshot (no changes) {   echo "## PHASE 0 — System Snapshot"   echo ""   echo "### Date & Host"   echo '"'"'```'"'"'   date -Is   hostnamectl   echo '"'"'```'"'"'   echo ""   echo "### Load & Memory"   echo '"'"'```'"'"'   uptime   free -h   echo '"'"'```'"'"'   echo ""   echo "### Disk Usage"   echo '"'"'```'"'"'   df -hT   echo '"'"'```'"'"'   echo ""   echo "### Pressure Stall Information (PSI)"   echo '"'"'```'"'"'   echo "=== CPU PSI ==="   cat /proc/pressure/cpu 2>/dev/null || echo "N/A"   echo ""   echo "=== Memory PSI ==="   cat /proc/pressure/memory 2>/dev/null || echo "N/A"   echo ""   echo "=== I/O PSI ==="   cat /proc/pressure/io 2>/dev/null || echo "N/A"   echo '"'"'```'"'"'   echo ""   echo "### Top Processes (load snapshot)"   echo '"'"'```'"'"'   top -b -n 1 | head -n 60   echo '"'"'```'"'"'   echo ""   echo "### Top CPU Consumers"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,ni,pri,stat,%cpu,%mem,rss,etime,cmd --sort=-%cpu | head -n 30   echo '"'"'```'"'"'   echo ""   echo "### Top Memory Consumers"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,ni,pri,stat,%cpu,%mem,rss,etime,cmd --sort=-%mem | head -n 30   echo '"'"'```'"'"' } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 1 — Detect Minecraft candidates {   echo "## PHASE 1 — Minecraft Candidate Detection"   echo ""   echo "### Candidate Services (systemd units)"   echo '"'"'```'"'"'   systemctl list-unit-files --type=service --no-pager | egrep -i "mine|minecraft|paper|spigot|bukkit|mc" || echo "No matches"   echo '"'"'```'"'"'   echo ""   echo "### Running Services (filtered)"   echo '"'"'```'"'"'   systemctl list-units --type=service --state=running --no-pager | egrep -i "mine|minecraft|paper|spigot|bukkit|mc|java" || echo "No matches"   echo '"'"'```'"'"'   echo ""   echo "### Candidate Java Processes"   echo '"'"'```'"'"'   ps -eo pid,ppid,user,%cpu,%mem,rss,etime,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" || echo "No matches"   echo '"'"'```'"'"' } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 2 — Detect MC service and dump systemd config {   echo "## PHASE 2 — Minecraft systemd Configuration"   echo ""      MC_UNIT=$(systemctl list-unit-files --type=service --no-pager | awk '"'"'{print $1}'"'"' | egrep -i "minecraft|paper|spigot|mc" | head -n 1 || true)   echo "### Detected MC Unit: \`$MC_UNIT\`"   echo ""      if [ -n "${MC_UNIT:-}" ]; then     echo '"'"'```'"'"'     echo "=== systemctl cat $MC_UNIT ==="     systemctl cat "$MC_UNIT" --no-pager || true     echo '"'"'```'"'"'     echo ""     echo "### Resource Limits"     echo '"'"'```'"'"'     systemctl show "$MC_UNIT" --no-pager \       -p CPUQuota -p CPUQuotaPerSecUSec -p AllowedCPUs \       -p MemoryMax -p MemoryHigh -p MemorySwapMax \       -p TasksMax -p LimitNOFILE -p LimitNPROC \       -p Nice -p OOMScoreAdjust -p Restart \       -p ExecStart -p ExecStop || true     echo '"'"'```'"'"'     echo ""     echo "### Control Group Path"     echo '"'"'```'"'"'     systemctl show "$MC_UNIT" --no-pager -p ControlGroup || true     echo '"'"'```'"'"'   else     echo "⚠️ No Minecraft service unit detected"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 3 — JVM flags and live Java stats {   echo "## PHASE 3 — JVM Allocation Flags & Live Stats"   echo ""      MC_PID=$(ps -eo pid,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" | awk '"'"'NR==1{print $1}'"'"' || true)   echo "### Detected MC PID: \`$MC_PID\`"   echo ""      if [ -n "${MC_PID:-}" ]; then     echo "### Command Line (JVM flags)"     echo '"'"'```'"'"'     tr '"'"'\0'"'"' '"'"' '"'"' < /proc/$MC_PID/cmdline 2>/dev/null; echo     echo '"'"'```'"'"'     echo ""     echo "### Virtual Memory & Threads"     echo '"'"'```'"'"'     egrep "VmRSS|VmSize|VmPeak|Threads|voluntary_ctxt_switches|nonvoluntary_ctxt_switches" /proc/$MC_PID/status 2>/dev/null || true     echo '"'"'```'"'"'     echo ""     echo "### Resource Limits (ulimits)"     echo '"'"'```'"'"'     cat /proc/$MC_PID/limits 2>/dev/null || true     echo '"'"'```'"'"'     echo ""     echo "### Process Snapshot"     echo '"'"'```'"'"'     ps -p $MC_PID -o pid,%cpu,%mem,rss,etime,cmd --no-headers 2>/dev/null || true     echo '"'"'```'"'"'     echo ""          # Optional: jcmd     if command -v jcmd >/dev/null 2>&1; then       echo "### JVM VM Flags"       echo '"'"'```'"'"'       jcmd "$MC_PID" VM.flags 2>/dev/null || echo "jcmd failed"       echo '"'"'```'"'"'       echo ""     else       echo "⚠️ jcmd not available (non-fatal)"       echo ""     fi   else     echo "⚠️ No Minecraft Java process detected"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 4 — Docker snapshot (if applicable) {   echo "## PHASE 4 — Docker Status (if applicable)"   echo ""      if command -v docker >/dev/null 2>&1; then     echo "### Docker Stats"     echo '"'"'```'"'"'     docker stats --no-stream 2>/dev/null || echo "docker stats failed"     echo '"'"'```'"'"'     echo ""     echo "### Docker Containers"     echo '"'"'```'"'"'     docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "docker ps failed"     echo '"'"'```'"'"'   else     echo "⚠️ Docker not available"   fi } | tee -a "$BUGLOG"  echo "" | tee -a "$BUGLOG"  # PHASE 5 — Summary {   echo "## PHASE 5 — Summary"   echo ""      MC_UNIT=$(systemctl list-unit-files --type=service --no-pager | awk '"'"'{print $1}'"'"' | egrep -i "minecraft|paper|spigot|mc" | head -n 1 || true)   MC_PID=$(ps -eo pid,cmd | egrep -i "java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server" | awk '"'"'NR==1{print $1}'"'"' || true)      echo "### Minecraft Status"   if [ -n "${MC_UNIT:-}" ] || [ -n "${MC_PID:-}" ]; then     echo "✅ **Minecraft appears to be running or installed**"     if [ -n "${MC_UNIT:-}" ]; then       echo "- Service: \`$MC_UNIT\`"     fi     if [ -n "${MC_PID:-}" ]; then       echo "- Process PID: \`$MC_PID\`"     fi   else     echo "❌ **No Minecraft service or process detected**"   fi   echo ""      echo "### Top 3 CPU Offenders"   echo '"'"'```'"'"'   ps -eo pid,user,%cpu,%mem,rss,cmd --sort=-%cpu | head -n 4   echo '"'"'```'"'"'   echo ""      echo "### Top 3 Memory Offenders"   echo '"'"'```'"'"'   ps -eo pid,user,%cpu,%mem,rss,cmd --sort=-%mem | head -n 4   echo '"'"'```'"'"'   echo ""      echo "### System Resource Status"   echo '"'"'```'"'"'   echo "Memory: $(free -h | awk '"'"'/^Mem:/{print $3 " / " $2}'"'"')"   echo "Load Avg: $(uptime | awk -F'"'"'load average:'"'"' '"'"'{print $2}'"'"')"   echo '"'"'```'"'"'   echo ""   echo "---"   echo "📋 Full diagnostic logged to: \`$BUGLOG\`" } | tee -a "$BUGLOG"  echo "" echo "✅ Flight Recorder Complete!" echo "📄 Report saved to: $BUGLOG" ' && pwd -P >| /tmp/claude-b22c-cwd
 788530  788447 slimy     0.0  0.0  2304       00:00 grep -E -i java.*(paper|spigot|minecraft|bukkit|forge|fabric)|paper\.jar|spigot\.jar|minecraft_server
```

## PHASE 2 — Minecraft systemd Configuration

### Detected MC Unit: `mc-backup.service`

```
=== systemctl cat mc-backup.service ===
# /etc/systemd/system/mc-backup.service
[Unit]
Description=Minecraft backup (tar worlds + configs)

[Service]
Type=oneshot
User=slimy
ExecStart=/opt/slimy/scripts/backup-mc.sh
```

### Resource Limits
```
Restart=no
ExecStart={ path=/opt/slimy/scripts/backup-mc.sh ; argv[]=/opt/slimy/scripts/backup-mc.sh ; ignore_errors=no ; start_time=[Fri 2026-01-09 03:30:00 UTC] ; stop_time=[Fri 2026-01-09 03:30:20 UTC] ; pid=3951635 ; code=exited ; status=0 }
CPUQuotaPerSecUSec=infinity
AllowedCPUs=
MemoryHigh=infinity
MemoryMax=infinity
MemorySwapMax=infinity
TasksMax=18964
LimitNOFILE=524288
LimitNPROC=63213
OOMScoreAdjust=0
Nice=0
```

### Control Group Path
```
ControlGroup=
```

## PHASE 3 — JVM Allocation Flags & Live Stats

### Detected MC PID: `788225`

### Command Line (JVM flags)
```
/usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui 
```

### Virtual Memory & Threads
```
VmPeak:	12075448 kB
VmSize:	12009912 kB
VmRSS:	 4371808 kB
Threads:	29
voluntary_ctxt_switches:	2
nonvoluntary_ctxt_switches:	7
```

### Resource Limits (ulimits)
```
Limit                     Soft Limit           Hard Limit           Units     
Max cpu time              unlimited            unlimited            seconds   
Max file size             unlimited            unlimited            bytes     
Max data size             unlimited            unlimited            bytes     
Max stack size            8388608              unlimited            bytes     
Max core file size        0                    unlimited            bytes     
Max resident set          unlimited            unlimited            bytes     
Max processes             63213                63213                processes 
Max open files            524288               524288               files     
Max locked memory         8388608              8388608              bytes     
Max address space         unlimited            unlimited            bytes     
Max file locks            unlimited            unlimited            locks     
Max pending signals       63213                63213                signals   
Max msgqueue size         819200               819200               bytes     
Max nice priority         0                    0                    
Max realtime priority     0                    0                    
Max realtime timeout      unlimited            unlimited            us        
```

### Process Snapshot
```
 788225  131 26.8 4372064     00:08 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
```

### JVM VM Flags
```
788225:
-XX:+AlwaysPreTouch -XX:-AlwaysTenure -XX:CICompilerCount=3 -XX:ConcGCThreads=1 -XX:+DisableExplicitGC -XX:G1ConcRefinementThreads=4 -XX:G1EagerReclaimRemSetThreshold=128 -XX:G1HeapRegionSize=16777216 -XX:G1HeapWastePercent=5 -XX:G1MaxNewSizePercent=40 -XX:G1MixedGCCountTarget=4 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1NewSizePercent=30 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:G1RemSetArrayOfCardsEntries=128 -XX:G1RemSetHowlMaxNumBuckets=8 -XX:G1RemSetHowlNumBuckets=8 -XX:G1ReservePercent=20 -XX:GCDrainStackTargetSize=64 -XX:InitialHeapSize=4294967296 -XX:InitialTenuringThreshold=1 -XX:InitiatingHeapOccupancyPercent=15 -XX:MarkStackSize=4194304 -XX:MaxGCPauseMillis=200 -XX:MaxHeapSize=8589934592 -XX:MaxNewSize=3422552064 -XX:MaxTenuringThreshold=1 -XX:MinHeapDeltaBytes=16777216 -XX:MinHeapSize=4294967296 -XX:-NeverTenure -XX:NonNMethodCodeHeapSize=5832780 -XX:NonProfiledCodeHeapSize=122912730 -XX:+ParallelRefProcEnabled -XX:+PerfDisableSharedMem -XX:ProfiledCodeHeapSize=122912730 -XX:ReservedCodeCacheSize=251658240 -XX:+SegmentedCodeCache -XX:SoftMaxHeapSize=8589934592 -XX:SurvivorRatio=32 -XX:-THPStackMitigation -XX:+UnlockExperimentalVMOptions -XX:+UseCompressedOops -XX:+UseFastUnorderedTimeStamps -XX:+UseG1GC 
```


## PHASE 4 — Docker Status (if applicable)

### Docker Stats
```
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O   BLOCK I/O   PIDS
```

### Docker Containers
```
NAMES     STATUS    PORTS
```

## PHASE 5 — Summary

### Minecraft Status
✅ **Minecraft appears to be running or installed**
- Service: `mc-backup.service`
- Process PID: `788225`

### Top 3 CPU Offenders
```
    PID USER     %CPU %MEM   RSS CMD
 788225 slimy     133 26.9 4385376 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
 788703 slimy    93.8  0.6 98700 node /home/slimy/.npm-global/bin/pnpm
 788679 slimy    59.5  0.6 107640 node /home/slimy/.npm-global/bin/pnpm
```

### Top 3 Memory Offenders
```
    PID USER     %CPU %MEM   RSS CMD
 788225 slimy     133 26.9 4385376 /usr/bin/java --add-opens=java.base/java.util.concurrent.locks=ALL-UNNAMED -Xms4G -Xmx8G -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 -XX:+UnlockExperimentalVMOptions -XX:+DisableExplicitGC -XX:+AlwaysPreTouch -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=16M -XX:G1ReservePercent=20 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=4 -XX:InitiatingHeapOccupancyPercent=15 -XX:G1MixedGCLiveThresholdPercent=90 -XX:G1RSetUpdatingPauseTimePercent=5 -XX:SurvivorRatio=32 -XX:+PerfDisableSharedMem -XX:MaxTenuringThreshold=1 -Dfile.encoding=UTF-8 --add-opens=java.base/java.net=ALL-UNNAMED --add-opens=java.base/java.lang.ref=ALL-UNNAMED -jar /opt/slimy/minecraft/paper-1.21-latest.jar --nogui
 783844 slimy    39.0  3.2 534744 claude --dangerously-skip-permissions
    324 root      0.9  0.8 140680 /usr/lib/systemd/systemd-journald
```

### System Resource Status
```
Memory: 5.7Gi / 15Gi
Load Avg:  5.84, 5.41, 5.18
```

---
📋 Full diagnostic logged to: `/opt/hybrid-trading-bot/docs/buglog/BUG_2026-01-09_nuc1_load_triage_with_minecraft_alloc.md`
