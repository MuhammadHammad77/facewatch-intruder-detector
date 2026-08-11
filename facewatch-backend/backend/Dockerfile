FROM python:3.11-slim

# Install system dependencies required for OpenCV, dlib, and face_recognition
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend files
COPY . .

# Expose the port Railway uses (defaults to 8000 for FastAPI/Uvicorn, Railway provides PORT env var)
ENV PORT=8000
EXPOSE $PORT

# Run the FastAPI application
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
