# src/analysis/vehicle_counting_smart_light.py
import cv2
import numpy as np
import os
import time
import yaml
import joblib 
import warnings 
import argparse
import psutil
import json
import math 
from datetime import datetime
from ultralytics import YOLO
import paho.mqtt.client as mqtt

# 👇 THE FIX: Force the system into Enterprise Headless Mode. 
os.environ["HEADLESS_MODE"] = "1"

# Ignore scikit-learn warnings about feature names
warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------------------------------
# 🎛️ ARGUMENT PARSING (DYNAMIC BENCHMARKING)
# -------------------------------------------------
parser = argparse.ArgumentParser(description="Capgemini Distributed Edge Node")
parser.add_argument("--node", type=str, default="NODE_A", help="Unique ID for this Edge Node")
parser.add_argument("--video", type=str, default=None, help="Path to user uploaded video file")
parser.add_argument("--model", type=str, default=None, help="Path to chosen YOLO model")
args = parser.parse_args()
NODE_ID = args.node

# -------------------------------------------------
# 📦 IMPORT CUSTOM SMART CITY MODULES
# -------------------------------------------------
from src.database.db import init_db, get_connection
from src.utils.logger import setup_logger
from src.decision.fine_calculator import FineCalculator
from src.decision.emergency_logic import EmergencyOverride
from src.utils.ocr_worker import OCRBackgroundWorker
from src.analysis.incident_detector import IncidentDetector

# -------------------------------------------------
# ⚙️ LOAD CONFIGURATION & LOGGER
# -------------------------------------------------
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

logger = setup_logger(f"EdgeWorker_{NODE_ID}")

# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------
os.makedirs("violations", exist_ok=True)

# 🚀 MLOPS: Create retraining folder if enabled
mlops_cfg = config.get("mlops_active_learning", {})
if mlops_cfg.get("enabled", False):
    os.makedirs(mlops_cfg.get("save_path", "data/needs_retraining"), exist_ok=True)

logger.info(f"🚀 Booting Edge Vision Worker for {NODE_ID}...")

# Dynamic Model Loading
MODEL_PATH = args.model if args.model else config["system"]["model_path"]
logger.info(f"🧠 Loading YOLO Model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

# Make the node "ONNX-Aware" to prevent the .fuse() crash!
if MODEL_PATH.endswith(".pt"):
    model.fuse()
    logger.info("⚙️ PyTorch Model Fused.")
else:
    logger.info("⚡ ONNX Model Loaded (Pre-fused and highly optimized).")

logger.info("🗄 Checking distributed database...")
init_db()

# 🚨 Global flags for Dashboard Emergency Control
emergency_force_green = False
emergency_end_time = 0
restart_requested = False  
ai_confidence = 0.15 # Default AI Confidence Tracker

# 👇 NEW: Initialize the dynamic stop line using the config file as a default starting point
stop_line_y = config.get("speed_estimation", {}).get("line_2_y", 1600) 

# The DevOps Suicide Switch & Emergency Listener
def on_command_message(client, userdata, msg):
    global emergency_force_green, emergency_end_time, restart_requested, ai_confidence, stop_line_y
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        
        if action == "RESET_NODE":
            logger.warning("🔄 Dashboard requested full reset. Rebooting...")
            os._exit(1) # Kills the script
        elif action == "FORCE_GREEN":
            logger.warning(f"🚨 EMERGENCY: Dashboard forced green light for {NODE_ID}")
            emergency_force_green = True
            emergency_end_time = time.time() + payload.get("duration", 15)
        elif action == "RESTART_VIDEO":
            logger.warning(f"🔄 Dashboard requested video restart for {NODE_ID}")
            restart_requested = True
        elif action == "SET_CONFIDENCE": 
            ai_confidence = float(payload.get("value", 0.15))
            logger.info(f"🎛️ AI Confidence dynamically updated to {ai_confidence}")
        elif action == "SET_STOP_LINE": # 👈 NEW: Listen for UI Calibration!
            stop_line_y = int(payload.get("value", stop_line_y))
            logger.info(f"📏 Stop Line dynamically updated to Y: {stop_line_y}")
            
    except Exception as e:
        pass

logger.info("📡 Connecting to MQTT broker...")
broker_address = os.environ.get("MQTT_BROKER", config["mqtt"]["broker"])
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"EdgeClient_{NODE_ID}")

