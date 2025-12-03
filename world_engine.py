# world_engine.py
"""
Core world engine: generate world, propose events, apply updates (after validation)
"""

from world_model import World, Region, City
from typing import Dict, Any, List, Tuple
from storage import create_snapshot
from validator import validate_update, ValidationErrorDetail
from datetime import datetime
import random
import json
from pathlib import Path
import csv

DATA_DIR = Path("data")
CITIES_CSV = DATA_DIR / "cities.csv"

def _load_cities_csv() -> List[Tuple[str, str, int]]:
    if not CITIES_CSV.exists():
        return []
    rows = []
    with open(CITIES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                name = r.get("city") or r.get("name") or r.get("City")
                region = r.get("region") or r.get("country") or r.get("Region") or "Unknown"
                pop = int(r.get("population") or 0)
                rows.append((name, region, pop))
            except Exception:
                continue
    return rows

def generate_world(name: str = "MyWorld", regions_count: int = 4, cities_per_region: int = 3) -> Dict[str, Any]:
    """
    Create a small synthesized world JSON.
    If a city CSV exists, use it as source for city names/regions.
    """
    cities_rows = _load_cities_csv()
    # Basic resource pool
    resource_pool = ["iron", "timber", "gold", "grain", "fish", "coal", "spice"]

    regions: Dict[str, Dict] = {}
    cities: Dict[str, Dict] = {}

    # If CSV exists, use its region names; else create synthetic regions
    if cities_rows:
        # group rows by region
        by_region = {}
        for name, region, pop in cities_rows:
            by_region.setdefault(region, []).append((name, pop))
        region_names = list(by_region.keys())
        random.shuffle(region_names)
        selected_regions = region_names[:regions_count] if region_names else [f"Region{i}" for i in range(regions_count)]
        for region in selected_regions:
            regs_cities = by_region.get(region, [])[:cities_per_region]
            # create region entry
            res = random.sample(resource_pool, k=min(2, len(resource_pool)))
            regions[region] = {
                "name": region,
                "cities": [],
                "resources": res
            }
            for name, pop in regs_cities:
                # ensure unique city name
                key = name
                idx = 1
                while key in cities:
                    key = f"{name}_{idx}"; idx += 1
                city_obj = {"name": key, "population": pop or random.randint(1000, 20000), "attributes": {}}
                cities[key] = city_obj
                regions[region]["cities"].append(key)
    else:
        # Synthetic creation
        for i in range(regions_count):
            rname = f"Region_{i+1}"
            regions[rname] = {
                "name": rname,
                "cities": [],
                "resources": random.sample(resource_pool, k=2)
            }
            for j in range(cities_per_region):
                cname = f"City_{i+1}_{j+1}"
                city_obj = {"name": cname, "population": random.randint(500, 50000), "attributes": {}}
                cities[cname] = city_obj
                regions[rname]["cities"].append(cname)

    world = {
        "name": name,
        "regions": list(regions.values()),
        "cities": cities,
        "metadata": {"generated_at": datetime.utcnow().isoformat() + "Z"},
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    # Save initial snapshot
    snap_id = create_snapshot(world, tag=f"initial-{name}")
    world["metadata"]["initial_snapshot"] = snap_id
    return world

def suggest_event(world: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propose a lightweight event based on current world state.
    Picks from a few templates using simple heuristics.
    """
    regions = world.get("regions", [])
    cities = world.get("cities", {})
    if not regions:
        return {"event": "No regions to generate events for."}

    templates = [
        lambda: {
            "type": "discover_resource",
            "text": f"City {random.choice(list(cities.keys()))} discovers a deposit of {random.choice(['coal','gold','salt','spice'])}."
        },
        lambda: {
            "type": "drought",
            "text": f"Region {random.choice([r['name'] for r in regions])} suffers a drought."
        },
        lambda: {
            "type": "trade_route",
            "text": f"Trade route opens between {random.choice([r['name'] for r in regions])} and {random.choice([r['name'] for r in regions])}."
        },
        lambda: {
            "type": "population_boost",
            "text": f"City {random.choice(list(cities.keys()))} experiences an unexpected population growth."
        }
    ]
    # weighted pick
    event = random.choice(templates)()
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event

def apply_update(world: Dict[str, Any], update_payload: Dict[str, Any], snapshot: bool = True) -> Dict[str, Any]:
    """
    Validate and apply update_payload to world. Returns updated world.
    Supported operations are validated in validator.validate_update
    """
    # validate first
    try:
        validate_update(world, update_payload)
    except ValidationErrorDetail as e:
        return {"ok": False, "error": str(e), "details": getattr(e, "details", None)}

    op = update_payload.get("op")
    if op == "add_city":
        region_name = update_payload["region"]
        city = update_payload["city"]
        # add city
        world["cities"][city["name"]] = city
        # append to region
        for r in world["regions"]:
            if r["name"] == region_name:
                r.setdefault("cities", []).append(city["name"])
                break
        # snapshot
        if snapshot:
            create_snapshot(world, tag=f"add_city:{city['name']}")
        return {"ok": True, "world": world}

    if op == "add_resource":
        region_name = update_payload["region"]
        resource = update_payload["resource"]
        for r in world["regions"]:
            if r["name"] == region_name:
                r.setdefault("resources", []).append(resource)
                break
        if snapshot:
            create_snapshot(world, tag=f"add_resource:{resource}@{region_name}")
        return {"ok": True, "world": world}

    if op == "transfer_city":
        city = update_payload["city"]
        from_region = update_payload["from"]
        to_region = update_payload["to"]
        # remove from from_region, add to to_region
        for r in world["regions"]:
            if r["name"] == from_region and city in r.get("cities", []):
                r["cities"].remove(city)
        for r in world["regions"]:
            if r["name"] == to_region:
                r.setdefault("cities", []).append(city)
        if snapshot:
            create_snapshot(world, tag=f"transfer_city:{city}:{from_region}->{to_region}")
        return {"ok": True, "world": world}

    if op == "set_population":
        city = update_payload["city"]
        population = update_payload["population"]
        if city in world["cities"]:
            world["cities"][city]["population"] = population
            if snapshot:
                create_snapshot(world, tag=f"set_pop:{city}:{population}")
            return {"ok": True, "world": world}

    # fallback
    return {"ok": False, "error": "Unsupported op after validation (unexpected)"}
