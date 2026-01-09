import sqlite3
import contextlib
import os

DB_PATH = os.environ.get("AG_DB_PATH", "/opt/hybrid-trading-bot/data/bot.db")

def get_connection():
    """Returns a read-only connection to the SQLite DB."""
    # URI mode=ro ensures we open in read-only mode at the driver level
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    
    # Enforce performance and safety PRAGMAs
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA query_only=ON;") # Double safety
    conn.execute("PRAGMA busy_timeout=2000;")
    
    conn.row_factory = sqlite3.Row
    return conn

@contextlib.contextmanager
def get_db():
    """Context manager for DB access."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def fetch_ticks_delta(last_ts: int, last_id: int, limit: int = 100):
    """Fetch ticks newer than (last_ts, last_id)."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, symbol, price, volume, ts
            FROM ticks
            WHERE (ts > ?) OR (ts = ? AND id > ?)
            ORDER BY ts ASC, id ASC
            LIMIT ?
        """, (last_ts, last_ts, last_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def fetch_signals_delta(last_ts: int, last_id: int, limit: int = 50):
    """Fetch signals newer than (last_ts, last_id)."""
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT id, event_id, signal_type, symbol, reason, confidence, ts
            FROM signals
            WHERE (ts > ?) OR (ts = ? AND id > ?)
            ORDER BY ts ASC, id ASC
            LIMIT ?
        """, (last_ts, last_ts, last_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def get_latest_stats():
    with get_db() as conn:
        ticks = conn.execute("SELECT MAX(id) as max_id, MAX(ts) as max_ts, COUNT(*) as count FROM ticks").fetchone()
        signals = conn.execute("SELECT COUNT(*) as count FROM signals").fetchone()
        return {
            "ticks": dict(ticks) if ticks else {},
            "signals": dict(signals) if signals else {},
        }