# Apply the listener and subscribe to the node's command channel
mqtt_client.on_message = on_command_message
mqtt_client.connect(broker_address, config["mqtt"]["port"], 60)
mqtt_client.loop_start()
mqtt_client.subscribe(f"smartcity/node/{NODE_ID}/command")

ocr_worker = OCRBackgroundWorker(mqtt_client, config["mqtt"]["topic_violation"])

ml_model = None
try:
    if os.path.exists("models/congestion_model.pkl"):
        ml_model = joblib.load("models/congestion_model.pkl")
        logger.info("🧠 Predictive ML Model Loaded! Proactive Light Control is ACTIVE.")
    else:
        logger.warning("⚠️ No ML model found. Running in standard reactive mode.")
except Exception as e:
    logger.error(f"Failed to load ML model: {e}")

# -------------------------------------------------
# 🦅 BIRD'S-EYE VIEW (BEV) MATH CALCULATION
# -------------------------------------------------
def setup_bev_matrix(cfg):
    try:
        src = np.float32(cfg["bev_homography"]["src_points"])
        dst = np.float32(cfg["bev_homography"]["dst_points"])
        return cv2.getPerspectiveTransform(src, dst)
    except:
        return None

def get_real_world_distance(p1, p2, matrix, ppm):
    if matrix is None: return 999.0
    pts = np.array([[p1, p2]], dtype=np.float32)
    warped = cv2.perspectiveTransform(pts, matrix)[0]
    return math.dist(warped[0], warped[1]) / ppm

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def draw_traffic_light(frame, state):
    h, w = frame.shape[:2]
    box_x1, box_y1 = w - 120, 20
    box_x2, box_y2 = w - 20, 260
    
    cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (40, 40, 40), -1)
    cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 255), 3)
    
    color_red = (0, 0, 255) if state == "RED" else (0, 0, 60)
    color_yellow = (0, 255, 255) if state == "YELLOW" else (0, 60, 60)
    color_green = (0, 255, 0) if state == "GREEN" else (0, 60, 0)
    
    center_x = w - 70
    cv2.circle(frame, (center_x, 70), 25, color_red, -1)     
    cv2.circle(frame, (center_x, 140), 25, color_yellow, -1) 
    cv2.circle(frame, (center_x, 210), 25, color_green, -1)  
    return frame

