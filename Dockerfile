FROM python:3.11-slim

WORKDIR /app

# Database papkasini yaratish va ruxsat berish
RUN mkdir -p /app && chmod 777 /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Run bot
CMD ["python", "app.py"]