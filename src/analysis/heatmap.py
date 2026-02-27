# src/analysis/heatmap.py
import cv2
import numpy as np

class HeatmapGenerator:
    def __init__(self, width, height, decay_rate=0.90):
        self.width = width
        self.height = height
        self.decay_rate = decay_rate  # 👈 NEW: How fast the trail fades (0.0 to 1.0)
        self.accum_image = np.zeros((self.height, self.width), np.float32)
        
    def update(self, tracks):
        """Adds vehicle center points and applies decay to fade old paths."""
        
        # 👈 NEW: Cool down the entire road every frame so old trails vanish
        self.accum_image = self.accum_image * self.decay_rate
        
        for track in tracks:
            x1, y1, x2, y2, track_id = map(int, track)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # Add "heat" where the car currently is
            cv2.circle(self.accum_image, (cx, cy), radius=20, color=(10,), thickness=-1)
            
    def apply_overlay(self, frame, alpha=0.5):
        """Converts the accumulation array into a heatmap and blends it safely."""
        max_val = np.max(self.accum_image)
        
        # Safe normalization to prevent flickering when the road is empty
        if max_val > 0.1:
            # We cap the divisor so faint trails don't suddenly turn bright red
            divisor = max(max_val, 15.0) 
            norm_accum = (self.accum_image / divisor) * 255
        else:
            norm_accum = self.accum_image
            
        norm_accum = np.uint8(norm_accum)
        color_map = cv2.applyColorMap(norm_accum, cv2.COLORMAP_JET)
        
        # --- SAFE BLENDING LOGIC ---
        blended = cv2.addWeighted(frame, 1 - alpha, color_map, alpha, 0)
        
        # Mask out the cold areas so the normal road shows through
        mask = norm_accum > 5
        mask_3d = np.repeat(mask[:, :, np.newaxis], 3, axis=2)
        
        return np.where(mask_3d, blended, frame)