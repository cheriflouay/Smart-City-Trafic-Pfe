# --------------------------------------------------
# GLOBAL CONFIGURATION FILE
# --------------------------------------------------

# Video & Model
VIDEO_PATH = "data/videos/traffic.mp4"
MODEL_PATH = "models/yolov8n.pt"

# Detection
CONF_THRESHOLD = 0.4
VEHICLE_CLASSES = [2, 3, 5, 7]

# Counting Line
LINE_POSITION = 900
OFFSET = 15

# Smart Light Timing
GREEN_TIME_BASE = 10
YELLOW_TIME = 3

# MQTT
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_LIGHT = "traffic/light"
TOPIC_VIOLATION = "traffic/violation"

# Database
DB_PATH = "traffic_system.db"

# System Info
SYSTEM_ID = "SMART_TRAFFIC_V1"
LOCATION = "Intersection A"
