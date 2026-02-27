# src/utils/ocr_worker.py
import threading
import queue
import easyocr
import json
from src.database.db import insert_violation
from src.utils.logger import setup_logger

logger = setup_logger("OCR_Worker")

class OCRBackgroundWorker:
    def __init__(self, mqtt_client, topic_violation):
        self.q = queue.Queue()
        self.mqtt_client = mqtt_client
        self.topic_violation = topic_violation
        
        logger.info("🔤 Initializing Background OCR Engine...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        logger.info("⚙️ Distributed Background OCR Worker is running.")

    def process_violation(self, node_id, image_path, track_id, timestamp, light_state, v_type, veh_speed, fine_amount):
        """Drops a violation job into the background queue with node identification."""
        self.q.put({
            "node_id": node_id,
            "image_path": image_path,
            "track_id": track_id,
            "timestamp": timestamp,
            "light_state": light_state,
            "v_type": v_type,
            "veh_speed": veh_speed,
            "fine_amount": fine_amount
        })

    def _process_queue(self):
        while True:
            job = self.q.get()
            
            try:
                plate_number = "UNKNOWN"
                result_ocr = self.reader.readtext(job["image_path"])
                if len(result_ocr) > 0:
                    plate_number = result_ocr[0][1]
                
                logger.info(f"🔍 [{job['node_id']}] OCR Detected Plate: {plate_number} (ID: {job['track_id']})")

                insert_violation(
                    node_id=job["node_id"],
                    timestamp=job["timestamp"], 
                    vehicle_id=job["track_id"], 
                    plate_number=plate_number, 
                    image_path=job["image_path"], 
                    light_state=job["light_state"], 
                    violation_type=job["v_type"], 
                    speed=job["veh_speed"], 
                    fine_amount=job["fine_amount"]
                )

                violation_payload = {
                    "event": "VIOLATION_TRIGGERED",
                    "node_id": job["node_id"],
                    "timestamp": job["timestamp"],
                    "vehicle_id": int(job["track_id"]),
                    "plate_number": plate_number,
                    "violation_type": job["v_type"],
                    "fine_amount": job["fine_amount"]
                }
                self.mqtt_client.publish(self.topic_violation, json.dumps(violation_payload))
                
            except Exception as e:
                logger.error(f"❌ Background Worker Error: {e}")
            finally:
                self.q.task_done()