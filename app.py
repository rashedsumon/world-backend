# app.py
"""
Streamlit UI that starts a FastAPI server in background.
Main file for Streamlit Cloud deployment.
"""

import streamlit as st
import threading
import uvicorn
import time
from api import app as fastapi_app
from data_loader import ensure_cities_dataset
from api import CURRENT_WORLD  # note: reading/updating in endpoints will update this module-level object
import requests
import json
from pathlib import Path

# ensure data ready
ensure_cities_dataset()

# Start FastAPI server in background thread (uvicorn)
def start_api():
    # note: uses port 8000 (Streamlit Cloud may route differently; this typically works locally)
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="info")

if "api_thread" not in st.session_state:
    t = threading.Thread(target=start_api, daemon=True)
    t.start()
    st.session_state["api_thread"] = t
    # Give API a moment to start
    time.sleep(0.5)

API_BASE = "http://127.0.0.1:8000"

st.title("Lightweight World Backend — Demo UI")
st.markdown("This Streamlit UI starts a small FastAPI server in the background and provides basic controls.")

# Generate world
st.header("World Generation")
name = st.text_input("World name", value="DemoWorld")
cols = st.columns(3)
regions_count = cols[0].number_input("Regions", min_value=1, max_value=12, value=4)
cities_per_region = cols[1].number_input("Cities per region", min_value=1, max_value=12, value=3)
if st.button("Generate world"):
    resp = requests.post(f"{API_BASE}/generate/world", json={"name": name, "regions_count": int(regions_count), "cities_per_region": int(cities_per_region)})
    st.write(resp.json())

# Show current world
st.header("Current World")
if st.button("Refresh world (from API)"):
    try:
        # No direct endpoint to fetch world; we rely on STREAM of endpoints - but we can attempt to generate world earlier.
        # For demo: display the CURRENT_WORLD imported from api module (best-effort)
        st.json(CURRENT_WORLD)
    except Exception as e:
        st.write("Unable to read current world:", e)

# Events
st.header("Event generation")
if st.button("Suggest an event"):
    resp = requests.post(f"{API_BASE}/generate/event")
    st.json(resp.json())

# Apply update (basic)
st.header("Apply update (validate then apply)")
st.markdown("Example update payloads (JSON). Supported ops: add_city, add_resource, transfer_city, set_population")
payload_text = st.text_area("Update JSON", value='{"op":"add_resource","region":"Northland","resource":"gold"}', height=120)
if st.button("Validate update"):
    try:
        payload = json.loads(payload_text)
    except Exception as e:
        st.error("Invalid JSON: " + str(e))
        payload = None
    if payload:
        resp = requests.post(f"{API_BASE}/validate", json=payload)
        st.json(resp.json())

if st.button("Apply update now"):
    try:
        payload = json.loads(payload_text)
    except Exception as e:
        st.error("Invalid JSON: " + str(e))
        payload = None
    if payload:
        resp = requests.post(f"{API_BASE}/apply-update", json=payload)
        st.json(resp.json())

# Snapshots / rollback
st.header("Snapshots")
if st.button("List snapshots"):
    resp = requests.get(f"{API_BASE}/snapshots")
    st.json(resp.json())

st.markdown("Rollback by snapshot id:")
snap_id = st.text_input("Snapshot ID to rollback", "")
if st.button("Rollback"):
    if not snap_id:
        st.error("Enter snapshot id")
    else:
        resp = requests.post(f"{API_BASE}/rollback", json={"snapshot_id": snap_id})
        st.json(resp.json())

st.markdown("---")
st.caption("This demo keeps state in memory and snapshots on disk (`data/snapshots`). Use the API endpoints directly for automation.")
