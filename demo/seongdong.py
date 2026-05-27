import osmium
import folium
from collections import defaultdict

# Path to your Seoul PBF on NAS
PBF = "Seoul.osm.pbf"   # e.g. "/volume1/data/Seoul.osm.pbf"

# Approximate bounding box for Seongdong-gu (min_lon, min_lat, max_lon, max_lat)
# Center ~ (37.5478, 127.0246), so we expand a bit around it.
BBOX = (127.00, 37.52, 127.06, 37.575)  # tweak later if needed

def in_bbox(lat, lon, bbox=BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)

class Extract(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}               # node_id -> (lat, lon) ONLY inside bbox
        self.ways = []                # list of (tags, [node_ids]) (highways in bbox)
        self.poi = defaultdict(list)  # layer -> list of (lat, lon, tags)

    def node(self, n):
        if not n.location.valid():
            return

        lat, lon = n.location.lat, n.location.lon
        if not in_bbox(lat, lon):
            return

        # store only nodes inside bbox
        self.nodes[n.id] = (lat, lon)

        tags = dict(n.tags)

        # POIs we care about (only if node is in bbox)
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

        # keep only ways that are interesting for us:
        # any 'highway' (roads, paths, steps, cycleways, etc.)
        # or footway=crossing
        if "highway" not in tags and tags.get("footway") != "crossing":
            return

        node_ids = [n.ref for n in w.nodes]

        # Check if at least one node of this way is inside bbox
        # (we'll only draw segments we have nodes for)
        if not any(nid in self.nodes for nid in node_ids):
            # NOTE: nodes inside bbox are filled in node() first,
            # but for safety, we still keep the way: we might process nodes later
            pass

        self.ways.append((tags, node_ids))


print("Parsing PBF within Seongdong-gu bbox...", BBOX)
h = Extract()
h.apply_file(PBF, locations=True)
print("Finished parsing. Nodes in bbox:", len(h.nodes))
print("Ways kept:", len(h.ways))

# Center map on bbox
center_lat = (BBOX[1] + BBOX[3]) / 2.0
center_lon = (BBOX[0] + BBOX[2]) / 2.0
print("Map center:", center_lat, center_lon)

# Create Folium map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=15,         # closer zoom for district
    control_scale=True,
    tiles="OpenStreetMap"
)

# Draw roads/paths/steps **inside the bbox**
roads_fg = folium.FeatureGroup(name="roads & paths", show=True)
stairs_fg = folium.FeatureGroup(name="stairs (highway=steps)", show=True)

for tags, node_ids in h.ways:
    coords = []
    for nid in node_ids:
        if nid in h.nodes:
            lat, lon = h.nodes[nid]
            coords.append((lat, lon))

    if len(coords) < 2:
        continue

    hw = tags.get("highway", "")

    # Highlight steps separately
    if hw == "steps":
        folium.PolyLine(
            coords,
            weight=4,
            color="red",
            tooltip="stairs"
        ).add_to(stairs_fg)
    else:
        # All other highways: light grey/blue
        folium.PolyLine(
            coords,
            weight=2,
            color="#666666",
            tooltip=hw
        ).add_to(roads_fg)

roads_fg.add_to(m)
stairs_fg.add_to(m)

# POI layers
def add_points(layer_name, points, color):
    if not points:
        return
    fg = folium.FeatureGroup(name=layer_name, show=True)
    for lat, lon, tags in points:
        title = f"{layer_name}\n{tags}"
        folium.CircleMarker(
            [lat, lon],
            radius=4,
            tooltip=title,
            color=color,
            fill=True,
            fill_opacity=0.8,
        ).add_to(fg)
    fg.add_to(m)

add_points("elevators", h.poi["elevators"], "blue")
add_points("crossings", h.poi["crossings"], "green")
add_points("benches",   h.poi["benches"],   "orange")
add_points("toilets",   h.poi["toilets"],   "purple")

folium.LayerControl(collapsed=False).add_to(m)

out_file = "seongdonggu_detailed.html"
m.save(out_file)
print(f"Wrote {out_file} (open it in your browser)")
