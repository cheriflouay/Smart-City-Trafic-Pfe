# src/utils/visual_simulator_3d.py
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

logger = setup_logger("VisualSimulator3D")
init_db()

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.connect(config["mqtt"]["broker"], config["mqtt"]["port"], 60)
    mqtt_client.loop_start()
except Exception as e:
    logger.error(f"MQTT Error: {e}")

# 3D Perspective Settings
WIDTH, HEIGHT = 1200, 720
HORIZON_Y = 280
CENTER_X = WIDTH // 2

# -------------------------------------------------
# 🎨 PROCEDURAL BACKGROUND GENERATOR (RUNS ONCE)
# -------------------------------------------------
def generate_environment():
    """Generates the gradient sky, stars, grass, and perspective road so we don't lag the main loop."""
    bg = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    # 1. Gradient Night Sky
    for y in range(HORIZON_Y):
        ratio = y / HORIZON_Y
        r = int(10 * (1 - ratio) + 120 * ratio)  # Dark blue to faint orange horizon
        g = int(15 * (1 - ratio) + 100 * ratio)
        b = int(30 * (1 - ratio) + 80 * ratio)
        cv2.line(bg, (0, y), (WIDTH, y), (b, g, r), 1)

    # 2. Starfield
    for _ in range(250):
        sx, sy = random.randint(0, WIDTH), random.randint(0, HORIZON_Y - 30)
        brightness = random.randint(100, 255)
        cv2.circle(bg, (sx, sy), random.choice([1, 1, 2]), (brightness, brightness, brightness), -1)

    # 3. Grass / Ground
    cv2.rectangle(bg, (0, HORIZON_Y), (WIDTH, HEIGHT), (25, 35, 20), -1)
    
    # 4. The 3D Road
    road_pts = np.array([
        [CENTER_X - 60, HORIZON_Y], [CENTER_X + 60, HORIZON_Y], 
        [WIDTH - 150, HEIGHT], [150, HEIGHT]
    ], np.int32)
    cv2.fillPoly(bg, [road_pts], (65, 65, 70)) # Asphalt Gray

    # 5. Dashed Lane Lines (Perspective Math)
    lanes = [-0.5, 0.5] # Divider lines
    for lane in lanes:
        for i in range(10):
            # Calculate depth for dashed lines
            y1 = HORIZON_Y + (i * 45) + (i**2 * 1.5)
            y2 = y1 + 20 + (i * 2)
            if y2 > HEIGHT: break
            
            spread1 = (y1 - HORIZON_Y) * 1.5
            spread2 = (y2 - HORIZON_Y) * 1.5
            
            x1 = int(CENTER_X + (lane * spread1))
            x2 = int(CENTER_X + (lane * spread2))
            
            thickness = max(1, int((y1 - HORIZON_Y) / 50))
            cv2.line(bg, (x1, int(y1)), (x2, int(y2)), (200, 200, 200), thickness)

    # 6. City Lights at Horizon
    for _ in range(15):
        cx = random.randint(CENTER_X - 200, CENTER_X + 200)
        ch = random.randint(2, 10)
        cv2.rectangle(bg, (cx, HORIZON_Y - ch), (cx + random.randint(5, 15), HORIZON_Y), (150, 200, 220), -1)

    return bg

