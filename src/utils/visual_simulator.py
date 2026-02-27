# src/utils/visual_simulator.py
import cv2
import numpy as np
import random
import time
from datetime import datetime
import sqlite3
import paho.mqtt.client as mqtt
import yaml
import json
from src.database.db import init_db
from src.utils.logger import setup_logger

# -------------------------------------------------
# ⚙️ CONFIGURATION & SETUP
# -------------------------------------------------
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

logger = setup_logger("VisualSimulator")
init_db()

# Connect to MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.connect(config["mqtt"]["broker"], config["mqtt"]["port"], 60)
    mqtt_client.loop_start()
except Exception as e:
    logger.error(f"MQTT Error: {e}")

# Simulator Settings
WIDTH, HEIGHT = 800, 600
ROAD_X1, ROAD_X2 = 250, 550
LINE_1_Y, LINE_2_Y = 200, 400

# -------------------------------------------------
# 🚗 VEHICLE CLASS
# -------------------------------------------------
class SimVehicle:
    def __init__(self, id_num):
        self.id = id_num
        self.x = random.randint(ROAD_X1 + 20, ROAD_X2 - 40)
        self.y = -50
        self.speed_kmh = random.randint(20, 110)
        # Map km/h to pixel movement per frame (rough estimation)
        self.vy = self.speed_kmh / 10.0 
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.crossed_line = False
        self.violated = False

# -------------------------------------------------
# 🎮 MAIN VISUAL LOOP
# -------------------------------------------------
def run_visual_simulator():
    logger.info("🎬 Starting Visual 2D Traffic Simulator...")
    
    cv2.namedWindow("Capgemini Digital Twin", cv2.WINDOW_NORMAL)
    
    vehicles = []
    vehicle_counter = 1000
    
    light_state = "GREEN"
    last_light_change = time.time()
    last_db_update = time.time()
    
    # Generate background once
    bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    bg[:] = (30, 30, 30) # Dark gray background
    cv2.rectangle(bg, (ROAD_X1, 0), (ROAD_X2, HEIGHT), (60, 60, 60), -1) # Road
    cv2.line(bg, (ROAD_X1, LINE_1_Y), (ROAD_X2, LINE_1_Y), (255, 0, 0), 2) # Speed Trap Start
    cv2.line(bg, (ROAD_X1, LINE_2_Y), (ROAD_X2, LINE_2_Y), (0, 0, 255), 3) # Red Light Line
    
    while True:
        frame = bg.copy()
        current_time = time.time()
        
        # 1. Traffic Light Logic
        if light_state == "GREEN" and current_time - last_light_change > 5:
            light_state = "YELLOW"
            last_light_change = current_time
        elif light_state == "YELLOW" and current_time - last_light_change > 2:
            light_state = "RED"
            last_light_change = current_time
        elif light_state == "RED" and current_time - last_light_change > 5:
            light_state = "GREEN"
            last_light_change = current_time
            
        # Draw Traffic Light
        color_map = {"RED": (0, 0, 255), "YELLOW": (0, 255, 255), "GREEN": (0, 255, 0)}
        cv2.circle(frame, (WIDTH - 100, 100), 30, color_map[light_state], -1)
        cv2.putText(frame, light_state, (WIDTH - 140, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, color_map[light_state], 2)

        # 2. Spawn Vehicles randomly
        spawn_rate = 0.05 if light_state == "GREEN" else 0.01 # Less cars spawn on red
        if random.random() < spawn_rate:
            vehicle_counter += 1
            vehicles.append(SimVehicle(vehicle_counter))

        # 3. Update & Draw Vehicles
        active_cars = 0
        total_speed = 0
        
        for v in vehicles:
            v.y += v.vy
            active_cars += 1
            total_speed += v.speed_kmh
            
            # Draw Car
            cv2.rectangle(frame, (int(v.x), int(v.y)), (int(v.x) + 30, int(v.y) + 50), v.color, -1)
            cv2.putText(frame, f"{v.speed_kmh}km/h", (int(v.x)-10, int(v.y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

            # Check Violations at Line 2
            if v.y > LINE_2_Y and not v.crossed_line:
                v.crossed_line = True
                
                is_red = (light_state == "RED")
                is_speeding = (v.speed_kmh > config["speed_estimation"]["speed_limit_kmh"])
                
                if is_red or is_speeding:
                    v.violated = True
                    v_type = "BOTH" if (is_red and is_speeding) else ("RED_LIGHT" if is_red else "SPEED")
                    fine = 60 if v_type == "RED_LIGHT" else min(200, int((v.speed_kmh - 50) * 2))
                    if v_type == "BOTH": fine += 60
                    
                    # Flash the screen for evidence!
                    cv2.rectangle(frame, (0,0), (WIDTH, HEIGHT), (255,255,255), 5)
                    cv2.putText(frame, "📸 SNAPSHOT TAKEN", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
                    
                    # Insert to DB
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    fake_plate = f"{random.randint(100, 999)} TU {random.randint(1000, 9999)}"
                    
                    conn = sqlite3.connect("traffic_system.db")
                    conn.cursor().execute("""
                        INSERT INTO violations (timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, v.id, fake_plate, "simulated_image.jpg", light_state, v_type, v.speed_kmh, fine))
                    conn.commit()
                    conn.close()
                    
                    # Send MQTT
                    payload = {"event": "VIOLATION_SIMULATED", "vehicle_id": v.id, "fine_amount": fine}
                    mqtt_client.publish(config["mqtt"]["topic_violation"], json.dumps(payload))
                    logger.warning(f"🚨 Violation ID {v.id} | {v_type} | {v.speed_kmh}km/h")

            # Keep violated cars highlighted in Red
            if v.violated:
                cv2.rectangle(frame, (int(v.x)-2, int(v.y)-2), (int(v.x) + 32, int(v.y) + 52), (0,0,255), 2)

        # 4. Update Congestion Metrics every 3 seconds
        if current_time - last_db_update > 3:
            avg_speed = total_speed / active_cars if active_cars > 0 else 0
            congestion = "HIGH" if active_cars > 8 else "MEDIUM" if active_cars > 4 else "LOW"
            
            conn = sqlite3.connect("traffic_system.db")
            conn.cursor().execute("""
                INSERT INTO traffic_metrics (timestamp, vehicle_count, avg_speed, congestion_level)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), active_cars, avg_speed, congestion))
            conn.commit()
            conn.close()
            
            last_db_update = current_time

        # Remove cars that drove off screen
        vehicles = [v for v in vehicles if v.y < HEIGHT + 100]

        # Render Data
        cv2.putText(frame, f"Active Cars: {active_cars}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        cv2.imshow("Capgemini Digital Twin", frame)
        if cv2.waitKey(30) & 0xFF == 27: # Press ESC to close
            break

    cv2.destroyAllWindows()
    logger.info("🛑 Visual Simulator Stopped.")

if __name__ == "__main__":
    run_visual_simulator()