# -------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------
def main():
    global emergency_force_green, emergency_end_time, restart_requested, ai_confidence, stop_line_y
    
    fine_calculator = FineCalculator()
    emergency_override = EmergencyOverride()
    incident_detector = IncidentDetector(stop_threshold_sec=5.0)

    # SETUP ADVANCED ENTERPRISE FEATURES
    bev_matrix = setup_bev_matrix(config)
    ppm = config.get("bev_homography", {}).get("pixels_per_meter", 25.0)
    tailgate_dist = config.get("bev_homography", {}).get("tailgating_threshold_meters", 2.5)

    # Dynamic Video Path Loading
    VIDEO_PATH = args.video if args.video else config["system"]["video_path"]
    logger.info(f"📹 Loading Video: {VIDEO_PATH}")
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        logger.error(f"❌ Could not open video: {VIDEO_PATH}")
        return

    video_native_fps = cap.get(cv2.CAP_PROP_FPS)

    vehicle_count = 0
    counted_ids = set()
    track_history = {} 
    
    prev_sys_time = 0
    frame_counter = 0  
    
    light_state = "GREEN"
    last_switch_time = time.time()
    last_heartbeat_time = time.time()
    last_frame_write = 0 
    vehicles_interval = 0

    ai_prediction = "NORMAL"
    window_name = f"Smart Traffic System | {NODE_ID}"
    
    if not os.environ.get("HEADLESS_MODE"):
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
    # Cache for bounding boxes during skipped frames
    cached_tracks = []
    inf_time_ms = 0.0 # Initialize inference time tracker

    logger.info(f"✅ Edge Node {NODE_ID} Started Successfully")

    while True:
        # 👇 1. Check if the dashboard clicked the RESTART button
        if restart_requested:
            logger.info("🔄 Restarting video from frame 0...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            counted_ids.clear() 
            track_history.clear()
            frame_counter = 0
            restart_requested = False

        ret, frame = cap.read()
        
        # 👇 2. Stop the video when it ends and show a standby screen
        if not ret:
            standby_frame = np.zeros((config["system"]["screen_height"], config["system"]["screen_width"], 3), dtype=np.uint8)
            cv2.putText(standby_frame, "VIDEO FINISHED - CLICK RESTART ON DASHBOARD", (100, config["system"]["screen_height"]//2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            
            temp_file = f"temp_feed_{NODE_ID}.jpg"
            final_file = f"latest_frame_{NODE_ID}.jpg"
            cv2.imwrite(temp_file, standby_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            try: os.replace(temp_file, final_file)
            except: pass
            
            time.sleep(0.1) # Sleep slightly so we don't fry the CPU while waiting
            continue

        frame_counter += 1
        video_time = frame_counter / video_native_fps
        current_sys_time = time.time()
        
        # Prevent division by zero error for extremely fast loop cycles
        time_diff = current_sys_time - prev_sys_time
        display_fps = 1 / time_diff if time_diff > 0 else 0
        prev_sys_time = current_sys_time

        # Send MQTT Health Heartbeat every 2.0 seconds
        if current_sys_time - last_heartbeat_time > 2.0:
            payload = {
                "node_id": NODE_ID,
                "status": "ONLINE",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent,
                "fps": round(display_fps, 1),           
                "inference_ms": round(inf_time_ms, 1)   
            }
            mqtt_client.publish(f"smartcity/node/{NODE_ID}/heartbeat", json.dumps(payload))
            last_heartbeat_time = current_sys_time

        # ========================================================
        # 🚀 THE FPS BOOST: INFERENCE DECIMATION (FRAME SKIPPING)
        # ========================================================
        if frame_counter % 3 == 0:
            # ---------------- DETECTION & TRACKING ----------------
            inf_start = time.time() 
            results = model.track(frame, persist=True, tracker=config["ai"]["tracker_type"], 
                                  verbose=False, conf=ai_confidence)
            inf_time_ms = (time.time() - inf_start) * 1000 
            
            tracks = []
            
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().numpy()
                classes = results[0].boxes.cls.int().cpu().numpy()
                confs = results[0].boxes.conf.cpu().numpy()
                
                for box, track_id, cls, conf in zip(boxes, track_ids, classes, confs):
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

                    # MLOps Active Learning
                    if mlops_cfg.get("enabled", False) and mlops_cfg["min_conf"] <= conf <= mlops_cfg["max_conf"]:
                        img_name = f"{mlops_cfg.get('save_path')}/retrain_{NODE_ID}_{cls}_{int(time.time())}.jpg"
                        y1_c, y2_c = max(0, y1), min(frame.shape[0], y2)
                        x1_c, x2_c = max(0, x1), min(frame.shape[1], x2)
                        if frame[y1_c:y2_c, x1_c:x2_c].size > 0:
                            cv2.imwrite(img_name, frame[y1_c:y2_c, x1_c:x2_c])

                    # Only track vehicles for intersection logic
                    if cls in config["ai"]["vehicle_classes"]:
                        tracks.append([x1, y1, x2, y2, track_id, cx, cy])
                    
            cached_tracks = tracks 

            # BEV Tailgating Detection
            if bev_matrix is not None:
                for i in range(len(tracks)):
                    for j in range(i + 1, len(tracks)):
                        id1, cx1, cy1 = tracks[i][4], tracks[i][5], tracks[i][6]
                        id2, cx2, cy2 = tracks[j][4], tracks[j][5], tracks[j][6]
                        
                        dist_meters = get_real_world_distance((cx1, cy1), (cx2, cy2), bev_matrix, ppm)
                        
                        if dist_meters < tailgate_dist and abs(cx1 - cx2) < 100:
                            cv2.line(frame, (cx1, cy1), (cx2, cy2), (0, 165, 255), 2)
                            cv2.putText(frame, f"TAILGATING ({dist_meters:.1f}m)", (int((cx1+cx2)/2), int((cy1+cy2)/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            # ---------------- PROCESS TRACKS ----------------
            for track in tracks:
                x1, y1, x2, y2, track_id, cx, cy = map(int, track)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {track_id}", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

                incident_type = incident_detector.update_and_detect(track_id, cx, cy, video_time)
                if incident_type:
                    logger.warning(f"⚠️ INCIDENT DETECTED: {incident_type} | ID: {track_id}")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    y1_crop, y2_crop = max(0, y1), min(frame.shape[0], y2)
                    x1_crop, x2_crop = max(0, x1), min(frame.shape[1], x2)
                    vehicle_img = frame[y1_crop:y2_crop, x1_crop:x2_crop]
                    inc_filename = f"violations/incident_{NODE_ID}_{track_id}_{int(time.time())}.jpg"
                    if vehicle_img.size > 0:
                        cv2.imwrite(inc_filename, vehicle_img)

                    try:
                        conn = get_connection()
                        conn.execute("INSERT INTO incidents (node_id, timestamp, incident_type, severity, vehicle_id, image_path) VALUES (?, ?, ?, ?, ?, ?)",
                                     (NODE_ID, timestamp, incident_type, "HIGH", track_id, inc_filename))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        logger.error(f"Failed to log incident: {e}")
                    
                    incident_detector.history.pop(track_id, None)

                # ---------------- RED LIGHT VIOLATION LOGIC ----------------
                if track_id in track_history:
                    prev_cy = track_history[track_id]
                    
                    # 👇 FIX: Use the Dynamic Stop Line!
                    if (prev_cy <= stop_line_y and cy > stop_line_y) or (prev_cy >= stop_line_y and cy < stop_line_y):
                        if track_id not in counted_ids:
                            
                            is_red_light = (light_state == "RED")

                            if is_red_light:
                                v_type = "RED_LIGHT"
                                calculated_fine = fine_calculator.calculate_fine(v_type, 0)
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                y1_crop, y2_crop = max(0, y1), min(frame.shape[0], y2)
                                x1_crop, x2_crop = max(0, x1), min(frame.shape[1], x2)
                                vehicle_img = frame[y1_crop:y2_crop, x1_crop:x2_crop]
                                filename = f"violations/violation_{NODE_ID}_{track_id}_{int(time.time())}.jpg"
                                
                                if vehicle_img.size > 0:
                                    cv2.imwrite(filename, vehicle_img)
                                    ocr_worker.process_violation(
                                        node_id=NODE_ID, image_path=filename, track_id=track_id,
                                        timestamp=timestamp, light_state=light_state, v_type=v_type,
                                        veh_speed=0.0, fine_amount=calculated_fine
                                    )

                            vehicle_count += 1
                            vehicles_interval += 1
                            counted_ids.add(track_id)

                track_history[track_id] = cy

        else:
            # 💨 SKIPPED FRAME: Just draw the cached tracks to keep the video smooth without AI math!
            for track in cached_tracks:
                x1, y1, x2, y2, track_id, cx, cy = map(int, track)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {track_id}", (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # ---------------- CONGESTION ANALYTICS ----------------
        avg_speed_now = 0.0 # Speed logic removed, defaulting to 0 for DB compatibility
        
        if frame_counter % int(video_native_fps * 3) == 0:
            c_level = "LOW"
            if vehicle_count > 25: c_level = "CRITICAL"
            elif vehicle_count > 15: c_level = "HIGH"
            elif vehicle_count > 8: c_level = "MEDIUM"
            
            try:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO traffic_metrics (node_id, timestamp, vehicle_count, avg_speed, congestion_level)
                    VALUES (?, ?, ?, ?, ?)
                """, (NODE_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), vehicle_count, avg_speed_now, c_level))
                conn.commit()
                conn.close()
            except: pass

        if ml_model and frame_counter % int(video_native_fps * 5) == 0: 
            now = datetime.now()
            try:
                features = [[now.hour, now.minute, now.weekday(), vehicle_count, avg_speed_now]]
                ai_prediction = ml_model.predict(features)[0]
            except: pass

        # ---------------- SMART LIGHT LOGIC WITH IOT OVERRIDE ----------------
        elapsed = current_sys_time - last_switch_time

        if emergency_override.check_override():
            if light_state != "RED":
                light_state = "RED"
                last_switch_time = current_sys_time
                mqtt_client.publish(config["mqtt"]["topic_light"], f"RED_OVERRIDE_{NODE_ID}")
            
            video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cv2.putText(frame, "🚨 EMERGENCY OVERRIDE ACTIVE 🚨", (video_w//2 - 300, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        elif emergency_force_green and current_sys_time < emergency_end_time:
            if light_state != "GREEN":
                light_state = "GREEN"
                last_switch_time = current_sys_time
                mqtt_client.publish(config["mqtt"]["topic_light"], f"GREEN_EMERGENCY_OVERRIDE_{NODE_ID}")
            
            video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cv2.putText(frame, "🚨 EMERGENCY OVERRIDE ACTIVE 🚨", (video_w//2 - 250, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        else:
            emergency_force_green = False # Reset the flag once time expires
            
            if light_state == "GREEN":
                calculated_time = config["traffic_light"]["green_time_base"] + (vehicles_interval * 1)
                if ai_prediction in ["HIGH", "CRITICAL"]: calculated_time += 10.0 
                adaptive_time = min(calculated_time, config["traffic_light"]["max_green_time"])

                if elapsed > adaptive_time:
                    light_state = "YELLOW"
                    last_switch_time = current_sys_time
                    mqtt_client.publish(config["mqtt"]["topic_light"], f"YELLOW_{NODE_ID}")

            elif light_state == "YELLOW":
                if elapsed > config["traffic_light"]["yellow_time"]:
                    light_state = "RED"
                    last_switch_time = current_sys_time
                    mqtt_client.publish(config["mqtt"]["topic_light"], f"RED_{NODE_ID}")

            elif light_state == "RED":
                if elapsed > config["traffic_light"]["green_time_base"]:
                    light_state = "GREEN"
                    vehicles_interval = 0
                    last_switch_time = current_sys_time
                    mqtt_client.publish(config["mqtt"]["topic_light"], f"GREEN_{NODE_ID}")

        # ---------------- DISPLAY & RENDER (CLEAN FEED) ----------------
        
        # 👇 FIX: Draw the Dynamic Stop Line!
        cv2.line(frame, (0, stop_line_y), (frame.shape[1], stop_line_y), (0, 0, 255), 3)
        
        cv2.putText(frame, f"FPS: {int(display_fps)} | Conf: {ai_confidence:.2f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        cv2.putText(frame, f"Active Node: {NODE_ID}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)

        # Draw the lights directly onto the full-quality frame
        frame = draw_traffic_light(frame, light_state)

        # 📡 WINDOWS-SAFE VIDEO BROADCASTING
        if current_sys_time - last_frame_write > 0.04: 
            try:
                # Use exactly ONE static temp file to prevent hard drive filling
                temp_file = f"temp_feed_{NODE_ID}.jpg"
                final_file = f"latest_frame_{NODE_ID}.jpg"
                
                # Write the high-quality frame to the temp file
                cv2.imwrite(temp_file, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                
                # Atomically overwrite the file FastAPI is reading
                os.replace(temp_file, final_file)
            except Exception as e:
                # If FastAPI is locking the file this exact millisecond, ignore it and try again next frame
                pass 
            
            last_frame_write = current_sys_time

        if not os.environ.get("HEADLESS_MODE"):
            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

    cap.release()
    if not os.environ.get("HEADLESS_MODE"):
        cv2.destroyAllWindows()
    mqtt_client.loop_stop()
    logger.info(f"✅ System {NODE_ID} Stopped Successfully")

if __name__ == "__main__":
    main()