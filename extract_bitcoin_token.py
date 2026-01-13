import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get("data", []):
        q = m.get("question", "").lower()
        if "bitcoin" in q or "btc" in q:
            for t in m.get("tokens", []):
                print(f"{t.get('token_id')}")
                sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
sys.exit(1)
