# src/decision/congestion.py
import sqlite3
import time
from datetime import datetime
import yaml
from src.utils.logger import setup_logger

logger = setup_logger()

class CongestionAnalyzer:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
            
        # Thresholds: Vehicles per minute
        self.low_threshold = 15
        self.med_threshold = 30
        self.high_threshold = 50
        
        self.db_path = self.config["system"]["db_path"]
        self.start_time = time.time()
        self.vehicle_count_interval = 0
        
        logger.info("📊 Congestion Analyzer Initialized.")

    def update_and_log(self, current_vehicle_total, current_avg_speed):
        """Calculates congestion every 60 seconds and logs it to the database."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # If a minute has passed, evaluate the congestion
        if elapsed >= 60.0:
            vehicles_this_minute = current_vehicle_total - self.vehicle_count_interval
            
            # Classification Logic
            if vehicles_this_minute < self.low_threshold:
                level = "LOW"
            elif vehicles_this_minute < self.med_threshold:
                level = "MEDIUM"
            elif vehicles_this_minute < self.high_threshold:
                level = "HIGH"
            else:
                level = "CRITICAL"
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save to Database
            self._save_to_db(timestamp, level, vehicles_this_minute, current_avg_speed)
            logger.info(f"🚦 Congestion Update: {level} ({vehicles_this_minute} vehicles/min)")
            
            # Reset interval timer and count
            self.start_time = current_time
            self.vehicle_count_interval = current_vehicle_total
            
            return level
        return None

    def _save_to_db(self, timestamp, level, count, avg_speed):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO traffic_metrics (timestamp, congestion_level, vehicle_count, average_speed)
            VALUES (?, ?, ?, ?)
            """, (timestamp, level, count, avg_speed or 0.0))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save traffic metrics: {e}")