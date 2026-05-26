import time
import json
import pandas as pd
import requests
import folium

OVERPASS = "https://overpass-api.de/api/interpreter"

def overpass(query: str):
    r = requests.get(OVERPASS, params={"data": query}, timeout=60)
    r.raise_for_status()
    return r.json()

def find_station_center(station_name: str):
    # Try to find station (node/way/relation) and use its center
    q = f"""
    [out:json][timeout:40];
    (
      node["public_transport"="station"]["name"="{station_name}"];
      way["public_transport"="station"]["name"="{station_name}"];
      relation["public_transport"="station"]["name"="{station_name}"];
      node["railway"="station"]["name"="{station_name}"];
      way["railway"="station"]["name"="{station_name}"];
      relation["railway"="station"]["name"="{station_name}"];
    );
    out center 1;
    """
    data = overpass(q)
    if not data.get("elements"):
        return None
    el = data["elements"][0]
    if el["type"] == "node":
        return (el["lat"], el["lon"])
    # way/relation
    c = el.get("center")
    if c:
        return (c["lat"], c["lon"])
    return None

def find_entrances_near(lat, lon, radius=800):
    q = f"""
    [out:json][timeout:40];
    (
      node["railway"="subway_entrance"](around:{radius},{lat},{lon});
      node["railway"="station_entrance"](around:{radius},{lat},{lon});
      node["entrance"](around:{radius},{lat},{lon});
    );
    out body;
    """
    data = overpass(q)
    entrances = []
    for el in data.get("elements", []):
        if el["type"] != "node":
            continue
        tags = el.get("tags", {})
        entrances.append({
            "lat": el["lat"],
            "lon": el["lon"],
            "tags": tags
        })
    return entrances

def best_match_point(exit_no, station_center, entrances):
    # exit_no can be like "1", "6", "8", or "내부"
    if station_center is None:
        return None, "no_station_found"

    if exit_no is None:
        return station_center, "station_center"

    s = str(exit_no).strip()

    # "내부" -> station center (no precise coordinate)
    if s == "내부":
        return station_center, "station_center_internal"

    # try exact match on entrance tags (ref / entrance:ref etc.)
    for ent in entrances:
        tags = ent["tags"]
        for k in ["ref", "ref:exit", "exit", "entrance:ref"]:
            if k in tags and str(tags[k]).strip() == s:
                return (ent["lat"], ent["lon"]), "exact_exit_ref"

    # fallback: nearest entrance to station center
    if entrances:
        lat0, lon0 = station_center
        def dist2(ent):
            return (ent["lat"]-lat0)**2 + (ent["lon"]-lon0)**2
        nearest = min(entrances, key=dist2)
        return (nearest["lat"], nearest["lon"]), "nearest_entrance"

    return station_center, "station_center_no_entrances"

def main():
    # Change this filename to your CSV
    csv_path = "국가철도공단_수도권7호선_에스컬레이터_20250930_utf8.csv"

    df = pd.read_csv(csv_path)
    # Expected columns (Korean): 역명, 출입구번호, 상세위치, 시작층, 종료층, 선명, 철도운영기관명, 상하행구분
    needed = ["역명", "출입구번호", "상세위치", "시작층", "종료층", "선명", "철도운영기관명", "상하행구분"]
    for c in needed:
        if c not in df.columns:
            print("Missing column:", c, "Available:", list(df.columns))
            return

    stations = sorted(df["역명"].dropna().unique().tolist())

    station_cache = {}
    entrances_cache = {}

    points = []
    print("Stations:", stations)

    for st in stations:
        center = find_station_center(st)
        station_cache[st] = center
        if center:
            entrances = find_entrances_near(center[0], center[1], radius=800)
        else:
            entrances = []
        entrances_cache[st] = entrances
        print(f"{st}: center={center}, entrances={len(entrances)}")
        time.sleep(1.0)  # be polite to Overpass

    # Build point per row
    for _, row in df.iterrows():
        st = str(row["역명"]).strip()
        exit_no = row["출입구번호"]
        center = station_cache.get(st)
        entrances = entrances_cache.get(st, [])
        pt, quality = best_match_point(exit_no, center, entrances)

        if pt is None:
            continue

        lat, lon = pt
        props = row.to_dict()
        props["location_quality"] = quality
        props["lat"] = lat
        props["lon"] = lon
        points.append(props)

    out_df = pd.DataFrame(points)
    out_df.to_csv("escalators_with_coords.csv", index=False, encoding="utf-8-sig")
    print("Saved: escalators_with_coords.csv")

    # GeoJSON output
    features = []
    for p in points:
        features.append({
            "type": "Feature",
            "properties": {k: v for k, v in p.items() if k not in ["lat", "lon"]},
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]}
        })
    gj = {"type": "FeatureCollection", "features": features}
    with open("escalators_points.geojson", "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)
    print("Saved: escalators_points.geojson")

    # HTML map
    # center map on first point
    m = folium.Map(location=[points[0]["lat"], points[0]["lon"]], zoom_start=12)
    for p in points:
        popup = folium.Popup(html="<br>".join([f"{k}: {p[k]}" for k in ["역명","출입구번호","상하행구분","상세위치","시작층","종료층","location_quality"] if k in p]), max_width=450)
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=5,
            popup=popup
        ).add_to(m)

    m.save("escalators_map.html")
    print("Saved: escalators_map.html (open it in your browser)")

if __name__ == "__main__":
    main()
