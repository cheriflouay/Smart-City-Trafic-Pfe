from ultralytics import YOLO
import cv2

# ==============================
# Load YOLOv8 nano model
# ==============================
model = YOLO("yolov8n.pt")

# ==============================
# Load traffic video
# ==============================
video_path = "data/videos/traffic.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Error: Cannot open video.")
    exit()

# Get original video size
orig_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

WINDOW_NAME = "Traffic Detection"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, orig_width, orig_height)

# ==============================
# Performance settings
# ==============================
PROCESS_WIDTH = 640   # YOLO works on smaller frame
CONFIDENCE = 0.5

CLASSES = [0, 1, 2, 3, 5, 7]

# ==============================
# Video loop
# ==============================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Keep original frame copy
    original_frame = frame.copy()

    # Resize for YOLO processing
    h, w, _ = frame.shape
    scale = PROCESS_WIDTH / w
    small_frame = cv2.resize(frame, (PROCESS_WIDTH, int(h * scale)))

    # YOLO inference on small frame
    results = model(
        small_frame,
        conf=CONFIDENCE,
        classes=CLASSES,
        verbose=False
    )

    # Draw detections on small frame
    annotated_small = results[0].plot()

    # Resize detections back to original size
    annotated_frame = cv2.resize(
        annotated_small,
        (orig_width, orig_height)
    )

    # Display at original video size
    cv2.imshow(WINDOW_NAME, annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
