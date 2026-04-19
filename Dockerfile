FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    build-essential \
    make \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY LICENSE README.md pyproject.toml Makefile /app/
COPY hysail /app/hysail
COPY examples /app/examples
COPY scripts /app/scripts

RUN mkdir -p /app/logs /app/output

RUN chmod +x /app/scripts/*.sh && \
    python3.10 -m pip install --upgrade pip && \
    python3.10 -m pip install -e . && \
    make test

CMD ["make", "lorem_example"]
