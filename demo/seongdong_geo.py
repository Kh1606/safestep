import osmium
import json
from collections import defaultdict

PBF = "Seoul.osm.pbf"   # update path
BBOX = (127.00, 37.52, 127.06, 37.575)  # Seongdong-gu approx


def in_bbox(lat, lon, bbox=BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)


class ExtractSeongdong(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}               # node_id -> (lat, lon)
        self.walk_ways = []           # list of (osmid, tags, [node_ids])
        self.poi = defaultdict(list)  # layer -> list of (lat, lon, tags)

    def node(self, n):
        if not n.location.valid():
            return

        lat, lon = n.location.lat, n.location.lon
        if not in_bbox(lat, lon):
            return

        self.nodes[n.id] = (lat, lon)

        tags = dict(n.tags)

        if tags.get("highway") == "elevator":
            self.poi["elevators"].append((lat, lon, tags))

        if tags.get("highway") == "crossing" or tags.get("footway") == "crossing":
            self.poi["crossings"].append((lat, lon, tags))

        if tags.get("amenity") == "bench":
            self.poi["benches"].append((lat, lon, tags))

        if tags.get("amenity") == "toilets":
            self.poi["toilets"].append((lat, lon, tags))

    def way(self, w):
        tags = dict(w.tags)
        hw = tags.get("highway", "")

        # keep only walk-related highways
        walk_types = {"footway", "path", "pedestrian", "steps", "living_street"}
        if hw not in walk_types and tags.get("footway") != "crossing":
            return

        node_ids = [n.ref for n in w.nodes]

        # Keep the way; we'll filter by node presence later
        self.walk_ways.append((w.id, tags, node_ids))


print("Parsing PBF for Seongdong-gu...")
h = ExtractSeongdong()
h.apply_file(PBF, locations=True)
print("Done. Nodes in bbox:", len(h.nodes))
print("Walkways collected:", len(h.walk_ways))

# ---- Build walkways GeoJSON ----
walk_features = []
for osmid, tags, node_ids in h.walk_ways:
    coords = []
    for nid in node_ids:
        if nid in h.nodes:
            lat, lon = h.nodes[nid]
            coords.append([lon, lat])  # GeoJSON uses [lon, lat]

    if len(coords) < 2:
        continue

    feature = {
        "type": "Feature",
        "properties": {
            "osmid": osmid,
            "highway": tags.get("highway", ""),
            "name": tags.get("name", ""),
            "footway": tags.get("footway", "")
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coords
        }
    }
    walk_features.append(feature)

walk_geojson = {
    "type": "FeatureCollection",
    "features": walk_features
}

with open("seongdong_walkways.geojson", "w", encoding="utf-8") as f:
    json.dump(walk_geojson, f, ensure_ascii=False)

print("Wrote seongdong_walkways.geojson with", len(walk_features), "features")

# ---- Build POI GeoJSON ----
poi_features = []
for layer_name, points in h.poi.items():
    for lat, lon, tags in points:
        feature = {
            "type": "Feature",
            "properties": {
                "layer": layer_name,
                "amenity": tags.get("amenity", ""),
                "highway": tags.get("highway", ""),
                "name": tags.get("name", "")
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        poi_features.append(feature)

poi_geojson = {
    "type": "FeatureCollection",
    "features": poi_features
}

with open("seongdong_poi.geojson", "w", encoding="utf-8") as f:
    json.dump(poi_geojson, f, ensure_ascii=False)

print("Wrote seongdong_poi.geojson with", len(poi_features), "features")
