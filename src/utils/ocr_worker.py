# src/utils/ocr_worker.py
import threading
import queue
import easyocr
import json
import os
import cloudinary
import cloudinary.uploader
from src.database.db import get_connection
from src.utils.logger import setup_logger

# 👇 NEW: Import the email engine
from src.utils.email_notifier import send_violation_alert

logger = setup_logger("OCR_Worker")

# ☁️ CLOUDINARY CONFIGURATION (Your Live Credentials)
cloudinary.config( 
  cloud_name = "dh5f789pm", 
  api_key = "585433932373449", 
  api_secret = "EXmPRhHwoPJmbIdESyQfpFcU1qE",
  secure = True
)

class OCRBackgroundWorker:
    def __init__(self, mqtt_client, topic_violation):
        self.q = queue.Queue()
        self.mqtt_client = mqtt_client
        self.topic_violation = topic_violation
        
        logger.info("🔤 Initializing Background OCR Engine...")
        self.reader = easyocr.Reader(['en'], gpu=False)
        
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        logger.info("⚙️ Distributed Background OCR & Cloud Worker is running.")

    def process_violation(self, node_id, image_path, track_id, timestamp, light_state, v_type, veh_speed, fine_amount):
        """Drops a violation job into the background queue."""
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
                # 1. READ LICENSE PLATE
                plate_number = "UNKNOWN"
                result_ocr = self.reader.readtext(job["image_path"])
                if len(result_ocr) > 0:
                    plate_number = result_ocr[0][1]
                
                logger.info(f"🔍 [{job['node_id']}] OCR Detected Plate: {plate_number} (ID: {job['track_id']})")

                # 2. UPLOAD TO CLOUDINARY
                logger.info(f"☁️ Uploading ID {job['track_id']} to Cloudinary...")
                final_image_url = job['image_path']
                
                try:
                    upload_result = cloudinary.uploader.upload(
                        job["image_path"],
                        folder="capgemini_smart_city/violations",
                        public_id=f"{job['node_id']}_{job['track_id']}_{int(job['veh_speed'] if job['veh_speed'] else 0)}"
                    )
                    final_image_url = upload_result.get("secure_url")
                    logger.info(f"✅ Cloud Upload Success: {final_image_url}")
                    
                    try: os.remove(job["image_path"])
                    except: pass
                except Exception as e:
                    logger.error(f"❌ Cloudinary Upload Failed: {e}")

                # 3. SAVE TO DATABASE
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO violations 
                    (node_id, timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job["node_id"], job["timestamp"], job["track_id"], plate_number, 
                    final_image_url,
                    job["light_state"], job["v_type"], job["veh_speed"], job["fine_amount"]
                ))
                conn.commit()
                conn.close()

                # 👇 NEW: 4. SEND AUTOMATED EMAIL ALERT
                # We spin this up in a tiny separate thread so the OCR worker doesn't wait for the email to send!
                threading.Thread(target=send_violation_alert, args=(
                    job["node_id"], plate_number, job["v_type"], job["veh_speed"], job["fine_amount"], final_image_url
                ), daemon=True).start()

                # 5. BROADCAST TO MQTT
                violation_payload = {
                    "event": "VIOLATION_TRIGGERED",
                    "node_id": job["node_id"],
                    "timestamp": job["timestamp"],
                    "vehicle_id": int(job["track_id"]),
                    "plate_number": plate_number,
                    "violation_type": job["v_type"],
                    "fine_amount": job["fine_amount"],
                    "image_url": final_image_url
                }
                self.mqtt_client.publish(self.topic_violation, json.dumps(violation_payload))
                
            except Exception as e:
                logger.error(f"❌ Background Worker Error: {e}")
            finally:
                self.q.task_done()