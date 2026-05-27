#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.prepared import prep

try:
    from shapely import make_valid as _make_valid
except Exception:
    _make_valid = None

DATA_DIR = Path("data")
BOUNDARY_PATH = DATA_DIR / "seongdong_boundary.geojson"

LAYERS = [
    "default_maple_roads",
    "default_parks",
    "default_public_restrooms",
    "default_people_centred_pois",
    "wc_paths",
    "wc_chargers",
    "wc_assistive_centers",
    "wc_accessibility_status",
    "wc_safe_routes",
    "wc_dental_disabled",
    "elder_night_holiday_clinics",
    "elder_late_night_pharmacy",
    "elder_mental_health",
    "bike_paths",
    "bike_facilities",
]

def _swap_xy_coords(obj: Any) -> Any:
    # Recursively swap [x,y] -> [y,x] for coordinate arrays
    if isinstance(obj, list):
        if len(obj) >= 2 and isinstance(obj[0], (int, float)) and isinstance(obj[1], (int, float)):
            return [obj[1], obj[0]] + obj[2:]
        return [_swap_xy_coords(x) for x in obj]
    return obj

def _maybe_swap_geojson_geom(geom: Dict[str, Any]) -> Dict[str, Any]:
    # Swap only when it looks like [lat,lon] (y > 90)
    # Korea correct: [127,37] => y=37 OK
    # Swapped: [37,127] => y=127 invalid => swap
    def first_xy(g):
        t = g.get("type")
        if t == "GeometryCollection":
            geoms = g.get("geometries") or []
            return first_xy(geoms[0]) if geoms else None
        c = g.get("coordinates")
        # dig to first pair
        while isinstance(c, list) and c and not (isinstance(c[0], (int, float)) and len(c) >= 2):
            c = c[0]
        if isinstance(c, list) and len(c) >= 2 and isinstance(c[0], (int,float)) and isinstance(c[1], (int,float)):
            return c[0], c[1]
        return None

    xy = first_xy(geom)
    if not xy:
        return geom
    x, y = xy
    # swap rule: y is invalid latitude but x looks like latitude
    if abs(y) > 90 and abs(x) <= 90:
        g2 = json.loads(json.dumps(geom))  # deep copy
        if g2.get("type") == "GeometryCollection":
            g2["geometries"] = [_maybe_swap_geojson_geom(gg) for gg in (g2.get("geometries") or [])]
            return g2
        g2["coordinates"] = _swap_xy_coords(g2.get("coordinates"))
        return g2
    return geom

def _fix_geom(g):
    if g is None or g.is_empty:
        return None
    if g.is_valid:
        return g
    if _make_valid:
        try:
            gg = _make_valid(g)
            if not gg.is_empty:
                return gg
        except Exception:
            pass
    try:
        gg = g.buffer(0)
        if not gg.is_empty:
            return gg
    except Exception:
        pass
    return g

def load_boundary(path: Path):
    fc = json.loads(path.read_text(encoding="utf-8"))
    geoms = []
    for feat in fc.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        geom = _maybe_swap_geojson_geom(geom)
        geoms.append(shape(geom))
    if not geoms:
        raise RuntimeError("Boundary has no geometry")
    b = unary_union(geoms)
    b = _fix_geom(b)
    if b is None or b.is_empty:
        raise RuntimeError("Boundary is empty after fix")
    return b

def clip_feature(geom_json: Dict[str, Any], boundary, bprep):
    geom_json = _maybe_swap_geojson_geom(geom_json)
    try:
        g = shape(geom_json)
    except Exception:
        return None

    g = _fix_geom(g)
    if g is None or g.is_empty:
        return None

    # sanity: if not WGS84-ish, skip (you must reproject)
    minx, miny, maxx, maxy = g.bounds
    if maxx > 1000 or maxy > 1000:  # likely meters CRS
        return None

    # bbox quick reject
    bx1, by1, bx2, by2 = boundary.bounds
    gx1, gy1, gx2, gy2 = g.bounds
    if gx2 < bx1 or gx1 > bx2 or gy2 < by1 or gy1 > by2:
        return None

    if not bprep.intersects(g):
        return None

    # points keep if inside/intersects
    if g.geom_type in ("Point","MultiPoint"):
        return g

    inter = g.intersection(boundary)
    inter = _fix_geom(inter)
    if inter is None or inter.is_empty:
        return None
    return inter

def main():
    boundary = load_boundary(BOUNDARY_PATH)
    print("Boundary bounds:", boundary.bounds)
    bprep = prep(boundary)

    backup_dir = DATA_DIR / "_full_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for name in LAYERS:
        src = DATA_DIR / f"{name}.geojson"
        if not src.exists():
            print(f"[SKIP] {name} missing")
            continue

        # backup once
        bkp = backup_dir / src.name
        if not bkp.exists():
            bkp.write_bytes(src.read_bytes())

        fc = json.loads(src.read_text(encoding="utf-8"))
        out_feats = []
        skipped_crs = 0

        for feat in fc.get("features", []):
            geom = feat.get("geometry")
            if not geom:
                continue
            clipped = clip_feature(geom, boundary, bprep)
            if clipped is None:
                # detect likely CRS skip
                try:
                    gtmp = shape(_maybe_swap_geojson_geom(geom))
                    if gtmp.bounds[2] > 1000 or gtmp.bounds[3] > 1000:
                        skipped_crs += 1
                except Exception:
                    pass
                continue
            out_feats.append({
                "type": "Feature",
                "properties": feat.get("properties", {}) or {},
                "geometry": mapping(clipped),
            })

        src.write_text(json.dumps({"type":"FeatureCollection","features": out_feats}, ensure_ascii=False), encoding="utf-8")
        print(f"[CLIP] {name}: {len(out_feats)} features (skipped_crs={skipped_crs})")

    print("DONE")

if __name__ == "__main__":
    main()
