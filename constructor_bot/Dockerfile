FROM python:3.11-slim

# Ishchi papka
WORKDIR /app

# Tizim paketlari
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Kutubxonalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllari
COPY . .

# Port
EXPOSE 8000

# Ishga tushirish
CMD ["python", "main.py"]
