# Use a lightweight Python image
FROM python:3.11-slim

# 1. Install system dependencies (ffmpeg is a MUST for audio/video)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only requirements first (this makes building faster next time)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your main.py and index.html into the container
COPY . .

# 5. Tell Python to show logs immediately (unbuffered)
ENV PYTHONUNBUFFERED=1

# 6. Start the app using Uvicorn
# We use 0.0.0.0 so it can accept connections from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]