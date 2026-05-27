import json
from pathlib import Path
from ultralytics import YOLO

# ---- CONFIG ----
BASE_DIR     = Path(r"T:\docker\masil\ai")
MODEL_PATH   = BASE_DIR / "masil_v0.1.4.pt"
IMAGES_DIR   = BASE_DIR / "input_images"   # put test images here
RESULTS_DIR  = BASE_DIR / "results"        # YOLO imgs + our JSON
GPS_META_DIR = BASE_DIR / "input_images"        # GPS metadata JSONs from web app

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_gps_meta(stem: str):
    """
    Load GPS metadata JSON for this image, if it exists.

    Example GPS JSON:
    {
      "filename": "20251203_064649_892568.jpg",
      "lat": 37.5427859,
      "lon": 127.0451483,
      "accuracy_m": 14.467,
      "timestamp_utc": "20251203_064649_892568"
    }
    """
    if not GPS_META_DIR.exists():
        return None

    meta_path = GPS_META_DIR / f"{stem}.json"
    if not meta_path.exists():
        return None

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not read GPS meta for {stem}: {e}")
        return None


def main():
    model = YOLO(str(MODEL_PATH))

    results = model.predict(
        source=str(IMAGES_DIR),
        imgsz=640,
        conf=0.25,
        device=0,
        save=True,                           # save annotated images
        project=str(RESULTS_DIR),
        name="pred_images",
        exist_ok=True,
        stream=True,
    )

    for r in results:
        img_path = Path(r.path)     # original image path
        stem = img_path.stem        # e.g. "20251203_064649_892568"
        h, w = r.orig_shape         # (height, width)

        # --- collect detections ---
        detections = []
        for box in r.boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            conf = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()  # bbox in pixels

            detections.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": conf,
                "bbox_xyxy": [x1, y1, x2, y2],
            })

        gps_meta = load_gps_meta(stem) or {}

        # --- final combined JSON for this image ---
        out = {
            "filename": img_path.name,
            "image_width":  w,
            "image_height": h,
            "lat": gps_meta.get("lat"),
            "lon": gps_meta.get("lon"),
            "accuracy_m": gps_meta.get("accuracy_m"),
            "timestamp_utc": gps_meta.get("timestamp_utc"),
            "detections": detections,
        }

        json_path = RESULTS_DIR / f"{stem}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        print("Saved combined JSON:", json_path)


if __name__ == "__main__":
    main()
