# clean_wheelchair_lifts.py
import json
import csv

INPUT = "wheelchair_lifts_raw.json"
OUTPUT = "wheelchair_lifts_clean.csv"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

body = data.get("response", {}).get("body", {})
items_block = body.get("items", {})
items = items_block.get("item", [])

if isinstance(items, dict):
    items = [items]

# 원본 -> 새 컬럼 이름 매핑
field_map = {
    "fcltNo": "facility_id",
    "fcltNm": "facility_name_kor",        # 승강기)휠체어리프트-신설동(2) 승강장 내부3 ...
    "lineNm": "line_name",               # 1호선, 2호선 ...
    "stnCd": "station_code",
    "stnNm": "station_name",
    "stnNo": "station_number",
    "crtrYmd": "record_date_yyyymmdd",   # 기준일자

    "elvtrSn": "lift_serial_no",
    "mngNo": "management_id",            # 내부1 / 내부2 등 관리번호
    "vcntEntrcNo": "entrance_no_or_internal",  # 1,2,3 / 내부 등

    "bgngFlrGrndUdgdSe": "start_floor_type",     # 지상 / 지하
    "bgngFlr": "start_floor",                    # B2, 1 ...
    "bgngFlrDtlPstn": "start_detail_position",   # 예: 용두 방면4-4

    "endFlrGrndUdgdSe": "end_floor_type",
    "endFlr": "end_floor",
    "endFlrDtlPstn": "end_detail_position",

    "elvtrLen": "lift_length",          # 길이 (m 또는 mm, 원본 그대로)
    "elvtrWdthBt": "lift_width",        # 폭
    "limitWht": "weight_limit",         # 300, 4인승 등

    "oprtngSitu": "status_M_running_S_stopped",  # M=운행, S=중지
}

fieldnames = list(field_map.values())

rows = []
for item in items:
    row = {}
    for src, dst in field_map.items():
        row[dst] = item.get(src, "")
    rows.append(row)

with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Saved {OUTPUT} with {len(rows)} rows")
