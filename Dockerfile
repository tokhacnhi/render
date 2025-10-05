FROM python:3.14-rc-slim

RUN apt-get update && \
    apt-get install -y wget unzip ffmpeg fonts-nanum curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install pandas requests fire edge-tts
