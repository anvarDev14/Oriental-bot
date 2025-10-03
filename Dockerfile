FROM python:3.11-slim

WORKDIR /app

# /app papkasiga to'liq ruxsat (COPY dan OLDIN)
RUN chmod 777 /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# /app ichidagi barcha fayllar uchun ruxsat
RUN chmod -R 777 /app

# Bot ishga tushirish
CMD ["python", "app.py"]