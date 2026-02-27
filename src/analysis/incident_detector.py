# src/analysis/incident_detector.py
import time
import math
from src.utils.logger import setup_logger

logger = setup_logger("IncidentDetector")

class IncidentDetector:
    """Enterprise module for detecting spatial anomalies (wrong-way, stopped)."""
    
    def __init__(self, fps=30, stop_threshold_sec=5.0, wrong_way_vector='DOWN'):
        self.history = {}  # {track_id: [(timestamp, cx, cy)]}
        self.stop_threshold_sec = stop_threshold_sec
        self.wrong_way_vector = wrong_way_vector # Expected traffic flow direction
        self.pixel_movement_threshold = 15 # Pixels

    def update_and_detect(self, track_id, cx, cy, current_time):
        """Updates vehicle trajectory and returns incident type if detected."""
        if track_id not in self.history:
            self.history[track_id] = []
        
        self.history[track_id].append((current_time, cx, cy))
        
        # Keep only the last 10 seconds of history to save RAM
        self.history[track_id] = [h for h in self.history[track_id] if current_time - h[0] < 10.0]
        
        if len(self.history[track_id]) < 5:
            return None

        oldest_time, old_x, old_y = self.history[track_id][0]
        time_diff = current_time - oldest_time
        
        # 1. Detect Stopped Vehicle
        distance = math.hypot(cx - old_x, cy - old_y)
        if time_diff >= self.stop_threshold_sec and distance < self.pixel_movement_threshold:
            return "STOPPED_VEHICLE"

        # 2. Detect Wrong-Way Driving
        dy = cy - old_y
        if self.wrong_way_vector == 'DOWN' and dy < -30: # Moving UP significantly
            return "WRONG_WAY"
        elif self.wrong_way_vector == 'UP' and dy > 30: # Moving DOWN significantly
            return "WRONG_WAY"

        return None