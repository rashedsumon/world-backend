

# data_loader.py
"""
Downloads or prepares a small city dataset using kagglehub.
If kagglehub or download fails, we fall back to a tiny builtin sample.
"""

import os
import csv
import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CITIES_CSV = DATA_DIR / "cities.csv"

def download_cities_dataset():
    """
    Attempt to download using kagglehub.dataset_download(...).
    If not available or fails, return False and use sample.
    """
    try:
        import kagglehub
    except Exception as e:
        print("kagglehub not available:", e)
        return False

    try:
        # This call matches your example usage
        path = kagglehub.dataset_download("juanmah/world-cities")
        print("kagglehub dataset path:", path)
        # kagglehub might produce an archive or csv(s). For simplicity, we assume a CSV called world-cities.csv
        # If path is a folder with CSV, try to move it to data/
        from pathlib import Path
        p = Path(path)
        # naive search for CSV
        for f in p.rglob("*.csv"):
            if "city" in f.name.lower() or "world" in f.name.lower() or "cities" in f.name.lower():
                dest = CITIES_CSV
                dest.write_bytes(f.read_bytes())
                print("Copied", f, "->", dest)
                return True
        # fallback: copy any csv found
        csvs = list(p.rglob("*.csv"))
        if csvs:
            dest = CITIES_CSV
            dest.write_bytes(csvs[0].read_bytes())
            print("Copied", csvs[0], "->", dest)
            return True
    except Exception as e:
        print("Failed to download via kagglehub:", e)
        return False

def create_sample_cities():
    """Create a tiny fallback CSV with sample cities"""
    sample = [
        ("Frostgate", "Northland", 12000),
        ("Whitehill", "Northland", 8000),
        ("Sunport", "Southreach", 42000),
        ("Marigold", "Southreach", 15000),
        ("Dustvale", "Highplain", 6000),
        ("Ironford", "Highplain", 22000),
    ]
    with open(CITIES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["city", "region", "population"])
        writer.writerows(sample)
    print("Created sample cities CSV at", CITIES_CSV)
    return True

def ensure_cities_dataset():
    """Public helper: ensure cities CSV exists (download or sample)"""
    if CITIES_CSV.exists():
        return True
    ok = download_cities_dataset()
    if not ok:
        create_sample_cities()
    return True

if __name__ == "__main__":
    ensure_cities_dataset()
