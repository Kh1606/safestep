import os
from pathlib import Path
import time


import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

VALHALLA_URL = os.environ.get("VALHALLA_URL", "http://valhalla:8002")

BASE_DIR = Path(__file__).resolve().parents[1]          # webapp/
DATA_DIR = BASE_DIR / "data"                           # webapp/data/
STATIC_DIR = Path(__file__).resolve().parent / "static" # webapp/app/static/

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/layers/{name}")
def get_layer(name: str):
    path = DATA_DIR / f"{name}.geojson"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Layer not found: {name}")
    return FileResponse(str(path), media_type="application/geo+json")

@app.post("/api/route")
def route(body: dict):
    r = requests.post(f"{VALHALLA_URL}/route", json=body, timeout=60)
    if not r.ok:
        # return Valhalla's real error message
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return JSONResponse(r.json())

    
# --- simple in-memory cache (optional, but helps avoid spamming) ---
_GEOCACHE = {}  # q -> (ts, data)
_GEOCACHE_TTL = 60  # seconds

# Seongdong-gu bbox (minlon, minlat, maxlon, maxlat)
SEONGDONG_BBOX = (127.008302, 37.5301151, 127.073761, 37.5730162)

# --- Kakao geocoding (replace Nominatim) ---
KAKAO_REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY", "").strip()

# Seongdong-gu bbox (minlon, minlat, maxlon, maxlat)
SEONGDONG_BBOX = (127.008302, 37.5301151, 127.073761, 37.5730162)

def _in_bbox(lon: float, lat: float, bbox=SEONGDONG_BBOX) -> bool:
    minlon, minlat, maxlon, maxlat = bbox
    return (minlon <= lon <= maxlon) and (minlat <= lat <= maxlat)

def _kakao_get(url: str, params: dict):
    if not KAKAO_REST_API_KEY:
        raise HTTPException(status_code=500, detail="KAKAO_REST_API_KEY not set")

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Kakao geocode error: {e}")

@app.get("/api/geocode")
def geocode(q: str = Query(..., min_length=2), limit: int = Query(5, ge=1, le=10)):
    q = q.strip()

    # cache (keep your existing cache logic if you want)
    now = time.time()
    cached = _GEOCACHE.get((q, limit))
    if cached and (now - cached[0]) < _GEOCACHE_TTL:
        return cached[1]

    minlon, minlat, maxlon, maxlat = SEONGDONG_BBOX
    rect = f"{minlon},{minlat},{maxlon},{maxlat}"

    out = []
    seen = set()

    # 1) Address search (best for exact road/lot addresses)
    addr_json = _kakao_get(
        "https://dapi.kakao.com/v2/local/search/address.json",
        {"query": q, "size": min(limit, 30), "page": 1, "analyze_type": "similar"},
    )

    for d in addr_json.get("documents", []):
        try:
            lon = float(d["x"])
            lat = float(d["y"])
        except Exception:
            continue
        if not _in_bbox(lon, lat):
            continue

        # prefer road address name if exists
        display = (
            (d.get("road_address") or {}).get("address_name")
            or (d.get("address") or {}).get("address_name")
            or d.get("address_name", "")
        )

        key = (round(lat, 7), round(lon, 7), display)
        if key in seen:
            continue
        seen.add(key)

        out.append({"display_name": display, "lat": lat, "lon": lon, "source": "address"})
        if len(out) >= limit:
            _GEOCACHE[(q, limit)] = (now, out)
            return out

    # 2) Keyword search fallback (good for POIs like stations, cafes)
    kw_json = _kakao_get(
        "https://dapi.kakao.com/v2/local/search/keyword.json",
        {"query": q, "rect": rect, "size": min(limit, 15), "page": 1},
    )

    for d in kw_json.get("documents", []):
        try:
            lon = float(d["x"])
            lat = float(d["y"])
        except Exception:
            continue
        if not _in_bbox(lon, lat):
            continue

        name = d.get("place_name", "")
        road = d.get("road_address_name", "")
        addr = d.get("address_name", "")
        display = " • ".join([x for x in [name, road or addr] if x])

        key = (round(lat, 7), round(lon, 7), display)
        if key in seen:
            continue
        seen.add(key)

        out.append({"display_name": display, "lat": lat, "lon": lon, "source": "keyword"})
        if len(out) >= limit:
            break

    _GEOCACHE[(q, limit)] = (now, out)
    return out


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
