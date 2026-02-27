# src/decision/anomaly_engine.py
import pandas as pd
from sklearn.ensemble import IsolationForest
from src.database.db import get_connection
from src.utils.logger import setup_logger

logger = setup_logger("AnomalyEngine")

def detect_traffic_anomalies():
    """Uses Unsupervised ML to detect weird traffic patterns across the city."""
    logger.info("🕵️‍♂️ Running Isolation Forest Anomaly Detection...")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, node_id, vehicle_count, avg_speed FROM traffic_metrics ORDER BY id DESC LIMIT 500", conn)
    conn.close()

    if len(df) < 50:
        logger.warning("Not enough data for anomaly detection.")
        return

    # Train Isolation Forest
    features = df[['vehicle_count', 'avg_speed']]
    model = IsolationForest(contamination=0.05, random_state=42) # Expect 5% anomalies
    df['anomaly'] = model.fit_predict(features) # -1 is anomaly, 1 is normal

    anomalies = df[df['anomaly'] == -1]
    
    if not anomalies.empty:
        logger.warning(f"🚨 Detected {len(anomalies)} anomalies in recent traffic flow!")
        for _, row in anomalies.iterrows():
            logger.warning(f"Anomaly at {row['node_id']}: {row['vehicle_count']} cars, {row['avg_speed']} km/h")
            # In production, we would trigger an MQTT alert here

if __name__ == "__main__":
    detect_traffic_anomalies()