# src/analysis/speed_estimation.py

class SpeedEstimator:
    def __init__(self, line_1_y, line_2_y, distance_meters):
        self.line_1_y = line_1_y
        self.line_2_y = line_2_y
        self.distance_meters = distance_meters
        
        # Memory dictionaries
        self.entry_times = {} # {track_id: timestamp}
        self.speeds = {}      # {track_id: speed_kmh}

    def update(self, track_id, prev_cy, cy, current_time):
        """Calculates speed based on time taken to cross between two lines."""
        
        # 1. Did the vehicle cross the FIRST line? (Start timer)
        if (prev_cy <= self.line_1_y and cy > self.line_1_y) or (prev_cy >= self.line_1_y and cy < self.line_1_y):
            self.entry_times[track_id] = current_time

        # 2. Did the vehicle cross the SECOND line? (End timer & Calculate)
        if track_id in self.entry_times and track_id not in self.speeds:
            if (prev_cy <= self.line_2_y and cy > self.line_2_y) or (prev_cy >= self.line_2_y and cy < self.line_2_y):
                
                time_elapsed = current_time - self.entry_times[track_id]
                
                if time_elapsed > 0:
                    speed_ms = self.distance_meters / time_elapsed
                    speed_kmh = speed_ms * 3.6
                    self.speeds[track_id] = round(speed_kmh, 2)
                    return self.speeds[track_id]
                    
        return None
    
    def get_speed(self, track_id):
        """Returns the calculated speed if it exists."""
        return self.speeds.get(track_id, None)