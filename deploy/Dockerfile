# deploy/Dockerfile
FROM python:3.11-slim

# 👇 THE FIX: Added build-essential and python3-dev to compile AI math libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip and install everything
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir onnxruntime psutil fpdf scikit-learn \
    fastapi uvicorn streamlit paho-mqtt easyocr pandas plotly \
    folium streamlit-folium streamlit-autorefresh lapx

# Copy the actual Smart City code
COPY src/ /app/src/
COPY config.yaml /app/

# Environment variables
ENV PYTHONUNBUFFERED=1 
ENV HEADLESS_MODE=1

# Default command
CMD ["python", "-m", "src.decision.orchestrator"]