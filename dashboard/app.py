import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "/opt/hybrid-trading-bot/data/bot.db"

def ro_conn():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

st.title("Hybrid Bot — Proof Loop")

@st.fragment(run_every=1)
def latest_tick():
    try:
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
