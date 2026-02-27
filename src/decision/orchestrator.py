# src/decision/orchestrator.py
import time
import json
import sqlite3
import os  
import paho.mqtt.client as mqtt
from datetime import datetime
from src.utils.logger import setup_logger
from src.database.db import get_connection

logger = setup_logger("Orchestrator")

class CentralOrchestrator:
    """Manages multi-node synchronization, V2X routing, and system health."""
    
    def __init__(self, port=1883):
        # 👇 THE FIX: Look for Docker network alias first, fallback to localhost
        self.broker = os.environ.get("MQTT_BROKER", "localhost")
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Central_Hub")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        logger.info(f"🌐 Orchestrator connected to MQTT Broker ({self.broker}:{self.port})")
        self.client.subscribe("smartcity/node/+/heartbeat")
        self.client.subscribe("smartcity/v2x/emergency")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode())

        if "heartbeat" in topic:
            self.handle_heartbeat(payload)
        elif "v2x/emergency" in topic:
            self.handle_v2x_emergency(payload)

    def handle_heartbeat(self, payload):
        """Updates the node registry database table."""
        try:
            conn = get_connection()
            conn.execute("""
                INSERT INTO nodes (node_id, status, last_heartbeat, cpu_load, ram_load) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET 
                status=excluded.status, last_heartbeat=excluded.last_heartbeat, 
                cpu_load=excluded.cpu_load, ram_load=excluded.ram_load
            """, (payload['node_id'], payload['status'], payload['timestamp'], 
                  payload['cpu'], payload['ram']))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"DB Error on heartbeat: {e}")

    def handle_v2x_emergency(self, payload):
        """Routes ambulance requests to the correct edge node."""
        node_id = payload.get("target_node")
        logger.warning(f"🚑 V2X Emergency mapped to {node_id}. Commanding Edge Override!")
        
        # Log to ledger
        conn = get_connection()
        conn.execute("""
            INSERT INTO v2x_ledger (node_id, timestamp, vehicle_type, priority_level, latency_ms, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (node_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "AMBULANCE", 1, payload.get("latency", 0), "GRANTED"))
        conn.commit()
        conn.close()

        # Command the specific node to turn Green
        command = {"action": "FORCE_GREEN", "duration": 15, "reason": "V2X_AMBULANCE"}
        self.client.publish(f"smartcity/node/{node_id}/command", json.dumps(command))

    def run(self):
        logger.info("🚀 Central Orchestrator Booting Up...")
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    hub = CentralOrchestrator()
    hub.run()