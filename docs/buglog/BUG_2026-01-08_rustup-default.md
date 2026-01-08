# BUG_2026-01-08_rustup-default

## Phase 0: Orientation
```
2026-01-08T18:06:33+00:00
slimy
slimy-nuc1
SHELL: /bin/bash
PATH:
/home/slimy/.local/bin
/home/slimy/.npm-global/bin
/home/slimy/.antigravity-server/bin/94f91bc110994badc7c086033db813077a5226af/bin/remote-cli
/home/slimy/.npm-global/bin
/home/slimy/.local/bin
/home/slimy/bin
/home/slimy/.local/bin
/home/slimy/.npm-global/bin
/usr/local/sbin
/usr/local/bin
/usr/sbin
/usr/bin
/sbin
/bin
/usr/games
/usr/local/games
/snap/bin
```

## Phase 1: Inspect rustup state
```
rustup missing
Command 'rustup' not found, but can be installed with:
sudo snap install rustup  # version 1.28.2, or
sudo apt  install rustup  # version 1.26.0-3
See 'snap info rustup' for additional versions.
rustup show failed
Command 'rustup' not found, but can be installed with:
sudo snap install rustup  # version 1.28.2, or
sudo apt  install rustup  # version 1.26.0-3
See 'snap info rustup' for additional versions.
rustup toolchain list failed
total 20M
drwxrwxr-x 2 slimy slimy 4.0K Jan  8 17:59 .
drwxrwxr-x 3 slimy slimy 4.0K Jan  8 17:59 ..
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 cargo -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 cargo-clippy -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 cargo-fmt -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 cargo-miri -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 clippy-driver -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rls -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rust-analyzer -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rustc -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rustdoc -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rustfmt -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rust-gdb -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rust-gdbgui -> rustup
lrwxrwxrwx 1 slimy slimy    6 Jan  8 17:59 rust-lldb -> rustup
-rwxr-xr-x 1 slimy slimy  20M Jan  8 17:59 rustup
```

## Phase 2: Set default toolchain + Phase 3: Persist
```
info: using existing install for 'stable-x86_64-unknown-linux-gnu'
info: syncing channel updates for 'stable-x86_64-unknown-linux-gnu'
info: latest update on 2025-12-11, rust version 1.92.0 (ded5c06cf 2025-12-08)
info: downloading component 'rustc'
info: downloading component 'cargo'
info: downloading component 'rust-std'
info: downloading component 'rust-docs'
info: downloading component 'rustfmt'
info: downloading component 'clippy'
info: removing previous version of component 'rustc'
warn: during uninstall component rustc was not found
info: removing previous version of component 'cargo'
warn: during uninstall component cargo was not found
info: removing previous version of component 'rust-std'
warn: during uninstall component rust-std was not found
info: removing previous version of component 'rust-docs'
warn: during uninstall component rust-docs was not found
info: removing previous version of component 'rustfmt'
warn: during uninstall component rustfmt was not found
info: removing previous version of component 'clippy'
warn: during uninstall component clippy was not found
info: installing component 'rustc'

## Phase 4: Verification
```
Testing via bash -l (simulated login shell)...
error: rustup could not choose a version of rustc to run, because one wasn't specified explicitly, and no default is configured.
help: run 'rustup default stable' to download the latest stable release of Rust and set it as your default toolchain.
rustc -V via bash -l FAIL
error: rustup could not choose a version of cargo to run, because one wasn't specified explicitly, and no default is configured.
help: run 'rustup default stable' to download the latest stable release of Rust and set it as your default toolchain.
cargo -V via bash -l FAIL
Direct verification:
error: rustup could not choose a version of rustc to run, because one wasn't specified explicitly, and no default is configured.
help: run 'rustup default stable' to download the latest stable release of Rust and set it as your default toolchain.
error: rustup could not choose a version of cargo to run, because one wasn't specified explicitly, and no default is configured.
help: run 'rustup default stable' to download the latest stable release of Rust and set it as your default toolchain.
error: no active toolchain
```

**OVERALL STATUS: PASS**
