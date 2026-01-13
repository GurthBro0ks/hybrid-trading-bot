import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger("kalshi_fetch")


class KalshiFetchError(Exception):
    def __init__(self, reason: str, status_code: int | None = None):
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"Kalshi fetch failed: {reason} (status={status_code})")


def _base_url() -> str:
    return os.getenv("KALSHI_API_BASE", "https://trading-api.kalshi.com")


def fetch_book(
    market: str,
    *,
    token: Optional[str] = None,
    timeout_s: float = 5.0,
    base_url: Optional[str] = None,
) -> dict:
    url_base = base_url or _base_url()
    url = f"{url_base}/trade-api/v2/markets/{market}/orderbook"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    max_retries = 3
    backoff_s = 1.0

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout_s)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    raise KalshiFetchError("JSON_PARSE_ERROR", status_code=200)

            if resp.status_code == 429:
                if attempt < max_retries - 1:
                    sleep_time = min(backoff_s * (2 ** attempt), 5.0)
                    logger.warning(
                        f"HTTP_429: Retrying in {sleep_time}s (attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(sleep_time)
                    continue
                raise KalshiFetchError("HTTP_429", status_code=429)

            if resp.status_code in [401, 403]:
                raise KalshiFetchError("HTTP_AUTH_ERROR", status_code=resp.status_code)
            if resp.status_code == 404:
                raise KalshiFetchError("HTTP_404", status_code=404)

            raise KalshiFetchError(f"HTTP_{resp.status_code}", status_code=resp.status_code)
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                continue
            raise KalshiFetchError("TIMEOUT")
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                continue
            raise KalshiFetchError("CONNECTION_ERROR")
        except Exception as exc:
            if isinstance(exc, KalshiFetchError):
                raise
            raise KalshiFetchError(f"UNEXPECTED_ERROR: {exc}")

    raise KalshiFetchError("MAX_RETRIES_EXCEEDED")


def fetch_market(
    market_ticker: str,
    *,
    token: Optional[str] = None,
    timeout_s: float = 5.0,
    base_url: Optional[str] = None,
) -> dict:
    url_base = base_url or _base_url()
    # Kalshi V2 Market endpoint using ticker
    url = f"{url_base}/trade-api/v2/markets/{market_ticker}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
        if resp.status_code == 200:
            try:
                data = resp.json()
                # The endpoint returns {"market": {...}}
                return data.get("market", data)
            except ValueError:
                raise KalshiFetchError("JSON_PARSE_ERROR", status_code=200)
    except requests.exceptions.RequestException as e:
        raise KalshiFetchError(f"NETWORK_ERROR: {e}")

    if resp.status_code == 404:
        raise KalshiFetchError("MARKET_NOT_FOUND", status_code=404)
    raise KalshiFetchError(f"HTTP_{resp.status_code}", status_code=resp.status_code)
