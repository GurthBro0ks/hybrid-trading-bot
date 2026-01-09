import streamlit as st
import time
import pandas as pd
import json
import os
from datetime import datetime
from lib.db import fetch_ticks_delta, get_latest_stats, fetch_signals_delta

st.set_page_config(
    page_title="Hybrid Bot Flight Recorder",
    page_icon="✈️",
    layout="wide",
)

# Initialize Session State
if "last_tick_ts" not in st.session_state: st.session_state.last_tick_ts = 0
if "last_tick_id" not in st.session_state: st.session_state.last_tick_id = 0
if "ticks_buffer" not in st.session_state: st.session_state.ticks_buffer = []

if "last_signal_ts" not in st.session_state: st.session_state.last_signal_ts = 0
if "last_signal_id" not in st.session_state: st.session_state.last_signal_id = 0
if "signals_buffer" not in st.session_state: st.session_state.signals_buffer = []

st.title("Flight Recorder Phase 3")

tab1, tab2, tab3 = st.tabs(["Ops Health", "Live Ticks", "Signals"])

with tab1:
    st.header("Ops Health (PSI & Soak)")
    
    # 1. System PSI
    # Read /proc/pressure directly (quick & dirty for dashboard)
    cols = st.columns(3)
    try:
        psi = {}
        for res in ["cpu", "memory", "io"]:
            with open(f"/proc/pressure/{res}") as f:
                line = f.readline()
                # some avg10=X.XX ...
                val = float(line.split()[1].split("=")[1])
                psi[res] = val
        
        cols[0].metric("CPU Pressure (avg10)", f"{psi['cpu']}%")
        cols[1].metric("MEM Pressure (avg10)", f"{psi['memory']}%")
        cols[2].metric("IO Pressure (avg10)", f"{psi['io']}%")
    except Exception as e:
        st.error(f"Failed to read PSI: {e}")

    # 2. Soak Decisions Log
    st.subheader("Latest Soak Decisions")
    log_path = "/opt/hybrid-trading-bot/data/ops/soak_decisions.jsonl"
    if os.path.exists(log_path):
        data = []
        with open(log_path) as f:
            for line in f.readlines()[-10:]: # Last 10
                try:
                    data.append(json.loads(line))
                except: pass
        if data:
            df_log = pd.DataFrame(data)
            # Reorder columns
            cols_show = ["timestamp", "state", "action", "reason", "cpu_psi"]
            st.dataframe(df_log[cols_show].sort_values("timestamp", ascending=False), use_container_width=True)
        else:
            st.info("No decisions logged yet.")
    else:
        st.warning("Soak log not found.")

with tab2:
    st.header("Live Ticks (Delta Fetch)")
    
    # Poll for new ticks
    new_ticks = fetch_ticks_delta(st.session_state.last_tick_ts, st.session_state.last_tick_id)
    
    if new_ticks:
        # Update pointers
        last = new_ticks[-1]
        st.session_state.last_tick_ts = last["ts"]
        st.session_state.last_tick_id = last["id"]
        
        # Add to buffer (keep last 50)
        st.session_state.ticks_buffer.extend(new_ticks)
        if len(st.session_state.ticks_buffer) > 50:
            st.session_state.ticks_buffer = st.session_state.ticks_buffer[-50:]
            
    # Display Buffer
    if st.session_state.ticks_buffer:
        df = pd.DataFrame(st.session_state.ticks_buffer)
        df["ts_human"] = pd.to_datetime(df["ts"], unit="ms")
        st.dataframe(df.sort_values("id", ascending=False), use_container_width=True)
        
        # Chart
        st.line_chart(df.set_index("ts_human")["price"])
    else:
        st.info("Waiting for ticks...")

with tab3:
    st.header("Signals")
    # Poll for new signals
    new_signals = fetch_signals_delta(st.session_state.last_signal_ts, st.session_state.last_signal_id)
    if new_signals:
         last = new_signals[-1]
         st.session_state.last_signal_ts = last["ts"]
         st.session_state.last_signal_id = last["id"]
         st.session_state.signals_buffer.extend(new_signals)
         if len(st.session_state.signals_buffer) > 50:
             st.session_state.signals_buffer = st.session_state.signals_buffer[-50:]
             
    if st.session_state.signals_buffer:
        df_sig = pd.DataFrame(st.session_state.signals_buffer)
        df_sig["ts_human"] = pd.to_datetime(df_sig["ts"], unit="ms")
        st.dataframe(df_sig.sort_values("id", ascending=False), use_container_width=True)
    else:
        st.info("No signals yet.")

# Auto-refresh
time.sleep(1)
st.rerun()
