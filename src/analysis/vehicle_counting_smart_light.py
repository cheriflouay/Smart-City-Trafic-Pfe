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
from datetime import datetime
from ultralytics import YOLO
import paho.mqtt.client as mqtt

# Ignore scikit-learn warnings about feature names
warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------------------------------
# 🎛️ ARGUMENT PARSING (DISTRIBUTED NODE ID)
# -------------------------------------------------
parser = argparse.ArgumentParser(description="Capgemini Distributed Edge Node")
parser.add_argument("--node", type=str, default="NODE_A", help="Unique ID for this Edge Node (e.g., NODE_A)")
args = parser.parse_args()
NODE_ID = args.node

# -------------------------------------------------
# 📦 IMPORT CUSTOM SMART CITY MODULES
# -------------------------------------------------
from src.database.db import init_db, get_connection
from src.utils.logger import setup_logger
from src.analysis.speed_estimation import SpeedEstimator
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

logger.info(f"🚀 Booting Edge Vision Worker for {NODE_ID}...")
logger.info("🧠 Loading YOLO Model...")
model = YOLO(config["system"]["model_path"])
model.fuse() 

logger.info("🗄 Checking distributed database...")
init_db()

# The DevOps Suicide Switch Listener
def on_command_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("action") == "RESET_NODE":
            logger.warning("🔄 Dashboard requested full reset. Rebooting Docker Container...")
            os._exit(1) # Kills the script so Docker instantly restarts it
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
# HELPER FUNCTIONS
# -------------------------------------------------
def resize_with_aspect_ratio(frame):
    h, w = frame.shape[:2]
    scale = min(config["system"]["screen_width"] / w, config["system"]["screen_height"] / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(frame, (new_w, new_h))
    
    canvas = np.zeros((config["system"]["screen_height"], config["system"]["screen_width"], 3), dtype=np.uint8)
    x_offset, y_offset = (config["system"]["screen_width"] - new_w) // 2, (config["system"]["screen_height"] - new_h) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    return canvas

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
    
    speed_estimator = SpeedEstimator(
        line_1_y=config["speed_estimation"]["line_1_y"],
        line_2_y=config["speed_estimation"]["line_2_y"],
        distance_meters=config["speed_estimation"]["distance_meters"]
    )
    fine_calculator = FineCalculator()
    emergency_override = EmergencyOverride()
    incident_detector = IncidentDetector(stop_threshold_sec=5.0)

    cap = cv2.VideoCapture(config["system"]["video_path"])
    if not cap.isOpened():
        logger.error("❌ Could not open video.")
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
        
    # 👇 NEW: Cache for bounding boxes during skipped frames
    cached_tracks = []

    logger.info(f"✅ Edge Node {NODE_ID} Started Successfully")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.info("🔄 Video ended. Looping back to the start...")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            counted_ids.clear() 
            track_history.clear()
            speed_estimator.entry_times.clear()
            speed_estimator.speeds.clear()
            frame_counter = 0
            continue

        frame_counter += 1
        video_time = frame_counter / video_native_fps
        current_sys_time = time.time()
        display_fps = 1 / (current_sys_time - prev_sys_time) if prev_sys_time != 0 else 0
        prev_sys_time = current_sys_time

        # Send MQTT Health Heartbeat
        if current_sys_time - last_heartbeat_time > 5.0:
            payload = {
                "node_id": NODE_ID,
                "status": "ONLINE",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cpu": psutil.cpu_percent(),
                "ram": psutil.virtual_memory().percent
            }
            mqtt_client.publish(f"smartcity/node/{NODE_ID}/heartbeat", json.dumps(payload))
            last_heartbeat_time = current_sys_time

        # ========================================================
        # 🚀 THE FPS BOOST: INFERENCE DECIMATION (FRAME SKIPPING)
        # ========================================================
        if frame_counter % 2 == 0:
            # ---------------- DETECTION & TRACKING ----------------
            results = model.track(frame, persist=True, tracker=config["ai"]["tracker_type"], 
                                  imgsz=320, verbose=False, classes=config["ai"]["vehicle_classes"])
            tracks = []
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.int().cpu().numpy()
                
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = map(int, box)
                    tracks.append([x1, y1, x2, y2, track_id])
                    
            cached_tracks = tracks # Save boxes for the next skipped frame

            # ---------------- PROCESS TRACKS ----------------
            for track in tracks:
                x1, y1, x2, y2, track_id = map(int, track)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

                veh_speed = speed_estimator.get_speed(track_id)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"ID: {track_id}" if veh_speed is None else f"ID: {track_id} | {veh_speed}km/h"
                cv2.putText(frame, label, (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
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

                # ---------------- CROSSING & VIOLATION LOGIC ----------------
                if track_id in track_history:
                    prev_cy = track_history[track_id]
                    calculated_speed = speed_estimator.update(track_id, prev_cy, cy, video_time)
                    
                    line_2 = config["speed_estimation"]["line_2_y"]
                    if (prev_cy <= line_2 and cy > line_2) or (prev_cy >= line_2 and cy < line_2):
                        if track_id not in counted_ids:
                            
                            is_red_light = (light_state == "RED")
                            is_speeding = False

                            if veh_speed is not None and veh_speed > config["speed_estimation"]["speed_limit_kmh"]:
                                is_speeding = True

                            if is_red_light or is_speeding:
                                if is_red_light and is_speeding:
                                    v_type = "BOTH"
                                elif is_red_light:
                                    v_type = "RED_LIGHT"
                                else:
                                    v_type = "SPEED"

                                calculated_fine = fine_calculator.calculate_fine(v_type, veh_speed)
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
                                        veh_speed=veh_speed, fine_amount=calculated_fine
                                    )

                            vehicle_count += 1
                            vehicles_interval += 1
                            counted_ids.add(track_id)

                track_history[track_id] = cy

        else:
            # 💨 SKIPPED FRAME: Just draw the cached tracks to keep the video smooth without AI math!
            for track in cached_tracks:
                x1, y1, x2, y2, track_id = map(int, track)
                veh_speed = speed_estimator.get_speed(track_id)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"ID: {track_id}" if veh_speed is None else f"ID: {track_id} | {veh_speed}km/h"
                cv2.putText(frame, label, (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)


        # ---------------- CONGESTION ANALYTICS ----------------
        current_speeds = list(speed_estimator.speeds.values())
        avg_speed_now = sum(current_speeds) / len(current_speeds) if current_speeds else 0.0
        
        if frame_counter % int(video_native_fps * 3) == 0:
            c_level = "LOW"
            if vehicle_count > 25 or avg_speed_now < 15: c_level = "CRITICAL"
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

        # ---------------- SMART LIGHT LOGIC WITH IOT & AI OVERRIDE ----------------
        elapsed = current_sys_time - last_switch_time

        if emergency_override.check_override():
            if light_state != "GREEN":
                light_state = "GREEN"
                last_switch_time = current_sys_time
                mqtt_client.publish(config["mqtt"]["topic_light"], f"GREEN_EMERGENCY_OVERRIDE_{NODE_ID}")
            
            video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cv2.putText(frame, "🚨 EMERGENCY OVERRIDE ACTIVE 🚨", (video_w//2 - 250, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        else:
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

        # ---------------- DISPLAY & RENDER (HEADLESS SAFE) ----------------
        cv2.line(frame, (0, config["speed_estimation"]["line_1_y"]), (frame.shape[1], config["speed_estimation"]["line_1_y"]), (255, 0, 0), 2)
        cv2.line(frame, (0, config["speed_estimation"]["line_2_y"]), (frame.shape[1], config["speed_estimation"]["line_2_y"]), (0, 0, 255), 3)
        cv2.putText(frame, f"Total Count: {vehicle_count}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, f"FPS: {int(display_fps)}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
        cv2.putText(frame, f"Active Node: {NODE_ID}", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 100), 2)
        
        if ml_model:
            pred_color = (0, 0, 255) if ai_prediction in ["HIGH", "CRITICAL"] else (0, 255, 0)
            cv2.putText(frame, f"AI Forecast: {ai_prediction}", (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.8, pred_color, 2)

        frame = draw_traffic_light(frame, light_state)
        display_frame = resize_with_aspect_ratio(frame)

        # 👇 THE FIX: Uncapped the UI throttle from 0.15s to 0.04s to allow up to 25 FPS video streaming
        if current_sys_time - last_frame_write > 0.04: 
            try:
                # 1. Compress image in RAM first
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
                _, buffer = cv2.imencode('.jpg', display_frame, encode_param)
                
                # 2. Write to a unique temporary file so Windows doesn't lock it
                temp_filename = f"temp_frame_{NODE_ID}_{int(current_sys_time*1000)}.jpg"
                with open(temp_filename, "wb") as f:
                    f.write(buffer)
                
                # 3. Atomically replace the file the API is looking for
                os.replace(temp_filename, f"latest_frame_{NODE_ID}.jpg")
            except Exception:
                pass # If Windows locks it, just skip rendering this specific frame!
            
            last_frame_write = current_sys_time

        if not os.environ.get("HEADLESS_MODE"):
            cv2.imshow(window_name, display_frame)
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