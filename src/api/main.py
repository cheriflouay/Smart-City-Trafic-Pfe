# src/api/main.py
from fastapi import FastAPI, HTTPException, Query, Body, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
import sqlite3
import joblib
import os
import time
import json
import random
import cv2
import subprocess
import sys
import psutil 
import numpy as np 
from datetime import datetime, timedelta
from typing import Optional
import paho.mqtt.client as mqtt
import pandas as pd
from fpdf import FPDF

# Import your database initializer
from src.database.db import init_db

app = FastAPI(
    title="Capgemini Distributed Smart City ADAS API", 
    version="3.0.0",
    description="Professional backend for real-time traffic violation monitoring and emergency response."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ☁️ THE FREE "CLOUD": This tells FastAPI to host your images on port 8000
os.makedirs("violations", exist_ok=True)
app.mount("/violations", StaticFiles(directory="violations"), name="violations")

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

# ---------------------------------------------------------
# 📡 MQTT LISTENER & TELEMETRY CACHE
# ---------------------------------------------------------
node_telemetry = {} 

def on_mqtt_message(client, userdata, msg):
    try:
        topic = msg.topic
        if "heartbeat" in topic:
            payload = json.loads(msg.payload.decode())
            node_id = payload.get("node_id")
            if node_id:
                node_telemetry[node_id] = payload 
    except Exception as e: 
        pass

try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_message = on_mqtt_message 
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe("smartcity/node/+/heartbeat") 
    mqtt_client.loop_start()
    print("✅ MQTT Connection established for Emergency & Telemetry.")
except Exception as e:
    print(f"⚠️ MQTT Broker Offline. Error: {e}")
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.subscribe("smartcity/node/+/heartbeat")
        mqtt_client.loop_start()
    except:
        pass

@app.get("/api/telemetry/{node_id}")
def get_telemetry(node_id: str):
    return JSONResponse(content=node_telemetry.get(node_id, {
        "status": "OFFLINE", "fps": 0, "inference_ms": 0, "cpu": 0, "ram": 0
    }))

ml_model = None
MODEL_PATH = "models/congestion_model.pkl" 
if os.path.exists(MODEL_PATH):
    ml_model = joblib.load(MODEL_PATH)
    print("🧠 AI Congestion Model Loaded Successfully.")

def get_db_connection():
    db_path = os.path.abspath("data/traffic_system.db")
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------------------------------
# 🌱 ENTERPRISE DATABASE AUTO-SEEDING & UPGRADE
# ---------------------------------------------------------
@app.on_event("startup")
def startup_event():
    init_db()  
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 👇 NEW: Automatically upgrade DB schema to support OCR HITL Workflow
    try:
        cursor.execute("ALTER TABLE violations ADD COLUMN ocr_status TEXT DEFAULT 'AUTO_APPROVED'")
        conn.commit()
        print("✅ Database Schema Upgraded: Added 'ocr_status' column.")
    except sqlite3.OperationalError:
        pass # Column already exists, safe to ignore
    
    try:
        cursor.execute("SELECT COUNT(*) FROM violations")
        count = cursor.fetchone()[0]
    except Exception:
        count = 0
    
    if count == 0:
        num_records = random.randint(45, 150)
        print(f"🌱 Database is empty. Auto-seeding with {num_records} dynamic records...")
        
        plates = ["1234 TUN 200", "8475 TUN 195", "UNKNOWN", "9921 TUN 210", "1122 TUN 180", "5544 TUN 220", "??? TUN 11"]
        violation_types = ["RED_LIGHT", "SPEED", "BOTH", "WRONG_WAY"]
        nodes = ["NODE_A", "NODE_B"]
        now = datetime.now()
        
        for i in range(1, num_records + 1):
            random_days = random.randint(0, 7)
            random_mins = random.randint(0, 1440)
            v_time = now - timedelta(days=random_days, minutes=random_mins)
            
            node = random.choice(nodes)
            plate = random.choice(plates)
            v_type = random.choice(violation_types)
            speed = random.uniform(40.0, 95.0) if v_type in ["SPEED", "BOTH"] else random.uniform(10.0, 45.0)
            fine = 200.0 if v_type == "RED_LIGHT" else (150.0 if v_type == "SPEED" else 350.0)
            
            # 👇 NEW: Simulate real-world OCR confidence splits
            if plate == "UNKNOWN" or "???" in plate:
                ocr_status = random.choice(["NEEDS_JUNIOR", "ESCALATED_TO_SENIOR"])
            else:
                ocr_status = "AUTO_APPROVED"
            
            img = f"https://res.cloudinary.com/dh5f789pm/image/upload/v1772816251/capgemini_smart_city/violations/{node}_{i}_0.jpg"
            
            cursor.execute("""
                INSERT INTO violations (node_id, timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount, ocr_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (node, v_time.strftime("%Y-%m-%d %H:%M:%S"), i, plate, img, "RED" if "RED" in v_type else "GREEN", v_type, round(speed, 1), fine, ocr_status))
        
        conn.commit()
        print(f"✅ Successfully auto-injected {num_records} dynamic records!")
    else:
        print(f"✅ Database already contains {count} real violations. Skipping auto-seed.")
        
    conn.close()

# ---------------------------------------------------------
# 🎛️ DYNAMIC SIMULATION & MODEL BENCHMARKING
# ---------------------------------------------------------
@app.post("/api/upload_video")
async def upload_video(file: UploadFile = File(...)):
    await stop_simulation()
    time.sleep(0.5) 
    
    os.makedirs("data/videos", exist_ok=True)
    timestamp = int(time.time())
    file_path = f"data/videos/{timestamp}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    return {"status": "SUCCESS", "video_path": file_path, "filename": file.filename}

current_ai_process = None

@app.post("/api/stop_simulation")
async def stop_simulation():
    global current_ai_process
    
    if current_ai_process is not None:
        try: current_ai_process.terminate()
        except: pass
        current_ai_process = None

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline:
                cmd_str = " ".join(str(item) for item in cmdline if item)
                if 'vehicle_counting_smart_light' in cmd_str:
                    proc.kill()
                    print(f"🛑 Cleaned up ghost AI process (PID: {proc.info['pid']})")
        except Exception: 
            pass 

    try:
        standby = np.zeros((768, 1366, 3), dtype=np.uint8)
        cv2.putText(standby, "SIMULATION STOPPED", (350, 384), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,0,255), 3)
        cv2.imwrite("latest_frame_NODE_A.jpg", standby)
    except: pass

    if "NODE_A" in node_telemetry:
        node_telemetry["NODE_A"] = {"status": "OFFLINE", "fps": 0, "inference_ms": 0, "cpu": 0, "ram": 0}

    return {"status": "SUCCESS", "message": "Simulation halted."}

@app.post("/api/run_simulation")
async def run_simulation(
    video_path: str = Form(...), 
    model_choice: str = Form(...),
    node_id: str = Form("NODE_A")
):
    global current_ai_process
    
    await stop_simulation()
    
    model_map = {
        "YOLOv8_Nano": "models/yolov8n.onnx",
        "YOLOv8_Small": "models/yolov8s.onnx",
        "YOLOv8_Custom": "models/best.pt"
    }
    selected_model = model_map.get(model_choice, "models/yolov8n.onnx")

    cmd = [
        sys.executable, "-m", "src.analysis.vehicle_counting_smart_light", 
        "--node", node_id,
        "--video", video_path,
        "--model", selected_model
    ]
    
    current_ai_process = subprocess.Popen(cmd)
    print(f"🚀 Started NEW AI Simulation for {node_id} using {selected_model}")
    
    return {
        "status": "SUCCESS", 
        "message": f"Simulation started on {node_id}",
        "video_used": video_path,
        "model_used": selected_model
    }

# ---------------------------------------------------------
# 📹 HIGH-PERFORMANCE VIDEO STREAMING
# ---------------------------------------------------------
def frame_generator(node_id: str):
    if node_id == "NODE_A":
        file_path = f"latest_frame_{node_id}.jpg"
        while True:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        image_bytes = f.read()
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')
                except Exception:
                    pass
            time.sleep(0.04) 
    else:
        if node_id == "NODE_B": video_source = "data/videos/traffic1.mp4"
        else: video_source = "data/videos/traffic2.mp4"
        
        if not os.path.exists(video_source): video_source = "data/videos/traffic.mp4" 

        cap = cv2.VideoCapture(video_source)
        while True:
            success, frame = cap.read()
            if not success:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            
            cv2.putText(frame, f"CAM ID: {node_id} - LIVE", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)

            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)

@app.get("/api/video_feed/{node_id}")
def video_feed(node_id: str):
    return StreamingResponse(frame_generator(node_id), media_type="multipart/x-mixed-replace; boundary=frame")

# ---------------------------------------------------------
# 🚨 EMERGENCY RESPONSE & DYNAMIC CONTROL API
# ---------------------------------------------------------
@app.post("/api/command")
async def send_emergency_command(payload: dict = Body(...)):
    action = payload.get("action")
    node_id = payload.get("node_id", "NODE_A")
    
    if action == "FORCE_GREEN":
        command = json.dumps({"action": "FORCE_GREEN", "duration": 15, "priority": "CRITICAL"})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        return {"status": "SUCCESS"}
        
    elif action == "RESTART_VIDEO":
        command = json.dumps({"action": "RESTART_VIDEO", "priority": "NORMAL"})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        return {"status": "SUCCESS"}
        
    elif action == "SET_CONFIDENCE":
        val = payload.get("value", 0.15)
        command = json.dumps({"action": "SET_CONFIDENCE", "value": val})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        return {"status": "SUCCESS"}
        
    elif action == "SET_STOP_LINE":
        val = payload.get("value", 1600)
        command = json.dumps({"action": "SET_STOP_LINE", "value": int(val)})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        return {"status": "SUCCESS"}
    
    raise HTTPException(status_code=400, detail="Invalid command.")

# ---------------------------------------------------------
# 🧑‍⚖️ HUMAN-IN-THE-LOOP OCR REVIEW API (NEW)
# ---------------------------------------------------------
@app.get("/api/ocr/queue")
def get_ocr_queue():
    """Fetches all violations that need human review."""
    try:
        conn = get_db_connection()
        # Using rowid safely connects the frontend update logic to the correct DB row
        rows = conn.execute("SELECT rowid as db_id, * FROM violations WHERE ocr_status IN ('NEEDS_JUNIOR', 'ESCALATED_TO_SENIOR') ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        return []

@app.post("/api/ocr/review")
async def review_ocr(payload: dict = Body(...)):
    """Updates the plate and status after human verification."""
    db_id = payload.get("db_id")
    new_plate = payload.get("plate_number")
    new_status = payload.get("new_status") # 'VERIFIED', 'ESCALATED_TO_SENIOR', or 'DISMISSED'

    try:
        conn = get_db_connection()
        conn.execute("UPDATE violations SET plate_number=?, ocr_status=? WHERE rowid=?", (new_plate, new_status, db_id))
        conn.commit()
        conn.close()
        return {"status": "SUCCESS", "message": f"Record {db_id} updated to {new_status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 📊 ANALYTICS & MONITORING
# ---------------------------------------------------------
@app.get("/api/stats")
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM violations")
        total_violations = cursor.fetchone()[0]
        conn.close()
        return JSONResponse(content={"total_violations": total_violations})
    except Exception as e:
        return JSONResponse(content={"total_violations": 0, "error": str(e)})

@app.get("/api/violations")
def get_recent_violations(limit: int = 100, node_id: Optional[str] = None, timeframe: Optional[str] = "all"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM violations WHERE 1=1"
        params = []
        
        if node_id and node_id != "ALL":
            query += " AND node_id=?"
            params.append(node_id)
            
        if timeframe == "daily":
            query += " AND timestamp >= datetime('now', '-1 day')"
        elif timeframe == "weekly":
            query += " AND timestamp >= datetime('now', '-7 days')"
        elif timeframe == "monthly":
            query += " AND timestamp >= datetime('now', '-30 days')"
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching violations: {e}")
        return []

# ---------------------------------------------------------
# 🔮 AI PREDICTIONS
# ---------------------------------------------------------
@app.get("/api/predict/congestion")
def get_ai_forecast(node_id: Optional[str] = None):
    if not ml_model:
        return {"forecast": "MODEL_OFFLINE", "status": "No AI model found."}
        
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT vehicle_count, avg_speed FROM traffic_metrics "
    params = []
    if node_id and node_id != "ALL":
        query += "WHERE node_id=? "
        params.append(node_id)
    query += "ORDER BY timestamp DESC LIMIT 1"
    
    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        v_count = row["vehicle_count"]
        a_speed = row["avg_speed"]
        now = datetime.now()
        try:
            features = [[now.hour, now.minute, now.weekday(), v_count, a_speed]]
            prediction = ml_model.predict(features)[0]
            return {
                "forecast": prediction,
                "current_vehicles": v_count,
                "current_speed": round(a_speed, 2),
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    return {"forecast": "UNKNOWN", "status": "Insufficient data."}

# ---------------------------------------------------------
# 📄 LEGACY EXPORT ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/export/excel")
def export_excel(timeframe: str = "daily"):
    try:
        conn = get_db_connection()
        # 👇 NEW: Added ocr_status to Excel export!
        df = pd.read_sql_query("SELECT timestamp, plate_number, violation_type, speed, fine_amount, ocr_status, image_path FROM violations ORDER BY timestamp DESC", conn)
        conn.close()
        
        file_path = "Capgemini_Smart_City_Report.xlsx"
        df.to_excel(file_path, index=False, sheet_name="Violations")
        
        return FileResponse(file_path, filename="Capgemini_Report.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/pdf")
def export_pdf(timeframe: str = "daily"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, plate_number, violation_type, fine_amount FROM violations ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="CAPGEMINI - SMART CITY ADAS REPORT", ln=True, align='C')
        
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(50, 10, "Timestamp", border=1)
        pdf.cell(40, 10, "Plate", border=1)
        pdf.cell(50, 10, "Violation", border=1)
        pdf.cell(30, 10, "Fine (TND)", border=1, ln=True)

        pdf.set_font("Arial", size=10)
        for row in rows:
            pdf.cell(50, 10, str(row['timestamp']), border=1)
            pdf.cell(40, 10, str(row['plate_number']), border=1)
            pdf.cell(50, 10, str(row['violation_type']).replace('_', ' '), border=1)
            pdf.cell(30, 10, str(row['fine_amount']), border=1, ln=True)
            
        file_path = "Capgemini_Smart_City_Report.pdf"
        pdf.output(file_path)
        
        return FileResponse(file_path, filename="Capgemini_Report.pdf", media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)