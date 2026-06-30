FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux asciinema ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/test-venv && \
    /opt/test-venv/bin/pip install --no-cache-dir pytest==8.3.3

COPY . /app/src
WORKDIR /app/src
