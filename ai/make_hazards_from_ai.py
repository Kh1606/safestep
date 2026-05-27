import json
from pathlib import Path

RESULTS_DIR = Path(r"T:\docker\masil\ai\results")
OUT_GEOJSON = Path(r"T:\docker\masil\demo\hazards_from_ai.geojson")

CONF_THRESHOLD = 0.25  # ignore very low-confidence boxes
HAZARD_CLASSES = {"stair", "ramp", "curb", "grab_bar"}  # adjust to your model names

features = []

for json_path in RESULTS_DIR.glob("*.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        print("Skipping (no GPS):", json_path.name)
        continue

    detections = data.get("detections", [])
    if not detections:
        print("Skipping (no detections):", json_path.name)
        continue

    # pick best detection we care about
    best = None
    for det in detections:
        cls_name = det.get("class_name")
        conf = det.get("confidence", 0.0)
        if cls_name in HAZARD_CLASSES and conf >= CONF_THRESHOLD:
            if best is None or conf > best["confidence"]:
                best = det

    if best is None:
        print("Skipping (no hazard-like classes above threshold):", json_path.name)
        continue

    # create hazard feature
    feature = {
        "type": "Feature",
        "properties": {
            "filename": data["filename"],
            "hazard_type": best["class_name"],   # e.g. "stair"
            "confidence": best["confidence"],
            "image_width": data.get("image_width"),
            "image_height": data.get("image_height"),
            "timestamp_utc": data.get("timestamp_utc"),
            "accuracy_m": data.get("accuracy_m"),
            # route_id will be added later when we snap to a MASIL route
            "route_id": None
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat],
        },
    }
    features.append(feature)
    print("Added hazard from:", json_path.name, "->", best["class_name"], best["confidence"])

geojson = {
    "type": "FeatureCollection",
    "features": features,
}

OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
with OUT_GEOJSON.open("w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print("Wrote", OUT_GEOJSON, "with", len(features), "hazards.")
