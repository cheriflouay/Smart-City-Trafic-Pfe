# src/decision/hybrid_ml_engine.py
import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from src.database.db import get_connection
from src.utils.logger import setup_logger

logger = setup_logger("MLOpsEngine")

def train_hybrid_model():
    """Trains a CPU-optimized Ensemble Model and logs MLOps metadata."""
    logger.info("🧠 Booting Hybrid ML Engine (CPU Optimized)...")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT timestamp, vehicle_count, avg_speed, congestion_level FROM traffic_metrics", conn)

    if len(df) < 100:
        logger.warning("Insufficient data. Minimum 100 rows required.")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    X = df[['hour', 'day_of_week', 'vehicle_count', 'avg_speed']]
    y = df['congestion_level']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Hybrid Ensemble (Fast on CPU, highly accurate)
    clf1 = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    clf2 = HistGradientBoostingClassifier(random_state=42)
    model = VotingClassifier(estimators=[('rf', clf1), ('hgb', clf2)], voting='soft')

    logger.info("⚙️ Training Hybrid Model...")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='weighted')
    
    version = f"hybrid_v{int(datetime.now().timestamp())}"
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, f"models/{version}.pkl")

    # MLOps Logging
    conn.execute("""
        INSERT INTO ml_registry (version_id, model_type, trained_at, accuracy_score, f1_score, is_active)
        VALUES (?, 'HYBRID_ENSEMBLE', ?, ?, ?, 1)
    """, (version, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), acc, f1))
    
    # Deactivate older models
    conn.execute("UPDATE ml_registry SET is_active = 0 WHERE version_id != ?", (version,))
    conn.commit()
    conn.close()

    logger.info(f"✅ MLOps: Model {version} deployed. Acc: {acc:.2f} | F1: {f1:.2f}")

if __name__ == "__main__":
    train_hybrid_model()