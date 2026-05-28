"""Render the SafeStep 'how it works' flowchart.

Run from this directory:  python howitworks.py
Deps:  pip install diagrams cairosvg   (and Graphviz on PATH)
Icons: brand-colored PNGs under app/assets/_diagram_icons/ (run scripts/gen_diagram_icons.py once).
"""
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.generic.storage import Storage
from diagrams.generic.compute import Rack
from diagrams.custom import Custom

ICONS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "_diagram_icons"))


def icon(name: str) -> str:
    return os.path.join(ICONS, f"{name}.png")


graph_attr = {"fontsize": "18", "bgcolor": "white", "pad": "0.4", "splines": "spline"}
node_attr = {"fontsize": "13"}
edge_attr = {"fontsize": "11"}

with Diagram(
    "SafeStep — accessible pedestrian routing for Seoul",
    filename="howitworks",
    direction="LR",
    show=False,
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    with Cluster("Data sources"):
        osm = Storage("OpenStreetMap\n(.pbf)")
        soa = Storage("Seoul open-data\naccessibility POIs")
        imgs = Storage("Street imagery")

    with Cluster("Processing"):
        osmium = Custom("osmium\nwalkways extract", icon("openstreetmap"))
        poi = Custom("POI scripts\nelevators · lifts ·\ntoilets · escalators", icon("python"))
        yolo = Custom("YOLOv11\nhazard detection", icon("ultralytics"))

    with Cluster("Backend"):
        valhalla = Rack("Valhalla\ncustom pedestrian\nprofile")
        api = Custom("FastAPI\n/api/route · /layers ·\n/api/geocode (Kakao)", icon("fastapi"))

    ui = Custom("Leaflet UI\nSeongdong-gu highlight\nmodes + layers", icon("leaflet"))

    osm >> Edge(color="#0ea5e9") >> osmium
    osmium >> Edge(color="#0ea5e9", label="walkways") >> valhalla

    soa >> Edge(color="#10b981") >> poi
    poi >> Edge(color="#10b981", label="POIs") >> api

    imgs >> Edge(color="#ef4444") >> yolo
    yolo >> Edge(color="#ef4444", label="hazards") >> api

    valhalla >> Edge(color="#111111", label="routes") >> api
    api >> Edge(color="#f59e0b", label="JSON") >> ui
