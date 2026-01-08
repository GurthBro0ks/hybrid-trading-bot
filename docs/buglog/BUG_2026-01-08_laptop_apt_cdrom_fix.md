# Flight Recorder — laptop apt cdrom fix
2026-01-08T13:39:33-05:00
mint
/etc/apt/sources.list:2:# deb cdrom:[Linux Mint 22.2 _Zara_ - Release amd64 20250828]/ noble contrib main
/etc/apt/sources.list:3:deb cdrom:[Linux Mint 22.2 _Zara_ - Release amd64 20250828]/ noble contrib main

WARNING: apt does not have a stable CLI interface. Use with caution in scripts.

Ign:1 http://packages.linuxmint.com zara InRelease
Hit:2 http://packages.linuxmint.com zara Release
Hit:3 http://security.ubuntu.com/ubuntu noble-security InRelease
Hit:5 https://download.docker.com/linux/ubuntu noble InRelease
Get:6 https://cli.github.com/packages stable InRelease [3917 B]
Hit:7 https://dl.google.com/linux/chrome/deb stable InRelease
Hit:8 https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev antigravity-debian InRelease
Hit:9 http://archive.ubuntu.com/ubuntu noble InRelease
Hit:10 http://archive.ubuntu.com/ubuntu noble-updates InRelease
Hit:11 http://archive.ubuntu.com/ubuntu noble-backports InRelease
Fetched 3917 B in 2s (2462 B/s)
Reading package lists...
Building dependency tree...
Reading state information...
229 packages can be upgraded. Run 'apt list --upgradable' to see them.
/etc/apt/sources.list:2:# deb cdrom:[Linux Mint 22.2 _Zara_ - Release amd64 20250828]/ noble contrib main
/etc/apt/sources.list:3:# deb cdrom:[Linux Mint 22.2 _Zara_ - Release amd64 20250828]/ noble contrib main
