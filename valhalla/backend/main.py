# backend/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# allow browser to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALHALLA_URL = os.environ.get("VALHALLA_URL", "http://localhost:8002") + "/route"

# 4km2 bbox
MIN_LON = 127.0338335438
MIN_LAT = 37.5337808883
MAX_LON = 127.0564924562
MAX_LAT = 37.5517471117

def in_bbox(lat: float, lon: float) -> bool:
    return (MIN_LAT <= lat <= MAX_LAT) and (MIN_LON <= lon <= MAX_LON)

def decode_polyline6(s: str):
    coords = []
    index = 0
    lat = 0
    lng = 0
    length = len(s)

    while index < length:
        shift = 0
        result = 0
        while True:
            b = ord(s[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        shift = 0
        result = 0
        while True:
            b = ord(s[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        coords.append((lng / 1e6, lat / 1e6))  # GeoJSON wants (lon,lat)

    return coords

@app.get("/route")
def route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    if not in_bbox(start_lat, start_lon) or not in_bbox(end_lat, end_lon):
        raise HTTPException(status_code=400, detail="Start or end is outside the 4km² area")

    payload = {
        "locations": [
            {"lat": start_lat, "lon": start_lon},
            {"lat": end_lat, "lon": end_lon},
        ],
        "costing": "pedestrian",
    }

    r = requests.post(VALHALLA_URL, json=payload, timeout=60)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Valhalla error: {r.text}")

    data = r.json()
    shape = data["trip"]["legs"][0]["shape"]
    coords = decode_polyline6(shape)

    if len(coords) < 2:
        raise HTTPException(status_code=500, detail="Route geometry too short")

    return {
        "type": "Feature",
        "properties": {
            "distance_km": data["trip"]["summary"]["length"],
            "time_sec": data["trip"]["summary"]["time"],
            "costing": "pedestrian",
        },
        "geometry": {"type": "LineString", "coordinates": coords},
    }
