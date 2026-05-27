import requests
import json

import os
SERVICE_KEY = os.environ.get("SEOUL_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/B553766/wksn"

def fetch_elevators():
    url = f"{BASE_URL}/getWksnElvtr"
    params = {
        "serviceKey": SERVICE_KEY,
        "dataType": "JSON",
        "pageNo": 1,
        "numOfRows": 1000,
    }
    r = requests.get(url, params=params)
    print("Status:", r.status_code)
    print("Request URL:", r.url)

    data = r.json()
    return data

data = fetch_elevators()

body = data["response"]["body"]

# items is a dict: {"item": [...]} or {"item": {...}}
items_container = body.get("items", {})
items = items_container.get("item", [])

# If there's only one item, it may be a dict → wrap it in a list
if isinstance(items, dict):
    items = [items]

print("Total items from API:", body.get("totalCount"))
print("Items we parsed:", len(items))

# Show first few items
for item in items[:3]:
    print(
        item.get("stnNm"),      # station name
        item.get("lineNm"),     # line
        item.get("dtlPstn"),    # detailed position
        item.get("oprtngSitu"), # operation status
    )

# Save full data if you want
with open("elevators_raw.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
