import osmium
import json

PBF_IN = "seoul_4km2.osm.pbf"
ROADS_OUT = "roads.geojson"
CORNERS_OUT = "corners.geojson"

# filter: keep highways that are walk-relevant (you can relax this later)
SKIP_HIGHWAYS = {
    "motorway", "motorway_link",
    "trunk", "trunk_link",
}

class Export(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.roads = []
        self.node_ways = {}   # node_id -> set(way_id)
        self.node_xy = {}     # node_id -> [lon,lat]

    def way(self, w):
        hw = w.tags.get("highway")
        if not hw:
            return
        if hw in SKIP_HIGHWAYS:
            return

        coords = []
        for n in w.nodes:
            if not n.location.valid():
                continue
            lon = float(n.location.lon)
            lat = float(n.location.lat)
            coords.append([lon, lat])
            self.node_xy[n.ref] = [lon, lat]
            self.node_ways.setdefault(n.ref, set()).add(w.id)

        if len(coords) < 2:
            return

        props = {
            "way_id": int(w.id),
            "highway": hw,
            "name": w.tags.get("name"),
            "foot": w.tags.get("foot"),
            "sidewalk": w.tags.get("sidewalk"),
            "surface": w.tags.get("surface"),
        }

        self.roads.append({
            "type": "Feature",
            "properties": {k:v for k,v in props.items() if v is not None},
            "geometry": {"type": "LineString", "coordinates": coords}
        })

def main():
    h = Export()
    # IMPORTANT: locations=True so way nodes have coordinates
    h.apply_file(PBF_IN, locations=True)

    roads_fc = {"type":"FeatureCollection", "features": h.roads}

    # corners = nodes used by 2+ different ways (intersections)
    corner_features = []
    for nid, ways in h.node_ways.items():
        if len(ways) >= 2:   # change to >=3 if you want fewer points
            xy = h.node_xy.get(nid)
            if not xy:
                continue
            corner_features.append({
                "type":"Feature",
                "properties":{"node_id": int(nid), "ways": len(ways)},
                "geometry":{"type":"Point","coordinates": xy}
            })

    corners_fc = {"type":"FeatureCollection", "features": corner_features}

    with open(ROADS_OUT, "w", encoding="utf-8") as f:
        json.dump(roads_fc, f, ensure_ascii=False)

    with open(CORNERS_OUT, "w", encoding="utf-8") as f:
        json.dump(corners_fc, f, ensure_ascii=False)

    print("Wrote:", ROADS_OUT, "features:", len(h.roads))
    print("Wrote:", CORNERS_OUT, "features:", len(corner_features))

if __name__ == "__main__":
    main()
