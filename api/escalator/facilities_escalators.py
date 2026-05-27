# facilities_escalator.py
import requests
import json

import os
SERVICE_KEY = os.environ.get("SEOUL_API_KEY", "")

# 🚩 Escalator endpoint (교통약자이용정보_에스컬레이터 조회)
BASE_URL = "https://apis.data.go.kr/B553766/wksn/getWksnEsctr"

def fetch_page(page_no, num_rows=1000):
    params = {
        "serviceKey": SERVICE_KEY,
        "dataType": "JSON",   # <- IMPORTANT: uppercase JSON for this API
        "pageNo": page_no,
        "numOfRows": num_rows,
    }

    r = requests.get(BASE_URL, params=params, timeout=10)
    print(f"Status: {r.status_code}")
    print("Request URL:", r.url)

    # For debugging: show first part of the raw response
    print("Raw first 200 chars:", r.text[:200].replace("\n", " "))

    r.raise_for_status()
    data = r.json()
    return data


def main():
    all_items = []
    page_no = 1
    num_rows = 1000
    first_response = None

    while True:
        data = fetch_page(page_no, num_rows)
        if first_response is None:
            # Keep the first full response structure to reuse for saving
            first_response = data

        body = data.get("response", {}).get("body", {})
        items = body.get("items", {}).get("item", [])

        # API sometimes returns a single dict instead of a list
        if isinstance(items, dict):
            items = [items]

        total_count = body.get("totalCount", 0)
        print(f"Page {page_no}: got {len(items)} items, totalCount={total_count}")

        all_items.extend(items)

        # Stop when we have all records
        if page_no * num_rows >= int(total_count):
            break

        page_no += 1

    if first_response is None:
        print("No data fetched, nothing to save.")
        return

    # Put ALL items into the first response structure
    first_response["response"]["body"]["items"]["item"] = all_items
    first_response["response"]["body"]["totalCount"] = len(all_items)

    # Save as RAW file
    out_path = "escalators_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(first_response, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(all_items)} escalators to {out_path}")


if __name__ == "__main__":
    main()
