FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi==0.136.3 uvicorn==0.38.0 flask==3.1.2 pytest==8.4.2 httpx==0.28.1 requests==2.32.5
COPY probe.py /opt/traceguard/probe.py
COPY validate.py /opt/traceguard/validate.py
ENV PYTHONDONTWRITEBYTECODE=1
USER 1000:1000
WORKDIR /workspace/src
