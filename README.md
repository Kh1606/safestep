# SafeStep — accessible pedestrian routing for Seoul

**SafeStep** plans wheelchair- and mobility-friendly walking routes across Seoul
(prototyped in Seongdong-gu, 성동구). It combines OpenStreetMap walkways, public
accessibility facilities (elevators, wheelchair lifts, accessible toilets, escalators),
AI-detected street hazards, and a custom Valhalla routing profile — served through a
FastAPI web app with an interactive map.

> Originally prototyped as *masil* (마실 — Korean for a neighbourhood stroll).

**🌐 Live demo (hazard map):** https://kh1606.github.io/safestep/

**Stack:** Python · FastAPI · Valhalla · Leaflet · YOLO (Ultralytics) · OpenStreetMap · Kakao / Seoul open-data APIs · Docker

## How it fits together

```
api/        Fetch + clean public accessibility POIs (elevators, wheelchair lifts,
            accessible toilets, escalators) from Seoul open data -> CSV/JSON.
demo/       Seongdong-gu pipeline: extract walkways from OSM, generate routes and
            hazard layers, render the Leaflet map (this powers the live demo).
ai/         YOLO model that detects pedestrian hazards in street imagery and emits
            geo-located hazard JSON (run_yolo_to_json.py, make_hazards_from_ai.py).
valhalla/   Custom Valhalla routing setup (config, backend, tools) for pedestrian /
            accessibility-aware routing.
webapp/     FastAPI app (app/main.py + static UI) tying routing, POIs and hazards
            together with Kakao geocoding. Dockerised (docker-compose).
recon3d/    Experimental 3D reconstruction (video -> COLMAP / NeRF -> glb) + viewer.
version2/   OSM extraction helpers (Seoul / Seongdong boundary + polygons).
web/        Small GPS-tagged photo upload server used to collect hazard imagery.
```

## Setup

```bash
cp .env.example .env     # SEOUL_API_KEY, KAKAO_REST_API_KEY, VALHALLA_URL
```

**Web app**

```bash
cd webapp
docker compose up --build      # http://localhost:8088
```

**Accessibility POIs** (needs `SEOUL_API_KEY`)

```bash
python api/elevators/facilities.py     # + the other api/<type>/ scripts
```

**Hazard detection** (needs YOLO weights — see below)

```bash
python ai/run_yolo_to_json.py
```

## Data & models (not committed)

Large / generated assets are gitignored — bring your own:

- OSM extracts (`*.osm.pbf`) and Valhalla tiles (`valhalla/tiles/`)
- YOLO weights (`ai/*.pt`) and webapp map layers (`webapp/data/`)
- 3D-reconstruction inputs/outputs (videos, frames, NeRF / COLMAP data)

Secrets go in `.env` (see `.env.example`) — never commit real keys.

## License

MIT — see [LICENSE](LICENSE).
