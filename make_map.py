import osmium
import folium
from collections import defaultdict

PBF = "Seoul.osm.pbf"

# Example bbox (Gangnam-ish). Change later.
# (min_lon, min_lat, max_lon, max_lat)
BBOX = (127.020, 37.490, 127.040, 37.510)

def in_bbox(lat, lon, bbox=BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)

class Extract(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}               # node_id -> (lat, lon)
        self.ways = []                # list of (tags, [node_ids])
        self.poi = defaultdict(list)  # layer -> list of (lat, lon, tags)

    def node(self, n):
        if not n.location.valid():
            return
        lat, lon = n.location.lat, n.location.lon
        if in_bbox(lat, lon):
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
        # keep only interesting linear features
        if "highway" not in tags and tags.get("footway") != "crossing":
            return
        # store ways; we’ll draw only those whose nodes are in bbox
        self.ways.append((tags, [n.ref for n in w.nodes]))

h = Extract()
h.apply_file(PBF, locations=True)

# Center map on bbox
center_lat = (BBOX[1] + BBOX[3]) / 2
center_lon = (BBOX[0] + BBOX[2]) / 2
m = folium.Map(location=[center_lat, center_lon], zoom_start=16, control_scale=True)

# Draw roads/paths (simple)
for tags, node_ids in h.ways:
    coords = []
    for nid in node_ids:
        if nid in h.nodes:
            lat, lon = h.nodes[nid]
            coords.append((lat, lon))
    if len(coords) < 2:
        continue

    hw = tags.get("highway", "")
    if hw == "steps":
        folium.PolyLine(coords, weight=4, tooltip="stairs").add_to(m)
    elif hw in ("footway", "path", "pedestrian"):
        folium.PolyLine(coords, weight=2, tooltip=hw).add_to(m)
    else:
        folium.PolyLine(coords, weight=2, tooltip=hw).add_to(m)

# POI layers
def add_points(layer_name, points):
    fg = folium.FeatureGroup(name=layer_name, show=True)
    for lat, lon, tags in points:
        title = f"{layer_name}\n{tags}"
        folium.CircleMarker([lat, lon], radius=4, tooltip=title).add_to(fg)
    fg.add_to(m)

add_points("elevators", h.poi["elevators"])
add_points("crossings", h.poi["crossings"])
add_points("benches", h.poi["benches"])
add_points("toilets", h.poi["toilets"])

folium.LayerControl(collapsed=False).add_to(m)
m.save("map.html")
print("Wrote map.html (open it in your browser)")
