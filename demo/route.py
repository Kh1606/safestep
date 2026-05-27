import json
from pathlib import Path

walk_path = Path("seongdong_walkways.geojson")
routes_path = Path("masil_routes.geojson")

with walk_path.open("r", encoding="utf-8") as f:
    walk_data = json.load(f)

# Pick a "nice" walkway as demo route:
# here: first feature that has at least 20 points
demo_feature = None
for feat in walk_data["features"]:
    coords = feat["geometry"]["coordinates"]
    if len(coords) >= 20:   # long enough to look like a route
        demo_feature = feat
        break

if demo_feature is None:
    raise RuntimeError("No suitable walkway with >=20 coords found.")

# Build MASIL route feature
route_feature = {
    "type": "Feature",
    "properties": {
        "route_id": "seongdong_route_1",
        "name": "Demo Route 1",
        "source_osmid": demo_feature["properties"].get("osmid"),
        "highway": demo_feature["properties"].get("highway", ""),
    },
    "geometry": demo_feature["geometry"],  # reuse same LineString
}

routes_geojson = {
    "type": "FeatureCollection",
    "features": [route_feature],
}

with routes_path.open("w", encoding="utf-8") as f:
    json.dump(routes_geojson, f, ensure_ascii=False, indent=2)

print("Wrote", routes_path, "with 1 demo route.")
