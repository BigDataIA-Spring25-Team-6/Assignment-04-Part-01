FROM python:3.10-slim

WORKDIR /app

COPY llm_integration/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY llm_integration /app/llm_integration

CMD ["python", "llm_integration/redis_consumer.py"]
