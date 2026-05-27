import osmium
import json
from collections import defaultdict

PBF = "Seoul.osm.pbf"   # update path if needed
BBOX = (127.00, 37.52, 127.06, 37.575)  # Seongdong-gu approx


def in_bbox(lat, lon, bbox=BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)


def is_pedestrian_accessible(tags):
    """
    Decide if a way is usable for pedestrians.

    We include:
      - dedicated pedestrian infrastructure: footway, path, steps, pedestrian, living_street, track
      - normal roads (residential, tertiary, primary, etc.) unless explicitly foot=no/private/motorroad=yes
    """
    hw = tags.get("highway", "")

    # 1) Dedicated pedestrian infrastructure
    dedicated_foot = {
        "footway", "path", "pedestrian", "steps", "living_street",
        "track", "corridor"
    }
    if hw in dedicated_foot:
        return True

    # 2) Normal roads that usually allow walking
    road_types = {
        "residential", "unclassified", "service",
        "tertiary", "tertiary_link",
        "secondary", "secondary_link",
        "primary", "primary_link"
    }
    if hw in road_types:
        # Skip if explicitly forbidden
        if tags.get("foot") in {"no", "private"}:
            return False
        if tags.get("motorroad") == "yes":
            return False
        # Otherwise assume walkable (at least on sidewalk)
        return True

    # 3) Motorways / trunks: only if explicitly marked as foot=yes
    car_only = {"motorway", "motorway_link", "trunk", "trunk_link"}
    if hw in car_only:
        return tags.get("foot") in {"yes", "designated"}

    # 4) Everything else: not included for now
    return False


def classify_walk_category(tags):
    hw = tags.get("highway", "")
    dedicated_foot = {
        "footway", "path", "pedestrian", "steps", "living_street",
        "track", "corridor"
    }
    if hw in dedicated_foot:
        return "footway"
    road_types = {
        "residential", "unclassified", "service",
        "tertiary", "tertiary_link",
        "secondary", "secondary_link",
        "primary", "primary_link"
    }
    if hw in road_types:
        return "road"
    return "other"


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

        # POIs
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
        if not is_pedestrian_accessible(tags):
            return

        node_ids = [n.ref for n in w.nodes]
        self.walk_ways.append((w.id, tags, node_ids))


print("Parsing PBF for Seongdong-gu...")
h = ExtractSeongdong()
h.apply_file(PBF, locations=True)
print("Done. Nodes in bbox:", len(h.nodes))
print("Walkways (all walkable ways) collected:", len(h.walk_ways))

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

    walk_cat = classify_walk_category(tags)

    feature = {
        "type": "Feature",
        "properties": {
            "osmid": osmid,
            "highway": tags.get("highway", ""),
            "name": tags.get("name", ""),
            "footway": tags.get("footway", ""),
            "sidewalk": tags.get("sidewalk", ""),
            "surface": tags.get("surface", ""),
            "walk_cat": walk_cat,  # footway / road / other
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
