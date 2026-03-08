# src/api/main.py
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
import sqlite3
import joblib
import os
import time
import json
import random
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

try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    print("✅ MQTT Connection established for Emergency Overrides.")
except Exception as e:
    print(f"⚠️ MQTT Broker Offline. Error: {e}")
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except:
        pass

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
# 🌱 ENTERPRISE DATABASE AUTO-SEEDING (Runs on Startup)
# ---------------------------------------------------------
@app.on_event("startup")
def startup_event():
    init_db()  # Guarantee the tables exist
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Check exactly how many violations are currently in the database
    try:
        cursor.execute("SELECT COUNT(*) FROM violations")
        count = cursor.fetchone()[0]
    except Exception:
        count = 0
    
    # 2. If the database is completely empty, auto-generate a random dynamic amount!
    if count == 0:
        # Generate a random dynamic number between 45 and 150
        num_records = random.randint(45, 150)
        print(f"🌱 Database is empty. Auto-seeding with {num_records} dynamic records...")
        
        plates = ["1234 TUN 200", "8475 TUN 195", "UNKNOWN", "9921 TUN 210", "1122 TUN 180", "5544 TUN 220", "UNKNOWN"]
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
            
            # Cloudinary URL format mapping
            img = f"https://res.cloudinary.com/dh5f789pm/image/upload/v1772816251/capgemini_smart_city/violations/{node}_{i}_0.jpg"
            
            cursor.execute("""
                INSERT INTO violations (node_id, timestamp, vehicle_id, plate_number, image_path, light_state, violation_type, speed, fine_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (node, v_time.strftime("%Y-%m-%d %H:%M:%S"), i, plate, img, "RED" if "RED" in v_type else "GREEN", v_type, round(speed, 1), fine))
        
        conn.commit()
        print(f"✅ Successfully auto-injected {num_records} dynamic records!")
    else:
        print(f"✅ Database already contains {count} real violations. Skipping auto-seed.")
        
    conn.close()

# ---------------------------------------------------------
# 📹 HIGH-PERFORMANCE VIDEO STREAMING
# ---------------------------------------------------------
def frame_generator(node_id: str):
    file_path = f"latest_frame_{node_id}.jpg"
    while True:
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')
            except Exception:
                pass
        time.sleep(0.04) 

@app.get("/api/video_feed/{node_id}")
def video_feed(node_id: str):
    return StreamingResponse(
        frame_generator(node_id), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

# ---------------------------------------------------------
# 🚨 EMERGENCY RESPONSE API
# ---------------------------------------------------------
@app.post("/api/command")
async def send_emergency_command(payload: dict = Body(...)):
    action = payload.get("action")
    node_id = payload.get("node_id", "NODE_A")
    
    if action == "FORCE_GREEN":
        command = json.dumps({"action": "FORCE_GREEN", "duration": 15, "priority": "CRITICAL"})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        print(f"🚨 EMERGENCY: Force Green issued for {node_id}")
        return {"status": "SUCCESS", "message": f"Emergency Green signal sent to {node_id}"}
        
    elif action == "RESTART_VIDEO":
        command = json.dumps({"action": "RESTART_VIDEO", "priority": "NORMAL"})
        mqtt_client.publish(f"smartcity/node/{node_id}/command", command)
        print(f"🔄 COMMAND: Restart video issued for {node_id}")
        return {"status": "SUCCESS", "message": f"Restart command sent to {node_id}"}
    
    raise HTTPException(status_code=400, detail="Invalid command.")

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

# ---------------------------------------------------------
# 📊 ANALYTICS & MONITORING (WITH TIMEFRAME FILTERS)
# ---------------------------------------------------------
@app.get("/api/violations")
def get_recent_violations(limit: int = 100, node_id: Optional[str] = None, timeframe: Optional[str] = "all"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start building the SQL query dynamically
        query = "SELECT * FROM violations WHERE 1=1"
        params = []
        
        # 1. Filter by Node
        if node_id and node_id != "ALL":
            query += " AND node_id=?"
            params.append(node_id)
            
        # 2. Filter by Timeframe (Daily, Weekly, Monthly)
        if timeframe == "daily":
            query += " AND timestamp >= datetime('now', '-1 day')"
        elif timeframe == "weekly":
            query += " AND timestamp >= datetime('now', '-7 days')"
        elif timeframe == "monthly":
            query += " AND timestamp >= datetime('now', '-30 days')"
            
        # Finish the query with limits
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
        v_count, row["vehicle_count"]
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
# 📄 LEGACY EXPORT ENDPOINTS (Retained for backward compatibility)
# ---------------------------------------------------------
@app.get("/api/export/excel")
def export_excel(timeframe: str = "daily"):
    """Generates an Excel file of the database logs."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT timestamp, plate_number, violation_type, speed, fine_amount, image_path FROM violations ORDER BY timestamp DESC", conn)
        conn.close()
        
        file_path = "Capgemini_Smart_City_Report.xlsx"
        df.to_excel(file_path, index=False, sheet_name="Violations")
        
        return FileResponse(file_path, filename="Capgemini_Report.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/pdf")
def export_pdf(timeframe: str = "daily"):
    """Generates a formatted PDF report of recent violations."""
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