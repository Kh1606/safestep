import json, requests

def decode_polyline6(s):
    coords=[]
    index=0
    lat=0
    lon=0
    while index < len(s):
        shift=0; result=0
        while True:
            b=ord(s[index])-63; index+=1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20: break
        dlat = ~(result>>1) if (result & 1) else (result>>1)
        lat += dlat

        shift=0; result=0
        while True:
            b=ord(s[index])-63; index+=1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20: break
        dlon = ~(result>>1) if (result & 1) else (result>>1)
        lon += dlon

        coords.append((lat/1e6, lon/1e6))
    return coords

start = {"lat": 37.542764, "lon": 127.045163}
end   = {"lat": 37.548000, "lon": 127.050000}

data = requests.post("http://localhost:8002/route", json={
    "locations":[start,end],
    "costing":"pedestrian"
}, timeout=120).json()

shape = data["trip"]["legs"][0]["shape"]
pts = decode_polyline6(shape)

geojson = {
  "type":"FeatureCollection",
  "features":[{
    "type":"Feature",
    "properties":{
      "costing":"pedestrian",
      "distance_km": data["trip"]["summary"]["length"],
      "time_sec": data["trip"]["summary"]["time"]
    },
    "geometry":{"type":"LineString","coordinates":[[lon,lat] for (lat,lon) in pts]}
  }]
}

with open("route.geojson","w",encoding="utf-8") as f:
    json.dump(geojson,f,ensure_ascii=False)
print("Wrote route.geojson")
