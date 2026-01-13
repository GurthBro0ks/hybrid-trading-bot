
import time
import requests
import logging

logger = logging.getLogger("polymarket_fetch")

class PolymarketFetchError(Exception):
    def __init__(self, reason: str, status_code: int = None):
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"Polymarket fetch failed: {reason} (status={status_code})")

def fetch_book(token_id: str, timeout_s: float = 5.0) -> dict:
    """
    Fetch orderbook from Polymarket CLOB.
    Endpoint: GET https://clob.polymarket.com/book?token_id=<token_id>
    """
    url = "https://clob.polymarket.com/book"
    params = {"token_id": token_id}
    
    max_retries = 3
    backoff_s = 1.0
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout_s)
            
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    raise PolymarketFetchError("JSON_PARSE_ERROR", status_code=200)
            
            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    sleep_time = min(backoff_s * (2 ** attempt), 5.0)
                    logger.warning(f"HTTP_429: Retrying in {sleep_time}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise PolymarketFetchError("HTTP_429", status_code=429)
            
            if resp.status_code in [401, 403]:
                raise PolymarketFetchError("HTTP_AUTH_ERROR", status_code=resp.status_code)
            if resp.status_code == 404:
                raise PolymarketFetchError("HTTP_404", status_code=404)
            
            raise PolymarketFetchError(f"HTTP_{resp.status_code}", status_code=resp.status_code)
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            raise PolymarketFetchError("TIMEOUT")
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                continue
            raise PolymarketFetchError("CONNECTION_ERROR")
        except Exception as e:
            if isinstance(e, PolymarketFetchError):
                raise
            raise PolymarketFetchError(f"UNEXPECTED_ERROR: {str(e)}")

    raise PolymarketFetchError("MAX_RETRIES_EXCEEDED")
