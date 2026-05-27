import requests
import json
import csv

import os
SERVICE_KEY = os.environ.get("SEOUL_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/B553766/wksn"

def fetch_toilets():
    # ⚠️ Endpoint name may vary slightly depending on docs.
    # Try this first; if it fails, we’ll adjust.
    url = f"{BASE_URL}/getWksnRstrm"
    params = {
        "serviceKey": SERVICE_KEY,
        "dataType": "JSON",
        "pageNo": 1,
        "numOfRows": 1000,
    }
    r = requests.get(url, params=params)
    print("Status:", r.status_code)
    print("Request URL:", r.url)
    print("Raw first 200 chars:", r.text[:200])  # debug: see if it’s error or JSON

    data = r.json()
    return data

data = fetch_toilets()

body = data["response"]["body"]
items_container = body.get("items", {})
items = items_container.get("item", [])

if isinstance(items, dict):
    items = [items]

print("Total items from API:", body.get("totalCount"))
print("Items we parsed:", len(items))

# Pick useful fields (names based on typical spec; adjust after seeing real keys)
clean = []
for it in items:
    clean.append({
        "fcltNo": it.get("fcltNo"),
        "station_name": it.get("stnNm"),
        "line": it.get("lineNm"),
        "station_no": it.get("stnNo"),
        "gender": it.get("sexdstnDvNm"),      # 남/여/공용 etc., adjust if diff
        "location": it.get("dtlPstn"),        # 상세위치
        "inside_outside": it.get("vcntEntrcNo"),  # 출입구/내부 구분 등, adjust if diff
        "status": it.get("oprtngSitu"),       # 운영상태, if present
    })

# Save raw
with open("toilets_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Save clean JSON/CSV only if we have items
if clean:
    with open("toilets_clean.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)

    fieldnames = list(clean[0].keys())
    with open("toilets_clean.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean)

    print("Saved toilets_clean.json and toilets_clean.csv")
else:
    print("No toilet items parsed – check key names in toilets_raw.json")
