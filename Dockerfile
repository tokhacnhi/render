FROM python:3.14-rc-slim

RUN apt-get update && \
    apt-get install -y wget unzip ffmpeg fonts-nanum && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
