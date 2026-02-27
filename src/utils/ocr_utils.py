import cv2
import easyocr
import re
import numpy as np

# --------------------------------------------------
# INITIALIZE OCR READER (CPU mode)
# --------------------------------------------------

reader = easyocr.Reader(['en'], gpu=False)


# --------------------------------------------------
# IMAGE PREPROCESSING FOR BETTER OCR
# --------------------------------------------------

def preprocess_plate_image(image):
    """
    Improve plate image before OCR:
    - Convert to grayscale
    - Increase contrast
    - Apply threshold
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Increase contrast
    gray = cv2.equalizeHist(gray)

    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return thresh


# --------------------------------------------------
# PLATE VALIDATION (BASIC REGEX)
# --------------------------------------------------

def validate_plate(text):
    """
    Basic validation to filter OCR noise.
    Modify regex according to your country's plate format.
    """

    text = text.replace(" ", "").upper()

    # Example generic pattern: letters + numbers
    pattern = r'^[A-Z0-9]{4,10}$'

    if re.match(pattern, text):
        return text

    return None


# --------------------------------------------------
# MAIN OCR FUNCTION
# --------------------------------------------------

def extract_plate_text(vehicle_image):
    """
    Extract license plate text from vehicle crop.
    Returns detected plate or "UNKNOWN"
    """

    try:
        h, w, _ = vehicle_image.shape

        # Assume plate is lower-middle region of vehicle
        plate_region = vehicle_image[int(h * 0.5):h, int(w * 0.2):int(w * 0.8)]

        if plate_region.size == 0:
            return "UNKNOWN"

        processed = preprocess_plate_image(plate_region)

        results = reader.readtext(processed)

        for (bbox, text, confidence) in results:
            if confidence > 0.4:
                valid_plate = validate_plate(text)
                if valid_plate:
                    return valid_plate

        return "UNKNOWN"

    except Exception as e:
        print("OCR Error:", e)
        return "UNKNOWN"
