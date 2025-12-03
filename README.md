# Lightweight World Backend (Streamlit + FastAPI)

A small backend foundation that:
- generates structured world data (JSON)
- suggests simple logical events
- validates updates before applying them
- stores snapshots and allows rollback
- exposes minimal API endpoints

## Files
- `app.py` - Streamlit UI and starts FastAPI in background
- `api.py` - FastAPI routes
- `world_model.py` - Pydantic models
- `world_engine.py` - generation, events, apply updates
- `validator.py` - update validation
- `storage.py` - snapshot & rollback
- `data_loader.py` - downloads dataset via `kagglehub`
- `requirements.txt` - dependencies (Python 3.11.0)
- `.gitignore`

## Quick start (local)
1. Create virtual env using Python 3.11.0:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
