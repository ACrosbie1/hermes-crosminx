FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git curl build-essential ripgrep \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv && \
    uv pip install --system hermes-agent[all]

ENV TELEGRAM_TOKEN=""
ENV ANTHROPIC_API_KEY=""

CMD ["hermes", "gateway", "start", "--telegram"]
