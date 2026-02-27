import cv2
import numpy as np

# --------------------------------------------------
# DRAW COUNTING LINE
# --------------------------------------------------

def draw_counting_line(frame, line_position):
    cv2.line(
        frame,
        (0, line_position),
        (frame.shape[1], line_position),
        (0, 0, 255),
        3
    )
    return frame


# --------------------------------------------------
# DRAW TRACK BOX
# --------------------------------------------------

def draw_tracking_box(frame, x1, y1, x2, y2, track_id):
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.putText(
        frame,
        f"ID: {track_id}",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

    return frame


# --------------------------------------------------
# GET CENTER POINT
# --------------------------------------------------

def get_center(x1, y1, x2, y2):
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return cx, cy


# --------------------------------------------------
# DRAW SYSTEM INFO
# --------------------------------------------------

def draw_system_info(frame, vehicle_count, light_state):

    cv2.putText(
        frame,
        f"Total Vehicles: {vehicle_count}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        3
    )

    cv2.putText(
        frame,
        f"Light State: {light_state}",
        (20, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 0),
        3
    )

    return frame
