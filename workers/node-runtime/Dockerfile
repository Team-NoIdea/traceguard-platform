FROM node:24-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY probe.py /opt/traceguard/probe.py
USER 1000:1000
WORKDIR /workspace/src
