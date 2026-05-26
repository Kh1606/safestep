from ultralytics import YOLO

def main():
    # 1) Load model
    model = YOLO("yolo11n.pt")  # already downloaded

    # 2) Train
    model.train(
        data="train_1/data.yaml",   # <-- path to your data.yaml
        epochs=30,
        imgsz=640,
        batch=16,
        device=0,           # GPU id, or "cpu"
        workers=0,          # set 0 on Windows when running from a script
        save_period=1,      # save weights every epoch
        project="wm_yolo11",
        name="exp1",
        exist_ok=True,
    )

if __name__ == "__main__":
    main()
