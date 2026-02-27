# src/api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse # 👈 NEW: Required for video streaming
import sqlite3
import joblib
import os
import time # 👈 NEW: Required for the frame generator
from datetime import datetime
from typing import Optional

app = FastAPI(title="Capgemini Distributed Smart City API", version="2.0")

ml_model = None
MODEL_PATH = "models/congestion_model.pkl" # Fallback if hybrid isn't trained yet
if os.path.exists(MODEL_PATH):
    ml_model = joblib.load(MODEL_PATH)

def get_db_connection():
    # Force FastAPI to look in the exact root folder where the data is
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "traffic_system.db")
    
    # Fallback just in case
    if not os.path.exists(db_path):
        db_path = "traffic_system.db" 
        
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn

# 👇 NEW: Optimized Video Streaming Generator
def frame_generator(node_id):
    """Reads the latest saved frame from the edge node and yields it as a continuous MJPEG stream."""
    file_path = f"latest_frame_{node_id}.jpg"
    while True:
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
                # Yield the frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')
            except Exception:
                pass # Ignore if file is locked
        
        # 👇 THE FIX: Increased sleep to 0.1s (10 FPS limit). This stops Windows I/O crashing!
        time.sleep(0.1)

# 👇 NEW: The Video API Endpoint
@app.get("/api/video_feed/{node_id}")
def video_feed(node_id: str):
    """Streams the live AI vision feed from the Edge Node."""
    return StreamingResponse(frame_generator(node_id), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/nodes")
def get_active_nodes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodes ORDER BY last_heartbeat DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/stats/revenue")
def get_revenue_stats(node_id: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if node_id and node_id != "ALL":
        cursor.execute("SELECT SUM(fine_amount) as total_revenue, COUNT(id) as total_tickets FROM violations WHERE node_id=?", (node_id,))
    else:
        cursor.execute("SELECT SUM(fine_amount) as total_revenue, COUNT(id) as total_tickets FROM violations")
        
    row = cursor.fetchone()
    conn.close()
    return {
        "total_revenue": row["total_revenue"] if row["total_revenue"] else 0,
        "total_tickets": row["total_tickets"] if row["total_tickets"] else 0
    }

@app.get("/api/violations")
def get_recent_violations(limit: int = 100, node_id: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if node_id and node_id != "ALL":
        cursor.execute("SELECT * FROM violations WHERE node_id=? ORDER BY timestamp DESC LIMIT ?", (node_id, limit))
    else:
        cursor.execute("SELECT * FROM violations ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
        v_count, a_speed = row["vehicle_count"], row["avg_speed"]
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
            
    return {"forecast": "UNKNOWN", "status": "No data available."}