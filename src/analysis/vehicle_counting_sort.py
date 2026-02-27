import cv2
import numpy as np
import time
import os
from ultralytics import YOLO
from src.tracking.sort import Sort

# -----------------------------------
# CONFIGURATION
# -----------------------------------
VIDEO_PATH = "data/videos/traffic.mp4"
MODEL_PATH = "models/yolov8n.pt"
CONF_THRESHOLD = 0.4
LINE_POSITION = 450
OFFSET = 15
VEHICLE_CLASSES = [2, 3, 5, 7]

SCREEN_W = 1366
SCREEN_H = 768


def resize_with_aspect_ratio(frame):
    h, w = frame.shape[:2]
    scale = min(SCREEN_W / w, SCREEN_H / h)

    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h))
    canvas = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)

    x_offset = (SCREEN_W - new_w) // 2
    y_offset = (SCREEN_H - new_h) // 2

    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    return canvas


def main():

    if not os.path.exists(VIDEO_PATH):
        print("❌ Video not found.")
        return

    model = YOLO(MODEL_PATH)
    model.fuse()

    tracker = Sort()
    cap = cv2.VideoCapture(VIDEO_PATH)

    window_name = "Vehicle Counting with SORT"

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name,
                          cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)

    vehicle_count = 0
    counted_ids = set()
    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
        prev_time = current_time

        detections = []

        results = model(frame, imgsz=960, verbose=False)

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if cls in VEHICLE_CLASSES and conf > CONF_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detections.append([x1, y1, x2, y2, conf])

        detections = np.array(detections) if len(detections) > 0 else np.empty((0, 5))

        tracks = tracker.update(detections)

        cv2.line(frame, (0, LINE_POSITION),
                 (frame.shape[1], LINE_POSITION),
                 (0, 0, 255), 3)

        for track in tracks:
            x1, y1, x2, y2, track_id = map(int, track)

            cv2.rectangle(frame, (x1, y1), (x2, y2),
                          (0, 255, 0), 2)

            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

            if LINE_POSITION - OFFSET < cy < LINE_POSITION + OFFSET:
                if track_id not in counted_ids:
                    vehicle_count += 1
                    counted_ids.add(track_id)

        cv2.putText(frame, f"Vehicle Count: {vehicle_count}",
                    (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255), 3)

        cv2.putText(frame, f"FPS: {int(fps)}",
                    (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0), 3)

        display_frame = resize_with_aspect_ratio(frame)
        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
