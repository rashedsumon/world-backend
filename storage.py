# storage.py
"""
Snapshot storage and rollback management.
Stores world snapshots as JSON files under data/snapshots/
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import uuid

SNAPSHOT_DIR = Path("data") / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def _snapshot_path(snapshot_id: str) -> Path:
    return SNAPSHOT_DIR / f"{snapshot_id}.json"

def create_snapshot(world: Dict[str, Any], tag: str | None = None) -> str:
    """
    Save a timestamped snapshot and return snapshot_id.
    snapshot contains: id, tag, created_at, world
    """
    snapshot_id = uuid.uuid4().hex[:12]
    payload = {
        "id": snapshot_id,
        "tag": tag or "",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "world": world
    }
    path = _snapshot_path(snapshot_id)
    path.write_text(json.dumps(payload, indent=2))
    return snapshot_id

def list_snapshots() -> List[Dict[str, Any]]:
    snapshots = []
    for f in SNAPSHOT_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            snapshots.append({
                "id": data.get("id"),
                "tag": data.get("tag"),
                "created_at": data.get("created_at")
            })
        except Exception:
            continue
    # sort newest first
    snapshots.sort(key=lambda s: s["created_at"], reverse=True)
    return snapshots

def load_snapshot(snapshot_id: str) -> Dict[str, Any]:
    path = _snapshot_path(snapshot_id)
    if not path.exists():
        raise FileNotFoundError("No snapshot with id: " + snapshot_id)
    data = json.loads(path.read_text())
    return data["world"]

def rollback_to(snapshot_id: str) -> Dict[str, Any]:
    """
    Return the world dict from snapshot (caller should apply it).
    """
    return load_snapshot(snapshot_id)