# -------------------------------------------------
# 🚗 3D VEHICLE CLASS (DETAILED)
# -------------------------------------------------
class SimVehicle3D:
    def __init__(self, id_num):
        self.id = id_num
        self.lane = random.choice([-1.0, -0.33, 0.33, 1.0])  # 4 explicit lanes
        self.y = HORIZON_Y + 5
        self.speed_kmh = random.randint(30, 110)
        # Metallic car colors
        self.color = random.choice([(180,180,180), (50,50,200), (200,50,50), (30,30,30), (200,200,50)])
        self.crossed_line = False
        self.violated = False

    def update(self):
        depth_scale = (self.y - HORIZON_Y + 10) / 100.0
        self.y += (self.speed_kmh / 25.0) * depth_scale
        spread = (self.y - HORIZON_Y) * 1.35
        self.x = CENTER_X + (self.lane * spread)

    def draw(self, frame):
        scale = max(0.05, (self.y - HORIZON_Y) / (HEIGHT - HORIZON_Y))
        w = int(140 * scale)
        h = int(70 * scale)
        x_int, y_int = int(self.x), int(self.y)

        # 1. Shadow underneath
        cv2.ellipse(frame, (x_int, y_int + int(h*0.4)), (int(w*0.6), int(h*0.3)), 0, 0, 360, (15, 15, 15), -1)

        # 2. Headlight Beams (Glowing on the road)
        if scale > 0.2:
            beam_w = int(w * 1.5)
            beam_h = int(h * 3.0)
            overlay = frame.copy()
            beam_pts = np.array([
                [x_int - w//3, y_int + h//4], [x_int + w//3, y_int + h//4],
                [x_int + beam_w, y_int + beam_h], [x_int - beam_w, y_int + beam_h]
            ], np.int32)
            cv2.fillPoly(overlay, [beam_pts], (180, 220, 220))
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame) # Soft alpha blend

        # 3. Car Body
        glow_color = (0, 0, 255) if self.violated else self.color
        
        # Chassis
        cv2.rectangle(frame, (x_int - w//2, y_int - h//2), (x_int + w//2, y_int + h//2), glow_color, -1)
        # Roof / Cabin
        roof_color = tuple(min(255, c + 30) for c in glow_color)
        cv2.rectangle(frame, (x_int - w//3, y_int - h//2 + 2), (x_int + w//3, y_int), roof_color, -1)
        # Rear Windshield
        cv2.rectangle(frame, (x_int - w//3 + 4, y_int - h//2 + 4), (x_int + w//3 - 4, y_int - h//4), (30, 30, 30), -1)

        # 4. Lights
        if scale > 0.1:
            hl_r = max(2, int(10 * scale))
            # Taillights (Red)
            cv2.circle(frame, (x_int - w//2 + 5, y_int - h//2 + 5), hl_r, (50, 50, 255), -1)
            cv2.circle(frame, (x_int + w//2 - 5, y_int - h//2 + 5), hl_r, (50, 50, 255), -1)
            # Headlights (Bright Yellow/White)
            cv2.circle(frame, (x_int - w//2 + 5, y_int + h//2 - 5), hl_r, (200, 255, 255), -1)
            cv2.circle(frame, (x_int + w//2 - 5, y_int + h//2 - 5), hl_r, (200, 255, 255), -1)

# -------------------------------------------------
# 🎮 MAIN VISUAL LOOP
# -------------------------------------------------
def run_visual_simulator():
    logger.info("🎬 Starting Ultra 3D Digital Twin Simulation...")
    cv2.namedWindow("Capgemini Digital Twin (Edge AI)", cv2.WINDOW_NORMAL)
    
    # Pre-render the heavy background to save CPU!
    STATIC_BG = generate_environment()
    
    vehicles = []
    vehicle_counter = 1000
    light_state = "GREEN"
    last_light_change = time.time()
    last_db_update = time.time()
    
    # Red Light Line math
    stop_y = int(HEIGHT * 0.85)
    stop_w = int((stop_y - HORIZON_Y) * 1.6)

    while True:
        # Load the pre-rendered starry night and road
        frame = STATIC_BG.copy()
        current_time = time.time()
        
        # --- TRAFFIC LIGHT LOGIC ---
        if light_state == "GREEN" and current_time - last_light_change > 6:
            light_state = "YELLOW"
            last_light_change = current_time
        elif light_state == "YELLOW" and current_time - last_light_change > 2:
            light_state = "RED"
            last_light_change = current_time
        elif light_state == "RED" and current_time - last_light_change > 5:
            light_state = "GREEN"
            last_light_change = current_time
            
        # Draw Stop Line
        line_color = (0, 0, 255) if light_state == "RED" else (0, 200, 0)
        cv2.line(frame, (CENTER_X - stop_w, stop_y), (CENTER_X + stop_w, stop_y), line_color, 4)

        # Draw 3D Traffic Light Pole
        pole_x = WIDTH - 200
        cv2.rectangle(frame, (pole_x-6, HORIZON_Y), (pole_x+6, HEIGHT), (40,40,45), -1) 
        # Light Box with gradient border
        cv2.rectangle(frame, (pole_x-30, HORIZON_Y-160), (pole_x+30, HORIZON_Y), (50,50,50), 4)
        cv2.rectangle(frame, (pole_x-30, HORIZON_Y-160), (pole_x+30, HORIZON_Y), (15,15,15), -1)
        
        # Traffic Light Glows
        color_map = {"RED": (0, 0, 255), "YELLOW": (0, 255, 255), "GREEN": (0, 255, 0)}
        dim_colors = {"RED": (0, 0, 40), "YELLOW": (0, 60, 60), "GREEN": (0, 40, 0)}
        
        cv2.circle(frame, (pole_x, HORIZON_Y-130), 20, color_map["RED"] if light_state=="RED" else dim_colors["RED"], -1)
        cv2.circle(frame, (pole_x, HORIZON_Y-80), 20, color_map["YELLOW"] if light_state=="YELLOW" else dim_colors["YELLOW"], -1)
        cv2.circle(frame, (pole_x, HORIZON_Y-30), 20, color_map["GREEN"] if light_state=="GREEN" else dim_colors["GREEN"], -1)

        # --- VEHICLE LOGIC ---
        spawn_rate = 0.08 if light_state == "GREEN" else 0.01 
        if random.random() < spawn_rate:
            vehicle_counter += 1
            vehicles.append(SimVehicle3D(vehicle_counter))

        active_cars = 0
        total_speed = 0
        
        # Sort so cars closest to camera draw last (on top)
        vehicles.sort(key=lambda v: v.y)
        
        for v in vehicles:
            v.update()
            v.draw(frame)
            active_cars += 1
            total_speed += v.speed_kmh

            # Check Violations
            if v.y > stop_y and not v.crossed_line:
                v.crossed_line = True
                
                is_red = (light_state == "RED")
                is_speeding = (v.speed_kmh > config["speed_estimation"]["speed_limit_kmh"])
                
                if is_red or is_speeding:
                    v.violated = True
                    v_type = "BOTH" if (is_red and is_speeding) else ("RED_LIGHT" if is_red else "SPEED")
                    fine = 60 if v_type == "RED_LIGHT" else min(200, int((v.speed_kmh - 50) * 2))
                    if v_type == "BOTH": fine += 60
                    
                    # 📸 FLASH
                    cv2.rectangle(frame, (0,0), (WIDTH, HEIGHT), (255,255,255), 15)
                    cv2.putText(frame, "📸 ALPR CAPTURE", (WIDTH//2 - 180, HEIGHT//2), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0,0,255), 3)
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    fake_plate = f"{random.randint(10, 999)} TU {random.randint(1000, 9999)}"
                    
                    conn = sqlite3.connect("traffic_system.db")
                    conn.cursor().execute("""
                        INSERT INTO violations (timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, v.id, fake_plate, "simulated_image.jpg", light_state, v_type, v.speed_kmh, fine))
                    conn.commit()
                    conn.close()
                    
                    payload = {"event": "VIOLATION_SIMULATED", "vehicle_id": v.id, "fine_amount": fine}
                    mqtt_client.publish(config["mqtt"]["topic_violation"], json.dumps(payload))

        # --- DB UPDATE ---
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

        vehicles = [v for v in vehicles if v.y < HEIGHT + 200]

        # HUD Overlay
        cv2.putText(frame, f"Capgemini Edge Digital Twin | FPS: 30+", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Active Tracking: {active_cars} vehicles", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imshow("Capgemini Digital Twin (Edge AI)", frame)
        if cv2.waitKey(30) & 0xFF == 27: 
            break

    cv2.destroyAllWindows()
    logger.info("🛑 3D Simulator Stopped.")

if __name__ == "__main__":
    run_visual_simulator()