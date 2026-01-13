import sys, json, requests

def main():
    try:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100"
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch Gamma markets: {resp.status_code}")
            return
        
        data = resp.json()
        found = False
        for m in data:
            if m.get("active") and not m.get("closed"):
                clob_ids = m.get("clobTokenIds")
                if clob_ids:
                    # clob_ids is often a JSON string representation of a list
                    if isinstance(clob_ids, str):
                        try:
                            clob_ids = json.loads(clob_ids)
                        except:
                            pass
                    
                    if clob_ids:
                        print(f"MATCH | IDs: {clob_ids} | Question: {m.get('question')}")
                        found = True
        if not found:
            print("No active CLOB markets found in Gamma")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
