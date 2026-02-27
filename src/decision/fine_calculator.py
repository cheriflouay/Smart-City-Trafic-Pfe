# src/decision/fine_calculator.py
import yaml
from src.utils.logger import setup_logger

logger = setup_logger()

class FineCalculator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as file:
            self.config = yaml.safe_load(file)
            
        self.fines = self.config.get("fines", {})
        self.speed_limit = self.config["speed_estimation"]["speed_limit_kmh"]
        logger.info("Fine Calculator initialized successfully.")

    def calculate_fine(self, violation_type, speed=None):
        """Calculates the dynamic fine amount based on violation type and severity."""
        total_fine = 0
        
        # 1. Red Light Penalty
        if violation_type in ["RED_LIGHT", "BOTH"]:
            total_fine += self.fines.get("red_light", 200)
        
        # 2. Speeding Penalty (Dynamic)
        if violation_type in ["SPEED", "BOTH"] and speed is not None:
            base_speed_fine = self.fines.get("speed_base", 150)
            
            # Calculate how far over the limit they were
            over_limit = max(0, speed - self.speed_limit)
            scaling_penalty = over_limit * self.fines.get("speed_per_kmh_over", 5)
            
            total_fine += (base_speed_fine + scaling_penalty)
            
        return int(total_fine)