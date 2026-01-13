import sys, json, requests

def main():
    try:
        url = "https://clob.polymarket.com/markets"
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch markets: {resp.status_code}")
            return
        
        data = resp.json()
        found = False
        for m in data.get("data", []):
            if m.get("enable_order_book") and m.get("active") and not m.get("closed"):
                question = m.get("question")
                tokens = m.get("tokens", [])
                for t in tokens:
                    token_id = t.get("token_id")
                    if token_id:
                        print(f"MATCH | ID: {token_id} | Question: {question}")
                        found = True
        if not found:
            print("No active CLOB markets found in /markets")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
