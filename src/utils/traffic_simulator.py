# src/utils/traffic_simulator.py
import sqlite3
import random
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from src.utils.logger import setup_logger
from src.database.db import init_db  # 👈 NEW: Import the database initializer
import yaml

# Load Config
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

logger = setup_logger("TrafficSimulator")

# Connect to MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
try:
    mqtt_client.connect(config["mqtt"]["broker"], config["mqtt"]["port"], 60)
    mqtt_client.loop_start()
    logger.info("📡 Simulator connected to MQTT Broker")
except Exception as e:
    logger.error(f"Failed to connect to MQTT: {e}")

def connect_db():
    return sqlite3.connect("traffic_system.db", check_same_thread=False)

def simulate_traffic():
    logger.info("🗄️ Initializing database tables...")
    init_db()  # 👈 NEW: Actually create the tables before we start!
    
    logger.info("🚦 Starting Traffic Simulation... Press Ctrl+C to stop.")
    vehicle_id_counter = 1000

    while True:
        try:
            conn = connect_db()
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Simulate Normal Traffic Flow
            vehicle_count = random.randint(5, 45)  # 5 to 45 cars per interval
            avg_speed = round(random.uniform(15.0, 65.0), 2)
            
            # Determine congestion level
            if vehicle_count > 35 or avg_speed < 20:
                congestion = "CRITICAL"
            elif vehicle_count > 25:
                congestion = "HIGH"
            elif vehicle_count > 15:
                congestion = "MEDIUM"
            else:
                congestion = "LOW"

            # Insert Metrics
            cursor.execute("""
                INSERT INTO traffic_metrics (timestamp, vehicle_count, avg_speed, congestion_level)
                VALUES (?, ?, ?, ?)
            """, (timestamp, vehicle_count, avg_speed, congestion))
            
            logger.info(f"📊 Simulated Traffic: {vehicle_count} cars, Avg Speed: {avg_speed}km/h [{congestion}]")

            # 2. Simulate Random Violations (10% chance per loop)
            if random.random() < 0.10:
                vehicle_id_counter += 1
                veh_speed = round(random.uniform(70.0, 120.0), 2) # Speeding!
                v_type = random.choice(["SPEED", "RED_LIGHT", "BOTH"])
                
                fine_amount = 60 if v_type == "RED_LIGHT" else min(200, int((veh_speed - 50) * 2))
                if v_type == "BOTH": fine_amount += 60
                
                fake_plate = f"{random.randint(100, 999)} TU {random.randint(1000, 9999)}"

                cursor.execute("""
                    INSERT INTO violations (timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, vehicle_id_counter, fake_plate, "simulated_image.jpg", "RED", v_type, veh_speed, fine_amount))
                
                logger.warning(f"🚨 Simulated Violation! ID: {vehicle_id_counter} | Type: {v_type} | Fine: {fine_amount} TND")

                # Send MQTT Alert
                payload = {
                    "event": "VIOLATION_SIMULATED",
                    "timestamp": timestamp,
                    "vehicle_id": vehicle_id_counter,
                    "plate_number": fake_plate,
                    "violation_type": v_type,
                    "fine_amount": fine_amount
                }
                mqtt_client.publish(config["mqtt"]["topic_violation"], json.dumps(payload))

            conn.commit()
            conn.close()

            # Wait 5 seconds before the next simulation cycle
            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("🛑 Simulation Stopped.")
            break
        except Exception as e:
            logger.error(f"Simulation Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    simulate_traffic()