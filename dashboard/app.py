import sqlite3
import pandas as pd
import streamlit as st
import os

# Try tomllib (3.11+) or fallback to toml
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        st.error("Missing toml library. logic error.")
        st.stop()

# Helper to load config
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "../config/config.toml")
    with open(config_path, "rb") as f:
        return tomllib.load(f)

CONFIG = load_config()
DB_PATH = os.path.join(os.path.dirname(__file__), "../" + CONFIG["app"]["db_path"])
REFRESH_SECONDS = CONFIG["dashboard"].get("refresh_seconds", 1)

def ro_conn():
    # Use URI mode for read-only access
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

st.title("Hybrid Bot — Proof Loop")

@st.fragment(run_every=REFRESH_SECONDS)
def latest_tick():
    try:
        if not os.path.exists(DB_PATH):
             st.info("Waiting for database...")
             return
             
        with ro_conn() as conn:
            df = pd.read_sql(
                "SELECT symbol, price, ts FROM ticks ORDER BY ts DESC LIMIT 1",
                conn
            )
        if df.empty:
            st.metric("Latest Tick", "No data yet")
            return
        row = df.iloc[0]
        st.metric(row["symbol"], f"${row['price']:.4f}")
        st.caption(f"ts={int(row['ts'])}")
    except Exception as e:
        st.error(f"DB read error: {e}")

latest_tick()
