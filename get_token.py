import sys, json; data = json.load(sys.stdin); print(data[0]["tokens"][0]["token_id"] if data else "NONE")
