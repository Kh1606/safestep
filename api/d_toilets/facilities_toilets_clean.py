import json
import csv

RAW_PATH = "toilets_raw.json"
OUT_JSON = "toilets_clean.json"
OUT_CSV = "toilets_clean.csv"

# Map original API keys -> nice column names
FIELD_MAP = {
    "fcltNo": "facility_id",              # 화장실 시설 ID
    "fcltNm": "facility_name",            # 화장실 이름/설명
    "lineNm": "line_name",                # 호선 (예: 1호선)
    "stnCd": "station_code",              # 역 코드
    "stnNm": "station_name",              # 역 이름
    "stnNo": "station_number",            # 역 번호
    "crtrYmd": "data_date",               # 기준 날짜 (YYYYMMDD)
    "gateInoutSe": "inside_outside",      # 내부/외부
    "grndUdgdSe": "ground_or_underground",# 지상/지하
    "vcntEntrcNo": "exit_number",         # 출입구 번호 (예: 3, 4, 1,10)
    "dtlPstn": "detail_position",         # 상세 위치 설명
    "rstrmInfo": "toilet_info",           # 일반/교통약자/남녀/공용 등
    "stnFlr": "station_floor",            # 층 (B1, 1, ...)
    "whlchrAcsPsbltyYn": "wheelchair_accessible",  # Y/N
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

    print(f"Total toilet records: {len(clean_rows)}")

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
