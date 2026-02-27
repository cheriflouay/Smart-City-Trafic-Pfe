# src/decision/emergency_logic.py
import paho.mqtt.client as mqtt
import yaml
from src.utils.logger import setup_logger

logger = setup_logger()

class EmergencyOverride:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
            
        self.is_emergency_active = False
        
        # Setup specific MQTT client for emergency channel
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_message = self.on_message
        self.client.connect(self.config["mqtt"]["broker"], self.config["mqtt"]["port"], 60)
        self.client.subscribe("traffic/emergency")
        self.client.loop_start()
        
        logger.info("🚑 Emergency IoT V2I Listener Activated.")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        if payload == "EMERGENCY_APPROACHING":
            self.is_emergency_active = True
            logger.critical("🚨 EMERGENCY VEHICLE DETECTED VIA IoT! Overriding traffic light to GREEN.")
        elif payload == "EMERGENCY_CLEARED":
            self.is_emergency_active = False
            logger.info("✅ Emergency cleared. Returning to normal adaptive cycle.")

    def check_override(self):
        """Returns True if the light must be forced GREEN."""
        return self.is_emergency_active