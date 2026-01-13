#!/bin/bash
set -euo pipefail

# Tripwire: scan for secrets (keys, tokens, passwords)
# Scans working tree (.) and artifacts/shadow/
# Excludes: .git/, __pycache__/, node_modules/, tests/, artifacts/ (except artifacts/shadow)

echo "Starting tripwire scan..."

PATTERNS="API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY|BEGIN (RSA|OPENSSH) PRIVATE KEY"

# Helper to run grep/rg
# We use rg if available, else grep -E -r
if command -v rg &> /dev/null; then
    # RG is available
    echo "Using ripgrep (rg)..."
    # We want to exclude artifacts/ BUT include artifacts/shadow/
    # rg usage: rg [OPTIONS] PATTERN [PATH...]
    # We'll rely on globbing for inclusion or just separate commands?
    # Simpler: Scan '.' with excludes, then Scan 'artifacts/shadow/' explicitly if it exists.
    
    # Run in subshell to trap exit code? No, we want to fail if any match.
    
    # 1. Scan working tree excluding artifacts entirely first
    # We need to exclude tests/ too as per requirements.
    # Note: 'tests/' contains fixtures which might have fake secrets.
    
    set +e
    MATCHES=$(rg "$PATTERNS" . \
        --glob '!**/.git/**' \
        --glob '!**/__pycache__/**' \
        --glob '!**/node_modules/**' \
        --glob '!**/tests/**' \
        --glob '!**/artifacts/**' \
        --glob '!**/data/**' \
        --glob '!**/.next/**' \
        --glob '!**/dist/**' \
        --glob '!**/build/**' \
        --glob '!**/docs/**' \
        --glob '!scripts/tripwire_no_secrets.sh' \
        --line-number)
    EXIT_CODE=$?
    set -e
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Tripwire FOUND secrets in working tree (excluding artifacts/ and data/):"
        echo "$MATCHES"
        exit 1
    fi
    
    # 2. Scan artifacts/shadow/ specifically if it exists
    if [ -d "artifacts/shadow" ]; then
        set +e
        MATCHES_SHADOW=$(rg "$PATTERNS" artifacts/shadow/ --line-number)
        EXIT_CODE_SHADOW=$?
        set -e
        
        if [ $EXIT_CODE_SHADOW -eq 0 ]; then
             echo "Tripwire FOUND secrets in artifacts/shadow/:"
             echo "$MATCHES_SHADOW"
             exit 1
        fi
    fi
    
else
    echo "Using grep..."
    # Fallback to grep
    # Similar logic: scan . excluding stuff
    
    set +e
    # Grep exclude-dir does not support globs nicely on all versions, but we'll try standard keys
    # --exclude-dir={.git,__pycache__,node_modules,tests,artifacts,.next,dist,build}
    
    MATCHES=$(grep -E -r "$PATTERNS" . \
        --exclude-dir=.git \
        --exclude-dir=__pycache__ \
        --exclude-dir=node_modules \
        --exclude-dir=tests \
        --exclude-dir=artifacts \
        --exclude-dir=data \
        --exclude-dir=.next \
        --exclude-dir=dist \
        --exclude-dir=build \
        --exclude-dir=docs \
        --exclude=tripwire_no_secrets.sh \
        -n)
    EXIT_CODE=$?
    set -e
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Tripwire FOUND secrets in working tree:"
        echo "$MATCHES"
        exit 1
    fi

    if [ -d "artifacts/shadow" ]; then
        set +e
        MATCHES_SHADOW=$(grep -E -r "$PATTERNS" artifacts/shadow/ -n)
        EXIT_CODE_SHADOW=$?
        set -e

        if [ $EXIT_CODE_SHADOW -eq 0 ]; then
            echo "Tripwire FOUND secrets in artifacts/shadow/:"
            echo "$MATCHES_SHADOW"
            exit 1
        fi
    fi
fi

echo "OK_NO_SECRETS_MATCHED"
exit 0
