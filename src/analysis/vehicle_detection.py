import cv2
from ultralytics import YOLO
import os
import time
import numpy as np

# -----------------------------
# CONFIGURATION
# -----------------------------
VIDEO_PATH = "data/videos/traffic.mp4"
MODEL_PATH = "models/yolov8n.pt"
CONF_THRESHOLD = 0.4

VEHICLE_CLASSES = [2, 3, 5, 7]


def resize_with_aspect_ratio(frame, screen_width, screen_height):
    h, w = frame.shape[:2]

    scale = min(screen_width / w, screen_height / h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h))

    # Create black canvas
    canvas = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)

    x_offset = (screen_width - new_w) // 2
    y_offset = (screen_height - new_h) // 2

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas


def main():

    if not os.path.exists(VIDEO_PATH):
        print("❌ Video not found.")
        return

    print("🚀 Loading YOLO...")
    model = YOLO(MODEL_PATH)
    model.fuse()

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print("❌ Cannot open video.")
        return

    video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"🎥 Video Resolution: {video_w}x{video_h}")

    # Get screen resolution
    screen_w = 1366
    screen_h = 768

    window_name = "Vehicle Detection - YOLOv8"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(
        window_name,
        cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN
    )

    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
        prev_time = current_time

        results = model(frame, imgsz=960, verbose=False)

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if cls in VEHICLE_CLASSES and conf > CONF_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2),
                                  (0, 255, 0), 2)

        cv2.putText(frame,
                    f"FPS: {int(fps)}",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    3)

        # Resize correctly to fit screen
        display_frame = resize_with_aspect_ratio(
            frame,
            screen_w,
            screen_h
        )

        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
