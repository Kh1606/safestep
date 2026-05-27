# facilities_wheelchair_lifts.py
import requests
import json

import os
SERVICE_KEY = os.environ.get("SEOUL_API_KEY", "")
BASE_URL = "https://apis.data.go.kr/B553766/wksn"

# ⚠️ IMPORTANT:
# Go to the data.go.kr "미리보기" page for 휠체어리프트,
# copy the part AFTER /wksn/ in the URL, and put it here.
# Example pattern (this is just a guess, so replace it with the REAL one
# if you still get 404):
ENDPOINT_PATH = "getWksnWhcllift"

def fetch_page(page_no: int, num_rows: int = 1000) -> dict:
    url = f"{BASE_URL}/{ENDPOINT_PATH}"
    params = {
        "serviceKey": SERVICE_KEY,
        "dataType": "JSON",   # 서버가 지원하면 JSON, 아니면 XML이 나올 수 있음
        "pageNo": page_no,
        "numOfRows": num_rows,
    }
    r = requests.get(url, params=params, timeout=10)
    print(f"Status: {r.status_code}")
    print("Request URL:", r.url)

    # 빠르게 응답 내용 앞부분 확인
    print("Raw first 200 chars:", r.text[:200].replace("\n", " "))

    r.raise_for_status()

    # JSON 파싱 시도 (만약 XML이면 여기서 에러 남)
    try:
        data = r.json()
    except Exception:
        print("❌ JSON이 아니라 XML로 응답 온 것 같아요. dataType 파라미터나 엔드포인트 이름을 다시 확인해야 합니다.")
        raise

    return data

def main():
    all_items = []
    page_no = 1
    total_count = None

    while True:
        data = fetch_page(page_no)

        body = data.get("response", {}).get("body", {})
        if not body:
            print("No body in response, stop.")
            break

        if total_count is None:
            total_count = int(body.get("totalCount", 0) or 0)

        items_block = body.get("items", {})
        # items: {"item": [...]} 인 구조
        item_list = items_block.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]

        print(f"Page {page_no}: got {len(item_list)} items")
        all_items.extend(item_list)

        # 더 이상 아이템이 없거나, 전체 카운트 이상 모았으면 종료
        if not item_list or len(all_items) >= total_count:
            break

        page_no += 1

    print(f"Total collected items: {len(all_items)} (reported totalCount={total_count})")

    # elevators_raw/toilets_raw 와 비슷한 구조로 저장
    output = {
        "response": {
            "body": {
                "items": {
                    "item": all_items
                },
                "pageNo": 1,
                "numOfRows": len(all_items),
                "totalCount": total_count or len(all_items),
            }
        }
    }

    with open("wheelchair_lifts_raw.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✅ Saved wheelchair_lifts_raw.json")

if __name__ == "__main__":
    main()
