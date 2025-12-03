# validator.py
"""
Validate proposed updates before applying them.
Checks both schema and simple logical constraints.
"""

from typing import Dict, Any, List
from world_model import World, Region, City
from pydantic import ValidationError

class ValidationErrorDetail(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

def validate_update(world_dict: Dict[str, Any], update_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an update against the current world.

    update_payload format is flexible; we support:
    - {"op":"add_city", "region":"Northland", "city": {"name":"NewCity", "population":100}}
    - {"op":"add_resource", "region":"Northland", "resource":"gold"}
    - {"op":"transfer_city", "city":"X", "from":"A", "to":"B"}
    - {"op":"set_population", "city":"X", "population": 12345}
    - etc.

    Return: {"valid": True} or raise ValidationErrorDetail with message/details
    """
    # Basic shape validation using World model
    try:
        _ = World.parse_obj(world_dict)
    except ValidationError as e:
        raise ValidationErrorDetail("Current world data is invalid", details=str(e))

    op = update_payload.get("op")
    if not op:
        raise ValidationErrorDetail("Missing 'op' field in update")

    # helper lookups
    regions = {r["name"]: r for r in world_dict.get("regions", [])}
    cities = world_dict.get("cities", {})

    if op == "add_city":
        region_name = update_payload.get("region")
        city_obj = update_payload.get("city")
        if not region_name or not city_obj:
            raise ValidationErrorDetail("add_city requires 'region' and 'city' fields")
        if region_name not in regions:
            raise ValidationErrorDetail(f"Region '{region_name}' does not exist")
        if city_obj.get("name") in cities:
            raise ValidationErrorDetail(f"City '{city_obj.get('name')}' already exists")
        if city_obj.get("population", 0) < 0:
            raise ValidationErrorDetail("Population must be >= 0")
        return {"valid": True}

    if op == "add_resource":
        region_name = update_payload.get("region")
        resource = update_payload.get("resource")
        if not region_name or not resource:
            raise ValidationErrorDetail("add_resource requires 'region' and 'resource'")
        if region_name not in regions:
            raise ValidationErrorDetail(f"Region '{region_name}' does not exist")
        # reject duplicates
        if resource in regions[region_name].get("resources", []):
            raise ValidationErrorDetail(f"Resource '{resource}' already present in region")
        return {"valid": True}

    if op == "transfer_city":
        city = update_payload.get("city")
        from_region = update_payload.get("from")
        to_region = update_payload.get("to")
        if not city or not from_region or not to_region:
            raise ValidationErrorDetail("transfer_city requires 'city', 'from', 'to'")
        if from_region not in regions or to_region not in regions:
            raise ValidationErrorDetail("Invalid 'from' or 'to' region")
        if city not in cities:
            raise ValidationErrorDetail("City does not exist")
        if city not in regions[from_region].get("cities", []):
            raise ValidationErrorDetail(f"City not found in region '{from_region}'")
        return {"valid": True}

    if op == "set_population":
        city = update_payload.get("city")
        population = update_payload.get("population")
        if city not in cities:
            raise ValidationErrorDetail("City does not exist")
        if not isinstance(population, int) or population < 0:
            raise ValidationErrorDetail("Population must be a non-negative integer")
        return {"valid": True}

    # Unknown op => reject
    raise ValidationErrorDetail("Unknown operation: " + str(op))
