# src/utils/v2x_simulator.py
import time
import json
import random
import os
import paho.mqtt.client as mqtt
from src.utils.logger import setup_logger

logger = setup_logger("V2X_Simulator")

# 👇 THE FIX: Automatically detect the Docker network if inside a container
BROKER = os.environ.get("MQTT_BROKER", "localhost")
PORT = 1883
TOPIC = "smartcity/v2x/emergency"

def run_simulation():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Ambulance_Sim")
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start() 
        logger.info(f"🚑 V2X Simulator Active. Connected to Broker ({BROKER})...")
        
        for i in range(3):
            latency = random.randint(10, 150)
            payload = {
                "vehicle_id": f"AMB-{random.randint(100,999)}",
                "target_node": "NODE_A",
                "priority": 1,
                "latency": latency,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"📡 Broadcasting V2X Emergency to NODE_A (Ping: {latency}ms)")
            client.publish(TOPIC, json.dumps(payload))
            time.sleep(3) 
            
        time.sleep(1) 
        client.loop_stop()
        client.disconnect()
        logger.info("✅ V2X Simulation Complete.")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to broker: {e}")

if __name__ == "__main__":
    run_simulation()