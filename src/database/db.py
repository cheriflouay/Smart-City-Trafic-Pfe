# src/database/db.py
import sqlite3
from src.utils.logger import setup_logger

logger = setup_logger("EnterpriseDB")
DB_PATH = "traffic_system.db"

def get_connection(db_path=DB_PATH):
    """Returns a connection with a timeout to handle multi-node concurrent writes safely."""
    conn = sqlite3.connect(db_path, timeout=15.0) 
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    logger.info("🗄️ Initializing Distributed Enterprise Database Schema...")
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. NODE REGISTRY
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            location_name TEXT,
            status TEXT,          
            last_heartbeat DATETIME,
            cpu_load REAL,
            ram_load REAL
        )
    ''')

    # 2. TRAFFIC METRICS (Upgraded with node_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            vehicle_count INTEGER,
            avg_speed REAL,
            congestion_level TEXT,
            weather_condition TEXT DEFAULT 'CLEAR',
            FOREIGN KEY(node_id) REFERENCES nodes(node_id)
        )
    ''')

    # 3. VIOLATIONS (Upgraded with node_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            vehicle_id INTEGER,
            plate_number TEXT,
            violation_type TEXT,
            speed REAL,
            fine_amount REAL,
            image_path TEXT,
            light_state TEXT,
            status TEXT DEFAULT 'UNPROCESSED'
        )
    ''')

    # 4. INCIDENTS (Safety & Hazards)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            incident_type TEXT,
            severity TEXT,
            vehicle_id INTEGER,
            image_path TEXT,
            resolved BOOLEAN DEFAULT 0
        )
    ''')

    # 5. V2X SIMULATION LEDGER
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS v2x_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            vehicle_type TEXT,
            priority_level INTEGER,
            latency_ms INTEGER,
            action_taken TEXT
        )
    ''')

    # 6. MLOPS REGISTRY
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ml_registry (
            version_id TEXT PRIMARY KEY,
            model_type TEXT,
            trained_at TEXT,
            accuracy_score REAL,
            f1_score REAL,
            is_active BOOLEAN
        )
    ''')

    # 7. PERFORMANCE INDEXES
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_node ON traffic_metrics(node_id, timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_violations_node ON violations(node_id, timestamp);')

    conn.commit()
    conn.close()
    logger.info("✅ Database schema successfully upgraded to Multi-Node architecture.")

def insert_violation(node_id, timestamp, vehicle_id, plate_number, image_path, light_state, violation_type="RED_LIGHT", speed=None, fine_amount=0):
    """Upgraded to support multi-node tracking."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO violations (node_id, timestamp, vehicle_id, plate_number, violation_type, speed, fine_amount, image_path, light_state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (node_id, timestamp, vehicle_id, plate_number, violation_type, speed, fine_amount, image_path, light_state))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()