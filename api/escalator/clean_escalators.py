import json
import csv

RAW_PATH = "escalators_raw.json"
OUT_JSON = "escalators_clean.json"
OUT_CSV = "escalators_clean.csv"

# Map original API keys -> nicer column names
FIELD_MAP = {
    "fcltNo": "facility_id",                     # 시설 ID
    "fcltNm": "facility_name",                   # 에스컬레이터 이름/설명
    "lineNm": "line_name",                       # 호선 (1호선 등)
    "stnCd": "station_code",                     # 역 코드
    "stnNm": "station_name",                     # 역 이름
    "stnNo": "station_number",                   # 역 번호
    "crtrYmd": "data_date",                      # 기준 날짜 (YYYYMMDD)
    "upbdnbSe": "direction",                     # 상행 / 하행
    "vcntEntrcNo": "exit_number_or_inside",      # 1,2,5, '내부' 등
    "bgngFlrGrndUdgdSe": "start_floor_type",     # 지상 / 지하
    "bgngFlr": "start_floor",                    # 1, B1, B2...
    "bgngFlrDtlPstn": "start_floor_detail",      # 시작 위치 설명
    "endFlrGrndUdgdSe": "end_floor_type",        # 지상 / 지하
    "endFlr": "end_floor",                       # 1, B1, B2...
    "endFlrDtlPstn": "end_floor_detail",         # 끝 위치 설명
    "elvtrWdthBt": "width_mm",                   # 폭 (mm)
    "oprtngSitu": "operating_status",            # M 등 (운행 상태 코드)
}

def main():
    # 1) Load raw JSON
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["response"]["body"]["items"]["item"]
    if isinstance(items, dict):
        items = [items]

    clean_rows = []
    for it in items:
        row = {}
        for src_key, dst_key in FIELD_MAP.items():
            value = it.get(src_key)
            if value is None:
                value = ""
            row[dst_key] = value
        clean_rows.append(row)

    print(f"Total escalator records: {len(clean_rows)}")

    # 2) Save as JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(clean_rows, f, ensure_ascii=False, indent=2)

    # 3) Save as CSV
    fieldnames = list(FIELD_MAP.values())
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)

    print(f"Saved {OUT_JSON} and {OUT_CSV}")

if __name__ == "__main__":
    main()
