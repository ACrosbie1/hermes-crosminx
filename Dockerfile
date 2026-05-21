FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir anthropic python-telegram-bot

COPY hermes_bot.py .

ENV TELEGRAM_TOKEN=""
ENV ANTHROPIC_API_KEY=""

CMD ["python", "hermes_bot.py"]
