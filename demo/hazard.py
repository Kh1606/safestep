import json
from pathlib import Path

routes_path = Path("masil_routes.geojson")
hazards_path = Path("hazards_demo.geojson")

with routes_path.open("r", encoding="utf-8") as f:
    routes = json.load(f)

if not routes["features"]:
    raise RuntimeError("No routes found in masil_routes.geojson")

route = routes["features"][0]
route_id = route["properties"].get("route_id", "seongdong_route_1")
coords = route["geometry"]["coordinates"]

if len(coords) < 2:
    raise RuntimeError("Route geometry too short")

def point_at_fraction(coords, frac: float):
    """
    Very simple: pick a point at position frac along the list of coordinates.
    Not real distance-based, but fine for demo.
    """
    frac = min(max(frac, 0.0), 1.0)
    idx = int(frac * (len(coords) - 1))
    return coords[idx]

hazards = []

# example 1: high stairs around 30% of route
lon1, lat1 = point_at_fraction(coords, 0.3)
hazards.append({
    "type": "Feature",
    "properties": {
        "hazard_type": "stairs",
        "severity": "high",
        "route_id": route_id,
        "video_id": "demo_video_1",
        "position_along_route": 0.3
    },
    "geometry": {
        "type": "Point",
        "coordinates": [lon1, lat1]
    }
})

# example 2: gentle ramp around 70% of route
lon2, lat2 = point_at_fraction(coords, 0.7)
hazards.append({
    "type": "Feature",
    "properties": {
        "hazard_type": "ramp",
        "severity": "low",
        "route_id": route_id,
        "video_id": "demo_video_1",
        "position_along_route": 0.7
    },
    "geometry": {
        "type": "Point",
        "coordinates": [lon2, lat2]
    }
})

hazards_geojson = {
    "type": "FeatureCollection",
    "features": hazards
}

with hazards_path.open("w", encoding="utf-8") as f:
    json.dump(hazards_geojson, f, ensure_ascii=False, indent=2)

print("Wrote", hazards_path, "with", len(hazards), "demo hazards.")
