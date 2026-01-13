import sys, json
try:
    data = json.load(sys.stdin)
    # Gamma API returns a list of objects
    for m in data:
        token_ids = m.get("clobTokenIds")
        if token_ids and len(token_ids) > 0:
            # We want one token ID
            print(token_ids[0].strip('[]" '))
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
