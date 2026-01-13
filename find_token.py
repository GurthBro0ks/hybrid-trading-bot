import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get("data", []):
        if m.get("enable_order_book") and m.get("active") and not m.get("closed"):
            for t in m.get("tokens", []):
                print(f"{t.get('token_id')}")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
