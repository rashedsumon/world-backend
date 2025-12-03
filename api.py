# api.py
"""
FastAPI app with minimal endpoints.
This module is imported and launched by app.py in a background thread.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from world_engine import generate_world, suggest_event, apply_update
from storage import list_snapshots, rollback_to
from validator import validate_update, ValidationErrorDetail

app = FastAPI(title="Lightweight World Backend")

# Basic in-memory current world (for demo)
CURRENT_WORLD: Dict[str, Any] = {}

class GenerateWorldRequest(BaseModel):
    name: str = "MyWorld"
    regions_count: int = 4
    cities_per_region: int = 3

class UpdateRequest(BaseModel):
    op: str
    # payload is flexible; accept arbitrary JSON
    payload: Dict[str, Any] = {}

class RollbackRequest(BaseModel):
    snapshot_id: str

@app.post("/generate/world")
def api_generate_world(req: GenerateWorldRequest):
    global CURRENT_WORLD
    world = generate_world(name=req.name, regions_count=req.regions_count, cities_per_region=req.cities_per_region)
    CURRENT_WORLD = world
    return {"ok": True, "world": world}

@app.post("/generate/event")
def api_generate_event():
    global CURRENT_WORLD
    if not CURRENT_WORLD:
        raise HTTPException(status_code=400, detail="No current world. Generate one first.")
    ev = suggest_event(CURRENT_WORLD)
    return {"ok": True, "event": ev}

@app.post("/validate")
def api_validate(update: Dict[str, Any]):
    global CURRENT_WORLD
    if not CURRENT_WORLD:
        raise HTTPException(status_code=400, detail="No current world to validate against")
    try:
        out = validate_update(CURRENT_WORLD, update)
        return {"ok": True, "result": out}
    except ValidationErrorDetail as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "details": getattr(e, "details", None)})

@app.post("/apply-update")
def api_apply_update(update: Dict[str, Any]):
    global CURRENT_WORLD
    if not CURRENT_WORLD:
        raise HTTPException(status_code=400, detail="No current world to apply updates")
    res = apply_update(CURRENT_WORLD, update, snapshot=True)
    if not res.get("ok"):
        raise HTTPException(status_code=400, detail=res.get("error", "apply failed"))
    # ensure CURRENT_WORLD updated by reference
    CURRENT_WORLD = res["world"]
    return {"ok": True, "world": CURRENT_WORLD}

@app.get("/snapshots")
def api_snapshots():
    snaps = list_snapshots()
    return {"ok": True, "snapshots": snaps}

@app.post("/rollback")
def api_rollback(req: RollbackRequest):
    global CURRENT_WORLD
    try:
        world = rollback_to(req.snapshot_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    CURRENT_WORLD = world
    return {"ok": True, "world": CURRENT_WORLD}
