# world_model.py
"""
Pydantic models for the world. Small, explicit, easy to validate.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class City(BaseModel):
    name: str
    population: int = Field(ge=0)
    attributes: Dict[str, Any] = Field(default_factory=dict)  # e.g. {"harbor": True}

class Region(BaseModel):
    name: str
    cities: List[str] = Field(default_factory=list)   # store city names (normalized)
    resources: List[str] = Field(default_factory=list)

class World(BaseModel):
    name: str
    regions: List[Region] = Field(default_factory=list)
    cities: Dict[str, City] = Field(default_factory=dict)  # keyed by city name
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    @validator("cities", pre=True)
    def ensure_city_keys(cls, v):
        # pydantic will ensure dict shape; no-op here
        return v
