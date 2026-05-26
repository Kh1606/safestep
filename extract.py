import csv
import osmium

PBF = "Seoul.osm.pbf"            # <-- change if needed
OUT = "features_seoul.csv"
LIMIT_EACH = 3000             # keep it fast; increase later

def is_stairs(tags):
    return tags.get("highway") == "steps"

def is_elevator(tags):
    return tags.get("highway") == "elevator"

def is_crossing(tags):
    # common patterns in OSM
    return tags.get("footway") == "crossing" or tags.get("highway") == "crossing"

class Extract(osmium.SimpleHandler):
    def __init__(self, writer):
        super().__init__()
        self.w = writer
        self.count = {"stairs": 0, "elevator": 0, "crossing": 0}

    def _emit(self, kind, obj_id, lat, lon, tags_dict):
        # store only a few tags to keep CSV readable
        keep_keys = [
            "highway", "footway", "wheelchair", "ramp", "incline",
            "surface", "smoothness", "lit", "step_count", "name"
        ]
        small = {k: tags_dict.get(k) for k in keep_keys if k in tags_dict}
        self.w.writerow([kind, obj_id, lat, lon, small])

    def node(self, n):
        tags = dict(n.tags)

        if is_stairs(tags) and self.count["stairs"] < LIMIT_EACH:
            self._emit("stairs_node", n.id, n.location.lat, n.location.lon, tags)
            self.count["stairs"] += 1

        if is_elevator(tags) and self.count["elevator"] < LIMIT_EACH:
            self._emit("elevator_node", n.id, n.location.lat, n.location.lon, tags)
            self.count["elevator"] += 1

        if is_crossing(tags) and self.count["crossing"] < LIMIT_EACH:
            self._emit("crossing_node", n.id, n.location.lat, n.location.lon, tags)
            self.count["crossing"] += 1

    def way(self, w):
        tags = dict(w.tags)

        if is_stairs(tags) and self.count["stairs"] < LIMIT_EACH:
            self._emit("stairs_way", w.id, "", "", tags)
            self.count["stairs"] += 1

        if is_elevator(tags) and self.count["elevator"] < LIMIT_EACH:
            self._emit("elevator_way", w.id, "", "", tags)
            self.count["elevator"] += 1

        if is_crossing(tags) and self.count["crossing"] < LIMIT_EACH:
            self._emit("crossing_way", w.id, "", "", tags)
            self.count["crossing"] += 1

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kind", "id", "lat", "lon", "tags"])
    Extract(w).apply_file(PBF, locations=True)

print("Wrote:", OUT)
