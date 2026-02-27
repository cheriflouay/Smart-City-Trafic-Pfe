# deploy/Dockerfile
FROM python:3.11-slim

# Install system dependencies required for OpenCV and SQLite
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip, install base requirements, and explicitly install Enterprise Platform libraries
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir onnxruntime psutil fpdf scikit-learn \
    fastapi uvicorn streamlit paho-mqtt easyocr pandas plotly \
    folium streamlit-folium streamlit-autorefresh

# Copy the actual Smart City code
COPY src/ /app/src/
COPY config.yaml /app/
COPY traffic_system.db /app/

# Environment variables
ENV PYTHONUNBUFFERED=1 
ENV HEADLESS_MODE=1

# Default command
CMD ["python", "-m", "src.decision.orchestrator"]