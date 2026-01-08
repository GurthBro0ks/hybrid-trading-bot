# Flight Recorder — Laptop proof loop run
2026-01-08T13:31:13-05:00
mint
mint
/home/mint/Desktop/hybrid-trading-bot
## main...origin/main
?? docs/buglog/BUG_2026-01-08_laptop_proof_loop_run.md
79e8b6f proof: rust->sqlite(wal)->streamlit fragment loop
sqlite3 missing
rustc missing
cargo missing
Python 3.12.3
Ign:1 cdrom://Linux Mint 22.2 _Zara_ - Release amd64 20250828 noble InRelease
Err:2 cdrom://Linux Mint 22.2 _Zara_ - Release amd64 20250828 noble Release
  Please use apt-cdrom to make this CD-ROM recognized by APT. apt-get update cannot be used to add new CD-ROMs
Ign:3 http://packages.linuxmint.com zara InRelease
Hit:4 http://packages.linuxmint.com zara Release
Get:5 https://cli.github.com/packages stable InRelease [3917 B]
Hit:6 https://download.docker.com/linux/ubuntu noble InRelease
Get:8 http://security.ubuntu.com/ubuntu noble-security InRelease [126 kB]
Hit:9 http://archive.ubuntu.com/ubuntu noble InRelease
Hit:10 https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev antigravity-debian InRelease
Get:11 http://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
Hit:12 https://dl.google.com/linux/chrome/deb stable InRelease
Get:13 http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages [1396 kB]
Get:14 http://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
Get:15 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages [1687 kB]
Get:16 http://security.ubuntu.com/ubuntu noble-security/main Translation-en [227 kB]
Get:17 http://security.ubuntu.com/ubuntu noble-security/main amd64 Components [21.5 kB]
Get:18 http://security.ubuntu.com/ubuntu noble-security/restricted amd64 Components [212 B]
Get:19 http://security.ubuntu.com/ubuntu noble-security/universe amd64 Packages [920 kB]
Get:20 http://security.ubuntu.com/ubuntu noble-security/universe Translation-en [208 kB]
Get:21 http://security.ubuntu.com/ubuntu noble-security/universe amd64 Components [71.4 kB]
Get:22 http://archive.ubuntu.com/ubuntu noble-updates/main i386 Packages [567 kB]
Get:23 http://security.ubuntu.com/ubuntu noble-security/multiverse amd64 Components [212 B]
Get:24 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Components [175 kB]
Get:25 http://archive.ubuntu.com/ubuntu noble-updates/restricted amd64 Components [212 B]
Get:26 http://archive.ubuntu.com/ubuntu noble-updates/universe i386 Packages [993 kB]
Get:27 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 Packages [1507 kB]
Get:28 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 Components [377 kB]
Get:29 http://archive.ubuntu.com/ubuntu noble-updates/multiverse amd64 Components [940 B]
Get:30 http://archive.ubuntu.com/ubuntu noble-backports/main amd64 Components [7304 B]
Get:31 http://archive.ubuntu.com/ubuntu noble-backports/restricted amd64 Components [216 B]
Get:32 http://archive.ubuntu.com/ubuntu noble-backports/universe amd64 Components [10.5 kB]
Get:33 http://archive.ubuntu.com/ubuntu noble-backports/multiverse amd64 Components [212 B]
Reading package lists...
Reading package lists...
Building dependency tree...
Reading state information...
The following additional packages will be installed:
  libsqlite3-0
Suggested packages:
  sqlite3-doc
The following NEW packages will be installed:
  libsqlite3-dev sqlite3
The following packages will be upgraded:
  libsqlite3-0
1 upgraded, 2 newly installed, 0 to remove and 229 not upgraded.
Need to get 1756 kB of archives.
After this operation, 3987 kB of additional disk space will be used.
Get:1 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsqlite3-0 amd64 3.45.1-1ubuntu2.5 [701 kB]
Get:2 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsqlite3-dev amd64 3.45.1-1ubuntu2.5 [911 kB]
Get:3 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 sqlite3 amd64 3.45.1-1ubuntu2.5 [144 kB]
Fetched 1756 kB in 5s (366 kB/s)
(Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 585320 files and directories currently installed.)
Preparing to unpack .../libsqlite3-0_3.45.1-1ubuntu2.5_amd64.deb ...
Unpacking libsqlite3-0:amd64 (3.45.1-1ubuntu2.5) over (3.45.1-1ubuntu2.4) ...
Selecting previously unselected package libsqlite3-dev:amd64.
Preparing to unpack .../libsqlite3-dev_3.45.1-1ubuntu2.5_amd64.deb ...
Unpacking libsqlite3-dev:amd64 (3.45.1-1ubuntu2.5) ...
Selecting previously unselected package sqlite3.
Preparing to unpack .../sqlite3_3.45.1-1ubuntu2.5_amd64.deb ...
Unpacking sqlite3 (3.45.1-1ubuntu2.5) ...
Setting up libsqlite3-0:amd64 (3.45.1-1ubuntu2.5) ...
Setting up libsqlite3-dev:amd64 (3.45.1-1ubuntu2.5) ...
Setting up sqlite3 (3.45.1-1ubuntu2.5) ...
Processing triggers for man-db (2.12.0-4build2) ...
Processing triggers for libc-bin (2.39-0ubuntu8.6) ...

  stable-x86_64-unknown-linux-gnu installed - rustc 1.92.0 (ded5c06cf 2025-12-08)


Rust is installed now. Great!

To get started you may need to restart your current shell.
This would reload your PATH environment variable to include
Cargo's bin directory ($HOME/.cargo/bin).

To configure your current shell, you need to source
the corresponding env file under $HOME/.cargo.

This is usually done by running one of the following (note the leading DOT):
. "$HOME/.cargo/env"            # For sh/bash/zsh/ash/dash/pdksh
source "$HOME/.cargo/env.fish"  # For fish
source $"($nu.home-path)/.cargo/env.nu"  # For nushell
rustc 1.92.0 (ded5c06cf 2025-12-08)
cargo 1.92.0 (344c4567c 2025-10-21)
3.45.1 2024-01-30 16:01:20 e876e51a0ed5c5b3126f52e532044363a014bc594cfefa87ffb5b82257ccalt1 (64-bit)
ENGINE PID: 165697
DASH PID:   166500
To stop: kill $(cat /tmp/hybrid_engine_laptop.pid) ; kill $(cat /tmp/hybrid_dash_laptop.pid)
