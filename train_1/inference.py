from ultralytics import YOLO

def main():
    # Trained weights produced by train.py (see README)
    model = YOLO("wm_yolo11/exp1/weights/best.pt")

    model.predict(
        source="train_1/test_images",  # folder or single image
        imgsz=640,
        conf=0.25,
        device=0,           # GPU id, or "cpu"
        save=True,          # save images with bboxes
        project="wm_yolo11",
        name="pred",        # results folder name
        exist_ok=True,
    )

if __name__ == "__main__":
    main()
