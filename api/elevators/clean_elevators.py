import json
import csv

# 1. Load the raw response
with open("elevators_raw.json", "r", encoding="utf-8") as f:
    data = json.load(f)

body = data["response"]["body"]
items_container = body.get("items", {})
items = items_container.get("item", [])

if isinstance(items, dict):
    items = [items]

print("Items:", len(items))

# 2. Pick only the useful fields
clean = []
for it in items:
    clean.append({
        "fcltNo": it.get("fcltNo"),
        "station_name": it.get("stnNm"),
        "line": it.get("lineNm"),
        "station_no": it.get("stnNo"),
        "exit_no": it.get("vcntEntrcNo"),   # e.g. '3', '1,10', '내부'
        "detail_pos": it.get("dtlPstn"),    # text description
        "start_floor_type": it.get("bgngFlrGrndUdgdSe"),  # 지하/지상
        "start_floor": it.get("bgngFlr"),
        "end_floor_type": it.get("endFlrGrndUdgdSe"),
        "end_floor": it.get("endFlr"),
        "status": it.get("oprtngSitu"),     # M/S/I code
    })

# 3. Save as JSON
with open("elevators_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)

# 4. Save as CSV (easy to open in Excel)
fieldnames = list(clean[0].keys())
with open("elevators_clean.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(clean)

print("Saved elevators_clean.json and elevators_clean.csv")
